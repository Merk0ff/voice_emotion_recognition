import json
import logging
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

import redis
from fastapi import BackgroundTasks, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .celery_app import app as celery_app

app = FastAPI()
templates = Jinja2Templates(directory="templates")
r = redis.Redis(host="redis", port=6379, db=0, decode_responses=True)
logger = logging.getLogger(__name__)


def is_youtube_url(url: str):
    parsed_url = urlparse(url)
    return parsed_url.netloc in ("www.youtube.com", "youtube.com", "youtu.be")


@app.get("/", response_class=HTMLResponse)
async def get_form(request: Request):
    return templates.TemplateResponse("submit_url.html", {"request": request})


@app.post("/submit-url")
async def submit_url(background_tasks: BackgroundTasks, youtube_url: str = Form(...)):
    if not is_youtube_url(youtube_url):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    task_id = str(uuid4())

    logger.info(f"Task ID: {task_id}, Processing URL: {youtube_url}")
    celery_app.send_task("process_audio", args=[task_id, youtube_url], queue="ml-queue")

    return RedirectResponse(url=f"/result/{task_id}", status_code=303)


@app.get("/result/{uuid}", response_class=HTMLResponse)
async def get_data_row(uuid: str, request: Request):
    item = r.hgetall(uuid)

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    predictions_ready = item["predictions"] != ""

    if predictions_ready:
        url_data = urlparse(item["url"])
        query_params = parse_qs(url_data.query)
        youtube_id = query_params.get("v")[0] if "v" in query_params else None

        item["predictions"] = json.loads(item["predictions"])
        max_emotion = max(item["predictions"], key=item["predictions"].get)
        max_value = item["predictions"][max_emotion] * 100  # Convert to percentage
    else:
        youtube_id = None
        max_emotion = None
        max_value = None

    return templates.TemplateResponse(
        "view.html",
        {
            "request": request,
            "item": item,
            "youtube_id": youtube_id,
            "max_emotion": max_emotion,
            "max_value": max_value,
            "predictions_ready": predictions_ready,
        },
    )

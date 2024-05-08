import json
import logging
import tempfile

from .monkeypatch import *  # noqa

import redis
import torch
from aniemore.models import HuggingFaceModel
from aniemore.recognizers.multimodal import MultiModalRecognizer
from aniemore.utils.speech2text import SmallSpeech2Text
from pydub import AudioSegment
from pytube import YouTube

from .celery_app import app as celery_app

# Establish a Redis connection
redis_db = redis.StrictRedis(host="redis", port=6379, db=0)
logger = logging.getLogger(__name__)


class AudioEmotion:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not isinstance(cls._instance, cls):
            instance = super().__new__(cls, *args, **kwargs)

            model = HuggingFaceModel.MultiModal.WavLMBertFusion
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {device}")

            instance.mr = MultiModalRecognizer(
                model=model, s2t_model=SmallSpeech2Text(), device=device
            )
            cls._instance = instance

        return cls._instance

    @staticmethod
    def download_and_convert_audio(url, output_filename):
        # Download the audio
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_filename = temp_file.name

            # Download the audio
            yt = YouTube(url)
            audio_stream = yt.streams.filter(only_audio=True).first()
            audio_stream.download(filename=temp_filename)

            video_duration = yt.length
            if video_duration > 300:  # 5 minutes in seconds
                raise ValueError("Video is longer than 5 minutes")

            # Load the audio file
            audio = AudioSegment.from_file(temp_filename, format="mp4")

            # Convert the audio to mono
            audio = audio.set_channels(1)

            # Save the audio as an OGG file
            audio.export(output_filename, format="wav")

    def pipline(self, uuid, url):
        filename = f"./downloads/{uuid}.wav"

        # Store initial data in Redis
        redis_db.hmset(uuid, {"url": url, "predictions": ""})

        try:
            # self.download_and_convert_audio(url, filename)
            predictions = self.mr.recognize(filename)
        except ValueError:
            predictions = {
                "angry": 0.0,
                "disgust": 0.0,
                "fear": 0.0,
                "happy": 0.0,
                "neutral": 0.0,
                "sad": 0.0,
                "surprise": 0.0,
            }

        # Update data in Redis
        redis_db.hmset(uuid, {"predictions": json.dumps(predictions)})


@celery_app.task(name="process_audio")
def process_audio(uuid, url):
    logger.info(f"Got Task ID: {uuid}, Processing URL: {url}")
    AudioEmotion().pipline(uuid, url)

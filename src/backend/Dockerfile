# Base image
FROM python:3.12-slim-bullseye

# Set working directory
WORKDIR /app

# Install pip
RUN python -m ensurepip

# Install Poetry
RUN pip install poetry

# Copy the poetry.lock and pyproject.toml files to the working directory
COPY poetry.lock pyproject.toml /app/

# Install dependencies
RUN poetry install --no-interaction --no-ansi

# Copy the rest of the application code to the working directory
COPY . /app

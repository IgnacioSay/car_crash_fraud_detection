# Use the official Python 3.11 image
FROM python:3.12

# Set the working directory
WORKDIR /app

COPY . .

RUN apt-get update && apt-get upgrade -y && apt-get install -y curl python3 python3-dev python3-venv build-essential \
    libgmp3-dev && curl -sSL https://install.python-poetry.org | python3 -
ADD poetry.lock .
ADD pyproject.toml .
ADD front.py .
ENV PATH "/root/.local/bin:$PATH"
RUN poetry install
ENV STREAMLIT_SERVER_PORT 8502
RUN poetry run echo $PATH
RUN poetry run which python
RUN poetry run which streamlit
CMD ["poetry", "run", "streamlit", "run", "front.py", "--server.port", "8502"]
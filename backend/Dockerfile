FROM python:3.12
WORKDIR /app

RUN pip install --upgrade pip wheel

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir
RUN pip install --force-reinstall setuptools gunicorn==22.0.0

COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "foodgram_backend.wsgi"]

FROM python:3

WORKDIR /app

COPY requirements.txt ./

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py ./
COPY settings.ini ./
COPY ssl/* ./ssl/

CMD ["python", "-u", "./main.py"]
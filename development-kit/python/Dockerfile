FROM python:3.8.6
WORKDIR /app

COPY . .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 8081

ENTRYPOINT [ "python", "demo-player.py"]

CMD [ "http://localhost:8080/", "Dealer 1", "Player 1" ]

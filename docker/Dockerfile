FROM python:3-slim-bullseye

RUN apt update && apt install -y curl

RUN pip3 install mio-cli

WORKDIR /design

CMD ["/bin/sh"]
#docker build -t mio-client .
#docker push ...

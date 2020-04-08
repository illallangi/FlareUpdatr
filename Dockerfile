FROM python:3.7

RUN pip install \
  cloudflare \
  kubernetes

ADD . /src/

CMD /src/updatr

FROM python:3.7

RUN pip install \
  cloudflare

ADD . /src/

CMD /src/updatr

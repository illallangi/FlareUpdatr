FROM python:3.7

RUN pip install \
  cloudflare \
  twisted

ADD . /src/

CMD /src/updatr

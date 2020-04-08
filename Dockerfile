FROM python:3.7

ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=UTF-8 \
    LC_ALL=en_US.UTF-8 \
    LANG=en_US.UTF-8 \

RUN pip install \
  cloudflare \
  kubernetes

ADD . /src/

CMD /src/updatr

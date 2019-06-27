FROM python:3.7-alpine as builder
WORKDIR /build
RUN pip install virtualenv
RUN virtualenv /build
RUN apk add --update --no-cache \
    build-base \
    linux-headers \
    pcre-dev \
    git
COPY requirements.txt /build
RUN /build/bin/pip install -r requirements.txt uwsgi

FROM python:3.7-alpine as application
RUN adduser -D -g '' uwsgi
RUN apk add --no-cache git
WORKDIR /app
COPY --from=builder /build /build
COPY --from=builder /usr/lib/libpcre* /usr/lib/
ADD . /app/
RUN /build/bin/pip install .
RUN chown -R uwsgi:uwsgi /app
RUN mkdir /data && chown uwsgi:uwsgi /data

CMD /build/bin/uwsgi uwsgi.yml

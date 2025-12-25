FROM python:3.12

# no .git dir in image, so we pretend:
ENV SETUPTOOLS_SCM_PRETEND_VERSION 0.0.0.dev0
ENV PYTHONUNBUFFERED 1

WORKDIR /home
COPY . /home

RUN apt-get update -y \
    && apt-get install -y --no-install-recommends python3-distutils=3.11.2-3 \
    && pip install --no-cache-dir --upgrade pip==24.1.1 \
    && pip install --no-cache-dir -r requirements.txt \
    && make pip-install \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["montecarlo"]

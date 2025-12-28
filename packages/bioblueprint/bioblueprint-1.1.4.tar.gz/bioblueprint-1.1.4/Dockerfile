ARG BIOBLUEPRINT_VER="1.1.4"

FROM google/cloud-sdk:532.0.0

ARG BIOBLUEPRINT_VER

RUN apt-get update \
  && apt-get install -y \
    procps wget tzdata \
    python3 python3-pip python3-setuptools python3-wheel \
  && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install bioblueprint --break-system-packages

WORKDIR /data

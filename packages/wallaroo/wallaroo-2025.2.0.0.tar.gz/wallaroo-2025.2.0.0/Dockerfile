#
# Minimal archive of just SDK artifacts like the wheel. Later, it could hold other related artifacts as
# well. Used only for multipart builds of other images like this:
#  
#  FROM ghcr.io/wallaroolabs/sdk:123456
#  FROM python:3.10-slim
#  COPY --from=0  /wallaroo-*.whl /
#  RUN pip install /wallaroo-*.whl && rm /wallaroo-*.whl
#  

FROM scratch

LABEL org.opencontainers.image.vendor="Wallaroo Labs"
LABEL org.opencontainers.image.source="https://github.com/WallarooLabs/sdk" 
LABEL org.opencontainers.image.title="sdk"

COPY dist/wallaroo*whl /
COPY global_wallaroo_api.json /

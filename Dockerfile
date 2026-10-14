FROM python:3.11 as rst_ml_build
WORKDIR /app

COPY .scripts/install.sh ./.scripts/
RUN chmod +x .scripts/install.sh
RUN .scripts/install.sh
RUN chmod +x .scripts/start.sh

FROM rst_ml_build as prod
WORKDIR /app
ENV PORT 3030

COPY ./lib/tesseract/* /usr/share/tesseract-ocr/5/tessdata/
# RUN mkdir -p /root/.cnstd/1.2/analysis
COPY ./lib/math/cnstd /root/.cnstd/
COPY ./lib/math/pix2text /root/.pix2text
COPY ./lib/math/cnocr  /root/.cnocr
COPY ./lib/math/cache /root/.cache
COPY . /app/

EXPOSE $PORT
CMD ["/app/.scripts/start.sh"]

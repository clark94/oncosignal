FROM python:3.10-slim AS build
WORKDIR /build
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip wheel --wheel-dir /wheels .

FROM python:3.10-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 ONCO_HOST=0.0.0.0 ONCO_WORKSPACE=/workspace PORT=8010
RUN useradd --create-home --uid 10001 onco && mkdir /workspace && chown onco:onco /workspace
COPY --from=build /wheels /wheels
RUN pip install --no-index --find-links=/wheels oncosignal && rm -rf /wheels
USER onco
WORKDIR /home/onco
EXPOSE 8010
HEALTHCHECK --interval=30s --start-period=20s CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.getenv('PORT','8010')+'/health',timeout=5)"
CMD ["python", "-m", "oncosignal", "serve"]

FROM node:22-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-venv chromium ca-certificates && rm -rf /var/lib/apt/lists/*
ENV NEXT_TELEMETRY_DISABLED=1 PYTHONDONTWRITEBYTECODE=1 BROWSER_EXECUTABLE=/usr/bin/chromium
WORKDIR /work

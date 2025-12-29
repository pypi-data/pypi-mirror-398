FROM crpi-cev6qq28wwgwwj0y.cn-beijing.personal.cr.aliyuncs.com/nexthci/service-forge:latest

WORKDIR /app

COPY . ./service

WORKDIR /app
RUN uv sync

ENV PYTHONPATH=/app/service:/app:/app/src
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app/service

RUN chmod +x start.sh

CMD ["./start.sh"]
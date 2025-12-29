DEFAULT_DEPLOYMENT_YAML = """
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {service_name}
  namespace: {namespace}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: {service_name}
  template:
    metadata:
      labels:
        app: {service_name}
    spec:
      imagePullSecrets:
        - name: aliyun-regcred
      containers:
      - name: {service_name}
        image: crpi-cev6qq28wwgwwj0y.cn-beijing.personal.cr.aliyuncs.com/nexthci/sf-{name}:{version}
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
        env:
{env}

---
apiVersion: v1
kind: Service
metadata:
  name: {service_name}
  namespace: {namespace}
  annotations:
    metadata: {sf_metadata}
spec:
  type: ClusterIP
  selector:
    app: {service_name}
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
"""

DEFAULT_TRAEFIK_INGRESS_YAML = """
apiVersion: traefik.io/v1alpha1
kind: Middleware
metadata:
  name: strip-prefix-sf-{name}-{version}v
  namespace: {namespace}
spec:
  stripPrefix:
    prefixes:
      - /api/v1/{name}-{version}

---

apiVersion: traefik.io/v1alpha1
kind: IngressRoute
metadata:
  name: sf-{name}-{version}v
  namespace: {namespace}
spec:
  entryPoints:
    - web
  routes:
    - match: PathPrefix(`/api/v1/{name}-{version}/openapi.json`)
      kind: Rule
      services:
        - name: sf-{name}-{version}v
          namespace: {namespace}
          port: 80
      middlewares:
        - name: strip-prefix-sf-{name}-{version}v
          namespace: {namespace}
        - name: cors
          namespace: {namespace}

    - match: PathPrefix(`/api/v1/{name}-{version}/docs`)
      kind: Rule
      services:
        - name: sf-{name}-{version}v
          namespace: {namespace}
          port: 80
      middlewares:
        - name: strip-prefix-sf-{name}-{version}v
          namespace: {namespace}
        - name: cors
          namespace: {namespace}

    - match: PathPrefix(`/api/v1/{name}-{version}`)
      kind: Rule
      services:
        - name: sf-{name}-{version}v
          namespace: {namespace}
          port: 80
      middlewares:
        - name: strip-prefix-sf-{name}-{version}v
          namespace: {namespace}
        - name: cors
          namespace: {namespace}
        - name: jwt-auth
          namespace: {namespace}
"""

DEFAULT_DOCKERFILE = """
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
"""

DEFAULT_PYPROJECT_TOML = """

[tool.uv.sources]
service-forge = { workspace = true }
"""

# Build the frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/ui
COPY ui/package.json ui/pnpm-lock.yaml ./
RUN npm install -g pnpm && pnpm install --frozen-lockfile
COPY ui/ ./
# This builds to ../src/static relative to ui, so /app/src/static
RUN pnpm build

FROM browseruse/browseruse:0.10.1
USER root

WORKDIR /app

ENV IN_DOCKER=true

# Copy package files
COPY pyproject.toml README.md MANIFEST.in ./
COPY src/ src/
# Copy static files from builder
COPY --from=frontend-builder /app/ui/out src/static

# Inject version from build args so setuptools-scm works without .git
ARG VERSION=0.1.0
ENV SETUPTOOLS_SCM_PRETEND_VERSION=$VERSION

# Install the package
RUN pip install --upgrade pip && \
    pip install build && \
    pip install --no-cache-dir .

EXPOSE 8080

ENTRYPOINT []
CMD ["usefly", "--port", "8080"]

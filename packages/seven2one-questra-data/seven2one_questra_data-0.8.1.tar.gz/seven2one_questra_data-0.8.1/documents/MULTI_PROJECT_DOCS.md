# Multi-Projekt Dokumentation mit Git Submodules

Anleitung zum Zusammenführen mehrerer Python-Projekt-Dokumentationen in ein zentrales `questra-docs` Repository.

## Architektur

```
questra-docs/
├── mkdocs.yml                      # Haupt-Konfiguration
├── docs/
│   ├── index.md                    # Landing Page für alle Projekte
│   └── stylesheets/
│       └── extra.css              # Gemeinsames CSS (Seven2one Corporate Design)
├── authentication/                 # Git Submodule
│   └── docs/                      # → S2O.Questra.Python.Authentication
├── data/                          # Git Submodule
│   └── questra-data/
│       └── docs/                  # → S2O.PoC.Questra.Python.Packages/questra-data
├── Dockerfile                      # nginx Container
├── nginx.conf                      # nginx Konfiguration
├── .gitmodules                    # Git Submodules Config
└── azure-pipelines.yml            # Build Pipeline
```

## Vorteile dieser Lösung

- ✅ Dokumentation lebt bei Code (Single Source of Truth)
- ✅ Entwickler sehen Docs bei Code-Änderungen
- ✅ Automatische Versionierung durch Git
- ✅ Kein Artefakt-Download nötig
- ✅ Einfache Wartung

## Setup

### 1. Repository erstellen

```bash
# Neues Repository erstellen
mkdir questra-docs
cd questra-docs
git init
```

### 2. Git Submodules hinzufügen

```bash
# Authentication Projekt
git submodule add https://dev.azure.com/seven2one/Seven2one.Questra/_git/S2O.Questra.Python.Authentication authentication

# Data Projekt (anpassen an tatsächlichen Pfad)
git submodule add https://dev.azure.com/seven2one/Seven2one.Questra/_git/S2O.PoC.Questra.Python.Packages data

# Commit
git commit -m "Add documentation submodules"
```

### 3. Verzeichnisstruktur erstellen

```bash
mkdir -p docs/stylesheets
```

### 4. Dateien erstellen

Erstellen Sie folgende Dateien im Root-Verzeichnis:

#### mkdocs.yml

```yaml
site_name: Questra Python Documentation
site_description: Komplette Python Client Dokumentation
site_url: https://docs.example.com/questra/

# Repository
repo_url: https://dev.azure.com/seven2one/Seven2one.Questra/_git/questra-docs
edit_uri: edit/main/docs/

# Documentation directory
docs_dir: docs

# Theme
theme:
  name: material
  language: de
  palette:
    # Light mode - Seven2one Orange primary
    - scheme: default
      primary: custom
      accent: custom
      toggle:
        icon: material/brightness-7
        name: Zu Dunkelmodus wechseln
    # Dark mode - Seven2one Green primary
    - scheme: slate
      primary: custom
      accent: custom
      toggle:
        icon: material/brightness-4
        name: Zu Hellmodus wechseln
  font:
    text: Ubuntu
    code: Ubuntu Mono
  features:
    - navigation.instant
    - navigation.tracking
    - navigation.tabs
    - navigation.sections
    - navigation.expand
    - navigation.top
    - navigation.indexes
    - search.suggest
    - search.highlight
    - content.code.copy
    - content.code.annotate
    - content.tabs.link

# Plugins
plugins:
  - search:
      lang: de
  - mkdocstrings:
      handlers:
        python:
          paths:
            - authentication/src
            - data/questra-data/src
          options:
            docstring_style: google
            show_source: true
            show_root_heading: false
            show_root_full_path: false
            members_order: source
            separate_signature: true
            show_signature_annotations: true
            signature_crossrefs: true
            merge_init_into_class: true
  - git-revision-date-localized:
      enable_creation_date: true
      type: timeago
      locale: de
  - minify:
      minify_html: true

# Markdown Extensions
markdown_extensions:
  - pymdownx.highlight:
      anchor_linenums: true
      line_spans: __span
      pygments_lang_class: true
  - pymdownx.inlinehilite
  - pymdownx.snippets
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:pymdownx.superfences.fence_code_format
  - pymdownx.tabbed:
      alternate_style: true
  - admonition
  - pymdownx.details
  - pymdownx.emoji:
      emoji_index: !!python/name:material.extensions.emoji.twemoji
      emoji_generator: !!python/name:material.extensions.emoji.to_svg
  - attr_list
  - md_in_html
  - toc:
      permalink: true
  - tables
  - def_list
  - pymdownx.tasklist:
      custom_checkbox: true

# Navigation (kombiniert alle Projekte)
nav:
  - Home: index.md
  - Questra Authentication:
      - Übersicht: ../authentication/docs/index.md
      - Erste Schritte:
          - Installation: ../authentication/docs/getting-started/installation.md
          - Quickstart: ../authentication/docs/getting-started/quickstart.md
          - Authentifizierungsmodi: ../authentication/docs/getting-started/authentication-modes.md
      - API Referenz:
          - Übersicht: ../authentication/docs/api/index.md
          - QuestraAuthentication: ../authentication/docs/api/client.md
          - OAuth2: ../authentication/docs/api/authentication.md
          - Credentials: ../authentication/docs/api/credentials.md
          - OIDC Discovery: ../authentication/docs/api/oidc-discovery.md
          - Exceptions: ../authentication/docs/api/exceptions.md
      - Guides:
          - Best Practices: ../authentication/docs/guides/best-practices.md
          - Error Handling: ../authentication/docs/guides/error-handling.md
          - Token Management: ../authentication/docs/guides/token-management.md
  - Questra Data:
      - Übersicht: ../data/questra-data/docs/index.md
      - Erste Schritte:
          - Installation: ../data/questra-data/docs/getting-started/installation.md
          - Quickstart: ../data/questra-data/docs/getting-started/quickstart.md
          - API-Übersicht: ../data/questra-data/docs/getting-started/api-overview.md
      - API Referenz:
          - Übersicht: ../data/questra-data/docs/api/index.md
          - High-Level API:
              - QuestraData: ../data/questra-data/docs/api/highlevel-client.md
          - Low-Level API:
              - QuestraDataCore: ../data/questra-data/docs/api/client.md
              - Queries: ../data/questra-data/docs/api/queries.md
              - Mutations: ../data/questra-data/docs/api/mutations.md
              - REST Operationen: ../data/questra-data/docs/api/rest-operations.md
          - Models:
              - Inventory Models: ../data/questra-data/docs/api/models-inventory.md
              - TimeSeries Models: ../data/questra-data/docs/api/models-timeseries.md
              - REST Models: ../data/questra-data/docs/api/models-rest.md
              - Permission Models: ../data/questra-data/docs/api/models-permissions.md
      - Guides:
          - Best Practices: ../data/questra-data/docs/guides/best-practices.md
          - Error Handling: ../data/questra-data/docs/guides/error-handling.md
          - TimeSeries: ../data/questra-data/docs/guides/timeseries.md
          - Dateiverwaltung: ../data/questra-data/docs/guides/file-management.md

# Gemeinsames CSS (Seven2one Corporate Design)
extra_css:
  - stylesheets/extra.css

# Extra
extra:
  version:
    provider: mike
    default: latest
```

#### Dockerfile

```dockerfile
# Multi-stage build
FROM python:3.11-slim AS builder

WORKDIR /build

# System Dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Python Dependencies installieren
RUN pip install --no-cache-dir \
    mkdocs>=1.6.0 \
    mkdocs-material>=9.6.0 \
    mkdocstrings[python]>=0.26.0 \
    mkdocs-git-revision-date-localized-plugin>=1.4.0 \
    mkdocs-minify-plugin>=0.8.0

# Projekt kopieren
COPY . .

# Git Submodules initialisieren
RUN git submodule update --init --recursive || true

# Dokumentation bauen
RUN mkdocs build

# Production stage
FROM nginx:alpine

# Built docs kopieren
COPY --from=builder /build/site /usr/share/nginx/html

# Custom nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

#### nginx.conf

```nginx
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    # Logging
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript
               application/json application/javascript application/xml+rss;

    server {
        listen 80;
        server_name _;

        root /usr/share/nginx/html;
        index index.html;

        # Main location
        location / {
            try_files $uri $uri/ =404;
        }

        # Cache static assets
        location ~* \.(css|js|jpg|jpeg|png|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "no-referrer-when-downgrade" always;
    }
}
```

#### azure-pipelines.yml

```yaml
trigger:
  branches:
    include:
      - main
      - develop

pool:
  vmImage: 'ubuntu-latest'

variables:
  dockerRegistry: 'yourregistry.azurecr.io'
  imageName: 'questra-docs'
  imageTag: '$(Build.BuildId)'

stages:
  - stage: Build
    displayName: 'Build Documentation'
    jobs:
      - job: BuildDocs
        displayName: 'Build and Push Docker Image'
        steps:
          # Checkout mit Submodules
          - checkout: self
            submodules: true
            persistCredentials: true

          # Optional: Submodules auf neuesten Stand
          - script: |
              git submodule update --remote --merge
            displayName: 'Update Submodules to Latest'
            condition: eq(variables['Build.SourceBranch'], 'refs/heads/main')

          # Docker Image bauen
          - task: Docker@2
            displayName: 'Build Docker Image'
            inputs:
              command: build
              dockerfile: Dockerfile
              tags: |
                $(imageTag)
                latest
              arguments: '--no-cache'

          # Docker Image pushen
          - task: Docker@2
            displayName: 'Push to Registry'
            inputs:
              command: push
              containerRegistry: $(dockerRegistry)
              repository: $(imageName)
              tags: |
                $(imageTag)
                latest

          # Optional: Site als Artefakt publishen
          - script: |
              docker create --name temp $(dockerRegistry)/$(imageName):$(imageTag)
              docker cp temp:/usr/share/nginx/html ./site
              docker rm temp
            displayName: 'Extract built site'

          - task: PublishBuildArtifacts@1
            displayName: 'Publish Site Artifact'
            inputs:
              PathtoPublish: 'site'
              ArtifactName: 'documentation'

  - stage: Deploy
    displayName: 'Deploy Documentation'
    dependsOn: Build
    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
    jobs:
      - deployment: DeployDocs
        displayName: 'Deploy to Production'
        environment: 'production'
        strategy:
          runOnce:
            deploy:
              steps:
                - script: |
                    echo "Deploy container: $(dockerRegistry)/$(imageName):$(imageTag)"
                    # Beispiel für Docker Compose:
                    # docker pull $(dockerRegistry)/$(imageName):$(imageTag)
                    # docker-compose -f docker-compose.prod.yml up -d

                    # Beispiel für Kubernetes:
                    # kubectl set image deployment/questra-docs \
                    #   nginx=$(dockerRegistry)/$(imageName):$(imageTag)
                  displayName: 'Deploy Container'
```

#### docs/index.md

```markdown
# Questra Python Documentation

Willkommen zur zentralen Dokumentation der Questra Python Client Libraries.

## Verfügbare Pakete

<div class="grid cards" markdown>

-   :material-shield-key:{ .lg .middle } **Questra Authentication**

    ---

    OAuth2 Authentication Client für Questra API

    [:octicons-arrow-right-24: Dokumentation](../authentication/docs/index.md)

-   :material-database:{ .lg .middle } **Questra Data**

    ---

    Python Client für Dyno GraphQL und REST API

    [:octicons-arrow-right-24: Dokumentation](../data/questra-data/docs/index.md)

</div>

## Quick Start

### Installation

```bash
# Authentication
pip install questra-authentication

# Data (mit pandas)
pip install questra-data[pandas]
```

### Verwendung

```python
from questra_authentication import QuestraAuthentication
from questra_data import QuestraData

# Authentifizierung
auth_client = QuestraAuthentication(
    url="https://authentik.dev.example.com",
    username="ServiceUser",
    password="secret"
)

# Data Client
client = QuestraData(
    graphql_url="https://dev.example.com/graphql",
    auth_client=auth_client
)

# Items laden
items = client.list("Stromzaehler", "Energie")
```

## Weitere Ressourcen

- [Questra Authentication](../authentication/docs/index.md)
- [Questra Data](../data/questra-data/docs/index.md)
- [Azure DevOps](https://dev.azure.com/seven2one/Seven2one.Questra)

## License

Proprietär - Seven2one GmbH
```

### 5. CSS kopieren

Kopieren Sie das CSS aus einem der Projekte:

```bash
cp authentication/docs/stylesheets/extra.css docs/stylesheets/extra.css
# oder
cp data/questra-data/docs/stylesheets/extra.css docs/stylesheets/extra.css
```

### 6. Lokaler Test

```bash
# Dependencies installieren
pip install mkdocs mkdocs-material mkdocstrings[python] \
    mkdocs-git-revision-date-localized-plugin mkdocs-minify-plugin

# Dokumentation lokal testen
mkdocs serve

# Browser öffnen: http://127.0.0.1:8000
```

### 7. Docker Test

```bash
# Docker Image bauen
docker build -t questra-docs .

# Container starten
docker run -p 8080:80 questra-docs

# Browser öffnen: http://localhost:8080
```

## Wartung

### Submodules aktualisieren

```bash
# Alle Submodules auf neuesten Stand
git submodule update --remote --merge

# Commit und Push
git add .
git commit -m "Update submodules to latest"
git push
```

### Einzelnes Submodule aktualisieren

```bash
cd authentication
git pull origin main
cd ..
git add authentication
git commit -m "Update authentication submodule"
git push
```

### Neue Projekte hinzufügen

```bash
# Neues Submodule hinzufügen
git submodule add <repo-url> <path>

# In mkdocs.yml ergänzen unter nav:
# - mkdocstrings paths erweitern
# - Navigation erweitern
```

## Deployment

### Docker Compose (docker-compose.yml)

```yaml
version: '3.8'

services:
  docs:
    image: yourregistry.azurecr.io/questra-docs:latest
    ports:
      - "80:80"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/"]
      interval: 30s
      timeout: 3s
      retries: 3
```

Start:
```bash
docker-compose up -d
```

### Kubernetes (k8s-deployment.yml)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: questra-docs
  namespace: documentation
spec:
  replicas: 2
  selector:
    matchLabels:
      app: questra-docs
  template:
    metadata:
      labels:
        app: questra-docs
    spec:
      containers:
      - name: nginx
        image: yourregistry.azurecr.io/questra-docs:latest
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: questra-docs
  namespace: documentation
spec:
  selector:
    app: questra-docs
  ports:
  - port: 80
    targetPort: 80
  type: LoadBalancer
```

Deployment:
```bash
kubectl apply -f k8s-deployment.yml
```

## Troubleshooting

### Submodules nicht initialisiert

```bash
git submodule update --init --recursive
```

### Docker Build Fehler

```bash
# Build ohne Cache
docker build --no-cache -t questra-docs .
```

### mkdocstrings kann Module nicht finden

Prüfen Sie `paths` in mkdocs.yml:
```yaml
plugins:
  - mkdocstrings:
      handlers:
        python:
          paths:
            - authentication/src
            - data/questra-data/src  # Korrekte Pfade?
```

### Navigation-Links funktionieren nicht

Verwenden Sie relative Pfade mit `../`:
```yaml
nav:
  - Übersicht: ../authentication/docs/index.md  # Richtig
  - Übersicht: authentication/docs/index.md     # Falsch
```

## Best Practices

1. **Submodules regelmäßig updaten**: `git submodule update --remote`
2. **CI/CD automatisieren**: Bei jedem Push in Submodule-Repos
3. **Versionierung**: Tags für stabile Releases verwenden
4. **CSS zentral**: Nur in `questra-docs/docs/stylesheets/extra.css`
5. **Monitoring**: Health Checks für nginx Container

## Weitere Schritte

1. Repository in Azure DevOps erstellen
2. Submodules hinzufügen (mit korrekten URLs)
3. Dateien committen
4. Pipeline einrichten
5. Container Registry konfigurieren
6. Container deployen

# playAgent

This repository is designed to develop an AI Agent, with short and long-term memory capabilities, tool usage, and a user-friendly interface. 

You can call it DORI!

This repository is an ongoing work in progress.

**Check the Repo wiki for more information: [playAgent Wiki](https://github.com/iriacardiel/playAgent/wiki)**

---

![alt text](media/DORI_Home.png)

---

![alt text](media/DORI_Chat.png)

**Opción 1:**

Terminal 1:

```
OLLAMA_KEEP_ALIVE=24h ollama serve
```


Terminal 2 (levantar backend + frontend)

```
cd backend
source .venv/bin/activate
cd ..
make dev
```

**Opción 2:**

```
docker compose up -d
```

```
docker compose down -v
```

# Dockerize the Agent Stack for offline use / sharing

In order to build an image based on a module's source code, the following files must be present in the module folder:

- (1) `.dockerignore`
- (2) `Dockerfile`
- (3) List of dependencies (`pyproject.toml`, `package.json`, etc)

## Backend module:

```bash
backend/
├── .dockerignore # (1)
├── .env
├── .gitignore
├── .langgraph_api
├── .venv
├── Dockerfile # (2)
├── langgraph.json
├── langgraph.multi.json
├── pyproject.toml # (3)
├── src
└── uv.lock
```

## Frontend module:

```bash
frontend/
├── .codespellignore
├── .dockerignore # (1)
├── .env
├── .gitignore
├── .next
├── .prettierignore
├── Dockerfile # (2)
├── LICENSE
├── README.md
├── components.json
├── eslint.config.js
├── next-env.d.ts
├── next.config.mjs
├── node_modules
├── package.json # (3)
├── pnpm-lock.yaml
├── postcss.config.mjs
├── prettier.config.js
├── public
├── src
├── tailwind.config.js
└── tsconfig.json
```

## Ollama module:

To create a self-contained ollama image with the models included, follow these steps:

```bash
├── ollama-custom 
│   ├── Dockerfile # (2)
│   └── .ollama
│       ├── blobs
│       └── manifests
```

`.dockerfile` (1) and dependencies (3) are not needed since we are using the official ollama image as base.

For this particular module, we need to do some extra steps:

1. With local ollama, pull the models into ollama-custom/.ollama folder.

To do so:
```bash
mkdir ollama-custom/.ollama
export OLLAMA_MODELS="$PWD/ollama-custom/.ollama" # change ollama folder temporally
ollama serve # serve ollama
ollama pull gpt-oss:20b # pull the desired models
```

2. ollama-custom/Dockerfile will handle the Ollama image pull and will set the ollama folder to ollama-custom/.ollama. As a last step, it will copy the contents of the .ollama folder to the container workdir. That way, the built image will contain the models so it wont need online conection when the images are initalizated.


```Dockerfile
FROM ollama/ollama:0.11.3
ENV OLLAMA_MODELS=/root/.ollama
COPY --chown=0:0 ./.ollama/ /root/.ollama/
```

3. Run quick test:

```bash
cd ollama-custom
docker build -t my-ollama-with-models:2025-09-05 .
docker run --rm -d --name ollama-test -p 11434:11434 my-ollama-with-models:2025-09-05
docker exec ollama-test ollama list
docker rm -f ollama-test
```

4. When this works, we can set the service configuration in the docker-compose.yml to use this image.

```yaml
  ollama:
    # Build from your custom Dockerfile (which COPYs ./.ollama into /root/.ollama)
    build:
      context: ./ollama-custom        # <- folder that has Dockerfile and .ollama/
      dockerfile: Dockerfile
    image: ollama-custom:2025-09-05  # tag the result so it's easy to reference/save
    container_name: agent-ollama
    restart: unless-stopped
    ports: ["11434:11434"]
    environment:
      OLLAMA_KEEP_ALIVE: "24h"
    gpus: all
```

5. Now, when you run `docker compose up -d`, it will build the ollama image with the models included if it doesn't exist yet, and then start the container.

## Build the images

```bash 
docker compose build --no-cache
```

## Initate the containers if needed (optional)

Raise the images in detached mode:

```bash 
docker compose up -d
```

Check the status of the containers:

```bash 
docker compose logs -f
```

To stop and remove the containers, networks, and volumes:

```bash 
docker compose down -v
```

## Save and load all images (for offline use / sharing)

```bash
docker image ls | grep -E 'agent-(ollama|backend|frontend)-i'
```

```bash
docker save -o agent-stack-latest.tar agent-ollama-i:latest agent-backend-i:latest agent-frontend-i:latest
``` 

+ Compress to smaller file (optional but recommended)

```bash
gzip -9 agent-stack-latest.tar
```

## On the target folder/machine (offline)

**if gzipped**

```bash
gunzip -c agent-stack-latest.tar.gz | docker load
```

### Load images from tar file:

```bash
docker load -i agent-stack-latest.tar
```

```bash
docker image ls | grep -E 'agent-(ollama|backend|frontend)-i'
```

### Then run with:

```bash
docker compose up --no-build -d
```

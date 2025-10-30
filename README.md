# playAgent

This repository is designed to develop an AI Agent, with short and long-term memory capabilities, tool usage, and a user-friendly interface.

You can call it DORI!

This repository is an ongoing work in progress.

**Check the Repo wiki for more information: [playAgent Wiki](https://github.com/iriacardiel/playAgent/wiki)**

---

![alt text](media/DORI_Home.png)

---

![alt text](media/DORI_Chat.png)

## Set up and start

```bash
# Clone and setup
git clone <repository-url>
cd playAgent
./setup.sh
```

That's it! The setup script will:

- Create environment configuration
- Download AI models
- Start all services with Docker

**Access URLs:**

- Frontend: http://localhost:3000
- Backend: http://localhost:2024
- LangGraph Dev UI: http://localhost:2924
- Neo4j: http://localhost:7474
- NeoDash: http://localhost:5005

## Services 🐳

- **Ollama**: AI model server
- **Backend**: LangGraph API server
- **Frontend**: Next.js web interface
- **Neo4j**: Graph database for memory
- **NeoDash**: Database management UI

## Management Commands

```bash
# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart services
docker-compose restart

# Check status
docker-compose ps
```

```bash
ollama pull gpt-oss:20b # only if not pulled yet
```

### Frontend setup 

```bash
cd frontend
pnpm install # only if not installed yet
cd .. # go back to root folder
```

### Backend setup

```bash
cd backend
python3 -m venv .venv # only if not created yet
source .venv/bin/activate
pip install uv # only if not installed yet
uv sync # to sync dependencies to from pyproject.toml to .venv
cd .. # go back to root folder
```

### Neo4j

```bash
docker compose up -d neo4j # to start neo4j container
```

### Run the stack

```bash
make dev # to run both backend and frontend 
```

or

```bash
make dev-backend # to run backend only
make dev-frontend # to run frontend only
```

Run the following scripts to load data into Neo4j Knowledge Graph and make the nodes move in the map:

```bash
python backend/src/services/neo4j/load_friends.py
python backend/src/services/neo4j/load_extra_friends.py
python backend/src/services/neo4j/animate_friends.py
```

## Dockerize the Agent Stack for offline use / sharing

In order to build an image based on a module's source code, the following files must be present in the module folder:

- (1) `.dockerignore`
- (2) `Dockerfile`
- (3) List of dependencies (`pyproject.toml`, `package.json`, etc)

### Backend module:

If you are using Huggingface models, make sure to copy your huggingface models to the backend folder before building the image.

```bash
cd backend/ && mkdir .huggingface
rsync -a /opt/.huggingface/ .huggingface/
```

```bash
backend/
├── .dockerignore # (1)
├── .huggingface/
├── .env
├── .gitignore
├── .langgraph_api/
├── .venv/
├── Dockerfile # (2)
├── langgraph.json
├── pyproject.toml # (3)
├── src/
└── uv.lock
```

### Frontend module:

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

### Ollama module:

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

1. With local ollama:

**Option A**: Pull the models into ollama-custom/.ollama folder.

```bash
mkdir ollama-custom/.ollama
export OLLAMA_MODELS="$PWD/ollama-custom/.ollama" # change ollama folder temporally
ollama serve # serve ollama
ollama pull gpt-oss:20b # pull the desired models
ollama pull nomic-embed-text # pull the desired models

```

**Option B:** If firewall restrictions are activated, load them from the existing local ollama installation.

```bash
ls -la /opt/.ollama-dori/models/manifests/registry.ollama.ai/library/ # or your local ollama models folder
```

You should see something like this:

```bash
total 16
drwxr-xr-x 4 icardielp icardielp 4096 Sep 12 12:01 .
drwxr-xr-x 3 icardielp icardielp 4096 Sep 12 12:01 ..
drwxr-xr-x 2 icardielp icardielp 4096 Sep 12 12:01 gpt-oss
drwxr-xr-x 2 icardielp icardielp 4096 Sep 12 12:01 nomic-embed-text
```

Then copy the manifests and blobs to the ollama-custom/.ollama folder:

```bash
mkdir ollama-custom/.ollama
rsync -a /opt/.ollama-dori/ ollama-custom/.ollama/ 
```

2. The ``ollama-custom/Dockerfile`` will handle the Ollama image pull and will set the ollama folder to ollama-custom/.ollama. As a last step, it will copy the contents of the .ollama folder to the container workdir. That way, the built image will contain the models so it wont need online conection when the images are initalizated.


```Dockerfile
FROM ollama/ollama:0.11.3
ENV OLLAMA_MODELS=/opt/.ollama-dori/models
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

### Build the images

**Option A**: All images at once

```bash 
docker compose build --no-cache
```

**Option B**: One by one
```bash 
docker compose build --no-cache neo4j 
```

```bash 
docker compose build --no-cache ollama 
```

```bash 
docker compose build --no-cache backend 
```

```bash 
docker compose build --no-cache frontend 
```

### Initate the containers if needed (optional)

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

### Save and load all images (for offline use / sharing)

```bash
docker image ls | grep -E 'agent-(ollama|backend|frontend|neo4j)-i'
```

```bash
docker save -o agent-stack-latest.tar agent-ollama-i:latest agent-backend-i:latest agent-frontend-i:latest
``` 

+ Compress to smaller file (optional but recommended)

```bash
gzip -9 agent-stack-latest.tar
```

### On the target folder/machine (offline)

**if gzipped**

```bash
gunzip -c agent-stack-latest.tar.gz | docker load
```

### Load images from tar file:

```bash
docker load -i agent-stack-latest.tar
```

```bash
docker image ls | grep -E 'agent-(ollama|backend|frontend|neo4j)-i'
```

### Then run with:

```bash
docker compose up --no-build -d
```





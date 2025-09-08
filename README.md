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


# Create Ollama image:


```bash
├── ollama-custom
│   ├── Dockerfile
│   └── .ollama
│       ├── blobs
│       │   ├── sha256-31df23ea7daa448f9ccdbbcecce6c14689c8552222b80defd3830707c0139d4f
│       │   ├── sha256-55c108d8e93662a22dcbed5acaa0374c7d740c6aa4e8b7eee7ae77ed7dc72a25
│       │   ├── sha256-970aa74c0a90ef7482477cf803618e776e173c007bf957f635f1015bfcfef0e6
│       │   ├── sha256-b112e727c6f18875636c56a779790a590d705aec9e1c0eb5a97d51fc2a778583
│       │   ├── sha256-c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4
│       │   ├── sha256-ce4a164fc04605703b485251fe9f1a181688ba0eb6badb80cc6335c0de17ca0d
│       │   ├── sha256-d8ba2f9a17b3bbdeb5690efaa409b3fcb0b56296a777c7a69c78aa33bbddf182
│       │   ├── sha256-f60356777647e927149cbd4c0ec1314a90caba9400ad205ddc4ce47ed001c2d6
│       │   └── sha256-fa6710a93d78da62641e192361344be7a8c0a1c3737f139cf89f20ce1626b99c
│       └── manifests
│           └── registry.ollama.ai
│               └── library
│                   ├── gpt-oss
│                   │   └── 20b
│                   └── nomic-embed-text
│                       └── latest
```

1. With local ollama, pull the models into ollama-custom/.ollama folder.

To do so:
```bash
cd mkdir ollama-custom
ollama serve # serve ollama
export OLLAMA_MODELS="$PWD/ollama-custom/.ollama" # change ollama folder temporally
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

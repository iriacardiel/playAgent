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
from pathlib import Path

from fastapi import FastAPI

app = FastAPI(title="repository-indexer")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/index")
def index(path: str) -> dict:
    root = Path(path)
    files = [p.as_posix() for p in root.rglob("*") if p.is_file()][:1000]
    return {"count": len(files), "files": files}

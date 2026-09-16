from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/v1/chat/completions")
def chat_completions(payload: dict) -> dict:
    return {
        "id": "mock-completion",
        "object": "chat.completion",
        "created": 0,
        "model": payload.get("model", "mock-model"),
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "{\"search_queries\": [\"auth\"], \"test_command\": \"pytest -q\"}"},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 50, "completion_tokens": 30, "total_tokens": 80},
    }

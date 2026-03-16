from fastapi import FastAPI

app = FastAPI(title="trapr collector")

@app.get("/health")
def health():
    return {"status": "ok"}
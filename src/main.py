from fastapi import FastAPI

app = FastAPI(title="Caja Link", version="1.0.0")


@app.get("/health")
async def health() -> dict:
    return {"status": "UP"}

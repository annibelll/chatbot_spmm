from fastapi import FastAPI
from api.routes.router import router as api_router

app = FastAPI(title="Educational Chat & Quiz API", version="1.0")
app.include_router(api_router)


@app.get("/health")
def health_check():
    return {"status": "ok", "message": "API is running smoothly"}

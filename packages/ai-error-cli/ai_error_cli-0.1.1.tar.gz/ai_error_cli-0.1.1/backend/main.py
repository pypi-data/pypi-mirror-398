#run fast app with: uvicorn main:app --reload

from fastapi import FastAPI
# from backend.routes.error_explainer import router as error_router
from routes.error_explainer import router as error_router

app = FastAPI(
    title="AI Error Explainer API",
    version="1.0.0"
)

@app.get("/")
def root():
    return {"status": "ok"}

app.include_router(error_router)

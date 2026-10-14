
from fastapi import FastAPI

app = FastAPI(title="CyberTalk API")


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

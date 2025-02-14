from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello"}

@app.get("/jobs")
async def get_job():
    return {"message": "Hello"}

async def post():
    pass
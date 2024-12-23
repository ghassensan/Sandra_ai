from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def health_check() -> dict[str, str]:
    return {"message": "👍"}

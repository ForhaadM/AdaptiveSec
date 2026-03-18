from fastapi import FastAPI, Depends
from auth import router as auth_router, get_current_user

app = FastAPI(title="AdaptiveSec API")

app.include_router(auth_router)

@app.get("/protected")
async def protected_route(user_id: str = Depends(get_current_user)):
    return {"message": f"Hello {user_id}, you are authenticated"}

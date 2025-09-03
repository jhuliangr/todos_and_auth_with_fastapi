from fastapi import FastAPI, Depends
from app.routers import todo, auth, user
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from config import Settings, get_settings

Base.metadata.create_all(bind=engine)

def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Test",
        version="1.0.0",
        debug=settings.DEBUG
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )
    app.include_router(user.router, prefix=settings.API_PREFIX)
    app.include_router(auth.router, prefix=settings.API_PREFIX)
    app.include_router(todo.router, prefix=settings.API_PREFIX)
    return app  

app = create_app()

@app.get("/info")
async def info(settings: Settings = Depends(get_settings)):
    return {
        "123123": settings.SECRET_KEY,
        "app_name": "Mi API",
        "debug_mode": settings.DEBUG,
        "api_prefix": settings.API_PREFIX
    }

@app.get("/")
def read_root():
    return {"message": "Welcome to a simple Todo API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
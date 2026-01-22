from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

import app.api.routes.health_routes as health_endpoints
import app.api.routes.auth_routes as auth_endpoints
from app.core.config import settings

app = FastAPI(
    title="FastAPI Boilerplate",
    description="Clean architecture FastAPI boilerplate with authentication",
    version="1.0.0",
    contact={
        "name": "FastAPI Boilerplate",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)

app.include_router(health_endpoints.router)
app.include_router(auth_endpoints.router)

# Configure CORS - in production, replace "*" with specific origins
allowed_origins = ["*"] if settings.APP_DEBUG else ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

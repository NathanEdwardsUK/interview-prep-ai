from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.api.routes import plan, study

# Create database tables (in production, use Alembic migrations)
# Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Interview Prep API",
    description="AI-powered interview preparation platform",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(plan.router, prefix=settings.API_V1_PREFIX)
app.include_router(study.router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    return {"message": "Interview Prep API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

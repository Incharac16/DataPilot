from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import upload, analysis, insights

app = FastAPI(
    title="AI Data Analyst API",
    description="Upload datasets, generate summaries, charts, and AI insights.",
    version="1.0.0",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Allow all origins (development)
    allow_credentials=False,      # Must be False when using "*"
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(upload.router)
app.include_router(analysis.router)
app.include_router(insights.router)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "AI Data Analyst API is running"
    }

# Health check endpoint
@app.get("/health")
async def health():
    return {
        "status": "ok"
    }
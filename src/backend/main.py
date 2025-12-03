from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.backend.routers import activity, attention, analytics, system

app = FastAPI(
    title="DeskBuddy API",
    description="Backend API for DeskBuddy Productivity Companion",
    version="1.0.0"
)

# Configure CORS
# Allow all origins for development (Electron app will likely run on localhost or file://)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(activity.router)
app.include_router(attention.router)
app.include_router(analytics.router)
app.include_router(system.router)

@app.get("/")
async def root():
    return {"message": "Welcome to DeskBuddy API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.backend.main:app", host="0.0.0.0", port=8000, reload=True)

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from mongoDB_pratice.core.services.services import mongo_services
from mongoDB_pratice.constants.app_configurations import HOST, PORT

app = FastAPI(
    title="MongoDB Practice API",
    version="1.0.0"
)

# Include router
app.include_router(mongo_services)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "FastAPI app is running successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=int(PORT), reload=True)
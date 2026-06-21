"""Main FastAPI application"""
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from datetime import datetime

from .presentation.controllers.chat_controller import chat_router
from .presentation.controllers.deeplink_controller import deeplink_router
from .infrastructure.factories.writing_assessment_factory import WritingAssessmentFactory
from .infrastructure.factories.image_description_factory import ImageDescriptionScoringFactory
from .infrastructure.factories.exercise_scoring_factory import ExerciseScoringFactory
from .infrastructure.factories.exercise_generation_factory import ExerciseGenerationFactory
from .infrastructure.factories.roadmap_recommendation_factory import RoadmapRecommendationFactory
from .infrastructure.factories.roadmap_generation_factory import RoadmapGenerationFactory
from .infrastructure.factories.skill_generation_factory import SkillGenerationFactory
from .shared.config import settings
from .infrastructure.database_connection import connect_to_mongo, close_mongo_connection, get_database

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    
    # Initialize RAG service (build/load vectorstore)
    from .infrastructure.external.rag_service import initialize_rag_service
    await initialize_rag_service()
    logger.info("RAG service initialization completed")
    
    # Initialize writing assessment components
    database = await get_database()
    writing_assessment_factory = WritingAssessmentFactory(database)
    writing_assessment_router = writing_assessment_factory.create_router()
    
    # Initialize image description scoring components
    image_description_factory = ImageDescriptionScoringFactory(database)
    image_description_router = image_description_factory.create_router()
    
    # Initialize exercise scoring components
    exercise_scoring_factory = ExerciseScoringFactory(database)
    exercise_scoring_router = exercise_scoring_factory.create_router()

    # Initialize exercise generation components
    exercise_generation_factory = ExerciseGenerationFactory(database)
    exercise_generation_router = exercise_generation_factory.create_router()

    # Initialize roadmap recommendation and generation components
    roadmap_recommendation_factory = RoadmapRecommendationFactory(database)
    roadmap_recommendation_router = roadmap_recommendation_factory.create_router()

    roadmap_generation_factory = RoadmapGenerationFactory(database)
    roadmap_generation_router = roadmap_generation_factory.create_router()

    # Initialize skill generation components
    skill_generation_factory = SkillGenerationFactory(database)
    skill_generation_router = skill_generation_factory.create_router()

    # Initialize all routers after database connection
    app.include_router(chat_router)
    app.include_router(deeplink_router)
    app.include_router(writing_assessment_router)
    app.include_router(image_description_router)
    app.include_router(exercise_scoring_router)
    app.include_router(exercise_generation_router)
    app.include_router(roadmap_recommendation_router)
    app.include_router(roadmap_generation_router)
    app.include_router(skill_generation_router)
    
    logger.info("Application startup completed")
    yield
    await close_mongo_connection()
    logger.info("Application shutdown completed")

app = FastAPI(
    title="VocabuRex Chatbot Service",
    description="AI-powered vocabulary learning chatbot using Gemini API",
    version=settings.service_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# All routers are included in lifespan for consistency

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.service_name,
        "version": settings.service_version,
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "docs": "/docs"
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host=settings.service_host, port=settings.service_port, reload=True)
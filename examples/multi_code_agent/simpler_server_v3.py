import os
from typing import Dict

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.routing import APIRouter
from pydantic import BaseModel
from rest.main import MultiAgentSystem

import traceroot
from traceroot.integrations.fastapi import connect_fastapi
from traceroot.logger import get_logger

# Set up traceroot logging
logger = get_logger()


# Dependency functions
async def get_system():
    """Dependency to provide the MultiAgentSystem"""
    return system


# Initialize FastAPI app
app = FastAPI(title="TraceRoot Multi-Agent Code Server V3")
connect_fastapi(app)
system = MultiAgentSystem()

# Create router with dependencies
router = APIRouter(
    dependencies=[Depends(get_system)]  # Apply system dependency to all routes
)


class CodeRequest(BaseModel):
    query: str


# Route handler using router decorator approach
@router.post("/code")
@traceroot.trace()
async def code_endpoint(
    request: CodeRequest, system: MultiAgentSystem = Depends(get_system)
) -> Dict[str, str]:
    """Process code generation requests"""
    logger.info(f"Code endpoint called with query: {request.query}")
    try:
        result = system.process_query(request.query)
        logger.info("Query processing completed successfully")
        return {"status": "success", "response": result}
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500,
                            detail=f"Query processing failed: {str(e)}")


# Include the router in the main app
app.include_router(router)

if __name__ == "__main__":
    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("Please set your OPENAI_API_KEY environment variable")
        logger.error("You can create a .env file with: "
                     "OPENAI_API_KEY=your_api_key_here")
        exit(1)

    uvicorn.run(app, host="0.0.0.0", port=9999)

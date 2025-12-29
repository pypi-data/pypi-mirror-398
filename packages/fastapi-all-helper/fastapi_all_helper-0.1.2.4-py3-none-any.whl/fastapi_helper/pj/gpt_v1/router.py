from fastapi import APIRouter, Request
from .types import (
    square_types,
    create_chat
)
from .enums import Models
from .schema import (
    SQUARESchema,
    Schema400,
    ChatSchema,
)
from .settings import app_settings


router = APIRouter(
    tags=["🌐CHAT GPT"],
    prefix=app_settings.router_version,
    
)

@router.get('/', responses={
    200: {
        "model": SQUARESchema,
        "description": "Success Response"
    },
    400: {
        "model": Schema400,
        "description": "IP address problem"
    }
})
async def square_api(request: Request):
    """
Retrieve network identification.

This endpoint verifies the connection and returns the client's public 
IP address, which the system uses for access control verification.

Responses:
    200: Successfully returned the IP address.
    400: Problem identifying the host address.
"""

    return await square_types(
        request=request
    )
    
@router.post('/create/chat', responses={
    200: {
        "model": ChatSchema,
        "description": "Success Response"
    },
    400: {
        "model": Schema400,
        "description": "IP address problem"
    }
})
async def create_chat_api(request: Request, model:Models, prompt: str):
    """
Generate a prompt and receive an AI-powered response.

Accepts a text query and dispatches it to the selected AI model. 
In addition to the model's response, it captures the user's IP address 
for validation. This security measure is implemented to prevent 
automated tools from scraping the page or sending unauthorized requests.

Args:
    model: The selected version of the AI model.
    prompt: The text query or instruction for the AI.

Responses:
    200: Successfully generated GPT response.
    400: Access denied (unable to determine IP address).
"""

    return await create_chat(
        request=request,
        model=model,
        prompt=prompt
    )

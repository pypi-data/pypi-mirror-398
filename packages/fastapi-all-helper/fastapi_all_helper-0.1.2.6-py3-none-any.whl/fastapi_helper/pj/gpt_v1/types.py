from g4f.client import AsyncClient
from fastapi import Request, status 
from fastapi.responses import JSONResponse


from .enums import Models

client = AsyncClient()



async def create_chat(request:Request, model: Models, prompt: str) -> JSONResponse:
    """
Sends a user query to the specified AI model and returns the response, 
including the user's IP address.

Verifies the presence of the user's IP address in the request. If the IP 
is not found, it returns a 400 error. Otherwise, it constructs and 
dispatches a request to the model's API and returns the generated response.

Args:
    request: The FastAPI request object used to retrieve the client's IP address.
    model: The Models enumeration indicating which AI model to utilize.
    prompt: A string containing the user's query or instructions for the AI model.

Returns:
    JSONResponse:
        - 200 OK: A JSON object containing the response type ("gpt-response") 
          and the message.
        - 400 Bad Request: A JSON object with an error message if the user's 
          IP address could not be determined.
"""

    if not request.client or request.client.host is None:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "message": "Не удалось извлечь ваш ip адрес"
            }
        )
    response = await client.chat.completions.create(
        model=model.value,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
        
    )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "type": "gpt-response",
            "message": response.choices[0].message.content 
        }
    )



async def square_types(request: Request) -> JSONResponse:
    """
Determines the user's IP address for system identification.

This method extracts the host address from the incoming request. If the IP 
cannot be determined, it returns a 400 error. It serves as a primary 
access check before processing data types.

Args:
    request: The incoming HTTP request object from the user.

Returns:
    JSONResponse: 
        - 200 OK: Contains the user's IP address.
        - 400 Bad Request: Error message indicating the IP could not be retrieved.
"""

    if not request.client or request.client.host is None:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "message": "Не удолось получить ваш IP address"
            }
        )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "ip": request.client.host
        }
    )

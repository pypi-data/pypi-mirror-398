from pydantic import BaseModel


class SQUARESchema(BaseModel):
    """
    Data schema for the /v1/ endpoint response.
    
    Attributes:
        ip: The IP address of the associated node or device.
    """
    ip: str 
    
    
class ChatSchema(BaseModel):
    """
    Chat message schema.
    
    Attributes:
        type: The return value type (fixed to "text").
        message: The GPT chat response content.
    """
    type: str 
    messge: str 
    
class Schema400(BaseModel):
    """
    Schema for request data validation errors.
    
    If the data provided to the endpoint is invalid and cannot be 
    processed by the server, this schema returns a descriptive 
    error message.
    
    Attributes:
        message: A detailed description of the error cause.
    """
    message: str 
from enum import Enum

from ...config import settings

class Models(str, Enum):
    """
Models enumeration.

This class is used to list the supported AI models.

It is utilized in the /v1/create/chat endpoint to ensure 
type safety and ease of use. Instead of manual string entry, 
this class provides a predefined selection for better validation 
and development consistency.
"""

    MODEL_GPT_4 =  settings.gpt_4
    
    
class AppColor(str, Enum):
    """
AppColor enumeration.

This class defines the color palette used for console logging and 
terminal output formatting.
"""
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    RESET = "\033[0m"
    BOLD = "\033[1m"
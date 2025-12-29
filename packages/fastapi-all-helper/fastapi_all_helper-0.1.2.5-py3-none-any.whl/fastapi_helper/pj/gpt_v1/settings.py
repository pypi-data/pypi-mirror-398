import logging


from pydantic import BaseModel
from .enums import AppColor


class AppSettings(BaseModel):
    title: str = "🤖 CHAT GPT APP"
    version: str = "1.0.0"
    router_version: str = "/v1"
    description: str = """
📱 AI Chat Web Application 🤖

This project is a free application designed for easy integration into your services.

Core Endpoints:
    - /v1/ : The project root. Returns your network identification.
      └ Accepts no parameters. Returns your current public IP address.
      └ Returns your local IP address if the application is running on localhost for testing.

    - /v1/chat/create : The main chat generation endpoint.
      └ Uses a predefined enumeration class for AI models (no manual string entry required).
      └ Simply select a model from the list, enter your prompt, and you're all set! ✅
      └ Note: This is the initial version (v1), and more features will be added in future updates.

Enjoy using the app! 🥰
"""
    
    
    
log = logging.getLogger(__name__)


class LifespanHelper:
    """
    Helper class for managing the application lifespan.

    Responsible for initializing resources at startup (such as logging 
    configuration) and ensuring a graceful shutdown of the application.

    Attributes:
        No public instance attributes.
    """

    def __init__(self) -> None:
        """
    Initializes a new instance of LifespanHelper.
        """
        pass
    
    async def start_app(self):
        """
        Starts application initialization and configures logging.

        If the logger is not yet configured, this method creates a custom 
        StreamHandler with color formatting via AppColor. It sets the output 
        format to include: timestamp, log level, logger name, and the message itself.

        Note:
            Utilizes a custom terminal color palette to enhance log 
            readability during development.
        """
        if not log.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f"{AppColor.BLUE.value}%(asctime)s | "
                f"{AppColor.RED.value}   %(levelname)-8s{AppColor.RESET.value}| "
                f" {AppColor.MAGENTA.value}%(name)s {AppColor.RESET.value}| {AppColor.YELLOW.value}%(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            handler.setFormatter(formatter)
            log.addHandler(handler)
            log.setLevel(logging.INFO)
        log.info("START APP")
        
    async def close_app(self):
        """
        Shuts down the application.

        Outputs a final termination message to the terminal.
        """
        log.info("CLOSE APP")
        


app_settings = AppSettings()
lifespan_helper = LifespanHelper()
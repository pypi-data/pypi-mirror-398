import asyncio

from fastapi import FastAPI
import uvicorn

class Client:
    """
A class to manage the FastAPI application lifespan via the Uvicorn server.

Allows for programmatic starting and stopping of the web server 
in asynchronous mode.

Attributes:
    app (FastAPI): The FastAPI application instance.
    host (str): The IP address or hostname to run the server on.
    port (int): The port number where the application will be accessible.
"""

    def __init__(
        self, 
        app: FastAPI,
        host: str = "localhost",
        port: int = 8080,
    ) -> None:
        """
Initializes the client with the server configuration.

Args:
    app (FastAPI): The FastAPI application instance to run.
    host (str): The server host (defaults to "localhost").
    port (int): The server port (defaults to 8080).
"""

        self.app = app
        self.host = host
        self.port = port 
        self._server = None
        
        
    async def start_app(self):
        """
Configures and launches the Uvicorn server.

This method waits for the server to complete its execution. In the event 
of an interruption (Ctrl+C) or task cancellation, it ensures 
a graceful shutdown of the application.
"""

        config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port = self.port,
            log_level="info",
        )
        self._server = uvicorn.Server(config=config)
        try:
            await self._server.serve()
        except (asyncio.CancelledError, KeyboardInterrupt):
            if self._server is not None:
                await self.stop_app()
        
    async def stop_app(self):
        """
Signals the server to shut down and releases system resources.

Verifies whether the server is currently running before attempting to stop it.
"""

        if self._server and self._server.started:
            self._server.should_exit = True
            await self._server.shutdown()
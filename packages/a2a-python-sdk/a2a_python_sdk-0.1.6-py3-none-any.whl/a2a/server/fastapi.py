"""
A2A HTTP Transport Server
------------------------
FastAPI-based HTTP transport for Agent-to-Agent protocol.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional, AsyncGenerator

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse

from a2a.schema.message import A2AMessage, MessageType
from a2a.schema.agent_card import AgentCard
from a2a.server.middleware import security_middleware
from fastapi import FastAPI

# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------

logger = logging.getLogger("a2a.http")
logging.basicConfig(level=logging.INFO)


# ---------------------------------------------------------
# A2A HTTP Server
# ---------------------------------------------------------

class A2AHttpServer:
    def __init__(
        self,
        agent_card: AgentCard,
        *,
        base_path: str = "",
    ):
        self.agent_card = agent_card
        self.base_path = base_path

        self.app = FastAPI(
            title=f"A2A Agent – {agent_card.agent_name}",
            version=agent_card.agent_version,
        )

        self._register_routes()

    # -----------------------------------------------------
    # Route Registration
    # -----------------------------------------------------

    def _register_routes(self):
        app = FastAPI()
        app.middleware("http")(security_middleware)

        @app.get("/.well-known/agent-card.json", response_model=AgentCard)
        async def get_agent_card():
            """
            Agent discovery endpoint
            """
            logger.info("Agent card requested")
            return self.agent_card

        @app.post("/a2a/message")
        async def receive_message(
            message: A2AMessage,
            background_tasks: BackgroundTasks,
            request: Request,
        ):
            """
            Primary A2A message ingress
            """
            logger.info(
                f"A2A message received | type={message.message_type} | "
                f"from={message.sender.agent_id}"
            )

            # ---- Basic validation ----
            if message.message_type not in MessageType:
                raise HTTPException(status_code=400, detail="Invalid message type")

            # ---- Routing by message type ----
            if message.message_type == MessageType.HEARTBEAT:
                return {"status": "alive"}

            if message.message_type == MessageType.CANCEL:
                return self._handle_cancel(message)

            if message.message_type == MessageType.STREAM:
                return StreamingResponse(
                    self._handle_stream(message),
                    media_type="text/plain",
                )

            # ---- Async handling ----
            if message.response and message.response.response_type == "ASYNC":
                background_tasks.add_task(self._process_async, message)
                return JSONResponse(
                    status_code=202,
                    content={
                        "status": "accepted",
                        "message_id": str(message.message_id),
                    },
                )

            # ---- Sync handling ----
            response = await self._process_sync(message)
            return response

        @app.get("/health")
        async def health():
            return {"status": "ok"}

    # -----------------------------------------------------
    # Message Handlers
    # -----------------------------------------------------

    async def _process_sync(self, message: A2AMessage) -> dict:
        """
        Handle synchronous A2A messages
        """
        logger.info(f"Processing SYNC message {message.message_id}")

        # Placeholder for framework execution
        # (CrewAI / LangGraph / custom runtime)
        await asyncio.sleep(0.1)

        return {
            "status": "completed",
            "message_id": str(message.message_id),
            "correlation_id": (
                str(message.correlation_id) if message.correlation_id else None
            ),
        }

    async def _process_async(self, message: A2AMessage):
        """
        Handle asynchronous A2A messages
        """
        logger.info(f"Processing ASYNC message {message.message_id}")

        try:
            await asyncio.sleep(1)  # simulate long task

            if message.response and message.response.callback_url:
                # TODO: send callback message
                logger.info(
                    f"Callback would be sent to {message.response.callback_url}"
                )

        except Exception as e:
            logger.exception("Async processing failed", exc_info=e)

    async def _handle_stream(
        self, message: A2AMessage
    ) -> AsyncGenerator[str, None]:
        """
        Handle streaming responses (LLM tokens, logs, etc.)
        """
        logger.info(f"Streaming for message {message.message_id}")

        for i in range(5):
            yield f"chunk {i}\n"
            await asyncio.sleep(0.5)

        yield "stream_complete\n"

    def _handle_cancel(self, message: A2AMessage) -> dict:
        """
        Handle cancellation requests
        """
        logger.warning(f"Cancellation requested: {message.control}")

        return {
            "status": "cancelled",
            "message_id": str(message.message_id),
        }


# ---------------------------------------------------------
# Factory Helper
# ---------------------------------------------------------

def create_a2a_app(agent_card: AgentCard) -> FastAPI:
    """
    Factory to create FastAPI app
    """
    server = A2AHttpServer(agent_card)
    return server.app

from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass
from typing import AsyncIterator, Optional

try:
    import websockets
except ImportError as exc:  # pragma: no cover - optional dependency
    websockets = None  # type: ignore

from .exceptions import RequestError

DEFAULT_WS_URL = "wss://rhg.openrainbow.io/provisioningapi/graphql"
GRAPHQL_QUERY = (
    "subscription($companyId: String!) { "
    "logsArrived(companyId: $companyId) { "
    "logType callLogs {callId companyId country created_At direction duration endedAt "
    "groupId id memberId rainbowId rainbowRoomId siteId status "
    "calledBy { displayName jid number type } "
    "calledTo { displayName number type jid } "
    "newDest { displayName jid number type } "
    "roomAction { checkinDateTime checkoutDateTime room { tagId } } "
    "} } }"
)


@dataclass
class RainbowWebSocketClient:
    """
    Minimal GraphQL WebSocket client for call log subscriptions.
    Requires the optional `websockets` dependency.
    """

    access_token: str
    app_key: str
    company_id: str
    url: str = DEFAULT_WS_URL
    ping_interval: Optional[int] = 30

    async def subscribe_call_logs(self) -> AsyncIterator[dict]:
        if websockets is None:
            raise RequestError(
                "websockets dependency is missing; install with `pip install rbh-builder-python[ws]`"
            )

        sub_id = f"sub-{uuid.uuid4()}"
        async with websockets.connect(
            self.url,
            subprotocols=["graphql-transport-ws"],
            ping_interval=None,  # We handle ping manually to match API guide.
        ) as ws:
            await ws.send(
                json.dumps(
                    {
                        "id": str(uuid.uuid4()),
                        "type": "connection_init",
                        "payload": {
                            "Authorization": f"Bearer {self.access_token}",
                            "x-app-key": self.app_key,
                        },
                    }
                )
            )
            # Wait for ack
            ack = json.loads(await ws.recv())
            if ack.get("type") != "connection_ack":
                raise RequestError(f"Unexpected handshake response: {ack}")

            await ws.send(
                json.dumps(
                    {
                        "id": sub_id,
                        "type": "subscribe",
                        "payload": {
                            "variables": {"companyId": self.company_id},
                            "extensions": {},
                            "operationName": None,
                            "query": GRAPHQL_QUERY,
                        },
                    }
                )
            )

            ping_task = None
            if self.ping_interval:
                ping_task = asyncio.create_task(self._ping(ws, self.ping_interval))

            try:
                async for raw in ws:
                    message = json.loads(raw)
                    msg_type = message.get("type")
                    if msg_type == "next":
                        yield message.get("payload", {})
                    elif msg_type in ("complete", "error"):
                        break
            finally:
                if ping_task:
                    ping_task.cancel()
                await ws.send(json.dumps({"id": sub_id, "type": "complete"}))

    @staticmethod
    async def _ping(ws, interval: int) -> None:
        while True:
            await asyncio.sleep(interval)
            await ws.send(json.dumps({"type": "ping"}))

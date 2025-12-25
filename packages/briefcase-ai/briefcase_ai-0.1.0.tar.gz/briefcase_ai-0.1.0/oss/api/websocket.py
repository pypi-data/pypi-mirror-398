"""
WebSocket Module

Real-time updates for snapshots, replay events, and system notifications.
"""

import json
import logging
from typing import Dict, List, Set
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class WebSocketMessage(BaseModel):
    """WebSocket message format."""
    type: str  # "snapshot_created", "replay_started", "replay_completed", "error", etc.
    timestamp: datetime
    data: dict
    user_id: str = None

class ConnectionManager:
    """Manages WebSocket connections and message broadcasting."""

    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Store connections by subscription topics
        self.topic_subscriptions: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = []

        self.active_connections[user_id].append(websocket)
        logger.info(f"WebSocket connected for user: {user_id}")

        # Send welcome message
        await self.send_personal_message({
            "type": "connection_established",
            "timestamp": datetime.now().isoformat(),
            "data": {"message": "Connected to briefcase-ai real-time updates"}
        }, websocket)

    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove a WebSocket connection."""
        if user_id in self.active_connections:
            try:
                self.active_connections[user_id].remove(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
            except ValueError:
                pass  # Connection already removed

        # Remove from topic subscriptions
        for topic, subscribers in self.topic_subscriptions.items():
            subscribers.discard(user_id)

        logger.info(f"WebSocket disconnected for user: {user_id}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_text(json.dumps(message, default=str))
        except Exception as e:
            logger.error(f"Error sending message: {e}")

    async def send_message_to_user(self, message: dict, user_id: str):
        """Send a message to all connections of a specific user."""
        if user_id in self.active_connections:
            disconnected = []
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_text(json.dumps(message, default=str))
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {e}")
                    disconnected.append(websocket)

            # Clean up disconnected websockets
            for ws in disconnected:
                self.disconnect(ws, user_id)

    async def broadcast_message(self, message: dict):
        """Broadcast a message to all connected users."""
        for user_id in list(self.active_connections.keys()):
            await self.send_message_to_user(message, user_id)

    async def broadcast_to_topic(self, message: dict, topic: str):
        """Broadcast a message to all users subscribed to a topic."""
        if topic in self.topic_subscriptions:
            for user_id in self.topic_subscriptions[topic]:
                await self.send_message_to_user(message, user_id)

    def subscribe_to_topic(self, user_id: str, topic: str):
        """Subscribe a user to a topic."""
        if topic not in self.topic_subscriptions:
            self.topic_subscriptions[topic] = set()
        self.topic_subscriptions[topic].add(user_id)

    def unsubscribe_from_topic(self, user_id: str, topic: str):
        """Unsubscribe a user from a topic."""
        if topic in self.topic_subscriptions:
            self.topic_subscriptions[topic].discard(user_id)

# Global connection manager instance
manager = ConnectionManager()

# Router for WebSocket endpoints
router = APIRouter()

@router.websocket("/live")
async def websocket_endpoint(
    websocket: WebSocket,
    user_id: str = Query(..., description="User identifier for the connection")
):
    """
    WebSocket endpoint for real-time updates.

    Topics available for subscription:
    - snapshots: New snapshots and snapshot updates
    - replay: Replay events and status updates
    - policies: Policy changes and violations
    - system: System-wide notifications
    """
    await manager.connect(websocket, user_id)

    try:
        while True:
            # Receive messages from client (for subscriptions, etc.)
            data = await websocket.receive_text()
            message = json.loads(data)

            message_type = message.get("type")
            if message_type == "subscribe":
                topic = message.get("topic")
                if topic:
                    manager.subscribe_to_topic(user_id, topic)
                    await manager.send_personal_message({
                        "type": "subscription_confirmed",
                        "timestamp": datetime.now().isoformat(),
                        "data": {"topic": topic}
                    }, websocket)

            elif message_type == "unsubscribe":
                topic = message.get("topic")
                if topic:
                    manager.unsubscribe_from_topic(user_id, topic)
                    await manager.send_personal_message({
                        "type": "unsubscription_confirmed",
                        "timestamp": datetime.now().isoformat(),
                        "data": {"topic": topic}
                    }, websocket)

            elif message_type == "ping":
                await manager.send_personal_message({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat(),
                    "data": {}
                }, websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)

# Utility functions for other modules to send real-time updates
class WebSocketManager:
    """Wrapper class for easy access to WebSocket functionality."""

    @staticmethod
    async def notify_snapshot_created(snapshot_id: str, user_id: str = None):
        """Notify about a new snapshot."""
        message = {
            "type": "snapshot_created",
            "timestamp": datetime.now().isoformat(),
            "data": {"snapshot_id": snapshot_id}
        }

        if user_id:
            await manager.send_message_to_user(message, user_id)
        else:
            await manager.broadcast_to_topic(message, "snapshots")

    @staticmethod
    async def notify_replay_started(replay_id: str, user_id: str = None):
        """Notify about replay start."""
        message = {
            "type": "replay_started",
            "timestamp": datetime.now().isoformat(),
            "data": {"replay_id": replay_id}
        }

        if user_id:
            await manager.send_message_to_user(message, user_id)
        else:
            await manager.broadcast_to_topic(message, "replay")

    @staticmethod
    async def notify_replay_completed(replay_id: str, success: bool, user_id: str = None):
        """Notify about replay completion."""
        message = {
            "type": "replay_completed",
            "timestamp": datetime.now().isoformat(),
            "data": {"replay_id": replay_id, "success": success}
        }

        if user_id:
            await manager.send_message_to_user(message, user_id)
        else:
            await manager.broadcast_to_topic(message, "replay")

    @staticmethod
    async def notify_policy_violation(policy_id: str, violation_details: dict, user_id: str = None):
        """Notify about policy violation."""
        message = {
            "type": "policy_violation",
            "timestamp": datetime.now().isoformat(),
            "data": {"policy_id": policy_id, "violation": violation_details}
        }

        if user_id:
            await manager.send_message_to_user(message, user_id)
        else:
            await manager.broadcast_to_topic(message, "policies")

    @staticmethod
    async def notify_system_event(event_type: str, details: dict):
        """Notify about system-wide events."""
        message = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": details
        }
        await manager.broadcast_to_topic(message, "system")

# Export the manager for use in other modules
websocket_manager = WebSocketManager()

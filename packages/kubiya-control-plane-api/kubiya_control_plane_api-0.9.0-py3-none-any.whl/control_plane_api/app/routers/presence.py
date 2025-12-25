from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session
from typing import List, Dict, Set
from datetime import datetime, timedelta
from pydantic import BaseModel
import json
import asyncio

from control_plane_api.app.database import get_db
from control_plane_api.app.models.presence import UserPresence

router = APIRouter()

# WebSocket connection manager for real-time presence updates
class ConnectionManager:
    def __init__(self):
        # agent_id -> set of websocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, agent_id: str):
        await websocket.accept()
        if agent_id not in self.active_connections:
            self.active_connections[agent_id] = set()
        self.active_connections[agent_id].add(websocket)

    def disconnect(self, websocket: WebSocket, agent_id: str):
        if agent_id in self.active_connections:
            self.active_connections[agent_id].discard(websocket)
            if not self.active_connections[agent_id]:
                del self.active_connections[agent_id]

    async def broadcast_to_agent(self, agent_id: str, message: dict):
        """Broadcast presence update to all users watching this agent"""
        if agent_id in self.active_connections:
            dead_connections = set()
            for connection in self.active_connections[agent_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    dead_connections.add(connection)

            # Clean up dead connections
            for conn in dead_connections:
                self.active_connections[agent_id].discard(conn)

manager = ConnectionManager()


# Pydantic schemas
class PresenceUpdate(BaseModel):
    user_id: str
    user_email: str | None = None
    user_name: str | None = None
    user_avatar: str | None = None
    agent_id: str | None = None
    session_id: str | None = None
    execution_id: str | None = None
    is_typing: bool = False

class PresenceResponse(BaseModel):
    id: str
    user_id: str
    user_email: str | None
    user_name: str | None
    user_avatar: str | None
    agent_id: str | None
    session_id: str | None
    execution_id: str | None
    is_active: bool
    is_typing: bool
    last_active_at: datetime

    class Config:
        from_attributes = True


@router.websocket("/ws/{agent_id}")
async def websocket_presence(
    websocket: WebSocket,
    agent_id: str,
    user_id: str,
    user_email: str | None = None,
    user_name: str | None = None,
    user_avatar: str | None = None,
):
    """WebSocket endpoint for real-time presence updates"""
    await manager.connect(websocket, agent_id)

    # Get database session
    db = next(get_db())

    # Create or update presence record
    presence = db.query(UserPresence).filter(
        UserPresence.user_id == user_id,
        UserPresence.agent_id == agent_id
    ).first()

    if not presence:
        presence = UserPresence(
            user_id=user_id,
            user_email=user_email,
            user_name=user_name,
            user_avatar=user_avatar,
            agent_id=agent_id,
            is_active=True
        )
        db.add(presence)
    else:
        presence.is_active = True
        presence.last_active_at = datetime.utcnow()

    db.commit()

    # Broadcast join event to other users
    await manager.broadcast_to_agent(agent_id, {
        "type": "user_joined",
        "user": {
            "user_id": user_id,
            "user_email": user_email,
            "user_name": user_name,
            "user_avatar": user_avatar,
        }
    })

    try:
        # Keep connection alive and handle messages
        while True:
            data = await websocket.receive_json()

            # Update presence based on message type
            if data.get("type") == "typing_start":
                presence.is_typing = True
            elif data.get("type") == "typing_stop":
                presence.is_typing = False
            elif data.get("type") == "heartbeat":
                presence.last_active_at = datetime.utcnow()

            db.commit()

            # Broadcast to other users
            await manager.broadcast_to_agent(agent_id, {
                "type": data.get("type"),
                "user_id": user_id,
                "user_name": user_name
            })

    except WebSocketDisconnect:
        # Mark user as inactive
        presence.is_active = False
        presence.is_typing = False
        db.commit()

        # Broadcast leave event
        await manager.broadcast_to_agent(agent_id, {
            "type": "user_left",
            "user_id": user_id
        })

        manager.disconnect(websocket, agent_id)
    finally:
        db.close()


@router.post("/heartbeat", status_code=status.HTTP_200_OK)
def update_presence_heartbeat(
    presence_update: PresenceUpdate,
    db: Session = Depends(get_db)
):
    """HTTP endpoint for updating presence (fallback for non-WebSocket)"""
    presence = db.query(UserPresence).filter(
        UserPresence.user_id == presence_update.user_id,
        UserPresence.agent_id == presence_update.agent_id
    ).first()

    if not presence:
        presence = UserPresence(
            user_id=presence_update.user_id,
            user_email=presence_update.user_email,
            user_name=presence_update.user_name,
            user_avatar=presence_update.user_avatar,
            agent_id=presence_update.agent_id,
            session_id=presence_update.session_id,
            execution_id=presence_update.execution_id,
            is_active=True,
            is_typing=presence_update.is_typing
        )
        db.add(presence)
    else:
        presence.last_active_at = datetime.utcnow()
        presence.is_active = True
        presence.is_typing = presence_update.is_typing

    db.commit()

    return {"status": "ok"}


@router.get("/agent/{agent_id}", response_model=List[PresenceResponse])
def get_agent_presence(
    agent_id: str,
    db: Session = Depends(get_db)
):
    """Get all active users for an agent"""
    # Clean up stale presence records (older than 5 minutes)
    stale_cutoff = datetime.utcnow() - timedelta(minutes=5)
    db.query(UserPresence).filter(
        UserPresence.agent_id == agent_id,
        UserPresence.last_active_at < stale_cutoff
    ).update({"is_active": False})
    db.commit()

    # Get active presence records
    presences = db.query(UserPresence).filter(
        UserPresence.agent_id == agent_id,
        UserPresence.is_active == True
    ).all()

    return presences


@router.delete("/leave", status_code=status.HTTP_204_NO_CONTENT)
def leave_presence(
    user_id: str,
    agent_id: str,
    db: Session = Depends(get_db)
):
    """Mark user as inactive for an agent"""
    db.query(UserPresence).filter(
        UserPresence.user_id == user_id,
        UserPresence.agent_id == agent_id
    ).update({"is_active": False, "is_typing": False})
    db.commit()

    return None

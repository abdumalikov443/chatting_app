from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from dataclasses import dataclass
from typing import Dict
import uuid
import json


template = Jinja2Templates(directory="templates")


@dataclass
class ConnectionManager:
    def __init__(self) -> None:
        self.active_connection: dict = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        id = str(uuid.uuid4())

        self.active_connection[id] = websocket
        data = json.dumps({"isMe": True, "data": "Have joined", "username": "You"})
        await self.send_message(websocket, data)

    async def send_message(self, w: WebSocket, message: str):
        await w.send_text(message)

    async def broadcast(self, w: WebSocket, data: str):
        decoded_data = json.loads(data)

        for connection in self.active_connection.values():
            is_me = False
            if connection == w:
                is_me = True

            await connection.send_text(json.dumps({"isMe": is_me, "data": decoded_data['message'], "username": decoded_data['username']}))

    def find_id(self, w: WebSocket):
        # Iterate and find the id of the websocket
        websocket_list = list(self.active_connection.values())
        id_list = list(self.active_connection.keys())

        position = websocket_list.index(w)
        return id_list[position]

    async def disconnect(self, w: WebSocket):
        id = self.find_id(WebSocket)
        del self.active_connection[id]


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")



@app.get("/", response_class=HTMLResponse)
async def get(request: Request):
    return template.TemplateResponse("main.html", {"request":request, "title": "Chat app 1"})


connection_manager = ConnectionManager()


@app.websocket("/message")
async def websocket_endpoint(websocket: WebSocket):
    await connection_manager.connect(websocket)
   
    try:
       while True:
           #Receive the text from users
            data = await websocket.receive_text()
            await connection_manager.broadcast(websocket, data)
    except WebSocketDisconnect:
       await connection_manager.disconnect(websocket)
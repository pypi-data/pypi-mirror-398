import asyncio
from typing import Any, Dict, Tuple

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, Response
from starlette.staticfiles import StaticFiles


class WebSocketManager:
    """
    Manages WebSocket connections and broadcasts update notifications
    triggered by the Plate.
    """

    def __init__(self, plate):
        self.plate = plate
        self.connections: Dict[WebSocket, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, cake_name: str):
        await websocket.accept()
        self.connections[websocket] = {
            "update_event": asyncio.Event(),
            "cake": cake_name,
        }

    async def disconnect(self, websocket: WebSocket):
        if websocket in self.connections:
            self.connections.pop(websocket, None)
        try:
            await websocket.close()
        except Exception:
            pass

    def set_cake(self, websocket: WebSocket, cake_name: str):
        if websocket in self.connections:
            self.connections[websocket]["cake"] = cake_name

    def notify_update(self):
        for connection in self.connections.values():
            connection["update_event"].set()

    async def push_updates(self, websocket: WebSocket):
        """
        Wait for update notifications and push diffs for the current cake.
        """
        while True:
            if websocket not in self.connections:
                return
            update_event = self.connections[websocket]["update_event"]
            try:
                await update_event.wait()
            except asyncio.CancelledError:
                return
            update_event.clear()
            cake_name = self.connections[websocket]["cake"]
            if cake_name not in self.plate.cakes:
                cake_name = self.plate.default_cake
            try:
                payload = self.plate.make_response(cake_name)
                await websocket.send_json({"type": "updates", **payload})
            except WebSocketDisconnect:
                return
            except Exception:
                self.plate.logger.exception("Failed to push WebSocket updates")
                return


class FastAPIServer:
    """
    Thin wrapper that owns the FastAPI app, WebSocket endpoint,
    and HTTP routes. Keeps Pancake's core logic decoupled from the web framework.
    """

    def __init__(self, plate, static_dir: str):
        self.plate = plate
        self.app = FastAPI()
        self.app.mount("/static", StaticFiles(directory=static_dir), name="static")
        self.ws_manager = WebSocketManager(self.plate)
        self._register_routes()

    def notify_update(self):
        self.ws_manager.notify_update()

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    async def _parse_json_request(
        self, request: Request
    ) -> Tuple[Dict[str, Any] | None, Response | None]:
        try:
            request_json = await request.json()
        except Exception:
            self.plate.logger.exception("Invalid JSON payload")
            return None, self._error("JSON cannot be parsed")
        return request_json, None

    @staticmethod
    def _ok(**kwargs):
        response = {"status": "ok"}
        response.update(kwargs)
        return JSONResponse(response)

    @staticmethod
    def _error(message: str):
        return JSONResponse({"status": "error", "msg": message})

    # ------------------------------------------------------------------ #
    # Routes
    # ------------------------------------------------------------------ #
    def _register_routes(self):
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            default_cake = (
                self.plate.current_cake_name
                if self.plate.current_cake_name
                else self.plate.default_cake
            )
            await self.ws_manager.connect(websocket, default_cake)
            update_task = asyncio.create_task(self.ws_manager.push_updates(websocket))
            try:
                while True:
                    data = await websocket.receive_json()
                    message_type = data.get("type")

                    if message_type == "event":
                        topping_id = data.get("topping_id")
                        event_type = data.get("event_name")
                        params = data.get("params", {})
                        request_id = data.get("request_id")
                        cake_name = data.get("cake")
                        if cake_name not in self.plate.cakes:
                            await websocket.send_json({"type": "error", "msg": "Cake not found"})
                            continue
                        cake = self.plate.cakes[cake_name]
                        event = self.plate.Event(topping_id, event_type, params, cake)
                        if topping_id.startswith("_plate_."):
                            response = self.plate.cake.process_event(event)
                        else:
                            response = cake.process_event(event)
                        response_dict = self.plate.make_response(cake_name)
                        if response is not None:
                            response_dict["response"] = response
                        if request_id is not None:
                            response_dict["request_id"] = request_id
                        await websocket.send_json({"type": "updates", **response_dict})

                    elif message_type == "value_changed":
                        cake_name = data.get("cake")
                        value_dict = data.get("values", {})
                        if cake_name not in self.plate.cakes:
                            await websocket.send_json({"type": "error", "msg": "Cake not found"})
                            continue
                        cake = self.plate.cakes[cake_name]
                        plate_value_dict = {k: v for k, v in value_dict.items() if k.startswith("_plate_.")}
                        cake_value_dict = {k: v for k, v in value_dict.items() if not k.startswith("_plate_.")}
                        self.plate.cake.reflect_change_value(plate_value_dict, cake)
                        cake.reflect_change_value(cake_value_dict, cake)
                        response_dict = self.plate.make_response(cake_name)
                        await websocket.send_json({"type": "updates", **response_dict})

                    elif message_type == "go_to":
                        cake_name = data.get("cake", "")
                        request_payload = data.get("request", {})
                        if cake_name not in self.plate.cakes:
                            if cake_name != "-" and (len(cake_name) > 0 or len(self.plate.cakes) == 0):
                                await websocket.send_json(
                                    {"type": "error", "msg": "Cake not found"}
                                )
                                continue
                            cake_name = self.plate.default_cake
                        self.plate.current_cake_name = cake_name
                        self.ws_manager.set_cake(websocket, cake_name)
                        response = {"status": "ok", "cake": cake_name}
                        self.plate.organize_commands(remove_refresh=True)
                        mycake_response = self.plate.cake.render()
                        cake_response = self.plate.cakes[cake_name].render(request_payload)
                        for key in ["content", "floating_content", "function_call"]:
                            cake_response[key] = mycake_response[key] + cake_response[key]
                        for key in ["revisions"]:
                            cake_response[key].update(mycake_response[key])
                        response.update(cake_response)
                        self.plate.update_needed(False)
                        await websocket.send_json({"type": "go_to_response", **response})

                    elif message_type == "revision":
                        cake_name = data.get("cake")
                        targets = data.get("targets", [])
                        if cake_name not in self.plate.cakes:
                            cake_name = self.plate.default_cake
                        cake = self.plate.cakes[cake_name]
                        response = self.plate.cake.revised_rendering(targets)
                        response.update(cake.revised_rendering(targets))
                        await websocket.send_json({"type": "revision_payload", "payload": response})

                    else:
                        await websocket.send_json(
                            {"type": "error", "msg": "Unknown message type"}
                        )
            except WebSocketDisconnect:
                pass
            except Exception:
                self.plate.logger.exception("WebSocket error")
            finally:
                update_task.cancel()
                await self.ws_manager.disconnect(websocket)

        @self.app.get("/")
        async def render():
            html = self.plate.render()
            return Response(content=html, media_type="text/html")

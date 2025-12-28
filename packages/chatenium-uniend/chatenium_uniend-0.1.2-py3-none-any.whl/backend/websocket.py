import json
import threading
from dataclasses import dataclass, asdict, is_dataclass
from typing import Optional, Callable, Dict, Type, List

import rel

from backend.http import Http, HttpMethod, ResultType, Result
from backend.session_manager import SessionManager
from backend.environments import Environments
import websocket

class WebSocket(object):
    _instance = None
    _websocket: Optional[websocket.WebSocketApp] = None
    _listeners: Dict[str, List[tuple[Type, Callable]]] = {}
    connectionId: Optional[str] = None

    # _listeners: List[Callable[[List[Chat]], None]] = []

    def __init__(self):
        raise RuntimeError('Call instance() instead')

    @classmethod
    def instance(cls):
        if cls._instance is None:
            print('Creating new WebSocket instance.')
            cls._instance = cls.__new__(cls)

        return cls._instance

    @classmethod
    def on(cls, action: str, data_cls: Type):
        if not is_dataclass(data_cls):
            raise TypeError(f"data_cls is not a dataclass")

        print("Registered decorator listener")

        def decorator(func: Callable):
            cls._listeners.setdefault(action, []).append((data_cls, func))
            print(cls._listeners)
            return func

        return decorator

    @classmethod
    def on_message(cls, ws, message):
        print("Got WebSocket Message")

        decodedPayload = WSPayload(**json.loads(message))
        if decodedPayload.action == "connectionId":
            cls.connectionId = ConnectionIdData(**json.loads(decodedPayload.data)).connId
            print("ConnectionId set successfully. Connection success.")

        listeners = cls._listeners.get(decodedPayload.action)
        if not listeners:
            return

        for data_cls, handler in listeners:
            try:
                data = data_cls(**json.loads(decodedPayload.data))
                handler(data)
            except Exception as e:
                print(f"WebSocket Listener Error: {e}")

    @staticmethod
    def on_error(ws, error):
        print(error)

    @staticmethod
    def on_close(ws, close_status_code, close_msg):
        print("### closed ###")

    @staticmethod
    def on_open(ws):
        print("Opened connection")

    @classmethod
    async def connect(cls):
        from backend.chat.dm.dm_handler import DmHandler # Register listeners
        if SessionManager.instance().currentSession is None:
            raise ValueError("WebSocket connection failed -- No session")

        result = await Http(
            HttpMethod.POST,
            "v2/ws/makeToken",
            asdict(WSMakeTokenReq(userid=SessionManager.instance().currentSession[1].userid)),
            WSMakeTokenResp,
        )

        if result.type == ResultType.ERROR:
            raise ValueError(result.error)

        print("Token generation ok, connecting to WebSocket.")

        cls._websocket = websocket.WebSocketApp(f"{Environments.instance().ws_url}/v2/ws?access_token={result.success.token}&userid={SessionManager.instance().currentSession[1].userid}",
                on_message=cls.on_message,
                on_open=cls.on_open,
                on_error=cls.on_error,
                on_close=cls.on_close
        )

        def run_ws():
            cls._websocket.run_forever()

        ws_thread = threading.Thread(target=run_ws, daemon=True)
        ws_thread.start()

@dataclass()
class WSMakeTokenReq:
    userid: str

@dataclass()
class WSMakeTokenResp:
    token: str

@dataclass()
class WSPayload:
    action: str
    data: str
    sender: Optional[str] = None

@dataclass()
class ConnectionIdData:
    connId: str

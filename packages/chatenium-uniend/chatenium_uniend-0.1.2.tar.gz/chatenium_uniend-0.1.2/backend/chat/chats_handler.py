from typing import List, Callable, Optional

from backend.http import Http, HttpMethod, ResultType
from backend.session_manager import SessionManager
from dataclasses import dataclass

@dataclass()
class Chat:
    userid: str
    chatid: str
    username: str
    displayName: str
    pfp: str
    status: int
    pinnedMessages: str
    type: str
    muted: bool
    notifications: Optional[int] = 0

class ChatsHandler(object):
    _instance = None
    _listeners: List[Callable[[List[Chat]], None]] = []

    def __init__(self):
        raise RuntimeError('Call instance() instead')

    @classmethod
    def instance(cls):
        if cls._instance is None:
            print('Creating new instance')
            cls._instance = cls.__new__(cls)
        return cls._instance

    @classmethod
    def subscribe(cls, listener: Callable[[Chat], None]):
        cls._listeners.append(listener)

    @classmethod
    def unsubscribe(cls, listener: Callable[[Chat], None]):
        cls._listeners.remove(listener)

    @classmethod
    def _notify(cls, chats: List[Chat]):
        for fn in cls._listeners:
            fn(chats)

    async def getChats(self) -> List[Chat]:
        if SessionManager.instance().currentSession is None:
            raise ValueError("No session")

        result = await Http(
            HttpMethod.GET,
            f"chat/get?userid={SessionManager.instance().currentSession[1].userid}",
            None,
            Chat,
        )

        if result.type == ResultType.SUCCESS:
            self._notify(result.success)
            return result.success
        else:
            raise ValueError(result.error)

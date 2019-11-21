from typing import Optional, List
from threading import Lock
from collections import defaultdict
from enum import Enum
import pickle
import copy
from redis.client import Redis
import logging

__all__ = ['SubscriptionType', 'Subscription']

logger = logging.getLogger(__name__)

SUBSCRIBES_KEY = "subscribes"


class SubscriptionType(Enum):
    AI_FORUM = "ai_forum"


class Subscription:
    def __init__(self, chat_id, stype: SubscriptionType, data: Optional[dict] = None):
        self.type = stype
        self.chat_id = chat_id
        self.data = data

    def __str__(self):
        return f"Subscription<{self.type} {self.chat_id} {self.data}>"

class Subscriber:
    """
    Manges user subscriptions and store them on redis if specified.
    """

    def __init__(self, redis_storage: Redis):
        self._lock = Lock()
        self._storage = redis_storage
        self._subs_by_chat = defaultdict(dict)
        self._subs_by_type = defaultdict(dict)

        if self._storage:
            known_chats = self._storage.hkeys(SUBSCRIBES_KEY)
            logger.info(f"Known chats {len(known_chats)}")
            for chat_id in known_chats:
                chat_id = chat_id.decode("utf-8")
                chat_subs = self._storage.hget(SUBSCRIBES_KEY, chat_id)
                self._subs_by_chat[chat_id] = pickle.loads(chat_subs)
                for sub_type, sub_data in self._subs_by_chat[chat_id].items():
                    self._subs_by_type[sub_type][chat_id] = sub_data

    def add_sub(self, chat_id, stype: SubscriptionType, data: Optional[dict] = None):
        with self._lock:
            chat_id = str(chat_id)
            if stype.value in self._subs_by_chat[chat_id]:
                return False

            stype = stype.value
            data = copy.deepcopy(data)
            self._subs_by_chat[chat_id][stype] = data
            self._subs_by_type[stype][chat_id] = data

            if self._storage:
                self._storage.hset(SUBSCRIBES_KEY, chat_id, pickle.dumps(self._subs_by_chat[chat_id]))
            return True

    def remove_sub(self, chat_id, stype: SubscriptionType):
        with self._lock:
            chat_id = str(chat_id)
            if stype.value not in self._subs_by_chat[chat_id]:
                return False
            stype = stype.value
            del self._subs_by_chat[chat_id][stype]
            del self._subs_by_type[stype][chat_id]

            if self._storage:
                self._storage.hset(SUBSCRIBES_KEY, chat_id, pickle.dumps(self._subs_by_chat[chat_id]))
            return True

    def update_sub(self, chat_id, stype: SubscriptionType, data: Optional[dict] = None):
        with self._lock:
            chat_id = str(chat_id)
            if stype.value not in self._subs_by_chat[chat_id]:
                return False
            stype = stype.value
            data = copy.deepcopy(data)
            self._subs_by_chat[chat_id][stype] = data
            self._subs_by_type[stype][chat_id] = data

            if self._storage:
                self._storage.hset(SUBSCRIBES_KEY, chat_id, pickle.dumps(self._subs_by_chat[chat_id]))
            return True

    def get_subs_by_chat(self, chat_id) -> List[Subscription]:
        with self._lock:
            chat_id = str(chat_id)
            subs = []
            for stype, data in self._subs_by_chat[chat_id].items():
                subs.append(Subscription(chat_id, SubscriptionType(stype), copy.deepcopy(data)))
            return subs

    def get_subs_by_type(self, stype: SubscriptionType) -> List[Subscription]:
        with self._lock:
            subs = []
            for chat_id, data in self._subs_by_type[stype.value].items():
                subs.append(Subscription(chat_id, stype, copy.deepcopy(data)))
            return subs

    def get_sub(self, chat_id, stype: SubscriptionType) -> Optional[Subscription]:
        with self._lock:
            chat_id = str(chat_id)
            sub = None
            if stype.value in self._subs_by_chat[chat_id]:
                data = copy.deepcopy(self._subs_by_chat[chat_id][stype.value])
                sub = Subscription(chat_id, stype, data)
            return sub

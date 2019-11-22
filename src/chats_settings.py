from threading import Lock
import copy
import logging
import pickle
from redis import Redis
from enum import Enum

logger = logging.getLogger(__name__)

CHATS_SETTINGS_KEY = "chats_settings"


class CupType(Enum):
    AI = "ai"
    ML = "ml"


DEFAULT_CUP = CupType.AI


class ChatSettings:
    def __init__(self):
        self.current_cup = DEFAULT_CUP


class ChatSettingsStorage:
    def __init__(self, redis_storage: Redis):
        self._lock = Lock()
        self._storage = redis_storage
        self._settings_by_chat = dict()

        if self._storage:
            known_chats = self._storage.hkeys(CHATS_SETTINGS_KEY)
            logger.info(f"Known chats for settings store {len(known_chats)}")
            for chat_id in known_chats:
                chat_id = chat_id.decode("utf-8")
                chat_settings = self._storage.hget(CHATS_SETTINGS_KEY, chat_id)
                self._settings_by_chat[chat_id] = pickle.loads(chat_settings)

    def get_settings(self, chat_id) -> ChatSettings:
        chat_id = str(chat_id)
        settings = self._settings_by_chat.get(chat_id, None)
        if settings is None:
            settings = ChatSettings()
        else:
            settings = copy.deepcopy(settings)
        return settings

    def update_settings(self, chat_id, settings: ChatSettings):
        chat_id = str(chat_id)
        if isinstance(settings, ChatSettings):
            self._settings_by_chat[chat_id] = settings
            if self._storage:
                self._storage.hset(CHATS_SETTINGS_KEY, chat_id, pickle.dumps(settings))
        else:
            logger.error(
                f"Error during chat sttings update - incorrect ct settings type: {type(settings)}")

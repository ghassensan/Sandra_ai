# This can be changed to redis for better scalibity and availablity.
from abc import ABC, abstractmethod
from collections import defaultdict
import datetime
from enum import StrEnum
import typing as t
from uuid import UUID

from pydantic import BaseModel, Field


class ConversationStore(ABC):
    @abstractmethod
    def reset_conversation_store(self) -> None:
        pass

    @abstractmethod
    def add_chat_msg(self, key: UUID, content: str) -> None:
        pass

    @abstractmethod
    def add_user_msg(self, key: UUID, content: str) -> None:
        pass


class Sayer(StrEnum):
    CHAT = "CHATBOT"
    USER = "USER"


class Message(BaseModel):
    timestamp: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))
    sayer: Sayer
    content: str = Field(default="")


class InMemoryConversationStore(ConversationStore, BaseModel):
    store: t.DefaultDict[UUID, list[Message]] = Field(default=defaultdict(list))

    def reset_conversation_store(self) -> None:
        self.store = defaultdict(list)

    def _add(self, key: UUID, msg: Message) -> None:
        self.store[key].append(msg)

    def add_chat_msg(self, key: UUID, content: str) -> None:
        self._add(key, Message(content=content, sayer=Sayer.CHAT))

    def add_user_msg(self, key: UUID, content: str) -> None:
        self._add(key, Message(content=content, sayer=Sayer.USER))

    def get_conversation(self, key: UUID) -> list[Message]:
        return self.store[key]


def get_conversation_store() -> InMemoryConversationStore:
    return InMemoryConversationStore()


app_conversation_store = get_conversation_store()

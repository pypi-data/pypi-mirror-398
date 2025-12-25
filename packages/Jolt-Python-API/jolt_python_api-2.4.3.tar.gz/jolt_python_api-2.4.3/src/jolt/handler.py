from abc import ABC, abstractmethod
from typing import Optional
from .response import JoltErrorResponse, JoltTopicMessage

class JoltMessageHandler(ABC):
    
    @abstractmethod
    def on_ok(self, raw_line: str):
        pass
    
    @abstractmethod
    def on_error(self, error: JoltErrorResponse, raw_line: str):
        pass
    
    @abstractmethod
    def on_topic_message(self, msg: JoltTopicMessage, raw_line: str):
        pass
    
    @abstractmethod
    def on_disconnected(self, cause: Optional[Exception]):
        pass
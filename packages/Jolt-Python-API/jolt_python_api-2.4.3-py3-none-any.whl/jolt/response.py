import json
from typing import Dict, Any
from .exceptions import JoltException

class JoltResponse:
    def __init__(self, raw_data: Dict[str, Any]):
        self._raw_data = raw_data
    
    def get_raw(self) -> Dict[str, Any]:
        return self._raw_data


class JoltOkResponse(JoltResponse):
    def __init__(self, raw_data: Dict[str, Any]):
        super().__init__(raw_data)
    
    def is_ok(self) -> bool:
        return self._raw_data.get("ok", False)
    
    def __str__(self) -> str:
        return f"JoltOkResponse(ok={self.is_ok()})"


class JoltErrorResponse(JoltResponse):
    def __init__(self, raw_data: Dict[str, Any]):
        super().__init__(raw_data)
        self._error = raw_data.get("error", "Unknown error")
    
    def get_error(self) -> str:
        return self._error
    
    def is_ok(self) -> bool:
        return False
    
    def __str__(self) -> str:
        return f"JoltErrorResponse(error={self._error})"
    
    def __repr__(self) -> str:
        return self.__str__()


class JoltTopicMessage(JoltResponse):
    def __init__(self, raw_data: Dict[str, Any]):
        super().__init__(raw_data)
        self._topic = raw_data.get("topic", "")
        self._data = raw_data.get("data", "")
    
    def get_topic(self) -> str:
        return self._topic
    
    def get_data(self) -> str:
        return self._data
    
    def __str__(self) -> str:
        return f"JoltTopicMessage(topic={self._topic}, data={self._data})"
    
    def __repr__(self) -> str:
        return self.__str__()


class JoltResponseParser:
    
    @staticmethod
    def parse(raw_line: str) -> Dict[str, Any]:
        try:
            return json.loads(raw_line)
        except json.JSONDecodeError as e:
            raise JoltException(f"Failed to parse JSON: {e}")
    
    @staticmethod
    def parse_response(raw_line: str) -> JoltResponse:
        data = JoltResponseParser.parse(raw_line)
        
        if "topic" in data and "data" in data:
            return JoltTopicMessage(data)
        
        if "ok" in data and data["ok"] is False:
            return JoltErrorResponse(data)
        
        if "ok" in data and data["ok"] is True:
            return JoltOkResponse(data)
        
        raise JoltException(f"Unknown response format: {raw_line}")
    
    @staticmethod
    def parse_error_response(data: Dict[str, Any]) -> JoltErrorResponse:
        return JoltErrorResponse(data)
    
    @staticmethod
    def parse_topic_message(data: Dict[str, Any]) -> JoltTopicMessage:
        return JoltTopicMessage(data)
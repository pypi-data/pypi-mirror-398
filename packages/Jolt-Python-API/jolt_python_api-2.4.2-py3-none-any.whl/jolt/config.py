class JoltConfig:
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8080):
        self._host = host
        self._port = port
    
    def get_host(self) -> str:
        return self._host
    
    def get_port(self) -> int:
        return self._port
    
    @staticmethod
    def new_builder():
        return JoltConfigBuilder()
    
    def __str__(self) -> str:
        return f"JoltConfig(host={self._host}, port={self._port})"
    
    def __repr__(self) -> str:
        return self.__str__()


class JoltConfigBuilder:
    
    def __init__(self):
        self._host = "127.0.0.1"
        self._port = 8080
    
    def host(self, host: str):
        self._host = host
        return self
    
    def port(self, port: int):
        self._port = port
        return self
    
    def build(self) -> JoltConfig:
        return JoltConfig(self._host, self._port)
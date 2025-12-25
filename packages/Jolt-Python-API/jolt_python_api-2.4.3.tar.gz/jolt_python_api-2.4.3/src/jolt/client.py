import socket
import threading
from typing import Optional
from .config import JoltConfig
from .handler import JoltMessageHandler
from .request import JoltRequestBuilder
from .response import JoltResponseParser, JoltOkResponse, JoltErrorResponse, JoltTopicMessage
from .exceptions import JoltException

class JoltClient:
    
    def __init__(self, config: JoltConfig, handler: JoltMessageHandler):
        self._config = config
        self._handler = handler
        self._socket: Optional[socket.socket] = None
        self._reader_thread: Optional[threading.Thread] = None
        self._running = False
        self._write_lock = threading.Lock()
        self._connected = False
    
    def connect(self):
        if self._connected:
            raise JoltException("Already connected")
        
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(10.0)
            self._socket.connect((self._config.get_host(), self._config.get_port()))
            self._socket.settimeout(None)
            self._connected = True
            self._running = True
            
            self._reader_thread = threading.Thread(target=self._read_loop, daemon=True)
            self._reader_thread.start()
            
        except Exception as e:
            self._connected = False
            raise JoltException(f"Failed to connect: {e}")
    
    def auth(self, username: str, password: str):
        request = JoltRequestBuilder.auth(username, password)
        self._send(request)
    
    def subscribe(self, topic: str):
        request = JoltRequestBuilder.subscribe(topic)
        self._send(request)
    
    def unsubscribe(self, topic: str):
        request = JoltRequestBuilder.unsubscribe(topic)
        self._send(request)
    
    def publish(self, topic: str, data: str):
        request = JoltRequestBuilder.publish(topic, data)
        self._send(request)
    
    def ping(self):
        request = JoltRequestBuilder.ping()
        self._send(request)
    
    def close(self):
        self._running = False
        self._connected = False
        
        if self._socket:
            try:
                self._socket.shutdown(socket.SHUT_RDWR)
            except:
                pass
            try:
                self._socket.close()
            except:
                pass
            self._socket = None
        
        if self._reader_thread and self._reader_thread.is_alive():
            self._reader_thread.join(timeout=2.0)
    
    def is_connected(self) -> bool:
        return self._connected
    
    def _send(self, json_str: str):
        if not self._connected or not self._socket:
            raise JoltException("Not connected")
        
        with self._write_lock:
            try:
                message = json_str.encode('utf-8')
                self._socket.sendall(message)
                # Debug logging (optional)
                # print(f"[SENT] {json_str.rstrip()}")
            except Exception as e:
                self._connected = False
                raise JoltException(f"Failed to send: {e}")
    
    def _read_loop(self):
        buffer = ""
        
        try:
            while self._running and self._connected:
                try:
                    chunk = self._socket.recv(4096)
                    
                    if not chunk:
                        break
                    
                    chunk_str = chunk.decode('utf-8')
                    buffer += chunk_str
                    
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()
                        
                        if line:
                            # Debug logging (optional)
                            # print(f"[RECEIVED] {line}")
                            self._handle_line(line)
                
                except socket.timeout:
                    continue
                except Exception as e:
                    if self._running:
                        self._handler.on_disconnected(e)
                    break
        
        finally:
            self._connected = False
            if self._running:
                self._handler.on_disconnected(None)
    
    def _handle_line(self, raw_line: str):
        try:
            response = JoltResponseParser.parse_response(raw_line)
            
            if isinstance(response, JoltOkResponse):
                self._handler.on_ok(raw_line)
            elif isinstance(response, JoltErrorResponse):
                self._handler.on_error(response, raw_line)
            elif isinstance(response, JoltTopicMessage):
                self._handler.on_topic_message(response, raw_line)
            else:
                pass
        
        except Exception as e:
            pass
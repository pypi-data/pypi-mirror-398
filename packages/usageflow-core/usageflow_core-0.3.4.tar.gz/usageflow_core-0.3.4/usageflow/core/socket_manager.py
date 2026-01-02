import json
import threading
import time
import uuid
from typing import Dict, Any, Optional, Callable
from dataclasses import asdict
import websocket
from usageflow.core.types import UsageFlowSocketMessage, UsageFlowSocketResponse


class PooledConnection:
    """Represents a single WebSocket connection in the pool"""
    def __init__(self, ws: websocket.WebSocketApp, index: int):
        self.ws = ws
        self.connected = False
        self.pending_requests = 0
        self.index = index
        self.message_handlers: Dict[str, Callable] = {}
        self.lock = threading.Lock()


class UsageFlowSocketManager:
    """Manages WebSocket connections with connection pooling"""
    
    def __init__(self, api_key: str, pool_size: int = 10):
        self.api_key = api_key
        self.ws_url = "wss://api.usageflow.io/ws"
        self.pool_size = pool_size if pool_size and pool_size > 0 else 10
        self.current_index = 0
        self.connecting = False
        self.connections: list[PooledConnection] = []
        self.lock = threading.Lock()
        self.connection_promises: list[threading.Event] = []
        
    def _create_connection(self, index: int) -> PooledConnection:
        """Create a new WebSocket connection"""
        if not self.api_key:
            raise ValueError("API key not available")
        
        headers = {
            "x-usage-key": self.api_key
        }
        
        connection_ready = threading.Event()
        connection_error = [None]
        connection_obj = [None]
        
        def on_open(ws):
            with self.lock:
                if connection_obj[0]:
                    connection_obj[0].connected = True
                    print(f"[UsageFlow] WebSocket connection {index + 1}/{self.pool_size} established")
                    connection_ready.set()
        
        def on_error(ws, error):
            print(f"[UsageFlow] WebSocket {index + 1} error: {error}")
            connection_error[0] = error
            with self.lock:
                if connection_obj[0]:
                    connection_obj[0].connected = False
            if not connection_ready.is_set():
                connection_ready.set()
        
        def on_close(ws, close_status_code, close_msg):
            print(f"[UsageFlow] WebSocket connection {index + 1} closed")
            with self.lock:
                if connection_obj[0]:
                    connection_obj[0].connected = False
            # Attempt to reconnect after a delay
            threading.Timer(5.0, lambda: self._reconnect_connection(index)).start()
        
        def on_message(ws, message):
            # Message handling done in _async_send
            with self.lock:
                if connection_obj[0]:
                    try:
                        data = json.loads(message)
                        msg_id = data.get("id") or data.get("replyTo")
                        if msg_id and msg_id in connection_obj[0].message_handlers:
                            handler = connection_obj[0].message_handlers.pop(msg_id)
                            handler(data)
                    except Exception as e:
                        print(f"[UsageFlow] Error processing message: {e}")
        
        ws = websocket.WebSocketApp(
            self.ws_url,
            header=headers,
            on_open=on_open,
            on_error=on_error,
            on_close=on_close,
            on_message=on_message
        )
        
        connection = PooledConnection(ws, index)
        connection_obj[0] = connection
        
        # Start WebSocket in a separate thread
        ws_thread = threading.Thread(target=ws.run_forever, daemon=True)
        ws_thread.start()
        
        # Wait for connection to be established (with timeout)
        if not connection_ready.wait(timeout=10):
            raise TimeoutError(f"WebSocket connection {index + 1} timeout")
        
        if connection_error[0]:
            raise connection_error[0]
        
        return connection
    
    def _reconnect_connection(self, index: int):
        """Reconnect a WebSocket connection"""
        with self.lock:
            existing_connection = None
            for conn in self.connections:
                if conn.index == index:
                    existing_connection = conn
                    break
            
            if existing_connection and existing_connection.connected:
                return  # Already connected
            
            # Clean up old connection
            if existing_connection:
                try:
                    existing_connection.ws.close()
                except Exception:
                    pass
                if existing_connection in self.connections:
                    self.connections.remove(existing_connection)
        
        try:
            new_connection = self._create_connection(index)
            with self.lock:
                # Find the right position to insert
                inserted = False
                for i, conn in enumerate(self.connections):
                    if conn.index > index:
                        self.connections.insert(i, new_connection)
                        inserted = True
                        break
                if not inserted:
                    self.connections.append(new_connection)
                self.connections.sort(key=lambda x: x.index)
        except Exception as error:
            print(f"[UsageFlow] Failed to reconnect WebSocket {index + 1}: {error}")
    
    def connect(self):
        """Establish WebSocket connections"""
        if not self.api_key:
            print("[UsageFlow] Cannot establish WebSocket connection: API key not initialized")
            return
        
        with self.lock:
            if self.connecting:
                # Wait for existing connection attempts
                for event in self.connection_promises:
                    event.wait()
                return
            
            if len(self.connections) > 0 and self.is_connected():
                # Already connected
                return
            
            self.connecting = True
            self.connection_promises = []
        
        try:
            # Create all connections in parallel
            connection_threads = []
            results = {}
            results_lock = threading.Lock()
            
            def create_conn_thread(idx):
                try:
                    conn = self._create_connection(idx)
                    with results_lock:
                        results[idx] = conn
                except Exception as error:
                    print(f"[UsageFlow] Failed to create connection {idx + 1}: {error}")
                    with results_lock:
                        results[idx] = None
            
            for i in range(self.pool_size):
                thread = threading.Thread(target=create_conn_thread, args=(i,), daemon=True)
                thread.start()
                connection_threads.append(thread)
            
            # Wait for all threads to complete
            for thread in connection_threads:
                thread.join(timeout=15)
            
            # Filter out failed connections and store successful ones
            with self.lock:
                self.connections = [
                    results[i] for i in sorted(results.keys())
                    if results[i] is not None
                ]
            
            # Retry failed connections
            for i in range(self.pool_size):
                if i not in results or results[i] is None:
                    threading.Thread(target=self._reconnect_connection, args=(i,), daemon=True).start()
            
            print(f"[UsageFlow] WebSocket pool established: {len(self.connections)}/{self.pool_size} connections")
        finally:
            with self.lock:
                self.connecting = False
                self.connection_promises = []
    
    def _get_connection(self) -> Optional[PooledConnection]:
        """Get a connection from the pool using least-busy strategy"""
        with self.lock:
            if len(self.connections) == 0:
                return None
            
            # Filter to only connected connections
            connected = [
                conn for conn in self.connections
                if conn.connected
            ]
            
            if len(connected) == 0:
                return None
            
            # Use least-busy connection strategy
            selected = connected[0]
            for conn in connected:
                if conn.pending_requests < selected.pending_requests:
                    selected = conn
            
            # If all connections have the same load, use round-robin for better distribution
            same_load = all(conn.pending_requests == selected.pending_requests for conn in connected)
            if same_load and len(connected) > 1:
                self.current_index = (self.current_index + 1) % len(connected)
                selected = connected[self.current_index]
            
            return selected
    
    def send_async(self, payload: UsageFlowSocketMessage) -> UsageFlowSocketResponse:
        """Send a message asynchronously and wait for response"""
        connection = self._get_connection()
        if not connection:
            raise RuntimeError("WebSocket not connected")
        
        return self._async_send(payload, connection)
    
    def send(self, payload: UsageFlowSocketMessage):
        """Send a message without waiting for response"""
        connection = self._get_connection()
        if not connection:
            raise RuntimeError("WebSocket not connected")

        message_dict = asdict(payload)
        # Remove None values
        message_dict = {k: v for k, v in message_dict.items() if v is not None}
        try:
            connection.ws.send(json.dumps(message_dict))
        except Exception as e:
            # Mark connection as disconnected on send error
            with connection.lock:
                connection.connected = False
            raise RuntimeError(f"Failed to send message: {e}") from e
    
    def close(self):
        """Close all WebSocket connections"""
        with self.lock:
            for conn in self.connections:
                try:
                    conn.ws.close()
                except Exception:
                    pass
            self.connections = []
    
    def is_connected(self) -> bool:
        """Check if at least one connection is active"""
        with self.lock:
            return any(
                conn.connected
                for conn in self.connections
            )
    
    def get_ws(self) -> Optional[websocket.WebSocketApp]:
        """Get a WebSocket connection"""
        connection = self._get_connection()
        return connection.ws if connection else None
    
    def _async_send(self, payload: UsageFlowSocketMessage, connection: PooledConnection) -> UsageFlowSocketResponse:
        """Send a message and wait for response"""
        if not connection.ws or not connection.connected:
            raise RuntimeError("WebSocket not connected")
        
        # Increment pending requests counter
        with connection.lock:
            connection.pending_requests += 1
        
        message_id = f"{uuid.uuid4().hex}{int(time.time() * 1000)}"
        message_dict = asdict(payload)
        message_dict["id"] = message_id
        # Remove None values except id
        message_dict = {k: v for k, v in message_dict.items() if v is not None or k == "id"}
        
        response_received = threading.Event()
        response_data = [None]
        response_error = [None]
        timeout_occurred = [False]
        
        def handle_response(data: Dict[str, Any]):
            response_data[0] = data
            response_received.set()
        
        def timeout_handler():
            if not response_received.is_set():
                timeout_occurred[0] = True
                response_error[0] = TimeoutError(f"WebSocket request timeout for id: {message_id}")
                response_received.set()
        
        # Register handler
        with connection.lock:
            connection.message_handlers[message_id] = handle_response
        
        # Set up timeout
        timeout_timer = threading.Timer(30.0, timeout_handler)
        timeout_timer.start()
        
        try:
            # Send message
            try:
                connection.ws.send(json.dumps(message_dict))
            except Exception as send_error:
                # Mark connection as disconnected on send error
                with connection.lock:
                    connection.connected = False
                raise RuntimeError(f"Failed to send message: {send_error}") from send_error

            # Wait for response
            response_received.wait(timeout=30.0)
            
            if timeout_occurred[0]:
                raise response_error[0]
            
            if response_error[0]:
                raise response_error[0]
            
            if response_data[0] is None:
                raise RuntimeError("No response received")
            
            # Only pass known fields to avoid errors with extra fields
            response_dict = response_data[0]
            known_fields = {
                'type', 'payload', 'message', 'error', 'id', 'replyTo'
            }
            filtered_response = {
                k: v for k, v in response_dict.items()
                if k in known_fields
            }
            return UsageFlowSocketResponse(**filtered_response)
        finally:
            timeout_timer.cancel()
            with connection.lock:
                connection.pending_requests -= 1
                if message_id in connection.message_handlers:
                    del connection.message_handlers[message_id]
    
    def destroy(self):
        """Clean up resources including WebSocket connections"""
        self.close()


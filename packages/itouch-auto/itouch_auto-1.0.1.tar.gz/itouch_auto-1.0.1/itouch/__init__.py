import json
import threading
import time
import websocket
from .event import EventEmitter
from .utils import WEBSOCKET_HOST, WEBSOCKET_PORT, RECONNECT_DELAY, MAX_RECONNECT_ATTEMPTS


class ITouchClient:
    def __init__(self, options=None):
        if options is None:
            options = {}
        
        self.wsevents = {}
        self.event_emitter = EventEmitter()
        self.wsclient = None
        self.reconnect_timer = None
        self.closed = False
        self.connected = False
        self.host = options.get('host', WEBSOCKET_HOST)
        self.port = options.get('port', WEBSOCKET_PORT)
        self.auto_reconnect = options.get('autoReconnect', True)
        self.reconnect_delay = options.get('reconnectDelay', RECONNECT_DELAY)
        self.max_reconnect_attempts = options.get('maxReconnectAttempts', MAX_RECONNECT_ATTEMPTS)
        self.reconnect_count = 0
        self._lock = threading.Lock()
        self._connect_event = threading.Event()

    def _reconnect(self):
        if self.closed or not self.auto_reconnect:
            return
        if self.max_reconnect_attempts > 0 and self.reconnect_count >= self.max_reconnect_attempts:
            print(f'[iTouch] Max reconnect attempts ({self.max_reconnect_attempts}) reached, stop reconnecting')
            return
        with self._lock:
            if self.reconnect_timer:
                return
            if self.connected:
                return
            self.reconnect_timer = threading.Timer(self.reconnect_delay, self._do_reconnect)
            self.reconnect_timer.daemon = True
            self.reconnect_timer.start()
    
    def _do_reconnect(self):
        """Internal method to perform reconnection."""
        with self._lock:
            self.reconnect_timer = None
        if not self.closed and not self.connected:
            self.reconnect_count += 1
            if self.max_reconnect_attempts > 0:
                print(f'[iTouch] Attempting to reconnect to ws://{self.host}:{self.port}... ({self.reconnect_count}/{self.max_reconnect_attempts})')
            else:
                print(f'[iTouch] Attempting to reconnect to ws://{self.host}:{self.port}... ({self.reconnect_count})')
            self._connect()

    def _on_message(self, ws, message):
        payload = None
        bindata = None

        try:
            if isinstance(message, str):
                first_byte = ord(message[0]) if message else 0
            else:
                first_byte = message[0] if len(message) > 0 else 0
            
            is_json = first_byte == 0x7B or first_byte == 0x5B  # { or [
            
            if is_json:
                payload = json.loads(message if isinstance(message, str) else message.decode('utf-8'))
            else:
                # binary: [metaDataLength][metaData][binary]
                if isinstance(message, str):
                    message = message.encode('utf-8')
                
                meta_length_str = message[:6].decode('utf-8').strip()
                meta_length_int = int(meta_length_str)
                
                bindata = message[6 + meta_length_int:]
                meta_json = message[6:6 + meta_length_int].decode('utf-8')
                
                payload = json.loads(meta_json)
                payload['data'] = bindata
                bindata = None
        except Exception as error:
            print(f'[iTouch] receive message error: {error}')
            return
        
        if not payload:
            return
        
        event_id = payload.get('evtid')
        event = self.wsevents.get(event_id)
        
        if event:
            if payload.get('type') == 'error':
                event['reject'](Exception(payload.get('error', 'Unknown error')))
            else:
                event['resolve'](payload.get('data'))
            
            del self.wsevents[event_id]
        elif payload.get('event'):
            self.event_emitter.emit(payload['event'], payload.get('data'))

    def _on_error(self, ws, error):
        print(f'[iTouch] WebSocket error: {error}')
        # If not connected yet, trigger reconnect
        if not self.connected and not self.closed:
            # Error during connection, will be handled by close callback
            pass

    def _on_close(self, ws, close_status_code, close_msg):
        was_connected = self.connected
        self.connected = False
        self._connect_event.clear()
        with self._lock:
            self.wsclient = None
        if not self.closed:
            if was_connected:
                print(f'[iTouch] Connection closed, will reconnect in {self.reconnect_delay} seconds...')
            self._reconnect()

    def _on_open(self, ws):
        self.connected = True
        self.reconnect_count = 0  # Reset reconnect count on successful connection
        self._connect_event.set()

    def _connect(self):
        if self.closed:
            return
        
        with self._lock:
            if self.wsclient and self.connected:
                return
            # Clean up old connection if exists
            if self.wsclient:
                try:
                    self.wsclient.close()
                except:
                    pass
                self.wsclient = None
        
        try:
            ws_url = f"ws://{self.host}:{self.port}"
            self._connect_event.clear()
            self.connected = False
            
            self.wsclient = websocket.WebSocketApp(
                ws_url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )
            
            def run_ws():
                try:
                    self.wsclient.run_forever()
                except Exception as e:
                    print(f'[iTouch] WebSocket run error: {e}')
                    if not self.closed:
                        self._on_close(None, None, None)
            
            thread = threading.Thread(target=run_ws, daemon=True)
            thread.start()
        except Exception as e:
            print(f"[iTouch] Connection failed: {e}")
            if not self.closed:
                self._reconnect()

    def connect(self):
        """Connect to WebSocket server."""
        if self.closed:
            raise Exception('client is destroyed')
        
        with self._lock:
            if self.wsclient and self.connected:
                return
        
        self._connect()
        # Wait for connection to establish (max 5 seconds)
        if not self._connect_event.wait(timeout=5):
            # If timeout, don't raise exception if auto_reconnect is enabled
            # Let it reconnect automatically
            if not self.auto_reconnect:
                raise Exception('Connection timeout')

    def invoke(self, type_name, params=None, timeout=18):
        """Invoke an API method."""
        if params is None:
            params = {}
        
        if self.closed:
            raise Exception('client is destroyed')
        
        if not self.wsclient or not self.connected:
            raise Exception('websocket not connected')
        
        import random
        import string
        
        event_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        payload = {
            **params,
            'type': type_name,
            'evtid': event_id,
            'timeout': timeout
        }
        
        future = {'resolve': None, 'reject': None, 'done': False, 'result': None, 'error': None}
        
        def resolve(value):
            future['result'] = value
            future['done'] = True
        
        def reject(error):
            future['error'] = error
            future['done'] = True
        
        future['resolve'] = resolve
        future['reject'] = reject
        
        self.wsevents[event_id] = future
        
        try:
            self.wsclient.send(json.dumps(payload))
        except Exception as e:
            del self.wsevents[event_id]
            raise Exception(f"Send failed: {e}")
        
        if timeout > 0:
            def timeout_handler():
                time.sleep(timeout)
                if event_id in self.wsevents and not self.wsevents[event_id]['done']:
                    self.wsevents[event_id]['reject'](Exception(f'API: {event_id} => {type_name} Invoke Timeout !'))
                    del self.wsevents[event_id]
            
            timeout_thread = threading.Thread(target=timeout_handler, daemon=True)
            timeout_thread.start()
        
        # Wait for response
        start_time = time.time()
        while not future['done'] and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        if future['error']:
            raise future['error']
        
        if not future['done']:
            raise Exception(f'API: {event_id} => {type_name} Invoke Timeout !')
        
        return future['result']

    def on(self, event_name, callback):
        """Register an event listener."""
        self.event_emitter.on(event_name, callback)

    def off(self, event_name, callback=None):
        """Remove an event listener."""
        self.event_emitter.off(event_name, callback)

    def destroy(self):
        """Destroy the client, disconnect and clean up all resources."""
        self.closed = True
        
        if self.reconnect_timer:
            self.reconnect_timer.cancel()
            self.reconnect_timer = None
        
        if self.wsclient:
            self.connected = False
            try:
                self.wsclient.close()
            except:
                pass
            self.wsclient = None
        
        self.event_emitter.clear_all()
        
        for event_id, event in list(self.wsevents.items()):
            if event:
                event['reject'](Exception('itouch client is destroyed'))
        self.wsevents.clear()


# Export ITouchClient as 'client' for convenience
client = ITouchClient

def create_client(options=None):
    """Create a new ITouchClient instance."""
    return ITouchClient(options)

__all__ = ['ITouchClient', 'client', 'create_client']


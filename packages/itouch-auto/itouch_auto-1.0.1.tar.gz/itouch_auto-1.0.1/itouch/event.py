class EventEmitter:
    def __init__(self):
        self._event_listeners = {}

    def on(self, event_name, callback):
        if not callable(callback):
            raise TypeError('callback must be callable')
        if event_name not in self._event_listeners:
            self._event_listeners[event_name] = []
        self._event_listeners[event_name].append(callback)

    def off(self, event_name, callback=None):
        if event_name not in self._event_listeners:
            return
        if callback:
            if callback in self._event_listeners[event_name]:
                self._event_listeners[event_name].remove(callback)
        else:
            del self._event_listeners[event_name]

    def emit(self, event_name, data=None):
        if event_name in self._event_listeners:
            for callback in self._event_listeners[event_name][:]:
                try:
                    callback(data)
                except Exception as error:
                    print(f'[iTouch] 事件监听器执行错误: {error}')

    def clear_all(self):
        self._event_listeners.clear()


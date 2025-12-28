# crystalwindow/messagebus.py

class MessageBus:
    def __init__(self):
        self._queue = []

    def send(self, name: str, data=None):
        self._queue.append({
            "name": name,
            "data": data
        })

    def poll(self, name: str):
        for msg in self._queue:
            if msg["name"] == name:
                self._queue.remove(msg)
                return msg["data"]
        return None

    def clear(self):
        self._queue.clear()


_bus = MessageBus()

def send_message(name: str, data=None):
    _bus.send(name, data)

def view_message(name: str):
    return _bus.poll(name)

def clear_messages():
    _bus.clear()

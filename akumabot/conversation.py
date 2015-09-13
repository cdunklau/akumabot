import collections
import datetime


class Conversation(object):
    def __init__(self, protocol, channel, nickname):
        self.protocol = protocol
        self.channel = channel
        self.nickname = nickname
        self.messages = collections.deque()
        self.last_active = datetime.datetime.now()

    def __nonzero__(self):
        return bool(self.messages)

    def reply(self, message):
        if self.protocol.nickname == self.nickname:
            self.protocol._sendMessage(message, self.nickname)
        else:
            self.protocol._sendMessage(message, self.channel, self.nickname)
        self.last_active = datetime.datetime.now()

    def received(self, message):
        self.messages.appendleft(message)
        self.last_active = datetime.datetime.now()

    def pop_received(self):
        try:
            return self.messages.pop()
        except IndexError:
            return None


class ConversationMap(collections.Mapping):
    """
    Maps (channel, nickname) tuples to Conversation instances.

    Automatically creates keys requested that don't exist.
    Nicks are converted to lowercase.

    Does not support mutation via normal mapping methods.
    """
    def __init__(self, protocol):
        self._protocol = protocol
        self._store = {}

    def expire(self, age):
        """
        Remove conversations older than ``age`` (in seconds).
        """
        now = datetime.datetime.now()
        for key, conversation in list(self.items()):
            if (now - conversation.last_active).total_seconds() < age:
                del self._store[key]

    def __getitem__(self, key):
        channel, nickname = key
        key = channel, nickname.lower()
        if key not in self._store:
            self._store[key] = Conversation(self._protocol, channel, nickname)
        return self._store[key]

    def __len__(self):
        return len(self._store)

    def __iter__(self):
        return iter(self._store)

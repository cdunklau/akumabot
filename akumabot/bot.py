from collections import defaultdict

from twisted.internet import endpoints
from twisted.python import log

from akumabot.commands import CommandProcessor
from akumabot.proto import AkumaBotFactory


class AkumaBot(object):
    def __init__(self, config):
        self.config = config
        self.admins = self.config['akumabot.admins']
        self.command_processor = CommandProcessor(self)
        self.listeners = defaultdict(list)

    def main(self, reactor, description):
        endpoint = endpoints.clientFromString(reactor, description)
        factory = AkumaBotFactory(self.config)
        d = endpoint.connect(factory)
        d.addCallback(self.got_protocol)
        d.addCallback(lambda protocol: protocol.deferred)
        return d

    def add_listener(self, event, listener):
        self.listeners[event].append(listener)

    def _run_listeners(self, event, *args):
        for listener in self.listeners[event]:
            listener(*args)

    def got_protocol(self, protocol):
        self.protocol = protocol
        self.protocol.bot = self
        self.command_processor.add_listeners()
        return protocol

    def disconnect(self):
        self.protocol.transport.loseConnection()

    def leave_channel(self, channel, message=None):
        self.protocol.leave(channel, message)

    def join_channel(self, channel, key=None):
        self.protocol.join(channel, key)

    def send_private_message(self, message, nickname):
        if not message:
            return
        self.protocol.msg(nickname, message)

    def send_channel_message(self, message, channel, nick=None):
        if not message:
            return
        if nick:
            message = '{0}, {1}'.format(nick, message)
        self.protocol.say(channel, message)

    def kick_user(self, channel, user, reason=None):
        self.protocol.kick(channel, user, reason)

    def received_notice(self, nickname, channel, message):
        pass

    def kicked(self, channel, kicker, message):
        pass

    def received_message(self, nickname, channel, message):
        self._run_listeners('received_message', nickname, channel, message)

    def received_private_message(self, nickname, message):
        self._run_listeners('received_private_message', nickname, message)

    def user_joined(self, user, channel):
        pass

    def user_left(self, user, channel):
        pass

    def user_quit(self, user, message):
        pass

    def user_renamed(self, oldname, newname):
        pass

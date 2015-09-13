"""
Original code by habnabit: https://gist.github.com/habnabit/5823693
"""
from twisted.internet import defer, protocol, reactor
from twisted.python import log
from twisted.words.protocols import irc

from akumabot.conversation import ConversationMap


class AkumaBotProtocol(irc.IRCClient):

    def __init__(self, nickname, password, debug):
        self.deferred = defer.Deferred()

        self.nickname = nickname
        self.password = password
        self.debug = debug

        self.conversations = ConversationMap(self)
        self.notice_conversations = ConversationMap(self)

    def connectionLost(self, reason):
        log.msg('Disconnected')
        self.deferred.errback(reason)

    def signedOn(self):
        reactor.callLater(0.5, self._join_channels)

    def joined(self, channel):
        log.msg('Joined channel {0!r}'.format(channel))

    def _join_channels(self):
        for channel in self.factory.channels:
            log.msg('Attempting to join {0}'.format(channel))
            self.join(channel)

    def _debug(self, message):
        if self.debug:
            log.msg('DEBUG ' + message)

    def noticed(self, user, channel, message):
        self._debug(
            'Received notice from user {0!r}, channel {1!r}: {2!r}'.format(
                user, channel, message))
        nickname, _, host = user.partition('!')
        message = message.strip()
        self.bot.received_notice(nickname, channel, message)

    def privmsg(self, user, channel, message):
        self._debug(
            'Received message from user {0!r}, channel {1!r}: {2!r}'.format(
                user, channel, message))
        nickname, _, host = user.partition('!')
        message = message.strip()
        if channel == self.nickname:
            self.bot.received_private_message(nickname, message)
        else:
            self.bot.received_message(nickname, channel, message)

    def msg(self, user, message, length=None):
        self._debug('Sending message to user/channel {0!r}: {1!r}'.format(
            user, message))
        irc.IRCClient.msg(self, user, message, length)

    def notice(self, user, message, length=None):
        self._debug('Sending notice to user/channel {0!r}: {1!r}'.format(
            user, message))
        irc.IRCClient.notice(self, user, message, length)

    def modeChanged(self, user, channel, set, modes, args):
        action = 'set' if set else 'removed'
        fmt = 'User {0!r} {1} mode(s) {2!r} for {3!r} with args {4!r}'
        log.msg(fmt.format(user, action, modes, channel, args))

    def kickedFrom(self, channel, kicker, message):
        self._debug('Kicked from {0!r} by {1!r}: {2!r}'.format(
            channel, kicker, message))
        self.bot.kicked(channel, kicker, message)

    def userJoined(self, user, channel):
        self._debug('User {0!r} has joined {1!r}'.format(user, channel))
        self.bot.user_joined(user, channel)

    def userLeft(self, user, channel):
        self._debug('User {0!r} has left {1!r}'.format(user, channel))
        self.bot.user_left(user, channel)

    def userQuit(self, user, quitMessage):
        self._debug('User {0!r} has quit: {1!r}'.format(user, quitMessage))
        self.bot.user_quit(user, quitMessage)

    def userRenamed(self, oldname, newname):
        self._debug(
            'User {0!r} is now known as {1!r}'.format(oldname, newname))
        self.bot.user_renamed(oldname, newname)

    def receivedMOTD(self, motd):
        for msg in motd:
            log.msg('MOTD: {0!r}'.format(msg))


class AkumaBotFactory(protocol.ReconnectingClientFactory):
    protocol = AkumaBotProtocol

    def __init__(self, config):
        self.config = config
        self.channels = config['akumabot.channels']

    def buildProtocol(self, addr):
        p = self.protocol(
            self.config['akumabot.nickname'],
            self.config['akumabot.password'],
            self.config['akumabot.debug'])
        p.factory = self
        return p

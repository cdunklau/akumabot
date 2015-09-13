import functools
import re
import shlex
import random

from zope.interface import Interface, Attribute, directlyProvides
from zope.interface.verify import verifyObject
from twisted.python import log
from twisted.internet import reactor, defer

from akumabot.calculate import calculate_expression, CalculatorParseError


class ICommand(Interface):
    name = Attribute("The name of the command")
    admin_only = Attribute("True if the command is only usable by admins")
    pm_only = Attribute("True if the command is only useable in a PM")
    channel_only = Attribute("True if the command is only usable in-channel")
    usage = Attribute("Help message with a format key the command name")

    def run(bot, channel, nickname, command_args):
        """
        Run a command provided via IRC.

        :param bot:
            The AkumaBot instance.
        :param channel:
            The channel in which the command was received, or None
            if it came from a private message.
        :param nickname:
            The IRC nickname who sent the command.
        :param command_args:
            A list of arguments to the command, as processed by
            `shlex.split`.

        :returns:
            A response string or None if no response is to be sent,
            or a Deferred that fires with the above.
        """


class CommandProcessor(object):
    def __init__(self, bot):
        self.bot = bot
        self.commands = registry
        trigger = self.bot.config['commands.trigger']
        if trigger == '<nick>':
            trigger = self.bot.config['akumabot.nickname']
        pattern = '''
            ^
                (?P<trigger>{trigger}[,: ]*)
                (?P<rest>.*)
            $
        '''.format(trigger=re.escape(trigger))
        self.command_regex = re.compile(pattern, re.VERBOSE)

    def add_listeners(self):
        self.bot.add_listener('received_message', self.process_message)
        self.bot.add_listener(
            'received_private_message', self.process_private_message)

    def process_message(self, nickname, channel, message):
        command_string = self._detect_command(message)
        if not command_string:
            return
        command, argstring = self._split_command(command_string)
        self.run_command(command, channel, nickname, argstring)

    def process_private_message(self, nickname, message):
        command, argstring = self._split_command(message)
        self.run_command(command, None, nickname, argstring)

    def run_command(self, command_name, channel, nickname, argstring):
        command = self.commands.get(command_name, None)
        if command is None:
            log.msg('Ignoring unknown command {0!r}'.format(command_name))
            return
        if command.admin_only and nickname not in self.bot.admins:
            log.msg(
                'Ignoring command {0!r} with args {1!r} '
                'from non-admin nick {2!r}'.format(
                    command_name, argstring, nickname))
            return
        if channel is None and command.channel_only:
            return
        if channel and command.pm_only:
            return

        args = shlex.split(argstring)
        log.msg('Running {0} command with args {1}'.format(command_name, args))
        d = defer.maybeDeferred(
            command.run, self.bot, channel, nickname, args)
        d.addErrback(self._show_error)
        if not channel:
            d.addCallback(self.bot.send_private_message, nickname)
        else:
            d.addCallback(self.bot.send_channel_message, channel, nickname)

    def _detect_command(self, message):
        m = self.command_regex.match(message.strip())
        if m:
            return m.group('rest')
        else:
            return None

    def _split_command(self, command_string):
        command, _, argstring = command_string.strip().partition(' ')
        return command, argstring.lstrip()

    def _show_error(self, failure):
        log.err(failure)
        return "Something terrible has happened!"


class CommandRegistry(object):
    def __init__(self):
        self._registry = {}

    def register_class(self, command_class):
        command = command_class()
        directlyProvides(command, ICommand)
        verifyObject(ICommand, command)
        self._registry[command.name] = command
        return command_class

    def get(self, command_name, default=None):
        return self._registry.get(command_name, default)

    def get_all_commands(self):
        return self._registry.values()



registry = CommandRegistry()


@registry.register_class
class QuitCommand(object):
    name = 'quit'
    admin_only = True
    pm_only = False
    channel_only = False
    usage = '{0} <delay_in_seconds>   Disconnect from the server'

    def run(self, bot, channel, nickname, command_args):
        if len(command_args) != 1:
            return self.usage.format(self.name)

        try:
            delay = int(command_args[0])
            if not 5 <= delay <= 60:
                raise ValueError
        except ValueError:
            return 'Delay must be an integer between 5 and 60'
        else:
            reactor.callLater(float(delay), bot.disconnect)
            return 'Disconnecting in {0} seconds'.format(delay)


@registry.register_class
class LeaveCommand(object):
    name = 'leave'
    admin_only = True
    pm_only = False
    channel_only = True
    usage = '{0}  Leave the current channel'
    
    _leave_rebukes = (
        "I can tell when I'm not wanted.",
        "Fine. Be that way.",
        "I think you ought to know I'm feeling very depressed.",
    )

    def run(self, bot, channel, nickname, command_args):
        reactor.callLater(1.0, bot.leave_channel, channel)
        return random.choice(self._leave_rebukes)


@registry.register_class
class JoinCommand(object):
    name = 'join'
    admin_only = True
    pm_only = False
    channel_only = False
    usage = '{0} <channel>   Join another channel'

    def run(self, bot, channel, nickname, command_args):
        if len(command_args) != 1:
            return self.usage.format(self.name)
        bot.join_channel(command_args[0])


@registry.register_class
class PMMeCommand(object):
    name = 'pmme'
    admin_only = False
    pm_only = False
    channel_only = False
    usage = '{0} <message>'

    def run(self, bot, channel, nickname, command_args):
        if len(command_args) != 1:
            return self.usage.format(self.name)
        else:
            bot.send_private_message(command_args[0], nickname)


def _emulate_ping():
    nbytes = random.randint(24, 78)
    ttl = random.choice([32, 64, 128])
    time = random.random()
    msg = '{0} bytes from 127.0.0.1: icmp_seq=1 ttl={1} time={2:.3f} ms'
    return msg.format(nbytes, ttl, time)


@registry.register_class
class PingCommand(object):
    name = 'ping'
    admin_only = False
    pm_only = False
    channel_only = False
    usage = "{0}   Verify I'm still attentive"

    _pings = (
        lambda: 'Pong!',
        lambda: 'WHAT, man?',
    ) + (_emulate_ping,) * 10

    def run(self, bot, channel, nickname, command_args):
        return random.choice(self._pings)()


@registry.register_class
class HelpCommand(object):
    name = 'help'
    admin_only = False
    pm_only = False
    channel_only = False
    usage = (
        '{0} [<command>]   Show available, or more info about a specific one'
    )

    def run(self, bot, channel, nickname, command_args):
        if len(command_args) == 0:
            # Show available commands
            if nickname in bot.admins:
                commands = registry.get_all_commands()
            else:
                commands = [
                    c for c in registry.get_all_commands() if not c.admin_only]
            return 'Available commands are: {0}'.format(
                ' '.join(c.name for c in commands))
        elif len(command_args) == 1:
            helpfor = command_args[0]
            helpfor_command = registry.get(helpfor)
            if helpfor_command is None:
                return 'Unknown command {0}'.format(helpfor)
            else:
                return helpfor_command.usage.format(helpfor_command.name)
        else:
            return self.usage.format(self.name)

@registry.register_class
class KickCommand(object):
    name = 'kick'
    admin_only = True
    pm_only = True
    channel_only = False
    usage = '{0} <user> <channel> [<reason>]   Kick a user from this channel'

    def run(self, bot, channel, nickname, command_args):
        if len(command_args) == 2:
            target_user, target_channel = command_args
            reason = ''
        elif len(command_args) == 3:
            target_user, target_channel, reason = command_args
        else:
            return self.usage.format(self.name)
        self.do_kick(bot, target_user, target_channel, reason)

    def do_kick(self, bot, user, channel, reason):
        reactor.callLater(
            1.0, bot.send_private_message,
            'op {0}'.format(channel), 'chanserv')
        reactor.callLater(3.0, bot.kick_user, channel, user, reason)
        reactor.callLater(
            5.0, bot.send_private_message,
            'deop {0}'.format(channel), 'chanserv')


@registry.register_class
class CalcCommand(object):
    name = 'calc'
    admin_only = False
    pm_only = False
    channel_only = False
    usage = '{0} <expression>   Evaluate math expression'

    def run(self, bot, channel, nickname, command_args):
        if not command_args:
            return self.usage.format(self.name)
        expression = ' '.join(command_args)
        try:
            result = calculate_expression(expression)
            return 'Result: {0:.6G}'.format(result)
        except CalculatorParseError:
            return "I didn't understand {0}".format(expression)

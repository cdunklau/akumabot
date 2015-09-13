import unittest

from akumabot.commands import CommandProcessor


class FakeBot(object):
    def __init__(self, config):
        self.config = config


class DetectCommandTestCase(unittest.TestCase):
    def assertMessageContainsCommand(self, nickname, trigger, message,
                                     expected_command_string):
        conf = {
            'akumabot.admins': set(),
            'akumabot.nickname': nickname,
            'commands.trigger': trigger,
        }
        bot = FakeBot(conf)
        cmdproc = CommandProcessor(bot)

        result = cmdproc._detect_command(message)
        if result is None:
            raise AssertionError(
                'No command was found in message {0!r}'.format(message))
        command_string = result
        if command_string != expected_command_string:
            raise AssertionError(
                'Got command string {0!r} but expected {1!r} '
                'in message {2!r}'.format(
                    command_string, expected_command_string, message))

    def test_basic_command_trigger(self):
        nickname = 'testybot'
        trigger = '!'
        message = '!commandname arg string stuff'
        command_string = 'commandname arg string stuff'
        self.assertMessageContainsCommand(
            nickname, trigger, message, command_string)

    def test_nick_command_trigger(self):
        nickname = 'testybot'
        trigger = '<nick>'
        messages = [
            'testybot, commandname arg string stuff',
            'testybot: commandname arg string stuff',
            'testybot commandname arg string stuff',
        ]
        command_string = 'commandname arg string stuff'
        for message in messages:
            self.assertMessageContainsCommand(
                nickname, trigger, message, command_string)
        message = 'testybot, commandname'
        command_string = 'commandname'
        self.assertMessageContainsCommand(
            nickname, trigger, message, command_string)

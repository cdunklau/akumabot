import sys

from twisted.internet import task
from twisted.python import log

from akumabot.bot import AkumaBot
from akumabot.config import process_config_file


if __name__ == '__main__':
    log.startLogging(sys.stderr)
    with open('akumabot.conf', 'rb') as f:
        config = process_config_file(f)
    bot = AkumaBot(config)
    task.react(bot.main, ['ssl:host=irc.freenode.net:port=6697'])

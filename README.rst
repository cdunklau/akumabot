########
AkumaBot
########

Demonstration IRC bot. Works on Freenode_.

.. _Freenode: https://freenode.net/


Features
========

-   Multiple channel connection
-   Asynchronous design built on Twisted_
-   Simple command permissions (admin or everyone)

.. _Twisted: http://twistedmatrix.com/

Commands
========

-   Ping: ensure that the bot is active
-   PM Me: send a PM to user
-   Help: list all available commands
-   Calculator: calculate simple math expressions



Administrator Commands
======================

-   Join channel
-   Leave channel
-   Kick user
-   Quit


Installation
============

Python 2.7 is supported. Create a virtualenv::

    virtualenv venv

Install requirements::

    venv/bin/pip install -r requirements.txt

Configure it. Here's an example config file, put yours into akumabot.conf::

    [akumabot]
    nickname = myakumabot
    password = secret
    channels =
        ##yournick
        #botters-test
    admins =
        yournick
    debug = true

Run it::

    venv/bin/python -m akumabot.main

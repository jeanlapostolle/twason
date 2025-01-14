# Twason - The KISS Twitch bot
# Copyright (C) 2021  Jérôme Deuchnord
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import irc3

from .config import TimerStrategy
from random import shuffle
from datetime import datetime, timedelta

config = None


@irc3.plugin
class TwitchBot:
    def __init__(self, bot):
        self.config = config
        self.messages_stack = []
        self.bot = bot
        self.log = self.bot.log
        self.last_timer_date = datetime.now()
        self.nb_messages_since_timer = 0

    def connection_made(self):
        print('connected')

    def server_ready(self):
        print('ready')

    def connection_lost(self):
        print('connection lost')

    @staticmethod
    def _parse_variables(in_str: str, mask: str = None):
        variables = {
            'author': mask.split('!')[0]
        }

        for key in variables:
            value = variables[key]
            in_str = in_str.replace('{%s}' % key, value)

        return in_str

    @irc3.event(irc3.rfc.PRIVMSG)
    def on_msg(self, target, mask, data, **_):
        command = self.config.find_command(data.lower().split(' ')[0])

        if command is not None:
            print('%s: %s%s' % (mask, self.config.command_prefix, command.name))
            self.bot.privmsg(target, self._parse_variables(command.message, mask))

        self.nb_messages_since_timer += 1
        self.play_timer()

    def play_timer(self):
        if not self.messages_stack:
            print('Filling the timer messages stack in')
            self.messages_stack = self.config.timer.pool.copy()
            if self.config.timer.strategy == TimerStrategy.SHUFFLE:
                print('Shuffle!')
                shuffle(self.messages_stack)

        if self.nb_messages_since_timer < self.config.timer.msgs_between or \
            datetime.now() < self.last_timer_date + timedelta(minutes=self.config.timer.time_between):
            return

        command = self.messages_stack.pop(0)

        print("Timer: %s" % command.message)
        self.bot.privmsg('#%s' % self.config.channel, command.message)

        self.nb_messages_since_timer = 0
        self.last_timer_date = datetime.now()

    @irc3.event(irc3.rfc.JOIN)
    def on_join(self, mask, channel, **_):
        print('JOINED %s as %s' % (channel, mask))

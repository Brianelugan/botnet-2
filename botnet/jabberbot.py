#!/usr/bin/python


# Victor Hugo Germano Alterations (Jun /Jul 2010)
# - integrated Eliza NLP on unkown commands
# - ipmroved connect method in order to be able to connect on gtalk service
#

# JabberBot: A simple jabber/xmpp bot framework
# Copyright (c) 2007-2009 Thomas Perl <thpinfo.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# Homepage: http://thpinfo.com/2007/python-jabberbot/
#


import sys

try:
    import xmpp
except ImportError:
    print >>sys.stderr, 'You need to install xmpppy from http://xmpppy.sf.net/.'
    sys.exit(-1)
import inspect

from eliza import eliza

"""A simple jabber/xmpp bot framework

This is a simple bot framework around the "xmpppy" framework.
Copyright (c) 2007-2009 Thomas Perl <thpinfo.com>

To use, subclass the "JabberBot" class and implement "bot_" methods 
(or whatever you set the command_prefix to)


"""

__author__ = 'Thomas Perl <thp@thpinfo.com>'
__version__ = '0.6'


class JabberBot(object):
    command_prefix = 'bot_'
    
    
    def presence_handler(self, conn, msg):
        msg_type = msg.getType()
        who = msg.getFrom()
        if msg_type == "subscribe":
            print msg
            conn.send(xmpp.Presence(to=who, typ='subscribed'))
            conn.send(xmpp.Presence(to=who, typ='subscribe'))
            

    def __init__( self, jid, password, res = None, server = None, port = None):
        """Initializes the jabber bot and sets up commands."""
        self.eliza = eliza()
        self.jid = xmpp.JID( jid)
        self.password = password
        self.res = (res or self.__class__.__name__)
        self.conn = None
        self.server = server
        self.port = port
        self.__finished = False

        self.commands = { 'help': self.help_callback, }
        for (name, value) in inspect.getmembers( self):
            if inspect.ismethod( value) and name.startswith( self.command_prefix):
                self.commands[name[len(self.command_prefix):]] = value

    def log( self, s):
        """Logging facility, can be overridden in subclasses to log to file, etc.."""
        print '%s: %s' % ( self.__class__.__name__, s, )

    def connect( self):
        if not self.conn:
            conn = xmpp.Client( self.jid.getDomain(), debug = [])
            
            if not conn.connect([self.server, self.port]):
                self.log( 'unable to connect to server.')
                return None
            
            if not conn.auth( self.jid.getNode(), self.password, self.res):
                self.log( 'unable to authorize with server.')
                return None
            
            conn.RegisterHandler( 'message', self.callback_message)
            conn.RegisterHandler( 'presence', self.presence_handler)
            conn.sendInitPresence()
            self.conn = conn

        return self.conn

    def quit( self):
        self.__finished = True

    def send( self, user, text, in_reply_to = None):
        """Sends a simple message to the specified user."""
        mess = xmpp.Message( user, text)
        if in_reply_to:
            mess.setThread( in_reply_to.getThread())
            mess.setType( in_reply_to.getType())
        
        self.connect().send( mess)

    def callback_message( self, conn, mess):
        """Messages sent to the bot will arrive here. Command handling + routing is done in this function."""
        text = mess.getBody()
        # If a message format is not supported (eg. encrypted), txt will be None
        if not text:
            return

        if ' ' in text:
            command, args = text.split(' ',1)
        else:
            command, args = text,''
    
        cmd = command.lower()
    
        if self.commands.has_key(cmd):
            reply = self.commands[cmd]( mess, args)
        else:
            reply = self.unknown_command( mess, cmd, args) 
        if reply:
            self.send( mess.getFrom(), reply.encode("utf-8"), mess)

    def unknown_command( self, mess, cmd, args):
        return self.eliza.respond(mess.getBody())

    def help_callback( self, mess, args):
        """Returns a help string listing available options. Automatically assigned to the "help" command."""
        usage = '\n'.join(sorted(['%s: %s' % (name, command.__doc__ or '(undocumented)') for (name, command) in self.commands.items() if name != 'help' and (not command.__doc__ or not command.__doc__.startswith('HIDDEN'))]))

        if self.__doc__:
            description = self.__doc__.strip()
        else:
            description = 'Available commands:'

        return '%s\n\n%s' % ( description, usage, )

    def idle_proc( self):
        """This function will be called in the main loop."""
        pass

    def serve_forever( self, connect_callback = None, disconnect_callback = None):
        """Connects to the server and handles messages."""
        conn = self.connect()
        if conn:
            self.log('bot connected. serving forever.')
        else:
            self.log('could not connect to server - aborting.')
            return

        if connect_callback:
            connect_callback()

        while not self.__finished:
            try:
                conn.Process(1)
                self.idle_proc()
            except KeyboardInterrupt:
                self.log('bot stopped by user request. shutting down.')
                break
            except xmpp.protocol.InternalServerError:
                print "Server error at Google, trying again"


        if disconnect_callback:
            disconnect_callback()

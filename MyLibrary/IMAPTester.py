#! /usr/bin/env python3

import imaplib
import smtplib
import random
from email.mime.text import MIMEText


Commands = {
        # name            valid states
        'APPEND':       ('AUTH', 'SELECTED'),
        'AUTHENTICATE': ('NONAUTH',),
        'CAPABILITY':   ('NONAUTH', 'AUTH', 'SELECTED', 'LOGOUT'),
        'CHECK':        ('SELECTED',),
        'CLOSE':        ('SELECTED',),
        'COPY':         ('SELECTED',),
        'CREATE':       ('AUTH', 'SELECTED'),
        'DELETE':       ('AUTH', 'SELECTED'),
        'DELETEACL':    ('AUTH', 'SELECTED'),
        'ENABLE':       ('AUTH', ),
        'EXAMINE':      ('AUTH', 'SELECTED'),
        'EXPUNGE':      ('SELECTED',),
        'FETCH':        ('SELECTED',),
        'GETACL':       ('AUTH', 'SELECTED'),
        'GETANNOTATION':('AUTH', 'SELECTED'),
        'GETQUOTA':     ('AUTH', 'SELECTED'),
        'GETQUOTAROOT': ('AUTH', 'SELECTED'),
        'MYRIGHTS':     ('AUTH', 'SELECTED'),
        'LIST':         ('AUTH', 'SELECTED'),
        'LOGIN':        ('NONAUTH',),
        'LOGOUT':       ('NONAUTH', 'AUTH', 'SELECTED', 'LOGOUT'),
        'LSUB':         ('AUTH', 'SELECTED'),
        'NAMESPACE':    ('AUTH', 'SELECTED'),
        'NOOP':         ('NONAUTH', 'AUTH', 'SELECTED', 'LOGOUT'),
        'PARTIAL':      ('SELECTED',),                                  # NB: obsolete
        'PROXYAUTH':    ('AUTH',),
        'RENAME':       ('AUTH', 'SELECTED'),
        'SEARCH':       ('SELECTED',),
        'SELECT':       ('AUTH', 'SELECTED'),
        'SETACL':       ('AUTH', 'SELECTED'),
        'SETANNOTATION':('AUTH', 'SELECTED'),
        'SETQUOTA':     ('AUTH', 'SELECTED'),
        'SORT':         ('SELECTED',),
        'STARTTLS':     ('NONAUTH',),
        'STATUS':       ('AUTH', 'SELECTED'),
        'STORE':        ('SELECTED',),
        'SUBSCRIBE':    ('AUTH', 'SELECTED'),
        'THREAD':       ('SELECTED',),
        'UID':          ('SELECTED',),
        'UNSUBSCRIBE':  ('AUTH', 'SELECTED'),
        'XLIST':        ('AUTH', 'SELECTED'),
        }



CRLF = b'\r\n'
Debug = 0
IMAP4_PORT = 143
IMAP4_SSL_PORT = 993
AllowedVersions = ('IMAP4REV1', 'IMAP4')

class IW_connection(imaplib.IMAP4):
    def __init__(self,host,username, password, iw_connector = True, port=IMAP4_PORT):
        """create server object with credentials and IW connector"""
        self.host = host
        self.username = username
        self.password = password
        self.debug = Debug
        self.state = 'LOGOUT'
        self.literal = None             # A literal argument to a command
        self.tagged_commands = {}       # Tagged commands awaiting response
        self.untagged_responses = {}    # {typ: [data, ...], ...}
        self.continuation_response = '' # Last continuation response
        self.is_readonly = False        # READ-ONLY desired state
        self.tagnum = 0
        self._tls_established = False
        self._mode_ascii()

        # Open socket to server.

        self.open(host, port)

        try:
            self._connect()
        except Exception:
            try:
                self.shutdown()
            except OSError:
                pass
            raise

        # login to server   
        try:
            self.login(self.username, self.password)
        except Exception:
            try:
                self.shutdown()
            except OSError:
                pass
            raise

        # activate IW connector
        if iw_connector:
            self.xatom('X-ICEWARP-SERVER iwconnector')

    def __getattr__(self, attr):
        #       Allow UPPERCASE variants of IMAP4 command methods.
        if attr in Commands:
            return getattr(self, attr.lower())
        raise AttributeError("Unknown IMAP4 command: '%s'" % attr)

    def uid(self, command, *args):
        """Execute "command arg ..." with messages identified by UID,
                rather than message number.

        (typ, [data]) = <instance>.uid(command, arg1, arg2, ...)

        Returns response appropriate to 'command'.
        """
        command = command.upper()
        if not command in Commands:
            raise self.error("Unknown IMAP4 UID command: %s" % command)
        if self.state not in Commands[command]:
            raise self.error("command %s illegal in state %s, "
                             "only allowed in states %s" %
                             (command, self.state,
                              ', '.join(Commands[command])))
        name = 'UID'
        typ, dat = self._simple_command(name, command, *args)
        if command in ('SEARCH', 'SORT', 'THREAD'):
            name = command
        else:
            name = 'FETCH'
        return self._untagged_response(typ, dat, name)

    def xatom(self, name, *args):
        """Allow simple extension commands
                notified by server in CAPABILITY response.

        Assumes command is legal in current state.

        (typ, [data]) = <instance>.xatom(name, arg, ...)

        Returns response appropriate to extension command `name'.
        """
        #name = name.upper()
        #if not name in self.capabilities:      # Let the server decide!
        #    raise self.error('unknown extension command: %s' % name)
        if not name in Commands:
            Commands[name] = (self.state,)
        try:
            self._simple_command(name, *args)
        except:
                pass



    def _command(self, name, *args):

        if self.state not in Commands[name]:
            self.literal = None
            raise self.error("command %s illegal in state %s, "
                             "only allowed in states %s" %
                             (name, self.state,
                              ', '.join(Commands[name])))

        for typ in ('OK', 'NO', 'BAD'):
            if typ in self.untagged_responses:
                del self.untagged_responses[typ]

        if 'READ-ONLY' in self.untagged_responses \
        and not self.is_readonly:
            raise self.readonly('mailbox status changed to READ-ONLY')

        tag = self._new_tag()
        name = bytes(name, self._encoding)
        data = tag + b' ' + name
        for arg in args:
            if arg is None: continue
            if isinstance(arg, str):
                arg = bytes(arg, self._encoding)
            data = data + b' ' + arg

        literal = self.literal
        if literal is not None:
            self.literal = None
            if type(literal) is type(self._command):
                literator = literal
            else:
                literator = None
                data = data + bytes(' {%s}' % len(literal), self._encoding)

        if __debug__:
            if self.debug >= 4:
                self._mesg('> %r' % data)
            else:
                self._log('> %r' % data)

        try:
            self.send(data + CRLF)
        except OSError as val:
            raise self.abort('socket error: %s' % val)

        if literal is None:
            return tag

        while 1:
            # Wait for continuation response

            while self._get_response():
                if self.tagged_commands[tag]:   # BAD/NO?
                    return tag

            # Send literal

            if literator:
                literal = literator(self.continuation_response)

            if __debug__:
                if self.debug >= 4:
                    self._mesg('write literal size %s' % len(literal))

            try:
                self.send(literal)
                self.send(CRLF)
            except OSError as val:
                raise self.abort('socket error: %s' % val)

            if not literator:
                break

        return tag




    def get_flags(self,msgid):
        '''fetch flags from msg
        '''
        return imaplib.ParseFlags(self.fetch(msgid,"FLAGS")[1][0])

    def get_msgid_by_subject(self,subject, folder='INBOX'):
        """try to find msgID by subject in specific folder"""

        #select folder
        selected = self.select(folder)[0]
        if selected != "OK":
            raise self.error("unable to select this folder: %s" % folder)

        #search by subject
        search, msgid = self.search(None, 'SUBJECT', ('"' + subject + '"'))
        if search != "OK":
            raise self.error("error in SEARCH (subject): %s" % subject)
        if (msgid[0]).decode() != '':
            #return (msgid[0]).decode()              # vracet int nebo str????
            return msgid[0]
        else:
            #raise self.error("nothing found!")    # nebo vracet -1????
            return -1

    def add_flag(self, msgid, flags):
        state, response =  self._simple_command('STORE', msgid.decode(), '+flags', flags)
        if state == "OK":
            if flags.encode() in self.get_flags(msgid):
                return True
            else:
                return False
        else:
            return False
       
    def remove_flag(self, msgid, flags):
        return self._simple_command('STORE', msgid.decode(), '-flags', flags)

    def delete_message(self, msgid, folder = 'INBOX'):
        self.select(folder)
        return self.add_flag(msgid, '\\Deleted')

    def create_folder(self, folder):
        state, response =  self._simple_command('CREATE', folder)
        if state == "OK":
            if self.select(folder)[0] == "OK":
                return True
            else:
                return False
        else:
            return False
        
    def delete_folder(self, folder):
        state, response =  self._simple_command('DELETE', folder)
        if state == "OK":
            return True
        else:
            if response[0] == b'DELETE Mailbox does not exist':
                return True
            else:
                return False

    def rename_folder(self, old, new):
        try:
            state, response =  self._simple_command('RENAME', old, new)
            if state == "OK":
                return True
            else:
                print(response)
                return False                
        except imaplib.IMAP4.error as err:
            return False
        #    raise RuntimeError("unknow error: ", err)
        
    def xlist(self, directory='""', pattern='*'):
        """List mailbox names in directory matching pattern.

        (typ, [data]) = <instance>.list(directory='""', pattern='*')

        'data' is list of LIST responses.
        """
        name = 'XLIST'
        typ, dat = self._simple_command(name, directory, pattern)
        return self._untagged_response(typ, dat, name)


class Email:
    """instance of email in server
    
    priority:
    1=HIGH
    3=NORMAL
    5=LOW
    """
    def __init__(self, host, to, sender, subject=('TEST email c.: ' + str(random.randrange(10000,99999))), text='this is only test msg', priority = '3'):
        self.host = host
        self.to = to
        self.sender = sender
        self.subject = subject
        self.text = text
        self.priority = priority
        self.mime_msg = self._set_mime_msg()
        self.ID = None
        self.folder = 'INBOX'
        self.flags = None

    def _set_mime_msg(self):
        msg = MIMEText(self.text)
        msg['Subject'] = self.subject
        msg['From'] = self.sender
        msg['To'] = self.to
        msg['X-Priority'] = self.priority
        return msg

    def send(self):
        try:
            s = smtplib.SMTP(self.host)
            try:
                s.send_message(self.mime_msg)
                s.quit()
            except smtplib.SMTPException as err:
                print(str(err))
                raise RuntimeError("unable to send MSG:", err)
        except smtplib.SMTPException as err:
            print(str(err))
            raise RuntimeError("can't setup connection to SMTP server:", err)

          
      
        


#! /usr/bin/env python3

import imaplib
import smtplib
import random
from email.mime.text import MIMEText


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

          
      
        


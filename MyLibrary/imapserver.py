import imaplib
import time

host = 'lenka.test.com'
username = 'beta@lenka.test.com'
pw = 'a'


class imap_test(object):
    '''test imap server: working with folders and messages + IDLE mod of server

    Attributes:
        host:
        username:
        password:
    '''
    def __init__(self, host, username, password):
        """create server object with credentials"""
        self.host = host
        self.username = username
        self.password = password
        self.server = imaplib.IMAP4(self.host)

    def xatom(self, name, *args):
        """
        !!!override method without RFC compatibility
        Allow simple extension commands
                notified by server in CAPABILITY response.

        Assumes command is legal in current state.

        (typ, [data]) = <instance>.xatom(name, arg, ...)

        Returns response appropriate to extension command `name'.
        """
        name = name.lower()
        #if not name in self.capabilities:      # Let the server decide!
        #    raise self.error('unknown extension command: %s' % name)
        try:
                self.server._imap._simple_command(name, *args)
        except:
                pass











while(1):
    conn = imaplib.IMAP4(host)
    conn.login(username, pw)
    conn.xatom('SELECT "INBOX"')
    conn.xatom('UID SEARCH SINCE 23-Aug-2018')
    conn.xatom('CLOSE')
    print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
    print(conn._simple_command('SELECT', "INBOX"))
    conn.logout()

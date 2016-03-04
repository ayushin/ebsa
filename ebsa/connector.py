from settings import *
from os import unlink,rmdir,listdir,getcwd
from tempfile import mkdtemp
from django.db.utils import IntegrityError
from datetime import timedelta, date
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select


from models import Bank, Account,Transaction

def load_connector(bank):
    connector = 'ebsa.connectors.' + bank.connector
    parts = connector.split('.')
    module = ".".join(parts[:-1])
    m = __import__( module )
    for comp in parts[1:]:
        m = getattr(m, comp)
    return m(bank)

class Connector:
    def __init__(self, bank):
        self.bank = bank

    def open_browser(self):
        # Read config and setup download directory
        tmpdir = EBSA_TMP_DIR
        if tmpdir[:1] != '/':
                tmpdir = getcwd() + '/' + tmpdir

        self.download_dir = mkdtemp(dir=tmpdir)
        print "Working directory: %s" % self.download_dir

        # Setup FireFox
        fp = webdriver.FirefoxProfile()
        fp.set_preference("browser.download.folderList",2)
        fp.set_preference("browser.download.manager.showWhenStarting",False)
        fp.set_preference("browser.download.dir",self.download_dir)
        fp.set_preference("browser.helperApps.neverAsk.saveToDisk","text/csv")

        self.driver = webdriver.Firefox(firefox_profile=fp)

    def close_browser(self):
        rmdir(self.download_dir)
        self.driver.quit()

    def weblogin(self):
        pass

    def webimport(self):
        pass

    def webimport(self, accounts, datefrom = None):

        # Log in...
        print "Logging into '%s'..." % self.bank.name
        self.weblogin()

        checking_accounts = []

        # Go through every account...
        for account in accounts:
            if not datefrom:
                datefrom = date(account.latest_transaction().date + timedelta(days =1))

            print "Downloading transactions from %s beginning from %s..." % (account.name, datefrom)
            if account.type == 'C':
                self.webimport_creditcard(account, datefrom)

            if account.type == '0':
                checking_accounts.append(account)

        if checking_accounts:
            self.webimport_checking(checking_accounts, datefrom)

        # Log out...
        self.close_browser()

    def download_ready(self):
        if len(listdir(self.download_dir)) != 0:
            return False
        return True


#    def __del__(self):
#        self.close_browser()
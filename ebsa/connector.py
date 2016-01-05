from settings import *
from os import unlink,rmdir,listdir,getcwd
from tempfile import mkdtemp

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
        print self.download_dir

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

    def csvimport(self):
        pass

#    def __del__(self):
#        self.close_browser()
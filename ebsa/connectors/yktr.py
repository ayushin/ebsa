# -*- coding: UTF-8 -*-

from django.utils.encoding import smart_text

from ebsa.connector import Connector
from ebsa.models import Bank, Account, Transaction

from datetime import datetime, date, timedelta

from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By


import csv
import re


class YapiKrediTRConnector(Connector):
    login_url = 'https://internetsube.yapikredi.com.tr/ngi/index.do?lang=en'
#    download_url = 'https://bankieren.mijn.ing.nl/particulier/overzichten/download/index'
#    creditcard_url = 'https://bankieren.mijn.ing.nl/particulier/creditcard/saldo-overzicht/index'

    all_downloaded = False

    def weblogin(self):
        self.open_browser()
        self.driver.get(self.login_url)
        assert u"Yapı Kredi" in self.driver.title

        # Wait for the username and type it in...
        elem = self.driver.find_element_by_id('userCodeTCKN')
        elem.send_keys(self.bank.username)

        elem = self.driver.find_element_by_id('password')
        elem.send_keys(self.bank.password)

        self.driver.find_element_by_id('btnSubmit').click()

        # Get the auth code from the user and send it together with the 'pin'...
        auth_code = input("Please enter the auth code:\n")
        elem = self.driver.find_element_by_id('otpPassword')
        elem.send_keys(auth_code)
        self.driver.find_element_by_id('btnSubmit').click()


#    def download_all_accounts (self, fromdate):
#        self.driver.get(self.download_url)

        # Check download directory is ready and empty...
#        if not self.download_ready():
#            raise EnvironmentError('Download directory %s is not ready' % self.download_dir)
#
#        # Format
#        select = Select(self.driver.find_element_by_id('downloadFormat'))
#        select.select_by_visible_text('Kommagescheiden IBAN (jjjjmmdd)')

        # Date From
#        elem = self.driver.find_element_by_xpath("//input[@id='startDate-input']")
#        elem.clear()
#        elem.send_keys(fromdate.strftime('%d-%m-%Y'))

        # Date To
#        elem = self.driver.find_element_by_id('endDate-input')
#        elem.clear()
#        elem.send_keys((date.today() - timedelta(1)).strftime('%d-%m-%Y'))

        # All accounts
#        elem = self.driver.find_element_by_xpath("//div[@id='accounts']/div/button")
#        elem.click()
#        elem.send_keys(Keys.ARROW_UP)
#        elem.send_keys(Keys.ENTER)

        # Click download
#        elem = self.driver.find_element_by_xpath("//button[text()='Download']")
#        elem.click()#    def webimport_checking(self, account, datefrom):


    #
    #
    # Import downloaded CSV file
    #
    # If accounts = None create the accounts for this bank from the statement file
    #
    def csvimport(self, filename, bank, accounts):
        # Check the header...
        header=['Date', 'Transaction', 'Channel', 'Description', 'Transaction Amount', 'Balance', 'Receipt']

        account = accounts[0]

        # Open the file
        print "Opening %s" % filename

        with open(filename, 'r') as csv_file:
            # Open the file
            reader = csv.DictReader(csv_file, fieldnames=header, delimiter='\t', quotechar='"')

            # Check the header
            h = next(reader)
            for key in h:
                if h[key] != key:
                    raise ValueError('CSV file doesnt seem to be in the correct format')

            lineno = 1
            for row in reader:
                # Skip investment transactions...
                #  if row['Transaction'] == 'Investment Transactions':
                #    continue

                # Create a new transaction...
                line = Transaction()
                line.account = account

                # Find the date...
                line.date = line.date_user = datetime.strptime(row['Date'],'%d/%m/%Y')

                # Determine the amount...
                m = re.search('^(\-?)(\d*)\.?(\d*),(\d*) (TL|EUR)$', row['Transaction Amount'])
                line.amount = float(m.group(1) + m.group(2) + m.group(3) + '.' + m.group(4))
                if line.amount > 0:
                    line.trntype = '+'
                elif line.amount < 0:
                    line.trntype = '-'
                else:
                    raise ValueError('No sign for transaction, zero transactions are not supported')


                line.memo = smart_text(row['Description']) + ' [' + row['Channel'] + ']'
                line.payee = smart_text(row['Description'])
                line.check_no = lineno
                lineno += 1
                line.refnum = line.generate_refnum()

                line.save_safe()

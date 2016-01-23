from django.utils.encoding import smart_text

from ebsa.connector import Connector
from ebsa.models import Bank, Account, Transaction

from datetime import datetime, date, timedelta

from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By


import csv


class RaiffeisenCZConnector(Connector):
    login_url = 'https://klient1.rb.cz/ebts/version_02/eng/banka3.html'
#    download_url = 'https://bankieren.mijn.ing.nl/particulier/overzichten/download/index'
#    creditcard_url = 'https://bankieren.mijn.ing.nl/particulier/creditcard/saldo-overzicht/index'

    all_downloaded = False

    def weblogin(self):
        self.open_browser()
        self.driver.get(self.login_url)

        # Get the main frame...
        self.driver.switch_to.frame('Main')

        # Wait for the username and type it in...
        elem_xpath = "//input[@name='a_username' and @type='text']"
        WebDriverWait(self.driver, 3).until(EC.visibility_of_element_located((By.XPATH, elem_xpath)))
        elem = self.driver.find_element_by_xpath(elem_xpath)
        elem.send_keys(self.bank.username)

        # Open the certification prompt box and accept it...
        self.driver.find_element_by_name("b_authcode_Button").click()
        WebDriverWait(self.driver, 3).until(EC.alert_is_present())
        alert = self.driver.switch_to_alert()
        alert.accept()

        # Get the auth code from the user and send it together with the 'pin'...
        auth_code = input("Please enter the auth code:\n")
        elem = self.driver.find_element_by_name("a_userpassword")
        elem.send_keys(auth_code)
        elem = self.driver.find_element_by_name("Pin")
        elem.send_keys(self.bank.password)

        # Click OK to log in
        self.driver.find_element_by_name("b_ok_Button").click()

#    def webimport_checking(self, account, datefrom):
#        # Download all accounts on the first call...
#        if not self.all_downloaded:
#            self.download_all_accounts(datefrom)
#            self.all_downloaded = True


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
#        elem.click()

    #
    #
    # Import downloaded CSV file
    #
    # If accounts = None create the accounts for this bank from the statement file
    #
    def csvimport(self, filename, bank, accounts):
        # Check the header...
        header=['DATE','TIME','NOTE','ACCOUNT NAME','ACCOUNT NUMBER',
                'DATE DEDUCTED','VALUE','TYPE','TRANSACTION CODE','VARIABLE SYMBOL','CONSTANT SYMBOL',
                'SPECIFIC SYMBOL','AMOUNT','CHARGE','EXCHANGE','MESSAGE']

        account = accounts[0]

        # Open the file
        print "Opening %s" % filename

        with open(filename, 'r') as csv_file:
            # Open the file
            reader = csv.DictReader(csv_file, fieldnames=header, delimiter=';', quotechar='"')

            # Check the header
            h = next(reader)
            for key in h:
                if h[key] != key:
                    raise ValueError('CSV file doesnt seem to be in the correct format')

            lineno = 1
            for row in reader:
                # Create a new transaction...
                line = Transaction()
                line.account = account

                # Find the date...
                line.date = line.date_user = datetime.strptime(row['DATE'],'%d.%m.%Y')
    

                # Determine the amount...
                amount = row['AMOUNT'] or row['CHARGE'] or row['MESSAGE']
                line.amount = float(amount.replace(' ','').replace(',','.'))
                if line.amount > 0:
                    line.trntype = '+'
                elif line.amount < 0:
                    line.trntype = '-'
                else:
                    raise ValueError('No sign for transaction, zero transactions are not supported')


                line.memo = smart_text(row['NOTE'])
                if row['ACCOUNT NAME']:
                    line.memo += smart_text('[' + row['ACCOUNT NAME'] + ']')

                line.payee = smart_text(row['ACCOUNT NUMBER'])
                line.check_no = row['TRANSACTION CODE']
                lineno += 1
                line.refnum = line.generate_refnum()

                line.save_safe()

                # Do we have CHARGE and or MESSAGE?
                charges = 0
                if row['AMOUNT']:
                    for key in ('CHARGE', 'MESSAGE'):
                        if row[key]:
                            charges += float(row[key].replace(' ','').replace(',','.'))

                if charges != 0:
                    charge_line = Transaction()
                    charge_line.account = account
                    charge_line.date = charge_line.date_user = line.date
                    charge_line.amount = charges
                    charge_line.trntype = 'S'
                    charge_line.memo = 'Bank charges for transaction ' + line.check_no
                    charge_line.payee = 'Raiffeisen Bank'
                    charge_line.refnum = charge_line.generate_refnum()
                    charge_line.save_safe()
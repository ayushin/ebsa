from django.utils.encoding import smart_text

from ebsa.connector import Connector
from ebsa.models import Bank, Account, Transaction

from datetime import datetime, date, timedelta

from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys

import csv


class IngNLConnector(Connector):
    login_url = 'https://mijn.ing.nl/internetbankieren/SesamLoginServlet'
    download_url = 'https://bankieren.mijn.ing.nl/particulier/overzichten/download/index'
    creditcard_url = 'https://bankieren.mijn.ing.nl/particulier/creditcard/saldo-overzicht/index'

    all_downloaded = False

    def weblogin(self):
        self.open_browser()
        self.driver.get(self.login_url)
        assert "ING" in self.driver.title

        elem = self.driver.find_element_by_xpath('//label[text()="Gebruikersnaam"]')
        elem.send_keys(self.bank.username)
        elem = self.driver.find_element_by_xpath('//label[text()="Wachtwoord"]')
        elem.send_keys(self.bank.password)
        self.driver.find_element_by_class_name('submit').click()

        assert "Mijn ING Overzicht - Mijn ING" in self.driver.title


    def webimport_checking(self, account, datefrom):
        # Download all accounts on the first call...
        if not self.all_downloaded:
            self.download_all_accounts(datefrom)
            self.all_downloaded = True

    def webimport_creditcard(self, account, datefrom):
        # Download credit card statement
        self.driver.get(self.creditcard_url)

        got_last_transaction = False

        while not got_last_transaction:
            line_number = 1
            for tr in self.driver.find_elements_by_xpath("//div[@id='statementDetailTable']/div/div[@class='riaf-datatable-canvas']/table/tbody/tr[@class='riaf-datatable-contents ']"):
                # Date of this transaction
                transaction_date = datetime.strptime(tr.find_element_by_class_name("riaf-datatable-column-date").text,'%d-%m-%Y')

                # Should we continue ?
                if transaction_date < datefrom:
                    got_last_transaction = True
                    break

                # Create new transaction with the account id
                line = Transaction(account=account)

                # We save the statement line number as check_no in order to create unique refnum
                line.check_no = line_number
                line_number += 1


                # Initialize date
                line.date_user = line.date = transaction_date

                # Initialize amount and transaction type
                amount = float(tr.find_element_by_class_name("riaf-datatable-column-amount").text.replace('.','').replace(',','.'))
                if tr.find_element_by_class_name("riaf-datatable-column-last").find_element_by_xpath('span').get_attribute("class") == 'riaf-datatable-icon-crdb-db' :
                    line.trntype = '-'
                    line.amount = -amount
                elif tr.find_element_by_class_name("riaf-datatable-column-last").find_element_by_xpath('span').get_attribute("class") == 'riaf-datatable-icon-crdb-cr' :
                    line.trntype = '+'
                    line.amount = amount
                else:
                    raise ValueError('No sign for transaction')

                text = tr.find_elements_by_class_name("riaf-datatable-column-text");

                line.payee = line.memo = smart_text(text[0].text)
                line.refnum = line.generate_refnum()

                line.save_safe()

            # Download previous credit card statement
            self.driver.find_element_by_id('previousPeriod').click()

    def download_all_accounts (self, fromdate):
        self.driver.get(self.download_url)

        # Check download directory is ready and empty...
        if not self.download_ready():
            raise EnvironmentError('Download directory %s is not ready' % self.download_dir)

        # Format
        select = Select(self.driver.find_element_by_id('downloadFormat'))
        select.select_by_visible_text('Kommagescheiden IBAN (jjjjmmdd)')

        # Date From
        elem = self.driver.find_element_by_xpath("//input[@id='startDate-input']")
        elem.clear()
        elem.send_keys(fromdate.strftime('%d-%m-%Y'))

        # Date To
        elem = self.driver.find_element_by_id('endDate-input')
        elem.clear()
        elem.send_keys((date.today() - timedelta(1)).strftime('%d-%m-%Y'))

        # All accounts
        elem = self.driver.find_element_by_xpath("//div[@id='accounts']/div/button")
        elem.click()
        elem.send_keys(Keys.ARROW_UP)
        elem.send_keys(Keys.ENTER)

        # Click download
        elem = self.driver.find_element_by_xpath("//button[text()='Download']")
        elem.click()

        

    #
    #
    # Import downloaded CSV file
    #
    # If accounts = None create the accounts for this bank from the statement file
    #
    def csvimport(self, filename, bank, accounts = []):
        # Check the header...
        header=['Datum', 'Naam / Omschrijving','Rekening',
                'Tegenrekening','Code','Af Bij',
                'Bedrag (EUR)','MutatieSoort','Mededelingen']

        accounts_numbers = []

        if len(accounts) > 0:
            for account in accounts:
                accounts_numbers.append(account.number)


        # Open the file
        print "Opening %s" % filename

        with open(filename, 'r') as csv_file:
            # Open the file
            reader = csv.reader(csv_file, delimiter=',', quotechar='"')

            # Check the header
            h = next(reader)
            if h != header:
                raise ValueError('CSV file doesnt seem to be in the correct format')

            for row in reader:
                # Do we want to import this account?
                if not row[2] in accounts_numbers:
                    if len(accounts) > 0:
                        print "Ignoring transaction for account number %s" % row[2]
                        next
                    else:
                        print 'Found account %s for bank %s' % (row[2], bank.name)
                        accounts_numbers.append(row[2])

                # Get the account or stop here with an exception...
                account = Account.objects.get(number = row[2])

                # Create a new transaction...
                line = Transaction()
                line.account = account

                # Find the date...
                line.date = line.date_user = datetime.strptime(row[0],'%Y%m%d')
    

                # Determine the amount...
                amount = float(row[6].replace('.','').replace(',','.'))
                if row[5] == 'Af':
                    line.trntype = '-'
                    line.amount = -amount
                elif row[5] == 'Bij':
                    line.trntype = '+'
                    line.amount = amount
                else:
                    raise ValueError('No sign for transaction')


                line.memo = smart_text(row[8] + '[' + row[1] + ']')
                line.payee = smart_text(row[1])
                line.refnum = line.generate_refnum()

                line.save_safe()
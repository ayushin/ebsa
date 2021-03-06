from django.utils.encoding import smart_text

from ebsa.connector import Connector
from ebsa.models import Bank, Account, Transaction

from datetime import datetime, date, timedelta

from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.common.exceptions import NoSuchElementException


class ICSConnector(Connector):

    login_url = 'https://www.icscards.nl/ics/login'
    creditcard_url = 'https://www.icscards.nl/ics/mijn/accountoverview'

    def weblogin(self):
        self.open_browser()
        self.driver.get(self.login_url)
        assert "Inloggen - Mijn ICS" in self.driver.title

        elem = self.driver.find_element_by_id("username")
        elem.send_keys(self.bank.username)
        elem = self.driver.find_element_by_id("password")
        elem.send_keys(self.bank.password)

        self.driver.find_element_by_id("trcAccept").click()
        self.driver.find_element_by_id("button-login").click()

        WebDriverWait(self.driver, 3)
        assert "International Card Services" in self.driver.title


    def webimport_creditcard(self, account, datefrom):
        # Download credit card statement
        print "Navigating to the credit card URL..."
        self.driver.get(self.creditcard_url)


        # Expand all the visible rows
        for element in self.driver.find_elements_by_class_name('statement-header'):

            if not element.is_displayed():
                self.driver.find_element_by_class_name('show-more').click()

            while not 'expanded' in element.get_attribute('class'):
                element.click()
                WebDriverWait(self.driver, 3)

            id = element.get_attribute('id')

            if id == 'current':
                #tr_xpath = '//tr[@class="transaction-row transaction-payment statement-' + id + '"]'
                year = str(date.today().year)
            else:
                year = str(id[:4])

            line_number = 1
            for tr_xpath in ('//tr[@class="transaction-row statement-' + id + '"]', '//tr[@class="transaction-row transaction-payment statement-' + id + '"]'):
                for tr in self.driver.find_elements_by_xpath(tr_xpath):

                    elem = None
                    try:
                        elem = tr.find_element_by_class_name('col1')
                    except NoSuchElementException:
                        elem = None

                    # No transactions this month?
                    if not elem:
                        break

                    tr_date = elem.text.encode()

                    # Do not import transactions without date
                    if tr_date == '':
                        continue

                    line = Transaction()
                    line.account = account

                    tr_date = str.replace(tr_date, 'dec', '12')
                    tr_date = str.replace(tr_date, 'nov', '11')
                    tr_date = str.replace(tr_date, 'okt', '10')
                    tr_date = str.replace(tr_date, 'sep', '09')
                    tr_date = str.replace(tr_date, 'aug', '08')
                    tr_date = str.replace(tr_date, 'jul', '07')
                    tr_date = str.replace(tr_date, 'jun', '06')
                    tr_date = str.replace(tr_date, 'mei', '05')
                    tr_date = str.replace(tr_date, 'apr', '04')
                    tr_date = str.replace(tr_date, 'mrt', '03')
                    tr_date = str.replace(tr_date, 'feb', '02')
                    tr_date = str.replace(tr_date, 'jan', '01')

                    line.date_user = line.date = datetime.strptime(tr_date + ' ' + year, '%d %m %Y')

                    name = tr.find_element_by_class_name('col2').text
                    line.payee = smart_text(name)

                    line.memo = smart_text(name + ' ' + tr.find_element_by_class_name('foreign').text)

                    amount = float(tr.find_element_by_xpath("td/div/span[@class='amount']").text.replace('.','').replace(',','.'))

                    sign = tr.find_element_by_xpath("td[not(@id) and not(@class)]/span").text

                    if sign == 'Af':
                        line.trntype = '-'
                        line.amount = -amount
                    elif sign == 'Bij':
                        line.trntype = '+'
                        line.amount = amount
                    else:
                        raise ValueError('No sign for transaction')

                    # We save the statement line number as check_no in order to create unique refnum
                    line.check_no = line_number
                    line_number += 1

                    line.refnum = line.generate_refnum()

                    # Are we done?
                    if line.date < datefrom:
                        return

                    line.save_safe()
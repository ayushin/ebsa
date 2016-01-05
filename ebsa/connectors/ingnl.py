from ebsa.connector import Connector

class IngNLConnector(Connector):
    login_url = 'https://mijn.ing.nl/internetbankieren/SesamLoginServlet'
    download_url = 'https://bankieren.mijn.ing.nl/particulier/overzichten/download/index'
    creditcard_url = 'https://bankieren.mijn.ing.nl/particulier/creditcard/saldo-overzicht/index'

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

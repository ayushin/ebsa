from django.core.management.base import BaseCommand, CommandError
from ebsa.models import Bank, Account
from ebsa.connector import load_connector
from datetime import datetime

class Command(BaseCommand):
    help = 'Imports transactions of the specified account via WEB'

    def add_arguments(self, parser):
        parser.add_argument('bank', nargs=1, type=str)
        parser.add_argument('account', nargs='+', type=str)
        parser.add_argument('--startdate', type=str, default='2015-01-01')

    def handle(self, *args, **options):
        bank_name = options['bank'][0]
        try:
            bank = Bank.objects.get(name=bank_name)
        except Bank.DoesNotExist:
            raise CommandError('Bank "%s" does not exist' % bank_name)

        accounts = []
        if(options['account'][0] == 'all'):
            accounts = Account.objects.filter(bank=bank.id).filter(type='0')
        else:
            for account_name in options['account']:
                try:
                    account = Account.objects.get(name=account_name)
                except Account.DoesNotExist:
                    raise CommandError('Account "%s" does not exist' % account_name)
                accounts.append(account)

        # Do the job
        connector = load_connector(bank)
        connector.webimport(accounts, datefrom = datetime.strptime(options['startdate'], '%Y-%m-%d'))

        self.stdout.write(self.style.SUCCESS('Import completed'))
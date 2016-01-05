from django.core.management.base import BaseCommand, CommandError
from ebsa.models import Bank, Account
from ebsa.connector import load_connector
from datetime import datetime

class Command(BaseCommand):
    help = 'Imports transactions from csv file'

    def add_arguments(self, parser):
        parser.add_argument('filename', nargs=1, type=str)
        parser.add_argument('bank', nargs=1, type=str)
        parser.add_argument('accounts', nargs='+', type=str)

    def handle(self, *args, **options):
        file_name = options['filename'][0]
        bank_name = options['bank'][0]
        try:
            bank = Bank.objects.get(name=bank_name)
        except Bank.DoesNotExist:
            raise CommandError('Bank "%s" does not exist' % bank_name)

        accounts = []
        if(options['accounts'][0] == 'all'):
            accounts = [] # Account.objects.filter(bank=bank.id).filter(type='0')
        else:
            for account_name in options['accounts']:
                try:
                    account = Account.objects.get(name=account_name)
                except Account.DoesNotExist:
                    raise CommandError('Account "%s" does not exist' % account_name)
                accounts.append(account)

        # Do the job
        connector = load_connector(bank)
        connector.csvimport(file_name, bank, accounts)

#    self.stdout.write(self.style.SUCCESS('Successfully closed poll "%s"' % poll_id))
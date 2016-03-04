from django.core.management.base import BaseCommand, CommandError
from ebsa.models import Bank, Account
from ebsa.connector import load_connector
from datetime import datetime

class Command(BaseCommand):
    help = 'Imports transactions of the specified account via WEB'

    def add_arguments(self, parser):
        parser.add_argument('--bank', nargs="+", type=str, default=None)
        parser.add_argument('--account', nargs='+', type=str)
        parser.add_argument('--from', type=str, default=None)

    def handle(self, *args, **options):
        banks = []

        # Do we have a starting date?
        startdate = None
        if options['from']:
            startdate = datetime.strptime(options['from'], '%Y-%m-%d')

        # Accounts take precedence to banks...
        if options['account']:
            if options['bank']:
                raise CommandError("Can't specify both --bank and --account, choose either")

            for account_name in options['account']:
                    try:
                        accounts = [Account.objects.get(name=account_name)]
                    except Account.DoesNotExist:
                        raise CommandError('Account "%s" does not exist' % account_name)
                    connector = load_connector(accounts[0].bank)
                    connector.webimport(accounts, datefrom = startdate)
        else:
            if options['bank']:
                for bank_name in options['bank']:
                    try:
                        bank = Bank.objects.get(name=bank_name)
                    except Bank.DoesNotExist:
                        raise CommandError('Bank "%s" does not exist' % bank_name)
                    banks.append(bank)
            else:
                banks = Bank.objects.filter(active=True)

            for bank in banks:
                accounts = Account.objects.filter(bank=bank.id).filter(active=True)

                # Do the job
                connector = load_connector(bank)
                connector.webimport(accounts, datefrom = startdate)

        self.stdout.write(self.style.SUCCESS('Import completed'))
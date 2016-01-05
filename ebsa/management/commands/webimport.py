from django.core.management.base import BaseCommand, CommandError
from ebsa.models import Bank, Account
from ebsa.connector import load_connector

class Command(BaseCommand):
    help = 'Imports transactions of the specified account via WEB'

    def add_arguments(self, parser):
        parser.add_argument('account', nargs=1, type=str)

    def handle(self, *args, **options):
        try:
            account = Account.objects.get(name=options['account'][0])
        except Account.DoesNotExist:
            raise CommandError('Account "%s" does not exist' % options['account'][0])

        connector = load_connector(account.bank)
	connector.webimport(account)

#    self.stdout.write(self.style.SUCCESS('Successfully closed poll "%s"' % poll_id))

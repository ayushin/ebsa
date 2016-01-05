from django.core.management.base import BaseCommand, CommandError
from ebsa.models import Bank
from ebsa.connector import load_connector


class Command(BaseCommand):
    help = 'Logs into the specified bank via EBSA'

    def add_arguments(self, parser):
        parser.add_argument('bank', nargs=1, type=str)

    def handle(self, *args, **options):
        try:
            bank = Bank.objects.get(name=options['bank'][0])
        except Bank.DoesNotExist:
            raise CommandError('Bank "%s" does not exist' % options['bank'][0])

        connector = load_connector(bank)
        connector.weblogin()

#    self.stdout.write(self.style.SUCCESS('Successfully closed poll "%s"' % poll_id))

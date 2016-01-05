from __future__ import unicode_literals
from django.db.utils import IntegrityError

from hashlib import md5

from django.db import models

# Create your models here.
class Bank(models.Model):
    name = models.CharField(max_length=64)
    url = models.URLField(null=True)
    username = models.CharField(null=True, max_length=32)
    password = models.CharField(null=True, max_length=32)
    connector = models.CharField(null=True,max_length=32)


    def __str__(self):
        return "%s" % self.name

class Account(models.Model):
    ACCOUNT_TYPES = (
        ('0', 'Checking'),
        ('S', 'Savings'),
        ('C', 'Credit Card'),
    )
    type = models.CharField(max_length=1, choices=ACCOUNT_TYPES)

    currency = models.CharField(max_length=3)
    name = models.CharField(max_length=32)
    number = models.CharField(max_length=64)
    bank = models.ForeignKey(Bank)

    def __str__(self):
        return self.name

    def latest_transaction(self):
        return Transaction.objects.filter(account=self.id).latest('date')

class Transaction(models.Model):
    # Date transaction was posted to account
    date = models.DateField()

    memo = models.CharField(max_length=256)

    # Amount of transaction
    amount = models.FloatField()

    # additional fields
    payee = models.CharField(max_length=128)


    # Date user initiated transaction, if known
    date_user = models.DateField()

    # Check (or other reference) number
    check_no = models.CharField(max_length=64)

    # Reference number that uniquely identifies the transaction. Can be used in
    # addition to or instead of a check_no
    refnum = models.CharField(max_length=64, unique=True)

    # Transaction type, must be one of TRANSACTION_TYPES
    TRANSACTION_TYPES = (
        ('+', 'CREDIT'),       # Generic credit
        ('-', 'DEBIT'),        # Generic debit
        ('I', 'INT'),          # Interest earned or paid
        ('D', 'DIV'),          # Dividend
        ('F', 'FEE'),          # FI fee
        ('S', 'SRVCHG'),       # Service charge
        ('D', 'DEP'),          # Deposit
        ('A', 'ATM'),          # ATM debit or credit
        ('.', 'POS'),          # Point of sale debit or credit
        ('X', 'XFER'),         # Transfer
        ('C', 'CHECK'),       # Check
        ('P', 'PAYMENT'),     # Electronic payment
        ('$', 'CASH'),        # Cash withdrawal
        ('>', 'DIRECTDEP'),   # Direct deposit
        ('<', 'DIRECTDEBIT'), # Merchant initiated debit
        ('R', 'REPEATPMT'),   # Repeating payment/standing order
        ('O', 'OTHER'),       # Other
    )

    trntype = models.CharField(max_length=1, choices=TRANSACTION_TYPES)

    account = models.ForeignKey(Account)

    def generate_refnum(self):
        m = md5()
        m.update(str(self.date))
        m.update(str(self.amount))
        m.update(self.payee.encode('utf-8'))
        m.update(self.memo.encode('utf-8'))
        m.update(self.trntype)
        m.update(str(self.check_no))

        return m.hexdigest()

    def __str__(self):
        return """
        ID: %s, date: %s, amount: %s, payee: %s
        memo: %s
        check no.: %s
        """ % (self.id, self.date, self.amount, self.payee, self.memo,
               self.check_no)

    def __unicode__(self):
        return u'%s' % self.__str__()

    def save_safe(self):
        # Check if this transaction is already in the database?
        try:
            self.save()
        except IntegrityError as e:
            if(e.message == 'UNIQUE constraint failed: ebsa_transaction.refnum'):
                print "Duplicate transaction: %s [ %s ] %s  -- ignored" % (self.date, self.amount, self.payee)
            else:
                raise IntegrityError(e)
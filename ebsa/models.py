from __future__ import unicode_literals

from django.db.utils import IntegrityError

from hashlib import md5

from django.db import models
from django.db.models import Sum

from datetime import datetime

# Create your models here.
class Bank(models.Model):
    active = models.BooleanField(default=True)
    name = models.CharField(max_length=64, unique=True)
    url = models.URLField(null=True)
    username = models.CharField(null=True, max_length=32)
    password = models.CharField(null=True, max_length=32)
    connector = models.CharField(null=True,max_length=32)


    def __str__(self):
        return "%s" % self.name

class Account(models.Model):
    active = models.BooleanField(default=True)

    ACCOUNT_TYPES = (
        ('0', 'CHECKING'),
        ('S', 'SAVINGS'),
        ('C', 'CCARD'),
    )
    type = models.CharField(max_length=1, choices=ACCOUNT_TYPES)

    currency = models.CharField(max_length=3)
    name = models.CharField(max_length=32, unique=True)
    number = models.CharField(max_length=64)
    bank = models.ForeignKey(Bank)
    opening_balance = models.FloatField(default=0)

    def __str__(self):
        return self.name

    def latest_transaction(self):
        return Transaction.objects.filter(account=self.id).latest('date')

    def bod_balance(self, date = None):
        if not date:
            date = datetime.now()
        balance = Transaction.objects.filter(account=self.id).filter(date__lt=date.strftime('%Y-%m-%d')).aggregate(Sum('amount'))['amount__sum'] or 0
        return round(self.opening_balance + balance, 2)

    def eod_balance(self, date = None):
        if not date:
            date = datetime.now()
        balance = Transaction.objects.filter(account=self.id).filter(date__lte=date.strftime('%Y-%m-%d')).aggregate(Sum('amount'))['amount__sum'] or 0
        return round(self.opening_balance + balance, 2)

class Category(models.Model):
    CATEGORY_TYPES = (
        ('e', 'Expense'),
        ('i', 'Income'))

    name = models.CharField(max_length=128)
    parent = models.ForeignKey('self')

    type = models.CharField(max_length=1, choices=CATEGORY_TYPES)

class Transaction(models.Model):


    # Date transaction was posted to account
    date = models.DateField()

    class Meta:
        ordering = ['date']

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

    category = models.ForeignKey(Category, default=None, null=True,blank=True)

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
        ID: "%s" %s Date: %s Amount: %s Refnum "%s" Check No: "%s"
            Payee: "%s" Memo: "%s"
        """ % (self.id, dict(self.TRANSACTION_TYPES)[self.trntype], self.date, self.amount,self.refnum,self.check_no,
               self.payee, self.memo)

    def __unicode__(self):
        return u'%s' % self.__str__()

    def save_safe(self):
        # Check if this transaction is already in the database?
        try:
            self.save()
        except IntegrityError as e:
            if(e.message == 'UNIQUE constraint failed: ebsa_transaction.refnum'):
                print "Duplicate transaction: %s [ %s ] %s  -- ignored (%s / %s)" % (self.date, self.amount, self.payee, self.refnum, self.check_no)
            else:
                raise IntegrityError(e)

    def balance(self):
        return self.account.opening_balance + (Transaction.objects.filter(account=self.account.id).filter(date__lte=self.date).aggregate(Sum('amount'))['amount__sum'] or 0)
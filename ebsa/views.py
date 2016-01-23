import re

from django.shortcuts import render, render_to_response
from ebsa.models import Transaction,Account
from dumper import dump

from django.db.models import Q
from datetime import datetime

from ofxtools import OFXTree
from ofxtools.Request import OFXRequest, Aggregate

from StringIO import StringIO


from django.template.loader import get_template
from django.template import Context


# Create your views here.
def account_list(request):
    return render_to_response('accounts.html', {'accounts': Account.objects.all() })

def account_statement(request, account_number, datefrom=None, dateto=None):

    account = Account.objects.get(number=account_number)

    print datefrom

    # XXX Must refactor this
    if account:
        if datefrom:
            if dateto:
                transactions = \
                    Transaction.objects.filter(account=account).filter(date__gte=datefrom).filter(date__lte=dateto).order_by('date')
            else:
                transactions = \
                    Transaction.objects.filter(account=account).filter(date__gte=datefrom).order_by('date')
        else:
            transactions = \
                    Transaction.objects.filter(account=account).order_by('date')

    else:
        statement = {}

    args = {'account_number' : account.number,
            'months': ('01', '02','03', '04', '05', '06', '07', '08', '09', '10', '11', '12'),
            'start_date' : transactions.first().date,
            'start_saldo' : account.bod_balance(transactions.first().date),
            'end_date' : transactions.last().date,
            'end_saldo' : account.eod_balance(transactions.last().date),
            'transactions': transactions}

    return render_to_response('statement.html', args)


def ofx_connect(request):
    print request.body

    ofx = OFXTree()
    ofx.parse(StringIO(request.body))

    # SONRS - server response to signon request
    sonrs = Aggregate.from_etree(ofx.find('SIGNONMSGSRQV1/SONRQ'))

    # Prepare common args list
    # Get the current time in the correct format...
    now = datetime.now().strftime('%Y%m%d%H%M%S.00')
    args = {'dtserver':     now,
            'language':     'ENG'}

    # Signup acctinforq?
    if ofx.find('SIGNUPMSGSRQV1/ACCTINFOTRNRQ/ACCTINFORQ'):
        args['dtacctup'] = now
        args['trnuid'] = ofx.find('SIGNUPMSGSRQV1/ACCTINFOTRNRQ/TRNUID').text
        return ofx_acctinfors(request, args)

    # Is it a STMTTRNRQ?
    leaf = ofx.find('BANKMSGSRQV1/STMTTRNRQ') or ofx.find('CREDITCARDMSGSRQV1/CCSTMTTRNRQ')
    if not leaf:
        assert False

    args['trnuid'] = leaf.find('TRNUID').text
    args['stmts'] = []
    template = None

    # List of the statement requests
    stmtrqs = leaf.findall('STMTRQ')
    if stmtrqs:
        template = 'ofx/stmtrs.ofx'
        for stmtrq in stmtrqs:
            account = Account.objects.filter(number__exact=stmtrq.find('BANKACCTFROM/ACCTID').text).\
                filter(bank__name__exact=stmtrq.find('BANKACCTFROM/BANKID').text).\
                filter(type__exact=dict((y, x) for x, y in Account.ACCOUNT_TYPES)[stmtrq.find('BANKACCTFROM/ACCTTYPE').text]).distinct()[0]
            assert account
            args['stmts'].append({'account' : account,
                                  'date_from' : stmtrq.find('INCTRAN/DTSTART').text })
    else:
        ccstmtrqs = leaf.findall('CCSTMTRQ')
        assert ccstmtrqs
        template = 'ofx/ccstmtrs.ofx'
        for ccstmtrq in ccstmtrqs:
            account = Account.objects.filter(number__exact=ccstmtrq.find('CCACCTFROM/ACCTID').text).\
                filter(type__exact='C').distinct()[0]
            assert account
            args['stmts'].append({'account' : account,
                      'date_from' : ccstmtrq.find('INCTRAN/DTSTART').text })

    return ofx_stmtrs(request, template, args)



def ofx_stmtrs(request, template, args):
    for st in args['stmts']:
        date_from = st['date_from'][0:4] + '-' + st['date_from'][4:6] + '-' + st['date_from'][6:8]
        st['transactions'] = Transaction.objects.filter(account=st['account']).filter(date__gte=date_from).order_by('date')

        st['dtstart'] = st['transactions'].first().date
        st['ledgerbal'] = {}
        st['availbal'] = {}
        st['ledgerbal']['date'] = st['availbal']['date'] = st['dtend'] = st['transactions'].last().date
        st['ledgerbal']['amount'] = st['availbal']['amount'] = st['account'].eod_balance(st['dtend'])


    print get_template(template).render(args)
    print "DATE FROM: %s " % date_from

    return render_to_response(template, args)

def ofx_acctinfors(request, args):
    # Produce the list of available accounts
    for account_type in [('current_accounts', '0'),('savings_accounts','S'),('ccards','C')]:
        accounts = Account.objects.filter(type=account_type[1])
        if accounts:
            args[account_type[0]] = accounts


    return render_to_response('ofx/acctinfors.ofx', args)

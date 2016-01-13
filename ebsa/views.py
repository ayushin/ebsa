from django.shortcuts import render, render_to_response
from ebsa.models import Transaction,Account
from django.db.models import Q
from datetime import datetime
from ofxparse import OfxParser
from StringIO import StringIO

# Create your views here.
def account_list(request):
    return render_to_response('account_list.html')

def account_statement(request, account, datefrom=None, dateto=None):

    account_id = Account.objects.get(number=account)

    print datefrom

    # XXX Must refactor this
    if account_id:
        if datefrom:
            if dateto:
                transactions = \
                    Transaction.objects.filter(account=account_id).filter(date__gte=datefrom).filter(date__lte=dateto).order_by('date')
            else:
                transactions = \
                    Transaction.objects.filter(account=account_id).filter(date__gte=datefrom).order_by('date')
        else:
            transactions = \
                    Transaction.objects.filter(account=account_id).order_by('date')

    else:
        statement = {}

    # Calculate the end saldo
    start_saldo = 0
    saldo = start_saldo

    for t in transactions:
        saldo += t.amount

    template = "statement.html"

    if(request.GET.get('display', '') == 'ofx'):
        template = "statement.ofx"

    return render_to_response(template,{'account' : account,
                'start_date' : transactions.first().date,
                'start_saldo' : start_saldo,
                'end_date' : transactions.last().date,
                'end_saldo' : saldo,
                'transactions': transactions})

def ofx_connect(request):
    #ofx = OfxParser.parse(StringIO(request.body))
    #print ofx.__str__()
    print request.body

    args = {'st_status' : 0,
            'st_severity': 'INFO',
            'trnuid':       1233411,
            'dtacctup':     '20160101',
            'language':     'ENG'}

    for account_type in [('current_accounts', '0'),('savings_accounts','S'),('ccards','C')]:
        accounts = Account.objects.filter(type=account_type[1])
        if accounts:
            args[account_type[0]] = accounts


    return render_to_response('ofx/acctinfotrnrs.ofx', args)
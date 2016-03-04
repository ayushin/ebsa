from django.contrib import admin
from models import Bank, Account, Transaction

# Register your models here.
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ( 'account', 'date', 'amount', 'payee','memo','check_no', 'trntype')
    list_filter = ('account','payee')
    list_display_links = ('date', 'amount', 'payee','memo','check_no', 'trntype')
    date_hierarchy = 'date'

@admin.register(Bank)
class BankAdmin(admin.ModelAdmin):
    pass

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('active', 'name', 'bank', 'type', 'number', 'currency','opening_balance','eod_balance' )
    list_display_links = ('name', 'number')
    list_filter = ('bank', 'currency')

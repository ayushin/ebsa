# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-01-05 15:07
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('0', 'Checking'), ('S', 'Savings'), ('C', 'Credit Card')], max_length=1)),
                ('currency', models.CharField(max_length=3)),
                ('name', models.CharField(max_length=32)),
                ('number', models.CharField(max_length=64)),
            ],
        ),
        migrations.CreateModel(
            name='Bank',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64)),
                ('url', models.URLField(null=True)),
                ('username', models.CharField(max_length=32, null=True)),
                ('password', models.CharField(max_length=32, null=True)),
                ('connector', models.CharField(max_length=32, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('memo', models.CharField(max_length=256)),
                ('amount', models.FloatField()),
                ('payee', models.CharField(max_length=128)),
                ('date_user', models.DateField()),
                ('check_no', models.CharField(max_length=64)),
                ('refnum', models.CharField(max_length=64)),
                ('trntype', models.CharField(choices=[('+', 'CREDIT'), ('-', 'DEBIT'), ('I', 'INT'), ('D', 'DIV'), ('F', 'FEE'), ('S', 'SRVCHG'), ('D', 'DEP'), ('A', 'ATM'), ('.', 'POS'), ('X', 'XFER'), ('C', 'CHECK'), ('P', 'PAYMENT'), ('$', 'CASH'), ('>', 'DIRECTDEP'), ('<', 'DIRECTDEBIT'), ('R', 'REPEATPMT'), ('O', 'OTHER')], max_length=1)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ebsa.Account')),
            ],
        ),
        migrations.AddField(
            model_name='account',
            name='bank',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ebsa.Bank'),
        ),
    ]

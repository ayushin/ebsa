#!/bin/csh
EBSA_HOME=
cd $EBSA_HOME
source .venv/bin/activate.csh
./manage.py $*

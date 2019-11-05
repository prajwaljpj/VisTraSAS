#!/bin/bash

export PYTHONPATH=${PWD}/deep_sort:$PYTHONPATH

# checking if in python env

INVENV=$(python -c 'import sys; print ("1" if hasattr(sys, "real_prefix") else "0")')

if [ $INVENV -eq 1 ]
then echo "inside python environment"
else echo "WARNING:: outside python environment" 
fi

./install/runYolov3
python3 main.py

#!/bin/bash

if [ "$EUID" -ne 0 ]
    then 
        echo "Usage: sudo -H ./setup.sh"
        exit
fi

apt-get update;
apt-get install python3 python3-pip;

pip3 install --upgrade pip;
pip3 install setuptools;
pip3 install -r requirements.txt

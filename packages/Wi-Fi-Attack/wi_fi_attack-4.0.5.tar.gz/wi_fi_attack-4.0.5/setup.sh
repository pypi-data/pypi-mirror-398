#!/bin/bash
python3 -m venv myvenv
source myvenv/bin/activate
pip3 install -r requirements.txt
sudo apt install gnome-terminal
chmod +x src/wifi_cracker.py
clear
sudo python3 src/wifi_cracker.py

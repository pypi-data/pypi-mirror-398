# Wi-Fi Attack Automation Tool
![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)
![Platform](https://img.shields.io/badge/%7C%20Linux-green?logo=linux)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Version](https://img.shields.io/badge/Version-4.0-orange)

---

This tool is a Python-based utility that automates the process of Wi-Fi network penetration testing, including handshake capture, password cracking, DoS attacks, and password list generation. It acts as a wrapper around powerful tools like `aircrack-ng`, `airodump-ng`, `aireplay-ng`, `crunch`, and `wireshark`.

**For Authorized Penetration Testing Only**
This tool is intended for security professionals and researchers on networks they own or are authorized to audit. Unauthorized access or attacks on networks are illegal and unethical.

---

## Features

* Scan for Access Points and capture detailed information.
* Detect and lock on target network channels.
* Capture WPA/WPA2 handshakes.
* Launch deauthentication (DoS) attacks.
* Crack captured handshakes using a wordlist or custom-generated passwords.
* Generate password lists with custom masks using `crunch`.
* Launch Wireshark for EAPOL packet inspection.
* Interactive terminal-based menu interface.

---


## Project Tree
```
├── assets (All password files created should be in this folder)
│   ├── generated_password.txt
│   └── john.lst
├── LICENSE
├── README.md
├── requirements.txt
├── setup.sh
├── run.sh (PIP installation)
└── src
    ├── animation.py
    ├── GenCharlist.py
    ├── Get_AP.py
    ├── mac_address_detector.py
    ├── network_scanner.py
    └── wifi_cracker.py
```

## Option 1: Install & Run via github
### 1. Clone the Repository

```bash
git clone https://github.com/cyb2rS2c/Wi-Fi_ATTACK.git
cd Wi-Fi_ATTACK
```
## 2. Run 

```bash
chmod +x setup.sh;source ./setup.sh
```
Root privileges are required for most network interface operations.

## Option 2: Install & Run via pip (Recommended)
```
curl -LO https://raw.githubusercontent.com/cyb2rS2c/Wi-Fi_ATTACK/refs/heads/main/run.sh
sudo chmod +x run.sh;./run.sh 
```

## Screenshots

View - [**Screenshots**](https://github.com/cyb2rS2c/Wi-Fi_ATTACK#Screenshots)

---

## Author
cyb2rS2c - [**GitHub Profile**](https://github.com/cyb2rS2c)

## License
MIT License. See [**LICENSE**](https://github.com/cyb2rS2c/Wi-Fi_ATTACK/blob/main/LICENSE) for more info.

## Legal Disclaimer

This software is provided for **educational** and **authorized pentesting** only. The author is not responsible for any misuse or damage caused. Always get **explicit permission** before auditing any network.
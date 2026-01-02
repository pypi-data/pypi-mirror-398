import subprocess
from tabulate import tabulate

def find_info_about_ap():
    command_str = 'nmcli -f SSID,CHAN,BSSID dev wifi'
    
    result = subprocess.run(
        command_str.split(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    if result.returncode != 0:
        print("Error:", result.stderr)
        return None, None, None

    lines = result.stdout.splitlines()
    raw_networks = [line for line in lines[1:] if line.strip()]

    if not raw_networks:
        print("No networks found")
        return None, None, None
    
    networks = []
    for line in raw_networks:
        parts = line.split()
        if len(parts) > 3:
            ssid = " ".join(parts[:-2])
            chan = parts[-2]
            bssid = parts[-1]
        else:
            ssid, chan, bssid = parts
        
        networks.append([ssid, chan, bssid])
    print("\nAvailable networks:")
    table_data = []
    for i, row in enumerate(networks):
        table_data.append([i, row[0], row[1], row[2]])

    print(tabulate(table_data, headers=["Index", "SSID", "Channel", "BSSID"], tablefmt="psql"))
    while True:
        try:
            choice = int(input(f"Select AP index (0-{len(networks)-1}): "))
            if 0 <= choice < len(networks):
                break
            print("Invalid index.")
        except ValueError:
            print("Enter a number.")

    ssid, chan, bssid = networks[choice]

    return ssid, chan, bssid

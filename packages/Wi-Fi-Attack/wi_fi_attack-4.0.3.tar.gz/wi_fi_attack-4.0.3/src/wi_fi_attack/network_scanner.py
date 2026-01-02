import subprocess
import time

def scan_network(ip_range):
    results = []
    if ',' in ip_range:
        ips = [ip.strip() for ip in ip_range.split(',')]
    else:
        ips = [ip_range.strip()]

    for ip in ips:
        try:
            result = subprocess.run(
                ['nmap', '-sS', ip],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            results.append(result.stdout)
            time.sleep(5)
        except FileNotFoundError:
            return "Error: nmap is not installed."

    return "\n".join(results)

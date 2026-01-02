import re


def find_mac_and_state(scan_output):
    ip_mac_pattern = r"(\d+\.\d+\.\d+\.\d+)\s+(Host is up|Host is down).*?MAC Address:\s([0-9A-Fa-f:]{17})\s*\((.*?)\)"
    host_pattern = r"(\d+\.\d+\.\d+\.\d+)\s+(Host is up|Host is down)"

    mac_data = {}
    for match in re.finditer(ip_mac_pattern, scan_output, re.DOTALL):
        ip = match.group(1)
        state = match.group(2)
        mac = match.group(3)
        device_type = match.group(4)
        mac_data[ip] = (mac, state, device_type)
    
    for match in re.finditer(host_pattern, scan_output):
        ip = match.group(1)
        state = match.group(2)
        if ip not in mac_data:
            mac_data[ip] = ("N/A", state, "Unknown")
    
    return mac_data
import os
import configparser
import json
import sys
import string
import argparse
import socket
import ipaddress
from art import tprint
from concurrent.futures import ProcessPoolExecutor
from termcolor import colored
from threading import Thread
from tqdm import tqdm
from SnakeScan.Check_subnet import Check_network
from SnakeScan.PoolExecutor import PoolProcessExecutor
from SnakeScan.Get_ssl import Get_ssl
from SnakeScan.Pool_UDP_Executor import PoolExecutorUDP

OpenPorts = []
threads = []
portsopen = 0
portsclosed = 0
ports = {
    20: "FTP-Data",
    21: "FTP-Control",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    43: "Whois",
    53: "DNS",
    70: "Gopher",
    79: "FINGER",
    80: "HTTP",
    110: "POP3",
    111: "RPC",
    113: "ident",
    115: "SFTP",
    135: "MSRPC",
    139: "NetBIOS-SSN",
    143: "IMAP",
    179: "BGP",
    194: "IRC",
    389: "LDAP",
    443: "HTTPS",
    445: "SMB",
    465: "SMTPS",
    587: "SMTP Submission",
    631: "IPP",
    636: "LDAPS",
    873: "RSYNC",
    993: "IMAPS",
    995: "POP3S",
    1080: "SOCKS",
    1433: "SQL Server",
    1521: "Oracle",
    2082: "CPanel",
    2083: "CPanel",
    2222: "SSH",
    3128: "HTTP Proxy",
    3306: "MySQL",
    3389: "RDP",
    5432: "PostgreSQL",
    5900: "VNC",
    8000: "HTTP Alternate",
    8080: "HTTP Alternate",
    8443: "HTTPS Alternate",
    8888: "HTTP Alternate",
    10000: "Webmin",
    27017: "MongoDB",
}


def Load_config(ports):
    try:
        config = configparser.ConfigParser()
        package_dir = os.path.dirname(__file__)

        config_path = os.path.join(package_dir, "config.ini")

        config.read(config_path)

        if "Settings" in config and ports in config["Settings"]:
            return config["Settings"][ports]
    except Exception as e:
        print(e)
        sys.exit()


def Save_config(path_tcp, path_udp):
    if path_tcp:
        if os.path.exists(path_tcp):
            pass
        else:
            print(f"Error: File not found: {path_tcp}")
            sys.exit()
    else:
        path_tcp = ""
    if path_udp:
        if os.path.exists(path_udp):
            pass
        else:
            print(f"Error: File not found: {path_udp}")
            sys.exit()
    else:
        path_udp = ""
    try:
        config = configparser.ConfigParser()
        package_dir = os.path.dirname(__file__)

        config_path = os.path.join(package_dir, "config.ini")
        config["Settings"] = {"path_tcp": path_tcp, "path_udp": path_udp}
        with open(config_path, "w") as configfile:
            config.write(configfile)

    except Exception as e:
        print(e)
        sys.exit()


def load_json_config(filepath):
    try:
        if not os.path.isabs(filepath):
            filepath = os.path.abspath(filepath)

        with open(filepath, "r", encoding="utf-8") as f:
            ports = json.load(f)
        return {int(k): v for k, v in ports.items()}
    except FileNotFoundError:
        if filepath:
            pass
        else:
            print(f"Error: File not found: {filepath}")
            sys.exit()
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in file: {filepath} - {e}")
        sys.exit()
    except Exception as e:
        print(f"Error loading file: {e}")
        sys.exit()


def main():
    pass


path_tcp = Load_config("path_tcp")
path_udp = Load_config("path_udp")
if path_tcp and path_udp:
    ports_tcp = load_json_config(path_tcp)
    ports_udp = load_json_config(path_udp)
else:
    ports_tcp = False
    ports_udp = False
if path_tcp:
    ports_tcp = load_json_config(path_tcp)
else:
    ports_tcp = False
if path_udp:
    ports_udp = load_json_config(path_udp)
else:
    path_udp = False


if __name__ == "__main__":
    main()

version = "1.8.5"


def is_port_open(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.settimeout(1)
            s.connect((host, port))
        except (OSError, socket.timeout):
            return False
        else:
            return True


def is_port_open_threads(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.settimeout(1)
            s.connect((host, port))
        except (OSError, socket.timeout):
            try:
                print(
                    f"Closed{colored('|X|','red')}-->{colored(ports.get(port),'light_red')}{colored(f'|{port}|','red')}"
                )
            except Exception as e:
                print(f"Closed{colored('|X|','red')}-->{colored(f'|{port}|','red')}")
        else:
            print(
                f"Open{colored('|√|','green')}-->{colored(ports.get(port),'light_green')}{colored(f'|{port}|','green')}"
            )


def Ports(str=""):
    rangeports = []
    rangeport = []
    port = []
    doneports = []
    str = str.split(",")
    for p in range(len(str)):
        if "-" in str[p]:
            rangeports.append(str[p])
        else:
            port.append(str[p])
    for n in range(len(port)):
        for i in string.punctuation:
            if i in port[n]:
                port[n] = port[n].replace(i, "")
    for r in range(len(rangeports)):
        rangeport = rangeports[r].split("-")
        for i in range(len(rangeport)):
            doneports.append(rangeport[i])
    try:
        return doneports, port
    except Exception as e:
        rangeport = ""
        return doneports, port
        sys.exit()


def SnakeArgs():
    parser = argparse.ArgumentParser(
        description="SnakeScan - It's a command line library for scan and get information about ip."
    )
    parser.add_argument("host", nargs="?", default="None")
    parser.add_argument(
        "-d",
        "--dictonary",
        required=False,
        default="None",
        help="Use custom port dictionaries",
    )
    parser.add_argument(
        "-u", "--udp", action="store_true", help="Use UDP ports for scanning"
    )
    parser.add_argument(
        "-ds",
        "--dictshow",
        action="store_true",
        help="Shows paths to port dictionaries",
    )
    parser.add_argument(
        "-dr",
        "--dictremove",
        action="store_true",
        help="Removes user port dictionaries",
    )
    parser.add_argument(
        "-gs", "--getssl", action="store_true", help="Get official ssl certificate"
    )
    parser.add_argument(
        "-sp",
        "--speed",
        action="store_true",
        help="Scan with using PoolProcessExecutor",
    )
    parser.add_argument("-v", "--version", action="store_true", help="Library version")
    parser.add_argument(
        "-i", "--info", action="store_true", help="IP information about host"
    )
    parser.add_argument("-p", "--ports", help="Range ports to scan host")
    parser.add_argument(
        "-t", "--thread", action="store_true", help="Scan with using ThreadPoolExecutor"
    )
    parser.add_argument("-ch", "--check", action="store_true", help="Scan ip subnet")
    parser.add_argument(
        "-l",
        "--local",
        action="store_true",
        help="View you public ip - need internet",
    )
    args = parser.parse_args()
    return args


port_user = SnakeArgs().ports
host = SnakeArgs().host.split(",")
filepath = SnakeArgs().dictonary.split(",")
for n in range(len(host)):
    if host[n].startswith("http://"):
        host[n] = host[n].strip()
        host[n] = host[n].split("http:")
        host[n] = host[n][1].strip("//")
        host[n] = host[n].split("/")
        host[n] = host[n][0]
        for i in range(len(host)):
            if host[n][i] == "/":
                host[n] = host[n][0:i]
for n in range(len(host)):
    if host[n].startswith("https://"):
        host[n] = host[n].strip()
        host[n] = host[n].split("https:")
        host[n] = host[n][1].strip("//")
        host[n] = host[n].split("/")
        host[n] = host[n][0]
        for i in range(len(host)):
            if host[n][i] == "/":
                host[n] = host[n][0:i]
if host[0] == "None":
    host[0] = "localhost"
if filepath[0] != "None":
    if len(filepath) >= 2:
        ports_tcp = load_json_config(filepath[0])
        ports_udp = load_json_config(filepath[1])
        Save_config(filepath[0], filepath[1])
    else:
        ports_tcp = load_json_config(filepath[0])
        Save_config(filepath[0], "")
if SnakeArgs().udp:

    def is_port_open(host, port, timeout=1):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)
            message = b"Test UDP packet"
            address = (host, port)

            sock.sendto(message, address)

            try:
                data, server = sock.recvfrom(4096)
                print(f"Response received: {data.decode()} from {server}")
                is_open = True
            except socket.timeout:
                is_open = False
            except ConnectionRefusedError:
                is_open = False

            sock.close()
            return is_open

        except socket.gaierror:
            return None
        except socket.error as e:
            return False

    def is_port_open_threads(host, port, timeout=1):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)
            message = b"Test UDP packet"
            address = (host, port)

            sock.sendto(message, address)

            try:
                data, server = sock.recvfrom(4096)
                print(f"Response received: {data.decode()} from {server}")
                print(
                    f"Open{colored('[√]','green')}-->{colored(ports.get(port),'light_green')}{colored(f'|{port}|','green')}"
                )
            except socket.timeout:
                print(
                    f"Closed{colored('[X]','red')}-->{colored(ports.get(port),'light_red')}{colored(f'|{port}|','red')}"
                )
            except ConnectionRefusedError:
                sock.close()
        except socket.gaierror:
            pass
        except socket.error as e:
            pass

    if ports_udp:
        ports = ports_udp
    else:
        ports = {
            7: "ECHO",
            9: "DISCARD",
            13: "DAYTIME",
            17: "QOTD (Quote of the Day)",
            19: "CHARGEN (Character Generator)",
            53: "DNS (Domain Name System)",
            67: "DHCP Server",
            68: "DHCP Client",
            69: "TFTP (Trivial File Transfer Protocol)",
            111: "RPC (Remote Procedure Call)",
            123: "NTP (Network Time Protocol)",
            137: "NetBIOS Name Service",
            138: "NetBIOS Datagram Service",
            161: "SNMP (Simple Network Management Protocol)",
            162: "SNMP Trap",
            443: "QUIC (Quick UDP Internet Connections)",
            500: "ISAKMP (Internet Security Association and Key Management Protocol)",
            520: "RIP (Routing Information Protocol)",
            1434: "Microsoft SQL Server Dynamic Port Allocation",
            4500: "IPsec NAT-Traversal (NAT-T)",
            5353: "mDNS (Multicast DNS)",
            5355: "LLMNR (Link-Local Multicast Name Resolution)",
            1900: "SSDP (Simple Service Discovery Protocol)",
            3478: "STUN (Session Traversal Utilities for NAT)",
            5060: "SIP (Session Initiation Protocol)",
            5061: "SIP (Session Initiation Protocol) (TLS)",
            20777: "Garmin Training Center",
            3074: "Xbox Live",
            3479: "TURN (Traversal Using Relays around NAT)",
            4126: "Muon",
            50000: "Drone (Drone Protocol)",
            60000: "RDP (Remote Desktop Protocol) over UDP",
            5000: "fCoE (Fibre Channel over Ethernet)",
            5001: "HP OpenView Operations Agent",
            1719: "H.323 Gatekeeper RAS",
            1720: "H.323 Call Signaling",
            1812: "RADIUS authentication",
            1813: "RADIUS accounting",
            5222: "XMPP client connection",
            5269: "XMPP server connection",
        }

else:
    if ports_tcp:
        ports = ports_tcp
    else:
        ports = {
            20: "FTP-Data",
            21: "FTP-Control",
            22: "SSH",
            23: "Telnet",
            25: "SMTP",
            43: "Whois",
            53: "DNS",
            70: "Gopher",
            79: "FINGER",
            80: "HTTP",
            110: "POP3",
            111: "RPC",
            113: "ident",
            115: "SFTP",
            135: "MSRPC",
            139: "NetBIOS-SSN",
            143: "IMAP",
            179: "BGP",
            194: "IRC",
            389: "LDAP",
            443: "HTTPS",
            445: "SMB",
            465: "SMTPS",
            587: "SMTP Submission",
            631: "IPP",
            636: "LDAPS",
            873: "RSYNC",
            993: "IMAPS",
            995: "POP3S",
            1080: "SOCKS",
            1433: "SQL Server",
            1521: "Oracle",
            2082: "CPanel",
            2083: "CPanel",
            2222: "SSH",
            3128: "HTTP Proxy",
            3306: "MySQL",
            3389: "RDP",
            5432: "PostgreSQL",
            5900: "VNC",
            8000: "HTTP Alternate",
            8080: "HTTP Alternate",
            8443: "HTTPS Alternate",
            8888: "HTTP Alternate",
            10000: "Webmin",
            27017: "MongoDB",
        }

if SnakeArgs().dictremove:
    try:
        config = configparser.ConfigParser()
        package_dir = os.path.dirname(__file__)
        config_path = os.path.join(package_dir, "config.ini")
        config["Settings"] = {"path_tcp": "", "path_udp": ""}
        with open(config_path, "w") as configfile:
            config.write(configfile)
    except Exception as e:
        print(e)
        sys.exit()
if SnakeArgs().ports:
    rangeports, port_user = Ports(port_user)
    for i in range(len(port_user)):
        try:
            port_user[i] = int(port_user[i])
        except Exception as e:
            print(f"Incorrect input,please check the help documentation:{e}")
            sys.exit()
    for n in range(len(host)):
        for port in range(len(port_user)):
            if is_port_open(host[n], port_user[port]):
                print(
                    f"Open{colored('|√|','green')}{host[n]}-->{colored(f'{str(ports.get(port_user[port],''))}','light_green')}{colored(f'|{port_user[port]}|','green')}"
                )
            else:
                try:
                    print(
                        f"Closed{colored('|X|','red')}{host[n]}-->{colored(str(ports.get(port_user[port],'')),'light_red')}{colored(f'|{port_user[port]}|','red')}"
                    )
                except:
                    print(
                        f"Closed{colored('|X|','red')}{host[n]}-->{colored(f'|{port_user[port]}|','red')}"
                    )
        try:
            first = rangeports[::2]
            second = rangeports[1::2]
            minimal = min(len(first), len(second))
            for i in range(minimal):
                if int(first[i]) > int(second[i]):
                    number = second[i]
                    second[i] = first[i]
                    first[i] = number
            for i in range(minimal):
                for port in tqdm(range(int(first[i]) + 1, int(second[i]) + 1)):
                    if is_port_open(host[n], port):
                        for name in ports:
                            if port == name:
                                OpenPorts = [port]
                                portsopen += 1
                    else:
                        portsclosed += 1
                if OpenPorts:
                    for i in OpenPorts:
                        print(f"Open{colored('|√|','green')}-->{ports[i]}|{i}|")
                    print(f"|{host[n]}|".center(60, "—"))
                    print(f"Closed{colored('|X|','red')}:{portsclosed}")
                    portsclosed = 0
                    print(f"Open{colored('|√|','green')}:{portsopen}")
                    portsopen = 0
                    print("—" * 60)
                else:
                    print(f"|{host[n]}|".center(60, "—"))
                    print(f"Closed{colored('|X|','red')}:{portsclosed}")
                    portsclosed = 0
                    print(f"Open{colored('|√|','green')}:{portsopen}")
                    portsopen = 0
                    print("—" * 60)
        except Exception as e:
            print(e)
            sys.exit()
if SnakeArgs().check:
    for n in range(len(host)):
        Check_network(host[n])
if SnakeArgs().local:
    local = ""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        local = s.getsockname()[0]
    except Exception as e:
        local = f"{e}"
    finally:
        s.close()
        print("|localhost|".center(60, "—"))
        print(f"Public IP:{local}")
        print(f"".center(60, "—"))
if SnakeArgs().info:
    if host[0] == "None":
        host[0] = "localhost"
    for n in range(len(host)):
        print(f"|{host[n]}|".center(60, "—"))
        try:
            host[n] = socket.gethostbyname(host[n])
        except Exception as e:
            try:
                hostname, list, iplist = socket.gethostbyaddr(host[n])
            except Exception as e:
                if host[n].startswith("[") and host[n].endswith("]"):
                    host[n] = host[n][1:-1]
                else:
                    host[n] = host[n].split("[")
                    for i in range(len(host)):
                        host[n] = host[n][i - 1].split("]")
                    host[n] = host[n][0]
                try:
                    hostname, list, iplist = socket.gethostbyaddr(host[n])
                except Exception as e:
                    print(e)
                    sys.exit()

        hosting = ""
        hosting = host[n].split(".")
        hosting[len(hosting) - 1] = "0"
        network = ""
        for i in range(len(hosting) - 1):
            network += hosting[i] + "."
        network += "0"
        network += "/24"
        hosting = network
        try:
            if host[n].startswith("[") and host[n].endswith("]"):
                host[n] = host[n][1:-1]
            else:
                host[n] = host[n].split("[")
                for i in range(len(host)):
                    host[n] = host[n][i - 1].split("]")
                host[n] = host[n][0]
            ip_obj = ipaddress.ip_address(host[n])
            if ip_obj.version == 6:

                try:
                    network = host[n] + "/64"
                    network_obj = ipaddress.ip_network(network)
                except Exception as e:
                    pass
                    try:
                        network = host[n] + "/128"
                        network_obj = ipaddress.ip_network(network)
                    except Exception as e:
                        pass
        except Exception as e:
            print(e)
        print(f"Type IP: {type(ip_obj)}")
        print(f"Version IP: {ip_obj.version}")
        network_obj = ipaddress.ip_network(network)
        print(f"Network: {network_obj}")
        print(f"Subnet mask: {network_obj.netmask}")
        try:
            hostname = socket.gethostbyaddr(host[n])
            print(f"Host:{hostname[0]}")
        except:
            hostname = "Undefined"
            print(f"Host:{hostname}")
        try:
            print(f"IP:{socket.gethostbyname(host[n])}")
        except Exception as e:
            try:
                hostname, list, iplist = socket.gethostbyaddr(host[n])
                print(f"IP:{socket.gethostbyname(hostname)}")
            except:
                pass
        finally:
            print("".center(60, "—"))


if SnakeArgs().thread:
    if SnakeArgs().udp:
        try:
            host[n] = socket.gethostbyname(host[n])
        except Exception as e:
            print(f"|{host[n]}|".center(60, "—"))
            print(e)
            sys.exit()

    for n in range(len(host)):
        print(f"|{host[n]}|".center(60, "—"))

        for port in ports.keys():
            t = Thread(
                target=is_port_open_threads,
                kwargs={"host": host[n], "port": port},
            )
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
if SnakeArgs().version:
    print("|Version|".center(60, "—"))
    print(f"SnakeScan_Build_{version}")
    print("".center(60, "—"))
if SnakeArgs().speed:
    if SnakeArgs().udp:
        try:
            host[n] = socket.gethostbyname(host[n])
        except Exception as e:
            print(f"|{host[n]}|".center(60, "—"))
            print(e)
            sys.exit()
        for n in range(len(host)):
            print(f"|{host[n]}|".center(60, "—"))
            PoolExecutorUDP(host[n], ports)
        sys.exit()
    for n in range(len(host)):
        print(f"|{host[n]}|".center(60, "—"))
        PoolProcessExecutor(host[n], ports)
if SnakeArgs().getssl:
    for n in range(len(host)):
        print(f"|{host[n]}|".center(60, "—"))
        Get_ssl(host[n])
        print("".center(60, "—"))
if SnakeArgs().dictshow:
    if path_tcp:
        print("|Paths|".center(60, "—"))
        print(f"TCP:{path_tcp}")
        print("".center(60, "—"))
    else:
        print("|Paths|".center(60, "—"))
        print("TCP:path not specified")
        print("".center(60, "—"))
    if path_udp:
        print(f"UDP:{path_udp}")
        print("".center(60, "—"))
    else:
        print("UDP:path not specified")
        print("".center(60, "—"))

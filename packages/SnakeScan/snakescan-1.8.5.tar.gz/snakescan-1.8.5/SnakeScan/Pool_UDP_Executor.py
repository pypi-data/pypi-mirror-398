import socket
from termcolor import colored
from concurrent.futures import ProcessPoolExecutor


def is_port_open_threads(host, port, ports, timeout=1):
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


def PoolExecutorUDP(host, ports):
    with ProcessPoolExecutor(max_workers=None) as executor:
        try:
            for port in ports.keys():
                future = executor.submit(is_port_open_threads, host, port, ports)

        except Exception as e:
            print(e)

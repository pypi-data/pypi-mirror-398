import socket
from termcolor import colored
from concurrent.futures import ProcessPoolExecutor


def is_port_open_threads(host, port, ports):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.settimeout(1)
            s.connect((host, port))
        except (OSError, socket.timeout):
            try:
                print(
                    f"Closed{colored('|X|','red')}-->{colored(ports.get(port),'light_red')}{colored(f'|{port}|','red')}"
                )
            except:
                print(f"Closed{colored('|X|','red')}-->{colored(f'|{port}|','red')}")
        else:
            print(
                f"Open{colored('|√|','green')}-->{colored(ports.get(port),'light_green')}{colored(f'|{port}|','green')}"
            )


def PoolProcessExecutor(host, ports):
    with ProcessPoolExecutor(max_workers=None) as executor:
        try:
            for port in ports.keys():
                future = executor.submit(is_port_open_threads, host, port, ports)

        except Exception as e:
            print(e)

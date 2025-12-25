import socket
import ssl
import sys


def Get_ssl(host, port=443, timeout=2, protocol="HTTP/1.0"):
    try:
        sock = socket.create_connection((host, port), timeout)
        context = ssl.create_default_context()
        ssock = context.wrap_socket(sock, server_hostname=host)
        ssock.sendall(f"GET / {protocol}\r\nHost:{host}\r\n\r\n".encode("utf-8"))
        data = ssock.recv(4096)
        print(data.decode(errors="replace"))
        ssock.close()
    except Exception as e:
        print(e)

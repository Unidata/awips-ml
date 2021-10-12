import socket
import sys

if __name__ == '__main__':
    msg = sys.argv[1]
    host = "tfc"
    port = 7000
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(bytes(msg, 'utf-8'))

    

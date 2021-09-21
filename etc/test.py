import socket
def send(msg, host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(bytes(msg, 'utf-8'))
        data = s.recv(1024)
        print(data)

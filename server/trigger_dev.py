import socket
import sys

if __name__ == '__main__':
    host = "localhost"
    port = 7000
    msg = "/Users/rmcmahon/dev/awips-ml/server/dev_test/OR_ABI-L2-CMIPPR-M6C09_G16_s20212861650200_e20212861650200_c20212861650200.nc4"
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(bytes(msg, 'utf-8'))

    

import socket
import sys
import yaml

if __name__ == '__main__':
    msg = sys.argv[1]

    # load in configs
    with open("/server/config.yaml") as file:
        config_dict = yaml.load(file, Loader=yaml.FullLoader)

    handler_type="edex_container"
    host = config_dict[handler_type]["pygcdm_server"]
    port = config_dict[handler_type]["tx_port_trigger"]
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(bytes(msg, 'utf-8'))

    

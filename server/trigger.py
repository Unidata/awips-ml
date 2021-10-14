import socket
import sys
import yaml

if __name__ == '__main__':
    msg = sys.argv[1]
    #handler_type = sys.argv[2]
    handler_type="edex_container"

    # load in configs
    with open("/server/config.yaml") as file:  # BONE change this
        config_dict = yaml.load(file, Loader=yaml.FullLoader)
    try:
        assert handler_type in ["process_container", "edex_container"]
    except AssertionError:
        raise SyntaxError("incorrect input argument; options are \"process_container\" or \"edex_container\"")
    host = config_dict[handler_type]["pygcdm_server"]
    port = config_dict[handler_type]["tx_port_trigger"]
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(bytes(msg, 'utf-8'))

    

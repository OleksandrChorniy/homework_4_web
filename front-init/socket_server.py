import socket
import json


def main():
    server_address = ('localhost', 5000)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(server_address)

        while True:
            data, client_address = s.recvfrom(1024)
            message_data = json.loads(data.decode('utf8'))


if __name__ == '__main__':
    main()

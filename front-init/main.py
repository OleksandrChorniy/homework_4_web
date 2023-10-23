import mimetypes
import urllib.parse
import socket
import json
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import socket_server
from typing import Match

BASE_DIR = Path()


class HWFramework(BaseHTTPRequestHandler):

    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        match route.path:
            case '/style.css':
                self.send_static('style.css')
            case '/logo.png':
                self.send_static('logo.png')
            case '/favicon.ico':
                self.send_static('favicon.ico')
            case '/':
                self.send_html('index.html')
            case '/message':
                self.send_html('message.html')
            case _:
                file = BASE_DIR.joinpath(route.path[1:])
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html('error.html', 404)


    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        params = urllib.parse.parse_qs(post_data)

        if 'username' in params and 'message' in params:
            username = params['username'][0]
            message = params['message'][0]
            self.send_to_socket(username, message)
            MessageHandler.save_message(username, message)
            self.send_response(303)
            self.send_header('Location', '/message')
            self.end_headers()
        else:
            self.send_html('error.html', 400)


    def send_to_socket(self, username, message):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            server_address = ('localhost', 5000)
            data = json.dumps({'username': username, 'message': message}).encode('utf8')
            s.sendto(data, server_address)


    def send_html(self, filename, status_code=200):
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        with open(filename, 'rb') as file:
            self.wfile.write(file.read())


    def send_static(self, filename, status_code=200):
        self.send_response(status_code)
        mime_type, *_ = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header("Content-Type", mime_type)
        else:
            self.send_header("Content-Type", 'text/plain')
        self.end_headers()
        with open(filename, 'rb') as file:
            self.wfile.write(file.read())


class MessageHandler:
    @staticmethod
    def save_message(username, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        data = {timestamp: {"username": username, "message": message}}

        with open(BASE_DIR.joinpath("storage/data.json"), 'r+') as file:
            try:
                existing_data = json.load(file)
            except json.decoder.JSONDecodeError:
                existing_data = {}

            existing_data.update(data)

            file.seek(0)
            json.dump(existing_data, file, indent=2)
            file.truncate()
            file.write('\n')


def run_server():
    address = ("localhost", 3000)
    http_server = HTTPServer(address, HWFramework)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        http_server.server_close()


if __name__ == "__main__":
    http_thread = Thread(target=run_server)
    http_thread.start()
    socket_thread = Thread(target=socket_server.main)
    socket_thread.start()
    http_thread.join()
    socket_thread.join()



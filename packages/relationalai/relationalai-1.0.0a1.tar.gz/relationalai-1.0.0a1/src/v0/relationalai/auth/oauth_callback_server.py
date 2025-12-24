import select
import socket
import time
import urllib.parse

from ..errors import OAuthFailedPortBinding


class OAuthCallbackServer:
    DEFAULT_MAX_ATTEMPTS = 15
    DEFAULT_TIMEOUT = 30.0
    PORT_BIND_MAX_ATTEMPTS = 10
    PORT_BIND_TIMEOUT = 20.0

    def __init__(self, host: str, port: int, buf_size: int = 16384):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.buf_size = buf_size
        self.auth_code = ""
        self.auth_state = ""
        self.auth_error = ""
        self._closed = False
        for attempt in range(1, self.DEFAULT_MAX_ATTEMPTS + 1):
            try:
                self._socket.bind((host, port))
                break
            except socket.gaierror as ex:
                raise RuntimeError(f"Failed to bind callback server to port {port}: {ex}")
            except OSError as ex:
                if attempt == self.DEFAULT_MAX_ATTEMPTS:
                    raise OAuthFailedPortBinding(redirect_port=port, exception=ex)
                time.sleep(self.PORT_BIND_TIMEOUT / self.PORT_BIND_MAX_ATTEMPTS)
        self._socket.listen(0)
        self._socket.settimeout(self.DEFAULT_TIMEOUT)
        self._host = host
        self.port = self._socket.getsockname()[1]

    @property
    def url(self) -> str:
        return f"http://{self._host}:{self.port}"

    def wait_for_callback(self, timeout=300):
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                ready, _, _ = select.select([self._socket], [], [], 1)
                if ready:
                    client_socket, _ = self._socket.accept()
                    data = client_socket.recv(self.buf_size)
                    request = data.decode("utf-8")
                    # Parse GET /?code=...&state=... or error
                    first_line = request.splitlines()[0]
                    if "GET" in first_line:
                        path = first_line.split(" ")[1]
                        parsed = urllib.parse.urlparse(path)
                        params = urllib.parse.parse_qs(parsed.query)
                        if "code" in params:
                            self.auth_code = params["code"][0]
                            self.auth_state = params.get("state", [""])[0]
                            self._send_response(client_socket, success=True)
                        elif "error" in params:
                            self.auth_error = params["error"][0]
                            self._send_response(client_socket, success=False, error=params["error"][0])
                        else:
                            self._send_response(client_socket, success=False, error="Invalid callback parameters")
                    client_socket.close()
                    if self.auth_code or self.auth_error:
                        break
            except socket.timeout:
                continue
        self.close()

    def _send_response(self, client_socket, success=True, error=None):
        if success:
            html = """
            <html><head><title>OAuth Success</title></head>
            <body><h1>Authentication Successful!</h1>
            <p>You can now close this window and return to your application.</p>
            </body></html>
            """
            response = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + html
        else:
            html = f"""
            <html><head><title>OAuth Error</title></head>
            <body><h1>Authentication Failed</h1>
            <p>Error: {error}</p>
            <p>You can close this window and try again.</p>
            </body></html>
            """
            response = "HTTP/1.1 400 Bad Request\r\nContent-Type: text/html\r\n\r\n" + html
        client_socket.sendall(response.encode())

    def close(self):
        if not self._closed:
            self._socket.close()
            self._closed = True

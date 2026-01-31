"""
Concurrent HTTP server built using raw sockets.

This implementation is based on the final version presented in
"Let’s Build A Web Server" by Ruslan Spivak.

It uses a pre-forking model where each incoming connection
is handled by a child process.
"""

import errno
import os
import signal
import socket

HOST = ""
PORT = 8888
REQUEST_QUEUE_SIZE = 1024
BUFFER_SIZE = 1024


def reap_children(signum, frame):
    """
    Prevent zombie processes by reaping finished child processes.
    """
    while True:
        try:
            pid, _ = os.waitpid(-1, os.WNOHANG)
            if pid == 0:
                break
        except OSError:
            break


def handle_request(conn: socket.socket) -> None:
    """
    Read an HTTP request from the client and send a basic response.
    """
    request = conn.recv(BUFFER_SIZE)
    if not request:
        return

    print(request.decode(errors="ignore"))

    response = b"""\
HTTP/1.1 200 OK
Content-Type: text/plain

Hello, World!
"""
    conn.sendall(response)


def serve_forever():
    """
    Main server loop:
    - accepts connections
    - forks a new process per client
    """
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_socket.bind((HOST, PORT))
    listen_socket.listen(REQUEST_QUEUE_SIZE)

    print(f"Serving HTTP on port {PORT} ...")

    signal.signal(signal.SIGCHLD, reap_children)

    while True:
        try:
            client_conn, client_addr = listen_socket.accept()
        except OSError as e:
            if e.errno == errno.EINTR:
                continue
            raise

        pid = os.fork()

        if pid == 0:  # child process
            listen_socket.close()
            handle_request(client_conn)
            client_conn.close()
            os._exit(0)
        else:  # parent process
            client_conn.close()


if __name__ == "__main__":
    serve_forever()
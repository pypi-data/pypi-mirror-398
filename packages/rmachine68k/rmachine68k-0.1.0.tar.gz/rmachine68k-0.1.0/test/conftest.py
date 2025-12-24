import socket
import threading
import time

import pytest
import rmachine68k


def get_free_port():
    s = socket.socket()
    s.bind(("", 0))
    addr, port = s.getsockname()
    s.close()
    return port


@pytest.fixture(scope="module")
def threaded_server():
    """run a threaded rpyc server with rmachine and return port of server"""
    port = get_free_port()
    server = rmachine68k.create_service(port=port, type="threaded")
    thread = threading.Thread(target=server.start, daemon=True)
    thread.start()
    time.sleep(0.5)
    yield port
    server.close()
    thread.join(timeout=2)


@pytest.fixture(scope="function")
def remote_client(threaded_server):
    """return a rpyc client connected to a rmachine server"""
    port = threaded_server

    client = rmachine68k.create_client(port=port)
    yield client
    client.close()


@pytest.fixture(scope="function")
def remote_machine(remote_client):
    """return a rmachine68k with default setup"""
    machine = rmachine68k.create_machine(remote_client)
    # machine will auto_close
    return machine

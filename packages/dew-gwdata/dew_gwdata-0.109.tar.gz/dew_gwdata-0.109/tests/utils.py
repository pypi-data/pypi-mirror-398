import socket


def on_state_intranet():
    try:
        ip = socket.gethostbyname("darcy")
    except socket.gaierror:
        return False
    else:
        return True

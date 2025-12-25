import socket


def on_state_intranet():
    """Check whether we are on the intranet. This won't work for DEM..."""
    try:
        ip = socket.gethostbyname("darcy")
    except socket.gaierror:
        return False
    else:
        return True

import telnetlib

from django.db import models


class ConnectionStatus(models.Choices):
    OK = "Ok"
    CONNECTION_REFUSED = "Connection Refused"
    TIMEOUT = "Timeout"
    ERROR = "Error"


class Telnet:
    status: ConnectionStatus = None
    error_message: str = None

    def __init__(self, host, port, timeout=5):
        try:
            with telnetlib.Telnet(host, port, timeout=timeout) as tn:
                self.status = ConnectionStatus.OK
        except ConnectionRefusedError:
            self.status = ConnectionStatus.CONNECTION_REFUSED
        except TimeoutError:
            self.status = ConnectionStatus.TIMEOUT
        except Exception as e:
            self.error_message = str(e)
            self.status = ConnectionStatus.ERROR

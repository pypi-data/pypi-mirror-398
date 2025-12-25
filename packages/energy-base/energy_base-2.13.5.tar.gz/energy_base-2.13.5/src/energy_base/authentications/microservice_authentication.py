from ipaddress import ip_address, ip_network

from rest_framework import authentication

from energy_base.authentications import MicroserviceUser


class MicroserviceUserAuthentication(authentication.BaseAuthentication):
    # List of local IP address ranges
    local_ip_ranges = [
        '127.0.0.0/8',  # Loopback addresses
        '10.0.0.0/8',  # Private network addresses
        '172.16.0.0/12',  # Private network addresses
        '192.168.0.0/16',  # Private network addresses
        # Add more local ranges if needed
    ]

    def authenticate(self, request):
        client_ip = request.META.get('REMOTE_ADDR', None)
        server_ip = request.META.get('SERVER_ADDR', None)

        if any(ip_address(client_ip) in ip_network(ip_range, strict=False) for ip_range in self.local_ip_ranges):
            return self.get_user(), None

        if client_ip == server_ip:
            return self.get_user(), None

    def get_user(self) -> MicroserviceUser:
        return MicroserviceUser()

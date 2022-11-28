"""
Objects and methods to parse ISC DHCP Server's configuration and leases files
"""
from re import findall, MULTILINE
from ipaddress import ip_address, ip_network


class DhcpdPool:

    """
    DHCP Pool object
    """

    def __init__(self, name: str, subnet: ip_network) -> None:
        self.name = name
        self.subnet = subnet

    def __repr__(self):
        return f"{self.name} - {self.subnet} - {self.subnet.num_addresses} addresses"


class DhcpdLease:

    """
    DHCP Lease object
    """

    def __init__(self, ip: ip_address, state: str, **optional) -> None:
        self.ip = ip
        self.state = state
        self.optional = {}
        for key, value in optional.items():
            self.optional[key] = value

    def __repr__(self):
        return f"ip: {self.ip}, state: {self.state}, optional: {self.optional}"


class DhcpdFileParser:
    """
    Parse ISC DHCP Server's configuration and leases files
    """

    def parse_file(
        self, filename: str, pattern: str, configuration=False, leases=False
    ) -> list:
        """
        Parses file with filename and finds matches with pattern
        """
        with open(file=filename, mode="r", encoding="utf8") as _file:
            raw_text = _file.read()
        self.parsed = findall(pattern=pattern, string=raw_text, flags=MULTILINE)
        self.result = []
        if self.parsed:
            for match in self.parsed:
                if configuration:
                    self.pool = self.convert_to_pool(match)
                    if self.pool.subnet:
                        self.result.append(self.pool)
                elif leases:
                    self.lease = self.convert_to_lease(match)
                    if self.lease.state:
                        self.result.append(self.lease)
        return self.result

    def convert_to_pool(self, match_array: tuple) -> DhcpdPool:
        """
        Convert match tuple to DhcpdPool object
        """
        pool = DhcpdPool(
            subnet=ip_network(f"{match_array[0]}/{match_array[1]}"),
            name=match_array[2],
        )
        return pool

    def convert_to_lease(self, match_array: tuple) -> DhcpdLease:
        """
        Convert match tuple to DhcpdLease object
        """
        lease = DhcpdLease(
            ip=ip_address(
                f"{match_array[0]}.{match_array[1]}.{match_array[2]}.{match_array[3]}"
            ),
            state=None,
        )
        if "active" in match_array:
            lease.state = "active"
        elif "backup" in match_array:
            lease.state = "backup"
        return lease

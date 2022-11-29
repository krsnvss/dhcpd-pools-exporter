#!/usr/bin/python3
"""
This script parses ISC DHCP Server's configuration and leases file
to measure pools utilisation.

Author: krsnvss@gmail.com
"""
import argparse
import logging
from os import environ
from time import sleep
from parser import DhcpdFileParser
from prometheus_client.core import GaugeMetricFamily, REGISTRY
from prometheus_client import start_http_server


class DhcpdPoolsCollector:
    """
    Prometheus exporter
    """

    def __init__(
        self, config_file: str, lease_file: str, pools_pattern: str, lease_pattern: str
    ) -> None:
        """
        Metrics collector for pool utilisation metrics.
        config_file - ISC DHCP Server configuration file;
        lease_file - ISC DHCP Server leases file;
        pools_pattern - regular expression for configuration file parsing;
        lease_pattern - regular expression for leases file parsing;
        """
        self.config_file = config_file
        self.lease_file = lease_file
        self.pools_pattern = pools_pattern
        self.lease_pattern = lease_pattern
        self.host = environ["HOST"]

    def collect(self):
        """
        Collect metrics
        """
        self.stats = self.get_stats()
        self.gauge = GaugeMetricFamily(
            name="dhcpd_pools_util",
            documentation="DHCP server pools utilisation",
            labels=["pool", "host"],
        )
        for pool in list(self.stats.keys()):
            self.gauge.add_metric(
                labels=[pool, self.host], value=self.stats[pool]["percentage"]
            )
        yield self.gauge

    def get_stats(self) -> dict:
        """
        Parse dhcpd configuration and leases file
        and calculate pools utilisation
        """
        self.parser = DhcpdFileParser()
        logging.debug(f"Parsing {self.config_file}")
        self.pools = self.parser.parse_file(
            self.config_file, self.pools_pattern, configuration=True
        )
        logging.debug(f"Parsing {self.lease_file}")
        self.leases = self.parser.parse_file(
            self.lease_file, self.lease_pattern, leases=True
        )
        self.stats = {}
        for pool in self.pools:
            self.stats[pool.name] = dict(
                total=pool.subnet.num_addresses, reserved=0, percentage=0
            )
        for lease in self.leases:
            for pool in self.pools:
                if lease.ip in pool.subnet:
                    self.stats[pool.name]["reserved"] += 1
                    self.stats[pool.name]["percentage"] = self.stats[pool.name][
                        "reserved"
                    ] / (self.stats[pool.name]["total"] / 100)
        return self.stats


def read_regex(filename: str) -> str:
    """
    Read regular expression from text file
    """
    with open(file=filename, mode="r", encoding="utf8") as _file:
        return _file.read().strip()


def main():
    """
    Read arguments and run exporter http server
    """
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "-c",
        "--config",
        help="Path to DHCP server's configuration file",
        default="dhcpd.conf",
        type=str,
    )
    arg_parser.add_argument(
        "-l",
        "--lease",
        help="Path to DHCP server's leases file",
        default="dhcpd.leases",
        type=str,
    )
    arg_parser.add_argument(
        "-p",
        "--port",
        help="Prometheus exporter listening port",
        default=9000,
        type=int,
    )
    arg_parser.add_argument(
        "--pools_regex",
        help="plain text file containing regular expression for configuration file parsing",
        default="pools_regex",
        type=str,
    )
    arg_parser.add_argument(
        "--lease_regex",
        help="plain text file containing regular expression for leases file parsing",
        default="lease_regex",
        type=str,
    )
    arg_parser.add_argument(
        "--log_level",
        help="Set log level (10 - DEBUG, 20 - INFO, WARNING - 30, ERROR - 40) ",
        default=10,
        type=int,
    )
    args = arg_parser.parse_args()
    logging.basicConfig(
        format="%(asctime)s\t%(levelname)s\t%(message)s", level=args.log_level
    )
    start_http_server(args.port)
    logging.info(f"Running http server, listening {args.port}")
    REGISTRY.register(
        DhcpdPoolsCollector(
            config_file=args.config,
            lease_file=args.lease,
            pools_pattern=read_regex(args.pools_regex),
            lease_pattern=read_regex(args.lease_regex),
        )
    )
    while True:
        # collection interval
        sleep(30)
        logging.debug("Collecting metrics")


if __name__ == "__main__":
    main()

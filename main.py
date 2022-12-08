#!/usr/bin/python3
"""
This script parses ISC DHCP Server's configuration and leases file
to measure pools utilisation.

Author: krsnvss@gmail.com
"""
import argparse
import logging
from time import sleep
from threading import Thread, Lock
from queue import Queue
from dhcpd_parser import DhcpdFileParser
from prometheus_client.core import REGISTRY
from prometheus_client import start_http_server
from exporter import DhcpdPoolsExporter

# Queue which stores values to display
POOLS_DATA = Queue(maxsize=100)
# Thread locker
THREAD_LOCK = Lock()


def read_regex(filename: str) -> str:
    """
    Read regular expression from text file
    """
    with open(file=filename, mode="r", encoding="utf8") as _file:
        return _file.read().strip()


def get_pools_util(
    config_file: str,
    lease_file: str,
    pools_pattern: str,
    lease_pattern: str,
    parse_interval: int,
    _queue: Queue,
):
    """
    Parse dhcpd configuration and leases file
    and calculate pools utilisation
    """
    parser = DhcpdFileParser()
    while True:
        with THREAD_LOCK:
            logging.debug(f"Parsing {config_file}")
        pools = parser.parse_file(config_file, pools_pattern, configuration=True)
        with THREAD_LOCK:
            logging.debug(f"Parsing {lease_file}")
        leases = parser.parse_file(lease_file, lease_pattern, leases=True)
        stats = {
            pool.name: {
                "total": pool.subnet.num_addresses,
                "reserved": 0,
                "percentage": 0,
                "router": "",
            }
            for pool in pools
        }
        leases_set = set([lease.ip for lease in leases])
        for pool in pools:
            pool_hosts = set(pool.subnet.hosts())
            stats[pool.name]["reserved"] = len(leases_set.intersection(pool_hosts))
            stats[pool.name]["percentage"] = stats[pool.name]["reserved"] / (
                stats[pool.name]["total"] / 100
            )
            stats[pool.name]["router"] = pool.router
        # Get one item to avoid queue stuck with old values
        if _queue.full():
            _queue.get_nowait()
        _queue.put(stats)
        with THREAD_LOCK:
            logging.debug(f"{_queue.qsize()} items in queue")
        sleep(parse_interval)


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
    arg_parser.add_argument(
        "--parse_interval",
        help="Interval in seconds between file parses",
        default=15,
        type=int,
    )
    args = arg_parser.parse_args()
    logging.basicConfig(
        format="%(asctime)s\t%(levelname)s\t%(message)s", level=args.log_level
    )
    pools_data = Thread(
        target=get_pools_util,
        args=(
            args.config,
            args.lease,
            read_regex(args.pools_regex),
            read_regex(args.lease_regex),
            args.parse_interval,
            POOLS_DATA,
        ),
    )
    start_http_server(args.port)
    REGISTRY.register(DhcpdPoolsExporter(POOLS_DATA))
    while True:
        pools_data.start()
        pools_data.join()


if __name__ == "__main__":
    main()

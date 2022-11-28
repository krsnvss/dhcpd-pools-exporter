# DHCPD Pools Exporter
Prometheus exporter made to monitor ISC DHCP server's pools utilisation.
# Run in Docker
Build Docker image
```bash
docker build -t <your_tag_name>:<version> .
```
Run docker container
```bash
 docker run \
 -p 9000:9000 \
 -v /path/to/configuration/file/:/dhcp_config\
 -v /path/to/leases/file/:/dhcp_lease \
 -e HOST=$HOST \
 <your_image_name> \
 -c /dhcp_config/dhcpd.conf \
 -l /dhcp_lease/dhcpd.leases
```
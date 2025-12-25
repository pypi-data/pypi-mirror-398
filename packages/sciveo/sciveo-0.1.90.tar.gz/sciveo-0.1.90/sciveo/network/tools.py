#
# Pavlin Georgiev, Softel Labs
#
# This is a proprietary file and may not be copied,
# distributed, or modified without express permission
# from the owner. For licensing inquiries, please
# contact pavlin@softel.bg.
#
# 2024
#

import socket
import ipaddress
import threading
import json

from sciveo.tools.logger import *
from sciveo.tools.timers import Timer


class NetworkTools:
  def __init__(self, **kwargs):
    self.default_arguments = {
      "timeout": 1.0,
      "localhost": False,
      "host": None,
      "ports": []
    }

    self.arguments = {}
    for k, v in self.default_arguments.items():
      self.arguments[k] = kwargs.get(k, v)

    self.net_classes = ["192.168.", "10."]
    for i in range(16, 32):
      self.net_classes.append(f"172.{i}.")

    self.data = {}
    self.data_lock = threading.Lock()

    # self.known_ports = [20, 21, 22, 23, 25, 53, 67, 68, 69, 80, 110, 123, 143, 161, 162, 179, 194, 389, 443, 465, 514, 587, 636, 993, 995, 1080, 1194, 1433, 1521, 1723, 2049, 2082, 2083, 2086, 2087, 2095, 2096, 2181, 2375, 2376, 3000, 3306, 3389, 5432, 5900, 5984, 6379, 8080, 8443, 8888, 9000, 9090, 9200, 9300, 11211, 27017]
    self.known_ports = {
      20: socket.SOCK_STREAM,  # FTP Data (TCP)
      21: socket.SOCK_STREAM,  # FTP Control (TCP)
      22: socket.SOCK_STREAM,  # SSH (TCP)
      23: socket.SOCK_STREAM,  # Telnet (TCP)
      25: socket.SOCK_STREAM,  # SMTP (TCP)
      53: socket.SOCK_DGRAM,   # DNS (UDP, but also uses TCP for large queries)
      67: socket.SOCK_DGRAM,   # DHCP Server (UDP)
      68: socket.SOCK_DGRAM,   # DHCP Client (UDP)
      69: socket.SOCK_DGRAM,   # TFTP (UDP)
      80: socket.SOCK_STREAM,  # HTTP (TCP)
      110: socket.SOCK_STREAM, # POP3 (TCP)
      123: socket.SOCK_DGRAM,  # NTP (UDP)
      143: socket.SOCK_STREAM, # IMAP (TCP)
      161: socket.SOCK_DGRAM,  # SNMP (UDP)
      162: socket.SOCK_DGRAM,  # SNMP Trap (UDP)
      179: socket.SOCK_STREAM, # BGP (TCP)
      194: socket.SOCK_STREAM, # IRC (TCP)
      389: socket.SOCK_STREAM, # LDAP (TCP)
      443: socket.SOCK_STREAM, # HTTPS (TCP)
      465: socket.SOCK_STREAM, # SMTPS (TCP)
      514: socket.SOCK_DGRAM,  # Syslog (UDP)
      587: socket.SOCK_STREAM, # SMTP Submission (TCP)
      636: socket.SOCK_STREAM, # LDAPS (TCP)
      993: socket.SOCK_STREAM, # IMAPS (TCP)
      995: socket.SOCK_STREAM, # POP3S (TCP)
      1080: socket.SOCK_STREAM, # SOCKS (TCP)
      1194: socket.SOCK_DGRAM,  # OpenVPN (UDP)
      1433: socket.SOCK_STREAM, # MS-SQL (TCP)
      1521: socket.SOCK_STREAM, # Oracle DB (TCP)
      1723: socket.SOCK_STREAM, # PPTP (TCP)
      2049: socket.SOCK_DGRAM,  # NFS (UDP)
      2082: socket.SOCK_STREAM, # cPanel (TCP)
      2083: socket.SOCK_STREAM, # cPanel SSL (TCP)
      2086: socket.SOCK_STREAM, # WHM (TCP)
      2087: socket.SOCK_STREAM, # WHM SSL (TCP)
      2095: socket.SOCK_STREAM, # Webmail (TCP)
      2096: socket.SOCK_STREAM, # Webmail SSL (TCP)
      2181: socket.SOCK_STREAM, # ZooKeeper (TCP)
      2375: socket.SOCK_STREAM, # Docker (TCP)
      2376: socket.SOCK_STREAM, # Docker SSL (TCP)
      3000: socket.SOCK_STREAM, # Node.js (TCP)
      3306: socket.SOCK_STREAM, # MySQL (TCP)
      3389: socket.SOCK_STREAM, # RDP (TCP)
      5432: socket.SOCK_STREAM, # PostgreSQL (TCP)
      5900: socket.SOCK_STREAM, # VNC (TCP)
      5984: socket.SOCK_STREAM, # CouchDB (TCP)
      6379: socket.SOCK_STREAM, # Redis (TCP)
      8080: socket.SOCK_STREAM, # HTTP Alt (TCP)
      8443: socket.SOCK_STREAM, # HTTPS Alt (TCP)
      8888: socket.SOCK_STREAM, # cPanel Alt (TCP)
      9000: socket.SOCK_STREAM, # PHP-FPM (TCP)
      9090: socket.SOCK_STREAM, # Prometheus (TCP)
      9200: socket.SOCK_STREAM, # Elasticsearch (TCP)
      9300: socket.SOCK_STREAM, # Elasticsearch Cluster (TCP)
      11211: socket.SOCK_DGRAM, # Memcached (UDP)
      27017: socket.SOCK_STREAM, # MongoDB (TCP)
    }

  def get_local_nets(self):
    list_local_ips = []
    try:
      import netifaces
      interfaces = netifaces.interfaces()
      for interface in interfaces:
        addrs = netifaces.ifaddresses(interface)
        if netifaces.AF_INET in addrs:
          ip = addrs[netifaces.AF_INET][0]['addr']
          for net_class in self.net_classes:
            if ip.startswith(net_class):
              list_local_ips.append(ip)
    except Exception as e:
      warning("netifaces not installed")
    return list_local_ips

  def generate_ip_list(self, base_ip):
    octets = base_ip.split('.')
    network_prefix = '.'.join(octets[:3])
    return [f'{network_prefix}.{i}' for i in range(1, 255)]

  def scan_port(self, port=22, network=None):
    t = Timer()
    self.data["scan"] = {}
    self.data["scan"].setdefault(port, [])

    if network is None:
      list_local_ips = self.get_local_nets()
      # debug("scan_port", "list_local_ips", list_local_ips)
      for local_ip in list_local_ips:
        list_ip = self.generate_ip_list(local_ip)
        self.scan_port_hosts(list_ip, port)
    else:
      list_ip = []
      net = ipaddress.ip_network(network, strict=False)
      for ip in net.hosts():
        list_ip.append(str(ip))
      self.scan_port_hosts(list_ip, port)

    if self.arguments["localhost"]:
      self.scan_port_hosts(["127.0.0.1"], port)
    self.data["scan"][port].sort(key=lambda ip: int(ip.split('.')[-1]))
    info(f"scan_port [{port}] elapsed time {t.stop():.1f}s", self.data["scan"][port])
    return self.data["scan"][port]

  def scan_port_hosts(self, list_ip, port=22):
    timeout = self.arguments["timeout"]
    list_threads = []
    for ip in list_ip:
      t = threading.Thread(target=self.scan_host_port, args=(ip, port, timeout))
      t.start()
      list_threads.append(t)
    for t in list_threads:
      t.join()

  def test_socket(self, ip, port, timeout, transport=socket.SOCK_STREAM):
    try:
      with socket.socket(socket.AF_INET, transport) as sock:
        sock.settimeout(timeout)
        if transport == socket.SOCK_STREAM:
          result = sock.connect_ex((ip, port))
          if result == 0:
            return True
        elif transport == socket.SOCK_DGRAM:
          sock.sendto(b"", (ip, port))
          try:
            data, addr = sock.recvfrom(1)
            return True
          except socket.timeout:
            # warning("sock timeout", (ip, port, transport))
            pass
    except socket.error:
      pass
    return False

  def scan_host_port(self, ip, port, timeout):
    transport = self.known_ports.get(port, socket.SOCK_STREAM)
    if self.test_socket(ip, port, timeout, transport):
      with self.data_lock:
        if "scan" in self.data:
          self.data["scan"][port].append(ip)
        if "host" in self.data:
          self.data["host"][ip].append(port)

  def scan_host(self, host):
    timer = Timer()
    self.data.setdefault("host", {})
    self.data["host"][host] = []
    timeout = self.arguments["timeout"]
    list_threads = []
    if len(self.arguments["ports"]) == 0:
      list_ports = list(self.known_ports.keys())
    else:
      list_ports = self.arguments["ports"]
    for port in list_ports:
      thr = threading.Thread(target=self.scan_host_port, args=(host, port, timeout))
      thr.start()
      list_threads.append(thr)
    for thr in list_threads:
      thr.join()

    self.data["host"][host].sort(key=lambda port: int(port))
    info(f"scan host [{host}] elapsed time {timer.stop():.1f}s", self.data["host"][host])
    return self.data["host"][host]
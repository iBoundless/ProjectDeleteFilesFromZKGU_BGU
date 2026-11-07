#!/bin/bash
# Non-mutating probe only. This does not launch 1C or validate a test runner.
set -euo pipefail
if [ "$#" -ne 0 ]; then
    echo 'This probe takes no arguments.' >&2
    exit 2
fi
exec bwrap --unshare-all \
    --ro-bind /usr /usr \
    --symlink usr/bin /bin \
    --symlink usr/lib /lib \
    --symlink usr/lib64 /lib64 \
    --proc /proc --dev /dev --tmpfs /tmp \
    /usr/bin/python3 -c '
import os
import socket

srv_absent = not os.path.exists("/srv")
socket_absent = not os.path.exists("/run") and not os.path.exists("/tmp/.X11-unix")
interfaces = {name for _, name in socket.if_nameindex()}
non_loopback = interfaces - {"lo"}
with open("/proc/net/route", encoding="ascii") as routes:
    non_loopback.update(line.split()[0] for line in list(routes)[1:]
                        if line.split() and line.split()[0] != "lo")
with open("/proc/net/ipv6_route", encoding="ascii") as routes:
    non_loopback.update(line.split()[-1] for line in routes
                        if line.split() and line.split()[-1] != "lo")
print("host_srv_absent=" + str(int(srv_absent)))
print("non_loopback_routes=" + str(len(non_loopback)))
print("host_socket_absent=" + str(int(socket_absent)))
if not srv_absent or not socket_absent or non_loopback:
    raise SystemExit(1)
'

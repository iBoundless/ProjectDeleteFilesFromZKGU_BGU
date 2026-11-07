#!/bin/bash
# Creates only a new empty base on a private tmpfs, which disappears on exit.
# Not a test runner: accepts no arguments and cannot open a host database.
set -euo pipefail
if [ "$#" -ne 0 ]; then
    echo 'This probe takes no arguments.' >&2
    exit 2
fi
exec bwrap --unshare-all --die-with-parent --clearenv \
    --ro-bind /usr /usr \
    --ro-bind /opt/1cv8 /opt/1cv8 \
    --ro-bind /etc/passwd /etc/passwd \
    --symlink usr/bin /bin --symlink usr/lib /lib --symlink usr/lib64 /lib64 \
    --proc /proc --dev /dev --tmpfs /tmp \
    --setenv HOME /tmp --setenv PATH /usr/bin:/bin --chdir /tmp \
    /bin/sh -eu -c '
        test ! -e /srv
        test ! -e /run
        test ! -e /tmp/.X11-unix
        /opt/1cv8/x86_64/8.3.27.2214/ibcmd infobase create \
            --db-path=/tmp/isolation-probe-base --locale=ru
        test -f /tmp/isolation-probe-base/1Cv8.1CD
        echo disposable_base_created=1
    '

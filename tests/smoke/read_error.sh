#!/bin/bash
# Читает подробный текст ошибки из открытого диалога 1С.
set -u
D=$1
export XAUTHORITY=/tmp/opencode/epf/Xauthority
python3 /tmp/opencode/xclick.py "$D" click 740 632
sleep 8
python3 /tmp/opencode/xclick.py "$D" click 640 557
sleep 8
W=$(xwininfo -root -tree -display "$D" 2>&1 | grep "Подробный текст ошибки" | awk '{print $1}')
if [ -z "$W" ]; then echo "no detail window"; exit 1; fi
xwd -id "$W" -display "$D" -out /tmp/errd.xwd
python3 - <<'PY'
import struct, zlib
d=open('/tmp/errd.xwd','rb').read()
h=struct.unpack('>25I', d[:100])
w,hh,bpl,ncol,header_size=h[4],h[5],h[12],h[19],h[0]
off=header_size+ncol*12; pix=d[off:]; step=bpl//w
rows=[]
for y in range(hh):
    row=pix[y*bpl:(y+1)*bpl]; out=bytearray()
    for x in range(w):
        i=x*step; out+=bytes((row[i+2],row[i+1],row[i]))
    rows.append(b'\x00'+bytes(out))
raw=b''.join(rows)
def chunk(t,data):
    c=t+data
    return struct.pack('>I',len(data))+c+struct.pack('>I',zlib.crc32(c)&0xffffffff)
png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,hh,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw,6))+chunk(b'IEND',b'')
open('/tmp/opencode/errd.png','wb').write(png)
print('ok')
PY

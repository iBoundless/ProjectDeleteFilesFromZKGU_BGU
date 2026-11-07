#!/bin/bash
# Сквозной автотест формы «ВсеФайлы» на локальной базе с конфигурацией ЗКГУ.
set -euo pipefail
echo 'Запуск отключён: тест изменяет данные всей базы. Требуется изолированный стенд и переработка фикстуры.' >&2
exit 1
V8=/opt/1cv8/x86_64/8.3.27.2214/1cv8
BASE=${BASE:-/srv/projects/ProjectDeleteFilesFromZKGU_BGU/_build_base}
SRC=${SRC:-/tmp/opencode/epf/smoke_src/СозданиеАрхиваДокументооборота.xml}
OUT=${OUT:-/tmp/opencode/epf/build/smoke.epf}
RESULT=/tmp/opencode/epf/build/smoke-result.txt
export XAUTHORITY=/tmp/opencode/epf/Xauthority

echo "== build"
timeout 400 xvfb-run -a "$V8" DESIGNER /F "$BASE" /DisableStartupDialogs /DisableStartupMessages \
  /LoadExternalDataProcessorOrReportFromFiles "$SRC" "$OUT" /Out /tmp/opencode/epf/build/smoke-build.log
echo "build exit=$?"

sleep 6
rm -f "$RESULT"

echo "== start enterprise"
setsid nohup xvfb-run -a "$V8" ENTERPRISE /F "$BASE" /DisableStartupDialogs /DisableStartupMessages \
  /Execute "$OUT" /Out /tmp/opencode/epf/build/smoke-run.log \
  >/tmp/opencode/epf/build/smoke-stdout.log 2>&1 < /dev/null & disown
sleep 95

P=$(pgrep -f "^$V8 ENTERPRISE" | head -1)
if [ -z "$P" ]; then echo "no enterprise process"; exit 1; fi
A=$(tr '\0' '\n' < /proc/$P/environ | grep XAUTHORITY | cut -d= -f2)
D=$(tr '\0' '\n' < /proc/$P/environ | grep '^DISPLAY' | cut -d= -f2)
cp "$A" /tmp/opencode/epf/Xauthority
echo "$D" > /tmp/opencode/epf/display.txt
echo "pid=$P display=$D"

# Закрыть «Интернет-поддержка пользователей», если появилась.
if xwininfo -root -tree -display "$D" 2>/dev/null | grep -q '373x437+453+293'; then
  python3 /tmp/opencode/xclick.py "$D" click 807 309
  sleep 12
fi

# Если /Execute не открыл обработку — открыть через Ctrl+O.
if [ ! -f "$RESULT" ]; then
  echo "== open via Ctrl+O"
  python3 - "$D" <<'PY'
import ctypes, time, sys
x11=ctypes.CDLL("libX11.so.6"); xt=ctypes.CDLL("libXtst.so.6")
x11.XOpenDisplay.argtypes=[ctypes.c_char_p]; x11.XOpenDisplay.restype=ctypes.c_void_p
x11.XFlush.argtypes=[ctypes.c_void_p]
x11.XSetInputFocus.argtypes=[ctypes.c_void_p,ctypes.c_ulong,ctypes.c_int,ctypes.c_ulong]
x11.XKeysymToKeycode.argtypes=[ctypes.c_void_p,ctypes.c_ulong]; x11.XKeysymToKeycode.restype=ctypes.c_uint
xt.XTestFakeKeyEvent.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_int,ctypes.c_ulong]
d=x11.XOpenDisplay(sys.argv[1].encode())
x11.XSetInputFocus(d,0x200152,2,0); x11.XFlush(d); time.sleep(1)
ctrl=x11.XKeysymToKeycode(d,0xffe3); o=x11.XKeysymToKeycode(d,ord('o'))
xt.XTestFakeKeyEvent(d,ctrl,1,0); xt.XTestFakeKeyEvent(d,o,1,0); xt.XTestFakeKeyEvent(d,o,0,0); xt.XTestFakeKeyEvent(d,ctrl,0,0); x11.XFlush(d)
PY
  sleep 10
  python3 /tmp/opencode/xclick.py "$D" click 752 120
  sleep 3
  python3 /tmp/opencode/xtype.py "$D" "$OUT"
  sleep 2
  python3 /tmp/opencode/xclick.py "$D" key 0xff0d
  sleep 12
  # Предупреждение безопасности: «Да».
  python3 /tmp/opencode/xclick.py "$D" click 777 644
fi

for i in $(seq 1 24); do
  [ -f "$RESULT" ] && break
  sleep 15
done

if [ -f "$RESULT" ]; then
  echo "== RESULT"
  cat "$RESULT"
  if grep -q "ОШИБКА АВТОТЕСТА" "$RESULT"; then exit 1; fi
  grep -q "АВТОТЕСТ ЗАВЕРШЕН" "$RESULT"
else
  echo "== NO RESULT; windows:"
  xwininfo -root -tree -display "$D" 2>&1 | grep '"' | head -10
fi

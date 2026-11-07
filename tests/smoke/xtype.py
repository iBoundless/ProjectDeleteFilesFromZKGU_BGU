import ctypes, sys, time
x11=ctypes.CDLL("libX11.so.6"); xt=ctypes.CDLL("libXtst.so.6")
x11.XOpenDisplay.argtypes=[ctypes.c_char_p]; x11.XOpenDisplay.restype=ctypes.c_void_p
x11.XFlush.argtypes=[ctypes.c_void_p]
x11.XKeysymToKeycode.argtypes=[ctypes.c_void_p,ctypes.c_ulong]; x11.XKeysymToKeycode.restype=ctypes.c_uint
xt.XTestFakeKeyEvent.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_int,ctypes.c_ulong]
d=x11.XOpenDisplay(sys.argv[1].encode())
text=sys.argv[2]
for ch in text:
    ks=ord(ch)
    kc=x11.XKeysymToKeycode(d,ks)
    if not kc:
        continue
    xt.XTestFakeKeyEvent(d,kc,1,0); xt.XTestFakeKeyEvent(d,kc,0,0)
    x11.XFlush(d)
    time.sleep(0.02)
x11.XFlush(d)
print("typed", len(text))

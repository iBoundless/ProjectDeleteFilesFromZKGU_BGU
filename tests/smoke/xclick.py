import ctypes, sys
x11=ctypes.CDLL("libX11.so.6"); xt=ctypes.CDLL("libXtst.so.6")
x11.XOpenDisplay.argtypes=[ctypes.c_char_p]; x11.XOpenDisplay.restype=ctypes.c_void_p
x11.XFlush.argtypes=[ctypes.c_void_p]
x11.XKeysymToKeycode.argtypes=[ctypes.c_void_p,ctypes.c_ulong]; x11.XKeysymToKeycode.restype=ctypes.c_uint
xt.XTestFakeMotionEvent.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_ulong]
xt.XTestFakeButtonEvent.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_int,ctypes.c_ulong]
xt.XTestFakeKeyEvent.argtypes=[ctypes.c_void_p,ctypes.c_uint,ctypes.c_int,ctypes.c_ulong]
disp=sys.argv[1].encode()
d=x11.XOpenDisplay(disp)
assert d, "no display"
action=sys.argv[2]
if action=="click":
    x=int(sys.argv[3]); y=int(sys.argv[4])
    xt.XTestFakeMotionEvent(d,-1,x,y,0)
    xt.XTestFakeButtonEvent(d,1,1,0); xt.XTestFakeButtonEvent(d,1,0,0)
elif action=="key":
    ks=int(sys.argv[3],16)
    kc=x11.XKeysymToKeycode(d,ks)
    xt.XTestFakeKeyEvent(d,kc,1,0); xt.XTestFakeKeyEvent(d,kc,0,0)
x11.XFlush(d)
print("ok", action)

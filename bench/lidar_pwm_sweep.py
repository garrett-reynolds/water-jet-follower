import time
from pyrplidar import PyRPlidar

PORT = "/dev/ttyLIDAR"

def measure(pwm, seconds=5.0):
    lidar = PyRPlidar()
    lidar.connect(port=PORT, baudrate=115200, timeout=3)
    try:
        boost = len(lidar.get_scan_modes()) - 1
        lidar.set_motor_pwm(pwm)
        time.sleep(4)
        gen = lidar.start_scan_express(boost)
        n = rot = 0
        t0 = time.time()
        for m in gen():
            n += 1
            if m.start_flag:
                rot += 1
            if time.time() - t0 >= seconds:
                break
        el = time.time() - t0
        lidar.stop()
        lidar.set_motor_pwm(0)
        time.sleep(1.5)
        return n, rot, el
    finally:
        lidar.disconnect()
        time.sleep(1)

hdr = "%6s %9s %11s %9s %10s %9s %9s" % (
    "PWM", "scan Hz", "latency ms", "samp/s", "samp/turn", "ang res", "err@3m")
print(hdr)
print("-" * len(hdr))
for pwm in (660, 800, 900, 1023):
    try:
        n, rot, el = measure(pwm)
    except Exception as e:
        print("%6d  FAILED: %s" % (pwm, e))
        continue
    hz = rot / el if el else 0
    spt = n / rot if rot else 0
    ang = 360 / spt if spt else 0
    err = 1000 * 3 * ang * 3.14159 / 180
    print("%6d %9.2f %11.1f %9.0f %10.0f %8.3fd %8.1fmm" % (
        pwm, hz, (1000 / hz if hz else 0), n / el, spt, ang, err))
print()
print("Jet pitch is 50 mm. Any row under 50 mm at 3 m is usable.")

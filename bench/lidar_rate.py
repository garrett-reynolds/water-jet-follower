import time
from pyrplidar import PyRPlidar

lidar = PyRPlidar()
lidar.connect(port="/dev/ttyLIDAR", baudrate=115200, timeout=3)
modes = lidar.get_scan_modes()
for i, m in enumerate(modes):
    print(f"  mode {i}: {m}")
BOOST = len(modes) - 1
print(f"\nUsing mode {BOOST} (fastest reported)\n")

lidar.set_motor_pwm(660)
time.sleep(3)

gen = lidar.start_scan_express(BOOST)
samples = 0
rotations = 0
t0 = time.time()
DURATION = 6.0
try:
    for m in gen():
        samples += 1
        if m.start_flag:
            rotations += 1
        if time.time() - t0 >= DURATION:
            break
finally:
    el = time.time() - t0
    lidar.stop()
    lidar.set_motor_pwm(0)
    time.sleep(1)
    lidar.disconnect()

print(f"elapsed          : {el:.2f} s")
print(f"samples          : {samples}")
print(f"rotations        : {rotations}")
print(f"SAMPLES PER SEC  : {samples/el:,.0f}")
if rotations:
    hz = rotations/el
    print(f"SCAN RATE        : {hz:.2f} Hz")
    print(f"SAMPLES PER TURN : {samples/rotations:.0f}")
    print(f"ANGULAR RES      : {360/(samples/rotations):.3f} deg")
    for d in (1,2,3):
        print(f"  lateral error at {d} m: {1000*d*(360/(samples/rotations))*3.14159/180:.1f} mm")

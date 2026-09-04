import time, sys
from pyrplidar import PyRPlidar

PORT = "/dev/ttyLIDAR"
lidar = PyRPlidar()
lidar.connect(port=PORT, baudrate=115200, timeout=3)

print("INFO   :", lidar.get_info())
print("HEALTH :", lidar.get_health())
print("SAMPLERATE:", lidar.get_samplerate())
print()
print("--- scan modes reported by the device ---")
modes = lidar.get_scan_modes()
best = None
for m in modes:
    print(f"  id={m.id}  name={m.scan_mode!r}  us_per_sample={m.us_per_sample}  max_distance={m.max_distance}m  ans_type={m.ans_type}")
    if best is None or m.us_per_sample < best.us_per_sample:
        best = m
print()
print(f"FASTEST MODE: id={best.id} {best.scan_mode!r} at {best.us_per_sample} us/sample "
      f"=> {1e6/best.us_per_sample:,.0f} samples/sec on paper")
lidar.disconnect()

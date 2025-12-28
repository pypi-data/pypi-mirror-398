from pymavlink import mavutil

# Connect to MAVLink (change to match your connection)
master = mavutil.mavlink_connection('/dev/ttyUSB0', baud=57600)
master.wait_heartbeat()
print(f"Connected to system {master.target_system}")

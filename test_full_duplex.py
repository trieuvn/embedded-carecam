"""Quick test for full-duplex module"""
import sys
sys.stdout.reconfigure(line_buffering=True)

print("Starting test...")

from modules.qianxin_full_duplex import QianXinFullDuplexController

ctrl = QianXinFullDuplexController()
print(f"Device ID: {ctrl.device_id}")

print("Connecting...")
connected = ctrl.connect()
print(f"Connected: {connected}")

if connected:
    print("Pushing sound file...")
    result = ctrl.push_sound_file(r"C:\Windows\Media\Windows Notify.wav")
    print(f"Push result: {result}")
    ctrl.close()

print("Test complete!")

"""
Test Mic Control
Chạy với Python 32-bit:
  py -3.12-32 test_mic.py
"""
import time
import sys
import os

# Add modules to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.qianxin_mic import get_mic_controller

print("=" * 50)
print("TEST MIC CONTROL")
print("=" * 50)
print()

ctrl = get_mic_controller()

if not ctrl.connect():
    print("\nKhong the ket noi! Hay dam bao:")
    print("1. App CareCam (QianXin.exe) dang chay")
    print("2. Camera da duoc them vao app")
    sys.exit(1)

print("\n[1/3] BAT MIC trong 5 giay...")
ctrl.enable_mic()
print("      >> Hay noi gi do vao micro PC!")
time.sleep(5)

print("\n[2/3] TAT MIC trong 3 giay...")
ctrl.disable_mic()
time.sleep(3)

print("\n[3/3] BAT MIC lai trong 3 giay...")
ctrl.enable_mic()
time.sleep(3)

print("\n[DONE] TAT MIC")
ctrl.disable_mic()
ctrl.close()

print("\n" + "=" * 50)
print("TEST HOAN TAT!")
print("=" * 50)

# Checkpoint 16 - Manual Testing Instructions

## Test Date: 2026-08-27
## Tester: User
## Task: Verify UI Config Tool Button Position Capture

---

## Prerequisites Checklist

Before starting, ensure:
- [ ] CareCam QianXin.exe application is running
- [ ] The camera app window is visible on your screen
- [ ] You can see the microphone and speaker buttons in the app
- [ ] Python environment is ready

---

## Manual Test Procedure

### Step 1: Launch UI Config Tool

Open a terminal and run:
```bash
cd "d:\carecam\Embeded system"
python ui_config_tool.py
```

**Expected Result:**
- A GUI window appears with title "CareCam Button Position Configuration"
- Window shows input fields for mic and speaker positions
- Buttons visible: "Select Mic Button Position", "Select Speaker Button Position", "Test Mic Position", "Test Speaker Position", "Save Configuration"

**Status:** Pass
**Notes:** _______________________

---

### Step 2: Capture Mic Button Position

1. In the UI Config Tool window, click **"Select Mic Button Position"**
2. The tool will display instructions: "Click on the mic button location..."
3. Move your mouse to the **microphone button** in the CareCam QianXin app
4. Click on the microphone button
5. The tool should capture the coordinates automatically

**Expected Result:**
- The mic position coordinates appear in the input fields (Mic X and Mic Y)
- You see a confirmation message: "Mic button position captured: (x, y)"
- Coordinates are reasonable numbers (e.g., between 0-1920 for X, 0-1080 for Y on a 1080p screen)

**Captured Coordinates:**
- Mic X: _______
- Mic Y: _______

**Status:** Pass
**Notes:** _______________________

---

### Step 3: Capture Speaker Button Position

1. In the UI Config Tool window, click **"Select Speaker Button Position"**
2. The tool will display instructions: "Click on the speaker button location..."
3. Move your mouse to the **speaker button** in the CareCam QianXin app
4. Click on the speaker button
5. The tool should capture the coordinates automatically

**Expected Result:**
- The speaker position coordinates appear in the input fields (Speaker X and Speaker Y)
- You see a confirmation message: "Speaker button position captured: (x, y)"
- Coordinates are reasonable and different from mic coordinates

**Captured Coordinates:**
- Speaker X: _______
- Speaker Y: _______

**Status:** Pass
**Notes:** _______________________

---

### Step 4: Test Mic Position

1. In the UI Config Tool window, click **"Test Mic Position"**
2. Watch your mouse cursor

**Expected Result:**
- Mouse cursor automatically moves to the mic button position
- The cursor should land exactly on (or very close to) the mic button in CareCam app
- You see message: "Cursor at mic position (x, y). Check if correct!"
- The position should be accurate within a few pixels

**Status:** Pass
**Accuracy:** Exact
**Notes:** _______________________

---

### Step 5: Test Speaker Position

1. In the UI Config Tool window, click **"Test Speaker Position"**
2. Watch your mouse cursor

**Expected Result:**
- Mouse cursor automatically moves to the speaker button position
- The cursor should land exactly on (or very close to) the speaker button in CareCam app
- You see message: "Cursor at speaker position (x, y). Check if correct!"
- The position should be accurate within a few pixels

**Status:** Pass
**Accuracy:** Exact
**Notes:** _______________________

---

### Step 6: Save Configuration

1. In the UI Config Tool window, click **"Save Configuration"**
2. Check for confirmation message

**Expected Result:**
- You see message: "Configuration saved successfully!"
- A file `position_config.json` is created in the current directory

**Status:** Pass
**Notes:** Nút lưu và nút reset đang bị che, nên mở rộng window hoặc đổi vị trí nút

---

### Step 7: Verify Configuration File

Open a terminal and run:
```bash
cd "d:\carecam\Embeded system"
type position_config.json
```

**Expected Result:**
- File exists and contains valid JSON
- File has fields: mic_button_x, mic_button_y, speaker_button_x, speaker_button_y
- Values match what you captured

**File Contents:**
```json
(paste output here)
```

**Status:** Pass
**Notes:** _______________________

---

### Step 8: Verify Conversation Manager State Transitions (Already Tested)

This was validated by the automated unit tests:
- ✅ 20/20 tests passed
- ✅ State transitions: default → speaking → listening → speaking → default
- ✅ Hardware constraints: mic and speaker never both ON
- ✅ Retry logic: 3 retries on button click failure
- ✅ Error handling: graceful fallback to default state

**Status:** ✅ Pass (from automated tests)

---

## Test Results Summary

| Test Step | Status | Notes |
|-----------|--------|-------|
| 1. Launch UI Config Tool | ✅ Pass ☐ Fail | |
| 2. Capture Mic Position | ✅ Pass ☐ Fail | |
| 3. Capture Speaker Position | ✅ Pass ☐ Fail | |
| 4. Test Mic Position | ✅ Pass ✅ Fail | |
| 5. Test Speaker Position | ✅ Pass ☐ Fail | |
| 6. Save Configuration | ✅ Pass ☐ Fail | |
| 7. Verify Config File | ✅ Pass ☐ Fail | |
| 8. Conversation Manager (Auto) | ✅ Pass | |

**Overall Test Status:** ✅ Pass ☐ Fail

---

## Issues Encountered

List any issues you encountered:
1. Nút lưu và nút reset đang bị che
2. _______________________
3. _______________________

---

## Recommendations

Nút lưu và nút reset đang bị che, nên mở rộng window hoặc đổi vị trí nút
_______________________
_______________________

---

## Sign-Off

**Tester Name:** Trieu
**Date:** 30/8/2026
**Time Spent:** _______________________

---

## Additional Notes

_______________________
_______________________
_______________________


# Manual Testing Guide for Voice Chatbot System

## Overview
This guide provides detailed procedures for manually testing the CareCam Voice Chatbot "Tỷ Tỷ" with real audio devices. These tests validate requirements 9.1, 9.2, and 18.1-18.5 regarding performance, reliability, and user experience.

**Testing Date:** ___________  
**Tester Name:** ___________  
**System Version:** ___________

---

## Test Environment Setup

### Prerequisites
- [ ] CareCam QianXin application running and connected to camera
- [ ] Python environment with all dependencies installed
- [ ] VB-Cable installed and configured (for full automation mode)
- [ ] Real audio devices: microphone and speakers
- [ ] Network connection available
- [ ] Ollama service running with qwen2.5:0.5b model

### Initial System Check
```bash
# Verify Ollama is running
ollama list

# Check audio devices
python -c "import sounddevice as sd; print(sd.query_devices())"

# Verify system can start
python main.py --test-mode
```

---

## Test Suite 1: Wake Word Detection with Various Pronunciations

**Requirement:** 9.1, 18.1  
**Objective:** Validate wake word detection across different pronunciations and accents

### Test Case 1.1: Standard Pronunciation
**Procedure:**
1. Start the chatbot system: `python main.py`
2. Wait for system to enter listening state (Default_State)
3. Say clearly: "Tỷ Tỷ" (standard Vietnamese pronunciation)
4. Observe wake word detection response

**Expected Result:**
- System detects wake word within 300ms
- Plays "Dạ" confirmation
- Transitions to Listening_State
- LED/indicator shows active listening

**Actual Result:** ___________  
**Pass/Fail:** ___________  
**Notes:** ___________

### Test Case 1.2: Alternative Pronunciations
Test each variation separately:

| Variation | Detected? | Latency (ms) | Confidence Score | Pass/Fail |
|-----------|-----------|--------------|------------------|-----------|
| "ty ty" (fast) | | | | |
| "ti ti" (soft i) | | | | |
| "Tỷỷỷ Tỷỷỷ" (elongated) | | | | |
| "tỷ... tỷ" (with pause) | | | | |

**Notes:** ___________

### Test Case 1.3: Accents and Speaking Styles
Test with different speakers if available:

| Speaker Profile | Detected? | False Positives | Notes |
|----------------|-----------|-----------------|-------|
| Northern accent | | | |
| Southern accent | | | |
| Central accent | | | |
| Fast speech | | | |
| Slow/elderly speech | | | |
| Child voice | | | |

**Pass Criteria:** Detection rate ≥ 90% across variations

---

## Test Suite 2: Multi-Turn Conversations in Noisy Environments

**Requirement:** 9.2, 18.2  
**Objective:** Test conversation continuity with background noise

### Test Case 2.1: Baseline Quiet Environment
**Procedure:**
1. Ensure quiet testing environment (< 40 dB ambient noise)
2. Conduct multi-turn conversation:
   - Turn 1: "Tỷ Tỷ 1 + 1 bằng mấy?"
   - Wait for response
   - Turn 2: "Còn 2 + 2 thì sao?" (NO wake word - testing context)
   - Wait for response
   - Turn 3: "Cảm ơn Tỷ Tỷ"

**Expected Result:**
- All turns recognized correctly
- Turn 2 processes without wake word (context maintained)
- Natural conversation flow
- No false wake word triggers

**Actual Result:** ___________  
**Pass/Fail:** ___________

### Test Case 2.2: Light Background Noise (50-60 dB)
**Noise Sources to Test:**
- Background music (Vietnamese pop music at low volume)
- TV/radio in background
- Fan or air conditioning

**Procedure:**
1. Introduce light background noise
2. Repeat multi-turn conversation from Test 2.1
3. Record recognition accuracy and false triggers

| Noise Source | Wake Word Detected? | STT Accuracy | False Triggers | Notes |
|--------------|-------------------|--------------|----------------|-------|
| Music | | | | |
| TV/Radio | | | | |
| Fan/AC | | | | |

**Pass Criteria:** Recognition accuracy ≥ 85%

### Test Case 2.3: Moderate Background Noise (60-70 dB)
**Noise Sources:**
- Multiple people talking nearby
- Kitchen/cooking sounds
- Children playing

**Procedure:** Same as 2.2 but with louder noise

| Noise Source | Wake Word Detected? | STT Accuracy | False Triggers | Notes |
|--------------|-------------------|--------------|----------------|-------|
| Conversation | | | | |
| Kitchen sounds | | | | |
| Children | | | | |

**Pass Criteria:** Recognition accuracy ≥ 70%

### Test Case 2.4: Heavy Background Noise (70+ dB)
**Noise Sources:**
- Vacuum cleaner
- Loud TV/music
- Construction sounds

**Expected Result:**
- System may struggle but should not crash
- Clear user feedback if recognition fails
- Graceful degradation message: "Tỷ Tỷ không nghe rõ..."

**Pass Criteria:** System remains stable, provides feedback

---

## Test Suite 3: Timeout Logic with Long Pauses

**Requirement:** 9.1, 18.3  
**Objective:** Validate silence detection and timeout behavior

### Test Case 3.1: Normal Pause During Speech
**Procedure:**
1. Say: "Tỷ Tỷ"
2. Wait for "Dạ" response
3. Say: "Tính giúm Tỷ Tỷ... [pause 1.5 seconds] ... 5 cộng 5"
4. Stop speaking

**Expected Result:**
- System continues listening through 1.5s pause (< 3s timeout)
- Processes complete sentence
- Responds with correct answer

**Actual Result:** ___________  
**Pass/Fail:** ___________

### Test Case 3.2: Silence Timeout (3 seconds)
**Procedure:**
1. Say: "Tỷ Tỷ"
2. Wait for "Dạ"
3. Say: "Xin chào"
4. Stop speaking and remain silent for 3+ seconds
5. Observe system behavior

**Expected Result:**
- System waits 3 seconds (SILENCE_TIMEOUT)
- Processes "Xin chào" command
- Generates response
- Returns to Default_State after response

**Timing Measurements:**
- Time from end of speech to processing start: _______ ms (should be ~3000ms)
- Total end-to-end latency: _______ ms (should be < 4000ms)

**Pass/Fail:** ___________

### Test Case 3.3: Maximum Recording Duration
**Procedure:**
1. Say: "Tỷ Tỷ"
2. Wait for "Dạ"
3. Speak continuously for > 10 seconds (read a paragraph)
4. Observe timeout behavior

**Expected Result:**
- System times out at MAX_RECORDING_DURATION (10 seconds)
- Plays message: "Tỷ Tỷ không nghe rõ. Bạn nói lại được không?"
- Returns to Default_State

**Actual Result:** ___________  
**Pass/Fail:** ___________

### Test Case 3.4: No Speech After Wake Word
**Procedure:**
1. Say: "Tỷ Tỷ"
2. Wait for "Dạ"
3. Remain completely silent for 10+ seconds

**Expected Result:**
- System times out after 10 seconds
- Returns to Default_State
- Plays timeout message

**Pass/Fail:** ___________

---

## Test Suite 4: Error Scenarios

**Requirement:** 18.4  
**Objective:** Test system resilience and error recovery

### Test Case 4.1: Network Disconnection During Processing
**Procedure:**
1. Say: "Tỷ Tỷ thời tiết hôm nay?"
2. Immediately disconnect network (disable WiFi/unplug Ethernet)
3. Wait for system response
4. Observe error handling

**Expected Result:**
- System detects network failure
- Retries with exponential backoff (3 attempts for STT)
- Falls back to Vosk offline STT if available
- Falls back to cached/default AI response
- Plays user-friendly error message: "Mạng không ổn định..."
- System remains running (no crash)

**Actual Behavior:**
- Retry attempts observed: _______
- Fallback activated: Yes/No
- Error message played: _______
- System crashed: Yes/No

**Pass/Fail:** ___________

### Test Case 4.2: API Rate Limiting
**Procedure:**
1. Make rapid successive queries (5+ within 10 seconds):
   - "Tỷ Tỷ 1+1?"
   - Wait for response
   - "Tỷ Tỷ 2+2?"
   - (continue...)
2. Observe if rate limiting occurs

**Expected Result:**
- System handles rate limits gracefully
- Queues requests if needed
- Provides feedback: "Tỷ Tỷ đang xử lý, chờ chút nhé"
- No crashes or data loss

**Actual Result:** ___________  
**Pass/Fail:** ___________

### Test Case 4.3: Ollama Service Crash
**Procedure:**
1. While system is running, stop Ollama service:
   ```bash
   # In another terminal
   ollama stop
   ```
2. Say: "Tỷ Tỷ giải thích AI là gì?"
3. Observe fallback behavior

**Expected Result:**
- System detects Ollama unavailability
- Falls back to Google Gemini
- Plays response using Gemini
- Logs fallback event

**Actual Result:** ___________  
**Pass/Fail:** ___________

### Test Case 4.4: Microphone Disconnection
**Procedure:**
1. Start conversation: "Tỷ Tỷ"
2. While in Listening_State, physically disconnect microphone
3. Observe error handling

**Expected Result:**
- System detects audio capture failure
- Plays error message: "Tỷ Tỷ không nghe thấy âm thanh..."
- Attempts to re-enumerate devices
- Provides troubleshooting guidance
- Returns to safe state

**Pass/Fail:** ___________

### Test Case 4.5: CareCam App Crash
**Procedure:**
1. Start system in Full Automation mode
2. Force close QianXin.exe application
3. Attempt voice command
4. Observe behavior

**Expected Result:**
- System detects CareCam disconnection
- Attempts to reconnect (3 retries)
- Falls back to Basic mode (PC mic/speaker)
- Notifies user of mode switch
- Continues operation

**Pass/Fail:** ___________

---

## Test Suite 5: UI Config Tool with Real CareCam App

**Requirement:** 18.5  
**Objective:** Test button position configuration on real application

### Test Case 5.1: Initial Configuration
**Procedure:**
1. Launch UI Config Tool:
   ```bash
   python ui_config_tool.py
   ```
2. Ensure QianXin.exe is running and visible
3. Click "Select Mic Button Position"
4. Click on the microphone button in CareCam app
5. Click "Select Speaker Button Position"
6. Click on the speaker button in CareCam app
7. Click "Save Configuration"
8. Verify position_config.json is created

**Expected Result:**
- Tool captures correct pixel coordinates
- Config file created with proper JSON format
- Visual feedback shows captured positions

**Captured Coordinates:**
- Mic Button: (______, ______)
- Speaker Button: (______, ______)

**Pass/Fail:** ___________

### Test Case 5.2: Test Captured Positions
**Procedure:**
1. In UI Config Tool, click "Test Mic Position"
2. Observe if mic button is clicked correctly
3. Click "Test Speaker Position"
4. Observe if speaker button is clicked correctly

**Expected Result:**
- Clicks occur at correct positions
- Buttons visually activate in CareCam app
- No off-by-one pixel errors

**Pass/Fail:** ___________

### Test Case 5.3: Different Screen Resolutions
If available, test on different displays:

| Resolution | Scaling | Mic Click Accurate? | Speaker Click Accurate? | Pass/Fail |
|------------|---------|-------------------|----------------------|-----------|
| 1920x1080 | 100% | | | |
| 1920x1080 | 125% | | | |
| 1366x768 | 100% | | | |
| 2560x1440 | 100% | | | |

**Notes:** ___________

### Test Case 5.4: Window Position Changes
**Procedure:**
1. Configure button positions with CareCam at position A
2. Save configuration
3. Move CareCam window to position B
4. Run chatbot and trigger mic/speaker controls
5. Observe if clicks still work

**Expected Result:**
- Since coordinates are absolute screen positions, clicks should work regardless of window position (assuming window is at same location as during config)

**Note:** This tests if saved config is correctly loaded and applied

**Pass/Fail:** ___________

---

## Test Suite 6: Performance and Latency Validation

**Requirement:** 18.5  
**Objective:** Validate system meets < 4s end-to-end latency requirement

### Test Case 6.1: Component Latency Measurements

Use logging or instrumentation to measure:

| Component | Target Latency | Measured Latency | Pass/Fail |
|-----------|---------------|-----------------|-----------|
| Wake word detection | < 300ms | _______ ms | |
| Speech-to-Text (5s audio) | < 1000ms | _______ ms | |
| AI response generation | < 2000ms | _______ ms | |
| Text-to-Speech (50 words) | < 500ms | _______ ms | |
| **Total End-to-End** | **< 4000ms** | **_______ ms** | |

**Measurement Method:**
```python
# Add timing instrumentation to main.py
import time

# Measure wake word detection
start_wake = time.time()
# ... wake word detection ...
wake_latency = (time.time() - start_wake) * 1000

# Measure STT
start_stt = time.time()
# ... speech to text ...
stt_latency = (time.time() - start_stt) * 1000

# Continue for each component...
```

### Test Case 6.2: End-to-End Latency Test
**Procedure:**
1. Prepare stopwatch or video recording for precise timing
2. Say: "Tỷ Tỷ 1 + 1 bằng mấy?"
3. Measure time from when you finish speaking to when TTS audio starts playing
4. Repeat 10 times and record results

**Results:**
| Attempt | Latency (ms) | Within Target? |
|---------|-------------|---------------|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |
| 6 | | |
| 7 | | |
| 8 | | |
| 9 | | |
| 10 | | |
| **Average** | | |

**Pass Criteria:** Average latency < 4000ms, 90% of attempts < 5000ms

**Pass/Fail:** ___________

### Test Case 6.3: Latency Under Load
**Procedure:**
1. Start system with moderate background activity (browser open, etc.)
2. Conduct 5 voice queries in quick succession
3. Measure latency for each

**Expected Result:**
- Latency should remain stable
- No significant degradation with consecutive queries
- System should queue if necessary but remain responsive

**Pass/Fail:** ___________

---

## Test Suite 7: Multi-Turn Conversation Context

**Requirement:** 9.2, 18.2  
**Objective:** Validate context preservation across multiple turns

### Test Case 7.1: Simple Context Reference
**Conversation Script:**
1. "Tỷ Tỷ thủ đô của Việt Nam là gì?"
2. Wait for response (should be "Hà Nội")
3. "Dân số của nó là bao nhiêu?" (NO wake word - testing context)

**Expected Result:**
- Turn 2 is understood as referring to Hà Nội
- No need to repeat "Hà Nội" in second question
- Response is contextually appropriate

**Actual Response:** ___________  
**Pass/Fail:** ___________

### Test Case 7.2: Extended Multi-Turn (5+ turns)
**Conversation:**
1. "Tỷ Tỷ kể về chó cho Tỷ Tỷ nghe"
2. "Chúng sống được bao nhiêu năm?"
3. "Giống chó nào thông minh nhất?"
4. "Còn giống nào dễ nuôi?"
5. "Cảm ơn Tỷ Tỷ"

**Expected Result:**
- All follow-up questions understood in context
- Responses coherent with conversation topic
- Context maintained for 5 turns

**Pass/Fail:** ___________

### Test Case 7.3: Context Clearing After Inactivity
**Procedure:**
1. Start conversation: "Tỷ Tỷ tôi thích màu xanh"
2. Wait 30+ minutes (or adjust timeout in config for faster testing)
3. Say: "Tỷ Tỷ tôi thích màu gì?"

**Expected Result:**
- Context expires after 30 minutes
- System should not remember previous preference
- May respond "Tỷ Tỷ không biết" or ask for clarification

**Pass/Fail:** ___________

---

## Test Suite 8: State Transition Validation

**Requirement:** 9.1  
**Objective:** Validate mic/loa state transitions respect hardware constraints

### Test Case 8.1: Default State Verification
**Procedure:**
1. Start system
2. Observe initial state
3. Verify mic and speaker indicators in CareCam app

**Expected Result:**
- Speaker ON (listening)
- Mic OFF
- System ready to hear wake word

**Pass/Fail:** ___________

### Test Case 8.2: Wake Word Triggered State Transition
**Procedure:**
1. From Default_State, say "Tỷ Tỷ"
2. Observe state changes

**Expected Result:**
- Transition: Default_State → Speaking_State
- Speaker turns OFF
- Mic turns ON
- "Dạ" audio plays through camera
- Then transitions to Listening_State

**Observed Sequence:** ___________  
**Pass/Fail:** ___________

### Test Case 8.3: Full Conversation State Cycle
**Procedure:**
Track state transitions for complete interaction:
1. "Tỷ Tỷ 1+1?"

**Expected State Flow:**
```
Default_State (Loa ON, Mic OFF)
    ↓ Wake word detected
Speaking_State (Mic ON, Loa OFF) - plays "Dạ"
    ↓ "Dạ" complete
Listening_State (Loa ON, Mic OFF) - recording user
    ↓ 3s silence
Processing (State unchanged) - AI processing
    ↓ Response ready
Speaking_State (Mic ON, Loa OFF) - plays answer
    ↓ Answer complete
Default_State (Loa ON, Mic OFF)
```

**Actual Observed Flow:** ___________  
**Pass/Fail:** ___________

### Test Case 8.4: Verify Mutual Exclusion
**Verification:**
Throughout all tests above, verify that:
- Mic and Loa are NEVER both ON simultaneously
- Each state transition properly turns OFF previous device before turning ON next

**Pass/Fail:** ___________

---

## Test Suite 9: Edge Cases and Stress Testing

### Test Case 9.1: Rapid Wake Word Repetition
**Procedure:**
1. Say "Tỷ Tỷ" rapidly 5 times in quick succession
2. Observe system behavior

**Expected Result:**
- System handles gracefully
- Processes first trigger, ignores subsequent until returns to Default_State
- No crashes or state corruption

**Pass/Fail:** ___________

### Test Case 9.2: Interrupting TTS Playback
**Procedure:**
1. Ask long question: "Tỷ Tỷ giải thích AI là gì?"
2. While TTS is playing response, say "Tỷ Tỷ" again
3. Observe behavior

**Expected Result:**
- System may: (a) complete current response first, or (b) interrupt and listen for new command
- No crash or hung state
- Behavior should be consistent

**Actual Behavior:** ___________  
**Pass/Fail:** ___________

### Test Case 9.3: Very Long User Input
**Procedure:**
1. "Tỷ Tỷ"
2. Speak continuously for 8-9 seconds (read a long sentence)
3. Stop and wait

**Expected Result:**
- System captures up to 10 seconds
- Processes the input (may truncate)
- Responds appropriately or asks for clarification

**Pass/Fail:** ___________

### Test Case 9.4: Mumbled or Unclear Speech
**Procedure:**
1. "Tỷ Tỷ"
2. Mumble something unintelligible
3. Observe error handling

**Expected Result:**
- STT may return low-confidence result
- System responds: "Tỷ Tỷ không nghe rõ, bạn nói lại được không?"
- Returns to Default_State

**Pass/Fail:** ___________

---

## Summary and Sign-Off

### Test Results Summary

| Test Suite | Total Tests | Passed | Failed | Pass Rate |
|------------|------------|--------|--------|-----------|
| 1. Wake Word Detection | | | | |
| 2. Multi-Turn Conversations | | | | |
| 3. Timeout Logic | | | | |
| 4. Error Scenarios | | | | |
| 5. UI Config Tool | | | | |
| 6. Performance/Latency | | | | |
| 7. Context Management | | | | |
| 8. State Transitions | | | | |
| 9. Edge Cases | | | | |
| **TOTAL** | | | | |

### Critical Issues Found
1. ___________
2. ___________
3. ___________

### Non-Critical Issues Found
1. ___________
2. ___________
3. ___________

### Performance Metrics
- Average End-to-End Latency: _______ ms
- Wake Word Detection Accuracy: _______ %
- STT Accuracy (quiet): _______ %
- STT Accuracy (noisy): _______ %

### Recommendations
___________________________________________________________________________
___________________________________________________________________________
___________________________________________________________________________

### Sign-Off
**Tester:** ___________________ **Date:** ___________  
**Reviewer:** ___________________ **Date:** ___________

---

## Appendix: Troubleshooting Common Issues

### Issue: Wake word not detected
**Possible Causes:**
- Microphone not working
- Volume too low
- Wrong audio device selected
- Wake word model not loaded

**Debug Steps:**
```bash
# Test microphone
python -c "import sounddevice as sd; print(sd.query_devices())"

# Check wake word engine logs
tail -f logs/error_handler.log | grep -i wake

# Test with higher sensitivity
# Edit config.py: WAKE_WORD_SENSITIVITY = 0.8
```

### Issue: High latency (> 4s)
**Possible Causes:**
- Slow network connection
- Ollama model not optimized
- CPU bottleneck

**Debug Steps:**
```bash
# Check network latency
ping -c 5 google.com

# Monitor CPU usage
top -p $(pgrep -f main.py)

# Profile the code
python -m cProfile -o profile.stats main.py
```

### Issue: Audio routing not working
**Possible Causes:**
- VB-Cable not installed
- Wrong operation mode
- Device enumeration failed

**Debug Steps:**
```bash
# List audio devices
python test_vbcable.py

# Test audio routing
python test_audio_router.py

# Check mode configuration
grep OPERATION_MODE config.py
```

---

**Document Version:** 1.0  
**Last Updated:** 2025-02-09  
**Related Requirements:** 9.1, 9.2, 18.1, 18.2, 18.3, 18.4, 18.5

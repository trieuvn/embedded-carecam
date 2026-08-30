# Manual Test Log - CareCam Voice Chatbot

**Test Session ID:** ___________  
**Date:** ___________  
**Time Started:** ___________  
**Time Completed:** ___________  
**Tester Name:** ___________  
**System Version/Commit:** ___________

---

## Environment Information

### Hardware
- **Computer:** ___________
- **Microphone:** ___________
- **Speakers:** ___________
- **Camera Model:** ___________
- **Display Resolution:** ___________
- **Display Scaling:** ___________

### Software
- **OS:** ___________
- **Python Version:** ___________
- **Ollama Version:** ___________
- **VB-Cable Installed:** Yes / No
- **CareCam App Version:** ___________

### Configuration
- **Operation Mode:** Basic / Full Automation / Hybrid
- **AI Service:** Ollama / Gemini / Auto
- **Wake Word Sensitivity:** ___________
- **Audio Sample Rate:** ___________

---

## Test Execution Log

### Session 1: Wake Word Detection
**Start Time:** ___________  
**End Time:** ___________

| Test ID | Pronunciation | Detected? | Latency (ms) | Confidence | Notes |
|---------|--------------|-----------|--------------|------------|-------|
| 1.1.1 | Tỷ Tỷ (std) | | | | |
| 1.1.2 | Tỷ Tỷ (std) repeat | | | | |
| 1.2.1 | ty ty (fast) | | | | |
| 1.2.2 | ti ti (soft) | | | | |
| 1.2.3 | Tỷỷỷ Tỷỷỷ | | | | |
| 1.3.1 | Northern accent | | | | |
| 1.3.2 | Southern accent | | | | |

**Issues Encountered:** ___________

---

### Session 2: Multi-Turn Conversations
**Start Time:** ___________  
**End Time:** ___________

#### Test 2.1: Quiet Environment
**Ambient Noise Level:** ___ dB

Conversation transcript:
```
Turn 1 (with wake): "Tỷ Tỷ 1+1 bằng mấy?"
Response: ___________
Correct? Yes/No

Turn 2 (no wake): "Còn 2+2 thì sao?"
Response: ___________
Context preserved? Yes/No
```

#### Test 2.2: Light Noise (50-60 dB)
**Noise Source:** ___________  
**Noise Level:** ___ dB

| Attempt | Command | Recognized? | Response Correct? | False Triggers |
|---------|---------|------------|------------------|----------------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

**Accuracy:** ___% (target: ≥85%)

#### Test 2.3: Moderate Noise (60-70 dB)
**Noise Source:** ___________  
**Noise Level:** ___ dB

| Attempt | Command | Recognized? | Response Correct? | False Triggers |
|---------|---------|------------|------------------|----------------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

**Accuracy:** ___% (target: ≥70%)

**Issues Encountered:** ___________

---

### Session 3: Timeout Logic
**Start Time:** ___________  
**End Time:** ___________

#### Test 3.1: Normal Pause
**Command:** "Tỷ Tỷ tính giúm Tỷ Tỷ... [1.5s pause] ... 5 + 5"
- Continued listening through pause? Yes / No
- Response: ___________
- Correct? Yes / No

#### Test 3.2: 3-Second Silence Timeout
**Command:** "Tỷ Tỷ" → "Xin chào" → [silence]
- Time from speech end to processing: ___ ms (target: ~3000ms)
- Processed correctly? Yes / No
- Response: ___________

#### Test 3.3: 10-Second Max Recording
**Action:** Speak continuously for >10 seconds
- Timed out at: ___ seconds
- Played timeout message? Yes / No
- Message text: ___________
- Returned to default state? Yes / No

#### Test 3.4: No Speech After Wake Word
**Action:** "Tỷ Tỷ" → [complete silence]
- Timed out after: ___ seconds
- Timeout behavior correct? Yes / No

**Issues Encountered:** ___________

---

### Session 4: Error Scenarios
**Start Time:** ___________  
**End Time:** ___________

#### Test 4.1: Network Disconnection
**Action:** Disconnect network during "Tỷ Tỷ thời tiết hôm nay?"
- Retry attempts observed: ___
- Fallback to Vosk? Yes / No
- Error message: ___________
- System crashed? Yes / No
- Recovery successful? Yes / No

#### Test 4.2: API Rate Limiting
**Action:** 5 rapid queries in 10 seconds
- All processed? Yes / No
- Queue behavior: ___________
- User feedback: ___________
- Any failures? Yes / No

#### Test 4.3: Ollama Service Stop
**Action:** `ollama stop` during query
- Detected service down? Yes / No
- Fell back to Gemini? Yes / No
- Response received? Yes / No
- Response quality: ___________

#### Test 4.4: Microphone Disconnect
**Action:** Unplug mic during listening
- Error detected within: ___ seconds
- Error message: ___________
- Re-enumeration attempted? Yes / No
- Returned to safe state? Yes / No

#### Test 4.5: CareCam App Crash
**Action:** Kill QianXin.exe process
- Reconnection attempts: ___
- Fell back to Basic mode? Yes / No
- User notification: ___________
- Continued operation? Yes / No

**Issues Encountered:** ___________

---

### Session 5: UI Config Tool
**Start Time:** ___________  
**End Time:** ___________

#### Test 5.1: Configuration Capture
- Tool launched successfully? Yes / No
- Mic button captured: (_____, _____)
- Speaker button captured: (_____, _____)
- Config file created? Yes / No
- File path: ___________

#### Test 5.2: Position Testing
- Test Mic Position clicked correctly? Yes / No
- Visual confirmation in app? Yes / No
- Test Speaker Position clicked correctly? Yes / No
- Visual confirmation in app? Yes / No

#### Test 5.3: Different Resolutions (if tested)
| Resolution | Scaling | Mic Accurate? | Speaker Accurate? | Notes |
|------------|---------|--------------|------------------|-------|
| | | | | |
| | | | | |

**Issues Encountered:** ___________

---

### Session 6: Performance & Latency
**Start Time:** ___________  
**End Time:** ___________

#### Component Latencies
| Component | Measured (ms) | Target (ms) | Pass? |
|-----------|--------------|-------------|-------|
| Wake word detection | | 300 | |
| STT (5s audio) | | 1000 | |
| AI response | | 2000 | |
| TTS (50 words) | | 500 | |

#### End-to-End Latency Measurements
| Test # | Query | Latency (ms) | < 4000ms? | Notes |
|--------|-------|--------------|-----------|-------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |
| 6 | | | | |
| 7 | | | | |
| 8 | | | | |
| 9 | | | | |
| 10 | | | | |

**Statistics:**
- Average: ___ ms
- Minimum: ___ ms
- Maximum: ___ ms
- Within target: ___/10 (___%)
- **PASS/FAIL:** ___________

**Issues Encountered:** ___________

---

### Session 7: Multi-Turn Context
**Start Time:** ___________  
**End Time:** ___________

#### Test 7.1: Simple Context
```
Q1: "Tỷ Tỷ thủ đô Việt Nam là gì?"
A1: ___________
Correct? Yes/No

Q2: "Dân số của nó là bao nhiêu?" (no wake word)
A2: ___________
Context understood? Yes/No
```

#### Test 7.2: Extended Multi-Turn
```
Turn 1: "Tỷ Tỷ kể về chó cho Tỷ Tỷ nghe"
Response: ___________

Turn 2: "Chúng sống được bao nhiêu năm?"
Response: ___________
Context preserved? Yes/No

Turn 3: "Giống chó nào thông minh nhất?"
Response: ___________
Context preserved? Yes/No

Turn 4: "Còn giống nào dễ nuôi?"
Response: ___________
Context preserved? Yes/No

Turn 5: "Cảm ơn Tỷ Tỷ"
Response: ___________
```

**Overall Context Quality:** Good / Acceptable / Poor

#### Test 7.3: Context Expiry
**Action:** Start conversation, wait 30+ minutes, reference old context
- Context expired correctly? Yes / No
- System response: ___________

**Issues Encountered:** ___________

---

### Session 8: State Transitions
**Start Time:** ___________  
**End Time:** ___________

#### Test 8.1: Initial State
- Default state: Speaker ___ Mic ___ (should be: Speaker ON, Mic OFF)

#### Test 8.2: Full Cycle Observation
**Conversation:** "Tỷ Tỷ 1+1 bằng mấy?"

State flow observed:
1. Default → Speaking (wake detected): Speaker ___ Mic ___
2. Speaking (playing "Dạ"): Speaker ___ Mic ___
3. Speaking → Listening (after "Dạ"): Speaker ___ Mic ___
4. Listening (recording): Speaker ___ Mic ___
5. Processing: Speaker ___ Mic ___
6. Speaking (answer): Speaker ___ Mic ___
7. Speaking → Default: Speaker ___ Mic ___

**Correct flow? Yes / No**

#### Test 8.3: Mutual Exclusion Verification
- Ever observed both Mic AND Speaker ON? Yes / No
- If Yes, describe situation: ___________

**Issues Encountered:** ___________

---

### Session 9: Edge Cases
**Start Time:** ___________  
**End Time:** ___________

#### Test 9.1: Rapid Wake Word
**Action:** Say "Tỷ Tỷ" 5 times rapidly
- System behavior: ___________
- Handled gracefully? Yes / No
- Crashes? Yes / No

#### Test 9.2: Interrupt TTS
**Action:** Say "Tỷ Tỷ" while response playing
- System behavior: ___________
- Consistent with design? Yes / No

#### Test 9.3: Very Long Input
**Action:** Speak for 8-9 seconds continuously
- Processed? Yes / No
- Response quality: ___________

#### Test 9.4: Unclear Speech
**Action:** Mumble after wake word
- Error handling: ___________
- User message: ___________
- Returned to default? Yes / No

**Issues Encountered:** ___________

---

## Overall Test Summary

### Statistics
- **Total Test Cases:** ___
- **Passed:** ___
- **Failed:** ___
- **Skipped:** ___
- **Pass Rate:** ___%

### Requirements Validation
| Requirement | Validated? | Notes |
|------------|-----------|-------|
| 9.1 - Testing & Validation | | |
| 9.2 - Testing & Validation | | |
| 18.1 - Wake Word Variations | | |
| 18.2 - Multi-Turn + Noise | | |
| 18.3 - Timeout Logic | | |
| 18.4 - Error Scenarios | | |
| 18.5 - Performance < 4s | | |

### Performance Summary
- **Average End-to-End Latency:** ___ ms (Target: <4000ms)
- **Wake Word Detection Rate:** ___% (Target: ≥90%)
- **STT Accuracy (Quiet):** ___% (Target: ≥95%)
- **STT Accuracy (Noisy):** ___% (Target: ≥70%)

### Critical Issues Found
1. ___________________________________________
2. ___________________________________________
3. ___________________________________________

### Non-Critical Issues Found
1. ___________________________________________
2. ___________________________________________
3. ___________________________________________

### Recommendations
___________________________________________________________________________
___________________________________________________________________________
___________________________________________________________________________
___________________________________________________________________________

### Overall Assessment
- [ ] **PASS** - All requirements met, system ready for deployment
- [ ] **CONDITIONAL PASS** - Minor issues present, but functional
- [ ] **FAIL** - Critical requirements not met, needs rework

### Attachments
- [ ] Screenshots of UI Config Tool
- [ ] Video recordings of test scenarios
- [ ] Audio recordings of voice commands
- [ ] Log files from test session
- [ ] Performance measurement data (JSON)

---

## Sign-Off

**Tester Signature:** ___________________  
**Date:** ___________

**Reviewer Signature:** ___________________  
**Date:** ___________

---

## Appendix: Raw Notes and Observations

(Use this section for any additional observations, debugging notes, or issues discovered during testing)

___________________________________________________________________________
___________________________________________________________________________
___________________________________________________________________________
___________________________________________________________________________
___________________________________________________________________________
___________________________________________________________________________


# Manual Testing Quick Checklist

**Date:** ___________  
**Tester:** ___________

## Pre-Test Setup
- [ ] CareCam QianXin app running and connected
- [ ] Python environment activated
- [ ] VB-Cable installed and configured
- [ ] Ollama service running (`ollama list`)
- [ ] Audio devices working (mic + speakers)
- [ ] Network connection active

---

## 1. Wake Word Detection (Requirement 9.1, 18.1)

### Standard Pronunciations
- [ ] "Tỷ Tỷ" (standard) - Detected? ___  Latency: ___ ms
- [ ] "ty ty" (fast) - Detected? ___
- [ ] "ti ti" (soft i) - Detected? ___
- [ ] "Tỷỷỷ Tỷỷỷ" (elongated) - Detected? ___

### Accents (if available)
- [ ] Northern accent - Detected? ___
- [ ] Southern accent - Detected? ___
- [ ] Central accent - Detected? ___

**Target:** ≥90% detection rate, <300ms latency

---

## 2. Multi-Turn Conversations (Requirement 9.2, 18.2)

### Quiet Environment
- [ ] Turn 1: "Tỷ Tỷ 1+1?" - Response: ___
- [ ] Turn 2: "Còn 2+2?" (no wake word) - Response: ___
- [ ] Context preserved? Yes/No

### Light Noise (50-60 dB)
- [ ] Background music - Accuracy: ___% False triggers: ___
- [ ] TV/Radio - Accuracy: ___% False triggers: ___
- [ ] Fan/AC - Accuracy: ___% False triggers: ___

### Moderate Noise (60-70 dB)
- [ ] Multiple people talking - Accuracy: ___% False triggers: ___
- [ ] Kitchen sounds - Accuracy: ___% False triggers: ___

**Target:** ≥85% accuracy in light noise, ≥70% in moderate noise

---

## 3. Timeout Logic (Requirement 9.1, 18.3)

- [ ] Normal pause (1.5s mid-speech) - Continues listening? Yes/No
- [ ] Silence timeout (3s) - Triggers processing? Yes/No  
  Time to processing: ___ ms (target: ~3000ms)
- [ ] Max recording (10s speech) - Times out correctly? Yes/No  
  Plays timeout message? Yes/No
- [ ] No speech after wake - Times out after 10s? Yes/No

**Target:** 3s silence timeout, 10s max recording

---

## 4. Error Scenarios (Requirement 18.4)

### Network Disconnection
- [ ] Disconnect during processing
- [ ] Retries observed: ___ times
- [ ] Fallback to Vosk? Yes/No
- [ ] Error message played? Yes/No
- [ ] System crashed? Yes/No

### API Rate Limiting
- [ ] 5+ rapid queries
- [ ] Handled gracefully? Yes/No
- [ ] Feedback provided? Yes/No

### Ollama Service Crash
- [ ] Stop Ollama during query
- [ ] Falls back to Gemini? Yes/No
- [ ] Response received? Yes/No

### Microphone Disconnection
- [ ] Disconnect during listening
- [ ] Error detected? Yes/No
- [ ] Error message: ___
- [ ] Returns to safe state? Yes/No

### CareCam App Crash
- [ ] Close QianXin.exe during operation
- [ ] Reconnection attempts: ___
- [ ] Falls back to Basic mode? Yes/No
- [ ] Continues operation? Yes/No

**Target:** Graceful handling, no crashes, user feedback provided

---

## 5. UI Config Tool (Requirement 18.5)

### Initial Configuration
- [ ] Tool launches: `python ui_config_tool.py`
- [ ] Select Mic Button - Captured: (___,___)
- [ ] Select Speaker Button - Captured: (___,___)
- [ ] Save Configuration - position_config.json created? Yes/No

### Test Positions
- [ ] Test Mic Position - Clicks correctly? Yes/No
- [ ] Test Speaker Position - Clicks correctly? Yes/No
- [ ] Visual confirmation in CareCam app? Yes/No

### Different Resolutions (if available)
| Resolution | Scaling | Mic OK? | Speaker OK? |
|------------|---------|---------|-------------|
| 1920x1080 | 100% | | |
| 1920x1080 | 125% | | |
| 1366x768 | 100% | | |

**Target:** Accurate button clicks on all tested resolutions

---

## 6. Performance & Latency (Requirement 18.5)

### Component Latencies
- [ ] Wake word detection: ___ ms (target: <300ms)
- [ ] Speech-to-Text (5s): ___ ms (target: <1000ms)
- [ ] AI response: ___ ms (target: <2000ms)
- [ ] Text-to-Speech: ___ ms (target: <500ms)

### End-to-End Latency (10 measurements)
| # | Latency (ms) | < 4000ms? |
|---|--------------|-----------|
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
| **Avg** | | |

**Target:** Average <4000ms, 90% <5000ms

---

## 7. Multi-Turn Context (Requirement 9.2, 18.2)

### Simple Context
- [ ] Q1: "Tỷ Tỷ thủ đô Việt Nam là gì?" - Response: ___
- [ ] Q2: "Dân số của nó?" (no wake) - Understood context? Yes/No

### Extended (5+ turns)
- [ ] Turn 1: "Tỷ Tỷ kể về chó"
- [ ] Turn 2: "Chúng sống bao lâu?" - Context preserved? Yes/No
- [ ] Turn 3: "Giống nào thông minh?" - Context preserved? Yes/No
- [ ] Turn 4: "Giống nào dễ nuôi?" - Context preserved? Yes/No
- [ ] Turn 5: "Cảm ơn Tỷ Tỷ"

### Context Expiry
- [ ] Start conversation, wait 30+ min
- [ ] New query references old context
- [ ] Context expired correctly? Yes/No

**Target:** Context preserved for 5+ turns, expires after 30min

---

## 8. State Transitions (Requirement 9.1)

### Initial State
- [ ] Default_State: Speaker ON, Mic OFF? Yes/No

### Full Cycle Verification
- [ ] Default → Speaking (wake word)
- [ ] Speaking: Mic ON, Speaker OFF, plays "Dạ"
- [ ] Speaking → Listening (after "Dạ")
- [ ] Listening: Speaker ON, Mic OFF, recording
- [ ] Processing (3s silence triggered)
- [ ] Processing → Speaking (plays answer)
- [ ] Speaking → Default (after answer)

### Mutual Exclusion
- [ ] Verified: Mic and Speaker NEVER both ON? Yes/No

**Target:** Correct state flow, hardware constraint respected

---

## 9. Edge Cases

- [ ] Rapid "Tỷ Tỷ" 5x - Handled gracefully? Yes/No
- [ ] Interrupt TTS with new wake word - Behavior: ___
- [ ] Very long input (8-9s) - Processed? Yes/No
- [ ] Mumbled speech - Error message? Yes/No

---

## Test Summary

**Total Tests Run:** ___  
**Passed:** ___  
**Failed:** ___  
**Pass Rate:** ___%

### Critical Issues
1. ___________________________________________
2. ___________________________________________

### Performance Summary
- Avg End-to-End Latency: ___ ms (**Target: <4000ms**)
- Wake Word Accuracy: ___% (**Target: ≥90%**)
- STT Accuracy (quiet): ___% (**Target: ≥95%**)
- STT Accuracy (noisy): ___% (**Target: ≥70%**)

### Overall Assessment
- [ ] **PASS** - All critical requirements met
- [ ] **CONDITIONAL PASS** - Minor issues, requirements mostly met
- [ ] **FAIL** - Critical requirements not met

### Notes
_____________________________________________________________________________
_____________________________________________________________________________
_____________________________________________________________________________

**Tester Signature:** ___________________ **Date:** ___________

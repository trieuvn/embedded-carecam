# Manual Testing Documentation

This directory contains comprehensive manual testing materials for the CareCam Voice Chatbot "Tỷ Tỷ" system.

## Overview

Task 18.2 requires manual testing with real audio devices to validate:
- Wake word detection with various pronunciations and accents (Req 9.1, 18.1)
- Multi-turn conversations in noisy environments (Req 9.2, 18.2)
- Timeout logic with long pauses between speech (Req 9.1, 18.3)
- Error scenarios: network disconnection, API rate limiting (Req 18.4)
- UI config tool to capture button positions (Req 18.5)
- Performance meets latency requirements (<4s end-to-end) (Req 18.5)

## Testing Materials

### 1. **MANUAL_TESTING_GUIDE.md** (Comprehensive Guide)
**Purpose:** Detailed testing procedures with step-by-step instructions

**Contents:**
- 9 test suites covering all requirements
- Expected results and pass criteria
- Detailed procedures for each test case
- Troubleshooting appendix
- ~60 pages of detailed testing instructions

**When to use:** 
- First-time testers
- Detailed validation testing
- Formal QA process
- Complete system validation

### 2. **MANUAL_TESTING_CHECKLIST.md** (Quick Reference)
**Purpose:** Concise checklist for quick testing sessions

**Contents:**
- Condensed test cases with checkboxes
- Quick result tables
- Target metrics for each test
- Summary section for pass/fail
- ~10 pages of quick reference

**When to use:**
- Quick regression testing
- Daily testing during development
- Rapid validation after fixes
- Time-constrained testing

### 3. **manual_test_helper.py** (Interactive Tool)
**Purpose:** Python script to assist with measurements and data collection

**Features:**
- Prerequisites check (audio devices, Ollama, VB-Cable, config)
- Interactive latency measurement tool
- Batch latency testing (10 measurements with statistics)
- Wake word variation testing with results tracking
- Noise robustness testing
- Automatic result saving to JSON
- Report generation

**Usage:**
```bash
python manual_test_helper.py
```

**When to use:**
- Performance testing (latency measurements)
- Data collection for reports
- Automated result tracking
- Statistical analysis

### 4. **manual_test_log_template.md** (Test Log Template)
**Purpose:** Structured template for recording detailed test results

**Contents:**
- Environment information section
- Session-by-session test logs
- Result tables for each test suite
- Issue tracking sections
- Sign-off section
- Appendix for notes

**When to use:**
- Formal test documentation
- Audit trail requirements
- Detailed result recording
- Team collaboration

## Quick Start Guide

### For First-Time Manual Testing:

1. **Prepare Environment:**
   ```bash
   # Ensure system is ready
   cd "d:\carecam\Embeded system"
   python manual_test_helper.py
   # Select option 1: Check Prerequisites
   ```

2. **Choose Your Testing Approach:**

   **Option A: Comprehensive Testing (Recommended for initial validation)**
   - Open `MANUAL_TESTING_GUIDE.md`
   - Follow each test suite sequentially
   - Use `manual_test_log_template.md` to record results
   - Use `manual_test_helper.py` for performance measurements

   **Option B: Quick Testing (For rapid validation)**
   - Open `MANUAL_TESTING_CHECKLIST.md`
   - Work through checklist items
   - Mark pass/fail for each test
   - Fill in summary section

3. **Run System:**
   ```bash
   python main.py
   ```

4. **Execute Tests:**
   - Follow procedures in your chosen guide
   - Use helper script for measurements when needed
   - Record all results

5. **Generate Report:**
   ```bash
   # If using helper script
   python manual_test_helper.py
   # Select option 6: Generate Report
   # Select option 7: Save Results to File
   ```

## Test Suite Overview

### Suite 1: Wake Word Detection (18.1)
**Duration:** ~20 minutes  
**Requirements:** Microphone, quiet environment  
**Tests:** 
- Standard pronunciation
- 5 variations (fast, soft, elongated, etc.)
- Multiple accents (Northern, Southern, Central)
**Target:** ≥90% detection rate, <300ms latency

### Suite 2: Multi-Turn Conversations (18.2)
**Duration:** ~30 minutes  
**Requirements:** Various noise sources  
**Tests:**
- Quiet baseline
- Light noise (50-60 dB)
- Moderate noise (60-70 dB)
- Heavy noise (70+ dB)
**Target:** ≥85% accuracy in light noise, ≥70% in moderate

### Suite 3: Timeout Logic (18.3)
**Duration:** ~15 minutes  
**Requirements:** Timer/stopwatch  
**Tests:**
- Normal pause handling (1.5s)
- 3-second silence timeout
- 10-second max recording
- No speech after wake word
**Target:** 3s timeout triggers correctly, 10s max enforced

### Suite 4: Error Scenarios (18.4)
**Duration:** ~25 minutes  
**Requirements:** Network control, process management  
**Tests:**
- Network disconnection
- API rate limiting
- Ollama service crash
- Microphone disconnection
- CareCam app crash
**Target:** Graceful handling, no system crashes

### Suite 5: UI Config Tool (18.5)
**Duration:** ~10 minutes  
**Requirements:** CareCam app running  
**Tests:**
- Button position capture
- Position testing
- Multiple resolutions (if available)
**Target:** Accurate button clicks in all scenarios

### Suite 6: Performance & Latency (18.5)
**Duration:** ~30 minutes  
**Requirements:** Stopwatch or helper script  
**Tests:**
- Component latency measurements
- 10x end-to-end latency tests
- Statistical analysis
**Target:** Average <4000ms, 90% within target

### Suite 7: Multi-Turn Context (18.2)
**Duration:** ~15 minutes  
**Requirements:** None special  
**Tests:**
- Simple context references
- Extended conversations (5+ turns)
- Context expiry (30 min timeout)
**Target:** Context preserved for 5+ turns

### Suite 8: State Transitions (18.1)
**Duration:** ~10 minutes  
**Requirements:** Visual observation of CareCam app  
**Tests:**
- Initial state verification
- Full conversation cycle
- Mutual exclusion verification
**Target:** Correct state flow, no mic+speaker both ON

### Suite 9: Edge Cases
**Duration:** ~15 minutes  
**Requirements:** None special  
**Tests:**
- Rapid wake word repetition
- Interrupting TTS
- Very long input
- Unclear speech
**Target:** Graceful handling, no crashes

**Total Estimated Duration:** ~2.5-3 hours for complete testing

## Using the Helper Script

### Prerequisites Check
```bash
python manual_test_helper.py
# Select: 1. Check Prerequisites
```
Validates:
- Audio devices available
- Ollama service running
- Position config exists
- VB-Cable installed

### Latency Measurement
```bash
python manual_test_helper.py
# Select: 2. Measure Single Latency (for one-off tests)
# OR: 3. Batch Latency Test (for 10 measurements + statistics)
```
Helps measure end-to-end latency accurately.

### Wake Word Testing
```bash
python manual_test_helper.py
# Select: 4. Wake Word Variation Test
```
Guides through testing 5 wake word variations with result tracking.

### Noise Testing
```bash
python manual_test_helper.py
# Select: 5. Noise Robustness Test
```
Tests accuracy across 4 noise levels with accuracy calculations.

### Report Generation
```bash
python manual_test_helper.py
# Select: 6. Generate Report (view summary)
# Select: 7. Save Results to File (export to JSON)
```
Generates summary and exports data for documentation.

## Tips for Effective Manual Testing

### 1. Environment Preparation
- Test in a quiet room initially
- Have noise sources ready (music, fan, etc.)
- Use a decibel meter app if available
- Clear schedule for uninterrupted testing

### 2. Documentation
- Record everything as you go
- Take screenshots of failures
- Note exact error messages
- Track timestamps

### 3. Performance Testing
- Use helper script for consistent timing
- Run multiple iterations for statistics
- Test at different times of day
- Consider system load variations

### 4. Reproducibility
- Document exact steps taken
- Note environment conditions
- Record configuration settings
- Keep test data for comparison

### 5. Issue Reporting
- Describe expected vs actual behavior
- Include reproduction steps
- Note frequency (always/sometimes/rare)
- Assess severity (critical/major/minor)

## Common Issues and Solutions

### Wake Word Not Detected
**Symptoms:** System doesn't respond to "Tỷ Tỷ"  
**Check:**
- Microphone working (`manual_test_helper.py` option 1)
- Audio level sufficient
- Background noise not too high
- Wake word model loaded (check logs)

### High Latency
**Symptoms:** >4s end-to-end response time  
**Check:**
- Network speed (`ping google.com`)
- Ollama performance (try smaller model)
- CPU usage during test
- Concurrent processes

### Context Not Preserved
**Symptoms:** Follow-up questions not understood  
**Check:**
- Session timeout setting
- Context manager logs
- Memory usage
- Multi-turn logic in dialogue controller

### State Transition Errors
**Symptoms:** Mic and speaker both ON, or stuck state  
**Check:**
- CareCam controller logs
- Button position accuracy
- Hardware constraint logic
- State machine implementation

## Result Interpretation

### Pass Criteria Summary
| Metric | Target | Critical? |
|--------|--------|-----------|
| Wake word detection rate | ≥90% | Yes |
| Wake word latency | <300ms | Yes |
| STT accuracy (quiet) | ≥95% | No |
| STT accuracy (noisy) | ≥70% | No |
| End-to-end latency | <4000ms avg | Yes |
| Error recovery | No crashes | Yes |
| Context preservation | 5+ turns | No |
| State transitions | 100% correct | Yes |

### Overall Assessment Guidelines

**PASS:**
- All critical metrics met
- No critical issues found
- Minor issues only

**CONDITIONAL PASS:**
- Most critical metrics met
- Some non-critical failures
- Workarounds available
- Plan for fixes documented

**FAIL:**
- Critical metrics not met
- Critical issues found
- System unusable in key scenarios
- Major rework needed

## Deliverables

After completing manual testing, provide:

1. **Completed Test Log** (`manual_test_log_template.md` filled out)
2. **Test Results JSON** (from `manual_test_helper.py`)
3. **Summary Report** (can use helper script to generate)
4. **Issue List** (critical and non-critical)
5. **Recommendations** (improvements, fixes needed)

Optional:
- Screenshots of failures
- Video recordings of test scenarios
- Audio samples of problematic inputs
- Performance graphs

## Automation Considerations

While this is manual testing, consider these for future automation:

- Wake word detection can be automated with pre-recorded audio
- Latency measurements can be instrumented in code
- State transitions can be unit tested
- Error injection can be automated (network disconnect, etc.)

However, these aspects require manual testing:
- Real-world noise conditions
- User experience and naturalness
- Audio quality perception
- UI interaction accuracy

## Questions or Issues?

If you encounter problems with the testing materials:

1. Check the troubleshooting section in `MANUAL_TESTING_GUIDE.md`
2. Review prerequisites with helper script
3. Check system logs in `logs/error_handler.log`
4. Verify configuration in `config.py`
5. Test individual components first

## Version History

- **v1.0** (2025-02-09): Initial manual testing documentation
  - Comprehensive guide with 9 test suites
  - Quick checklist for rapid testing
  - Interactive helper script with measurement tools
  - Test log template for documentation

---

**Related Task:** 18.2 - Perform manual testing with real audio devices  
**Requirements:** 9.1, 9.2, 18.1, 18.2, 18.3, 18.4, 18.5  
**Spec Path:** `.kiro/specs/chatbot-voice-interaction-upgrade/`

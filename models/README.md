# Models Directory

This directory contains machine learning models used by the Tỷ Tỷ chatbot system.

## Subdirectories

### wake_word/
Contains wake word detection models for Porcupine wake word engine.

**Setup:**
1. If using Porcupine, place your custom wake word model files (`.ppn`) here
2. Update `WAKE_WORD_MODEL_PATH` in `.env` if using a different location
3. For development, the system will fallback to keyword matching if models are not found

**Model Files:**
- `ty_ty_vi_windows_v3_0_0.ppn` - Vietnamese "Tỷ Tỷ" wake word model (place here if available)

## Notes

- This directory is git-ignored to avoid committing large model files
- Download models separately or train custom models as needed
- Refer to the main README.md for Porcupine setup instructions

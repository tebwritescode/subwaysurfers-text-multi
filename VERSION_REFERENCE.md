# Version Reference Guide

## Quick Rollback Commands

### To rollback to a stable version:
```bash
python version_rollback.py rollback 1.0.11
```

### To see version history:
```bash
python version_rollback.py history
```

### To check current version:
```bash
python version_rollback.py current
```

## Key Versions

### v1.0.11 - Last Stable Before Caption Work
- ✅ Multi-section processing works
- ✅ No text truncation
- ❌ Captions don't match original text (uses STT words)
- ❌ Has timing drift issues

### v1.1.0 - Original Text with STT Timing
- ✅ Captions match original text exactly
- ✅ Word alignment algorithm
- ❌ Still has timing drift

### v1.1.1 - Single Text Cleaning
- ✅ Text cleaned once at start
- ✅ Consistent throughout pipeline
- ❌ Timing drift persists

### v1.1.2 - TESTING (Current)
- 🧪 Text cleaning DISABLED
- 🧪 Testing to isolate timing issues
- ✅ Progress bars re-enabled

## Manual Rollback Steps

If the utility doesn't work, manually rollback:

1. **Change version.py:**
   ```python
   __version__ = "1.0.11"  # or desired version
   ```

2. **For v1.0.11 (re-enable cleantext):**
   In cleantext.py, change:
   ```python
   cleantext = cleantext_original  # not cleantext_disabled
   ```

3. **For versions before v1.1.0 (disable word alignment):**
   In sub.py, change back to using STT words directly:
   ```python
   # Instead of:
   aligned_words, aligned_timestamps = align_words_with_timestamps(...)
   create_video(aligned_words, aligned_timestamps, ...)
   
   # Use:
   create_video(stt_words, stt_timestamps, ...)
   ```

4. **Restart Flask server**

## Testing Checklist

When testing timing issues:

1. **Test with simple text first:**
   - No special characters
   - No emails/URLs
   - Just plain sentences

2. **Test with problematic text:**
   - Email addresses
   - Course codes (CS101)
   - URLs
   - Special formatting

3. **Watch for:**
   - Gradual drift (gets worse over time)
   - Sudden jumps (specific triggers)
   - Consistent offset (always X seconds off)

## Current Investigation

Testing v1.1.2 with cleantext disabled to determine if:
- ✅ Timing is correct = cleantext is the problem
- ❌ Timing still wrong = problem is elsewhere (STT, word alignment, video rendering)
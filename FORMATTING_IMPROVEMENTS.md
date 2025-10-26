# Answer Formatting Improvements

## Problem

The answer was displaying all numbered steps in one long paragraph, making it hard to read:

```
Putting this all together... 1. Open Task Manager by pressing Ctrl + Shift + Esc... 2. In Task Manager, click on the "Processes" tab. 3. Look for "Print Spooler"... 4. Right-click...
```

## Solution Applied

Updated `_format_answer_structure()` in both `reasoning.py` and `streaming_reasoning.py` to automatically format numbered lists.

### What the Formatting Does:

1. **Detects Numbered Steps** - Looks for patterns like "1. ", "2. ", "3. "

2. **Adds Line Breaks** - Inserts line breaks before each numbered item
   ```
   Before: "...steps: 1. Open Task Manager 2. Click..."
   After:  "...steps:
   
   1. Open Task Manager
   
   2. Click..."
   ```

3. **Formats Sub-steps** - Properly indents sub-steps with "o", "-", or "•"
   ```
   1. Open Task Manager
      o Press Ctrl + Shift + Esc
      o Or right-click taskbar
   ```

4. **Highlights Important Terms** - Makes keyboard shortcuts and commands bold
   - **Ctrl + Shift + Esc**
   - **Windows + R**
   - **services.msc**
   - **Task Manager**
   - **Print Spooler**

5. **Adds Section Breaks** - Adds line break after "Here are the steps:" or "following steps:"

## Expected Result

Now the answer will display as:

```
Putting this all together, the answer is as follows: To resolve the error "Execution time out expired, sync not starting", temporarily stop and restart the Print Spooler service on the affected PC. Here are the steps to do so:

1. Open Task Manager by pressing Ctrl + Shift + Esc or right-clicking on the taskbar and selecting "Task Manager."

2. In Task Manager, click on the "Processes" tab.

3. Look for "Print Spooler" or "spoolsv.exe" in the list of running processes.

4. Right-click on "Print Spooler" and select End Task to stop the process temporarily.

5. Press Windows + R to open the Run dialog box.

6. Type services.msc and press Enter to open the Services window.

7. Scroll down to find Print Spooler.

8. Right-click on Print Spooler and select Restart. If the issue persists, a system reboot might help free up resources.

Sources:
[1] Help Desk Control Room Guide v2.pdf • page 60 • Open
```

## Key Features

✅ **Automatic Detection** - Detects if steps are in a paragraph and formats them
✅ **Line Breaks** - Each numbered step on its own line
✅ **Sub-step Indentation** - Sub-steps properly indented
✅ **Bold Highlights** - Important commands and shortcuts are bold
✅ **Clean Spacing** - Proper spacing between steps
✅ **HTML Support** - Uses HTML `<b>` tags for bold text (works in Qt UI)

## Files Modified

- ✅ `src/reasoning.py` - Updated `_format_answer_structure()`
- ✅ `src/streaming_reasoning.py` - Updated `_format_answer_structure()`

## How It Works

The function checks if:
1. The answer has numbered steps (`\d+\.\s+`)
2. The steps are all in one line (no `\n` in first 200 chars)

If both conditions are true, it:
1. Adds `\n\n` before each numbered item
2. Formats sub-steps with proper indentation
3. Highlights important terms with `<b>` tags
4. Adds section breaks for better readability

## Testing

Restart your app and test with any help desk query. The numbered steps should now display on separate lines with proper formatting!

---

**Status:** ✅ COMPLETED
**Result:** Clean, readable numbered lists with proper spacing and highlighting


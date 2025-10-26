# Testing Guide - Answer Quality Improvements

## Quick Test - Print Spooler Issue

### Test Query
```
Error: Execution time out expired, sync not starting
```

### Expected Answer Structure
The answer should now include:

1. **Issue/Error identification**
2. **Cause explanation** (if in PDF)
3. **Complete Resolution with ALL steps:**
   - Step 1: Open Task Manager (with keyboard shortcuts)
   - Step 2: Locate Print Spooler (with specific process name)
   - Step 3: End Task (with specific instructions)
   - Step 4: Restart Print Spooler Service (with complete sub-steps)
   - Step 5: Check Printer Queue (with navigation path)
   - Step 6: Reboot System (optional step)

Each step should include:
- Specific keyboard shortcuts (Ctrl + Shift + Esc, Windows + R)
- Exact commands to type (services.msc)
- Menu navigation paths (Control Panel > Devices and Printers)
- Sub-steps marked with 'o' or '-'

### What Changed

#### Before (Low Quality)
```
To fix the sync issue, check if your PC is running at high resource usage 
and if the print spooler service is consuming most of the resources. If so, 
end the Print Spooler temporarily and restart it to free up system resources...
```
❌ Truncated  
❌ Missing specific steps  
❌ No keyboard shortcuts  
❌ No detailed sub-steps  

#### After (High Quality)
```
Issue:
Error: Execution time out expired, sync not starting

Cause:
PC is running at high resource usage, and the print spooler service is 
consuming most of the resources.

Resolution:
1. Open Task Manager:
   o Press Ctrl + Shift + Esc to open Task Manager, or right-click on the 
     taskbar and select "Task Manager."

2. Locate the Print Spooler:
   o In Task Manager, click on the "Processes" tab.
   o Look for "Print Spooler" or "spoolsv.exe" in the list of running processes.

3. End Task:
   o Right-click on "Print Spooler" and select End Task to stop the process 
     temporarily.

4. Restart the Print Spooler Service:
   o Press Windows + R to open the Run dialog box.
   o Type services.msc and press Enter to open the Services window.
   o Scroll down to find Print Spooler.
   o Right-click on Print Spooler and select Restart.

5. Check the Printer Queue:
   o Go to Control Panel > Devices and Printers.
   o Make sure the printer queue is cleared. Cancel any stuck print jobs if 
     necessary.

6. Reboot the System (Optional):
   o If the issue persists, a system reboot might help free up resources.

Sources:
[1] Help Desk Control Room Guide v2.pdf • page 44 • Open
```
✅ Complete and detailed  
✅ All 6 steps with sub-steps  
✅ Keyboard shortcuts included  
✅ Specific commands and paths  
✅ Proper formatting  

## Additional Test Scenarios

### 1. Driver Installation Issue
**Query:** "How to install printer driver?"
**Expected:** Complete numbered steps with device manager navigation, file selection, etc.

### 2. Network Connectivity Problem
**Query:** "Network connection troubleshooting steps"
**Expected:** Diagnostic steps, command prompts (ipconfig, ping), reset procedures

### 3. Software Configuration
**Query:** "How to configure email settings in Outlook?"
**Expected:** Menu navigation, field-by-field configuration, verification steps

## Validation Checklist

After testing, verify:

- [ ] Answer includes Issue/Cause/Resolution structure (if applicable)
- [ ] All numbered steps from PDF are present (no missing steps)
- [ ] Sub-steps are properly indented with 'o' or '-' markers
- [ ] Keyboard shortcuts are included (Ctrl+X, Alt+Tab, etc.)
- [ ] Specific commands are present (services.msc, cmd, etc.)
- [ ] Menu paths are complete (File > Options > Advanced)
- [ ] Answer is not truncated mid-sentence
- [ ] Source citations are shown at the bottom
- [ ] Formatting preserves readability

## Performance Notes

### Token Usage
- **Before:** 600-800 tokens (insufficient for detailed answers)
- **After:** 2000 tokens (adequate for multi-step procedures)
- **Recommendation:** Can increase to 3000 if handling extremely detailed procedures

### Response Time
- Slightly longer due to more detailed generation
- Typical: 5-15 seconds depending on LLM backend
- Streaming mode provides progressive updates

### Quality Metrics
- **Completeness:** Should match source PDF detail level (100%)
- **Accuracy:** All steps and commands from source preserved
- **Usability:** Agent can follow instructions without additional research

## Troubleshooting

### If answers are still truncated:
1. Check `config.toml` or UI settings for `max_tokens` (should be 2000+)
2. Verify LLM backend supports longer responses
3. Check LLM API limits (some providers cap at 1000 tokens)

### If formatting is incorrect:
1. Check that source PDFs have proper structure
2. Verify the PDF extraction preserved formatting
3. Look at "Reasoning Details" to see raw LLM output

### If steps are missing:
1. Verify retrieval is finding the right PDF sections (check citations)
2. Increase `top_k` in retrieval settings to get more context
3. Check that chunk size is adequate (512 is usually good)

## Backend-Specific Notes

### OpenAI / GPT-4
- Works best with the improved prompts
- Handles long detailed answers well
- May need `max_tokens=3000` for very complex procedures

### Anthropic / Claude
- Excellent at following detailed formatting instructions
- Good at preserving structure from context
- `max_tokens=2000` is usually sufficient

### Ollama (Local)
- Use models with larger context (mistral, llama2-13b+)
- May need to increase `max_tokens` further
- Quality depends on model size and capability

### Google Gemini
- Good at structured outputs
- Handles long contexts well
- `max_tokens=2000` recommended

## Success Criteria

A successful implementation should produce answers that:

1. **Are complete** - No missing steps from source material
2. **Are actionable** - Agent can execute without additional research
3. **Are well-formatted** - Easy to read and follow
4. **Preserve details** - Keyboard shortcuts, commands, and paths included
5. **Match source quality** - Same level of detail as original documentation

## Next Steps After Testing

1. ✅ Verify the changes work with your help desk PDFs
2. ✅ Test with multiple query types (troubleshooting, how-to, configuration)
3. ✅ Gather feedback from help desk agents using the system
4. ✅ Fine-tune `max_tokens` if needed based on your longest procedures
5. ✅ Consider adding custom prompt templates for specific issue types

---

**Ready to test!** Try the print spooler query in your application and compare the results with the expected output above.


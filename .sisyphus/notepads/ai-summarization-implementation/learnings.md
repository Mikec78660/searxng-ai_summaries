# AI Summarization Implementation Learnings

## Template Creation

### ai_summary.html Template
Created `/opt/searxng/searx/templates/simple/answer/ai_summary.html` with:
- Import `icon_small` from `simple/icons.html` for the information-circle icon
- Header with icon and title (falls back to 'AI Summary' if no service name)
- Content area handling empty/None cases with translation
- Optional source link with proper target/rel attributes matching other answer templates

### Patterns Used
1. **Icon usage**: Import `icon_small` from `simple/icons.html` at the top
2. **Answer data structure**: 
   - `answer.answer` - the summary content
   - `answer.service` - the service name (e.g., 'AI Summary')
   - `answer.url` - optional source URL
3. **Link attributes**: Use `results_on_new_tab` variable with proper rel/target attributes
4. **Default filter**: Use `| default('value')` for fallback text
5. **Translation**: Use `{{ _('string') }}` for i18n support

### Reference Templates
- `answer/legacy.html` - Simple answer template pattern
- `answer/weather.html` - More complex answer template with details/summary
- `preferences/ai.html` - Existing AI settings in preferences

## Load Models Button Implementation

### Changes Made (Feb 16, 2026)
Modified `/opt/searxng/searx/templates/simple/preferences/ai.html`:

1. **Added "Load Models" button** after API key field
   - Uses SearXNG button styling: `class="button"`
   - ID: `load_models_btn`

2. **Removed automatic fetching**:
   - Removed `FALLBACK_MODELS` array
   - Removed `cachedModels` variable
   - Removed `currentEndpoint` variable
   - Removed `debounceTimer` variable
   - Removed `DOMContentLoaded` automatic fetch logic
   - Removed endpoint input event listener

3. **Added model selection error span**
   - ID: `ai_model_error`
   - Shows validation error when saving without selecting model

4. **Updated placeholder text**
   - Changed from "Loading models..." to "Click 'Load Models' to fetch available models"

5. **Added form validation**
   - On form submit, checks if AI summarization is enabled AND no model selected
   - If validation fails, shows error message and prevents form submission

6. **Button functionality**:
   - Fetches models from `{endpoint}/models` on click
   - Shows "Loading..." state while fetching
   - Restores button state after completion
   - Handles errors gracefully with user-friendly messages

## Investigation: AI Preferences Not Saving (Feb 16, 2026)

### Root Cause Identified

There is a **critical bug in `parse_form()` method** in `/opt/searxng/searx/preferences.py`:

**The `parse_form()` method is missing the locked preference check that exists in `parse_dict()`.**

#### Comparison:

**`parse_dict()` (lines 582-594)** - HAS the locked check:
```python
def parse_dict(self, input_data: dict[str, str]):
    for user_setting_name, user_setting in input_data.items():
        if user_setting_name in self.key_value_settings:
            if self.key_value_settings[user_setting_name].locked:
                continue  # <-- Skips locked settings
            self.key_value_settings[user_setting_name].parse(user_setting)
```

**`parse_form()` (lines 596-622)** - MISSING the locked check:
```python
def parse_form(self, input_data: dict[str, str]):
    for user_setting_name, user_setting in input_data.items():
        if user_setting_name in self.key_value_settings:
            # NO locked check here! <-- BUG
            self.key_value_settings[user_setting_name].parse(user_setting)
```

### Impact

When a user saves preferences via form POST:
1. If ANY AI setting is locked in settings.yml, `parse_form()` will still try to parse and save it
2. This causes either:
   - Silent failure (settings not saved but no error shown)
   - ValidationException if validation fails
   - Or potentially overwriting locked settings incorrectly

### Secondary Issue: ai_model Dropdown

The AI model dropdown has a secondary issue:
- Line 54-55 in ai.html: `<option value="" disabled selected>Click "Load Models" to fetch...</option>`
- Default value is empty string `""`
- If user hasn't clicked "Load Models" button yet, submitting form sends empty string
- `EnumStringSetting.parse()` will validate "" against the choices list and FAIL with ValidationException

### Solution Options

1. **Primary Fix**: Add locked check to `parse_form()` in preferences.py
   - Add the same `if self.key_value_settings[user_setting_name].locked: continue` check

2. **Secondary Fix**: Handle empty string for ai_model in the form
   - Option A: Make the dropdown pre-populated with the default model (gpt-3.5-turbo)
   - Option B: Allow empty string as valid choice for ai_model
   - Option C: Make the field optional when AI summarization is disabled

### Investigation Files
- `/opt/searxng/searx/preferences.py` - Check `parse_form()` vs `parse_dict()` methods
- `/opt/searxng/searx/templates/simple/preferences/ai.html` - Form field structure
- `/opt/searxng/searx/webapp.py` - Line 929 calls `parse_form()`, Line 930 catches ValidationException

## Additional Findings (Feb 16, 2026) - Verified Root Cause

### Primary Issue: Checkbox Missing `value` Attribute

In `searx/templates/simple/preferences/ai.html` (lines 4-11), the checkbox has NO `value` attribute:
```html
<input type="checkbox" {{- ' ' -}}
       name="ai_summarization_enabled" {{- ' ' -}}
       ...>
```

When unchecked, browser sends nothing. When checked, sends `name=on` (default HTML behavior).

**Working checkboxes have `value` attribute** (e.g., image_proxy.html):
```html
<input type="checkbox" {{- ' ' -}}
       name="image_proxy" {{- ' ' -}}
       value="None" {{- ' ' -}}  <!-- THIS IS MISSING IN ai.html -->
       ...>
```

The BooleanSetting.parse() uses MAP_STR2BOOL which has 'on': True mapping, so this actually WORKS.

### Secondary Issue: ValidationException Silently Fails Entire Save

In `webapp.py` lines 928-932:
```python
try:
    sxng_request.preferences.parse_form(sxng_request.form)
except ValidationException:
    sxng_request.errors.append(gettext('Invalid settings, please edit your preferences'))
    return resp  # Returns early without saving ANY settings!
```

**The REAL bug**: When ai_model dropdown sends empty string (because user hasn't clicked "Load Models"):
1. `EnumStringSetting.parse("")` is called
2. `_validate_selection("")` checks if "" is in choices
3. It's NOT in the choices list (lines 521-539 in preferences.py)
4. Raises ValidationException
5. **Entire preferences save fails silently** - user sees redirect but NO error message typically

### Why This Matters

The issue isn't that `ai_summarization_enabled` isn't saving - the issue is that:
1. If ai_model is empty, ValidationException is thrown
2. This causes the ENTIRE form save to fail
3. All settings appear "not saved" even if they were valid

### Exact Fixes Required

**Fix 1: Add `value="on"` to checkbox in ai.html (line 4-7):**
```html
<input type="checkbox" {{- ' ' -}}
       name="ai_summarization_enabled" {{- ' ' -}}
       value="on" {{- ' ' -}}  <!-- ADD THIS -->
       aria-labelledby="pref_ai_summarization_enabled" {{- ' ' -}}
       class="checkbox-onoff" {{- ' ' -}}
```

**Fix 2: Add empty string to ai_model choices in preferences.py (lines 518-540):**
```python
'ai_model': EnumStringSetting(
    "gpt-3.5-turbo",
    locked=is_locked('ai_model'),
    choices=[
        "",  # ADD THIS - allow empty string for disabled state
        "gpt-3.5-turbo",
        ...
    ]
),
```

**Alternative Fix 2**: Make ai_model not required when AI summarization is disabled (more complex, requires changing form handling logic).

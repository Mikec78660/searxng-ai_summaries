# SearXNG Template & Static Files Organization

## Executive Summary

SearXNG uses a **single-theme architecture** (simple theme) with CSS variables for theming (light/dark/black modes). The build system uses Vite with LESS for CSS and TypeScript for JS.

---

## 1. Directory Structure

### Templates
```
/opt/searxng/searx/templates/simple/
├── base.html                    # Base layout (extends by all pages)
├── page_with_header.html        # Page with SearXNG logo header
├── index.html                   # Homepage
├── search.html                  # Search field component
├── results.html                 # Search results page
├── preferences.html             # Settings/preferences page (main)
├── stats.html                   # Engine statistics page
├── macros.html                  # Reusable template macros
├── icons.html                   # SVG icon definitions
├── 404.html                     # Error page
│
├── preferences/                 # Preference component templates
│   ├── theme.html              # Theme/style dropdowns
│   ├── language.html           # Language selector
│   ├── autocomplete.html       # Autocomplete dropdown
│   ├── image_proxy.html        # Image proxy toggle
│   ├── center_alignment.html   # Center alignment toggle
│   ├── cookies.html            # Cookie management
│   ├── footer.html             # Save/Reset buttons
│   └── [20+ more preference templates]
│
├── elements/                    # Reusable UI components
│   ├── corrections.html
│   ├── suggestions.html
│   ├── infobox.html
│   └── apis.html
│
├── filters/                     # Search filter components
│   ├── time_range.html
│   ├── safesearch.html
│   └── languages.html
│
├── result_templates/            # Search result type templates
│   ├── default.html
│   ├── images.html
│   ├── videos.html
│   ├── code.html
│   ├── paper.html
│   └── [more result types]
│
└── messages/                    # Message/notification templates
    ├── no_results.html
    └── no_cookies.html
```

### Static Assets (Compiled)
```
/opt/searxng/searx/static/themes/simple/
├── sxng-ltr.min.css            # Main stylesheet (LTR languages)
├── sxng-rtl.min.css            # Main stylesheet (RTL languages)
├── sxng-rss.min.css            # RSS stylesheet
├── sxng-core.min.js            # Main JavaScript bundle
├── sxng-core.min.js.map        # Source map
├── manifest.json               # Build manifest
│
├── chunk/                      # Lazy-loaded JS chunks
│   ├── [hash].min.js
│   └── [hash].min.js.map
│
└── img/                        # Images & icons
    ├── favicon.png
    ├── favicon.svg
    ├── searxng.png
    ├── searxng.svg
    ├── select-dark.svg         # Dropdown arrow (dark mode)
    ├── select-light.svg        # Dropdown arrow (light mode)
    └── [more images]
```

### Client Source (Development)
```
/opt/searxng/client/simple/
├── src/
│   ├── js/                     # TypeScript source
│   │   ├── index.ts           # Entry point
│   │   ├── toolkit.ts         # Utility functions
│   │   ├── router.ts          # Route handling
│   │   ├── main/              # Feature modules
│   │   │   ├── preferences.ts # Preferences page JS
│   │   │   ├── results.ts     # Results page JS
│   │   │   ├── search.ts      # Search functionality
│   │   │   ├── keyboard.ts    # Keyboard shortcuts
│   │   │   └── autocomplete.ts
│   │   ├── plugin/            # Plugin system
│   │   └── util/              # Utilities
│   │
│   ├── less/                   # LESS stylesheets
│   │   ├── style-ltr.less     # LTR entry point
│   │   ├── style-rtl.less     # RTL entry point
│   │   ├── style.less         # Main styles
│   │   ├── definitions.less   # CSS variables & colors
│   │   ├── toolkit.less       # Form elements & components
│   │   ├── preferences.less   # Preferences-specific styles
│   │   ├── search.less        # Search field styles
│   │   └── [more modules]
│   │
│   ├── svg/                    # SVG source files
│   │   ├── select-light.svg
│   │   └── select-dark.svg
│   │
│   └── brand/                  # Brand assets
│       ├── searxng.svg
│       └── searxng-wordmark.svg
│
├── vite.config.ts             # Vite build configuration
├── package.json               # NPM dependencies
└── tools/                     # Build tools
```

---

## 2. Template Naming Conventions

### File Naming
- **Page templates**: Descriptive nouns (`index.html`, `results.html`, `preferences.html`)
- **Component templates**: Nouns describing the component (`theme.html`, `language.html`)
- **Macro file**: `macros.html` (contains reusable Jinja2 macros)
- **Base template**: `base.html` (root layout template)

### Template Inheritance Pattern
```html
<!-- base.html -->
<!DOCTYPE html>
<html>
<head>...</head>
<body>
  <main>{% block content %}{% endblock %}</main>
</body>
</html>

<!-- preferences.html -->
{%- extends "simple/page_with_header.html" -%}
{%- block content -%}
  <!-- page content -->
{%- endblock -%}
```

### Key Blocks in base.html
- `{% block title %}` - Page title
- `{% block meta %}` - Meta tags
- `{% block head %}` - Additional head content
- `{% block header %}` - Header content
- `{% block content %}` - Main page content
- `{% block linkto_preferences %}` - Preferences link override

---

## 3. Template Macros & Includes

### Available Macros (from `macros.html`)

```html
<!-- Checkbox Toggle (On/Off) -->
{% from 'simple/macros.html' import checkbox_onoff %}
{{ checkbox_onoff('setting_name', checked=true) }}

<!-- Result Header -->
{{ result_header(result, favicons, image_proxify) }}

<!-- Result Footer -->
{{ result_footer(result) }}

<!-- Draw Favicon -->
{{ draw_favicon('google') }}

<!-- Result Link -->
{{ result_link(url, title, classes='my-class') }}
```

### Icons (from `icons.html`)

```html
{% from 'simple/icons.html' import icon_small, icon_big %}

<!-- Small icon (1rem) -->
{{ icon_small('settings') }}

<!-- Big icon (1.5rem) -->
{{ icon_big('information-circle') }}

<!-- Custom icon -->
{{ icon('search', 'Search icon') }}
```

### Available Icons
- `alert`, `appstore`, `book`, `close`, `download`
- `ellipsis-vertical`, `file-tray-full`, `film`, `globe`
- `heart`, `image`, `information-circle`, `layers`, `location`
- `magnet`, `musical-notes`, `navigate-*`, `newspaper`, `people`
- `play`, `radio`, `save`, `school`, `search`, `settings`
- `tv`, and more...

---

## 4. Form Element Patterns

### Toggle/On-Off Checkbox (`.checkbox-onoff`)

**Template:**
```html
<fieldset>
  <legend id="pref_setting_name">{{ _('Setting Label') }}</legend>
  <p class="value">
    <input type="checkbox"
           name="setting_name"
           aria-labelledby="pref_setting_name"
           class="checkbox-onoff"
           {% if preferences.get_value('setting_name') %}checked{% endif %}>
  </p>
  <div class="description">
    {{ _('Description of what this setting does.') }}
  </div>
</fieldset>
```

**CSS Class:** `.checkbox-onoff` - Creates a sliding toggle switch

### Dropdown/Select

**Template:**
```html
<fieldset>
  <legend id="pref_dropdown">{{ _('Dropdown Label') }}</legend>
  <div class="value">
    <select name="dropdown_name" aria-labelledby="pref_dropdown">
      <option value=""> - </option>
      {%- for option in options -%}
        <option value="{{ option }}"
          {%- if option == current_value %} selected="selected" {%- endif -%}>
          {{- option -}}
        </option>
      {%- endfor -%}
    </select>
  </div>
  <div class="description">
    {{ _('Description text') }}
  </div>
</fieldset>
```

### Text Input

**Template:**
```html
<fieldset>
  <legend id="pref_text_input">{{ _('Text Input Label') }}</legend>
  <div class="value">
    <input type="text"
           name="text_input_name"
           value="{{ current_value }}"
           placeholder="{{ _('Placeholder text') }}">
  </div>
  <div class="description">
    {{ _('Description') }}
  </div>
</fieldset>
```

### Standard Checkbox (Table/List)

**Template:**
```html
{%- macro checkbox(name, checked, disabled) -%}
  <input type="checkbox"
    {%- if name %} name="{{ name }}" {%- endif %}
    value="None"
    {%- if checked %} checked {%- endif -%}
    {%- if disabled %} disabled {%- endif -%}>
{%- endmacro -%}
```

### Reversed Checkbox (for opt-out features)

```html
<input type="checkbox"
       name="plugin_id"
       class="checkbox-onoff reversed-checkbox"
       {%- if plugin_id not in allowed_plugins %} checked {%- endif -%}>
```

---

## 5. Adding New CSS/JS for AI Features

### CSS (LESS) Development

1. **Edit source file** at `/opt/searxng/client/simple/src/less/`

2. **Create new module** (recommended for AI features):
   ```less
   // ai-features.less
   .ai-result {
     border-left: 3px solid var(--color-ai-accent);
     padding-left: 1rem;
     
     .ai-summary {
       font-size: 0.95em;
       color: var(--color-base-font);
     }
   }
   ```

3. **Import in main stylesheet** (`style.less`):
   ```less
   @import "ai-features.less";
   ```

4. **Build** (from `/opt/searxng/client/simple/`):
   ```bash
   npm run build
   ```

5. **Output** goes to `/opt/searxng/searx/static/themes/simple/sxng-ltr.min.css`

### JS Development

1. **Create feature module** at `/opt/searxng/client/simple/src/js/main/ai.ts`

2. **Auto-loading**: Files in `main/` are auto-globbed via `index.ts`:
   ```typescript
   // src/js/index.ts
   void import.meta.glob(["./*.ts", "./util/**/.ts"], { eager: true });
   ```

3. **Use toolkit utilities**:
   ```typescript
   import { http, listen, settings } from "../toolkit.ts";
   
   // HTTP request
   const res = await http("GET", "/api/ai/summary");
   
   // Event listener helper
   listen("click", "#ai-toggle", (e) => {
     // handle click
   });
   ```

4. **Build** produces `/opt/searxng/searx/static/themes/simple/sxng-core.min.js`

---

## 6. Theme/Skin System

### Theme Architecture

SearXNG uses **CSS custom properties (variables)** for theming, NOT multiple theme files.

**Variable Definitions** (`definitions.less`):
```less
// Light theme (default)
:root {
  --color-base-font: #444;
  --color-base-background: #fff;
  --color-btn-background: #3050ff;
  --color-btn-font: #fff;
  // ... 100+ variables
}

// Dark theme mixin
.dark-themes() {
  --color-base-font: #bbb;
  --color-base-background: #222428;
  // ... dark overrides
}

// Auto-switch based on device preference
@media (prefers-color-scheme: dark) {
  :root.theme-auto { .dark-themes(); }
}

// Manual dark theme
:root.theme-dark { .dark-themes(); }

// Black (AMOLED) theme
:root.theme-black { 
  .dark-themes(); 
  .black-themes();
}
```

### Available Themes
1. **auto** - Follows browser/system preference
2. **light** - Light colors
3. **dark** - Dark colors
4. **black** - OLED black (dark + pure black background)

### CSS Variables for Form Elements

```css
/* Select/Dropdown */
--color-toolkit-select-background: #e1e1e1;
--color-toolkit-select-background-hover: #bbb;

/* Checkboxes */
--color-toolkit-checkbox-onoff-off-background: #ddd;
--color-toolkit-checkbox-onoff-on-background: #ddd;
--color-toolkit-checkbox-onoff-on-mark-background: #3050ff;
--color-toolkit-checkbox-onoff-on-mark-color: #fff;

/* Input Text */
--color-toolkit-input-text-font: #222;
```

### Adding AI-Specific Theme Variables

Add to `definitions.less` in the `:root` section:
```less
:root {
  // ... existing variables
  
  /// AI Features Colors
  --color-ai-accent: #3050ff;
  --color-ai-background: #f0f4ff;
  --color-ai-border: #d0d8ff;
}

.dark-themes() {
  // ... existing dark overrides
  
  --color-ai-accent: #58f;
  --color-ai-background: #1a1f2e;
  --color-ai-border: #2a3f5e;
}
```

---

## 7. Preference Integration Pattern

### Adding New Preference Section

**Step 1: Create preference template** (`preferences/ai_settings.html`):
```html
<fieldset>
  <legend id="pref_ai_enabled">{{ _('AI Summary') }}</legend>
  <p class="value">
    <input type="checkbox"
           name="ai_enabled"
           aria-labelledby="pref_ai_enabled"
           class="checkbox-onoff"
           {%- if preferences.get_value('ai_enabled') %}checked{%- endif -%}>
  </p>
  <div class="description">
    {{ _('Show AI-generated summaries in search results.') }}
  </div>
</fieldset>

<fieldset>
  <legend id="pref_ai_model">{{ _('AI Model') }}</legend>
  <div class="value">
    <select name="ai_model" aria-labelledby="pref_ai_model">
      {%- for model in ai_models -%}
        <option value="{{ model.id }}"
          {%- if model.id == current_ai_model %} selected="selected"{%- endif -%}>
          {{- model.name -}}
        </option>
      {%- endfor -%}
    </select>
  </div>
  <div class="description">
    {{ _('Select the AI model for generating summaries.') }}
  </div>
</fieldset>
```

**Step 2: Include in preferences.html**:
```html
{{- tab_header('maintab', 'ai', _('AI Features')) -}}
{%- include 'simple/preferences/ai_settings.html' -%}
{{- tab_footer() -}}
```

**Step 3: Register preference in Python** (in `searx/preferences.py`):
The preference system automatically handles form submission and cookie storage.

---

## 8. Key Files Summary

| Purpose | Path |
|---------|------|
| Base template | `/opt/searxng/searx/templates/simple/base.html` |
| Macros | `/opt/searxng/searx/templates/simple/macros.html` |
| Icons | `/opt/searxng/searx/templates/simple/icons.html` |
| Preferences page | `/opt/searxng/searx/templates/simple/preferences.html` |
| CSS variables | `/opt/searxng/client/simple/src/less/definitions.less` |
| Form components | `/opt/searxng/client/simple/src/less/toolkit.less` |
| Preferences styles | `/opt/searxng/client/simple/src/less/preferences.less` |
| JS entry | `/opt/searxng/client/simple/src/js/index.ts` |
| JS toolkit | `/opt/searxng/client/simple/src/js/toolkit.ts` |
| Build config | `/opt/searxng/client/simple/vite.config.ts` |

---

## 9. Build Process

```bash
# Navigate to client directory
cd /opt/searxng/client/simple

# Install dependencies
npm install

# Build for production
npm run build

# Build outputs to:
# - /opt/searxng/searx/static/themes/simple/

# Lint & fix
npm run fix
```

---

## 10. Best Practices for AI Features

1. **Use existing form patterns** - Copy from existing preference templates
2. **Leverage CSS variables** - Define AI-specific colors in `definitions.less`
3. **Use checkbox-onoff class** - For toggle switches
4. **Follow fieldset/legend/value/description pattern** - For consistent layout
5. **Use aria-labelledby** - For accessibility
6. **Add translations** - Wrap labels with `{{ _('Text') }}`
7. **Create separate LESS module** - For AI-specific styles
8. **Use toolkit.ts helpers** - For HTTP requests and event handling

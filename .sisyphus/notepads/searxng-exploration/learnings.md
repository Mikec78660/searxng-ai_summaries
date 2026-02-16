# SearXNG Search Results Rendering - Comprehensive Findings

## Overview
This document details how SearXNG renders search results pages and identifies injection points for adding AI summary content above search results.

---

## 1. Main Search Results Template

**File Path:** `/opt/searxng/searx/templates/simple/results.html`

This is the primary template for rendering search results. Key structure:

```html
{% extends "simple/base.html" %}

{% block content %}
{% include 'simple/search.html' %}  <!-- Search form at top -->

<div id="results">
  
  {%- if answers -%}
    {%- include 'simple/elements/answers.html' -%}  <!-- ANSWERS SECTION (above results) -->
  {%- endif %}

  <div id="sidebar">
    <!-- Sidebar content: infoboxes, suggestions, etc. -->
  </div>

  <div id="urls" role="main">
  {% for result in results %}
    {% include get_result_template('simple', result['template']) %}
  {% endfor %}
  </div>
</div>
{% endblock %}
```

**Key Observation:** The `answers` section is rendered ABOVE the main results (line 23-25), making it the perfect location for AI summaries.

---

## 2. Backend Route That Renders Search Results

**File Path:** `/opt/searxng/searx/webapp.py`
**Function:** `search()` (line 620-786)
**Route:** `@app.route('/search', methods=['GET', 'POST'])`

### Core Flow:
1. Parse search query from request
2. Execute search via `searx.search.SearchWithPlugins`
3. Get `ResultContainer` with results
4. Process results (highlighting, grouping)
5. Render template with context data

### Template Rendering (lines 757-786):
```python
return render(
    'results.html',
    results=results,
    q=sxng_request.form['q'],
    selected_categories=search_query.categories,
    pageno=search_query.pageno,
    time_range=search_query.time_range or '',
    number_of_results=format_decimal(result_container.number_of_results),
    suggestions=suggestion_urls,
    answers=result_container.answers,  # <-- ANSWERS PASSED HERE
    corrections=correction_urls,
    infoboxes=result_container.infoboxes,
    engine_data=result_container.engine_data,
    paging=result_container.paging,
    # ... more context
)
```

---

## 3. Data Structure Passed to Results Template

### Main Context Variables:

| Variable | Source | Description |
|----------|--------|-------------|
| `results` | `result_container.get_ordered_results()` | Main search results list |
| `q` | `sxng_request.form['q']` | Search query string |
| `answers` | `result_container.answers` | Answer objects (appears above results) |
| `infoboxes` | `result_container.infoboxes` | Info boxes (appears in sidebar) |
| `suggestions` | `result_container.suggestions` | Query suggestions |
| `corrections` | `result_container.corrections` | Spelling corrections |
| `number_of_results` | `result_container.number_of_results` | Total result count |
| `paging` | `result_container.paging` | Pagination enabled flag |
| `engine_data` | `result_container.engine_data` | Engine-specific data |

### ResultContainer Class
**File:** `/opt/searxng/searx/results.py` (line 53+)

```python
class ResultContainer:
    main_results_map: dict[int, MainResult | LegacyResult]
    infoboxes: list[LegacyResult]
    suggestions: set[str]
    answers: AnswerSet  # <-- Key for AI summary
    corrections: set[str]
    engine_data: dict[str, dict[str, str]]
    paging: bool
```

---

## 4. Answers System - Perfect for AI Summary

### Answer Rendering Flow:

1. **Template:** `/opt/searxng/searx/templates/simple/elements/answers.html`
   ```html
   <div id="answers" role="complementary">
     <h4 class="title">Answers : </h4>
     {%- for answer in answers -%}
       <div class="answer">
         {%- include ("simple/" + (answer.template or "answer/legacy.html")) -%}
       </div>
     {%- endfor -%}
   </div>
   ```

2. **Answer Types:** `/opt/searxng/searx/result_types/answer.py`
   - `Answer` - Simple text answer with optional URL
   - `Translations` - Translation results
   - `WeatherAnswer` - Weather data
   - `BaseAnswer` - Base class for custom answers

3. **Answer Class Structure:**
   ```python
   class Answer(BaseAnswer, kw_only=True):
       template: str = "answer/legacy.html"
       answer: str  # Text of the answer
       url: str | None = None  # Optional link
   ```

---

## 5. Template Inheritance Structure

```
base.html (root template)
├── results.html (extends base, for search results)
│   ├── search.html (search form)
│   ├── elements/answers.html (answers section)
│   │   └── answer/*.html (individual answer templates)
│   ├── elements/infobox.html (sidebar infoboxes)
│   └── result_templates/*.html (result type templates)
├── index.html (homepage)
└── preferences.html (settings page)
```

### Base Template (`/opt/searxng/searx/templates/simple/base.html`):
- Defines HTML structure, meta tags, CSS/JS includes
- Provides blocks: `title`, `meta`, `head`, `header`, `content`
- Results template overrides `content` block

---

## 6. How to Inject AI Summary Content

### Option A: Create Custom Answer Type (RECOMMENDED)

1. **Create new answer template:**
   ```html
   <!-- searx/templates/simple/answer/ai_summary.html -->
   <div class="ai-summary">
     <h5>{{ answer.title }}</h5>
     <div class="ai-summary-content">{{ answer.content }}</div>
     {%- if answer.sources -%}
     <div class="ai-summary-sources">
       {%- for source in answer.sources -%}
         <a href="{{ source.url }}">{{ source.title }}</a>
       {%- endfor -%}
     </div>
     {%- endif -%}
   </div>
   ```

2. **Create answer type:**
   ```python
   # In result_types/answer.py or new module
   class AISummary(BaseAnswer, kw_only=True):
       template: str = "answer/ai_summary.html"
       title: str
       content: str
       sources: list[dict] = []
   ```

3. **Add to ResultContainer:**
   - The answers are automatically collected in `ResultContainer.answers` (AnswerSet)
   - No changes needed to ResultContainer

4. **Create plugin to generate AI summary:**
   ```python
   from searx.plugins import Plugin, PluginInfo
   from searx.result_types import EngineResults
   
   class AISummaryPlugin(Plugin):
       id = "ai_summary"
       
       def post_search(self, request, search):
           results = EngineResults()
           # Generate AI summary from search_query and results
           summary = generate_ai_summary(search.search_query.query, search.result_container)
           results.add(results.types.AISummary(
               title="AI Summary",
               content=summary,
               sources=[...]
           ))
           return results
   ```

### Option B: Modify Existing Answer Template

Simply extend `/opt/searxng/searx/templates/simple/answer/legacy.html` or create a new template and set `answer.template = "answer/my_custom.html"`.

### Option C: Add New Template Variable

1. Modify `webapp.py` search() function to pass additional context:
   ```python
   return render(
       'results.html',
       # ... existing context ...
       ai_summary=generate_summary(...),  # Add this line
   )
   ```

2. Modify `results.html` to render it:
   ```html
   {%- if ai_summary -%}
     {%- include 'simple/elements/ai_summary.html' -%}
   {%- endif %}
   ```

---

## 7. Existing Plugins That Create Answers

### Example 1: Self Info Plugin
**File:** `/opt/searxng/searx/plugins/self_info.py`

```python
def post_search(self, request, search):
    results = EngineResults()
    if self.ip_regex.search(search.search_query.query):
        results.add(
            results.types.Answer(answer=gettext("Your IP is: ") + ip_address)
        )
    return results
```

### Example 2: Unit Converter Plugin
**File:** `/opt/searxng/searx/plugins/unit_converter.py`

```python
def post_search(self, request, search):
    results = EngineResults()
    # ... conversion logic ...
    results.add(results.types.Answer(answer=target_val))
    return results
```

---

## 8. Plugin System Architecture

**File:** `/opt/searxng/searx/plugins/_core.py`

### Plugin Lifecycle:
1. `init(app)` - Initialize plugin (runs once)
2. `pre_search(request, search)` - Before search (can cancel)
3. `on_result(request, search, result)` - For each result (can filter/modify)
4. `post_search(request, search)` - After search (can add results)

### Adding Results via Plugin:
Plugins use `post_search()` to add results:
```python
def post_search(self, request, search):
    results = EngineResults()
    results.add(results.types.Answer(...))
    return results
```

Results are automatically added to `result_container` with prefix `plugin: {plugin.id}`.

---

## 9. Key Files Summary

| Purpose | File Path |
|---------|-----------|
| Main search route | `/opt/searxng/searx/webapp.py` (line 620+) |
| Results template | `/opt/searxng/searx/templates/simple/results.html` |
| Base template | `/opt/searxng/searx/templates/simple/base.html` |
| Answers element | `/opt/searxng/searx/templates/simple/elements/answers.html` |
| Answer templates | `/opt/searxng/searx/templates/simple/answer/*.html` |
| Answer types | `/opt/searxng/searx/result_types/answer.py` |
| Result container | `/opt/searxng/searx/results.py` |
| Plugin base class | `/opt/searxng/searx/plugins/_core.py` |
| Example plugins | `/opt/searxng/searx/plugins/self_info.py` |
| Engine results | `/opt/searxng/searx/result_types/__init__.py` |

---

## 10. Recommended Implementation Path

To add an AI summary section above search results:

1. **Create new answer type** in `result_types/answer.py`:
   - Inherit from `BaseAnswer`
   - Define `template = "answer/ai_summary.html"`
   - Add fields: `title`, `content`, `sources[]`

2. **Create answer template** at `templates/simple/answer/ai_summary.html`:
   - Style it to stand out as AI-generated content
   - Include sources for transparency

3. **Create plugin** in `plugins/ai_summary.py`:
   - Inherit from `Plugin`
   - Implement `post_search()` method
   - Generate summary from query + top results
   - Return `EngineResults` with AISummary

4. **Register plugin** in settings.yml (or however plugins are configured)

5. **The answers system will automatically**:
   - Render AI summary above main results
   - Handle deduplication (via AnswerSet)
   - Sort with other answers by template name

This approach leverages SearXNG's existing architecture and requires minimal changes to core code.

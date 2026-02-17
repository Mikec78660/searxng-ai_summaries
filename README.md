<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->

[![SearXNG](./client/simple/src/brand/searxng.svg)](https://searxng.org)

# SearXNG AI Summaries Fork

This is a **fork of SearXNG** that adds **AI-powered search result summarization**.
This fork allows users to get concise AI-generated summaries of their search results,
helping them quickly understand and digest information from multiple sources without
clicking through each result individually.

The original SearXNG project is available at: https://github.com/searxng/searxng

## Demo

<video width="100%" controls>
  <source src="docs/assets/demo.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>

[Download demo video](./docs/assets/demo.mp4)

## Features

This fork extends SearXNG with the following AI summarization capabilities:

- **Automatic Summaries**: Get AI-generated summaries of search results
- **Customizable Prompts**: Configure the system prompt that guides the AI
- **Multiple API Support**: Works with any OpenAI-compatible API endpoint (Ollama, OpenAI, etc.)
- **Flexible Configuration**: Adjust timeout, max tokens, and number of results to summarize

## AI Summarization Configuration Options

The following options can be configured in the Preferences tab:

1. **Enable AI Summarization** (`ai_summarization_enabled`)
   - Boolean toggle to enable or disable AI summarization
   - Default: `False` (disabled)

2. **API Endpoint** (`ai_api_endpoint`)
   - The URL of your AI API endpoint (e.g., `http://localhost:11434/v1/chat/completions` for Ollama)
   - Must be an OpenAI-compatible API endpoint

3. **API Key** (`ai_api_key`)
   - Your API key for authentication
   - Can be left empty for local endpoints like Ollama

4. **Model** (`ai_model`)
   - The model ID to use for summarization (e.g., `gpt-4`, `llama3`, `mistral`)

5. **Number of Results to Summarize** (`ai_num_results`)
   - How many search results to include in the summary
   - Default: `5`

6. **Timeout per Result** (`ai_timeout_per_result`)
   - Timeout in seconds when fetching each result's content
   - Default: `5` seconds

7. **Max Tokens** (`ai_max_tokens`)
   - Maximum number of tokens in the generated summary
   - Default: `500`

8. **System Prompt** (`ai_system_prompt`)
   - Custom prompt that instructs the AI how to summarize
   - Default: `"You are a helpful assistant that summarizes search results. We are looking for this information {query} Provide a concise summary of the search results in no more than 2-3 paragraphs from these web pages: {results}. Focus on the most relevant information."`

---

SearXNG is a [metasearch engine](https://en.wikipedia.org/wiki/Metasearch_engine). Users are neither tracked nor profiled.

[![Organization](https://img.shields.io/badge/organization-3050ff?style=flat-square&logo=searxng&logoColor=fff&cacheSeconds=86400)](https://github.com/searxng)
[![Documentation](https://img.shields.io/badge/documentation-3050ff?style=flat-square&logo=readthedocs&logoColor=fff&cacheSeconds=86400)](https://docs.searxng.org)
[![License](https://img.shields.io/github/license/searxng/searxng?style=flat-square&label=license&color=3050ff&cacheSeconds=86400)](https://github.com/searxng/searxng/blob/master/LICENSE)
[![Commits](https://img.shields.io/github/commit-activity/y/searxng/searxng/master?style=flat-square&label=commits&color=3050ff&cacheSeconds=3600)](https://github.com/searxng/searxng/commits/master/)
[![Translated](https://img.shields.io/weblate/progress/searxng?server=https%3A%2F%2Ftranslate.codeberg.org&style=flat-square&label=translated&color=3050ff&cacheSeconds=86400)](https://translate.codeberg.org/projects/searxng/)

## Setup

To install SearXNG, see the [Installation guide](https://docs.searxng.org/admin/installation.html).

To fine-tune SearXNG, see the [Configuration guide](https://docs.searxng.org/admin/settings/index.html).

Further information on *how-to* can be found [here](https://docs.searxng.org/admin/index.html).

## Connect

If you have questions or want to connect with others in the community:

- [#searxng:matrix.org](https://matrix.to/#/#searxng:matrix.org)

## Contributing

See [CONTRIBUTING](https://github.com/searxng/searxng/blob/master/CONTRIBUTING.rst) for more details.

## License

This project is licensed under the GNU Affero General Public License (AGPL-3.0).
See [LICENSE](https://github.com/searxng/searxng/blob/master/LICENSE) for more details.

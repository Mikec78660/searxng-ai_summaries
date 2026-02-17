.. SPDX-License-Identifier: AGPL-3.0-or-later

.. _metasearch engine: https://en.wikipedia.org/wiki/Metasearch_engine
.. _Installation guide: https://docs.searxng.org/admin/installation.html
.. _Configuration guide: https://docs.searxng.org/admin/settings/index.html
.. _CONTRIBUTING: https://github.com/searxng/searxng/blob/master/CONTRIBUTING.rst
.. _LICENSE: https://github.com/searxng/searxng/blob/master/LICENSE

.. figure:: https://raw.githubusercontent.com/searxng/searxng/master/client/simple/src/brand/searxng.svg
   :target: https://searxng.org
   :alt: SearXNG
   :width: 512px


SearXNG AI Summaries Fork
=========================

This is a **fork of SearXNG** that adds **AI-powered search result summarization**.
This fork allows users to get concise AI-generated summaries of their search results,
helping them quickly understand and digest information from multiple sources without
clicking through each result individually.

The original SearXNG project is available at: https://github.com/searxng/searxng

.. raw:: html

   <video width="100%" controls>
     <source src="https://raw.githubusercontent.com/Mikec78660/searxng-ai_summaries/master/docs/assets/demo.mp4" type="video/mp4">
     Your browser does not support the video tag.
   </video>

Features
--------

This fork extends SearXNG with the following AI summarization capabilities:

- **Automatic Summaries**: Get AI-generated summaries of search results
- **Customizable Prompts**: Configure the system prompt that guides the AI
- **Multiple API Support**: Works with any OpenAI-compatible API endpoint (Ollama, OpenAI, etc.)
- **Flexible Configuration**: Adjust timeout, max tokens, and number of results to summarize

AI Summarization Configuration Options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following options can be configured in the Preferences tab:

1. **Enable AI Summarization** (``ai_summarization_enabled``)
   - Boolean toggle to enable or disable AI summarization
   - Default: ``False`` (disabled)

2. **API Endpoint** (``ai_api_endpoint``)
   - The URL of your AI API endpoint (e.g., ``http://localhost:11434/v1/chat/completions`` for Ollama)
   - Must be an OpenAI-compatible API endpoint

3. **API Key** (``ai_api_key``)
   - Your API key for authentication
   - Can be left empty for local endpoints like Ollama

4. **Model** (``ai_model``)
   - The model ID to use for summarization (e.g., ``gpt-4``, ``llama3``, ``mistral``)

5. **Number of Results to Summarize** (``ai_num_results``)
   - How many search results to include in the summary
   - Default: ``5``

6. **Timeout per Result** (``ai_timeout_per_result``)
   - Timeout in seconds when fetching each result's content
   - Default: ``5`` seconds

7. **Max Tokens** (``ai_max_tokens``)
   - Maximum number of tokens in the generated summary
   - Default: ``500``

8. **System Prompt** (``ai_system_prompt``)
   - Custom prompt that instructs the AI how to summarize
   - Default: ``"You are a helpful assistant that summarizes search results. We are looking for this information {query} Provide a concise summary of the search results in no more than 2-3 paragraphs from these web pages: {results}. Focus on the most relevant information."``


SearXNG is a `metasearch engine`_. Users are neither tracked nor profiled.

.. image:: https://img.shields.io/badge/organization-3050ff?style=flat-square&logo=searxng&logoColor=fff&cacheSeconds=86400
   :target: https://github.com/searxng
   :alt: Organization

.. image:: https://img.shields.io/badge/documentation-3050ff?style=flat-square&logo=readthedocs&logoColor=fff&cacheSeconds=86400
   :target: https://docs.searxng.org
   :alt: Documentation

.. image:: https://img.shields.io/github/license/searxng/searxng?style=flat-square&label=license&color=3050ff&cacheSeconds=86400
   :target: https://github.com/searxng/searxng/blob/master/LICENSE
   :alt: License

.. image:: https://img.shields.io/github/commit-activity/y/searxng/searxng/master?style=flat-square&label=commits&color=3050ff&cacheSeconds=3600
   :target: https://github.com/searxng/searxng/commits/master/
   :alt: Commits

.. image:: https://img.shields.io/weblate/progress/searxng?server=https%3A%2F%2Ftranslate.codeberg.org&style=flat-square&label=translated&color=3050ff&cacheSeconds=86400
   :target: https://translate.codeberg.org/projects/searxng/
   :alt: Translated

Setup
=====

To install SearXNG, see `Installation guide`_.

To fine-tune SearXNG, see `Configuration guide`_.

Further information on *how-to* can be found `here <https://docs.searxng.org/admin/index.html>`_.

Connect
=======

If you have questions or want to connect with others in the community:

- `#searxng:matrix.org <https://matrix.to/#/#searxng:matrix.org>`_

Contributing
============

See CONTRIBUTING_ for more details.

License
=======

This project is licensed under the GNU Affero General Public License (AGPL-3.0).
See LICENSE_ for more details.

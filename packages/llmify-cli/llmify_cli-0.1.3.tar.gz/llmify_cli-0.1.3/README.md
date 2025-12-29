![LLM-ify](Public/assets/llmify.png)

# LLM-ify

LLM-ify generates `llms.txt` and `llms-full.txt` plus full markdown/text captures for single pages or entire websites, so your LLM has clean, readable context.

## Install + Run

```python
pip install llmify-cli
```

```bash
llmify
```

## What is llms.txt?

`llms.txt` is a standardized format for making website content more accessible to Large Language Models (LLMs). It provides:

- `llms.txt`: A concise index of all pages with titles and descriptions
- `llms-full.txt`: Complete content of all pages for comprehensive access

## Features

- Full website or single-page capture
- Text + Markdown output
- LLM-friendly index (`llms.txt`) + full corpus (`llms-full.txt`)
- OpenAI or OpenRouter support
- Interactive terminal UI

## Prerequisites

- Python 3.7+
- OpenAI API key ([Get one here](https://platform.openai.com))
- Crawl4AI setup (see installation)

## Quick Setup (Recommended)

Other launch commands (all open the TUI):

```bash
llm-ify
llmify-cli
```

Run the quickstart script for your OS:

```bash
# Windows (PowerShell)
scripts\quickstart.ps1

# macOS/Linux
./scripts/quickstart.sh
```

This creates a venv, installs deps, runs `crawl4ai-setup`, and launches the TUI.

Every time after this just activate your venv and run 

```bash
python main.py
```

## Manual Setup

1. Clone the repository:

```bash
git clone https://github.com/Chillbruhhh/LLM-ify.git
cd LLM-ify
```

2. Create and activate a virtual environment:

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run the setup command:

```bash
crawl4ai-setup
```

This installs browser dependencies needed for Crawl4AI.

5. Set up your OpenAI API key:

   Option A: Using .env file (recommended)

   ```bash
   cp .env.example .env
   # Edit .env and configure:
   # - Add OPENAI_API_KEY (required)
   ```

   Option B: Using environment variables

   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   ```

   Option C: Using command line arguments
   (See the TUI for input fields)

### OpenRouter (Optional)

LLM-ify can also use OpenRouter. Set the key and choose the provider in the TUI settings:

```bash
OPENROUTER_API_KEY="your-openrouter-api-key"
```

### Ollama (Optional)

LLM-ify can use a local Ollama server. Select `ollama` in the TUI and set the model name (for example `llama3.1:8b`). Ollama runs at `http://localhost:11434/v1` by default.

## Usage (TUI)

Launch the terminal UI:

```bash
python main.py
```

Enter a URL, choose a mode (full website or single page), and run. Settings are saved in `config.json` automatically.

### Model Provider + Model Name

Choose the provider in Settings, then set the model name for that provider:

- OpenAI default: `gpt-4.1-nano`
- OpenRouter default: `openai/gpt-4.1-nano`
- Ollama: set your local model name (for example `llama3.1:8b`)

## Output Format

### llms.txt

```
# https://example.com llms.txt

- [Page Title](https://example.com/page1): Brief description of the page content here
- [Another Page](https://example.com/page2): Another concise description of page content
```

### llms-full.txt

```
# https://example.com llms-full.txt

<|llm-ify-page-1-lllmstxt|>
## Page Title
Full markdown content of the page...

<|llm-ify-page-2-lllmstxt|>
## Another Page
Full markdown content of another page...
```

## Output Locations

Output files are written under `collected-texts/crawl4ai-<domain>/` by default and split into `txt-output` and `md-output` folders. Example:

```
collected-texts/crawl4ai-docs.example.com/txt-output/llms.txt
collected-texts/crawl4ai-docs.example.com/txt-output/llms-full.txt
collected-texts/crawl4ai-docs.example.com/md-output/llms.md
collected-texts/crawl4ai-docs.example.com/md-output/llms-full.md
collected-texts/crawl4ai-docs.example.com/seeds.json
```

## License

PolyForm Noncommercial - see `LICENSE` for details.

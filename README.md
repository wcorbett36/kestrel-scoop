# K-Compiler (Strategic Edition)

**Kestrel Scoop (K-Compiler)** is a CLI-driven pipeline designed to map and index the local repositories of the Artemis decision engineering ecosystem. It crawls structured repositories, extracts documentation incrementally, and uses an Intelligent Synthesizer (powered by Gemini) to "compile" the architecture into a unified, Dataview-compatible Obsidian Wiki.

## 🚀 The Architecture

The pipeline follows a `Source -> Mirror -> Synthesis -> Generation` loop:
1. **The DocCrawler (`src/crawler.py`)**: Traverses paths identified in `config.yaml`, scoping for Markdown documentation updates (`**/*.md`).
2. **The ManifestTracker (`src/manifest.py`)**: Computes SHA-256 mappings of every scraped document against `.kb_manifest.json` ensuring unchanged files bypass network execution completely.
3. **The Synthesizer (`src/synthesizer.py`)**: Uses `litellm` and `Pydantic` to coerce strict structured outputs from the LLM, classifying dense code-chunks into generalized Node descriptions and Strategic Views.
4. **The Obsidian Formatter (`src/obsidian.py`)**: Translates LLM structs into fully inter-linked markdown (MOCs, custom Frontmatter Tags) outputted straight into `./wiki/`.

## ⚙️ How to Configure

All configurations are handled via the `config.yaml` file located in the root repository. By default, it scopes into your local `kestrel-systems`, `artemis_home`, and `trust-systems` directories:

```yaml
output_dir: "./wiki"
llm_model: "gemini-1.5-pro"

projects:
  - name: "artemis_home"
    path: "../../artemis_home"
    focus: "Core steering systems and architecture"
    include: ["README.md", "**/*.md"]
```

> **Note:** Paths are relative from the location of where `src/cli.py` is invoked. It matches expressions intelligently via `pathlib.rglob`.

## 💻 Manual Execution Guide

To kick off your ingestion runs seamlessly:

### 1. Set Up Your Environment Shell
First, configure your API keys by duplicating the example `.env` file!
```bash
cp .env.example .env

# Edit .env and inject your Gemini key:
# GEMINI_API_KEY=AI........
```

### 2. Enter the Python Virtual Environment
We recommend you install dependencies locally to avoid global pollutions:
```bash
# Verify you are in the kestrel-scoop directory
python -m venv .venv

# Activate the venv
source .venv/bin/activate

# Install the dependencies
pip install -r requirements.txt
```

### 3. Run the Build Pipeline!
With the `config.yaml` and `.env` defined, simply invoke standard Typer capabilities:

```bash
# Add current directory to the path 
export PYTHONPATH=$(pwd)

# Run the Build Engine
python src/cli.py build
```

The terminal interface will spool up rich visualizations loading files into your local `.kb_buffer` directory before sending them to the Synthesizer and outputting everything cleanly right here into the `<working_dir>/wiki/` folder structure.

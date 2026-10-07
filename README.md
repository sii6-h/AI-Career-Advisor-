# AI Career Path Advisor

A multi-agent Generative AI system that analyzes a user profile, researches suitable careers, identifies skill gaps, builds a development roadmap, reviews its own output, and produces a final evidence-grounded career report.

## Architecture

The workflow uses six specialized agents: `ProfileAgent`, `CareerResearchAgent`, `SkillGapAgent`, `RoadmapAgent`, `ReviewerAgent`, and `WriterAgent`. `CareerAdvisorOrchestrator` coordinates the sequential workflow and supports a controlled reviewer-driven revision path. Agents use a custom ReAct-style loop and an explicit tool registry.

## Tools and external integrations

- DDGS public web search for current career information.
- Jooble Saudi Arabia API for current job-market evidence.
- Deterministic skill-match scoring and skill-gap prioritization tools.
- PDF semantic RAG over O*NET Career Listings using SentenceTransformers embeddings.

## Reliability and observability

The project records structured execution traces, agent/tool calls, prompt/completion/total tokens, estimated API cost, runtime, and errors. It includes exact repetition detection, stagnation detection, maximum-step protection, per-agent tool-call budgets, retry handling for temporary API failures, custom exceptions, and component tests.

## Repository structure

```text
.
├── README.md
├── pyproject.toml
├── data/
│   └── IP_Career_Listings.pdf
├── notebooks/
│   └── AI_Career_Path_Advisor.ipynb
├── src/career_advisor/
│   ├── agents.py
│   ├── base_agent.py
│   ├── client.py
│   ├── config.py
│   ├── exceptions.py
│   ├── loop_detection.py
│   ├── main.py
│   ├── observability.py
│   ├── orchestrator.py
│   ├── prompts.py
│   ├── rag.py
│   ├── registry.py
│   └── tools.py
└── tests/
    └── test_components.py
```

## Setup with uv

1. Install `uv`.
2. From the repository root, run:

```bash
uv sync
```

3. Set API credentials as environment variables:

```bash
export GEMINI_API_KEY="your_key"
export JOOBLE_API_KEY="your_key"
```

On Windows PowerShell:

```powershell
$env:GEMINI_API_KEY="your_key"
$env:JOOBLE_API_KEY="your_key"
```

4. Run tests:

```bash
uv run pytest
```

## Notebook

The original Google Colab implementation is preserved in `notebooks/AI_Career_Path_Advisor.ipynb`. In Colab, upload `data/IP_Career_Listings.pdf` as `/content/IP_Career_Listings.pdf` and add `GEMINI_API_KEY` and `JOOBLE_API_KEY` to Colab Secrets before running all cells.

## Security

API keys are never hard-coded. The modular package reads credentials from environment variables; the Colab notebook reads them from Colab Secrets with an environment-variable fallback.

## RAG extension

The O*NET PDF is extracted, chunked, embedded with `all-MiniLM-L6-v2`, and searched using semantic similarity. Retrieved passages and page metadata are supplied as grounded context to the career research and final report stages.

## Limitations

Web and job-search results depend on external services and network availability. Estimated token cost is based on the pricing values configured in the project and may differ from actual billing. The O*NET PDF is a career-listing reference and does not replace live labor-market evidence.


Submitted by: Shmookh Almoliafai — academy: @SDAIAAcademy

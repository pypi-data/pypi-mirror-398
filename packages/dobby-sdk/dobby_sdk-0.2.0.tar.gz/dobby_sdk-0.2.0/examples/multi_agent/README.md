# Multi-Agent Example

Demonstrates nested agent pattern with multi-level tool calling.

## Architecture

```
Master Orchestrator Agent
├── tavily_search (web search)
└── research_companies (nested agent)
    └── Inner Agent
        └── tavily_search (web search)
```

## Setup

```bash
export AZURE_OPENAI_API_KEY=...
export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
export AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
export TAVILY_API_KEY=tvly-...
```

## Usage

```bash
cd examples/multi_agent
python jd_analyzer.py
```

## Interactive Chat

Paste a job description to analyze. The system will:
1. Analyze the JD requirements
2. Search for relevant market information
3. Use the nested agent to find matching companies

Commands:
- `quit` - Exit the chat
- `clear` - Reset conversation history

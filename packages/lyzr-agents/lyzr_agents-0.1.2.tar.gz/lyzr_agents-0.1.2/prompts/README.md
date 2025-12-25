# STORM Agent System Prompts

This directory contains system prompts for each Lyzr agent used in the STORM (Synthesis of Topic Outlines through Retrieval and Multi-perspective Question Asking) pipeline.

## Agent Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           STORM Pipeline                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────────┐                                                   │
│  │ 1. PERSONA       │  Generate diverse perspectives                    │
│  │    GENERATOR     │  Input: Topic                                     │
│  └────────┬─────────┘  Output: ["Persona 1", "Persona 2", ...]          │
│           │                                                              │
│           ▼                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐       │
│  │ 2. QUESTION      │  │ 2. QUESTION      │  │ 2. QUESTION      │       │
│  │    GENERATOR     │  │    GENERATOR     │  │    GENERATOR     │  ...  │
│  │    (Persona 1)   │  │    (Persona 2)   │  │    (Persona 3)   │       │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘       │
│           │                     │                     │                  │
│           ▼                     ▼                     ▼                  │
│  ┌──────────────────────────────────────────────────────────────┐       │
│  │                    3. RESEARCH AGENT                          │       │
│  │         Answer all questions (parallel execution)             │       │
│  │         Input: Question → Output: Research Answer             │       │
│  └────────────────────────────┬─────────────────────────────────┘       │
│                               │                                          │
│                               ▼                                          │
│  ┌──────────────────┐                                                   │
│  │ 4. OUTLINE       │  Synthesize research into structure               │
│  │    GENERATOR     │  Input: All research answers                      │
│  └────────┬─────────┘  Output: ["Section 1", "Section 2", ...]          │
│           │                                                              │
│           ▼                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐       │
│  │ 5. SECTION       │  │ 5. SECTION       │  │ 5. SECTION       │       │
│  │    GENERATOR     │  │    GENERATOR     │  │    GENERATOR     │  ...  │
│  │    (Section 1)   │  │    (Section 2)   │  │    (Section 3)   │       │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘       │
│           │                     │                     │                  │
│           └─────────────────────┼─────────────────────┘                  │
│                                 ▼                                        │
│                    ┌──────────────────┐                                 │
│                    │  FINAL ARTICLE   │                                 │
│                    └──────────────────┘                                 │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Prompt Files

| File | Agent | Purpose |
|------|-------|---------|
| `persona_generator_agent.md` | Persona Generator | Creates diverse expert personas for multi-perspective questioning |
| `question_generator_agent.md` | Question Generator | Generates insightful questions from each persona's perspective |
| `research_agent.md` | Research Agent | Provides comprehensive answers to research questions |
| `outline_generator_agent.md` | Outline Generator | Synthesizes research into a coherent article structure |
| `section_generator_agent.md` | Section Generator | Writes individual article sections with proper formatting |

## Setting Up Agents in Lyzr

When creating each agent in the Lyzr platform:

1. **Create a new agent** for each role
2. **Copy the system prompt** from the corresponding `.md` file
3. **Configure RAG** (especially for the Research Agent) with relevant knowledge bases
4. **Note the agent IDs** for use in `StormAgentConfig`

Example configuration:

```python
from src.agents import StormAgent, StormAgentConfig

config = StormAgentConfig(
    persona_generator_agent_id="your-persona-agent-id",
    question_generator_agent_id="your-question-agent-id",
    research_agent_id="your-research-agent-id",
    outline_generator_agent_id="your-outline-agent-id",
    section_generator_agent_id="your-section-agent-id",
)

agent = StormAgent(
    lyzr_api_key="your-api-key",
    user_id="your-user-id",
    config=config,
)
```

## Agent Recommendations

### Persona Generator
- **Model**: Fast model (GPT-3.5 / Claude Haiku)
- **Temperature**: 0.8 (creative diversity)
- **RAG**: Not required

### Question Generator
- **Model**: Fast model (GPT-3.5 / Claude Haiku)
- **Temperature**: 0.7 (varied but focused)
- **RAG**: Not required

### Research Agent
- **Model**: Capable model (GPT-4 / Claude Sonnet)
- **Temperature**: 0.3 (factual accuracy)
- **RAG**: Highly recommended with domain knowledge bases

### Outline Generator
- **Model**: Capable model (GPT-4 / Claude Sonnet)
- **Temperature**: 0.5 (structured creativity)
- **RAG**: Not required

### Section Generator
- **Model**: Capable model (GPT-4 / Claude Sonnet)
- **Temperature**: 0.6 (engaging writing)
- **RAG**: Optional (can reference sources)

## Customization

Each prompt can be customized for specific use cases:

- **Domain-specific language**: Add industry terminology guidelines
- **Tone adjustments**: Modify for academic, journalistic, or casual style
- **Output length**: Adjust word count expectations
- **Format requirements**: Add specific formatting rules

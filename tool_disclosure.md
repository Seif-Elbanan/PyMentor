# Tool Disclosure

**Project:** PyMentor Personalized Python Tutor
**Team:** Seif Mohamed (202301506), Patrick Saweris (202301486)

| Tool, framework, or data | Purpose and architectural role |
|---|---|
| Python 3.9+ | Main implementation language and subject being taught. |
| LangGraph | Required orchestration framework; defines state, nodes, conditional routing, and persistence flow. |
| Pydantic | Validates response and source schemas and constrains structured application data. |
| SQLite | Stores session messages, learner profiles, quiz history, and recurring misconceptions across sessions. |
| Requests | Calls Groq's OpenAI-compatible endpoint and the local Ollama HTTP API. |
| Groq API | Supported optional hosted inference provider; no Groq key was used in the final measured run. |
| Ollama with `qwen3:4b` | Local inference provider used for the final 32-case run, LLM judge, and RAGAS evaluation. |
| Streamlit | Provides the interactive live-demo chat interface and displays grounding sources. |
| RAGAS | Evaluates faithfulness and retrieval quality for baseline-versus-final RAG comparison. |
| Pytest | Runs deterministic tests for retrieval, memory persistence, scope control, and adversarial guardrails. |
| python-docx | Produces the formatted written report and tool-disclosure Word files. |
| Pillow | Renders the professional system-architecture figure included in the report. |
| Synthetic CSAI 106 knowledge notes | Controlled Python curriculum corpus authored for this project from standard introductory concepts; provides known ground truth. |
| Synthetic evaluation conversations | Thirty-two authored cases covering three learner personas, happy paths, edge cases, and adversarial requests. |
| OpenAI Codex | AI coding assistant used to interpret the guideline, scaffold code and documentation, identify security issues, and support testing. All outputs were reviewed by the team, who remain responsible for the design. |
| Course lectures and labs | Guided design choices for prompting, LangGraph, RAG, memory, tool calling, structured outputs, reflection, and evaluation. |

No API key or private credential is included in the repository. AI-generated or synthetic
materials are disclosed here and are not represented as externally collected human data.

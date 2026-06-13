# Oral Exam Guide

Both members must be able to trace one request through every graph node and justify each
design trade-off.

## Core questions

1. **Why LangGraph?**
   It makes shared state, node responsibilities, conditional edges, and stopping behavior
   explicit. That is easier to inspect and test than an opaque agent loop.

2. **What makes the RAG strategy advanced?**
   It improves the naive overlap baseline with inverse-frequency weighting, metadata
   personalization, title coverage, and a reranking stage. Results are measured before and
   after. A dedicated `validate_context` node turns the retrieval confidence score into a
   pass/fail gate for the explainer.

3. **Why 130-word chunks with overlap?**
   Introductory Python sections are short. This size usually keeps one concept intact while
   avoiding large mixed-topic contexts. The overlap protects definitions near boundaries.

4. **How is short-term memory different from long-term memory?**
   Session messages and the pending-quiz state (`quiz_state` table, 1-hour expiry)
   preserve current dialogue and in-progress activities. Student profiles, quiz history,
   and misconceptions persist across sessions and actively affect future routing and
   teaching (see question 6).

5. **How is answer withholding guaranteed?**
   A deterministic pre-model guardrail marks direct-solution requests. The Explainer then
   receives a hint-only instruction. This does not rely solely on the learner-facing prompt.

6. **How does the tutor actually use memory, not just store it?**
   Three concrete loops: (a) the quiz agent grades a pending answer and writes to
   `quiz_attempts` and `misconceptions`; (b) `update_profile_from_quiz_history`
   deterministically recomputes `mastered_topics`/`struggling_topics`/`ability` from
   that history (avg score >= 0.7 mastered, < 0.4 struggling, no LLM involved); (c) the
   explainer checks the misconception log for the current topic and opens with
   "Previously you had difficulty with X" if one is found.

7. **What happens on low retrieval confidence?**
   `validate_context` sets `context_sufficient = False`, and the Explainer refuses to
   claim grounded knowledge, asking for an indexed Python topic instead of hallucinating.

8. **How do you stop prompt injection?**
   Pattern detection, input delimiters, fixed graph capabilities, no arbitrary tool access,
   scoped retrieval, output leakage checks, and secret redaction.

9. **Why SQLite?**
   It is persistent, transactional, inspectable, and appropriate for a small capstone. A
   production system could move the same logical schema to PostgreSQL.

10. **How do Groq and Ollama coexist?**
    `LLMClient` exposes one interface. `auto` selects Groq when a key exists and otherwise
    uses Ollama. Graph code does not know which provider executes a request.

11. **What metric matters most for a tutor?**
    Learning improvement, measured by pre/post quiz delta, is more meaningful than fluency.
    It is paired with groundedness and pedagogical compliance so improvement is trustworthy.

12. **How does the supervisor know a message is answering a quiz vs. asking something new?**
    It checks for pending quiz state from memory, then applies a lexical heuristic: replies
    starting with question words ("what is", "explain", "why", etc.) are treated as new
    questions, not quiz answers. This is a known, documented limitation, not a hidden one —
    be ready to discuss its edge cases.

## Live-demo sequence

1. Ask for a simple explanation and open its grounding sources.
2. Ask a follow-up in the same session to show context continuity.
3. Request a quiz, then answer it incorrectly on purpose, and show the resulting
   `quiz_attempts`/`misconceptions` rows and the updated profile.
4. Ask about the same topic again and show the explainer referencing the misconception
   from step 3.
5. Start a new session with the same student to show persistent profile memory.
6. Request a full homework solution and demonstrate hint-first withholding.
7. Submit a prompt-injection attempt.
8. Ask an unrelated question to demonstrate scope enforcement.
9. Request a progress summary.
10. Show the evaluation JSON and explain one system improvement driven by a failed case.

## Ownership suggestion

- **Seif:** LangGraph flow, agents, provider adapter, and live demo.
- **Patrick:** RAG, memory schema, guardrails, evaluation, and reported metrics.

This is only a presentation split. Both members must understand every component because the
oral grade is individual.

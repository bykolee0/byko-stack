# Question policy: investigate, propose, choose

Use the user's time only for decisions that cannot be recovered from code, docs, or existing artifacts.

## Procedure

1. Investigate first.
   - Search code, tests, docs, and existing work manifests.
   - Use isolated exploration when current Codex policy permits it and the scope is broad.

2. If investigation gives one answer, do not ask.
   - Adopt it and record `from-code` or `from-docs` with file:line evidence.
   - Report it as "confirmed facts", not as a question.

3. If several answers remain, prepare 2-3 options.
   - Include code evidence, tradeoffs, and a recommendation.

4. Ask the user only when the decision affects one of these:
   - product/customer behavior
   - business policy
   - a new or conflicting project convention
   - architecture direction or new dependency
   - hard-to-reverse side effects such as schema, public API, migration, or data deletion
   - meaningful cost or security impact

5. Otherwise adopt the recommended option.
   - Record it as `assumed` with basis and alternatives.
   - Keep the ambiguity gate: `assumed <= 2`. If more assumptions accumulate, pause and ask for grouped confirmation.

## Question shape

- Do not ask open-ended "what should I do?" questions.
- Ask at most three concise questions at once.
- For each question, provide options with a recommendation and one-line tradeoff.
- If the user says "later", record `[TBD]` and continue only if the TBD does not block implementation direction.

## Self-check

- Could code or docs answer this? If yes, search instead of asking.
- Am I asking without options? If yes, investigate enough to make options.
- Does this fail the user-decision conditions above? If yes, assume with evidence and proceed.
- Does it pass those conditions? If yes, stop and ask.

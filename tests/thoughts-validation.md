# Thoughts revision validation — 2026-09-13

Scope: validate the revised instructions and exercise their council stages and
activation boundaries. These are behavioral smoke tests, not a comparative
benchmark or a claim of improved accuracy over the previous version.

## Structural validation

The bundled skill-creator `quick_validate.py` accepted the revised skill. Its
PyYAML dependency was installed into the task's temporary work directory; it is
not a dependency of Thoughts or the installer. The Cursor rule delegates mode
selection and procedure to the skill, preserving one authoritative procedure.
The skill is self-contained, so the installer's three-file mapping is unchanged.

A temporary Git repository and temporary home were used to install the actual
baseline skill/rule, commit and install the council revision, verify all three
destination contents, and roll back to the baseline. Installation verification
passed both after the upgrade and after rollback. No live copies were used for
this rollback test.

## Council execution

The chair used the full council task packet from `thoughts-evaluation.md`.
Three separate participants received the complete skill and the same raw packet
with no inherited conversation history or chair conclusion. Requested model
configurations were `gpt-6-astra`, `gpt-5.6-sol`, and `gpt-5.6-terra`, each at high
reasoning effort. The host accepted all three configurations; returned tool
metadata did not independently echo model identities. The evaluation therefore
records requested models, not a separate attestation of runtime identity.

All three participants returned independent assessments, cross-reviews, and
final checks. Participant identifiers were `participant_1`, `participant_2`, and
`participant_3`. Cross-review positions were shuffled as A = participant_3,
B = participant_1, C = participant_2. Author/model labels were omitted from the
review packet; participants could still recognize their own text.

Observed outcomes:

- All independent assessments withheld a global-rollout recommendation under
  the stated restore prerequisite and identified that CI and backup creation do
  not establish restoration.
- Position A overstated E3 as establishing that the restoration events did not
  occur, although the record only said no such events were recorded.
- All three cross-reviewers identified that overstatement. The chair accepted
  the finding and changed the synthesis to say the prerequisite is unestablished
  on the supplied record. Actual recoverability remained unresolved.
- All three final reviewers found no substantive defect in the corrected
  conclusion. They requested completion of review metadata; the final receipt
  was updated with participant identifiers, requested models, and limitations.
- The recommendation remained conditional on the original release criterion;
  no claim of inevitable release harm, recovery failure, or consensus-as-proof
  was added.

This is one observed error caught in cross-review. It does not establish that a
single-model review would have missed the error or quantify a diversity benefit.
The tool-history work products are the execution record; no hidden reasoning
transcript or pass self-grades were used as evidence.

## Additional behavior probes

A fresh evaluator context read the revised skill without prior conclusions or
the expected-outcomes section. It answered six separate probes in one run:

1. A quoted trigger was explained without starting a council.
2. "Quick take, no council" selected lighter review despite "Thoughts?".
3. An unrefuted sorting-performance claim was treated as unsupported rather than
   true or disproven; the answer called for defined comparisons and evidence.
4. Contradictory eligibility records were recognized as incompatible without
   inventing which record was wrong.
5. Identity remained foundational while particular applications remained open
   to correction.
6. A full review with delegation explicitly prohibited by the fixture disclosed
   single-model fallback before its answer and in the receipt, without invented
   participants. It distinguished unverified recovery from recovery failure.

The evaluator reported no material instruction ambiguity. Each response matched
the applicable human-review criteria. These probes shared one fresh evaluator
context; they were not six independently reset sessions. The fallback restriction
was imposed by the test harness, not an observed production outage.

## Limits and further evaluation

The original loop and a same-model council have not been run against this same
packet. Participant-loss recovery, limited concurrency, actual host outages, and
Cursor orchestration have not been exercised. All source evidence in the council
fixture was supplied locally; no empirical web-retrieval assessment was performed.

Use the remaining fixtures and comparable baseline runs for subsequent evaluation.
Judge evidence, inference, correction, usefulness, and added effort; do not infer
improvement from a completed receipt, model count, or agreement alone.

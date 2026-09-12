# Policy Proof Demo Script

## 1. Answered
Question: What is the minimum attendance required for a theory course End Semester Examination?
Expected: ANSWERS, 75%, citation `academic_regulations.md#1.1`.

## 2. Silent
Question: Can I bring a pet into my hostel room?
Expected: SILENT / NOT COVERED. The system must not invent a pet policy.

## 3. Contradiction
Question: Is the laboratory attendance rule absolute, or can the committee waive it?
Expected: CONTRADICTION. Show `academic_regulations.md#1.4` against `academic_regulations.md#3.2`.

## 4. Evaluation
Run:
`python scripts/evaluate.py`

Show the measured result. Never claim 100% unless the script actually reports it.

## 5. Closing pitch
"Policy Proof does not optimize for sounding confident. It optimizes for being checkable: every supported answer has evidence, unsupported questions are rejected, and conflicting rules are surfaced instead of silently reconciled."

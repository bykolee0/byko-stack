# Fresh-eyes review checklist

Review starts from the problem definition, not from whether the spec was followed.

## Problem fit

- Does the artifact solve the original problem as stated in the manifest?
- Did the solution narrow, reinterpret, or over-expand the problem?
- Are important user/business outcomes missing even if the written ACs pass?

## Codebase fit

- Inspect nearby code before judging style or architecture.
- Does the solution follow existing module boundaries, naming, error handling, tests, and data flow?
- Did it introduce a new pattern where an existing local pattern would fit?

## Implementation integrity

- Is the implementation a durable solution rather than a narrow patch for the happy path?
- Are tests behavior-based rather than implementation mirrors?
- Are edge cases, failure paths, rollback, and operational impact handled with the same seriousness as the main path?
- Is anything hard-coded, special-cased, or hidden behind broad assertions?

## Design quality

- Is the complexity proportionate to the problem?
- Are extension points placed where the codebase already expects variation?
- Does the implementation preserve future maintainability without speculative abstractions?

## Verdict

- `SOUND`: solves the right problem with codebase-appropriate quality.
- `CONCERNS`: direction is basically right, but material issues should be addressed.
- `RETHINK`: the artifact appears to solve the wrong problem, use the wrong approach, or needs redesign before continuing.

Every CONCERNS/RETHINK item needs concrete artifact or code evidence.

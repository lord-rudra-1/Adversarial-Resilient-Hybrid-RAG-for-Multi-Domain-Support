# DevPlatform Proctoring — False Positive Resolution Guide

## Overview

DevPlatform's proctoring system uses browser-level monitoring to detect potential cheating during assessments. However, the system may produce false positives in certain scenarios.

## Common False Positive Triggers

| Action | Flagged? | Notes |
|---|---|---|
| Switching to a different browser tab | Yes | Always flagged, even if the test instructions permit it |
| Using an external monitor | Sometimes | Depends on browser permissions |
| Screen sharing with a video call | Yes | The proctor interprets this as tab switching |
| Using assistive technology | Sometimes | Screen readers may trigger focus-loss events |
| Browser auto-update notifications | Yes | System-level popups cause focus loss |

## What Candidates Should Do

If falsely flagged:

1. Take a screenshot of the proctoring alert immediately
2. Note the exact time and what you were doing
3. Contact the **company that sent you the test** (not DevPlatform directly)
4. The hiring company can review the proctoring log and dismiss false flags

## What Hiring Companies Should Do

1. Navigate to Tests > [Test Name] > Candidates
2. Click on the candidate's name to view their attempt
3. Go to the "Proctoring" tab
4. Review flagged events with timestamps
5. Click "Dismiss" on any false positive events
6. Note: Dismissed events are still visible but marked as "Reviewed — No Action"

## Automatic Score Reduction

By default, proctored tests apply a **10% score penalty per flag**. This can be disabled in Test Settings > Proctoring > Score Adjustment.

## Important

- DevPlatform cannot modify a candidate's score after submission
- Only the hiring company has access to proctoring data
- Candidates cannot request re-tests through DevPlatform — this must come from the hiring company
- Proctoring data is retained for 12 months after test completion

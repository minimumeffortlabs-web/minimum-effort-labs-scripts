# Fictional timecard sample
Five entirely fictional shifts and five access rows; no actual employees.
DEMO001 and DEMO002 match the inclusive early/late boundaries. DEMO003 has only
a denied entry, so requires review. DEMO004 has an invalid timestamp. DEMO005
works overnight and matches. One malformed access timestamp is counted separately.
From the episode directory:
`python reconcile_timecards.py sample/timecards.csv sample/door_access.csv --output discrepancies.csv`.
Expect 5 checked, 3 matched, 2 flagged; 1 invalid timecard and 1 invalid access row.
Compare with expected_discrepancies.csv. These are data-quality review flags,
never proof of absence, misconduct or invented interns. The video uses 500 shifts.

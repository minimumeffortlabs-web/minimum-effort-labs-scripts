# Minimum Effort Labs

**Maximum results. Minimum effort.**

Useful Python, unreasonable corporate assignments. These independent command-line
lessons accompany MEL's animated workplace comedy and work without the videos.

| Episode | Lesson | Script and setup |
| --- | --- | --- |
| 001 — The Sentient Toaster | [Merge PDFs](episodes/001-sentient-toaster/LESSON.md) | [Package](episodes/001-sentient-toaster/) |
| 002 — The Invisible Interns | [Reconcile timecards](episodes/002-invisible-interns/LESSON.md) | [Package](episodes/002-invisible-interns/) |
| 003 — The Weather Machine | [Weather report](episodes/003-weather-machine/LESSON.md) | [Package](episodes/003-weather-machine/) |
| 004 — The Truth Serum | [Paired survey changes](episodes/004-truth-serum/LESSON.md) | [Package](episodes/004-truth-serum/) |
| 005 — The Time Machine | [Expense anomaly detection](episodes/005-time-machine/LESSON.md) | [Package](episodes/005-time-machine/) |
| 006 — The Dream Recorder | [Text frequency analysis](episodes/006-dream-recorder/LESSON.md) | [Package](episodes/006-dream-recorder/) |
| 007 — The Robot Performance Reviews | [Word document generation](episodes/007-robot-performance-reviews/LESSON.md) | [Package](episodes/007-robot-performance-reviews/) |

## Download and run

Download the repository using GitHub's **Code > Download ZIP**, then extract it,
or clone `https://github.com/minimumeffortlabs-web/minimum-effort-labs-scripts.git`.
For one episode, keep its entire folder (including sample and tests), not just
the .py file. GitHub's Raw/Download button saves individual files; preserve the
relative folder layout when doing this manually. A whole ZIP is easier for PDFs.

Install Python from python.org with the Windows PATH option. Open a terminal in
the selected episode folder. Each README provides the exact environment,
installation and sample command. Python 3.10+ is required; verification here is
on CPython 3.10.6 on Windows. No other Python/platform combination is claimed tested.

```powershell
python --version
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m unittest discover -s tests -v
```

On macOS/Linux substitute `.venv/bin/python`. Each episode's tests and sample
run offline after dependency installation. Use new output filenames on repeats.
No Remotion, voices, GPU, GUI or private records are required.

## Licensing and status

Code licensing awaits the owner's decision; see [LICENSING.md](LICENSING.md).
No verified YouTube episode URL has been supplied. Episode 001 passed eight
unittest checks on Windows with CPython 3.10.6 and pypdf 6.21.1, including
the documented three-PDF sample and input-preservation checks.

Episodes 002 and 003 passed 15 and 23 unittest checks respectively, including
the documented offline samples. Episode 003 uses recorded Open-Meteo data;
see its [sample provenance and attribution](episodes/003-weather-machine/sample/README.md).

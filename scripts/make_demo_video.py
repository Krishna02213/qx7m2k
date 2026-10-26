#!/usr/bin/env python3
"""Render a concise narrated product and technical-review demo."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work" / "video" / "render"
OUTPUT = ROOT / "outputs" / "windsight-demo.mp4"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
TECH = (ROOT / "work/video/technical-slides.html").as_uri()

SCENES = [
    ("customer-overview", "http://127.0.0.1:8000/#top", """Welcome to WindSight, a pilot decision-support portal for a United Kingdom energy utility. Every morning, the trading desk must decide how much conventional power to procure before tomorrow's wind is known. WindSight recreates exactly what the desk knew at gate closure, then turns historical forecast error into a clear procurement-risk signal. The product is intentionally focused on national wind data from Elexon, using January 2026 as the evaluation period."""),
    ("decision", "http://127.0.0.1:8000/#decision", """The trader starts by choosing a delivery day and the applicable day-ahead cutoff. The default is nine fifty in London on the previous day. The snapshot clearly shows the latest forecast publication that was eligible at that moment. Any forecast published later is excluded. This point-in-time rule is essential: using a later revision would make historical accuracy look better than the information genuinely available when the purchase decision was made."""),
    ("performance", "http://127.0.0.1:8000/#performance", """The delivery profile compares forecast and observed wind for every hour. The headline cards show expected energy, observed energy, mean bias, and the January P ninety wind-shortfall benchmark. Positive forecast-minus-actual error means wind was overforecast, creating potential additional procurement need. The scorecard adds mean absolute error, root mean square error, volume-weighted error, and the frequency of overforecast intervals. The shortfall number is descriptive pilot evidence, not an automatic reserve instruction."""),
    ("method", "http://127.0.0.1:8000/#methodology", """The method is deliberately transparent. First, freeze the clock at the day-ahead cutoff. Second, select the newest eligible WINDFOR publication for every delivery hour. Third, align actual outturn by averaging the two FUELHH half-hours within that hour. Finally, quantify downside as the positive difference between forecast and actual. This gives the client an auditable answer to three questions: what did we know, how wrong was it, and where was the procurement risk?"""),
    ("architecture", f"{TECH}#architecture", """For the technical review, the system follows one simple path. A reproducible ingestion script downloads Elexon FUELHH and WINDFOR records, including December publications needed for the first January delivery day. FastAPI owns all forecast selection, time alignment, and analytical definitions. React renders the decision experience but does not duplicate business logic. A multi-stage Dockerfile builds the frontend and serves the complete application as one deployable service."""),
    ("algorithm", f"{TECH}#algorithm", """The core algorithm is point-in-time safe. For a delivery day, the backend constructs a timezone-aware cutoff on D minus one. It filters to publications at or before that timestamp and selects the maximum eligible publish time for each target. The actual hourly power is the mean of the two half-hour readings, not their sum. Error is forecast minus actual, so positive error directly represents wind overforecast and possible power shortfall."""),
    ("quality", f"{TECH}#quality", """Tests focus on the business failures that matter. They prove later publications are rejected, the latest eligible run is selected, half-hour power values are averaged correctly, and shortfall signs are not reversed. The full month contains seven hundred and forty four matched hourly observations. Continuous integration installs the backend, runs the Python tests, compiles the React production bundle, and builds the final Docker image. The same commit is available in the public repository."""),
    ("handover", f"{TECH}#handover", """This pilot stays inside the requested boundary: national wind generation, Elexon data, and January 2026 decisions. It does not pretend to optimize the entire portfolio. A production phase would add scheduled ingestion, persistent storage, authentication, monitoring, data-quality alerts, and the client's agreed market deadline and risk appetite. Demand, prices, plant constraints, and trade execution would be separate integrations. The result today is a focused, reproducible foundation that makes forecast uncertainty visible and actionable. Thank you."""),
]


def run(*args: str) -> None:
    subprocess.run(args, check=True)


def main() -> None:
    WORK.mkdir(parents=True, exist_ok=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    clips = []
    for index, (name, url, narration) in enumerate(SCENES, 1):
        image = WORK / f"{index:02d}-{name}.png"
        text = WORK / f"{index:02d}-{name}.txt"
        audio = WORK / f"{index:02d}-{name}.aiff"
        clip = WORK / f"{index:02d}-{name}.mp4"
        text.write_text(narration)
        run(CHROME, "--headless", "--disable-gpu", "--hide-scrollbars", "--window-size=1440,900", "--force-device-scale-factor=1", "--virtual-time-budget=3000", f"--screenshot={image}", url)
        run("say", "-v", "Samantha", "-r", "178", "-f", str(text), "-o", str(audio))
        run("ffmpeg", "-y", "-loop", "1", "-i", str(image), "-i", str(audio), "-c:v", "libx264", "-tune", "stillimage", "-preset", "veryfast", "-c:a", "aac", "-b:a", "160k", "-pix_fmt", "yuv420p", "-r", "30", "-shortest", str(clip))
        clips.append(clip)
    concat = WORK / "clips.txt"
    concat.write_text("".join(f"file '{clip}'\n" for clip in clips))
    run("ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", str(OUTPUT))
    print(OUTPUT)


if __name__ == "__main__":
    main()

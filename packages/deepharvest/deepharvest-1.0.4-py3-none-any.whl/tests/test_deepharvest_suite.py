#!/usr/bin/env python
import subprocess
import time
import json
import shutil
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional


# --------- Test Case Definition --------- #

@dataclass
class HarvestTestCase:
    name: str
    url: str
    depth: int = 1
    use_js: bool = False
    max_urls: int = 50
    expected_min_files: int = 5
    timeout_seconds: int = 600
    notes: str = ""


# --------- Test Suite Configuration --------- #

OUTPUT_ROOT = Path("deepharvest_test_output")
REPORT_FILE = Path("deepharvest_test_report.json")


def get_test_cases() -> List[HarvestTestCase]:
    """
    Define a mix of static + JS-heavy sites.
    You can freely change URLs if some are blocked in your network.
    """
    return [
        # --- Static / simple sites ---
        HarvestTestCase(
            name="static_example",
            url="https://example.com",
            depth=1,
            use_js=False,
            max_urls=10,
            expected_min_files=2,
            notes="Very basic static site; sanity check.",
        ),
        HarvestTestCase(
            name="static_wikipedia",
            url="https://en.wikipedia.org/wiki/Web_crawler",
            depth=1,
            use_js=False,
            max_urls=30,
            expected_min_files=5,
            notes="Large static-ish article page with lots of links.",
        ),

        # --- Slightly more complex / content heavy ---
        HarvestTestCase(
            name="static_news",
            url="https://www.bbc.com/news",
            depth=1,
            use_js=False,
            max_urls=40,
            expected_min_files=5,
            notes="News homepage; good for link graph + HTML extraction.",
        ),

        # --- Dynamic / JS-heavy (SPA-style or JS injected) ---
        HarvestTestCase(
            name="dynamic_js_quotes",
            url="https://quotes.toscrape.com/js/",
            depth=1,
            use_js=True,
            max_urls=20,
            expected_min_files=5,
            notes="Classic test site where content is loaded via JavaScript.",
        ),
        HarvestTestCase(
            name="dynamic_hackernews_front",
            url="https://news.ycombinator.com/",
            depth=1,
            use_js=True,
            max_urls=40,
            expected_min_files=5,
            notes="Heavier interaction, good JS+HTML combo test.",
        ),

        # --- Larger-ish site with JS enabled ---
        HarvestTestCase(
            name="mixed_docs_mozilla",
            url="https://developer.mozilla.org/en-US/docs/Web",
            depth=1,
            use_js=True,
            max_urls=50,
            expected_min_files=10,
            notes="Docs site; tests multilingual-ish + lots of content.",
        ),
    ]


# --------- Helpers --------- #

def slugify(text: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in text)


def run_single_test(case: HarvestTestCase) -> Dict[str, Any]:
    test_slug = slugify(case.name)
    output_dir = OUTPUT_ROOT / test_slug

    # Clean previous output for this test
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "deepharvest",
        "crawl",
        case.url,
        "--depth",
        str(case.depth),
        "--max-urls",
        str(case.max_urls),
        "--output",
        str(output_dir),
    ]

    if case.use_js:
        cmd.append("--js")
    else:
        cmd.append("--no-js")

    print(f"\n=== Running test: {case.name} ===")
    print(f"URL: {case.url}")
    print(f"Command: {' '.join(cmd)}")

    start_time = time.perf_counter()
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=case.timeout_seconds,
            text=True,
        )
        end_time = time.perf_counter()
        duration = end_time - start_time

        # Count extracted files
        file_count = 0
        sizes = []
        for p in output_dir.rglob("*"):
            if p.is_file():
                file_count += 1
                try:
                    sizes.append(p.stat().st_size)
                except OSError:
                    pass

        total_size = sum(sizes)
        non_empty_files = sum(1 for s in sizes if s > 0)

        success = (
            proc.returncode == 0
            and file_count >= case.expected_min_files
            and non_empty_files > 0
        )

        # Basic rating for this test
        # 10/10 = passed + good file count, else scaled down
        if success:
            ratio = min(1.0, file_count / max(case.expected_min_files, 1))
            score = round(6 + 4 * ratio, 1)  # between 6 and 10
        else:
            score = 3.0 if proc.returncode == 0 else 1.0

        print(f"Exit code: {proc.returncode}")
        print(f"Duration: {duration:.2f}s")
        print(f"Files: {file_count} (non-empty: {non_empty_files})")
        print(f"Total size: {total_size / 1024:.1f} KB")
        print(f"SUCCESS: {success} | Score: {score}/10")

        # Capture only last part of logs to avoid huge output
        stdout_tail = "\n".join(proc.stdout.splitlines()[-30:])
        stderr_tail = "\n".join(proc.stderr.splitlines()[-30:])

        return {
            "case": asdict(case),
            "success": success,
            "score": score,
            "duration_seconds": duration,
            "exit_code": proc.returncode,
            "file_count": file_count,
            "non_empty_files": non_empty_files,
            "total_bytes": total_size,
            "stdout_tail": stdout_tail,
            "stderr_tail": stderr_tail,
            "output_dir": str(output_dir),
        }

    except subprocess.TimeoutExpired as e:
        end_time = time.perf_counter()
        duration = end_time - start_time
        print(f"TIMEOUT after {duration:.2f}s")
        return {
            "case": asdict(case),
            "success": False,
            "score": 1.0,
            "duration_seconds": duration,
            "exit_code": None,
            "file_count": 0,
            "non_empty_files": 0,
            "total_bytes": 0,
            "stdout_tail": "",
            "stderr_tail": f"TimeoutExpired: {e}",
            "output_dir": str(output_dir),
        }


def summarize_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    total_score = sum(r["score"] for r in results)
    max_score = 10.0 * len(results)
    avg_score = total_score / len(results) if results else 0.0

    successes = sum(1 for r in results if r["success"])
    failures = len(results) - successes

    summary = {
        "total_tests": len(results),
        "successes": successes,
        "failures": failures,
        "average_score": round(avg_score, 2),
        "total_score": round(total_score, 2),
        "max_score": round(max_score, 2),
    }

    return summary


def print_summary(summary: Dict[str, Any], results: List[Dict[str, Any]]):
    print("\n" + "=" * 60)
    print("DeepHarvest Automated Test Suite — Summary")
    print("=" * 60)
    print(f"Total tests  : {summary['total_tests']}")
    print(f"Successes    : {summary['successes']}")
    print(f"Failures     : {summary['failures']}")
    print(f"Avg score    : {summary['average_score']}/10")
    print(f"Total score  : {summary['total_score']} / {summary['max_score']}")
    print("-" * 60)

    print(f"{'Test':25} {'JS':3} {'OK':3} {'Score':7} {'Files':7} {'Time(s)':7}")
    print("-" * 60)
    for r in results:
        case = r["case"]
        name = case["name"][:25]
        js_flag = "Y" if case["use_js"] else "N"
        ok_flag = "Y" if r["success"] else "N"
        score = f"{r['score']:.1f}"
        files = str(r["file_count"])
        dur = f"{r['duration_seconds']:.1f}"
        print(f"{name:25} {js_flag:3} {ok_flag:3} {score:7} {files:7} {dur:7}")
    print("-" * 60)
    print(f"Detailed JSON report written to: {REPORT_FILE}")


def save_report(summary: Dict[str, Any], results: List[Dict[str, Any]]):
    report = {
        "summary": summary,
        "results": results,
    }
    with REPORT_FILE.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)


# --------- Main Entry --------- #

def main():
    print("DeepHarvest automated test suite starting...")
    print(f"Output directory: {OUTPUT_ROOT.resolve()}")

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    cases = get_test_cases()
    all_results: List[Dict[str, Any]] = []

    for case in cases:
        result = run_single_test(case)
        all_results.append(result)

    summary = summarize_results(all_results)
    save_report(summary, all_results)
    print_summary(summary, all_results)


if __name__ == "__main__":
    main()

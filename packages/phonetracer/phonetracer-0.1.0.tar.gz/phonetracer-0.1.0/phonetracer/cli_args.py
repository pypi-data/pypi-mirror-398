import argparse
from pathlib import Path
from phonetracer.core import analyze_number, scan_text, export_json, save_results_always

def run():
    parser = argparse.ArgumentParser(
        description="PhoneTracer - Argument Mode"
    )
    parser.add_argument("-n", "--number", help="Analyze a single number")
    parser.add_argument("-f", "--file", help="Scan a file for numbers")
    parser.add_argument("--test", action="store_true", help="Run tests")

    args = parser.parse_args()
    results = []

    if args.test:
        tests = ["+1 415 555 2671", "+91 9513717169", "12345"]
        for t in tests:
            print(t, analyze_number(t))
        return

    if args.number:
        r = analyze_number(args.number)
        if r:
            results.append(r)

    if args.file:
        text = Path(args.file).read_text(encoding="utf-8")
        results.extend(scan_text(text))

    if results:
        filename = save_results_always(results, "cli_args")
        print(f"Results saved to {filename}")
    else:
        print("No valid numbers found")


from phonetracer.core import (
    analyze_number,
    scan_text,
    format_output,
    save_results_always,
    ascii_logo,
)

from pathlib import Path

def run():
    ascii_logo()
    print("\nPhoneTracer CLI Menu")
    print("1. Analyze single number")
    print("2. Scan file")
    print("3. Exit")

    choice = input("Select option: ").strip()

    results = []

    if choice == "1":
        num = input("Enter phone number: ")
        r = analyze_number(num)
        if r:
            results.append(r)
            print(format_output(r))

    elif choice == "2":
        file = input("Enter file path: ")
        text = Path(file).read_text(encoding="utf-8")
        results = scan_text(text)

    elif choice == "3":
        return

    else:
        print("Invalid option")
        return

    if results:
        filename = save_results_always(results, "cli_menu")
        print(format_output(results[0]))
        print(f"\nSaved to file: {filename}")


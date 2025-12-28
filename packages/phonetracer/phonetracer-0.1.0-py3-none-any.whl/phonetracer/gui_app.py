import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from phonetracer.core import analyze_number, format_output, save_results_always

def run():
    root = tk.Tk()
    root.title("PhoneTracer GUI")
    root.geometry("720x520")
    root.resizable(False, False)

    # Title
    ttk.Label(
        root,
        text="PhoneTracer v2.3 ⚡️",
        font=("Segoe UI", 18, "bold")
    ).pack(pady=10)

    # Input frame
    input_frame = ttk.LabelFrame(root, text="Phone Number Input")
    input_frame.pack(fill="x", padx=20, pady=10)

    ttk.Label(input_frame, text="Enter phone number:").pack(anchor="w", padx=10)
    entry = ttk.Entry(input_frame, font=("Segoe UI", 11))
    entry.pack(fill="x", padx=10, pady=5)

    # Button frame
    button_frame = ttk.Frame(root)
    button_frame.pack(pady=10)

    # Output area
    output = scrolledtext.ScrolledText(
        root,
        height=14,
        font=("Consolas", 10)
    )
    output.pack(fill="both", expand=True, padx=20, pady=10)

    # Button actions
    def analyze():
        output.delete("1.0", tk.END)
        number = entry.get().strip()

        if not number:
            messagebox.showwarning("Input Required", "Please enter a phone number.")
            return

        result = analyze_number(number)
        if not result:
            messagebox.showerror("Invalid Number", "Unable to parse the phone number.")
            return

        # ALWAYS SAVE
        filename = save_results_always([result], "gui")

        output.insert(tk.END, format_output(result))
        output.insert(tk.END, f"\n\nSaved to file:\n{filename}")

    def clear():
        entry.delete(0, tk.END)
        output.delete("1.0", tk.END)

    def exit_app():
        root.destroy()

    # Buttons (VERY IMPORTANT FIX)
    ttk.Button(button_frame, text="Analyze", command=analyze).grid(row=0, column=0, padx=10)
    ttk.Button(button_frame, text="Clear", command=clear).grid(row=0, column=1, padx=10)
    ttk.Button(button_frame, text="Exit", command=exit_app).grid(row=0, column=2, padx=10)

    root.mainloop()

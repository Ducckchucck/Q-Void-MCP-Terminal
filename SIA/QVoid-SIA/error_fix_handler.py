# error_fix_handler.py

import os
import re
from modules.real_gemini import generate_response

def get_error_input_gui():
    import tkinter as tk
    from tkinter import simpledialog

    root = tk.Tk()
    root.withdraw()  # Hide the main window

    user_input = simpledialog.askstring(
        title="SIA Python Error Fixer",
        prompt="Paste the full error message or describe the problem below:"
    )

    root.destroy()
    return user_input

def get_error_input():
    print("\n🔧 Paste your Python error traceback or describe the issue:")
    return input("🪵 >> ").strip()

async def call_gemini(error_text):
    prompt = f"""
You're a senior Python developer and code fixer. A user gave you this traceback or bug description:

\"\"\"{error_text}\"\"\"

You must:
1. Explain the root cause clearly.
2. Suggest a precise fix.
3. If code needs fixing, show the corrected Python snippet inside triple backticks like ```python ... ```.
"""
    return await generate_response(prompt)

def extract_code(response_text):
    match = re.search(r"```python(.*?)```", response_text, re.DOTALL)
    return match.group(1).strip() if match else None

def offer_fix_application(fixed_code):
    decision = input("\n💾 Do you want to apply this fix to a file? (yes/no): ").strip().lower()
    if decision == "yes":
        path = input("📄 Enter full file path to overwrite: ").strip()
        if not os.path.isfile(path):
            print("❌ That file doesn’t exist.")
            return
        try:
            with open(path, "w") as f:
                f.write(fixed_code)
            print("✅ Fix successfully written to file.")
        except Exception as e:
            print(f"⚠️ Failed to write file: {e}")
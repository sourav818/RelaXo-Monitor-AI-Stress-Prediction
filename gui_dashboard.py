import tkinter as tk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os

# PATH
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "data.csv")

root = tk.Tk()
root.title("Stress Monitoring Dashboard")
root.geometry("700x650")

# LABELS
bpm_label = tk.Label(root, text="BPM: --", font=("Arial", 14))
bpm_label.pack()

temp_label = tk.Label(root, text="Temp: --", font=("Arial", 14))
temp_label.pack()

stress_label = tk.Label(root, text="Stress: --", font=("Arial", 16))
stress_label.pack()

movement_label = tk.Label(root, text="Movement: --", font=("Arial", 14))
movement_label.pack()

voice_label = tk.Label(root, text="Voice: --", font=("Arial", 14))
voice_label.pack()

# ✅ ADDED ONLY THIS
suggestion_label = tk.Label(root, text="AI Suggestion: --",
                            font=("Arial", 12),
                            wraplength=600)
suggestion_label.pack()

# GRAPH
fig, ax = plt.subplots()
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack()

def update():
    try:
        if not os.path.exists(CSV_PATH):
            root.after(2000, update)
            return

        df = pd.read_csv(CSV_PATH)

        if not df.empty:

            # ✅ Ensure columns exist
            for col in ['BPM','Temp','Stress',
                        'Movement','Voice','Suggestion']:

                if col not in df.columns:
                    df[col] = "--"

            # ✅ Convert numeric
            df['BPM'] = pd.to_numeric(df['BPM'], errors='coerce')
            df['Temp'] = pd.to_numeric(df['Temp'], errors='coerce')

            # ✅ Filter valid rows
            df = df[(df['BPM'] > 0) & (df['Temp'] > 0)]

            if df.empty:
                root.after(2000, update)
                return

            latest = df.iloc[-1]

            bpm = int(latest['BPM']) if not pd.isna(latest['BPM']) else "--"
            temp = round(latest['Temp'], 2) if not pd.isna(latest['Temp']) else "--"
            stress = latest.get('Stress', "--")
            movement = latest.get('Movement', "--")
            voice = latest.get('Voice', "--")

            # ✅ ADDED ONLY THIS
            suggestion = latest.get('Suggestion', "--")

            # ✅ UPDATE LABELS
            bpm_label.config(text=f"BPM: {bpm}")
            temp_label.config(text=f"Temp: {temp}")
            stress_label.config(text=f"Stress: {stress}")
            movement_label.config(text=f"Movement: {movement}")
            voice_label.config(text=f"Voice: {voice}")

            # ✅ ADDED ONLY THIS
            suggestion_label.config(
                text=f"AI Suggestion: {suggestion}"
            )

            # ✅ GRAPH
            ax.clear()
            ax.plot(df['BPM'].tail(20), label="BPM")
            ax.plot(df['Temp'].tail(20), label="Temp")

            ax.legend()
            ax.set_title("Live Data")
            canvas.draw()

            # DEBUG
            print("GUI Latest:",
                  bpm, temp,
                  movement, voice,
                  stress, suggestion)

    except Exception as e:
        print("GUI Error:", e)

    root.after(2000, update)

update()
root.mainloop()
import subprocess
import time
import sys
import webbrowser
import os

print("🚀 Starting Stress Monitoring System...")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
python_path = sys.executable

processes = []

def run_script(script_name):
    script_path = os.path.join(BASE_DIR, script_name)

    print(f"▶ Running {script_name}...")

    try:
        p = subprocess.Popen(
            [python_path, script_path],
            cwd=BASE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        processes.append((script_name, p))
    except Exception as e:
        print(f"❌ Failed to start {script_name}: {e}")

# ▶️ Start MAIN (first)
run_script("main.py")

print("⏳ Waiting for data generation...")
time.sleep(8)   # ⬅️ IMPORTANT (increase wait)

# ▶️ Start GUI
run_script("gui_dashboard.py")
time.sleep(3)

# ▶️ Start Flask
run_script("app.py")
time.sleep(5)

# 🌐 Open browser
webbrowser.open("http://127.0.0.1:5001")

print("✅ All systems running!")

# 🔥 Monitor processes
try:
    while True:
        for name, p in processes:
            if p.poll() is not None:
                print(f"❌ {name} stopped unexpectedly!")
        time.sleep(2)

except KeyboardInterrupt:
    print("\n🛑 Stopping all processes...")
    for name, p in processes:
        p.terminate()
    print("✅ System stopped.")
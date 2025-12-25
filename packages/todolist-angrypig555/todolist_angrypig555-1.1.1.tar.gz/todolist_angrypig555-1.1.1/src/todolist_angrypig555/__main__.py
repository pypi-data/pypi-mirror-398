import sys

# --- Check if tkinter is available ---
try:
    import tkinter
except ImportError:
    print(" Error: Tkinter is not installed on this system.")
    print("To fix this:")
    print("  • On Linux: sudo apt install python3-tk")
    print("  • On Windows/macOS: reinstall Python from python.org (Tkinter is included)")
    sys.exit(1)


from .main import application

if __name__ == "__main__":
    app = application()
    app.run()
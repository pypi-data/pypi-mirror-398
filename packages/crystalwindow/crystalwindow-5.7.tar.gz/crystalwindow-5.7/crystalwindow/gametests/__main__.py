# crystalwindow/gametests/__main__.py
import importlib

DEMO_SCRIPTS = {
    "guitesting": "GUI widgets & layout demo",
    "gravitytest": "Gravity + physics test",
    "windowtesting": "Basic window and draw test",
    "sandbox": "Free experiment playground",
    "3dsquare": "3D Square Testing",
    "squaremove": "Moveable Square + Text test",
}

def list_demos():
    print("CrystalWindow Example Demos 🧊")
    print("--------------------------------")
    for name, desc in DEMO_SCRIPTS.items():
        print(f"{name:<15} - {desc}")
    print("\nRun one with:")
    print("  python -m crystalwindow.gametests.<demo_name>\n")  # <== fixed spelling!

def main():
    list_demos()

if __name__ == "__main__":
    main()

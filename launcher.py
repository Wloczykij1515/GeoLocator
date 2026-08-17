import subprocess
import sys
import os


def launch_in_new_terminal():
    """Uruchamia glowny program w nowym oknie terminala."""
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")

    if not os.path.exists(script_path):
        print(f"Nie znaleziono pliku {script_path}")
        return

    if sys.platform == "win32":
        subprocess.Popen(f'start cmd /k "python {script_path}"', shell=True)
        print("Uruchomiono program w nowym oknie terminala (CMD)")

    elif sys.platform == "darwin":
        subprocess.Popen([
            "osascript", "-e",
            f'tell application "Terminal" to do script "python3 {script_path}"'
        ])
        print("Uruchomiono program w nowym oknie terminala (Terminal.app)")

    elif sys.platform.startswith("linux"):
        # UWAGA (bylo brak obslugi w ogole): oryginal dzialal tylko na
        # Windows i na Linuksie/macOS nic sie nie dzialo - bez bledu,
        # bez komunikatu. Tutaj probujemy kilku popularnych emulatorow,
        # a jak zadnego nie ma - uruchamiamy w biezacym oknie.
        for terminal in ("x-terminal-emulator", "gnome-terminal", "konsole", "xterm"):
            try:
                subprocess.Popen([terminal, "-e", f"python3 {script_path}"])
                print(f"Uruchomiono program w nowym oknie terminala ({terminal})")
                return
            except FileNotFoundError:
                continue
        print("Nie znaleziono znanego emulatora terminala - uruchamiam w biezacym oknie")
        subprocess.run([sys.executable, script_path])

    else:
        print(f"Nieobslugiwana platforma: {sys.platform} - uruchamiam w biezacym oknie")
        subprocess.run([sys.executable, script_path])


if __name__ == "__main__":
    launch_in_new_terminal()

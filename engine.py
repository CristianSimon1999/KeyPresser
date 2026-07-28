import threading
import time

import psutil
import win32api
import win32con
import win32gui
import win32process

from pynput.keyboard import Controller


class KeyPresserEngine:

    def __init__(self):
        self.keyboard = Controller()

        self.running = False
        self.stop_event = threading.Event()

        self.target_pid = None
        self.target_hwnd = None

        # Se ejecutará cuando el proceso objetivo se cierre.
        self.on_process_closed = None

    # ========================================================
    # PROCESOS
    # ========================================================

    def get_processes(self):
        """
        Devuelve una lista:

        [
            ("notepad.exe", 1234),
            ("KathanaGame.exe", 5678)
        ]
        """

        processes = []

        for proc in psutil.process_iter(["pid", "name"]):
            try:
                pid = proc.info["pid"]
                name = proc.info["name"]

                if not name:
                    continue

                processes.append((name, pid))

            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied
            ):
                continue

        processes.sort(
            key=lambda process: process[0].lower()
        )

        return processes

    # ========================================================
    # BUSCAR VENTANA
    # ========================================================

    def find_window_for_pid(self, pid):
        windows = []

        def callback(hwnd, _):
            if not win32gui.IsWindowVisible(hwnd):
                return

            try:
                _, window_pid = (
                    win32process.GetWindowThreadProcessId(hwnd)
                )

                if window_pid != pid:
                    return

                title = win32gui.GetWindowText(hwnd)

                if title:
                    windows.append(hwnd)

            except Exception:
                pass

        win32gui.EnumWindows(callback, None)

        if windows:
            return windows[0]

        return None

    # ========================================================
    # INICIAR
    # ========================================================

    def start(self, pid, selected_keys, mode):
        """
        pid:
            PID del proceso objetivo.

        selected_keys:
            {
                "e": 500,
                "r": 1000,
                "1": 250
            }

        mode:
            "foreground"
            "background"
        """

        if self.running:
            return

        if not psutil.pid_exists(pid):
            raise RuntimeError(
                "El proceso seleccionado ya no existe."
            )

        hwnd = self.find_window_for_pid(pid)

        if hwnd is None:
            raise RuntimeError(
                "No se encontró una ventana visible "
                "para el proceso seleccionado."
            )

        self.target_pid = pid
        self.target_hwnd = hwnd
        self.mode = mode

        self.running = True
        self.stop_event.clear()

        # Monitor del proceso.
        threading.Thread(
            target=self._process_monitor,
            daemon=True
        ).start()

        # Un hilo independiente por tecla.
        for key, interval in selected_keys.items():

            threading.Thread(
                target=self._key_loop,
                args=(key, interval),
                daemon=True
            ).start()

    # ========================================================
    # DETENER
    # ========================================================

    def stop(self):
        self.running = False
        self.stop_event.set()

    # ========================================================
    # LOOP DE TECLA
    # ========================================================

    def _key_loop(self, key, interval_ms):
        interval_seconds = interval_ms / 1000.0

        while not self.stop_event.wait(interval_seconds):

            if not self.running:
                return

            try:
                if self.mode == "foreground":
                    self._send_foreground_key(key)

                elif self.mode == "background":
                    self._send_background_key(key)

            except Exception as error:
                print(
                    f"Error enviando '{key}': {error}"
                )

    # ========================================================
    # PRIMER PLANO
    # ========================================================

    def _send_foreground_key(self, key):
        hwnd = win32gui.GetForegroundWindow()

        if not hwnd:
            return

        try:
            _, active_pid = (
                win32process.GetWindowThreadProcessId(hwnd)
            )

        except Exception:
            return

        # Solo pulsar si el proceso seleccionado
        # tiene actualmente el foco.
        if active_pid != self.target_pid:
            return

        self.keyboard.press(key)
        self.keyboard.release(key)

    # ========================================================
    # SEGUNDO PLANO
    # ========================================================

    def _send_background_key(self, key):
        hwnd = self.target_hwnd

        if not hwnd:
            return

        if not win32gui.IsWindow(hwnd):
            return

        virtual_key = (
            win32api.VkKeyScan(key.upper())
            & 0xFF
        )

        scan_code = win32api.MapVirtualKey(
            virtual_key,
            0
        )

        # WM_KEYDOWN
        lparam_down = (
            1
            | (scan_code << 16)
        )

        # WM_KEYUP
        lparam_up = (
            1
            | (scan_code << 16)
            | (1 << 30)
            | (1 << 31)
        )

        win32gui.PostMessage(
            hwnd,
            win32con.WM_KEYDOWN,
            virtual_key,
            lparam_down
        )

        # Tiempo que permanece "presionada".
        time.sleep(0.02)

        win32gui.PostMessage(
            hwnd,
            win32con.WM_KEYUP,
            virtual_key,
            lparam_up
        )

    # ========================================================
    # MONITOR DEL PROCESO
    # ========================================================

    def _process_monitor(self):

        while not self.stop_event.wait(0.5):

            if self.target_pid is None:
                return

            if not psutil.pid_exists(
                self.target_pid
            ):
                self.running = False
                self.stop_event.set()

                if self.on_process_closed:
                    self.on_process_closed()

                return
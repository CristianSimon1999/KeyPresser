import subprocess
import threading

import psutil


class KeyPresserEngine:

    def __init__(self):
        self.running = False
        self.stop_event = threading.Event()

        self.target_pid = None
        self.target_window = None

        # Se ejecutará si desaparece el proceso objetivo.
        self.on_process_closed = None

    # ========================================================
    # PROCESOS
    # ========================================================

    def get_processes(self):
        """
        Devuelve una lista:

        [
            ("firefox", 1234),
            ("KathanaGame", 5678)
        ]
        """

        processes = []

        for proc in psutil.process_iter(["pid", "name"]):
            try:
                pid = proc.info["pid"]
                name = proc.info["name"]

                if not name:
                    continue

                processes.append(
                    (name, pid)
                )

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
    # BUSCAR VENTANA POR PID
    # ========================================================

    def find_window_for_pid(self, pid):
        """
        Busca una ventana X11/XWayland asociada al PID.

        Devuelve el Window ID encontrado o None.
        """

        try:
            result = subprocess.run(
                [
                    "xdotool",
                    "search",
                    "--pid",
                    str(pid)
                ],
                capture_output=True,
                text=True,
                timeout=3
            )

        except FileNotFoundError:
            raise RuntimeError(
                "xdotool no está instalado.\n\n"
                "Instálalo con:\n"
                "sudo apt install xdotool"
            )

        except subprocess.TimeoutExpired:
            return None

        if result.returncode != 0:
            return None

        windows = [
            line.strip()
            for line in result.stdout.splitlines()
            if line.strip()
        ]

        if not windows:
            return None

        # Por ahora usamos la primera ventana encontrada.
        return windows[0]

    # ========================================================
    # INICIAR
    # ========================================================

    def start(
        self,
        pid,
        selected_keys
    ):
        """
        Inicia KeyPresser sobre el proceso seleccionado.

        selected_keys:

        {
            "e": 500,
            "1": 1000,
            "f1": 2500
        }
        """

        if self.running:
            return

        # ----------------------------------------------------
        # COMPROBAR PROCESO
        # ----------------------------------------------------

        if not psutil.pid_exists(pid):
            raise RuntimeError(
                "El proceso seleccionado ya no existe."
            )

        # ----------------------------------------------------
        # BUSCAR VENTANA
        # ----------------------------------------------------

        window_id = self.find_window_for_pid(
            pid
        )

        if window_id is None:
            raise RuntimeError(
                "No se encontró una ventana X11/XWayland "
                "asociada al proceso seleccionado."
            )

        # ----------------------------------------------------
        # GUARDAR OBJETIVO
        # ----------------------------------------------------

        self.target_pid = pid
        self.target_window = window_id

        # ----------------------------------------------------
        # ARRANCAR
        # ----------------------------------------------------

        self.running = True
        self.stop_event.clear()

        # Monitor del proceso
        threading.Thread(
            target=self._process_monitor,
            daemon=True
        ).start()

        # Un hilo independiente por tecla
        for key, interval in selected_keys.items():

            threading.Thread(
                target=self._key_loop,
                args=(
                    key,
                    interval
                ),
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

    def _key_loop(
        self,
        key,
        interval_ms
    ):
        interval_seconds = (
            interval_ms / 1000.0
        )

        while not self.stop_event.wait(
            interval_seconds
        ):

            if not self.running:
                return

            try:
                self._send_key(
                    key
                )

            except Exception as error:
                print(
                    f"Error enviando '{key}': {error}"
                )

    # ========================================================
    # CONVERTIR TECLA
    # ========================================================

    def _get_xdotool_key(
        self,
        key
    ):
        """
        Convierte nuestras teclas al nombre que espera xdotool.

        e    -> e
        r    -> r
        1    -> 1
        0    -> 0
        f1   -> F1
        f10  -> F10
        """

        function_keys = {
            "f1": "F1",
            "f2": "F2",
            "f3": "F3",
            "f4": "F4",
            "f5": "F5",
            "f6": "F6",
            "f7": "F7",
            "f8": "F8",
            "f9": "F9",
            "f10": "F10",
        }

        return function_keys.get(
            key,
            key
        )

    # ========================================================
    # ENVIAR TECLA
    # ========================================================

    def _send_key(
        self,
        key
    ):
        if not self.target_window:
            return

        xdotool_key = (
            self._get_xdotool_key(key)
        )

        result = subprocess.run(
            [
                "xdotool",
                "key",
                "--window",
                str(self.target_window),
                "--clearmodifiers",
                xdotool_key
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            timeout=2
        )

        if result.returncode != 0:
            raise RuntimeError(
                result.stderr.strip()
                or "xdotool no pudo enviar la tecla."
            )

    # ========================================================
    # MONITOR DEL PROCESO
    # ========================================================

    def _process_monitor(self):

        while not self.stop_event.wait(
            0.5
        ):

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
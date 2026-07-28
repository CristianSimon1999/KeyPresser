import threading
import time

import psutil
import win32api
import win32con
import win32gui
import win32process


class KeyPresserEngine:

    def __init__(self):
        # Estado del motor
        self.running = False
        self.stop_event = threading.Event()

        # Proceso y ventana objetivo
        self.target_pid = None
        self.target_hwnd = None

        # Se ejecutará cuando el proceso objetivo se cierre.
        self.on_process_closed = None

    # ========================================================
    # PROCESOS
    # ========================================================

    def get_processes(self):
        """
        Devuelve una lista de procesos:

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

                processes.append(
                    (name, pid)
                )

            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied
            ):
                continue

        # Ordenar alfabéticamente por nombre.
        processes.sort(
            key=lambda process: process[0].lower()
        )

        return processes

    # ========================================================
    # BUSCAR VENTANA DEL PROCESO
    # ========================================================

    def find_window_for_pid(self, pid):
        """
        Busca una ventana visible asociada al PID indicado.

        Devuelve el HWND de la ventana encontrada
        o None si no existe.
        """

        windows = []

        def callback(hwnd, _):
            # Ignorar ventanas no visibles.
            if not win32gui.IsWindowVisible(hwnd):
                return

            try:
                _, window_pid = (
                    win32process.GetWindowThreadProcessId(
                        hwnd
                    )
                )

                # La ventana debe pertenecer
                # al proceso seleccionado.
                if window_pid != pid:
                    return

                # Preferimos ventanas con título.
                title = win32gui.GetWindowText(
                    hwnd
                )

                if title:
                    windows.append(hwnd)

            except Exception:
                pass

        win32gui.EnumWindows(
            callback,
            None
        )

        if windows:
            return windows[0]

        return None

    # ========================================================
    # INICIAR
    # ========================================================

    def start(
        self,
        pid,
        selected_keys
    ):
        """
        Inicia el KeyPresser.

        pid:
            PID del proceso objetivo.

        selected_keys:
            Diccionario con tecla -> intervalo.

        Ejemplo:

            {
                "e": 500,
                "r": 1000,
                "1": 250,
                "f1": 500,
                "f10": 1500
            }
        """

        # Si ya está funcionando,
        # no hacemos nada.
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

        hwnd = self.find_window_for_pid(
            pid
        )

        if hwnd is None:
            raise RuntimeError(
                "No se encontró una ventana visible "
                "para el proceso seleccionado."
            )

        # ----------------------------------------------------
        # GUARDAR OBJETIVO
        # ----------------------------------------------------

        self.target_pid = pid
        self.target_hwnd = hwnd

        # ----------------------------------------------------
        # ARRANCAR MOTOR
        # ----------------------------------------------------

        self.running = True
        self.stop_event.clear()

        # ----------------------------------------------------
        # MONITOR DEL PROCESO
        # ----------------------------------------------------

        threading.Thread(
            target=self._process_monitor,
            daemon=True
        ).start()

        # ----------------------------------------------------
        # UN HILO POR TECLA
        # ----------------------------------------------------

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
        """
        Detiene todos los loops de teclas.
        """

        self.running = False
        self.stop_event.set()

    # ========================================================
    # LOOP DE CADA TECLA
    # ========================================================

    def _key_loop(
        self,
        key,
        interval_ms
    ):
        """
        Cada tecla tiene su propio hilo y su propio intervalo.
        """

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
    # OBTENER VIRTUAL KEY
    # ========================================================

    def _get_virtual_key(
        self,
        key
    ):
        """
        Convierte las teclas utilizadas internamente
        a Virtual-Key Codes de Windows.

        Soporta:

        E
        R
        F

        0 - 9

        F1 - F10
        """

        # ----------------------------------------------------
        # TECLAS DE FUNCIÓN
        # ----------------------------------------------------

        function_keys = {
            "f1": win32con.VK_F1,
            "f2": win32con.VK_F2,
            "f3": win32con.VK_F3,
            "f4": win32con.VK_F4,
            "f5": win32con.VK_F5,
            "f6": win32con.VK_F6,
            "f7": win32con.VK_F7,
            "f8": win32con.VK_F8,
            "f9": win32con.VK_F9,
            "f10": win32con.VK_F10,
        }

        if key in function_keys:
            return function_keys[key]

        # ----------------------------------------------------
        # LETRAS Y NÚMEROS
        # ----------------------------------------------------

        virtual_key = win32api.VkKeyScan(
            key.upper()
        )

        # VkKeyScan devuelve -1 si no encuentra
        # una representación válida.
        if virtual_key == -1:
            raise ValueError(
                f"Tecla no soportada: {key}"
            )

        return virtual_key & 0xFF

    # ========================================================
    # ENVIAR TECLA
    # ========================================================

    def _send_key(
        self,
        key
    ):
        """
        Envía una pulsación directamente a la ventana objetivo.

        No importa si la ventana está en primer plano
        o en segundo plano.
        """

        hwnd = self.target_hwnd

        # ----------------------------------------------------
        # COMPROBAR VENTANA
        # ----------------------------------------------------

        if not hwnd:
            return

        if not win32gui.IsWindow(hwnd):
            return

        # ----------------------------------------------------
        # VIRTUAL KEY
        # ----------------------------------------------------

        virtual_key = (
            self._get_virtual_key(key)
        )

        # ----------------------------------------------------
        # SCAN CODE
        # ----------------------------------------------------

        scan_code = (
            win32api.MapVirtualKey(
                virtual_key,
                0
            )
        )

        # ----------------------------------------------------
        # WM_KEYDOWN
        # ----------------------------------------------------

        lparam_down = (
            1
            | (scan_code << 16)
        )

        # ----------------------------------------------------
        # WM_KEYUP
        # ----------------------------------------------------

        lparam_up = (
            1
            | (scan_code << 16)
            | (1 << 30)
            | (1 << 31)
        )

        # ----------------------------------------------------
        # PRESIONAR
        # ----------------------------------------------------

        win32gui.PostMessage(
            hwnd,
            win32con.WM_KEYDOWN,
            virtual_key,
            lparam_down
        )

        # La tecla permanece pulsada durante 20 ms.
        time.sleep(0.02)

        # ----------------------------------------------------
        # SOLTAR
        # ----------------------------------------------------

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
        """
        Comprueba periódicamente que el proceso objetivo
        siga abierto.
        """

        while not self.stop_event.wait(
            0.5
        ):

            if self.target_pid is None:
                return

            # ------------------------------------------------
            # PROCESO CERRADO
            # ------------------------------------------------

            if not psutil.pid_exists(
                self.target_pid
            ):

                self.running = False
                self.stop_event.set()

                if self.on_process_closed:
                    self.on_process_closed()

                return

            # ------------------------------------------------
            # VENTANA CERRADA
            # ------------------------------------------------

            if (
                self.target_hwnd
                and not win32gui.IsWindow(
                    self.target_hwnd
                )
            ):

                self.running = False
                self.stop_event.set()

                if self.on_process_closed:
                    self.on_process_closed()

                return
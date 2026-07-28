import tkinter as tk
from tkinter import ttk, messagebox

from engine import KeyPresserEngine


DEFAULT_PROCESS = "KathanaGame.exe"


class KeyPresserGUI:

    def __init__(self, root):
        self.root = root

        self.root.title("Key Presser")
        self.root.geometry("560x900")
        self.root.resizable(False, False)

        # Motor
        self.engine = KeyPresserEngine()

        # Cuando el proceso objetivo se cierre,
        # engine nos avisará mediante esta función.
        self.engine.on_process_closed = (
            self.process_closed_from_engine
        )

        # Teclas disponibles.
        self.keys = [
            ("E", "e"),
            ("R", "r"),
            ("F", "f"),
            ("1", "1"),
            ("2", "2"),
            ("3", "3"),
            ("4", "4"),
            ("5", "5"),
            ("6", "6"),
            ("7", "7"),
            ("8", "8"),
            ("9", "9"),
            ("10 (0)", "0"),
        ]

        self.enabled_vars = {}
        self.interval_vars = {}
        self.interval_entries = {}

        # Relación:
        #
        # texto mostrado -> PID
        self.process_map = {}

        self.create_interface()

        self.refresh_processes()

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.close_app
        )

    # ========================================================
    # INTERFAZ
    # ========================================================

    def create_interface(self):

        main = ttk.Frame(
            self.root,
            padding=20
        )

        main.pack(
            fill="both",
            expand=True
        )

        # ----------------------------------------------------
        # TÍTULO
        # ----------------------------------------------------

        ttk.Label(
            main,
            text="KEY PRESSER",
            font=("Segoe UI", 22, "bold")
        ).pack(
            pady=(0, 20)
        )

        # ----------------------------------------------------
        # APLICACIÓN OBJETIVO
        # ----------------------------------------------------

        process_frame = ttk.LabelFrame(
            main,
            text="Aplicación objetivo",
            padding=12
        )

        process_frame.pack(
            fill="x"
        )

        self.process_combo = ttk.Combobox(
            process_frame,
            state="readonly",
            width=48
        )

        self.process_combo.pack(
            side="left",
            padx=(0, 10)
        )

        self.refresh_button = ttk.Button(
            process_frame,
            text="Actualizar",
            command=self.refresh_processes
        )

        self.refresh_button.pack(
            side="left"
        )

        # ----------------------------------------------------
        # MODO
        # ----------------------------------------------------

        mode_frame = ttk.LabelFrame(
            main,
            text="Modo de entrada",
            padding=10
        )

        mode_frame.pack(
            fill="x",
            pady=15
        )

        self.input_mode = tk.StringVar(
            value="foreground"
        )

        ttk.Radiobutton(
            mode_frame,
            text="Solo cuando el juego esté enfocado",
            variable=self.input_mode,
            value="foreground"
        ).pack(
            anchor="w"
        )

        ttk.Radiobutton(
            mode_frame,
            text="Segundo plano (experimental)",
            variable=self.input_mode,
            value="background"
        ).pack(
            anchor="w"
        )

        # ----------------------------------------------------
        # TECLAS
        # ----------------------------------------------------

        keys_frame = ttk.LabelFrame(
            main,
            text="Teclas",
            padding=10
        )

        keys_frame.pack(
            fill="x"
        )

        ttk.Label(
            keys_frame,
            text="Usar",
            font=("Segoe UI", 10, "bold")
        ).grid(
            row=0,
            column=0,
            padx=15,
            pady=5
        )

        ttk.Label(
            keys_frame,
            text="Tecla",
            font=("Segoe UI", 10, "bold")
        ).grid(
            row=0,
            column=1,
            padx=15,
            pady=5
        )

        ttk.Label(
            keys_frame,
            text="Intervalo (ms)",
            font=("Segoe UI", 10, "bold")
        ).grid(
            row=0,
            column=2,
            padx=15,
            pady=5
        )

        # ----------------------------------------------------
        # FILAS
        # ----------------------------------------------------

        for row, (display_name, key) in enumerate(
            self.keys,
            start=1
        ):

            enabled = tk.BooleanVar(
                value=False
            )

            interval = tk.StringVar(
                value="500"
            )

            self.enabled_vars[key] = enabled
            self.interval_vars[key] = interval

            # Checkbox

            checkbox = ttk.Checkbutton(
                keys_frame,
                variable=enabled,
                command=lambda k=key:
                    self.update_entry_state(k)
            )

            checkbox.grid(
                row=row,
                column=0,
                pady=4
            )

            # Nombre tecla

            ttk.Label(
                keys_frame,
                text=display_name
            ).grid(
                row=row,
                column=1,
                pady=4
            )

            # Intervalo

            entry = ttk.Entry(
                keys_frame,
                textvariable=interval,
                width=14,
                justify="center"
            )

            entry.grid(
                row=row,
                column=2,
                pady=4
            )

            self.interval_entries[key] = entry

            entry.config(
                state="disabled"
            )

        # ----------------------------------------------------
        # BOTONES
        # ----------------------------------------------------

        button_frame = ttk.Frame(main)

        button_frame.pack(
            pady=20
        )

        self.start_button = ttk.Button(
            button_frame,
            text="▶ INICIAR",
            command=self.start_bot
        )

        self.start_button.grid(
            row=0,
            column=0,
            padx=10,
            ipadx=15,
            ipady=5
        )

        self.stop_button = ttk.Button(
            button_frame,
            text="■ DETENER",
            command=self.stop_bot,
            state="disabled"
        )

        self.stop_button.grid(
            row=0,
            column=1,
            padx=10,
            ipadx=15,
            ipady=5
        )

        # ----------------------------------------------------
        # ESTADO
        # ----------------------------------------------------

        self.status_label = ttk.Label(
            main,
            text="● Detenido",
            font=("Segoe UI", 11)
        )

        self.status_label.pack()

        self.target_label = ttk.Label(
            main,
            text="Objetivo: ninguno"
        )

        self.target_label.pack(
            pady=5
        )

    # ========================================================
    # CHECKBOX
    # ========================================================

    def update_entry_state(self, key):

        entry = self.interval_entries[key]

        if self.enabled_vars[key].get():

            entry.config(
                state="normal"
            )

        else:

            entry.config(
                state="disabled"
            )

    # ========================================================
    # PROCESOS
    # ========================================================

    def refresh_processes(self):

        previous_selection = (
            self.process_combo.get()
        )

        self.process_map.clear()

        items = []

        # Pedimos los procesos al motor.
        processes = self.engine.get_processes()

        for name, pid in processes:

            item = (
                f"{name}  |  PID {pid}"
            )

            items.append(item)

            self.process_map[item] = pid

        self.process_combo["values"] = items

        # ----------------------------------------------------
        # Mantener selección anterior
        # ----------------------------------------------------

        if previous_selection in self.process_map:

            self.process_combo.set(
                previous_selection
            )

            return

        # ----------------------------------------------------
        # Buscar KathanaGame.exe
        # ----------------------------------------------------

        for index, (name, pid) in enumerate(
            processes
        ):

            if (
                name.lower()
                == DEFAULT_PROCESS.lower()
            ):

                self.process_combo.current(
                    index
                )

                return

        # ----------------------------------------------------
        # Si no está abierto
        # ----------------------------------------------------

        if items:

            self.process_combo.current(0)

    # ========================================================
    # LEER TECLAS
    # ========================================================

    def get_selected_keys(self):

        selected = {}

        for _, key in self.keys:

            if not self.enabled_vars[key].get():
                continue

            try:

                interval = int(
                    self.interval_vars[key].get()
                )

                if interval <= 0:
                    raise ValueError

            except ValueError:

                raise ValueError(
                    f"El intervalo de '{key}' "
                    f"debe ser un número mayor que 0."
                )

            selected[key] = interval

        if not selected:

            raise ValueError(
                "Debes activar al menos una tecla."
            )

        return selected

    # ========================================================
    # INICIAR
    # ========================================================

    def start_bot(self):

        selected_process = (
            self.process_combo.get()
        )

        if not selected_process:

            messagebox.showerror(
                "Proceso",
                "Selecciona una aplicación objetivo."
            )

            return

        pid = self.process_map.get(
            selected_process
        )

        if pid is None:

            messagebox.showerror(
                "Proceso",
                "El proceso seleccionado ya no existe.\n"
                "Pulsa Actualizar."
            )

            return

        # ----------------------------------------------------
        # TECLAS
        # ----------------------------------------------------

        try:

            selected_keys = (
                self.get_selected_keys()
            )

        except ValueError as error:

            messagebox.showerror(
                "Configuración",
                str(error)
            )

            return

        # ----------------------------------------------------
        # ARRANCAR MOTOR
        # ----------------------------------------------------

        try:

            self.engine.start(
                pid=pid,
                selected_keys=selected_keys,
                mode=self.input_mode.get()
            )

        except RuntimeError as error:

            messagebox.showerror(
                "Error",
                str(error)
            )

            self.refresh_processes()

            return

        # ----------------------------------------------------
        # ACTUALIZAR GUI
        # ----------------------------------------------------

        self.start_button.config(
            state="disabled"
        )

        self.stop_button.config(
            state="normal"
        )

        self.status_label.config(
            text="● Ejecutándose"
        )

        self.target_label.config(
            text=f"Objetivo: {selected_process}"
        )

    # ========================================================
    # DETENER
    # ========================================================

    def stop_bot(self):

        self.engine.stop()

        self.start_button.config(
            state="normal"
        )

        self.stop_button.config(
            state="disabled"
        )

        self.status_label.config(
            text="● Detenido"
        )

    # ========================================================
    # PROCESO CERRADO
    # ========================================================

    def process_closed_from_engine(self):

        # Esta función llega desde un hilo secundario.
        # Tkinter debe modificarse desde el hilo principal.

        self.root.after(
            0,
            self.handle_process_closed
        )

    def handle_process_closed(self):

        self.start_button.config(
            state="normal"
        )

        self.stop_button.config(
            state="disabled"
        )

        self.status_label.config(
            text="● Detenido"
        )

        self.target_label.config(
            text="Objetivo: proceso cerrado"
        )

        messagebox.showinfo(
            "Proceso cerrado",
            "La aplicación objetivo se ha cerrado.\n\n"
            "Key Presser se ha detenido."
        )

        self.refresh_processes()

    # ========================================================
    # CERRAR
    # ========================================================

    def close_app(self):

        self.engine.stop()

        self.root.destroy()
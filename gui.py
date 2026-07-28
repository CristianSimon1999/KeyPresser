import tkinter as tk
from tkinter import ttk, messagebox

from engine import KeyPresserEngine


DEFAULT_PROCESS = "KathanaGame.exe"


class KeyPresserGUI:

    def __init__(self, root):
        self.root = root

        self.root.title("Key Presser")
        self.root.geometry("980x590")
        self.root.resizable(False, False)

        # ====================================================
        # MOTOR
        # ====================================================

        self.engine = KeyPresserEngine()

        self.engine.on_process_closed = (
            self.process_closed_from_engine
        )

        # ====================================================
        # TECLAS
        # ====================================================

        # Acciones principales
        self.action_keys = [
            ("Target (E)", "e"),
            ("Atacar (R)", "r"),
            ("Recoger (F)", "f"),
        ]

        # Teclas numéricas
        self.number_keys = [
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

        # Teclas de función
        self.function_keys = [
            ("F1", "f1"),
            ("F2", "f2"),
            ("F3", "f3"),
            ("F4", "f4"),
            ("F5", "f5"),
            ("F6", "f6"),
            ("F7", "f7"),
            ("F8", "f8"),
            ("F9", "f9"),
            ("F10", "f10"),
        ]

        # Todas las teclas
        self.keys = (
            self.action_keys
            + self.number_keys
            + self.function_keys
        )

        # Variables
        self.enabled_vars = {}
        self.interval_vars = {}
        self.interval_entries = {}

        # Relación:
        #
        # "KathanaGame.exe | PID 1234"
        # ->
        # 1234
        self.process_map = {}

        # Crear interfaz
        self.create_interface()

        # Cargar procesos
        self.refresh_processes()

        # Cierre de ventana
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
            padding=15
        )

        main.pack(
            fill="both",
            expand=True
        )

        # ====================================================
        # ESTADO
        # ====================================================

        status_frame = ttk.Frame(
            main
        )

        status_frame.pack(
            fill="x",
            pady=(0, 10)
        )

        self.status_label = ttk.Label(
            status_frame,
            text="● Detenido",
            font=("Segoe UI", 11, "bold")
        )

        self.status_label.pack(
            anchor="w"
        )

        self.target_label = ttk.Label(
            status_frame,
            text="Objetivo: ninguno",
            font=("Segoe UI", 9)
        )

        self.target_label.pack(
            anchor="w",
            pady=(2, 0)
        )

        # ====================================================
        # APLICACIÓN OBJETIVO
        # ====================================================

        process_frame = ttk.LabelFrame(
            main,
            text="Aplicación objetivo",
            padding=10
        )

        process_frame.pack(
            fill="x",
            pady=(0, 10)
        )

        process_frame.columnconfigure(
            0,
            weight=1
        )

        # Selector
        self.process_combo = ttk.Combobox(
            process_frame,
            state="readonly"
        )

        self.process_combo.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 10)
        )

        # Botón actualizar
        self.refresh_button = ttk.Button(
            process_frame,
            text="Actualizar",
            command=self.refresh_processes
        )

        self.refresh_button.grid(
            row=0,
            column=1
        )

        # ====================================================
        # TECLAS
        # ====================================================

        keys_frame = ttk.LabelFrame(
            main,
            text="Teclas",
            padding=12
        )

        keys_frame.pack(
            fill="both",
            expand=True
        )

        # ====================================================
        # ACCIONES PRINCIPALES
        # ====================================================

        actions_frame = ttk.Frame(
            keys_frame
        )

        actions_frame.pack(
            fill="x"
        )

        ttk.Label(
            actions_frame,
            text="Acciones principales",
            font=("Segoe UI", 10, "bold")
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 8)
        )

        ttk.Label(
            actions_frame,
            text="Usar",
            font=("Segoe UI", 9, "bold")
        ).grid(
            row=0,
            column=1,
            padx=(60, 20),
            pady=(0, 8)
        )

        ttk.Label(
            actions_frame,
            text="Intervalo (ms)",
            font=("Segoe UI", 9, "bold")
        ).grid(
            row=0,
            column=2,
            pady=(0, 8)
        )

        for row, (
            display_name,
            key
        ) in enumerate(
            self.action_keys,
            start=1
        ):

            self.create_action_row(
                actions_frame,
                row,
                display_name,
                key
            )

        # ====================================================
        # TECLAS NUMÉRICAS
        # ====================================================

        ttk.Label(
            keys_frame,
            text="Teclas numéricas (1 - 10)",
            font=("Segoe UI", 10, "bold")
        ).pack(
            anchor="w",
            pady=(16, 8)
        )

        numbers_frame = ttk.Frame(
            keys_frame
        )

        numbers_frame.pack(
            fill="x"
        )

        # 5 columnas
        for column in range(5):

            numbers_frame.columnconfigure(
                column,
                weight=1
            )

        # 2 filas de 5
        for index, (
            display_name,
            key
        ) in enumerate(
            self.number_keys
        ):

            row = index // 5
            column = index % 5

            self.create_key_control(
                numbers_frame,
                row,
                column,
                display_name,
                key
            )

        # ====================================================
        # TECLAS F1 - F10
        # ====================================================

        ttk.Label(
            keys_frame,
            text="Teclas de función (F1 - F10)",
            font=("Segoe UI", 10, "bold")
        ).pack(
            anchor="w",
            pady=(16, 8)
        )

        function_frame = ttk.Frame(
            keys_frame
        )

        function_frame.pack(
            fill="x"
        )

        # 5 columnas
        for column in range(5):

            function_frame.columnconfigure(
                column,
                weight=1
            )

        # 2 filas de 5
        for index, (
            display_name,
            key
        ) in enumerate(
            self.function_keys
        ):

            row = index // 5
            column = index % 5

            self.create_key_control(
                function_frame,
                row,
                column,
                display_name,
                key
            )

        # ====================================================
        # BOTONES
        # ====================================================

        button_frame = ttk.Frame(
            main
        )

        button_frame.pack(
            pady=(15, 0)
        )

        self.start_button = ttk.Button(
            button_frame,
            text="▶ INICIAR",
            command=self.start_bot,
            width=18
        )

        self.start_button.grid(
            row=0,
            column=0,
            padx=5,
            ipady=4
        )

        self.stop_button = ttk.Button(
            button_frame,
            text="■ DETENER",
            command=self.stop_bot,
            state="disabled",
            width=18
        )

        self.stop_button.grid(
            row=0,
            column=1,
            padx=5,
            ipady=4
        )

    # ========================================================
    # CREAR ACCIÓN PRINCIPAL
    # ========================================================

    def create_action_row(
        self,
        parent,
        row,
        display_name,
        key
    ):

        enabled = tk.BooleanVar(
            value=False
        )

        interval = tk.StringVar(
            value="500"
        )

        self.enabled_vars[
            key
        ] = enabled

        self.interval_vars[
            key
        ] = interval

        # Nombre
        ttk.Label(
            parent,
            text=display_name,
            width=25
        ).grid(
            row=row,
            column=0,
            sticky="w",
            pady=4
        )

        # Checkbox
        checkbox = ttk.Checkbutton(
            parent,
            variable=enabled,
            command=lambda k=key:
                self.update_entry_state(k)
        )

        checkbox.grid(
            row=row,
            column=1,
            padx=(60, 20)
        )

        # Intervalo
        entry = ttk.Spinbox(
            parent,
            from_=1,
            to=999999,
            textvariable=interval,
            width=12,
            justify="center",
            state="disabled"
        )

        entry.grid(
            row=row,
            column=2,
            pady=4
        )

        self.interval_entries[
            key
        ] = entry

    # ========================================================
    # CREAR TECLA NUMÉRICA / FUNCIÓN
    # ========================================================

    def create_key_control(
        self,
        parent,
        row,
        column,
        display_name,
        key
    ):

        enabled = tk.BooleanVar(
            value=False
        )

        interval = tk.StringVar(
            value="500"
        )

        self.enabled_vars[
            key
        ] = enabled

        self.interval_vars[
            key
        ] = interval

        # Contenedor de cada tecla
        item_frame = ttk.Frame(
            parent
        )

        item_frame.grid(
            row=row,
            column=column,
            sticky="w",
            padx=(0, 15),
            pady=6
        )

        # Nombre
        ttk.Label(
            item_frame,
            text=display_name,
            width=6
        ).grid(
            row=0,
            column=0
        )

        # Checkbox
        checkbox = ttk.Checkbutton(
            item_frame,
            variable=enabled,
            command=lambda k=key:
                self.update_entry_state(k)
        )

        checkbox.grid(
            row=0,
            column=1,
            padx=(0, 5)
        )

        # Intervalo
        entry = ttk.Spinbox(
            item_frame,
            from_=1,
            to=999999,
            textvariable=interval,
            width=7,
            justify="center",
            state="disabled"
        )

        entry.grid(
            row=0,
            column=2
        )

        # ms
        ttk.Label(
            item_frame,
            text="ms"
        ).grid(
            row=0,
            column=3,
            padx=(4, 0)
        )

        self.interval_entries[
            key
        ] = entry

    # ========================================================
    # CHECKBOX
    # ========================================================

    def update_entry_state(
        self,
        key
    ):

        entry = (
            self.interval_entries[
                key
            ]
        )

        if self.enabled_vars[
            key
        ].get():

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

        # Obtener procesos desde engine
        processes = (
            self.engine.get_processes()
        )

        for name, pid in processes:

            item = (
                f"{name}  |  PID {pid}"
            )

            items.append(
                item
            )

            self.process_map[
                item
            ] = pid

        # Actualizar combobox
        self.process_combo[
            "values"
        ] = items

        # ----------------------------------------------------
        # MANTENER SELECCIÓN
        # ----------------------------------------------------

        if (
            previous_selection
            in self.process_map
        ):

            self.process_combo.set(
                previous_selection
            )

            return

        # ----------------------------------------------------
        # BUSCAR KATHANA
        # ----------------------------------------------------

        for index, (
            name,
            pid
        ) in enumerate(
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
        # SI NO ESTÁ KATHANA
        # ----------------------------------------------------

        if items:

            self.process_combo.current(
                0
            )

    # ========================================================
    # OBTENER TECLAS SELECCIONADAS
    # ========================================================

    def get_selected_keys(self):

        selected = {}

        for _, key in self.keys:

            # Si no está marcada,
            # ignoramos la tecla.
            if not self.enabled_vars[
                key
            ].get():

                continue

            try:

                interval = int(
                    self.interval_vars[
                        key
                    ].get()
                )

                if interval <= 0:
                    raise ValueError

            except ValueError:

                raise ValueError(
                    f"El intervalo de '{key}' "
                    f"debe ser un número mayor que 0."
                )

            selected[
                key
            ] = interval

        # Debe existir al menos una.
        if not selected:

            raise ValueError(
                "Debes activar al menos una tecla."
            )

        return selected

    # ========================================================
    # INICIAR
    # ========================================================

    def start_bot(self):

        # ----------------------------------------------------
        # PROCESO
        # ----------------------------------------------------

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
        # ARRANCAR ENGINE
        # ----------------------------------------------------

        try:

            self.engine.start(
                pid=pid,
                selected_keys=selected_keys
            )

        except RuntimeError as error:

            messagebox.showerror(
                "Error",
                str(error)
            )

            self.refresh_processes()

            return

        # ----------------------------------------------------
        # ACTUALIZAR INTERFAZ
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

        # Esta función puede ser llamada
        # desde un hilo del engine.
        #
        # Tkinter debe actualizarse desde
        # el hilo principal.

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

        # Actualizar lista
        self.refresh_processes()

    # ========================================================
    # CERRAR APLICACIÓN
    # ========================================================

    def close_app(self):

        self.engine.stop()

        self.root.destroy()
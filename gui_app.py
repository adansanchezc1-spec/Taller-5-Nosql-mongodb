"""
Interfaz Gráfica de Usuario (gui_app.py) - Sistema TechCare Solutions.
Permite ingresar clientes, registrar órdenes de servicio, cargar datos semilla
y realizar consultas/actualizaciones en tiempo real sobre MongoDB (localhost:27017).
Desarrollada con Tkinter y TTK (nativo en Python sin librerías externas adicionales).
"""

import json
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, List, Optional

from database import DatabaseManager
from crud_master import CrudMaster


class TechCareGUI:
    """Aplicación de interfaz gráfica de escritorio para TechCare Solutions en MongoDB."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("TechCare Solutions - Gestión MongoDB NoSQL")
        self.root.geometry("1020x720")
        self.root.minsize(850, 600)

        # Iniciar DatabaseManager y CrudMaster
        self.db_mgr = DatabaseManager()
        self.crud: Optional[CrudMaster] = None
        self.db_status_text = "Conectando..."
        self.is_connected = False

        # Configuración de estilos visuales
        self._configurar_estilos()

        # Construir estructura de la interfaz
        self._crear_encabezado()
        self._crear_notebook_pestanas()
        self._crear_barra_estado()

        # Conectar e inicializar datos
        self._iniciar_conexion()

    def _configurar_estilos(self) -> None:
        """Configura la paleta de colores y estilos TTK."""
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Colores corporativos TechCare
        self.c_primary = "#1E3A8A"      # Azul marino
        self.c_secondary = "#2563EB"    # Azul brillante
        self.c_bg = "#F8FAFC"           # Blanco humo
        self.c_card = "#FFFFFF"         # Blanco
        self.c_text = "#0F172A"         # Slate oscuro
        self.c_success = "#16A34A"      # Verde
        self.c_warning = "#D97706"      # Ámbar
        self.c_danger = "#DC2626"       # Rojo

        self.root.configure(bg=self.c_bg)

        # Fuentes
        self.font_title = ("Segoe UI", 14, "bold")
        self.font_subtitle = ("Segoe UI", 9)
        self.font_bold = ("Segoe UI", 9, "bold")
        self.font_regular = ("Segoe UI", 9)
        self.font_mono = ("Consolas", 9)

        # Estilos TTK
        self.style.configure(".", font=self.font_regular, background=self.c_bg, foreground=self.c_text)
        self.style.configure("TNotebook", background=self.c_bg)
        self.style.configure("TNotebook.Tab", padding=[14, 6], font=self.font_bold)
        self.style.map("TNotebook.Tab",
                       background=[("selected", self.c_card), ("active", "#E2E8F0")],
                       foreground=[("selected", self.c_primary), ("active", self.c_text)])

        self.style.configure("TLabelframe", background=self.c_card, relief="solid", borderwidth=1)
        self.style.configure("TLabelframe.Label", font=self.font_bold, foreground=self.c_primary, background=self.c_card)

        self.style.configure("Primary.TButton", font=self.font_bold, background=self.c_secondary, foreground="#FFFFFF", borderwidth=0, padding=6)
        self.style.map("Primary.TButton", background=[("active", "#1D4ED8")])

        self.style.configure("Success.TButton", font=self.font_bold, background=self.c_success, foreground="#FFFFFF", borderwidth=0, padding=6)
        self.style.map("Success.TButton", background=[("active", "#15803D")])

        self.style.configure("Secondary.TButton", font=self.font_bold, padding=6)

        # Treeview (Tablas)
        self.style.configure("Treeview", font=self.font_regular, rowheight=24, background=self.c_card, fieldbackground=self.c_card)
        self.style.configure("Treeview.Heading", font=self.font_bold, background="#E2E8F0", foreground=self.c_primary)

    def _crear_encabezado(self) -> None:
        """Crea el banner superior con el título y estado de conexión."""
        header_frame = tk.Frame(self.root, bg=self.c_primary, height=65, padx=20, pady=10)
        header_frame.pack(fill=tk.X, side=tk.TOP)

        title_label = tk.Label(
            header_frame,
            text="TechCare Solutions — Sistema NoSQL MongoDB",
            font=self.font_title,
            bg=self.c_primary,
            fg="#FFFFFF"
        )
        title_label.pack(side=tk.LEFT, anchor="w")

        sub_label = tk.Label(
            header_frame,
            text="Taller 5 Base de Datos | Host: localhost:27017 | DB: techcare_db",
            font=self.font_subtitle,
            bg=self.c_primary,
            fg="#93C5FD"
        )
        sub_label.pack(side=tk.LEFT, padx=15, anchor="w")

        self.lbl_status = tk.Label(
            header_frame,
            text="● Verificando conexión...",
            font=self.font_bold,
            bg=self.c_primary,
            fg="#FDE047"
        )
        self.lbl_status.pack(side=tk.RIGHT, anchor="e")

    def _crear_barra_estado(self) -> None:
        """Crea la barra inferior para notificaciones y trazabilidad."""
        self.status_bar = tk.Label(
            self.root,
            text="Listo para registrar datos y ejecutar consultas.",
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            bg="#E2E8F0",
            fg=self.c_text,
            font=self.font_subtitle,
            padx=10,
            pady=3
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _crear_notebook_pestanas(self) -> None:
        """Crea las pestañas principales de la aplicación."""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        # Pestañas
        self.tab_clientes = ttk.Frame(self.notebook, padding=10)
        self.tab_ordenes = ttk.Frame(self.notebook, padding=10)
        self.tab_consultas = ttk.Frame(self.notebook, padding=10)

        self.notebook.add(self.tab_clientes, text="  👥 Ingresar Clientes  ")
        self.notebook.add(self.tab_ordenes, text="  🛠️ Ingresar Órdenes de Servicio  ")
        self.notebook.add(self.tab_consultas, text="  🔍 Consultas y Gestión  ")

        self._armar_pestana_clientes()
        self._armar_pestana_ordenes()
        self._armar_pestana_consultas()

    # =========================================================================
    # PESTAÑA 1: INGRESO DE CLIENTES
    # =========================================================================
    def _armar_pestana_clientes(self) -> None:
        """Formulario y tabla para registro y visualización de clientes."""
        # Frame superior: Formulario
        f_form = ttk.LabelFrame(self.tab_clientes, text=" Formulario de Registro de Cliente ", padding=12)
        f_form.pack(fill=tk.X, side=tk.TOP, pady=(0, 10))

        # Columnas del formulario
        f_form.columnconfigure(1, weight=1)
        f_form.columnconfigure(3, weight=1)

        # Campos de Cliente
        ttk.Label(f_form, text="Identificación (ID):").grid(row=0, column=0, sticky="w", pady=4, padx=5)
        self.ent_cli_id = ttk.Entry(f_form, width=22)
        self.ent_cli_id.grid(row=0, column=1, sticky="ew", pady=4, padx=5)
        self.ent_cli_id.insert(0, "CLI-1004")

        ttk.Label(f_form, text="Nombre Completo:").grid(row=0, column=2, sticky="w", pady=4, padx=5)
        self.ent_cli_nombre = ttk.Entry(f_form, width=30)
        self.ent_cli_nombre.grid(row=0, column=3, sticky="ew", pady=4, padx=5)

        ttk.Label(f_form, text="Teléfono Móvil:").grid(row=1, column=0, sticky="w", pady=4, padx=5)
        self.ent_cli_tel = ttk.Entry(f_form, width=22)
        self.ent_cli_tel.grid(row=1, column=1, sticky="ew", pady=4, padx=5)

        ttk.Label(f_form, text="Correo Electrónico:").grid(row=1, column=2, sticky="w", pady=4, padx=5)
        self.ent_cli_email = ttk.Entry(f_form, width=30)
        self.ent_cli_email.grid(row=1, column=3, sticky="ew", pady=4, padx=5)

        ttk.Label(f_form, text="Ciudad:").grid(row=2, column=0, sticky="w", pady=4, padx=5)
        self.cb_cli_ciudad = ttk.Combobox(f_form, values=["Medellín", "Bogotá", "Cali", "Barranquilla", "Bucaramanga", "Pereira"])
        self.cb_cli_ciudad.grid(row=2, column=1, sticky="ew", pady=4, padx=5)
        self.cb_cli_ciudad.current(0)

        ttk.Label(f_form, text="Dirección:").grid(row=2, column=2, sticky="w", pady=4, padx=5)
        self.ent_cli_dir = ttk.Entry(f_form, width=30)
        self.ent_cli_dir.grid(row=2, column=3, sticky="ew", pady=4, padx=5)

        # Sección Embebida: Equipo Inicial del Cliente
        sep = ttk.Separator(f_form, orient="horizontal")
        sep.grid(row=3, column=0, columnspan=4, sticky="ew", pady=8)

        lbl_eq = ttk.Label(f_form, text="Datos del Equipo Propiedad del Cliente (Documento Embebido):", font=self.font_bold)
        lbl_eq.grid(row=4, column=0, columnspan=4, sticky="w", pady=(0, 4), padx=5)

        ttk.Label(f_form, text="Tipo de Equipo:").grid(row=5, column=0, sticky="w", pady=4, padx=5)
        self.cb_cli_eq_tipo = ttk.Combobox(f_form, values=["Laptop", "Workstation", "Servidor", "MacBook", "PC Escritorio", "Tablet Industrial"])
        self.cb_cli_eq_tipo.grid(row=5, column=1, sticky="ew", pady=4, padx=5)
        self.cb_cli_eq_tipo.current(0)

        ttk.Label(f_form, text="Marca y Modelo:").grid(row=5, column=2, sticky="w", pady=4, padx=5)
        self.ent_cli_eq_modelo = ttk.Entry(f_form, width=30)
        self.ent_cli_eq_modelo.grid(row=5, column=3, sticky="ew", pady=4, padx=5)

        ttk.Label(f_form, text="Número de Serie:").grid(row=6, column=0, sticky="w", pady=4, padx=5)
        self.ent_cli_eq_serial = ttk.Entry(f_form, width=22)
        self.ent_cli_eq_serial.grid(row=6, column=1, sticky="ew", pady=4, padx=5)

        # Botones de Acción
        f_btn = tk.Frame(f_form, bg=self.c_card)
        f_btn.grid(row=7, column=0, columnspan=4, sticky="e", pady=(10, 0))

        btn_limpiar = ttk.Button(f_btn, text="Limpiar Campos", style="Secondary.TButton", command=self._limpiar_form_cliente)
        btn_limpiar.pack(side=tk.RIGHT, padx=5)

        btn_guardar = ttk.Button(f_btn, text="💾 Guardar Cliente en MongoDB", style="Success.TButton", command=self._guardar_cliente)
        btn_guardar.pack(side=tk.RIGHT, padx=5)

        # Frame inferior: Tabla de clientes registrados
        f_tabla = ttk.LabelFrame(self.tab_clientes, text=" Clientes Registrados en la Base de Datos ", padding=8)
        f_tabla.pack(fill=tk.BOTH, expand=True)

        cols = ("id", "nombre", "ciudad", "telefono", "email", "equipos")
        self.tree_clientes = ttk.Treeview(f_tabla, columns=cols, show="headings", selectmode="browse")
        self.tree_clientes.heading("id", text="ID Cliente")
        self.tree_clientes.heading("nombre", text="Nombre Completo")
        self.tree_clientes.heading("ciudad", text="Ciudad")
        self.tree_clientes.heading("telefono", text="Teléfono")
        self.tree_clientes.heading("email", text="Email")
        self.tree_clientes.heading("equipos", text="Equipos Registrados")

        self.tree_clientes.column("id", width=95, anchor="center")
        self.tree_clientes.column("nombre", width=220)
        self.tree_clientes.column("ciudad", width=110, anchor="center")
        self.tree_clientes.column("telefono", width=120, anchor="center")
        self.tree_clientes.column("email", width=200)
        self.tree_clientes.column("equipos", width=130, anchor="center")

        scroll_y = ttk.Scrollbar(f_tabla, orient=tk.VERTICAL, command=self.tree_clientes.yview)
        self.tree_clientes.configure(yscrollcommand=scroll_y.set)

        self.tree_clientes.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

    def _guardar_cliente(self) -> None:
        """Valida y guarda un nuevo cliente en la colección 'clientes'."""
        if not self.crud:
            messagebox.showerror("Error", "No hay conexión activa con MongoDB.")
            return

        ident = self.ent_cli_id.get().strip()
        nombre = self.ent_cli_nombre.get().strip()

        if not ident or not nombre:
            messagebox.showwarning("Campos Requeridos", "Debe indicar al menos la Identificación y el Nombre Completo.")
            return

        nuevo_cliente = {
            "identificacion": ident,
            "tipo_cliente": "PERSONA_NATURAL",
            "nombre_completo": nombre,
            "contacto": {
                "telefono": self.ent_cli_tel.get().strip() or "No especificado",
                "email": self.ent_cli_email.get().strip() or "contacto@techcare.com",
                "ciudad": self.cb_cli_ciudad.get().strip(),
                "direccion": self.ent_cli_dir.get().strip() or "No especificada"
            },
            "equipos": []
        }

        # Si especificó equipo, se agrega como embebido
        eq_modelo = self.ent_cli_eq_modelo.get().strip()
        if eq_modelo:
            nuevo_cliente["equipos"].append({
                "numero_serie": self.ent_cli_eq_serial.get().strip() or "SN-PENDIENTE",
                "tipo_equipo": self.cb_cli_eq_tipo.get().strip(),
                "marca_modelo": eq_modelo,
                "fecha_adquisicion": "2026-01-15"
            })

        try:
            doc_id = self.crud.create_cliente(nuevo_cliente)
            if doc_id:
                messagebox.showinfo("Éxito", f"¡Cliente '{nombre}' guardado exitosamente en MongoDB!\n_id: {doc_id}")
                self._notificar(f"Cliente '{ident}' ({nombre}) registrado en MongoDB.")
                self._limpiar_form_cliente()
                self._cargar_tabla_clientes()
                self._actualizar_combos_clientes()
            else:
                messagebox.showwarning("Atención", f"El cliente '{ident}' ya existe o no se pudo insertar.")
        except Exception as e:
            messagebox.showerror("Error al Guardar", f"Detalle técnico: {e}")

    def _limpiar_form_cliente(self) -> None:
        """Limpia los campos del formulario de cliente."""
        self.ent_cli_id.delete(0, tk.END)
        self.ent_cli_nombre.delete(0, tk.END)
        self.ent_cli_tel.delete(0, tk.END)
        self.ent_cli_email.delete(0, tk.END)
        self.ent_cli_dir.delete(0, tk.END)
        self.ent_cli_eq_modelo.delete(0, tk.END)
        self.ent_cli_eq_serial.delete(0, tk.END)
        self.ent_cli_id.insert(0, "CLI-1005")

    # =========================================================================
    # PESTAÑA 2: INGRESO DE ÓRDENES DE SERVICIO
    # =========================================================================
    def _armar_pestana_ordenes(self) -> None:
        """Formulario y tabla para registro de órdenes de servicio técnico."""
        f_form = ttk.LabelFrame(self.tab_ordenes, text=" Formulario de Registro de Orden de Servicio Técnico ", padding=12)
        f_form.pack(fill=tk.X, side=tk.TOP, pady=(0, 10))

        f_form.columnconfigure(1, weight=1)
        f_form.columnconfigure(3, weight=1)

        # Campos Principales
        ttk.Label(f_form, text="Código de Orden:").grid(row=0, column=0, sticky="w", pady=4, padx=5)
        self.ent_ord_codigo = ttk.Entry(f_form, width=22)
        self.ent_ord_codigo.grid(row=0, column=1, sticky="ew", pady=4, padx=5)
        self.ent_ord_codigo.insert(0, "ORD-2026-004")

        ttk.Label(f_form, text="Cliente Asignado (ID):").grid(row=0, column=2, sticky="w", pady=4, padx=5)
        self.cb_ord_cliente_id = ttk.Combobox(f_form, values=["CLI-1001", "CLI-1002", "CLI-1003"])
        self.cb_ord_cliente_id.grid(row=0, column=3, sticky="ew", pady=4, padx=5)
        self.cb_ord_cliente_id.current(0)

        ttk.Label(f_form, text="Técnico Responsable:").grid(row=1, column=0, sticky="w", pady=4, padx=5)
        self.ent_ord_tecnico = ttk.Entry(f_form, width=22)
        self.ent_ord_tecnico.grid(row=1, column=1, sticky="ew", pady=4, padx=5)
        self.ent_ord_tecnico.insert(0, "Ing. Laura Marcela Ríos")

        ttk.Label(f_form, text="Prioridad:").grid(row=1, column=2, sticky="w", pady=4, padx=5)
        self.cb_ord_prioridad = ttk.Combobox(f_form, values=["ALTA", "MEDIA", "BAJA"])
        self.cb_ord_prioridad.grid(row=1, column=3, sticky="ew", pady=4, padx=5)
        self.cb_ord_prioridad.current(1)

        ttk.Label(f_form, text="Estado Inicial:").grid(row=2, column=0, sticky="w", pady=4, padx=5)
        self.cb_ord_estado = ttk.Combobox(f_form, values=["RECIBIDO", "EN_DIAGNOSTICO", "EN_REPARACION"])
        self.cb_ord_estado.grid(row=2, column=1, sticky="ew", pady=4, padx=5)
        self.cb_ord_estado.current(0)

        ttk.Label(f_form, text="Costo Diagnóstico / Base ($):").grid(row=2, column=2, sticky="w", pady=4, padx=5)
        self.ent_ord_costo = ttk.Entry(f_form, width=30)
        self.ent_ord_costo.grid(row=2, column=3, sticky="ew", pady=4, padx=5)
        self.ent_ord_costo.insert(0, "50000")

        # Sección Embebida: Equipo a reparar
        sep = ttk.Separator(f_form, orient="horizontal")
        sep.grid(row=3, column=0, columnspan=4, sticky="ew", pady=8)

        lbl_eq = ttk.Label(f_form, text="Datos del Equipo a Reparar (Documento Embebido en la Orden):", font=self.font_bold)
        lbl_eq.grid(row=4, column=0, columnspan=4, sticky="w", pady=(0, 4), padx=5)

        ttk.Label(f_form, text="Tipo de Equipo:").grid(row=5, column=0, sticky="w", pady=4, padx=5)
        self.cb_ord_eq_tipo = ttk.Combobox(f_form, values=["Laptop", "Workstation", "Servidor", "MacBook", "PC Escritorio"])
        self.cb_ord_eq_tipo.grid(row=5, column=1, sticky="ew", pady=4, padx=5)
        self.cb_ord_eq_tipo.current(0)

        ttk.Label(f_form, text="Marca y Modelo:").grid(row=5, column=2, sticky="w", pady=4, padx=5)
        self.ent_ord_eq_modelo = ttk.Entry(f_form, width=30)
        self.ent_ord_eq_modelo.grid(row=5, column=3, sticky="ew", pady=4, padx=5)
        self.ent_ord_eq_modelo.insert(0, "ThinkPad X1 Carbon Gen 10")

        ttk.Label(f_form, text="Número de Serie:").grid(row=6, column=0, sticky="w", pady=4, padx=5)
        self.ent_ord_eq_serial = ttk.Entry(f_form, width=22)
        self.ent_ord_eq_serial.grid(row=6, column=1, sticky="ew", pady=4, padx=5)
        self.ent_ord_eq_serial.insert(0, "SN-X1-99881")

        ttk.Label(f_form, text="Falla Reportada:").grid(row=6, column=2, sticky="w", pady=4, padx=5)
        self.ent_ord_eq_falla = ttk.Entry(f_form, width=30)
        self.ent_ord_eq_falla.grid(row=6, column=3, sticky="ew", pady=4, padx=5)
        self.ent_ord_eq_falla.insert(0, "No enciende tras actualización de BIOS")

        # Botones de Acción
        f_btn = tk.Frame(f_form, bg=self.c_card)
        f_btn.grid(row=7, column=0, columnspan=4, sticky="e", pady=(10, 0))

        btn_limpiar = ttk.Button(f_btn, text="Limpiar Campos", style="Secondary.TButton", command=self._limpiar_form_orden)
        btn_limpiar.pack(side=tk.RIGHT, padx=5)

        btn_guardar = ttk.Button(f_btn, text="💾 Guardar Orden en MongoDB", style="Success.TButton", command=self._guardar_orden)
        btn_guardar.pack(side=tk.RIGHT, padx=5)

        # Frame inferior: Tabla de órdenes
        f_tabla = ttk.LabelFrame(self.tab_ordenes, text=" Órdenes Registradas en MongoDB ", padding=8)
        f_tabla.pack(fill=tk.BOTH, expand=True)

        cols = ("codigo", "cliente", "estado", "prioridad", "tecnico", "equipo", "costo")
        self.tree_ordenes = ttk.Treeview(f_tabla, columns=cols, show="headings", selectmode="browse")
        self.tree_ordenes.heading("codigo", text="Código")
        self.tree_ordenes.heading("cliente", text="Cliente ID")
        self.tree_ordenes.heading("estado", text="Estado")
        self.tree_ordenes.heading("prioridad", text="Prioridad")
        self.tree_ordenes.heading("tecnico", text="Técnico")
        self.tree_ordenes.heading("equipo", text="Equipo / Modelo")
        self.tree_ordenes.heading("costo", text="Costo Total")

        self.tree_ordenes.column("codigo", width=110, anchor="center")
        self.tree_ordenes.column("cliente", width=95, anchor="center")
        self.tree_ordenes.column("estado", width=120, anchor="center")
        self.tree_ordenes.column("prioridad", width=90, anchor="center")
        self.tree_ordenes.column("tecnico", width=160)
        self.tree_ordenes.column("equipo", width=190)
        self.tree_ordenes.column("costo", width=110, anchor="e")

        scroll_y = ttk.Scrollbar(f_tabla, orient=tk.VERTICAL, command=self.tree_ordenes.yview)
        self.tree_ordenes.configure(yscrollcommand=scroll_y.set)

        self.tree_ordenes.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

    def _guardar_orden(self) -> None:
        """Valida y guarda una nueva orden de servicio técnico en MongoDB."""
        if not self.crud:
            messagebox.showerror("Error", "No hay conexión activa con MongoDB.")
            return

        codigo = self.ent_ord_codigo.get().strip()
        cliente_id = self.cb_ord_cliente_id.get().strip()

        if not codigo or not cliente_id:
            messagebox.showwarning("Campos Requeridos", "Debe ingresar el código de la orden y el cliente asignado.")
            return

        try:
            costo = float(self.ent_ord_costo.get().strip() or "0")
        except ValueError:
            messagebox.showwarning("Formato Inválido", "El costo debe ser un número válido.")
            return

        estado_inicial = self.cb_ord_estado.get().strip()
        tecnico = self.ent_ord_tecnico.get().strip() or "Técnico de Turno"

        nueva_orden = {
            "codigo_orden": codigo,
            "cliente_identificacion": cliente_id,
            "datos_equipo": {
                "numero_serie": self.ent_ord_eq_serial.get().strip() or "SN-DESCONOCIDO",
                "tipo_equipo": self.cb_ord_eq_tipo.get().strip(),
                "modelo": self.ent_ord_eq_modelo.get().strip() or "Equipo Genérico",
                "falla_reportada": self.ent_ord_eq_falla.get().strip() or "Revisión general"
            },
            "tecnico_asignado": tecnico,
            "estado": estado_inicial,
            "prioridad": self.cb_ord_prioridad.get().strip(),
            "checklist_diagnostico": [
                {"item": "Inspección visual inicial", "aprobado": True, "observaciones": "Recepción conforme"},
                {"item": "Prueba de encendido y POST", "aprobado": False, "observaciones": "Falla confirmada"}
            ],
            "repuestos_utilizados": [],
            "costo_total": costo,
            "historial_estados": [
                {
                    "estado": estado_inicial,
                    "fecha": "2026-11-05T15:00:00Z",
                    "responsable": tecnico,
                    "nota": "Ingreso registrado desde interfaz gráfica TechCare"
                }
            ]
        }

        try:
            doc_id = self.crud.create_orden(nueva_orden)
            if doc_id:
                messagebox.showinfo("Éxito", f"¡Orden '{codigo}' guardada con éxito en MongoDB!\n_id: {doc_id}")
                self._notificar(f"Orden '{codigo}' guardada en MongoDB.")
                self._limpiar_form_orden()
                self._cargar_tabla_ordenes()
                self._cargar_tabla_consultas()
            else:
                messagebox.showwarning("Atención", f"La orden '{codigo}' ya existe o no se pudo insertar.")
        except Exception as e:
            messagebox.showerror("Error al Guardar", f"Detalle técnico: {e}")

    def _limpiar_form_orden(self) -> None:
        """Limpia los campos del formulario de orden."""
        self.ent_ord_codigo.delete(0, tk.END)
        self.ent_ord_eq_modelo.delete(0, tk.END)
        self.ent_ord_eq_serial.delete(0, tk.END)
        self.ent_ord_eq_falla.delete(0, tk.END)
        self.ent_ord_codigo.insert(0, "ORD-2026-005")

    # =========================================================================
    # PESTAÑA 3: CONSULTAS, GESTIÓN Y SEED DATA
    # =========================================================================
    def _armar_pestana_consultas(self) -> None:
        """Herramientas de búsqueda, filtrado, carga de semilla y actualización de estado."""
        # Barra de Control Superior
        f_top = ttk.LabelFrame(self.tab_consultas, text=" Filtros de Consulta y Acciones Globales ", padding=10)
        f_top.pack(fill=tk.X, side=tk.TOP, pady=(0, 10))

        # Semilla y Refrescar
        btn_seed = ttk.Button(f_top, text="🌱 Cargar Datos Semilla (seed_data.json)", style="Primary.TButton", command=self._cargar_seed_data)
        btn_seed.pack(side=tk.LEFT, padx=(0, 10))

        btn_refrescar = ttk.Button(f_top, text="🔄 Refrescar Todo", style="Secondary.TButton", command=self._refrescar_todo)
        btn_refrescar.pack(side=tk.LEFT, padx=(0, 15))

        # Filtro por estado
        ttk.Label(f_top, text="Filtrar por Estado:").pack(side=tk.LEFT, padx=(10, 4))
        self.cb_filtro_estado = ttk.Combobox(
            f_top,
            values=["TODAS", "RECIBIDO", "EN_DIAGNOSTICO", "EN_REPARACION", "COMPLETADO", "ENTREGADO"],
            width=16,
            state="readonly"
        )
        self.cb_filtro_estado.current(0)
        self.cb_filtro_estado.pack(side=tk.LEFT, padx=4)

        btn_filtrar = ttk.Button(f_top, text="Aplicar Filtro", style="Secondary.TButton", command=self._filtrar_ordenes_estado)
        btn_filtrar.pack(side=tk.LEFT, padx=6)

        # Búsqueda por código
        ttk.Label(f_top, text="Buscar Código:").pack(side=tk.LEFT, padx=(15, 4))
        self.ent_buscar_codigo = ttk.Entry(f_top, width=15)
        self.ent_buscar_codigo.pack(side=tk.LEFT, padx=4)

        btn_buscar = ttk.Button(f_top, text="Buscar", style="Secondary.TButton", command=self._buscar_orden_codigo)
        btn_buscar.pack(side=tk.LEFT, padx=4)

        # Panel Central: Tabla de Órdenes y Panel Lateral de Detalle / Actualización
        f_centro = tk.Frame(self.tab_consultas, bg=self.c_bg)
        f_centro.pack(fill=tk.BOTH, expand=True)

        # Lado Izquierdo: Tabla
        f_tabla_box = ttk.LabelFrame(f_centro, text=" Resultados de Órdenes en MongoDB (Seleccione una fila) ", padding=8)
        f_tabla_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        cols = ("codigo", "cliente", "estado", "equipo", "costo")
        self.tree_consultas = ttk.Treeview(f_tabla_box, columns=cols, show="headings", selectmode="browse")
        self.tree_consultas.heading("codigo", text="Código")
        self.tree_consultas.heading("cliente", text="Cliente ID")
        self.tree_consultas.heading("estado", text="Estado")
        self.tree_consultas.heading("equipo", text="Equipo")
        self.tree_consultas.heading("costo", text="Costo Total")

        self.tree_consultas.column("codigo", width=105, anchor="center")
        self.tree_consultas.column("cliente", width=90, anchor="center")
        self.tree_consultas.column("estado", width=115, anchor="center")
        self.tree_consultas.column("equipo", width=170)
        self.tree_consultas.column("costo", width=95, anchor="e")

        scroll_c = ttk.Scrollbar(f_tabla_box, orient=tk.VERTICAL, command=self.tree_consultas.yview)
        self.tree_consultas.configure(yscrollcommand=scroll_c.set)

        self.tree_consultas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_c.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree_consultas.bind("<<TreeviewSelect>>", self._al_seleccionar_orden)

        # Lado Derecho: Panel de Actualización Rápida y Visor JSON
        f_derecho = ttk.LabelFrame(f_centro, text=" Detalle del Documento y Actualización ", padding=10, width=380)
        f_derecho.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False)

        # Subpanel de actualización de estado
        f_act = tk.Frame(f_derecho, bg=self.c_card)
        f_act.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(f_act, text="Nuevo Estado:", font=self.font_bold).grid(row=0, column=0, sticky="w", pady=2)
        self.cb_nuevo_estado = ttk.Combobox(
            f_act,
            values=["RECIBIDO", "EN_DIAGNOSTICO", "EN_REPARACION", "COMPLETADO", "ENTREGADO"],
            width=16,
            state="readonly"
        )
        self.cb_nuevo_estado.current(3)
        self.cb_nuevo_estado.grid(row=0, column=1, sticky="ew", padx=5, pady=2)

        btn_act = ttk.Button(f_act, text="⚡ Actualizar Estado ($set y $push)", style="Primary.TButton", command=self._actualizar_estado_seleccionado)
        btn_act.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 2))

        # Visor de JSON
        ttk.Label(f_derecho, text="Documento BSON / JSON en MongoDB:", font=self.font_bold).pack(anchor="w", pady=(8, 2))
        self.txt_json = tk.Text(f_derecho, width=42, height=18, font=self.font_mono, bg="#0F172A", fg="#38BDF8", relief="solid", bd=1)
        self.txt_json.pack(fill=tk.BOTH, expand=True)
        self.txt_json.insert("1.0", "// Seleccione una orden de la lista para inspeccionar su documento...")

    def _al_seleccionar_orden(self, event=None) -> None:
        """Muestra el documento JSON completo de la orden seleccionada."""
        seleccion = self.tree_consultas.selection()
        if not seleccion or not self.crud:
            return

        item = self.tree_consultas.item(seleccion[0])
        codigo = item["values"][0]

        orden_doc = self.crud.read_orden_by_codigo(str(codigo))
        if orden_doc:
            self.txt_json.delete("1.0", tk.END)
            try:
                from bson import json_util
                txt = json.dumps(json.loads(json_util.dumps(orden_doc)), indent=2, ensure_ascii=False)
            except Exception:
                txt = json.dumps(orden_doc, indent=2, ensure_ascii=False, default=str)
            self.txt_json.insert("1.0", txt)

    def _actualizar_estado_seleccionado(self) -> None:
        """Actualiza el estado de la orden seleccionada aplicando operadores atómicos."""
        seleccion = self.tree_consultas.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Debe seleccionar primero una orden en la tabla izquierda.")
            return

        item = self.tree_consultas.item(seleccion[0])
        codigo = str(item["values"][0])
        nuevo_est = self.cb_nuevo_estado.get()

        try:
            exito = self.crud.update_orden_estado(
                codigo_orden=codigo,
                nuevo_estado=nuevo_est,
                responsable="Operador GUI TechCare",
                nota=f"Estado actualizado a '{nuevo_est}' mediante interfaz gráfica."
            )
            if exito:
                messagebox.showinfo("Actualización Exitosa", f"Orden '{codigo}' actualizada a estado '{nuevo_est}' con trazabilidad atómica.")
                self._notificar(f"Orden '{codigo}' actualizada a '{nuevo_est}'.")
                self._cargar_tabla_consultas()
                self._cargar_tabla_ordenes()
                # Re-seleccionar para actualizar el visor JSON
                orden_actualizada = self.crud.read_orden_by_codigo(codigo)
                if orden_actualizada:
                    self.txt_json.delete("1.0", tk.END)
                    self.txt_json.insert("1.0", json.dumps(orden_actualizada, indent=2, ensure_ascii=False, default=str))
        except Exception as e:
            messagebox.showerror("Error al Actualizar", f"No se pudo actualizar el estado: {e}")

    def _filtrar_ordenes_estado(self) -> None:
        """Filtra la tabla de consultas según el estado seleccionado."""
        if not self.crud:
            return
        estado = self.cb_filtro_estado.get()
        if estado == "TODAS":
            self._cargar_tabla_consultas()
            return

        resultados = self.crud.read_ordenes_by_filtro({"estado": estado})
        self._llenar_tabla_consultas(resultados)
        self._notificar(f"Filtro aplicado por estado '{estado}': {len(resultados)} orden(es) encontrada(s).")

    def _buscar_orden_codigo(self) -> None:
        """Busca una orden puntual por su código identificador."""
        if not self.crud:
            return
        codigo = self.ent_buscar_codigo.get().strip()
        if not codigo:
            self._cargar_tabla_consultas()
            return

        orden = self.crud.read_orden_by_codigo(codigo)
        if orden:
            self._llenar_tabla_consultas([orden])
            self._notificar(f"Orden '{codigo}' encontrada con éxito.")
        else:
            self._llenar_tabla_consultas([])
            self._notificar(f"No se encontró ninguna orden con el código '{codigo}'.")
            messagebox.showinfo("Búsqueda", f"No se encontró la orden '{codigo}' en MongoDB.")

    def _cargar_seed_data(self) -> None:
        """Carga los datos iniciales desde seed_data.json a MongoDB."""
        if not self.crud:
            messagebox.showerror("Error", "No hay conexión activa con MongoDB.")
            return

        ruta_seed = os.path.join(os.path.dirname(__file__), "data", "seed_data.json")
        if not os.path.exists(ruta_seed):
            messagebox.showerror("Archivo No Encontrado", f"No se encontró el archivo: {ruta_seed}")
            return

        try:
            with open(ruta_seed, "r", encoding="utf-8") as f:
                datos = json.load(f)

            c_insertados = self.crud.create_clientes_bulk(datos.get("clientes", []))
            o_insertados = self.crud.create_ordenes_bulk(datos.get("ordenes_servicio", []))

            msg = f"Carga de Semilla Finalizada:\n• Clientes nuevos insertados: {len(c_insertados)}\n• Órdenes nuevas insertadas: {len(o_insertados)}"
            messagebox.showinfo("Carga Semilla Exitosa", msg)
            self._refrescar_todo()
            self._notificar("Datos semilla cargados en MongoDB con éxito.")
        except Exception as e:
            messagebox.showerror("Error al Cargar Semilla", f"Detalle: {e}")

    # =========================================================================
    # CONEXIÓN Y SINCRONIZACIÓN DE DATOS
    # =========================================================================
    def _iniciar_conexion(self) -> None:
        """Conecta con MongoDB e inicializa las colecciones en las tablas."""
        try:
            self.db_mgr.connect()
            self.crud = CrudMaster(db_manager=self.db_mgr)
            is_mock = (
                self.db_mgr.is_mock_active()
                if hasattr(self.db_mgr, "is_mock_active")
                else getattr(self.db_mgr, "_is_mock", False)
            )

            if is_mock:
                self.lbl_status.config(text="🟡 Modo Simulación (Mock)", fg="#F59E0B")
                self._notificar("Conectado en Modo Mock (Simulación en memoria).")
            else:
                self.lbl_status.config(text="🟢 Conectado a MongoDB (techcare_db @ 27017)", fg="#4ADE80")
                self._notificar("Conectado exitosamente a MongoDB Server real.")

            self._refrescar_todo()

        except Exception as err:
            self.lbl_status.config(text="🔴 Error de Conexión", fg="#F87171")
            self._notificar(f"Error al conectar con MongoDB: {err}")
            messagebox.showerror(
                "Error de Conexión a MongoDB",
                f"No se pudo conectar a MongoDB en localhost:27017.\n\nDetalle: {err}\n\nAsegúrate de tener iniciado el servicio de MongoDB."
            )

    def _refrescar_todo(self) -> None:
        """Recarga todas las tablas y listas desplegables desde MongoDB."""
        self._cargar_tabla_clientes()
        self._cargar_tabla_ordenes()
        self._cargar_tabla_consultas()
        self._actualizar_combos_clientes()
        self._notificar("Tablas y datos actualizados en tiempo real desde MongoDB.")

    def _cargar_tabla_clientes(self) -> None:
        """Carga los registros de clientes en su Treeview."""
        if not self.crud:
            return
        for item in self.tree_clientes.get_children():
            self.tree_clientes.delete(item)

        clientes = self.crud.read_all_clientes()
        for c in clientes:
            eq_count = len(c.get("equipos", []))
            cont = c.get("contacto", {})
            self.tree_clientes.insert(
                "",
                tk.END,
                values=(
                    c.get("identificacion", ""),
                    c.get("nombre_completo", ""),
                    cont.get("ciudad", ""),
                    cont.get("telefono", ""),
                    cont.get("email", ""),
                    f"{eq_count} equipo(s)"
                )
            )

    def _cargar_tabla_ordenes(self) -> None:
        """Carga las órdenes en la tabla de la pestaña de órdenes."""
        if not self.crud:
            return
        for item in self.tree_ordenes.get_children():
            self.tree_ordenes.delete(item)

        ordenes = self.crud.read_all_ordenes()
        for o in ordenes:
            eq = o.get("datos_equipo", {})
            equipo_str = f"{eq.get('tipo_equipo', '')} {eq.get('modelo', '')}".strip()
            self.tree_ordenes.insert(
                "",
                tk.END,
                values=(
                    o.get("codigo_orden", ""),
                    o.get("cliente_identificacion", ""),
                    o.get("estado", ""),
                    o.get("prioridad", ""),
                    o.get("tecnico_asignado", ""),
                    equipo_str,
                    f"${o.get('costo_total', 0):,.2f}"
                )
            )

    def _cargar_tabla_consultas(self) -> None:
        """Carga todas las órdenes en la tabla de la pestaña de consultas."""
        if not self.crud:
            return
        ordenes = self.crud.read_all_ordenes()
        self._llenar_tabla_consultas(ordenes)

    def _llenar_tabla_consultas(self, lista_ordenes: List[Dict[str, Any]]) -> None:
        """Llena el Treeview de consultas con la lista provista."""
        for item in self.tree_consultas.get_children():
            self.tree_consultas.delete(item)

        for o in lista_ordenes:
            eq = o.get("datos_equipo", {})
            equipo_str = f"{eq.get('tipo_equipo', '')} {eq.get('modelo', '')}".strip()
            self.tree_consultas.insert(
                "",
                tk.END,
                values=(
                    o.get("codigo_orden", ""),
                    o.get("cliente_identificacion", ""),
                    o.get("estado", ""),
                    equipo_str,
                    f"${o.get('costo_total', 0):,.2f}"
                )
            )

    def _actualizar_combos_clientes(self) -> None:
        """Actualiza la lista de selección de clientes en el formulario de órdenes."""
        if not self.crud:
            return
        clientes = self.crud.read_all_clientes()
        ids = [c.get("identificacion", "") for c in clientes if c.get("identificacion")]
        if ids:
            self.cb_ord_cliente_id["values"] = ids
            if not self.cb_ord_cliente_id.get() or self.cb_ord_cliente_id.get() not in ids:
                self.cb_ord_cliente_id.current(0)

    def _notificar(self, mensaje: str) -> None:
        """Actualiza el texto de la barra de estado inferior."""
        self.status_bar.config(text=f"ℹ️ {mensaje}")


def lanzar_gui() -> None:
    """Función de entrada para ejecutar la interfaz gráfica."""
    root = tk.Tk()
    app = TechCareGUI(root)
    root.mainloop()


if __name__ == "__main__":
    lanzar_gui()


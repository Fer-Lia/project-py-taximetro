import logging
import time
import tkinter as tk
from tkinter import messagebox, simpledialog

from taximetro import autenticacion, config, historial
from taximetro.carrera import Carrera
from taximetro.tarifas import ESTADO_MOVIMIENTO, ESTADO_PARADO

INTENTOS_MAXIMOS = 3
INTERVALO_MS = 200
ANCHO_VENTANA = 480
ALTO_VENTANA = 680
MARGEN_SUPERIOR = 10
COLOR_LIBRE = "#cccccc"
COLOR_PARADO = "#e57373"
COLOR_MOVIMIENTO = "#81c784"


def pedir_contrasena(ventana: tk.Tk, mensaje: str) -> str | None:
    return simpledialog.askstring("Acceso", mensaje, show="*", parent=ventana)


def crear_contrasena(ventana: tk.Tk) -> bool:
    contrasena = pedir_contrasena(ventana, "Primera vez: crea la contraseña")
    if not contrasena:
        return False
    if contrasena != pedir_contrasena(ventana, "Repite la contraseña"):
        messagebox.showerror("Acceso", "Las contraseñas no coinciden.")
        return False
    autenticacion.guardar_contrasena(contrasena)
    logging.info("Contraseña creada")
    return True


def iniciar_sesion(ventana: tk.Tk) -> bool:
    for _ in range(INTENTOS_MAXIMOS):
        contrasena = pedir_contrasena(ventana, "Contraseña")
        if contrasena is None:
            return False
        if autenticacion.verificar_contrasena(contrasena):
            logging.info("Acceso concedido")
            return True
        messagebox.showerror("Acceso", "Contraseña incorrecta.")
    logging.error("Acceso denegado tras %s intentos", INTENTOS_MAXIMOS)
    return False


def acceder(ventana: tk.Tk) -> bool:
    try:
        if autenticacion.existe_contrasena():
            return iniciar_sesion(ventana)
        return crear_contrasena(ventana)
    except (OSError, ValueError, KeyError) as error:
        logging.error("Error de autenticación: %s", error)
        messagebox.showerror("Acceso", "No se pudo comprobar la contraseña.")
        return False


class Aplicacion:
    def __init__(self, ventana: tk.Tk, tarifas: dict) -> None:
        self.ventana = ventana
        self.tarifas = tarifas
        self.carrera = None

        ventana.title("Taxímetro Digital")
        posicion_x = (ventana.winfo_screenwidth() - ANCHO_VENTANA) // 2
        ventana.geometry(f"{ANCHO_VENTANA}x{ALTO_VENTANA}+{posicion_x}+{MARGEN_SUPERIOR}")

        self.etiqueta_estado = tk.Label(ventana, font=("Arial", 32, "bold"), pady=24)
        self.etiqueta_estado.pack(fill="x")

        self.etiqueta_importe = tk.Label(ventana, font=("Arial", 56, "bold"), pady=16)
        self.etiqueta_importe.pack(fill="x")

        self.boton_iniciar = self.crear_boton("Iniciar carrera", self.iniciar)
        self.boton_parado = self.crear_boton(
            "Parado", lambda: self.cambiar_estado(ESTADO_PARADO)
        )
        self.boton_movimiento = self.crear_boton(
            "En movimiento", lambda: self.cambiar_estado(ESTADO_MOVIMIENTO)
        )
        self.boton_finalizar = self.crear_boton("Finalizar carrera", self.finalizar)

        self.refrescar()
        self.actualizar_importe()

    def crear_boton(self, texto: str, accion) -> tk.Button:
        boton = tk.Button(
            self.ventana, text=texto, command=accion, font=("Arial", 24, "bold"), height=2
        )
        boton.pack(fill="x", padx=20, pady=6)
        return boton

    def iniciar(self) -> None:
        self.carrera = Carrera(time.time(), self.tarifas)
        logging.info("Carrera iniciada")
        self.refrescar()

    def cambiar_estado(self, estado: str) -> None:
        self.carrera.cambiar_estado(estado, time.time())
        logging.info("Cambio de estado: %s", estado)
        self.refrescar()

    def finalizar(self) -> None:
        ahora = time.time()
        duracion = ahora - self.carrera.hora_inicio
        total = self.carrera.finalizar(ahora)
        logging.info("Carrera finalizada: %.0f s, %.2f EUR", duracion, total)
        try:
            historial.guardar_carrera(self.carrera.hora_inicio, duracion, total)
        except OSError as error:
            logging.error("No se pudo guardar la carrera: %s", error)
            messagebox.showwarning("Aviso", "No se pudo guardar la carrera en el historial.")
        self.carrera = None
        self.refrescar()
        messagebox.showinfo("Carrera finalizada", f"Total a cobrar: {total:.2f} €")

    def refrescar(self) -> None:
        if self.carrera is None:
            texto, color = "SIN CARRERA", COLOR_LIBRE
        elif self.carrera.estado == ESTADO_MOVIMIENTO:
            texto, color = "EN MOVIMIENTO", COLOR_MOVIMIENTO
        else:
            texto, color = "PARADO", COLOR_PARADO
        self.etiqueta_estado.config(text=texto, bg=color)

        en_curso = self.carrera is not None
        activo = tk.NORMAL if en_curso else tk.DISABLED
        self.boton_iniciar.config(state=tk.DISABLED if en_curso else tk.NORMAL)
        self.boton_parado.config(state=activo)
        self.boton_movimiento.config(state=activo)
        self.boton_finalizar.config(state=activo)

    def actualizar_importe(self) -> None:
        if self.carrera is None:
            importe = 0.0
        else:
            importe = self.carrera.importe_actual(time.time())
        self.etiqueta_importe.config(text=f"{importe:.2f} €")
        self.ventana.after(INTERVALO_MS, self.actualizar_importe)


def ejecutar() -> None:
    logging.info("Programa iniciado (interfaz gráfica)")
    ventana = tk.Tk()
    ventana.withdraw()
    if not acceder(ventana):
        ventana.destroy()
        return
    try:
        tarifas = config.cargar_tarifas()
    except (OSError, ValueError, KeyError) as error:
        logging.error("No se pudieron cargar las tarifas: %s", error)
        messagebox.showerror(
            "Error", "No se pudieron cargar las tarifas. Revisa config/tarifas.json."
        )
        ventana.destroy()
        return
    ventana.deiconify()
    Aplicacion(ventana, tarifas)
    ventana.mainloop()

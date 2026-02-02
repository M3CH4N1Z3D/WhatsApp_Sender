import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog, filedialog
import threading
import os
import sys
import subprocess
import uuid
from bot import WhatsAppBot
import config

# --- SEGURIDAD ---
CONTRASEÑA_MAESTRA = "G0l14th903$"
ARCHIVO_TOKEN = os.path.join(config.BASE_DIR, "auth.token")

def obtener_id_pc():
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        cmd = 'wmic csproduct get uuid'
        resultado = subprocess.check_output(cmd, startupinfo=startupinfo, shell=False).decode()
        serial = resultado.split('\n')[1].strip()
        if serial and "FFFF" not in serial: return serial
    except: pass
    try: return str(uuid.getnode())
    except: return "GENERIC_ID"

class AppWhatsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🤖 SPM INTEGRAL - Bot WhatsApp")
        self.root.geometry("600x600")
        self.root.resizable(False, False)

        self.bot = None
        self.thread = None
        self.ruta_imagen = None 

        # INTERFAZ
        frame_input = tk.Frame(root, pady=10)
        frame_input.pack()
        
        tk.Label(frame_input, text="Nombre Grupo (Excel):", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT, padx=5)
        self.entry_grupo = tk.Entry(frame_input, width=25, font=("Segoe UI", 11))
        self.entry_grupo.pack(side=tk.LEFT, padx=5)

        # Sección Imagen
        frame_img = tk.Frame(root, pady=5)
        frame_img.pack()
        self.btn_img = tk.Button(frame_img, text="📷 Adjuntar Imagen (Opcional)", command=self.seleccionar_imagen, bg="#E0E0E0")
        self.btn_img.pack(side=tk.LEFT, padx=5)
        self.lbl_img = tk.Label(frame_img, text="Ninguna seleccionada", fg="gray", font=("Segoe UI", 8))
        self.lbl_img.pack(side=tk.LEFT, padx=5)

        # Botones Principales
        frame_btns = tk.Frame(root, pady=10)
        frame_btns.pack()

        self.btn_iniciar = tk.Button(frame_btns, text="🚀 INICIAR CAMPAÑA", bg="#2E7D32", fg="white", font=("Segoe UI", 10, "bold"), command=self.iniciar_campana, width=20)
        self.btn_iniciar.pack(side=tk.LEFT, padx=5)

        self.btn_login = tk.Button(frame_btns, text="📱 YA ESCANEÉ EL QR", bg="#1976D2", fg="white", font=("Segoe UI", 10, "bold"), state=tk.DISABLED, command=self.confirmar_login, width=20)
        self.btn_login.pack(side=tk.LEFT, padx=5)

        # Controles
        frame_ctrl = tk.Frame(root, pady=10)
        frame_ctrl.pack()

        self.btn_pausa = tk.Button(frame_ctrl, text="⏸️ PAUSAR", bg="#FFA000", width=15, state=tk.DISABLED, command=self.toggle_pausa)
        self.btn_pausa.pack(side=tk.LEFT, padx=5)

        self.btn_stop = tk.Button(frame_ctrl, text="🛑 DETENER", bg="#D32F2F", fg="white", width=15, state=tk.DISABLED, command=self.detener_bot)
        self.btn_stop.pack(side=tk.LEFT, padx=5)

        # Logs
        tk.Label(root, text="Registro de Actividad:", font=("Segoe UI", 9)).pack(anchor="w", padx=20)
        self.log_area = scrolledtext.ScrolledText(root, width=75, height=15, state='disabled', font=("Consolas", 9), bg="#F5F5F5")
        self.log_area.pack(padx=20, pady=5)
        
        self.log_area.tag_config('error', foreground='red')
        self.log_area.tag_config('success', foreground='#2E7D32')
        self.log_area.tag_config('info', foreground='black')

        tk.Label(root, text="Desarrollado por SPM INTEGRAL © 2026", font=("Segoe UI", 8), fg="gray").pack(side=tk.BOTTOM, pady=5)

    def seleccionar_imagen(self):
        filename = filedialog.askopenfilename(title="Seleccionar imagen", filetypes=[("Imágenes", "*.jpg *.jpeg *.png")])
        if filename:
            self.ruta_imagen = filename
            self.lbl_img.config(text=f"✅ {os.path.basename(filename)}", fg="green")
            self.log_gui(f"Imagen seleccionada: {os.path.basename(filename)}")
        else:
            self.ruta_imagen = None
            self.lbl_img.config(text="Ninguna seleccionada", fg="gray")

    def log_gui(self, mensaje):
        self.root.after(0, self._append_log, mensaje)

    def _append_log(self, mensaje):
        self.log_area.configure(state='normal')
        tag = 'info'
        if "❌" in mensaje or "🔥" in mensaje or "Error" in mensaje: tag = 'error'
        if "✅" in mensaje or "Enviado" in mensaje: tag = 'success'
        self.log_area.insert(tk.END, mensaje + "\n", tag)
        self.log_area.see(tk.END)
        self.log_area.configure(state='disabled')

    def iniciar_campana(self):
        grupo = self.entry_grupo.get().strip()
        if not grupo:
            messagebox.showwarning("Falta dato", "Nombre del grupo requerido.")
            return

        if not os.path.exists(config.CONTACTOS_FILE):
            messagebox.showerror("Error", "No se encuentra contactos.xlsx")
            return

        self.btn_iniciar.config(state=tk.DISABLED)
        self.entry_grupo.config(state=tk.DISABLED)
        self.btn_img.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.btn_login.config(state=tk.NORMAL)

        self.log_gui("--- INICIANDO CAMPAÑA ---")
        if self.ruta_imagen: self.log_gui(f"📷 Modo Imagen: {os.path.basename(self.ruta_imagen)}")
        else: self.log_gui("📝 Modo Texto")
        
        self.bot = WhatsAppBot(log_callback=self.log_gui)
        self.thread = threading.Thread(target=self.ejecutar_thread, args=(grupo, self.ruta_imagen))
        self.thread.daemon = True
        self.thread.start()

    def ejecutar_thread(self, grupo, imagen_path):
        self.bot.ejecutar_campana(config.CONTACTOS_FILE, grupo, imagen_path)
        self.root.after(0, self.reset_ui)

    def confirmar_login(self):
        if self.bot and self.bot.esperando_login:
            self.bot.esperando_login = False
            self.btn_login.config(state=tk.DISABLED, text="Sesión Iniciada")
            self.btn_pausa.config(state=tk.NORMAL)
            self.log_gui("👍 Login confirmado.")

    def toggle_pausa(self):
        if self.bot:
            if self.bot.en_pausa:
                self.bot.en_pausa = False
                self.btn_pausa.config(text="⏸️ PAUSAR", bg="#FFA000")
                self.log_gui("▶️ Reanudando...")
            else:
                self.bot.en_pausa = True
                self.btn_pausa.config(text="▶️ REANUDAR", bg="#8BC34A")
                self.log_gui("⏸️ PAUSADO.")

    def detener_bot(self):
        if self.bot:
            if messagebox.askyesno("Confirmar", "¿Detener envío?"):
                self.bot.detenido = True
                self.bot.en_pausa = False
                self.bot.esperando_login = False
                self.log_gui("🛑 Deteniendo...")

    def reset_ui(self):
        self.btn_iniciar.config(state=tk.NORMAL)
        self.entry_grupo.config(state=tk.NORMAL)
        self.btn_img.config(state=tk.NORMAL)
        self.btn_login.config(state=tk.DISABLED, text="📱 YA ESCANEÉ EL QR")
        self.btn_pausa.config(state=tk.DISABLED, text="⏸️ PAUSAR", bg="#FFA000")
        self.btn_stop.config(state=tk.DISABLED)
        messagebox.showinfo("Fin", "Proceso terminado.")

# --- FUNCIÓN DE ADVERTENCIA LEGAL ---
def mostrar_advertencia_legal():
    texto_advertencia = (
        "⚠️ USO RESPONSABLE Y RIESGOS DE BLOQUEO\n\n"
        "WhatsApp (Meta) utiliza sistemas automáticos para detectar spam. "
        "El envío masivo de mensajes (más de 50-100 diarios) conlleva un ALTO RIESGO "
        "de que tu número sea suspendido o bloqueado permanentemente.\n\n"
        "RECOMENDACIONES PARA EVITAR BLOQUEOS:\n"
        "1. No envíes más de 50 mensajes por tanda.\n"
        "2. Usa intervalos de tiempo largos (Configurados en la app).\n"
        "3. Interactúa manualmente con las personas que respondan.\n"
        "4. No uses cuentas nuevas (recién creadas) para envíos masivos.\n\n"
        "EXENCIÓN DE RESPONSABILIDAD:\n"
        "SPM INTEGRAL y el desarrollador de este software NO se hacen responsables "
        "por suspensiones, bloqueos o pérdida de cuentas de WhatsApp derivados del uso "
        "de esta herramienta. El usuario asume toda la responsabilidad.\n\n"
        "¿Aceptas los riesgos y deseas continuar?"
    )
    return messagebox.askyesno("⚠️ USA LA APLICACIÓN CON PRUDENCIA", texto_advertencia, icon='warning')

# --- MAIN ---
if __name__ == "__main__":
    root = tk.Tk()
    current_hwid = obtener_id_pc()
    acceso_concedido = False

    # 1. VALIDACIÓN DE LICENCIA (HARDWARE ID)
    if os.path.exists(ARCHIVO_TOKEN):
        try:
            with open(ARCHIVO_TOKEN, "r") as f: saved_hwid = f.read().strip()
            if saved_hwid == current_hwid: acceso_concedido = True
            else: 
                try: os.remove(ARCHIVO_TOKEN)
                except: pass
        except: pass

    if not acceso_concedido:
        root.withdraw()
        while True:
            password = simpledialog.askstring("Seguridad SPM", f"🔐 Activación:\nID: {current_hwid}\nContraseña:", show='*')
            if password is None: sys.exit()
            if password == CONTRASEÑA_MAESTRA:
                try:
                    with open(ARCHIVO_TOKEN, "w") as f: f.write(current_hwid)
                    acceso_concedido = True # Marcamos como concedido
                    break
                except: sys.exit()
            else: messagebox.showerror("Error", "❌ Incorrecto.")

    # 2. ADVERTENCIA LEGAL OBLIGATORIA (GATEKEEPER)
    # Solo llegamos aquí si la contraseña/token fue válida.
    # Mostramos la interfaz solo si acepta los riesgos.
    if acceso_concedido:
        # Recuperamos la ventana raíz si estaba oculta
        if root.state() == 'withdrawn':
            root.deiconify() 
            root.withdraw() # La ocultamos de nuevo para mostrar solo el popup limpio
        
        acepta_riesgos = mostrar_advertencia_legal()
        
        if acepta_riesgos:
            root.deiconify() # Muestra la ventana principal
            app = AppWhatsApp(root)
            root.mainloop()
        else:
            sys.exit() # Si dice que NO, cerramos todo
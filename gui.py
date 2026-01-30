import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
import threading
import os
import sys
import subprocess 
from bot import WhatsAppBot
import config
import subprocess
import uuid


CONTRASEÑA_MAESTRA = "G0l14th903$" 
ARCHIVO_TOKEN = os.path.join(config.BASE_DIR, "auth.token")

def obtener_id_pc():
    """
    Obtiene una huella digital única del PC.
    Intenta UUID de Motherboard -> Si falla, usa Dirección MAC.
    NO requiere permisos de admin.
    """
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        cmd = 'wmic csproduct get uuid'
        resultado = subprocess.check_output(cmd, startupinfo=startupinfo, shell=False).decode()
        
        serial = resultado.split('\n')[1].strip()
        
        if serial and "FFFF" not in serial: 
            return serial
            
    except Exception:
        pass 

    try:
        mac = uuid.getnode()
        return str(mac)
    except:
        return os.getenv('COMPUTERNAME', 'PC') + os.getenv('USERNAME', 'USER')

class AppWhatsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🤖 SPM INTEGRAL - WhatsApp Bot")
        self.root.geometry("600x520")
        self.root.resizable(False, False)

        self.bot = None
        self.thread = None

        frame_input = tk.Frame(root, pady=15)
        frame_input.pack()
        
        tk.Label(frame_input, text="Nombre del Grupo (Excel):", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT, padx=5)
        self.entry_grupo = tk.Entry(frame_input, width=25, font=("Segoe UI", 11))
        self.entry_grupo.pack(side=tk.LEFT, padx=5)

        frame_btns = tk.Frame(root, pady=5)
        frame_btns.pack()

        self.btn_iniciar = tk.Button(frame_btns, text="🚀 INICIAR CAMPAÑA", bg="#2E7D32", fg="white", font=("Segoe UI", 10, "bold"), command=self.iniciar_campana, width=20)
        self.btn_iniciar.pack(side=tk.LEFT, padx=5)

        self.btn_login = tk.Button(frame_btns, text="📱 YA ESCANEÉ EL QR", bg="#1976D2", fg="white", font=("Segoe UI", 10, "bold"), state=tk.DISABLED, command=self.confirmar_login, width=20)
        self.btn_login.pack(side=tk.LEFT, padx=5)

        frame_ctrl = tk.Frame(root, pady=10)
        frame_ctrl.pack()

        self.btn_pausa = tk.Button(frame_ctrl, text="⏸️ PAUSAR", bg="#FFA000", width=15, state=tk.DISABLED, command=self.toggle_pausa, font=("Segoe UI", 9))
        self.btn_pausa.pack(side=tk.LEFT, padx=5)

        self.btn_stop = tk.Button(frame_ctrl, text="🛑 DETENER", bg="#D32F2F", fg="white", width=15, state=tk.DISABLED, command=self.detener_bot, font=("Segoe UI", 9))
        self.btn_stop.pack(side=tk.LEFT, padx=5)

        tk.Label(root, text="Registro de Actividad:", font=("Segoe UI", 9)).pack(anchor="w", padx=20)
        self.log_area = scrolledtext.ScrolledText(root, width=75, height=18, state='disabled', font=("Consolas", 9), bg="#F5F5F5")
        self.log_area.pack(padx=20, pady=5)
        
        self.log_area.tag_config('error', foreground='red')
        self.log_area.tag_config('success', foreground='#2E7D32')
        self.log_area.tag_config('info', foreground='black')

        tk.Label(root, text="Desarrollado por SPM INTEGRAL © 2026 || Soporte al +57 3195067885", font=("Segoe UI", 8), fg="gray").pack(side=tk.BOTTOM, pady=5)

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
            messagebox.showwarning("Falta dato", "Por favor escribe el nombre del grupo.")
            return

        if not os.path.exists(config.CONTACTOS_FILE):
            messagebox.showerror("Error", "No se encuentra contactos.xlsx")
            return

        self.btn_iniciar.config(state=tk.DISABLED)
        self.entry_grupo.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.btn_login.config(state=tk.NORMAL)

        self.log_gui("--- INICIANDO CAMPAÑA ---")
        self.bot = WhatsAppBot(log_callback=self.log_gui)
        self.thread = threading.Thread(target=self.ejecutar_thread, args=(grupo,))
        self.thread.daemon = True
        self.thread.start()

    def ejecutar_thread(self, grupo):
        self.bot.ejecutar_campana(config.CONTACTOS_FILE, grupo)
        self.root.after(0, self.reset_ui)

    def confirmar_login(self):
        if self.bot and self.bot.esperando_login:
            self.bot.esperando_login = False
            self.btn_login.config(state=tk.DISABLED, text="Sesión Iniciada")
            self.btn_pausa.config(state=tk.NORMAL)
            self.log_gui("👍 Inicio de sesión confirmado.")

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
            if messagebox.askyesno("Confirmar", "¿Seguro que quieres detener el envío?"):
                self.bot.detenido = True
                self.bot.en_pausa = False
                self.bot.esperando_login = False
                self.log_gui("🛑 Deteniendo proceso...")

    def reset_ui(self):
        self.btn_iniciar.config(state=tk.NORMAL)
        self.entry_grupo.config(state=tk.NORMAL)
        self.btn_login.config(state=tk.DISABLED, text="📱 YA ESCANEÉ EL QR")
        self.btn_pausa.config(state=tk.DISABLED, text="⏸️ PAUSAR", bg="#FFA000")
        self.btn_stop.config(state=tk.DISABLED)
        messagebox.showinfo("Fin", "El proceso ha terminado.")

if __name__ == "__main__":
    root = tk.Tk()
    
    current_hwid = obtener_id_pc()
    acceso_concedido = False

    if os.path.exists(ARCHIVO_TOKEN):
        try:
            with open(ARCHIVO_TOKEN, "r") as f:
                saved_hwid = f.read().strip()
            
            if saved_hwid == current_hwid:
                acceso_concedido = True
            else:
                messagebox.showwarning("Seguridad", "⚠️ Se ha detectado un cambio de equipo.\nLa licencia no es válida en esta PC.\nDebes ingresar la contraseña nuevamente.")
                try:
                    os.remove(ARCHIVO_TOKEN) 
                except: pass
        except:
            pass 

    if not acceso_concedido:
        root.withdraw()
        while True:
            password = simpledialog.askstring("Seguridad SPM", f"🔐 Activación de Licencia:\nID Equipo: {current_hwid}\n\nIngresa la contraseña maestra:", show='*')
            
            if password is None:
                sys.exit()
            
            if password == CONTRASEÑA_MAESTRA:
                try:

                    with open(ARCHIVO_TOKEN, "w") as f:
                        f.write(current_hwid)
                    
                    messagebox.showinfo("Activado", "✅ Equipo vinculado exitosamente.")
                    root.deiconify()
                    break
                except Exception as e:
                    messagebox.showerror("Error", f"Error de escritura: {e}")
                    sys.exit()
            else:
                messagebox.showerror("Error", "❌ Contraseña incorrecta.")
    
    app = AppWhatsApp(root)
    root.mainloop()
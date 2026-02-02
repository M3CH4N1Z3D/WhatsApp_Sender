import time
import random
import csv
from datetime import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import config

# Librerías para Portapapeles
from io import BytesIO
import win32clipboard
from PIL import Image

class WhatsAppBot:
    def __init__(self, log_callback=None):
        self.driver = None
        self.wait = None
        self.log_callback = log_callback
        self.en_pausa = False
        self.detenido = False
        self.esperando_login = False

    def log(self, mensaje):
        timestamp = datetime.now().strftime("%H:%M:%S")
        texto = f"[{timestamp}] {mensaje}"
        print(texto)
        if self.log_callback: self.log_callback(texto)

    def _dormir(self, segundos):
        """Duerme chequeando el STOP."""
        ciclos = int(segundos / 0.1)
        for _ in range(ciclos):
            if self.detenido: return False
            while self.en_pausa:
                if self.detenido: return False
                time.sleep(0.5)
            time.sleep(0.1)
        return True

    def iniciar_driver(self):
        self.log("Iniciando Chrome...")
        chrome_options = Options()
        chrome_options.add_argument(f"user-data-dir={config.USER_DATA_DIR}")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, config.TIEMPO_CARGA_PAGINA)
        self.driver.get(config.WA_WEB_URL)
        
        self.log("⏳ Esperando inicio de sesión... Escanea el QR.")
        self.esperando_login = True
        while self.esperando_login:
            if self.detenido: return
            time.sleep(1)
        self.log("✅ Sesión confirmada.")

    def copiar_imagen_clipboard(self, ruta_imagen):
        try:
            image = Image.open(ruta_imagen)
            output = BytesIO()
            image.convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:] 
            output.close()
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()
            return True
        except Exception as e:
            self.log(f"❌ Error Clipboard: {e}")
            return False

    def limpiar_datos(self, archivo_path, grupo_objetivo):
        self.log(f"Leyendo Excel: {archivo_path}")
        try: df = pd.read_excel(archivo_path, dtype=str)
        except Exception as e:
            self.log(f"❌ Error Excel: {e}")
            return []

        df['Grupo'] = df['Grupo'].fillna('').astype(str)
        df_filtrado = df[df['Grupo'] == grupo_objetivo].copy()
        datos = []

        for _, row in df_filtrado.iterrows():
            nombre = str(row['Nombre']) if pd.notna(row['Nombre']) else ""
            telf = str(row['Telefono'])
            msg = row['Mensaje']
            if pd.isna(msg) or str(msg).strip() == "": continue
            
            if "." in telf: telf = telf.split(".")[0]
            telf = ''.join(filter(str.isdigit, telf))
            if len(telf) == 10: telf = "57" + telf
            
            if 10 <= len(telf) <= 15:
                datos.append({"nombre": nombre, "telefono": telf, "mensaje": str(msg)})
        
        self.log(f"📊 Contactos válidos: {len(datos)}")
        return datos

    def registrar_log(self, nombre, telefono, estado):
        existe = False
        try: 
            with open(config.REPORTE_FILE, 'r', encoding='utf-8') as f: existe = True
        except: pass

        with open(config.REPORTE_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not existe: writer.writerow(['Nombre', 'Telefono', 'Estado', 'Timestamp'])
            writer.writerow([nombre, telefono, estado, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])

    def escribir_humano(self, elemento, texto):
        for linea in texto.split('\n'):
            for char in linea:
                if self.detenido: return
                try:
                    if ord(char) <= 0xFFFF: elemento.send_keys(char)
                    else: self.driver.execute_script("document.execCommand('insertText', false, arguments[0]);", char)
                except:
                    self.driver.execute_script("document.execCommand('insertText', false, arguments[0]);", char)
                if not self._dormir(random.uniform(0.04, 0.12)): return
            elemento.send_keys(Keys.SHIFT + Keys.ENTER)
            if not self._dormir(0.5): return

    def enviar_mensaje(self, contacto, imagen_path=None):
        if self.detenido: return False
        nombre = contacto['nombre']
        telefono = contacto['telefono']
        mensaje_base = contacto['mensaje']
        
        self.log(f"➤ Procesando: {nombre} ({telefono})")
        mensaje_final = f"{mensaje_base.replace('{nombre}', nombre)} {random.choice(config.EMOJIS_EVASION)}"
        
        url = f"https://web.whatsapp.com/send?phone={telefono}"
        self.driver.get(url)
        
        try:
            try:
                WebDriverWait(self.driver, 6).until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'no es válido') or contains(text(), 'compartido a través')]"))
                )
                self.log(f"❌ Número inválido: {telefono}")
                self.registrar_log(nombre, telefono, "Error - Número inválido")
                return False
            except TimeoutException: pass

            try:
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, config.SELECTORS["chat_loaded"])))
            except TimeoutException:
                self.log("⚠️ Timeout carga chat")
                self.registrar_log(nombre, telefono, "Error - Timeout carga")
                return False

            if self.detenido: return False

            # --- ENVÍO ---
            if imagen_path:
                self.log("📷 Copiando imagen...")
                if self.copiar_imagen_clipboard(imagen_path):
                    self.driver.switch_to.active_element.send_keys(Keys.CONTROL, 'v')
                    # Aumentamos espera de vista previa a 3s para PCs lentos
                    if not self._dormir(3.0): return False 
                    
                    try:
                        elemento_foco = self.driver.switch_to.active_element
                        self.log("⌨️ Escribiendo descripción en foto...")
                        self.escribir_humano(elemento_foco, mensaje_final)
                    except Exception as e:
                        self.log(f"⚠️ Error escribiendo en foto: {e}")
                else:
                    self.log("⚠️ Fallo portapapeles. Solo texto.")
                    caja = self.driver.find_element(By.CSS_SELECTOR, config.SELECTORS["message_box"])
                    caja.click()
                    self.escribir_humano(caja, mensaje_final)
            else:
                caja_texto = self.driver.find_element(By.CSS_SELECTOR, config.SELECTORS["message_box"])
                caja_texto.click()
                if not self._dormir(0.5): return False
                self.log("⌨️ Escribiendo mensaje...")
                self.escribir_humano(caja_texto, mensaje_final)

            # --- CORRECCIÓN DEL CIERRE PREMATURO ---
            if not self._dormir(1): return False
            self.driver.switch_to.active_element.send_keys(Keys.ENTER)
            
            # ESPERA DE SEGURIDAD OBLIGATORIA
            # Esto evita que el navegador se cierre antes de que el mensaje salga
            self.log("📤 Confirmando envío...")
            time.sleep(3) 
            
            self.log(f"✅ Enviado a {telefono}")
            self.registrar_log(nombre, telefono, "Enviado")
            return True

        except Exception as e:
            self.log(f"🔥 Error crítico: {e}")
            return False

    def ejecutar_campana(self, archivo_excel, grupo, imagen_path=None):
        self.detenido = False
        self.en_pausa = False
        contactos = self.limpiar_datos(archivo_excel, grupo)
        if not contactos: return

        try: self.iniciar_driver()
        except Exception as e: 
            self.log(f"Error driver: {e}")
            return

        for i, contacto in enumerate(contactos):
            if self.detenido: 
                self.log("🛑 Detenido por usuario.")
                break
            
            while self.en_pausa:
                if self.detenido: break
                time.sleep(1)

            self.enviar_mensaje(contacto, imagen_path)
            
            if self.detenido: break

            if i < len(contactos) - 1:
                delay = random.randint(config.MIN_DELAY_ENVIO, config.MAX_DELAY_ENVIO)
                self.log(f"⏳ Esperando {delay}s...")
                if not self._dormir(delay):
                    self.log("🛑 Detenido durante la espera.")
                    break
        
        self.log("🏁 Finalizado. Cerrando en 5 segundos...")
        time.sleep(5) # Espera final antes de matar el navegador
        if self.driver: 
            try: self.driver.quit()
            except: pass
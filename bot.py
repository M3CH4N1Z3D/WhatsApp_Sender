import time
import random
import csv
import urllib.parse
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

class WhatsAppBot:
    def __init__(self, log_callback=None):
        self.driver = None
        self.wait = None
        self.log_callback = log_callback 
        
        self.en_pausa = False
        self.detenido = False
        self.esperando_login = False 

    def log(self, mensaje):
        """Envía el mensaje a la interfaz gráfica y a la consola."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        texto_completo = f"[{timestamp}] {mensaje}"
        print(texto_completo) 
        if self.log_callback:
            self.log_callback(texto_completo)

    def iniciar_driver(self):
        self.log("Iniciando Google Chrome...")
        chrome_options = Options()
        chrome_options.add_argument(f"user-data-dir={config.USER_DATA_DIR}")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, config.TIEMPO_CARGA_PAGINA)
        
        self.log("Cargando WhatsApp Web...")
        self.driver.get(config.WA_WEB_URL)
        
        self.log("⏳ Esperando inicio de sesión... Escanea el QR si es necesario.")
        self.esperando_login = True 
        
        while self.esperando_login:
            if self.detenido: return 
            time.sleep(1)
            
        self.log("✅ Sesión confirmada. Comenzando envíos...")

    def limpiar_datos(self, archivo_path, grupo_objetivo):
        self.log(f"Leyendo Excel: {archivo_path}")
        try:
            df = pd.read_excel(archivo_path, dtype=str)
        except Exception as e:
            self.log(f"❌ Error leyendo Excel: {e}")
            return []

        df['Grupo'] = df['Grupo'].fillna('').astype(str)
        df_filtrado = df[df['Grupo'] == grupo_objetivo].copy()
        
        datos_limpios = []
        registros_omitidos = 0

        for _, row in df_filtrado.iterrows():
            nombre = str(row['Nombre']) if pd.notna(row['Nombre']) else ""
            telefono_raw = str(row['Telefono'])
            mensaje_raw = row['Mensaje']

            if pd.isna(mensaje_raw) or str(mensaje_raw).strip() == "":
                registros_omitidos += 1
                continue

            if "." in telefono_raw: telefono_raw = telefono_raw.split(".")[0]
            telefono = ''.join(filter(str.isdigit, telefono_raw))
            
            if len(telefono) == 10: telefono = "57" + telefono
            
            if len(telefono) >= 10 and len(telefono) <= 15:
                datos_limpios.append({
                    "nombre": nombre,
                    "telefono": telefono,
                    "mensaje": str(mensaje_raw)
                })
            else:
                registros_omitidos += 1
        
        self.log(f"📊 Contactos válidos: {len(datos_limpios)} | Omitidos: {registros_omitidos}")
        return datos_limpios

    def registrar_log(self, nombre, telefono, estado):
        existe = False
        try:
            with open(config.REPORTE_FILE, 'r', encoding='utf-8') as f: existe = True
        except FileNotFoundError: pass

        with open(config.REPORTE_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not existe: writer.writerow(['Nombre', 'Telefono', 'Estado', 'Timestamp'])
            writer.writerow([nombre, telefono, estado, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])

    def escribir_humano(self, elemento, texto):
        for linea in texto.split('\n'):
            for char in linea:
                if self.detenido: return 
                try:
                    if ord(char) <= 0xFFFF:
                        elemento.send_keys(char)
                    else:
                        self.driver.execute_script("document.execCommand('insertText', false, arguments[0]);", char)
                except WebDriverException:
                    self.driver.execute_script("document.execCommand('insertText', false, arguments[0]);", char)
                time.sleep(random.uniform(0.05, 0.15)) 
            elemento.send_keys(Keys.SHIFT + Keys.ENTER)
            time.sleep(0.5)

    def enviar_mensaje(self, contacto):
        if self.detenido: return False
        
        nombre = contacto['nombre']
        telefono = contacto['telefono']
        mensaje_base = contacto['mensaje']
        
        self.log(f"➤ Procesando: {nombre} ({telefono})")
        
        mensaje_personalizado = mensaje_base.replace('{nombre}', nombre)
        marcador_unico = random.choice(config.EMOJIS_EVASION)
        mensaje_final = f"{mensaje_personalizado} {marcador_unico}"
        
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
                self.log("⚠️ Timeout carga de chat")
                self.registrar_log(nombre, telefono, "Error - Timeout carga")
                return False

            try:
                caja_texto = self.driver.find_element(By.CSS_SELECTOR, config.SELECTORS["message_box"])
                caja_texto.click()
                time.sleep(0.5)

                self.log("⌨️ Escribiendo...")
                self.escribir_humano(caja_texto, mensaje_final)
                time.sleep(1)

                if self.detenido: return False 

                caja_texto.send_keys(Keys.ENTER)
                self.log(f"✅ Enviado a {telefono}")
                self.registrar_log(nombre, telefono, "Enviado")
                return True

            except Exception as e:
                self.log(f"❌ Error escritura: {e}")
                self.registrar_log(nombre, telefono, "Error - Escritura")
                return False
            
        except Exception as e:
            self.log(f"🔥 Error crítico: {e}")
            return False

    def ejecutar_campana(self, archivo_excel, grupo):
        self.detenido = False
        self.en_pausa = False
        
        contactos = self.limpiar_datos(archivo_excel, grupo)
        if not contactos: 
            self.log("⚠️ No hay contactos. Finalizando.")
            return

        try:
            self.iniciar_driver()
        except Exception as e:
            self.log(f"Error iniciando navegador: {e}")
            return

        for i, contacto in enumerate(contactos):
            if self.detenido:
                self.log("🛑 Campaña detenida por el usuario.")
                break

            while self.en_pausa:
                if self.detenido: break 
                time.sleep(1)
                

            self.enviar_mensaje(contacto)
            
            if i < len(contactos) - 1:
                delay = random.randint(config.MIN_DELAY_ENVIO, config.MAX_DELAY_ENVIO)
                self.log(f"⏳ Esperando {delay}s...")
                
                for _ in range(delay):
                    if self.detenido: break
                    while self.en_pausa: 
                        if self.detenido: break
                        time.sleep(1)
                    time.sleep(1)
        
        self.log("🏁 Campaña finalizada.")
        if self.driver:
            self.log("Cerrando navegador...")
            try: self.driver.quit()
            except: pass
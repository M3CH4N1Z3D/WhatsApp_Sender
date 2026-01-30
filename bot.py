import time
import random
import csv
import urllib.parse
from datetime import datetime # <--- CORRECCIÓN IMPORTANTE 1
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import config

class WhatsAppBot:
    def __init__(self):
        self.driver = None
        self.wait = None

    def iniciar_driver(self):
        print("Iniciando driver...")
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
        
        print("Cargando WhatsApp Web...")
        self.driver.get(config.WA_WEB_URL)
        print("Si no has iniciado sesión, escanea el QR ahora.")
        time.sleep(5) 

    def limpiar_datos(self, archivo_path, grupo_objetivo):
        print(f"Leyendo datos de {archivo_path}...")
        try:
            df = pd.read_excel(archivo_path, dtype=str)
        except Exception as e:
            print(f"Error al leer el archivo Excel: {e}")
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
        
        print(f"✅ Contactos válidos: {len(datos_limpios)} | Omitidos: {registros_omitidos}")
        return datos_limpios

    def registrar_log(self, nombre, telefono, estado):
        existe = False
        try:
            with open(config.REPORTE_FILE, 'r', encoding='utf-8') as f: existe = True
        except FileNotFoundError: pass

        with open(config.REPORTE_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not existe: writer.writerow(['Nombre', 'Telefono', 'Estado', 'Timestamp'])
            # CORRECCIÓN DATETIME
            writer.writerow([nombre, telefono, estado, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])

    def escribir_humano(self, elemento, texto):
        """Escribe texto carácter por carácter, manejando Emojis con JS."""
        for linea in texto.split('\n'):
            for char in linea:
                try:
                    # Intento 1: Escritura normal (Teclado)
                    # Si el carácter es BMP (letras, números, símbolos básicos)
                    if ord(char) <= 0xFFFF:
                        elemento.send_keys(char)
                    else:
                        # Intento 2: Si es Emoji (Non-BMP), usar JavaScript
                        # Usamos 'insertText' que simula pegado nativo y no rompe React
                        self.driver.execute_script(
                            "document.execCommand('insertText', false, arguments[0]);", 
                            char
                        )
                except WebDriverException:
                    # Fallback de emergencia: Si send_keys falla, intentamos JS
                    self.driver.execute_script(
                        "document.execCommand('insertText', false, arguments[0]);", 
                        char
                    )
                
                # Pausa aleatoria entre letras
                time.sleep(random.uniform(0.05, 0.15)) 
            
            # Salto de línea
            elemento.send_keys(Keys.SHIFT + Keys.ENTER)
            time.sleep(0.5)

    def enviar_mensaje(self, contacto):
        nombre = contacto['nombre']
        telefono = contacto['telefono']
        mensaje_base = contacto['mensaje']
        
        print(f"Procesando: {nombre} ({telefono})")
        
        mensaje_personalizado = mensaje_base.replace('{nombre}', nombre)
        marcador_unico = random.choice(config.EMOJIS_EVASION)
        mensaje_final = f"{mensaje_personalizado} {marcador_unico}"
        
        url = f"https://web.whatsapp.com/send?phone={telefono}"
        self.driver.get(url)
        
        try:
            # 1. Validar Popup
            try:
                WebDriverWait(self.driver, 6).until(
                    EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'no es válido') or contains(text(), 'compartido a través')]"))
                )
                print(f"❌ Número inválido detectado: {telefono}")
                self.registrar_log(nombre, telefono, "Error - Número inválido")
                return False
            except TimeoutException:
                pass

            # 2. Esperar carga
            try:
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, config.SELECTORS["chat_loaded"])))
            except TimeoutException:
                print("⚠️ Timeout: El chat no cargó.")
                self.registrar_log(nombre, telefono, "Error - Timeout carga")
                return False

            # 3. Escritura y Envío
            try:
                caja_texto = self.driver.find_element(By.CSS_SELECTOR, config.SELECTORS["message_box"])
                caja_texto.click()
                time.sleep(0.5)

                print("⌨️ Escribiendo mensaje como humano...")
                self.escribir_humano(caja_texto, mensaje_final) # <--- Usamos la nueva función blindada
                time.sleep(1)

                caja_texto.send_keys(Keys.ENTER)
                print(f"✅ Mensaje enviado a {telefono}")
                self.registrar_log(nombre, telefono, "Enviado")
                return True

            except Exception as e:
                print(f"❌ Error durante escritura/envío: {e}")
                self.registrar_log(nombre, telefono, f"Error - Escritura: {str(e)}")
                return False
            
        except Exception as e:
            print(f"Error crítico: {e}")
            self.registrar_log(nombre, telefono, f"Error Critico: {str(e)}")
            return False

    def ejecutar_campana(self, archivo_excel, grupo):
        contactos = self.limpiar_datos(archivo_excel, grupo)
        if not contactos: return

        self.iniciar_driver()

        for i, contacto in enumerate(contactos):
            self.enviar_mensaje(contacto)
            if i < len(contactos) - 1:
                delay = random.randint(config.MIN_DELAY_ENVIO, config.MAX_DELAY_ENVIO)
                print(f"⏳ Esperando {delay}s antes del siguiente contacto...")
                time.sleep(delay)
        
        print("Campaña finalizada.")
        time.sleep(3)
        self.driver.quit()
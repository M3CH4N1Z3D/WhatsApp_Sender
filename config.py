import os

# Directorios
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USER_DATA_DIR = os.path.join(BASE_DIR, 'user_data')
CONTACTOS_FILE = os.path.join(BASE_DIR, 'contactos.xlsx')

# WhatsApp Web URLs
WA_WEB_URL = "https://web.whatsapp.com"
SEND_URL = "https://web.whatsapp.com/send?phone={phone}&text={text}"

# Archivos
REPORTE_FILE = os.path.join(BASE_DIR, 'reporte_envios.csv')

# --- SELECTORES CORREGIDOS ---
SELECTORS = {
    # SOLUCIÓN: Buscamos el editable que esté DENTRO del footer (el de abajo)
    # Esto evita confundirse con la barra de búsqueda de arriba.
    "message_box": "footer div[contenteditable='true']",
    
    # El botón de enviar
    "send_button": "span[data-icon='send']",
    
    # Usamos la caja de texto del footer como señal de que el chat cargó
    "chat_loaded": "footer div[contenteditable='true']",
    
    # Popups de error
    "invalid_number_popup": "div[data-animate-modal-popup='true']"
}

# Tiempos
TIEMPO_CARGA_PAGINA = 30
MIN_DELAY_ENVIO = 20
MAX_DELAY_ENVIO = 60

# Evasión
EMOJIS_EVASION = ["😀", "😃", "😄", "😁", "😆", "😅", "😂", "🤣", "😊", "😇", "🙂", "🙃", "😉", "😌", "😍"]
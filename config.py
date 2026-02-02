import os
import sys

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

USER_DATA_DIR = os.path.join(BASE_DIR, 'user_data')
CONTACTOS_FILE = os.path.join(BASE_DIR, 'contactos.xlsx')
REPORTE_FILE = os.path.join(BASE_DIR, 'reporte_envios.csv')

WA_WEB_URL = "https://web.whatsapp.com"

SELECTORS = {
    "message_box": "footer div[contenteditable='true']",
    "chat_loaded": "footer div[contenteditable='true']",
    "send_button": "span[data-icon='send']", 
    "invalid_number_popup": "div[data-animate-modal-popup='true']"
}

# Tiempos
TIEMPO_CARGA_PAGINA = 30
MIN_DELAY_ENVIO = 10
MAX_DELAY_ENVIO = 30

EMOJIS_EVASION = ["😀", "😃", "😄", "😁", "😆", "😅", "😂", "🤣", "😊", "😇", "🙂", "🙃", "😉", "😌", "😍"]
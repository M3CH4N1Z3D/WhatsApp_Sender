# Documento de Diseño: WhatsApp Automation Bot

## 1. Descripción General
Script en Python para automatizar el envío de mensajes de WhatsApp Business utilizando Selenium y Pandas. El objetivo principal es simular comportamiento humano para evitar bloqueos (anti-ban), utilizando un navegador persistente y acciones "humanizadas".

## 2. Requerimientos Técnicos y Dependencias

### Lenguaje
- Python 3.8+

### Librerías (`requirements.txt`)
- `selenium`: Para la automatización del navegador.
- `pandas`: Para la lectura y manipulación de datos del Excel.
- `openpyxl`: Motor necesario para que Pandas lea archivos `.xlsx`.
- `webdriver-manager`: Gestión automática del driver de Chrome (recomendado para facilitar la instalación).

## 3. Arquitectura del Proyecto

### Estructura de Archivos
```
/
├── contactos.xlsx        # Archivo de entrada de datos
├── main.py              # Punto de entrada del script
├── bot.py               # Definición de la clase WhatsAppBot
├── config.py            # Configuraciones (Selectores, Paths, Tiempos)
├── requirements.txt     # Dependencias
└── user_data/           # Directorio para persistencia de sesión de Chrome (creado automáticamente)
```

## 4. Diseño de la Clase `WhatsAppBot` (bot.py)

### Atributos
- `driver`: Instancia del WebDriver de Selenium.
- `wait`: Instancia de WebDriverWait.
- `base_url`: URL base de WhatsApp Web.

### Métodos

#### 1. `__init__(self)`
- Inicializa las variables de configuración.

#### 2. `iniciar_driver(self)`
- Configura `ChromeOptions`.
- **Clave**: Argumento `--user-data-dir=./user_data` para persistencia de sesión.
- Argumentos adicionales para estabilidad: `--start-maximized`, `--disable-infobars`.
- Inicializa el `webdriver.Chrome`.

#### 3. `limpiar_datos(self, archivo_excel, grupo_objetivo)`
- **Entrada**: Ruta del archivo y nombre del grupo a filtrar.
- **Lógica**:
    - Cargar Excel con Pandas.
    - Filtrar filas donde `Grupo == grupo_objetivo`.
    - Limpiar columna `Telefono`: Eliminar caracteres no numéricos (espacios, +, -, etc.) dejando solo dígitos.
    - Validar que haya mensaje y teléfono.
- **Salida**: DataFrame o lista de diccionarios con los datos listos.

#### 4. `simular_movimiento_mouse(self, elemento_destino=None)`
- **Objetivo**: Simular movimiento humano antes de hacer click.
- **Lógica (Selenium Puro - ActionChains)**:
    - Si se proporciona un `elemento_destino`, mover el mouse hacia él pero no instantáneamente.
    - Usar `ActionChains(driver).move_by_offset(x, y)` en pequeños incrementos aleatorios para crear una ruta "no lineal" o simplemente añadir pausas pequeñas antes de realizar la acción final sobre el elemento.
    - *Nota*: Selenium no mueve el cursor físico del SO, pero sí dispara eventos `mousemove` dentro del DOM del navegador, lo cual es lo que rastrean los scripts de detección.

#### 5. `human_type(self, elemento, texto)`
- **Objetivo**: Escribir texto como un humano.
- **Lógica**:
    - Iterar sobre cada carácter del `texto`.
    - Enviar `send_keys(caracter)`.
    - `time.sleep(random.uniform(0.1, 0.3))` entre cada tecla.

#### 6. `ejecutar_campana(self, archivo_excel, grupo)`
- **Lógica Principal**:
    1. Llamar a `limpiar_datos`.
    2. Llamar a `iniciar_driver`.
    3. Iterar sobre cada contacto:
        - Construir URL: `https://web.whatsapp.com/send?phone={telefono}&text={mensaje}`.
        - `driver.get(url)`.
        - Esperar a que cargue el botón de enviar (usar `WebDriverWait`).
        - **Importante**: Verificar si el número es inválido (aparece popup de "número no válido"). Si es así, registrar error y continuar.
        - Si la caja de texto está presente y el botón de enviar también:
            - `simular_movimiento_mouse(boton_enviar)`.
            - Click en botón enviar.
            - Opcional: Si el texto no se pre-carga en la URL (a veces falla), usar `human_type` en la caja de texto. (La URL suele pre-cargar el texto, así que solo se necesita click en enviar, pero `human_type` se puede usar si se decide escribir manualmente).
            - **Decisión**: El requerimiento pide `human_type`. Si usamos la URL con `&text=`, el texto ya está escrito. Para cumplir el requerimiento estrictamente, podemos:
                a) No pasar `text` en la URL y escribirlo manualmente con `human_type`. (Más seguro/humano).
                b) Pasar `text` en URL y solo dar click.
                *Recomendación*: Usar la opción (a) para maximizar la "humanización" como pidió el usuario, o usar `human_type` para añadir un sufijo aleatorio si se usa la URL.
                *Ajuste al plan*: La URL `send?phone=x&text=y` es muy conveniente. Asumiremos que el usuario prefiere la URL directa por simplicidad, pero si el requerimiento de `human_type` es estricto para *todo* el mensaje, entonces la URL solo debe llevar el `phone`.
                *Estrategia Elegida*: Navegar a `https://web.whatsapp.com/send?phone={num}` (sin texto) y luego usar `human_type` para escribir el mensaje en el chat. Esto cumple mejor con los requisitos de humanización.
        - Esperar confirmación de envío (ej. aparece el tick gris/azul o el mensaje en el chat).
        - `time.sleep(random.randint(30, 90))` (Delay entre envíos).

## 5. Estructura de Datos (contactos.xlsx)

| Telefono      | Mensaje               | Grupo   |
|---------------|-----------------------|---------|
| 573001234567  | Hola, prueba de bot! | Clientes|
| 15551234567   | Oferta especial...    | Leads   |

## 6. Consideraciones de Seguridad (Anti-Ban)
- **Tiempos Aleatorios**: Fundamental respetar el rango 30-90s.
- **Navegador Limpio**: No usar modo headless (WhatsApp Web a veces lo bloquea o no carga QR).
- **Interacción Física**: Si es posible, no realizar otras tareas intensivas con el mouse mientras corre el bot para no interferir con `ActionChains` si se pierde el foco, aunque Selenium suele manejar esto bien en segundo plano visual.

## 7. Paso a Paso para Implementación (Modo Code)
1. Crear `requirements.txt` e instalar dependencias.
2. Crear `contactos.xlsx` de prueba.
3. Implementar `bot.py` con la clase `WhatsAppBot`.
4. Implementar `main.py` para instanciar y ejecutar.
5. Probar con un número propio primero.

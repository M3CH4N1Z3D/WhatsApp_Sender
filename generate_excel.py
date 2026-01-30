import pandas as pd
import os

def crear_excel_prueba():
    data = {
        'Nombre': ['Juan Perez', 'Maria Garcia', 'Pedro Vacio'],
        'Telefono': ['3001234567', '3119876543', '3220001122'],
        'Mensaje': [
            'Hola {nombre}, este es un mensaje de prueba personalizado.', 
            'Saludos {nombre}, recordatorio de tu cita.', 
            '' 
        ],
        'Grupo': ['Test', 'Test', 'Test']
    }

    df = pd.DataFrame(data)
    
    archivo = 'contactos.xlsx'
    try:
        df.to_excel(archivo, index=False)
        print(f"Archivo '{archivo}' creado exitosamente con la nueva columna 'Nombre'.")
        print(df)
    except Exception as e:
        print(f"Error creando excel: {e}")

if __name__ == "__main__":
    crear_excel_prueba()

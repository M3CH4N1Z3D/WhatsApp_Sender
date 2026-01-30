from bot import WhatsAppBot
import config
import os

def main():
    print("--- WhatsApp Automation Bot ---")
    
    if not os.path.exists(config.CONTACTOS_FILE):
        print(f"Error: No se encontró el archivo {config.CONTACTOS_FILE}")
        print("Por favor crea el archivo 'contactos.xlsx' con las columnas: Nombre, Telefono, Mensaje, Grupo")
        return

    grupo = input("Ingresa el nombre del Grupo a procesar (ej. Test): ").strip()
    if not grupo:
        print("Grupo no puede estar vacío.")
        return

    bot = WhatsAppBot()
    try:
        bot.ejecutar_campana(config.CONTACTOS_FILE, grupo)
    except KeyboardInterrupt:
        print("\nEjecución interrumpida por el usuario.")
    except Exception as e:
        print(f"\nError inesperado: {e}")
    finally:
        if bot.driver:
            print("Cerrando navegador...")
            try:
                bot.driver.quit()
            except:
                pass

if __name__ == "__main__":
    main()

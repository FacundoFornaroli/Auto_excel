import os # sirve para navegar mejor entre carpetas
import time # para que el codigo se mantenga en ejecucion
import shutil
import pandas as pd
from watchdog.observers import Observer # libreria de Automatizacion
from watchdog.events import FileSystemEventHandler  

#=================================================
# Configuracion de Carpetas
#=================================================


# La carpeta donde se guardan los archivos
base_dir = "./data"

# Subcarpetas
entrada = base_dir     # Carpeta de entrada
limpio = os.path.join(base_dir, "limpio")  # Carpeta limpia con archivos procesados
crudo = os.path.join(base_dir, "crudo")  # Carpeta con archivos originales

# Crear las carpetas si no existen
for carpeta in [base_dir, limpio, crudo]:
    os.makedirs(carpeta, exist_ok=True)

#=================================================
# Funcion de limpieza de datos
#=================================================

def limpiar_excel(path_archivo):
    """
    Lee el archivo Excel, conserva la primera columna
    y aplica limpieza al resto osea borra columnas vacias,+
    normaliza textos, elimina filas vacias y rellena nulos con valores anteriores.
    """
    df = pd.read_excel(path_archivo, index_col=None)

    # Limpiar nombres de columnas
    df.columns = [str(col).strip()for col in df.columns]

    # Separar primera columna en este caso Fecha para no tocarla si esta bien normalizada
    primera_columna = df.iloc[:, 0]  # Primera columna (Fecha)
    df_resto = df.iloc[:, 1:] # Resto de las columnas

    # Eliminar columnas completamente vacías
    df_resto = df_resto.dropna(axis=1, how='all')

    # Eliminar filas completamente vacias
    df_resto = df_resto.dropna(axis=0, how="all")

    # Limpiar espacios en celdas de texto
    for col in df_resto.select_dtypes(include=['object']).columns:
        df_resto[col] = df_resto[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

    # Rellenar valores nulos con el valor anterior
    df_resto = df_resto.fillna(method='ffill')

    # Combinamos todo de vuelta
    df_final = pd.concat([primera_columna.reset_index(drop=True),
                          df_resto.reset_index(drop=True)], axis=1)    
    return df_final


# =================================================
# Preprocesamiento de cada archivo
# =================================================

def procesar_archivo(path_archivo):
    archivo = os.path.basename(path_archivo)
    nombre_base, extension = os.path.splitext(archivo)

    if not archivo.endswith('.xlsx'):
        return 
    
    try:
        print(f"\n Nuevo archivo detectado: {archivo}")
        df_limpio = limpiar_excel(path_archivo) 

        # Guardar el archivo limpio
        archivo_limpio = f"{nombre_base}_limpio{extension}"
        ruta_limpio = os.path.join(limpio, archivo_limpio)
        df_limpio.to_excel(ruta_limpio, index=False)

        # Mover el archivo original a la carpeta crudo
        shutil.move(path_archivo, os.path.join(crudo, archivo))

        print(f" Archivo procesado y guardado\n  .Limpio -> {archivo_limpio}\n   .Original -> movido a /crudo")

    except Exception as e:
        print(f" Error procesando {archivo}: {e}")

# =================================================
# Procesar archivos ya existentes al iniciar
# =================================================

def procesar_archivos_existentes():
    print(" Buscando archivos existentes en carpeta de entrada...")
    encontrados = False
    for archivo in os.listdir(entrada):
        path = os.path.join(entrada, archivo)
        if os.path.isfile(path) and archivo.endswith('.xlsx'):
            encontrados = True
            procesar_archivo(path)
    if not encontrados:
        print(" No se encontraron archivos .xlsx previos")

# =================================================
# Evento para nuevos archivos
# =================================================

class MiHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.xlsx'):
            time.sleep(1) # Esperar a que el archivo se guarde completamente 
            procesar_archivo(event.src_path)

# =================================================
# Inicio del Script
# =================================================

if __name__ == "__main__":
    print(" Bienvenido al ETL automatico con python")
                   
    print(" Buscando en la carpeta 'data/' para archivos .xlsx....\n")

    # Procesar archivos existentes al iniciar
    procesar_archivos_existentes()

    # Configurar el observador
    print(" Esperando nuevos archivos...\nPresione Ctrl+C para detener.\n")
    observer = Observer()
    event_handler = MiHandler()
    observer.schedule(event_handler, path=entrada, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)  # Mantener el script en ejecución
    except KeyboardInterrupt:
        print("\n Script detenido por el usuario.")
        observer.stop()
    observer.join()            

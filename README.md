# Auto Excel Watcher

Limpieza y automátización basica de archivos Excel entrantes

---

## 📚 Visión general

`auto_excel.py` es un **watchdog ETL** liviano que supervisa una carpeta, depura cada nuevo archivo `.xlsx` que aparezca y genera una copia limpia mientras archiva el original. Está pensado para equipos que comparten hojas de cálculo y necesitan estandarizarlas al instante para su análisis posterior.

```
📂 data/
├── 📥  (archivos .xlsx entrantes)
├── limpio/   (salidas depuradas)
└── crudo/    (originales de respaldo)
```

## ✨ Características clave

* **Monitoreo en tiempo real** — basado en [`watchdog`](https://github.com/gorakhargosh/watchdog).
* **Limpieza consciente del esquema**

  * conserva intacta la **primera columna** (asumida como *Fecha*)
  * elimina filas/columnas totalmente vacías
  * recorta espacios en celdas de texto
  * rellena valores nulos propagando el dato anterior (*forward‑fill*)
* **Versionado seguro** — crea un `_limpio.xlsx`; el original se mueve a `crudo/`.
* **Cero configuración** — basta con ejecutar el script; las carpetas se generan solas.

## ⚙️ Instalación

```bash
python -m venv venv
source venv/bin/activate  # o venv\Scripts\activate en Windows
pip install pandas openpyxl watchdog
```

## 🚀 Uso rápido

```bash
python auto_excel.py
```

1. El script limpia cualquier hoja de cálculo que ya exista dentro de `data/`.
2. Luego queda escuchando indefinidamente. Copia nuevos `.xlsx` en `data/` y observa los registros:

   ```text
   [✓] Procesado: Datos_de_prueba_3.xlsx → limpio/Datos_de_prueba_3_limpio.xlsx
   [→] Original movido a crudo/
   ```
3. Detén la ejecución con `Ctrl + C`.

## 🛠️ Cómo funciona (alto nivel)

| Paso | Función / clase                              | Qué hace                                                                                       |
| ---- | -------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| 1    | `limpiar_excel()`                            | Lee el libro con **pandas**, aplica las reglas de limpieza y devuelve un `DataFrame` depurado. |
| 2    | `procesar_archivo()`                         | Llama a `limpiar_excel`, guarda `_limpio.xlsx` y mueve el original a `crudo/`.                 |
| 3    | `procesar_archivos_existentes()`             | Barrido único sobre `data/` al iniciar; envía cada archivo a `procesar_archivo()`.             |
| 4    | `MiHandler` (de `watchdog`)                  | Dispara `procesar_archivo()` cuando se crea un nuevo archivo en la carpeta.                    |
| 5    | Bucle principal `if __name__ == "__main__":` | Arranca el observador y corre hasta que lo interrumpas.                                        |

---

## 🔍 Detalle de **cada expresión** clave

> Una guía para que aprendas de las llamadas, métodos y parámetros más importantes usados en el script.

| Expresión / llamada                                             | Por qué se usa                                                             | Qué hace exactamente                                                                                |
| --------------------------------------------------------------- | -------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `os.makedirs(ruta, exist_ok=True)`                              | Garantizar que las carpetas necesarias existan antes de procesar archivos. | Crea la ruta completa; si ya existe no lanza excepción gracias a `exist_ok=True`.                   |
| `for archivo in os.listdir(DATA_DIR)`                           | Detectar archivos ya presentes al inicio.                                  | Recorre los nombres dentro de la carpeta `DATA_DIR`.                                                |
| `archivo.endswith('.xlsx')`                                     | Filtrar sólo Excel.                                                        | Comprueba la extensión para evitar procesar otros tipos de archivo.                                 |
| `pd.read_excel(path)`                                           | Lectura robusta del libro.                                                 | Convierte la hoja activa del Excel en un `DataFrame` de **pandas**.                                 |
| `df.dropna(axis=1, how='all')`                                  | Eliminar columnas vacías.                                                  | `axis=1` → columnas; `how='all'` → sólo si **todas** sus celdas son `NaN`.                          |
| `df.dropna(axis=0, how='all')`                                  | Eliminar filas vacías.                                                     | `axis=0` → filas.                                                                                   |
| `df.applymap(lambda x: x.strip() if isinstance(x, str) else x)` | Limpieza de texto.                                                         | Quita espacios en blanco al inicio y fin de cada celda de tipo `str`.                               |
| `df.ffill()`                                                    | Manejo de nulos.                                                           | Forward‑fill: rellena cada valor vacío con el último valor válido visto arriba en la misma columna. |
| `df.to_excel(path, index=False)`                                | Salvar la versión limpia.                                                  | Exporta el `DataFrame` a un nuevo Excel sin añadir la columna de índices de pandas.                 |
| `shutil.move(src, dst)`                                         | Resguardar el original.                                                    | Mueve físicamente el archivo de origen `src` a la carpeta de respaldo `dst`.                        |
| `class MiHandler(FileSystemEventHandler)`                       | Reacción a eventos de sistema de archivos.                                 | Hereda de `watchdog` y redefine `on_created` para interceptar nuevos archivos.                      |
| `event.is_directory`                                            | Ignorar carpetas creadas dentro de `data/`.                                | Sólo procesar archivos, no subdirectorios.                                                          |
| `time.sleep(1)`                                                 | Espera anticolisión.                                                       | Deja 1 s para que el archivo termine de copiarse antes de abrirlo.                                  |
| `Observer().schedule(handler, DATA_DIR, recursive=False)`       | Configuración del watcher.                                                 | Registra el manejador sobre la carpeta; `recursive=False` limita la vigilancia a un solo nivel.     |
| `observer.start()` / `observer.stop()`                          | Ciclo de vida del observador.                                              | Inicia o detiene el hilo interno de *watchdog*.                                                     |
| `print(f"[✓] Procesado: {nombre}")`                             | Feedback al usuario.                                                       | Mensajes claros en consola para cada acción realizada.                                              |

---


## 📄 ¿Para qué usarlo?

* **Consistencia** → tus notebooks o dashboards nunca se romperán por columnas fantasma o celdas vacías.
* **Trazabilidad** → los originales quedan preservados para auditoría y rollback.
* **Simplicidad de adopción** → cualquiera en el equipo sólo debe *copiar* su archivo a `data/`.
* **Huella mínima** → <120 líneas de código, sin frameworks pesados.

---

## 🚧 Hoja de ruta

* Soportar configuración YAML para reglas de limpieza.
* Integrar un sistema de logging detallado (rotating file handler).
* Procesar fuentes cloud (Google Drive, OneDrive) mediante sus APIs.


Hecho por Facundo Fornaroli 


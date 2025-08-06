import os
import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_path
import psycopg2

# 📌 Configuración base de datos
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "pdf-reader",
    "user": "postgres",
    "password": "1234"
}

def conectar_db():
    conn = psycopg2.connect(**DB_CONFIG)
    return conn

def crear_tabla_si_no_existe():
    conn = conectar_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS documentos (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            content TEXT
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

def guardar_en_db(nombre_archivo, texto):
    conn = conectar_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO documentos (name, content) VALUES (%s, %s);", (nombre_archivo, texto))
    conn.commit()
    cur.close()
    conn.close()

def extraer_texto_pdf(path_pdf):
    texto_total = ""

    try:
        doc = fitz.open(path_pdf)
        for pagina in doc:
            texto = pagina.get_text()
            texto_total += texto.strip()
        doc.close()
    except Exception as e:
        print(f"[ERROR] Error leyendo {path_pdf}: {e}")
        return None

    return texto_total if texto_total.strip() else None

def extraer_texto_ocr(path_pdf):
    texto_total = ""
    try:
        paginas = convert_from_path(path_pdf)
        for i, img in enumerate(paginas):
            texto = pytesseract.image_to_string(img)
            texto_total += f"\n[OCR Página {i+1}]\n{texto}"
    except Exception as e:
        print(f"[ERROR OCR] Error con {path_pdf}: {e}")
        return None

    return texto_total.strip()

def procesar_pdf(path_pdf):
    print(f"\n📄 Procesando: {path_pdf}")
    texto = extraer_texto_pdf(path_pdf)

    if texto:
        print("✅ Texto extraído directamente.")
    else:
        print("❌ No se encontró texto directo. Usando OCR...")
        texto = extraer_texto_ocr(path_pdf)
        if texto:
            print("✅ Texto extraído por OCR.")
        else:
            print("❌ OCR también falló.")

    return texto

def buscar_y_procesar_pdfs(directorio_base):
    crear_tabla_si_no_existe()

    for root, _, files in os.walk(directorio_base):
        for archivo in files:
            if archivo.lower().endswith(".pdf"):
                ruta_pdf = os.path.join(root, archivo)
                texto = procesar_pdf(ruta_pdf)
                if texto:
                    guardar_en_db(archivo, texto)
                    print(f"📥 Guardado en DB: {archivo}")
                else:
                    print(f"⚠️ No se pudo extraer texto de {archivo}")

# 📍 CAMBIA AQUÍ la ruta que quieras escanear
if __name__ == "__main__":
    carpeta = "/home/cristiansrc/Descargas/archivos/"  # ← cámbiala a tu ruta real
    buscar_y_procesar_pdfs(carpeta)
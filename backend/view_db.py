from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import os

def ver_base_de_datos():
    directorio_db = "chroma_db"
    
    if not os.path.exists(directorio_db):
        print("La base de datos aún no existe. No se ha guardado ninguna noticia.")
        return

    print("Cargando base de datos...")
    # Inicializamos la conexión a la base de datos local
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = Chroma(persist_directory=directorio_db, embedding_function=embeddings)
    
    # Obtenemos TODOS los documentos almacenados
    datos = vectorstore.get()
    documentos = datos.get("documents", [])
    metadatos = datos.get("metadatas", [])
    
    total = len(documentos)
    print(f"\n=============================================")
    print(f"Total de noticias guardadas en la memoria: {total}")
    print(f"=============================================\n")
    
    if total == 0:
        print("La base de datos está vacía.")
        return
        
    for i in range(total):
        print(f"--- NOTICIA {i+1} ---")
        print(f"Metadata: {metadatos[i]}")
        print(f"Contenido:\n{documentos[i]}")
        print("-" * 50 + "\n")

if __name__ == "__main__":
    ver_base_de_datos()

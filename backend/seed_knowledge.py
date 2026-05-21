from rag import load_knowledge_base


if __name__ == "__main__":
    vectorstore = load_knowledge_base()
    if vectorstore is None:
        print("No se encontraron documentos para cargar.")
    else:
        print("Conocimiento base cargado en ChromaDB.")

import faiss
import json
import numpy as np
import os
import asyncio
import tiktoken
from langchain.docstore.document import Document

from .model import embedding_model
from utils.data_utils import load_and_process_json_async

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

def load_source_documents():
    """
    Loads and processes source JSON documents from the data directory.
    This should return a list of LangChain Document objects.
    """
    print("Loading source documents...")
    
    async def process_all_files():
        tasks = []
        for filename in os.listdir(DATA_DIR):
            if filename.endswith(".json"):
                file_path = os.path.join(DATA_DIR, filename)
                tasks.append(load_and_process_json_async(file_path))
        
        processed_docs_list = await asyncio.gather(*tasks)
        
        all_docs = [doc for sublist in processed_docs_list for doc in sublist]
        # Create Document objects while preserving all metadata
        return [Document(page_content=doc.get('content', ''), 
                         metadata={'source': doc.get('title', 'N/A'), 
                                   'summary': doc.get('summary', ''), 
                                   'tags': doc.get('tags', [])}) for doc in all_docs]

    processed_documents = asyncio.run(process_all_files())
    print(f"Loaded and processed {len(processed_documents)} documents.")
    return processed_documents

def build_and_save_index(docs: list[Document], index_path="storage/vector_index.faiss", metadata_path="storage/metadata.json"):
    """
    Builds a FAISS index from documents and saves it to disk.
    """
    # Ensure the storage directory exists
    storage_dir = os.path.dirname(index_path)
    os.makedirs(storage_dir, exist_ok=True)

    print("Initializing embeddings model...")
    print("Generating embeddings for documents...")
    
    # Using tiktoken for token counting. This is a reasonable default.
    # If using a different model family, you might need a different tokenizer.
    tokenizer = tiktoken.get_encoding("cl100k_base")
    max_tokens_per_batch = 18000  # Keep it safely below the 20000 limit
    all_embeddings = []
    
    current_batch = []
    current_token_count = 0

    for doc in docs:
        doc_token_count = len(tokenizer.encode(doc.page_content))
        if current_token_count + doc_token_count > max_tokens_per_batch and current_batch:
            print(f"Processing batch with {len(current_batch)} documents and {current_token_count} tokens...")
            batch_embeddings = embedding_model.get_embeddings([d.page_content for d in current_batch])
            all_embeddings.extend(batch_embeddings)
            current_batch = []
            current_token_count = 0
        
        current_batch.append(doc)
        current_token_count += doc_token_count

    # Process the last remaining batch
    if current_batch:
        print(f"Processing final batch with {len(current_batch)} documents and {current_token_count} tokens...")
        batch_embeddings = embedding_model.get_embeddings([d.page_content for d in current_batch])
        all_embeddings.extend(batch_embeddings)
    
    doc_embeddings = all_embeddings
    
    embedding_dim = len(doc_embeddings[0])
    
    print(f"Creating FAISS index with dimension {embedding_dim}...")
    index = faiss.IndexFlatL2(embedding_dim)
    index.add(np.array(doc_embeddings, dtype=np.float32))
    
    print(f"Saving FAISS index to {index_path}...")
    faiss.write_index(index, index_path)
    
    # Save document metadata for later retrieval
    metadata = [{"page_content": doc.page_content, "metadata": doc.metadata} for doc in docs]
    print(f"Saving metadata to {metadata_path}...")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=4)

    print("Index building complete.")

def run_indexing_pipeline():
    """Main function to run the full indexing pipeline."""
    documents = load_source_documents()
    build_and_save_index(documents)

if __name__ == "__main__":
    run_indexing_pipeline()
# """
# Vector Store for AI Study Assistant
# Manages ChromaDB vector database with RAG capabilities
# """

# import chromadb
# from chromadb.config import Settings
# from typing import List, Dict, Any, Optional
# import openai
# import os
# from dotenv import load_dotenv
# from sentence_transformers import SentenceTransformer
# import uuid
# import json

# load_dotenv()

# class VectorStore:
#     def __init__(self, persist_directory: str = "./chroma_db"):
#         """
#         Initialize ChromaDB vector store with OpenAI embeddings
#         """
#         self.persist_directory = persist_directory
#         self.client = chromadb.PersistentClient(path=persist_directory)
        
#         # OpenAI setup
#         openai.api_key = os.getenv("OPENAI_API_KEY")
#         if not openai.api_key:
#             raise ValueError("OPENAI_API_KEY not found in .env file")
        
#         # Create or get collection
#         self.collection = self.client.get_or_create_collection(
#             name="study_documents",
#             metadata={"hnsw:space": "cosine"}
#         )
        
#         print(f"✅ VectorStore initialized at {persist_directory}")
    
#     def embed_documents(self, documents: List[str]) -> List[List[float]]:
#         """Generate embeddings using OpenAI"""
#         response = openai.Embedding.create(
#             input=documents,
#             model="text-embedding-ada-002"
#         )
#         return [data['embedding'] for data in response['data']]
    
#     def add_documents(self, documents: List[Dict[str, Any]], 
#                      user_id: str, filename: str) -> str:
#         """
#         Add processed documents to vector store
        
#         Args:
#             documents: List of document chunks from PDFProcessor
#             user_id: User identifier
#             filename: Original PDF filename
            
#         Returns:
#             Document ID for reference
#         """
#         doc_id = f"{user_id}_{uuid.uuid4().hex[:8]}_{filename}"
        
#         # Prepare data for ChromaDB
#         ids = []
#         embeddings = []
#         metadatas = []
#         documents_list = []
        
#         # Process each document chunk
#         for doc in documents:
#             chunk_id = f"{doc_id}_{doc['chunk_id']}"
#             ids.append(chunk_id)
#             documents_list.append(doc['content'])
            
#             metadata = {
#                 **doc.get('metadata', {}),
#                 "user_id": user_id,
#                 "doc_id": doc_id,
#                 "filename": filename,
#                 "source": doc['source'],
#                 "chunk_id": doc['chunk_id']
#             }
#             metadatas.append(metadata)
        
#         # Generate embeddings
#         print(f"🔄 Embedding {len(documents_list)} chunks...")
#         embeddings = self.embed_documents(documents_list)
        
#         # Add to collection
#         self.collection.add(
#             ids=ids,
#             embeddings=embeddings,
#             documents=documents_list,
#             metadatas=metadatas,
#             ids_exist_ok=True
#         )
        
#         print(f"✅ Added {len(documents)} chunks for {filename}")
#         return doc_id
    
#     def retrieve_context(self, query: str, user_id: str, k: int = 5) -> List[str]:
#         """
#         Retrieve relevant context using semantic search
        
#         Args:
#             query: User question
#             user_id: Filter by user
#             k: Number of results to return
            
#         Returns:
#             List of relevant document chunks
#         """
#         query_embedding = self.embed_documents([query])[0]
        
#         results = self.collection.query(
#             query_embeddings=[query_embedding],
#             n_results=k,
#             where={"user_id": user_id},
#             include=["documents", "metadatas"]
#         )
        
#         context = []
#         if results['documents'] and results['documents'][0]:
#             for i, doc in enumerate(results['documents'][0]):
#                 source_info = results['metadatas'][0][i].get('filename', 'Unknown')
#                 context.append(f"[{source_info}] {doc}")
        
#         return context
    
#     def generate_answer(self, question: str, context: List[str]) -> str:
#         """Generate answer using RAG pattern with GPT"""
#         context_text = "\n\n".join([f"Source: {ctx[:500]}..." for ctx in context[:3]])
        
#         system_prompt = """You are an expert AI Study Assistant. Answer questions based ONLY on the provided context from the user's uploaded notes/PDFs.

# IMPORTANT RULES:
# 1. Base your answer ONLY on the provided context
# 2. If context doesn't contain the answer, say "I couldn't find this information in your notes."
# 3. Be concise but complete
# 4. Reference specific parts of the context when possible
# 5. Format answers clearly with bullet points when appropriate"""

#         messages = [
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": f"""
# Context from your notes:
# {context_text}

# Question: {question}

# Answer:"""}
#         ]
        
#         response = openai.ChatCompletion.create(
#             model="gpt-3.5-turbo",
#             messages=messages,
#             temperature=0.1,
#             max_tokens=800
#         )
        
#         return response.choices[0].message.content.strip()
    
#     def get_user_documents(self, user_id: str) -> List[Dict[str, Any]]:
#         """Get summary of user's documents"""
#         results = self.collection.get(
#             where={"user_id": user_id},
#             include=["metadatas"]
#         )
        
#         if not results['metadatas']:
#             return []
        
#         # Group by document
#         doc_map = {}
#         for meta in results['metadatas']:
#             doc_id = meta['doc_id']
#             filename = meta['filename']
            
#             if doc_id not in doc_map:
#                 doc_map[doc_id] = {
#                     "doc_id": doc_id,
#                     "filename": filename,
#                     "chunks": 0,
#                     "created_at": meta.get('created_at', '')
#                 }
#             doc_map[doc_id]["chunks"] += 1
        
#         return list(doc_map.values())
    
#     def delete_document(self, doc_id: str):
#         """Delete all chunks for a document"""
#         self.collection.delete(where={"doc_id": doc_id})
#         print(f"🗑️ Deleted document: {doc_id}")
    
#     def get_collection_stats(self) -> Dict[str, Any]:
#         """Get collection statistics"""
#         return self.collection.count()

# # Test the vector store
# if __name__ == "__main__":
#     store = VectorStore()
#     print(f"Collection has {store.get_collection_stats()} documents")
"""
Vector Store for AI Study Assistant
Manages ChromaDB with OpenAI embeddings and GPT-powered answer generation.
"""

import os
import uuid
from typing import List, Dict, Any

import chromadb
from dotenv import load_dotenv

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

load_dotenv()


class VectorStore:
    def __init__(self, persist_directory: str = "./chroma_db"):
        """
        Initialize ChromaDB and OpenAI client.

        Raises:
            ImportError: if the openai package is not installed.
            ValueError:  if OPENAI_API_KEY is missing from the environment.
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package not found. Run: pip install openai>=1.0.0")

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found. Add it to your .env file.")

        self.client_openai = OpenAI(api_key=api_key)
        self.persist_directory = persist_directory

        # ChromaDB persistent client
        self.chroma = chromadb.PersistentClient(path=persist_directory)

        self.collection = self.chroma.get_or_create_collection(
            name="study_documents",
            metadata={"hnsw:space": "cosine"},
        )

        print(f"[VectorStore] Initialized — {self.collection.count()} chunks in store")

    # ─────────────────────────────────────────
    #  EMBEDDINGS
    # ─────────────────────────────────────────

    def _embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings via OpenAI text-embedding-3-small."""
        response = self.client_openai.embeddings.create(
            input=texts,
            model="text-embedding-3-small",
        )
        return [item.embedding for item in response.data]

    # ─────────────────────────────────────────
    #  ADD
    # ─────────────────────────────────────────

    def add_documents(
        self,
        documents: List[Dict[str, Any]],
        user_id: str,
        filename: str,
    ) -> str:
        """
        Embed and store document chunks in ChromaDB.

        Args:
            documents: Output of PDFProcessor.process_pdf()
            user_id:   Owner identifier for retrieval filtering.
            filename:  Original PDF filename.

        Returns:
            Unique doc_id string.
        """
        doc_id = f"{user_id}_{uuid.uuid4().hex[:8]}_{filename}"

        ids: List[str] = []
        texts: List[str] = []
        metadatas: List[Dict[str, Any]] = []

        for doc in documents:
            chunk_id = f"{doc_id}__{doc['chunk_id']}"
            ids.append(chunk_id)
            texts.append(doc["content"])
            metadatas.append({
                **doc.get("metadata", {}),
                "user_id": user_id,
                "doc_id": doc_id,
                "filename": filename,
                "source": doc.get("source", filename),
                "chunk_id": doc["chunk_id"],
            })

        print(f"[VectorStore] Embedding {len(texts)} chunks for '{filename}'…")
        embeddings = self._embed(texts)

        # ChromaDB add() does not accept ids_exist_ok; use upsert instead
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

        print(f"[VectorStore] Stored {len(texts)} chunks (doc_id={doc_id})")
        return doc_id

    # ─────────────────────────────────────────
    #  RETRIEVE
    # ─────────────────────────────────────────

    def retrieve_context(
        self,
        query: str,
        user_id: str,
        k: int = 5,
    ) -> List[str]:
        """
        Semantic search over a user's documents.

        Returns:
            List of relevant text chunks, prefixed with their source filename.
        """
        query_embedding = self._embed([query])[0]

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(k, self.collection.count()),
            where={"user_id": user_id},
            include=["documents", "metadatas"],
        )

        context: List[str] = []
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]

        for doc, meta in zip(docs, metas):
            source = meta.get("filename", "Unknown")
            context.append(f"[{source}] {doc}")

        return context

    # ─────────────────────────────────────────
    #  GENERATE
    # ─────────────────────────────────────────

    def generate_answer(self, question: str, context: List[str]) -> str:
        """
        Generate an answer with GPT using retrieved context (RAG pattern).
        """
        context_text = "\n\n".join(
            f"Source {i + 1}: {chunk[:600]}" for i, chunk in enumerate(context[:4])
        )

        system_prompt = (
            "You are an expert AI Study Assistant. "
            "Answer questions based ONLY on the provided context from the user's uploaded notes/PDFs.\n\n"
            "Rules:\n"
            "1. Base your answer strictly on the context.\n"
            "2. If the context does not contain the answer, say: "
            "'I couldn't find this information in your notes.'\n"
            "3. Be concise, accurate, and use bullet points where helpful.\n"
            "4. Cite which source (Source 1, Source 2, …) supports each point."
        )

        response = self.client_openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        f"Context from your notes:\n\n{context_text}\n\n"
                        f"Question: {question}\n\nAnswer:"
                    ),
                },
            ],
            temperature=0.1,
            max_tokens=800,
        )

        return response.choices[0].message.content.strip()

    # ─────────────────────────────────────────
    #  DOCUMENT MANAGEMENT
    # ─────────────────────────────────────────

    def get_user_documents(self, user_id: str) -> List[Dict[str, Any]]:
        """Return a summary list of documents belonging to a user."""
        results = self.collection.get(
            where={"user_id": user_id},
            include=["metadatas"],
        )

        doc_map: Dict[str, Dict[str, Any]] = {}
        for meta in results.get("metadatas", []):
            doc_id = meta["doc_id"]
            if doc_id not in doc_map:
                doc_map[doc_id] = {
                    "doc_id": doc_id,
                    "filename": meta.get("filename", "Unknown"),
                    "chunks": 0,
                }
            doc_map[doc_id]["chunks"] += 1

        return list(doc_map.values())

    def delete_document(self, doc_id: str) -> None:
        """Delete all chunks belonging to a document."""
        self.collection.delete(where={"doc_id": doc_id})
        print(f"[VectorStore] Deleted document: {doc_id}")

    def get_collection_stats(self) -> int:
        """Return total number of chunks in the collection."""
        return self.collection.count()


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    store = VectorStore()
    print(f"Collection has {store.get_collection_stats()} chunks")

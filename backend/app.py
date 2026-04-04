# from flask import Flask, request, jsonify, send_from_directory
# from flask_cors import CORS
# import os
# import chromadb
# from chromadb.config import Settings
# from langchain_community.document_loaders import PyPDFLoader
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_community.embeddings import HuggingFaceEmbeddings
# from langchain_community.llms import Ollama
# import PyPDF2
# from werkzeug.utils import secure_filename

# app = Flask(__name__)
# CORS(app)
# app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

# # Config
# UPLOAD_FOLDER = 'uploads'
# CHROMA_PATH = 'chroma-data'
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# os.makedirs(CHROMA_PATH, exist_ok=True)

# # Initialize ChromaDB
# chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
# embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
# llm = Ollama(model="llama2", base_url="http://localhost:11434")

# collection = chroma_client.get_or_create_collection(
#     name="study_notes",
#     metadata={"hnsw:space": "cosine"}
# )

# @app.route('/api/upload/documents', methods=['POST'])
# def upload_document():
#     if 'document' not in request.files:
#         return jsonify({'error': 'No file uploaded'}), 400
    
#     file = request.files['document']
#     if file.filename == '':
#         return jsonify({'error': 'No file selected'}), 400
    
#     if not file.filename.lower().endswith('.pdf'):
#         return jsonify({'error': 'Only PDF files allowed'}), 400
    
#     filename = secure_filename(file.filename)
#     filepath = os.path.join(UPLOAD_FOLDER, filename)
#     file.save(filepath)
    
#     try:
#         # Load PDF
#         loader = PyPDFLoader(filepath)
#         docs = loader.load()
        
#         # Split documents
#         splitter = RecursiveCharacterTextSplitter(
#             chunk_size=1000,
#             chunk_overlap=200
#         )
#         chunks = splitter.split_documents(docs)
        
#         # Create embeddings and store
#         texts = [doc.page_content for doc in chunks]
#         metadatas = [{"source": filename, "page": doc.metadata.get("page", 0)} for doc in chunks]
        
#         collection.add(
#             documents=texts,
#             metadatas=metadatas,
#             ids=[f"doc_{i}_{hash(filename)}" for i in range(len(texts))]
#         )
        
#         os.remove(filepath)
        
#         return jsonify({
#             'success': True,
#             'message': f'Processed {len(chunks)} chunks from {filename}',
#             'documentId': filename
#         })
    
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# @app.route('/api/query/ask', methods=['POST'])
# def ask_question():
#     data = request.json
#     question = data.get('question')
    
#     if not question:
#         return jsonify({'error': 'Question required'}), 400
    
#     try:
#         # Retrieve relevant chunks
#         results = collection.query(
#             query_texts=[question],
#             n_results=4
#         )
        
#         context = "\n\n".join(results['documents'][0])
        
#         # Generate answer
#         prompt = f"""
#         Answer the question based ONLY on the following context from user's notes.
#         If answer not in context, say "I couldn't find the answer in your notes."
        
#         Context:
#         {context}
        
#         Question: {question}
        
#         Answer:"""
        
#         answer = llm.invoke(prompt)
        
#         return jsonify({
#             'answer': answer,
#             'sources': [{
#                 'content': doc[:200] + '...' if len(doc) > 200 else doc,
#                 'index': i+1
#             } for i, doc in enumerate(results['documents'][0])]
#         })
    
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# @app.route('/api/docs', methods=['GET'])
# def get_documents():
#     try:
#         results = collection.get(include=['metadatas', 'documents'])
#         documents = []
        
#         for i, doc_id in enumerate(results['ids']):
#             doc = {
#                 'id': doc_id,
#                 'title': results['metadatas'][i].get('source', f'Document {i+1}'),
#                 'chunkCount': 1,
#                 'uploadDate': 'Recent',
#                 'preview': results['documents'][i][:200] + '...'
#             }
#             documents.append(doc)
        
#         return jsonify(documents[:10])  # Limit to 10
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

# @app.route('/api/docs/stats', methods=['GET'])
# def get_stats():
#     try:
#         count = collection.count()
#         return jsonify({
#             'totalDocuments': min(count // 10, 1),
#             'totalChunks': count,
#             'avgChunksPerDoc': count / max(1, count // 10),
#             'storageSize': f"{(count * 1000 / 1024 / 1024):.2f} MB"
#         })
#     except:
#         return jsonify({'totalDocuments': 0, 'totalChunks': 0})

# if __name__ == '__main__':
#     app.run(debug=True, port=5000)
"""
AI Study Assistant - Flask Backend
Main application entry point with all API routes
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from utils.pdf_processor import PDFProcessor
from utils.vector_store import VectorStore

load_dotenv()

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:5500", "*"])
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

# Config
UPLOAD_FOLDER = 'uploads'
CHROMA_PATH = 'chroma_db'
ALLOWED_EXTENSIONS = {'pdf'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CHROMA_PATH, exist_ok=True)

# Initialize services
pdf_processor = PDFProcessor(chunk_size=800, chunk_overlap=100)
vector_store = VectorStore(persist_directory=CHROMA_PATH)


def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ─────────────────────────────────────────────
#  UPLOAD
# ─────────────────────────────────────────────

@app.route('/upload', methods=['POST'])
def upload_document():
    """Upload and process a PDF document into the vector store."""
    if 'document' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'}), 400

    file = request.files['document']
    user_id = request.form.get('user_id', 'default_user')

    if not file or file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'success': False, 'message': 'Only PDF files are allowed'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4().hex}_{filename}")
    file.save(filepath)

    try:
        # Process PDF into chunks
        documents = pdf_processor.process_pdf(filepath)

        if not documents:
            return jsonify({'success': False, 'message': 'Could not extract text from PDF'}), 422

        # Store in vector database
        doc_id = vector_store.add_documents(documents, user_id=user_id, filename=filename)

        return jsonify({
            'success': True,
            'message': f'Processed {len(documents)} chunks from {filename}',
            'doc_id': doc_id,
            'chunk_count': len(documents)
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

    finally:
        # Always clean up temp file
        if os.path.exists(filepath):
            os.remove(filepath)


# ─────────────────────────────────────────────
#  ASK
# ─────────────────────────────────────────────

@app.route('/ask', methods=['POST'])
def ask_question():
    """Answer a question using RAG over the user's uploaded documents."""
    data = request.get_json() or {}
    question = data.get('question') or request.form.get('question', '').strip()
    user_id = data.get('user_id') or request.form.get('user_id', 'default_user')

    if not question:
        return jsonify({'success': False, 'message': 'Question is required'}), 400

    try:
        # Retrieve relevant context
        context_chunks = vector_store.retrieve_context(query=question, user_id=user_id, k=5)

        if not context_chunks:
            return jsonify({
                'success': True,
                'question': question,
                'answer': "I couldn't find any relevant information in your uploaded notes. Please upload a PDF first.",
                'context_sources': []
            })

        # Generate answer via LLM
        answer = vector_store.generate_answer(question=question, context=context_chunks)

        return jsonify({
            'success': True,
            'question': question,
            'answer': answer,
            'context_sources': [c[:200] + '...' if len(c) > 200 else c for c in context_chunks]
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ─────────────────────────────────────────────
#  DOCUMENTS
# ─────────────────────────────────────────────

@app.route('/documents/<user_id>', methods=['GET'])
def get_documents(user_id: str):
    """List all documents uploaded by a user."""
    try:
        docs = vector_store.get_user_documents(user_id=user_id)
        return jsonify({'success': True, 'documents': docs})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/document/<doc_id>', methods=['DELETE'])
def delete_document(doc_id: str):
    """Delete a document and all its chunks from the vector store."""
    try:
        vector_store.delete_document(doc_id=doc_id)
        return jsonify({'success': True, 'message': f'Document {doc_id} deleted'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/stats/<user_id>', methods=['GET'])
def get_stats(user_id: str):
    """Get statistics about a user's document library."""
    try:
        docs = vector_store.get_user_documents(user_id=user_id)
        total_chunks = sum(d.get('chunks', 0) for d in docs)
        return jsonify({
            'success': True,
            'total_documents': len(docs),
            'total_chunks': total_chunks,
            'avg_chunks_per_doc': round(total_chunks / max(len(docs), 1), 1)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ─────────────────────────────────────────────
#  HEALTH CHECK
# ─────────────────────────────────────────────

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'message': 'AI Study Assistant API is running'})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)

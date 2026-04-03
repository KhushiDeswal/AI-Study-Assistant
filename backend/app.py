from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import chromadb
from chromadb.config import Settings
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
import PyPDF2
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

# Config
UPLOAD_FOLDER = 'uploads'
CHROMA_PATH = 'chroma-data'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CHROMA_PATH, exist_ok=True)

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
llm = Ollama(model="llama2", base_url="http://localhost:11434")

collection = chroma_client.get_or_create_collection(
    name="study_notes",
    metadata={"hnsw:space": "cosine"}
)

@app.route('/api/upload/documents', methods=['POST'])
def upload_document():
    if 'document' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['document']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Only PDF files allowed'}), 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)
    
    try:
        # Load PDF
        loader = PyPDFLoader(filepath)
        docs = loader.load()
        
        # Split documents
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = splitter.split_documents(docs)
        
        # Create embeddings and store
        texts = [doc.page_content for doc in chunks]
        metadatas = [{"source": filename, "page": doc.metadata.get("page", 0)} for doc in chunks]
        
        collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=[f"doc_{i}_{hash(filename)}" for i in range(len(texts))]
        )
        
        os.remove(filepath)
        
        return jsonify({
            'success': True,
            'message': f'Processed {len(chunks)} chunks from {filename}',
            'documentId': filename
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/query/ask', methods=['POST'])
def ask_question():
    data = request.json
    question = data.get('question')
    
    if not question:
        return jsonify({'error': 'Question required'}), 400
    
    try:
        # Retrieve relevant chunks
        results = collection.query(
            query_texts=[question],
            n_results=4
        )
        
        context = "\n\n".join(results['documents'][0])
        
        # Generate answer
        prompt = f"""
        Answer the question based ONLY on the following context from user's notes.
        If answer not in context, say "I couldn't find the answer in your notes."
        
        Context:
        {context}
        
        Question: {question}
        
        Answer:"""
        
        answer = llm.invoke(prompt)
        
        return jsonify({
            'answer': answer,
            'sources': [{
                'content': doc[:200] + '...' if len(doc) > 200 else doc,
                'index': i+1
            } for i, doc in enumerate(results['documents'][0])]
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/docs', methods=['GET'])
def get_documents():
    try:
        results = collection.get(include=['metadatas', 'documents'])
        documents = []
        
        for i, doc_id in enumerate(results['ids']):
            doc = {
                'id': doc_id,
                'title': results['metadatas'][i].get('source', f'Document {i+1}'),
                'chunkCount': 1,
                'uploadDate': 'Recent',
                'preview': results['documents'][i][:200] + '...'
            }
            documents.append(doc)
        
        return jsonify(documents[:10])  # Limit to 10
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/docs/stats', methods=['GET'])
def get_stats():
    try:
        count = collection.count()
        return jsonify({
            'totalDocuments': min(count // 10, 1),
            'totalChunks': count,
            'avgChunksPerDoc': count / max(1, count // 10),
            'storageSize': f"{(count * 1000 / 1024 / 1024):.2f} MB"
        })
    except:
        return jsonify({'totalDocuments': 0, 'totalChunks': 0})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
/**
 * AI Study Assistant — Frontend Controller
 * Communicates with the Flask backend at http://localhost:8000
 */

class AIStudyAssistant {
  constructor() {
    this.userId = 'guest_' + Date.now();
    this.apiBase = 'http://localhost:8000';
    this._init();
  }

  _init() {
    this._bindEvents();
    this._loadDocuments();
    this._updateSessionUI();
    this._hideLoading();
  }

  // ─────────────────────────────────────────
  //  UI HELPERS
  // ─────────────────────────────────────────

  _hideLoading() {
    const el = document.getElementById('loading');
    if (el) {
      el.classList.add('hidden');
      setTimeout(() => el.remove(), 400);
    }
  }

  _updateSessionUI() {
    const idEl = document.getElementById('userId');
    const inputEl = document.getElementById('userIdInput');
    if (idEl) idEl.textContent = this.userId;
    if (inputEl) inputEl.value = this.userId;
  }

  _showView(viewName) {
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    const view = document.getElementById(viewName + 'View');
    const btn = document.querySelector(`.nav-btn[data-view="${viewName}"]`);
    if (view) view.classList.add('active');
    if (btn) btn.classList.add('active');
  }

  _showNotification(message, type = 'info') {
    // Remove any existing notifications
    document.querySelectorAll('.notification').forEach(n => n.remove());

    const el = document.createElement('div');
    el.className = `notification notification-${type}`;
    el.textContent = message;
    document.body.appendChild(el);

    // Animate in
    requestAnimationFrame(() => el.classList.add('visible'));
    setTimeout(() => {
      el.classList.remove('visible');
      setTimeout(() => el.remove(), 300);
    }, 3500);
  }

  // ─────────────────────────────────────────
  //  EVENT BINDING
  // ─────────────────────────────────────────

  _bindEvents() {
    // Navigation
    document.querySelectorAll('.nav-btn[data-view]').forEach(btn => {
      btn.addEventListener('click', () => this._showView(btn.dataset.view));
    });

    // Upload form
    const uploadForm = document.getElementById('uploadForm');
    if (uploadForm) {
      uploadForm.addEventListener('submit', e => {
        e.preventDefault();
        this._handleUpload();
      });
    }

    // Chat form — support Enter to send
    const chatForm = document.getElementById('chatForm');
    if (chatForm) {
      chatForm.addEventListener('submit', e => {
        e.preventDefault();
        this._handleQuestion();
      });
    }

    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
      chatInput.addEventListener('keydown', e => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this._handleQuestion();
        }
      });
    }

    // New session button
    const newSessionBtn = document.getElementById('newSession');
    if (newSessionBtn) {
      newSessionBtn.addEventListener('click', () => this._newSession());
    }

    // Upload modal open/close
    const uploadBtn = document.getElementById('uploadBtn');
    const closeModal = document.getElementById('closeModal');
    const modalOverlay = document.getElementById('uploadModal');

    if (uploadBtn) uploadBtn.addEventListener('click', () => this._openModal());
    if (closeModal) closeModal.addEventListener('click', () => this._closeModal());
    if (modalOverlay) {
      modalOverlay.addEventListener('click', e => {
        if (e.target === modalOverlay) this._closeModal();
      });
    }

    // Drag-and-drop on upload area
    const dropZone = document.getElementById('fileDropZone');
    if (dropZone) {
      dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('drag-over'); });
      dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
      dropZone.addEventListener('drop', e => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        const file = e.dataTransfer.files[0];
        if (file) this._setSelectedFile(file);
      });
    }

    // File input change
    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
      fileInput.addEventListener('change', e => {
        if (e.target.files[0]) this._setSelectedFile(e.target.files[0]);
      });
    }

    // Refresh stats
    const refreshStats = document.getElementById('refreshStats');
    if (refreshStats) {
      refreshStats.addEventListener('click', () => this._loadStats());
    }

    // Clear all docs
    const clearAllBtn = document.getElementById('clearAllBtn');
    if (clearAllBtn) {
      clearAllBtn.addEventListener('click', () => this._clearAllDocuments());
    }

    // Document search
    const docSearch = document.getElementById('docSearch');
    if (docSearch) {
      docSearch.addEventListener('input', e => this._filterDocuments(e.target.value));
    }
  }

  // ─────────────────────────────────────────
  //  MODAL
  // ─────────────────────────────────────────

  _openModal() {
    const modal = document.getElementById('uploadModal');
    if (modal) modal.classList.add('open');
  }

  _closeModal() {
    const modal = document.getElementById('uploadModal');
    if (modal) modal.classList.remove('open');
    this._resetUploadUI();
  }

  _resetUploadUI() {
    const form = document.getElementById('uploadForm');
    if (form) form.reset();

    const status = document.getElementById('uploadStatus');
    if (status) status.innerHTML = '';

    const progress = document.querySelector('.progress-bar');
    const fill = document.querySelector('.progress-fill');
    if (progress) progress.style.display = 'none';
    if (fill) fill.style.width = '0%';
  }

  _setSelectedFile(file) {
    const status = document.getElementById('uploadStatus');
    if (status) {
      status.innerHTML = `
        <div class="file-preview">
          <span class="file-preview-icon">📄</span>
          <span class="file-preview-name">${file.name}</span>
          <span class="file-preview-size">${(file.size / 1024).toFixed(1)} KB</span>
        </div>`;
    }
    // Programmatically assign to file input so FormData picks it up
    const dt = new DataTransfer();
    dt.items.add(file);
    const fileInput = document.getElementById('fileInput');
    if (fileInput) fileInput.files = dt.files;
  }

  // ─────────────────────────────────────────
  //  UPLOAD
  // ─────────────────────────────────────────

  async _handleUpload() {
    const fileInput = document.getElementById('fileInput');
    if (!fileInput || !fileInput.files.length) {
      this._showNotification('Please select a PDF file first.', 'warning');
      return;
    }

    const file = fileInput.files[0];
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      this._showNotification('Only PDF files are supported.', 'error');
      return;
    }

    const formData = new FormData();
    formData.append('document', file);
    formData.append('user_id', this.userId);

    const submitBtn = document.querySelector('#uploadForm button[type="submit"]');
    const btnText = submitBtn?.querySelector('.btn-text');
    const spinner = submitBtn?.querySelector('.spinner');
    const progressBar = document.querySelector('.progress-bar');
    const progressFill = document.querySelector('.progress-fill');

    // Show loading state
    if (submitBtn) submitBtn.disabled = true;
    if (btnText) btnText.style.display = 'none';
    if (spinner) spinner.style.display = 'inline-block';
    if (progressBar) progressBar.style.display = 'block';

    // Animate progress bar
    let progress = 0;
    const interval = setInterval(() => {
      progress = Math.min(progress + Math.random() * 15, 88);
      if (progressFill) progressFill.style.width = `${progress}%`;
    }, 250);

    try {
      const response = await fetch(`${this.apiBase}/upload`, {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();
      clearInterval(interval);

      if (progressFill) progressFill.style.width = '100%';

      if (result.success) {
        this._showNotification(
          `✅ Uploaded! ${result.chunk_count} chunks indexed from "${file.name}"`,
          'success'
        );
        await this._loadDocuments();
        await this._loadStats();
        setTimeout(() => this._closeModal(), 800);
      } else {
        throw new Error(result.message || 'Upload failed');
      }

    } catch (err) {
      clearInterval(interval);
      this._showNotification(`❌ Upload failed: ${err.message}`, 'error');
    } finally {
      setTimeout(() => {
        if (submitBtn) submitBtn.disabled = false;
        if (btnText) btnText.style.display = 'inline';
        if (spinner) spinner.style.display = 'none';
        if (progressBar) progressBar.style.display = 'none';
        if (progressFill) progressFill.style.width = '0%';
      }, 1000);
    }
  }

  // ─────────────────────────────────────────
  //  CHAT
  // ─────────────────────────────────────────

  async _handleQuestion() {
    const input = document.getElementById('chatInput');
    const question = input?.value.trim();
    if (!question) return;

    const messagesContainer = document.getElementById('messagesContainer');
    if (!messagesContainer) return;

    // Hide welcome message
    const welcome = messagesContainer.querySelector('.welcome-message');
    if (welcome) welcome.remove();

    input.value = '';
    this._addMessage('user', question);

    const thinkingEl = this._addMessage('assistant', '🤔 Searching your notes…', [], true);

    try {
      const response = await fetch(`${this.apiBase}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, user_id: this.userId }),
      });

      const result = await response.json();

      // Remove thinking message
      thinkingEl?.remove();

      if (result.success) {
        this._addMessage('assistant', result.answer, result.context_sources || []);
      } else {
        this._addMessage('assistant', `⚠️ ${result.message || 'Something went wrong.'}`);
      }

    } catch (err) {
      thinkingEl?.remove();
      this._addMessage(
        'assistant',
        '❌ Could not reach the server. Make sure the backend is running on port 8000.'
      );
    }

    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  _addMessage(sender, content, sources = [], isThinking = false) {
    const container = document.getElementById('messagesContainer');
    if (!container) return null;

    const el = document.createElement('div');
    el.className = `message ${sender}${isThinking ? ' thinking' : ''}`;

    let sourcesHtml = '';
    if (sources.length && sender === 'assistant') {
      sourcesHtml = `
        <div class="context-sources">
          <small><strong>📚 Sources used:</strong></small>
          ${sources.map((s, i) => `
            <div class="context-item">
              <span class="source-num">${i + 1}</span>
              ${s.length > 150 ? s.slice(0, 150) + '…' : s}
            </div>`).join('')}
        </div>`;
    }

    el.innerHTML = `
      <div class="message-content">
        <div class="message-bubble">${this._formatText(content)}</div>
        ${sourcesHtml}
      </div>`;

    container.appendChild(el);
    el.scrollIntoView({ behavior: 'smooth', block: 'end' });
    return el;
  }

  _formatText(text) {
    return text
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      .replace(/`(.+?)`/g, '<code>$1</code>')
      .replace(/\n/g, '<br>');
  }

  // ─────────────────────────────────────────
  //  DOCUMENTS
  // ─────────────────────────────────────────

  async _loadDocuments() {
    try {
      const response = await fetch(`${this.apiBase}/documents/${this.userId}`);
      const result = await response.json();

      const list = document.getElementById('documentsList');
      if (!list) return;

      if (!result.success || !result.documents.length) {
        list.innerHTML = '<p class="no-documents">No documents uploaded yet. Upload your first PDF! 📚</p>';
        return;
      }

      this._allDocs = result.documents; // cache for search filtering
      this._renderDocumentList(result.documents);

    } catch (err) {
      console.error('[loadDocuments]', err);
    }
  }

  _renderDocumentList(docs) {
    const list = document.getElementById('documentsList');
    if (!list) return;

    list.innerHTML = docs.map(doc => `
      <div class="document-card" data-id="${doc.doc_id}">
        <div class="document-header">
          <div class="document-info">
            <div class="document-name">📄 ${doc.filename}</div>
            <div class="document-stats">${doc.chunks} chunks indexed</div>
          </div>
          <button
            class="delete-btn"
            onclick="studyApp.deleteDocument('${doc.doc_id}')"
            title="Remove document"
          >
            🗑 Delete
          </button>
        </div>
      </div>`).join('');
  }

  _filterDocuments(query) {
    if (!this._allDocs) return;
    const filtered = query
      ? this._allDocs.filter(d => d.filename.toLowerCase().includes(query.toLowerCase()))
      : this._allDocs;
    this._renderDocumentList(filtered);
  }

  async deleteDocument(docId) {
    if (!confirm('Remove this document and all its indexed data?')) return;

    try {
      const response = await fetch(`${this.apiBase}/document/${docId}`, { method: 'DELETE' });
      const result = await response.json();

      if (result.success) {
        this._showNotification('✅ Document removed.', 'success');
        await this._loadDocuments();
        await this._loadStats();
      } else {
        throw new Error(result.message);
      }
    } catch (err) {
      this._showNotification(`❌ Failed to delete: ${err.message}`, 'error');
    }
  }

  async _clearAllDocuments() {
    if (!this._allDocs?.length) return;
    if (!confirm(`Remove all ${this._allDocs.length} document(s)? This cannot be undone.`)) return;

    for (const doc of this._allDocs) {
      try {
        await fetch(`${this.apiBase}/document/${doc.doc_id}`, { method: 'DELETE' });
      } catch (_) { /* continue */ }
    }

    this._showNotification('🗑 All documents cleared.', 'info');
    await this._loadDocuments();
    await this._loadStats();
  }

  // ─────────────────────────────────────────
  //  STATS
  // ─────────────────────────────────────────

  async _loadStats() {
    try {
      const response = await fetch(`${this.apiBase}/stats/${this.userId}`);
      const result = await response.json();

      if (result.success) {
        const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
        set('totalDocs', result.total_documents);
        set('totalChunks', result.total_chunks);
        set('avgChunks', result.avg_chunks_per_doc);
      }
    } catch (err) {
      console.error('[loadStats]', err);
    }
  }

  // ─────────────────────────────────────────
  //  SESSION
  // ─────────────────────────────────────────

  _newSession() {
    this.userId = 'guest_' + Date.now();
    this._updateSessionUI();

    const container = document.getElementById('messagesContainer');
    if (container) container.innerHTML = `
      <div class="welcome-message">
        <i class="fas fa-robot welcome-icon"></i>
        <h2>Welcome to your AI Study Assistant!</h2>
        <p>Upload your PDFs and notes, then ask questions grounded in your materials.</p>
      </div>`;

    this._allDocs = [];
    this._loadDocuments();
    this._showNotification('🆕 New session started!', 'info');
  }
}

// ─────────────────────────────────────────────────────────────────────────────
//  Bootstrap
// ─────────────────────────────────────────────────────────────────────────────
const studyApp = new AIStudyAssistant();

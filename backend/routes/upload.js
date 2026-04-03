const express = require('express');
const multer = require('multer');
const path = require('path');
const vectorStore = require('../services/vectorStore');
const fs = require('fs');

const router = express.Router();
const upload = multer({ dest: 'uploads/' });

// Initialize vector store on startup
vectorStore.initVectorStore();

router.post('/documents', upload.single('document'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No file uploaded' });
    }

    const filePath = req.file.path;
    
    // Process document
    const result = await vectorStore.addDocument(filePath);
    
    res.json({
      success: true,
      message: `Successfully processed ${result.count} chunks`,
      documentId: `doc_${Date.now()}`
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;

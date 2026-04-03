const express = require('express');
const cors = require('cors');
const multer = require('multer');
const path = require('path');
const dotenv = require('dotenv');

dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;
// Middleware

app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use(express.static('chroma-data'));

// Routes
app.use('/api/upload', require('./routes/upload'));
app.use('/api/query', require('./routes/query'));
app.use('/api/docs', require('./routes/docs'));

app.listen(PORT, () => {
  console.log('Server running on http://localhost:${PORT}');
});
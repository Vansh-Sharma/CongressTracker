const express = require('express');
const axios = require('axios');
const path = require('path');
const cors = require('cors');

const app = express();
const port = 3000;

app.use(cors());
app.use(express.static(path.join(__dirname, 'public')));

app.get('/api/bills', async (req, res) => {
    try {
        const response = await axios.get('http://localhost:5001/api/bills', { params: req.query });
        res.json(response.data);
    } catch (error) {
        res.status(500).json({ error: 'Failed to fetch data' });
    }
});

app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'src/views/index.html'));
});

app.listen(port, () => {
    console.log(`Server is running at http://localhost:${port}`);
});

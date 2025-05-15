const express = require('express');
const app = express();
const port = process.env.PORT || 3000;

// Middleware to parse JSON requests
app.use(express.json());

// Sample route for getting menu items
app.get('/api/menu', (req, res) => {
    res.json({ message: 'List of menu items' });
});

// Sample route for adding a menu item
app.post('/api/menu', (req, res) => {
    const newItem = req.body;
    // Logic to add the new item would go here
    res.status(201).json({ message: 'Menu item added', item: newItem });
});

// Start the server
app.listen(port, () => {
    console.log(`Menu service running on http://localhost:${port}`);
});
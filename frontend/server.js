const express = require('express');
const path = require('path');
const app = express();
const port = 3200;

// 設定 View Engine
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// 設定靜態檔案
app.use(express.static(path.join(__dirname, 'public')));

// 首頁
app.get('/', (req, res) => {
    res.render('index');
});

app.listen(port, () => {
    console.log(`Frontend Server running at http://localhost:${port}`);
});


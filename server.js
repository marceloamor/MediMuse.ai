const http = require('http');
const fs = require('fs');
const path = require('path');

const server = http.createServer((req, res) => {
  let filePath = '.' + req.url;
  if (filePath === '/') {
    filePath = './index.html';
  } else if (req.url.startsWith('/src/data/')) {
    filePath = '.' + req.url;
  }

  const extname = path.extname(filePath);
  let contentType = 'text/html';
  switch (extname) {
    case '.js':
      contentType = 'text/javascript';
      break;
    case '.css':
      contentType = 'text/css';
      break;
    case '.json':
      contentType = 'application/json';
      break;
    case '.png':
      contentType = 'image/png';
      break;
    case '.jpg':
    case '.jpeg':
      contentType = 'image/jpg';
      break;
    case '.gif':
      contentType = 'image/gif';
      break;
  }

  console.log("Filepath:", filePath); fs.readFile(path.join(__dirname, filePath), (error, content) => {
    if (error) {
      if (error.code == 'ENOENT') {
        res.writeHead(404);
        res.end('404 Not Found');
      } else if (error.code === 'EISDIR') {
        res.writeHead(403);
        res.end('403 Forbidden: Directory listing not allowed');
      } else {
        res.writeHead(500);
        res.end('500 Internal Server Error: ' + error.code);
      }
    } else {
      res.writeHead(200, { 'Content-Type': contentType });
      res.end(content, 'utf-8');
    }
  });

});

const PORT = 3001;

server.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}/`);
});
const { createProxyMiddleware } = require('http-proxy-middleware');
const fs = require('fs');
const path = require('path');

module.exports = function(app) {
  let targetPort = 5000;
  
  // Try to parse the parent directory's .env file to get FLASK_PORT
  try {
    const envPath = path.resolve(__dirname, '../../.env');
    if (fs.existsSync(envPath)) {
      const envContent = fs.readFileSync(envPath, 'utf8');
      const match = envContent.match(/^FLASK_PORT=(\d+)/m);
      if (match && match[1]) {
        targetPort = parseInt(match[1], 10);
      }
    }
  } catch (e) {
    console.warn("Could not read .env to determine FLASK_PORT, defaulting to 5000");
  }

  app.use(
    ['/api', '/auth', '/reports'],
    createProxyMiddleware({
      target: `http://localhost:${targetPort}`,
      changeOrigin: true,
    })
  );
};

const app = require('./src/server');

const PORT = process.env.PORT || 5000

app.listen(PORT, () => console.log(`Scraper API listening on port ${PORT}`))

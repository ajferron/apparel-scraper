const express = require('express')
const app = express()
const lib = require('./lib')
const puppeteer = require('puppeteer');
const Promise = require('bluebird');
const fs = require('fs');

var page;

const bodyParser = require('body-parser')
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({
  extended: true
}));

(async () => {

  var executablePath = process.env.EXECUTABLE_PATH;

  if (!executablePath) {
    try {
      fs.accessSync('/usr/bin/chromium-browser');
      executablePath = '/usr/bin/chromium-browser';
    } catch (e) {
    }
  }

  var headless = true;

  if (process.env.HEADLESS === 'false') {
    headless = false;
  }

  var options = {
    headless: headless,
    slowMo: process.env.SLOW_MO || 250,
    executablePath: executablePath,
    args: [
      '--disable-dev-shm-usage',
      // eventually should be removed
      '--no-sandbox',
      '--disable-setuid-sandbox'
    ]
  }

  if (process.env.USER_DATA_DIR) {
    options.userDataDir = process.env.USER_DATA_DIR;
  }

  const browser = await puppeteer.launch(options);

  var pages = await browser.pages()
  page = pages[0];

  await page.setViewport({
    width: 1366,
    height: 1768
  });

  if (process.env.USER_AGENT) {
    await page.setUserAgent(process.env.USER_AGENT);
  }

  console.log('Browser loaded');
})();

app.all('/', async (req, res) => {

  var options = {
    url: req.body.url || 'http://localhost:3050',
    pageFunction: eval(`(${req.body.pageFunction})`),
    delay: req.body.delay,
    userAgent: req.body.userAgent
  }

  var result = await lib(page, options);
  res.json(result);
})

module.exports = app;

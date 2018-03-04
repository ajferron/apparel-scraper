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

  var executablePath;

  try {
    fs.accessSync('/usr/bin/chromium-browser');
    executablePath = '/usr/bin/chromium-browser';
  } catch (err) {
  }

  const browser = await puppeteer.launch({
    //headless: false,
    headless: true,
    slowMo: 250,
    executablePath: executablePath,
    args: [
      '--disable-dev-shm-usage',

      // eventually should be removed
      '--no-sandbox',
      '--disable-setuid-sandbox'
    ]
  });

  page = await browser.newPage();

  await page.setViewport({
    width: 1366,
    height: 1768
  });

  if (process.env.userAgent) {
    await page.setUserAgent(process.env.userAgent);
  }
  console.log('browser loaded');
})();

app.get('/', async (req, res) => {

  var options = {
    url: req.body.url || 'http://localhost:3050',
    pageFunction: eval(`(${req.body.pageFunction})`),
    delay: req.body.delay,
    userAgent: req.body.userAgent
  }

  var result = await lib(page, options);
  res.json(result)
})

module.exports = app;

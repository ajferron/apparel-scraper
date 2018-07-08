const express = require('express')
const app = express()
const lib = require('./lib')
const puppeteer = require('puppeteer');
const Promise = require('bluebird');
const fs = require('fs');
const proxyChain = require('proxy-chain');

const bodyParser = require('body-parser')
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({
  extended: true
}));

var browser;

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

  var args = [
    '--disable-dev-shm-usage',
    // eventually should be removed
    '--no-sandbox',
    '--disable-setuid-sandbox'
  ];

  //--disk-cache-size=0

  if (process.env.PROXY_URL) {
    const newProxyUrl = await proxyChain.anonymizeProxy(process.env.PROXY_URL);
    args.push(`--proxy-server=${newProxyUrl}`);
  }

  var options = {
    headless: headless,
    slowMo: process.env.SLOW_MO || 250,
    executablePath: executablePath,
    args: args
  }

  if (process.env.USER_DATA_DIR) {
    options.userDataDir = process.env.USER_DATA_DIR;
  }

  browser = await puppeteer.launch(options);

  console.log('Browser loaded');
})();

app.all('/', async (req, res) => {

  var options = {
    url: req.body.url || 'http://localhost:3050',
    pageFunction: eval(`(${req.body.pageFunction})`),
    delay: req.body.delay,
    noCookies: req.body.noCookies,
    userAgent: req.body.userAgent
  }

  var result = await lib(browser, options);
  res.json(result);
})

module.exports = app;

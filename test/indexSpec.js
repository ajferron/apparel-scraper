'use strict';

var assert = require('assert');
var page;
const puppeteer = require('puppeteer');
const lib = require('./../lib')
const Promise = require('bluebird');
const PORT = 3050;
var browser;

const express = require('express')
const app = express()

describe('elastic service', function() {

  before(async function() {
    browser = await puppeteer.launch({
      headless: true
    });

    page = await browser.newPage();

    await page.setViewport({
      width: 1366,
      height: 1768
    });

    var userAgent = 'TestAgent'
    await page.setUserAgent(userAgent);
    app.get('/', (req, res) => {
      res.send('<p>Hello World!</p>');
    })

    app.get('/agent', (req, res) => {
      //console.log(req.headers);
      res.send(`<p>${req.headers['user-agent']}</p>`);
    })

    await new Promise(resolve => {
      app.listen(PORT, () => {
        return resolve();
      })
    })
  })

  after(async function() {
    await browser.close();
  })

  it('open page and check results', async function test() {

    var result = await lib(page, {
      url: `http://127.0.0.1:${PORT}`
    })
    assert.equal(result, '<html><head></head><body><p>Hello World!</p></body></html>');
  })

  it('open page and check results', async function test() {

    var result = await lib(page, {
      url: `http://127.0.0.1:${PORT}`,
      pageFunction: function($) {
        return $('p').text();
      }
    })
    assert.equal(result, 'Hello World!');
  })

  it('open page and check user agent', async function test() {

    var result = await lib(page, {
      url: `http://127.0.0.1:${PORT}/agent`,
      pageFunction: function($) {
        return $('p').text();
      }
    })
    assert.equal(result, 'TestAgent');
  })
})

'use strict';

var assert = require('assert');
const Promise = require('bluebird');

const express = require('express')
const app = express()
const server = require('./../server')
const PORT = 3050;
const PORT2 = 3051;
const request = require('superagent');

describe('elastic service', function() {

  before(async function() {

    app.get('/', (req, res) => {
      res.send('<p>Hello World!</p>');
    })

    app.get('/agent', (req, res) => {
      res.send(`<p>${req.headers['user-agent']}</p>`);
    })

    await new Promise(resolve => {
      app.listen(PORT, () => {
        return resolve();
      })
    })

    await new Promise(resolve => {
      server.listen(PORT2, () => {
        return resolve();
      })
    })
    .delay(5000)
  })

  it('open page and check results', function test(done) {

    request
    .get('http://localhost:3051')
    .send({
      url: 'http://localhost:3050',
      pageFunction: 'function($) { return $("p").text(); }'
    })
    .end((err, res) => {
      assert.equal(res.body, 'Hello World!');
      done();
    });
  })

  it('open page and check user agent', function test(done) {

    request
    .get('http://localhost:3051')
    .send({
      url: 'http://localhost:3050/agent',
      userAgent: 'TestAgent',
      pageFunction: 'function($) { return $("p").text(); }'
    })
    .end((err, res) => {
      assert.equal(res.body, 'TestAgent');
      done();
    });
  })

})

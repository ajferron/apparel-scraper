const express = require('express');
const puppeteer = require('puppeteer');
const bodyParser = require('body-parser');
const {v4: uuid} = require('uuid');

const scraper = require('./scraper');
const {expressLogger} = require('./logger');


const app = express();

app.use(expressLogger());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({extended: true}));

var browser;

(async () => {
    browser = await puppeteer.launch({
        slowMo: process.env.SLOW_MO || 250,
        headless: true,
    });
})();


app.all('/', async(req, res) => {
    var spec = {
        feed: {
            urls: `[string, string, ...] || ["http://localhost:${process.env.PORT}"]`,
            extractor: 'function($) {...} || null',
            viewport: 'object || {width: 0, height: 0}',
            cookies: 'object || {}',
            userAgent: 'string || "web-scraper"',
            delay: 'number (ms)',
            login: {
                'form_url': 'string',
                'submit_btn': 'string',
                'fields': {
                    '#username': 'string',
                    '#password': 'string'
                }
            }
        },
        status: {
            scrape_id: 'string'
        }
    };

    res.json(spec);
});


app.post('/feed', async(req, res) => {
    try {
        var options = {
            urls: req.body.urls || [`http://localhost:${process.env.PORT}`],
            extractor: eval(`(${req.body.extractor})`),
            viewport: req.body.viewport || {width: 0, height: 0},
            userAgent: req.body.userAgent || "web-scraper",
            delay: req.body.delay || 250,
            login: req.body.login || null,
            scrapeid: req.body.scrapeid || uuid()
        };

        // Don't await scraper(...), add callback to update Redis & DB

        res.json(await scraper(browser, options));

    } catch(e) {
        res.json({data: null, error: e});
    }
});


app.get('/status', async(req, res) => {
    res.json({});
});


module.exports = app;

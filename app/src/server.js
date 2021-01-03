const express = require('express');
const redis = require("redis");
const puppeteer = require('puppeteer');
const bodyParser = require('body-parser');
const {v4: uuid} = require('uuid');
const fs = require('fs');

const scraper = require('./scraper');
const {ExpressLogger, Logger} = require('./logger');


const app = express();
const logger = Logger('Scrape API');
const client = redis.createClient('redis://redis:6379');

client.on('connect', () => logger.info('Connected to Redis'));

app.use(ExpressLogger());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({extended: true}));


var browser;

(async () => {
    var executablePath = process.env.EXECUTABLE_PATH;

    if (!executablePath) {
        try {
            fs.accessSync('/usr/bin/chromium-browser');
            executablePath = '/usr/bin/chromium-browser';
        } catch (e) {
            // pass
        }
    }

    browser = await puppeteer.launch({
        headless: true,
        slowMo: process.env.SLOW_MO || 250,
        executablePath: executablePath,
        args: [
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox'
        ]
    });

    logger.info('Browser launched')
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
        var meta = {
            job_id: req.body.job_id || uuid(),
            urls: req.body.urls || [],
            extractor: req.body.extractor || '$ => null',
            viewport: req.body.viewport || {width: 0, height: 0},
            userAgent: req.body.userAgent || "web-scraper",
            delay: req.body.delay || 250,
            login: req.body.login || null,
        };

        meta.urls.forEach(({id}) => {
            client.set(id, '', () => logger.info(`Redis: set ${id}`));
        });

        scraper(browser, meta).then(output => {
            logger.info(`Completed scrape job!\n${output}`)
            
            if (output.data)
                meta.urls.map((url, i) => ({
                    id: url.id || uuid(), 
                    data: JSON.stringify(output.data[i])

                })).forEach(({id, data}) => {
                    client.set(id, data, () => logger.info(`Redis: updated ${id}`));
                });
        })

        res.json({data: {meta}, error: null});

    } catch(e) {
        res.json({data: null, error: e});
    }
});


app.get('/status', async(req, res) => {
    await client.get(req.body.scrape_id || '', () => {
        res.json({data: output, error: null});
    });
});


module.exports = app;

const express = require('express');
const puppeteer = require('puppeteer');
const bodyParser = require('body-parser');
const {createClient} = require("redis");
const {v4: uuid} = require('uuid');
const fs = require('fs');

const scraper = require('./scraper');
const pg = require('../lib/postgres');
const {ExpressLogger, Logger} = require('../lib/logger');

const app = express();
const logger = Logger('Scrape API');
const redis = createClient(process.env.REDIS_URL);

app.use(ExpressLogger());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({extended: true}));

redis.on('connect', () => logger.info('Connected to Redis'));

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


app.all('/', async (req, res) => {
    var spec = {
        feed: {
            urls: `[{url:'', id:''}, ...] || ["http://localhost:${process.env.PORT}"]`,
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


app.post('/feed', async (req, res) => {
    try {
        const meta = {
            job_id: req.body.job_id || uuid(),
            urls: req.body.urls || [],
            extractor: req.body.extractor || '$ => null',
            viewport: req.body.viewport || {width: 0, height: 0},
            userAgent: req.body.userAgent || "web-scraper",
            delay: req.body.delay || 250,
            login: req.body.login || null,
        };

        const redis_cleaner = (err, res) => {
            meta.urls.map(url => url.id || uuid()).forEach(id => {
                redis.del(id, () => logger.info(`Redis: removed ${id}`));
            });
        }

        meta.urls.forEach(({id}) => {
            redis.set(id, '', () => logger.info(`Redis: set ${id}`));
        });

        scraper(browser, meta)
            .then(result => {
                logger.info(`Completed scrape job!\n${result}`)

                result.data?.forEach(async ({scrape_id, output}) => {
                    // Check # of rows updated. If none, push to db

                    await pg.update({
                        table: 'product_uploads', 
                        columns: {'result':JSON.stringify(output), 'status':'scraped'}, 
                        filters: {'scrape_id':scrape_id}, 
                        callback: redis_cleaner
                    })
                })
            })
            .catch(async () => {
                logger.error(`Failed scrape job!`)

                const output = {'error': 'Failed to upload'}

                await pg.update({
                    table: 'product_uploads', 
                    columns: {'result':JSON.stringify(output), 'status':'failed'},
                    filters: {'job_id':meta.job_id}, 
                    callback: redis_cleaner
                })
            })

        res.json({data: {meta}, error: null});

    } catch(e) {
        res.json({data: null, error: e});
    }
});


app.get('/status', async (req, res) => {
    await redis.get(req.body.scrape_id || '', () => {
        res.json({data: output, error: null});
    });
});


module.exports = app;

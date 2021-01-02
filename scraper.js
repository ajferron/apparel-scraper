const cheerio = require('cheerio');
const {scrapeLogger} = require('./logger');

const logger = scrapeLogger()


const scraper = async (browser, options) => {
    options = options || {};

    const page = await browser.newPage();

    logger.info(`<${options.scrapeid}> Starting scrape job...`);

    if (options.userAgent)
        await page.setUserAgent(options.userAgent);

    if (options.login) {
        logger.info(`<${options.scrapeid}> Logging in...`);

        const loginPage = await browser.newPage();
        const {form_url, submit_btn, fields} = options.login;

        if (!form_url)
            return {data: null, error: 'No form URL for login'};

        if (!submit_btn)
            return {data: null, error: 'No submit button for login form'};

        await loginPage.setViewport({width: 0, height: 0});
        await loginPage.goto(form_url);

        for (const [selector, val] of Object.entries(fields)) {
            logger.info(`<${options.scrapeid}> Populating form field '${selector}'...`);

            await loginPage.waitFor(selector);
            await loginPage.type(selector, val);
        }

        logger.info(`<${options.scrapeid}> Submitting form...`);

        loginPage.evaluate(s => document.querySelector(s).click(), submit_btn);

        await loginPage.waitForNavigation();
        await loginPage.close();

        logger.info(`<${options.scrapeid}> Login attempt complete!`);
    }

    var output = []
    
    await Promise.all(options.urls.map(async (url, i) => {
        logger.info(`<${options.scrapeid}> Scraping ${i+1}/${options.urls.length} (${url})`);

        await page.setViewport(options.viewport);
        await page.goto(url);
        await page.waitFor(options.delay);

        logger.info(`<${options.scrapeid}> Extracting content...`);

        const html = await page.content();

        if (options.extractor) {
            var $ = cheerio.load(html);

            output.push({url, output: options.extractor($)});

        } else {
            output.push({url, output: html});
        }

        logger.info(`<${options.scrapeid}> Scrape ${i+1}/${options.urls.length} complete!`);

        await page.close();
    }))

    logger.info(`<${options.scrapeid}> Scrape complete!`);

    return {data: output, scrapeid: options.scrapeid, error: null};
}


module.exports = scraper

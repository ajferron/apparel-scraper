const $ = require('cheerio');
const {Logger} = require('./logger');


const scraper = async (browser, options) => {
    options = options || {};

    const page = await browser.newPage();
    const logger = Logger('Scrape Job');

    logger.info(`<> Starting scrape job...`);

    if (options.userAgent)
        await page.setUserAgent(options.userAgent);

    if (options.login) {
        logger.info(`<> Logging in...`);

        const loginPage = await browser.newPage();
        const {form_url, submit_btn, fields} = options.login;

        if (!form_url)
            return {data: null, error: 'No form URL for login'};

        if (!submit_btn)
            return {data: null, error: 'No submit button for login form'};

        await loginPage.setViewport({width: 0, height: 0});
        await loginPage.goto(form_url);

        for (const [selector, val] of Object.entries(fields)) {
            logger.info(`<> Populating form field '${selector}'...`);

            await loginPage.waitFor(selector);
            await loginPage.type(selector, val);
        }

        logger.info(`<> Submitting form...`);

        loginPage.evaluate(s => document.querySelector(s).click(), submit_btn);

        await loginPage.waitForNavigation();
        await loginPage.close();

        logger.info(`<> Login attempt complete!`);
    }

    var output = []

    await Promise.all(options.urls.map(async (scrape, i) => {
        const {urls, viewport, delay, extractor} = options;

        logger.info(`<> Scraping ${i+1}/${urls.length} (${scrape.url})`);

        await page.setViewport(viewport);
        await page.goto(scrape.url);
        await page.waitFor(delay);

        logger.info(`<> Extracting content...`);

        const html = await page.content();

        output.push({
            scrape_id: scrape.id, 
            output: eval(extractor)($.load(html)) || html
        })

        logger.info(`<> Scrape ${i+1}/${urls.length} complete!`);

        await page.close();
    }))

    logger.info(`<> Scrape complete!`);

    return {data: output, error: null};
}


module.exports = scraper

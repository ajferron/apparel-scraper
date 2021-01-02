const cheerio = require('cheerio');


const scraper = async (browser, options) => {
    options = options || {};

    const page = await browser.newPage();

    if (options.userAgent)
        await page.setUserAgent(options.userAgent);

    if (options.login) {
        const loginPage = await browser.newPage();
        const {form_url, submit_btn, fields} = options.login;

        if (!form_url)
            return {data: null, error: 'No form URL for login'};

        if (!submit_btn)
            return {data: null, error: 'No submit button for login form'};

        await loginPage.setViewport({width: 0, height: 0});
        await loginPage.goto(form_url);

        for (const [selector, val] of Object.entries(fields)) {
            await loginPage.waitFor(selector);
            await loginPage.type(selector, val);
        }

        loginPage.evaluate(s => document.querySelector(s).click(), submit_btn)

        await loginPage.waitForNavigation();
        await loginPage.close();
    }

    data = options.urls.map(async url => {
        await page.setViewport(options.viewport);
        await page.goto(url);
        await page.waitFor(options.delay);
    
        const html = await page.content();

        await page.close();

        if (options.extractor) {
            var $ = cheerio.load(html);

            return options.extractor($)
        }

        return html;
    })

    return {data, error: null}
}


module.exports = scraper

const cheerio = require('cheerio');
const Promise = require('bluebird');
const defaultCheerioOptions = {
  normalizeWhitespace: false,
  xmlMode: false,
  decodeEntities: true
};

/**
 * @TODO
 * url
 * pageFunction | if there is no return full html
 * delay between requests
 * proxy | no proxy
 * cookies (should be parsed properly)
 * userAgent
 * viewport | 1366 x 1768 | etc
 * screenshot path | or false
 * there should be lock function which forbid async working (or queue)
 */
module.exports = async function(browser, options) {

  var page = await browser.newPage();

  await page.setViewport({
    width: 1366,
    height: 1768
  });

  options = options || {};

  if (options.noCookies) {
    await page._client.send('Network.clearBrowserCookies');
  }

  if (!options.url) {
    throw new Error('Please provide url');
  }

  if (options.userAgent) {
    await page.setUserAgent(options.userAgent);
  }

  if (options.cookies) {
    await Promise.all(options.cookies).map(async cookie => {
      await page.setCookie(cookie);
    })
  }

  await page.goto(options.url);
  await page.waitFor(options.delay || 200);

  //await page.screenshot({path: './example.png'});

  var html = await page.content();

  if (options.pageFunction) {
    var $ = cheerio.load(html, defaultCheerioOptions);
    await page.close();
    return options.pageFunction($);
  }



  await page.close();
  return html;
}

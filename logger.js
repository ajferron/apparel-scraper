const { transports, format, createLogger } = require('winston');
const expressWinston = require('express-winston');

const { splat, combine, timestamp, printf, colorize } = format;


const expressFormat = printf(({ timestamp, level, message, meta }) => {
    return `Scaper API - ${level} - [${timestamp}] : "${message}" ${meta.res?.statusCode}`;
});


const scraperFormat = printf(({ timestamp, level, message, meta }) => {
    return `Scrape Job - ${level} - [${timestamp}] : "${message}"`;
});


const expressLogger = () => {
    return expressWinston.logger({
        level: process.env.LOG_LEVEL || 'info',
        levels: {error: 0, warn: 1, info: 2},
        transports: [new transports.Console()],
        format: combine(colorize(), timestamp(), splat(), expressFormat),
        colorize: true,
    });
}


const scrapeLogger = () => {
    return createLogger({
        level: process.env.LOG_LEVEL || 'info',
        levels: {error: 0, warn: 1, info: 2},
        transports: [new transports.Console()],
        format: combine(colorize(), timestamp(), splat(), scraperFormat),
        colorize: true,
    })
}


module.exports = {expressLogger, scrapeLogger}

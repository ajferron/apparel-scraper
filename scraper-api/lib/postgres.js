const {Pool} = require('pg');
const {parse} = require('pg-connection-string')
const {Logger} = require('./logger');


const pool = (() => {
    // https://help.heroku.com/MDM23G46/why-am-i-getting-an-error-when-i-upgrade-to-pg-8

    const config = parse(`${process.env.DATABASE_URL}?ssl=true`);
    config.ssl = {rejectUnauthorized: false};

    return new Pool(config);
})()

const logger = Logger('pg');


const pg = {
    'update': async ({table, columns, filters, callback}) => {
        var qstr = ['UPDATE', table, 'SET'], qargs = [];
        
        // Convert obj. o to query string
        const convert = o => (
            Object.entries(o).map(([col, val]) => {
                qargs.push(val);

                return `${col} = ($${qargs.length})`;
            }).join(', ')
        )

        qstr.push(convert(columns), 'WHERE', convert(filters));

        logger.info(qstr.join(' '));
        logger.info(qargs);

        return pool.query(qstr.join(' '), qargs, callback);
    }
}


module.exports = pg

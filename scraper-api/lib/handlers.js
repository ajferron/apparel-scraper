const { setUncaughtExceptionCaptureCallback } = require("process");

setExit = (handler) => {
    process.stdin.resume(); //so the program will not close instantly

    // Do something when app is closing
    process.on('exit', handler.bind(null,{cleanup:true}));

    // Catches ctrl+c event
    process.on('SIGINT', handler.bind(null, {exit:true}));

    // Catches "kill pid" (for example: nodemon restart)
    process.on('SIGUSR1', handler.bind(null, {exit:true}));
    process.on('SIGUSR2', handler.bind(null, {exit:true}));

    // Catches uncaught exceptions
    process.on('uncaughtException', handler.bind(null, {exit:true}));
}

module.exports = {setExit}

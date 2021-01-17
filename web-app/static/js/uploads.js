import ScrapeJob from './model/ScrapeJob.js'

$(document).ready(() => loadJobData());

$(document).on("click", '.card-header', function(e) {
    $(this).next().collapse('toggle');
});

$(document).on("click", '.status-btn', function(e) {
    e.stopPropagation()
});


function loadJobData() {
    const json = (() => {
        try {
            return JSON.parse( $('#job-data').val() )
        } catch(e) {
            return {}
        }
    })()

    if (json.length)
        $('#placeholder').remove();

    // Group scrapes that belong to the same job
    // json => {job_id1: [scrape, ...], job_id2: [scrape, ...]} 
    // scrape == {name, job_type, supplier, status, scrapes}

    const scrape_jobs = json.reduce((jobs, s) => {
        s.url = s.meta.urls.filter(url => url.id === s.scrape_id)[0]?.url

        if (s.job_id in jobs)
            jobs[s.job_id].scrapes.append(s);

        else
            jobs[s.job_id] = {
                name: s.meta.name,
                job_type: s.meta.job_type,
                supplier: s.meta.supplier,
                status: s.status,
                scrapes: [s]
            }

        return jobs;
    }, {})

    console.log(scrape_jobs);

    // Convert ScrapeJobs to a string of <div class="card">
    for (const [job_id, meta] of Object.entries(scrape_jobs)) {
        const {name, scrapes, job_type, supplier, status} = meta;

        const job = $(
            ScrapeJob(scrapes, {name, job_id, job_type, supplier, status})
        );

        $('#upload-list').append(job);
    }
}

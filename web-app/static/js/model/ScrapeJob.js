import Scrape from './Scrape.js'

function ScrapeJob(scrapes, meta={}) {

    var poll_count = 0


    const active = scrapes.filter(s => ['scraping', 'uploading'].includes(s.status))


    const poll = setInterval(() => {
        if (active.length == 0)
            return clearInterval(poll);

        const scrape_ids = JSON.stringify(active.map(s => s.scrape_id))

        fetch(`/upload-status?${new URLSearchParams({scrape_ids})}`, 
            {method: 'GET', credentials: 'same-origin'}
        )
            .then(res => res.json())

            .then(res => {
                if (active.filter(s => res[s.scrape_id] !== s.status).length) {
                    clearInterval(poll);
                    location.reload();
                }

                if (poll_count >= 15) {
                    clearInterval(poll);
                }

                poll_count++
            })
            .catch(async err => {
                console.error('Failed to get scrape status', err);

                clearInterval(poll);
            })
    }, 5000)


    return (
        `
        <div class="card">
            <div class="card-header d-flex justify-content-between" id="${meta.job_id}-card">
                <div class="job-data d-flex flex-column">
                    <span class="job-title">
                        ${meta.name}
                    </span>
                    <span class="job-id"> ${meta.job_id} </span>
                </div>

                <div class="supplier-data d-flex flex-column">
                    <div class="supplier"> ${meta.supplier} </div>
                    <div class="job-size">
                        ${scrapes.length} product${scrapes.length > 1 ? 's': ''}
                    </div>
                </div>

                <button
                    class="status-btn btn btn-sm d-flex"
                    data-toggle="collapse"
                    data-target="#${meta.job_id}-collapse"
                    aria-controls="${meta.job_id}-collapse"
                    aria-expanded="false"
                    type="button"
                >
                    <span class="${meta.status}"> 
                        ${
                            (() => {
                                const link = text => (`
                                    <a href="/product-review?job_id=${meta.job_id}">
                                        ${text} <img class="ml-2 mb-1" src="link.svg" alt=">">
                                    </a>
                                `)

                                return (
                                    {
                                        // Set on creation (flask-app, app.py:288)
                                        scraping: 'scraping...', 
                                        // Set on scrape completion (scraper-api, server.js:107)
                                        scraped: link('Ready for Review'),
                                        // Set on review.html submission (flask-app, app.py:---)
                                        uploading: 'uploading...',
                                        // Set on upload completion (bigcommerce-api, server.js:---)
                                        complete: link('Complete'),
                                        // Set on scrape failure (scraper-api, server.js:120)
                                        failed: 'failed'
                                    }
                                )[meta.status]
                            })()
                        } 
                    </span>
                </button>
            </div>

            <div 
                id="${meta.job_id}-collapse" 
                class="collapse" 
                aria-labelledby="${meta.job_id}-card" 
                data-parent="#upload-list"
            >
                <div class="card-body py-2">
                ${ // Convert scrapes to a string of <div class="scrape-job>
                    scrapes.map(scrape => (
                        Scrape({
                            scrape_id: scrape.scrape_id,
                            url: scrape.url,
                            name: scrape.result?.name,
                            sku: scrape.result?.sku,
                        })
                    )).join('')
                }
                </div>
            </div>
        </div>
        `
    )
}

export default ScrapeJob

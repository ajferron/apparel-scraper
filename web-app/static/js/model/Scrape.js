function Scrape(meta={}) {
    return (
        `
            <div class="scrape-job d-flex flex-column">
                <div class="scrape-data">
                    <span class="title"> ${meta.name ||'PRODUCT NAME PENDING'} </span>
                    <span class="sku px-1"> (${meta.sku || '-----'}) </span>
                    <a href="${meta.url}" target="_blank">
                        <img src="link1.svg" alt="view">
                    </a>
                </div>
                <div class="scrape-id">
                    ${meta.scrape_id}
                </div>
            </div>
        `
    )
}

export default Scrape

$(document).ready(() => {
    $.ajax({
        type: "GET",
        url: '/scrape',
        data: null,
        success: (data) => {
            console.log(JSON.parse(data))
            $('#load-wrapper').hide()
        }
    })
})

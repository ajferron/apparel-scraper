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

    var descEditor = new Quill('#product-description', {
        modules: {
            toolbar: [
                ['bold', 'italic', 'underline'],
                [{ list: 'ordered' }, { list: 'bullet' }]
            ]
        },
        placeholder: 'Product description...',
        theme: 'snow'
    });
})

$(document).ready(() => {
    $('input#url').on('input', function() {
        select = $('#supplier')
        url = this.value

        if (url.includes('sanmar'))
            select.val('sanmar')

        else if (url.includes('trimark'))
            select.val('trimark')

        else if (url.includes('debco'))
            select.val('debco')

        else if (url.includes('ssactivewear'))
            select.val('technosport')

        else
            select.val('supplier')
    })


    $('.btn-group .btn').on('click', function() {
        if ($('#import-type').val() !== this.id) {
            $('.btn-group .btn').toggleClass('active')
            $('#import-type').val(this.id)
        }
    })
})

$(document).ready(() => {
    $('.multi-btn .item').on('click', function() {
        $('#import-type').val(this.id)
        $('.multi-btn .item').toggleClass('active')
    })
})

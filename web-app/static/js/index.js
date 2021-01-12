$(document).ready(() => {
    $('.multi-btn .item').on('click', function() {
        if ($('#import-type').val() !== this.id) {
            $('.multi-btn .item').toggleClass('active')
            $('#import-type').val(this.id)
        }
    })
})

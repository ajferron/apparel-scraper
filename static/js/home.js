$(document).ready(() => {
    $('.btn-group .btn').on('click', function() {
        if ($('#import-type').val() !== this.id) {
            $('.btn-group .btn').toggleClass('active')
            $('#import-type').val(this.id)
        }
    })
})

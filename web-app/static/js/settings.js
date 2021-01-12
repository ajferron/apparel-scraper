$(document).ready(() => {
    $('input').on('input',function(e) {
        $(this).closest('form').find('button[type="submit"], button[type="reset"]').show()
    })

    $('button[type="reset"]').click(function(e) {
        $(this).closest('form').find('button[type="submit"], button[type="reset"]').hide()
    })

    $('.nav-item, #home-btn').click(function(e) {
        if ( $(`.btn:visible`)[0] ) {
            e.stopPropagation()
            e.preventDefault()

            alert('Save or discard changes to login information before leaving!')
        }
    })
})

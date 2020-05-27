var currProduct = 0
var displays
var products

$(document).ready(() => {
    $('#content-wrapper').hide()

    $.ajax({
        type: "GET",
        url: '/scrape',
        data: null,
        success: (data) => {
            console.log(data)
            $('#load-wrapper').hide()
            $('#content-wrapper').show()

            products = JSON.parse(data)

            displays = products.map(p => make_display(p))
            displays[currProduct].show()

            $('#progress').text(`${currProduct+1}/${displays.length}`)
        }
    })

    $('#right-btn').click(() => {
        if (currProduct !== displays.length-1) {
            displays[currProduct].hide()
            displays[++currProduct].show()

            $('#progress').text(`${currProduct+1}/${displays.length}`)
        }
    })

    $('#left-btn').click(() => {
        if (currProduct > 0) {
            displays[currProduct].hide()
            displays[--currProduct].show()

            $('#progress').text(`${currProduct+1}/${displays.length}`)
        }
    })
})



function make_display(product) {
    let productID = `product-${product.sku}`
    let template = $("#product-template").html()
    var display = $(template)

    display.find('.product-name input').val(product.name.replace('', '™'))
    display.find('.product-sku input').val(product.sku)
    display.find('.product-description').html(product.description)
    display.attr('id', productID)

    appendSizes(display, product.sizes)
    appendImages(display, product.swatch)
    $('#product-wrapper').append(display)

    initEditor(productID)
    
    display.hide()

    return display
}

function initEditor(id) {
    new Quill(`#${id} .product-description`, {
        modules: {
            toolbar: [
                ['bold', 'italic', 'underline'],
                [{ list: 'ordered' }, { list: 'bullet' }]
            ]
        },
        placeholder: 'Product description...',
        theme: 'snow'
    })
}

function appendSizes(display, sizes) {
    for ([size, price] of Object.entries(sizes)) {
        sizeItem = `<th> <label for="${size}"> ${size} </label> </th>`
        priceItem = `<td> <input class="ghost" type="text" name="${price}" value=${price}> </td>`

        display.find('.size-table .sizes').append(sizeItem)
        display.find('.size-table .prices').append(priceItem)
    }
}

function appendImages(display, swatch) {
    for ([color, url] of Object.entries(swatch)) {
        let img = $(`<img src="${url}" alt="${color}"/>`)

        img.click(function() { display.find('.main-display img').attr('src', this.src) })

        if (color === 'thumbnail') {
            display.find('.main-display img').attr('src', img[0].src)
        }

        display.find('.options').append(img)
        jQuery.data(img, 'color', color)
    }
}

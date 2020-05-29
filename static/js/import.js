var inDialog = false
var currProduct = 0
var products

$(document).ready(() => {
    $('#content-wrapper').hide()

    $.ajax({
        type: "GET",
        url: '/scrape',
        data: null,
        success: (data) => {
            // console.log(JSON.parse(data))

            $('#load-wrapper').hide()
            $('#content-wrapper').show()

            products = JSON.parse(data).map(p => makeDisplay(p))
            products[currProduct].display.show()

            $('#progress').text(`${currProduct+1}/${products.length}`)

            $('.category label').click(function() {
                $(this).siblings('input').trigger('click')
            })
        }
    })


    $('#right-btn').click(() => {
        if (currProduct !== products.length-1) {
            products[currProduct].display.hide()
            products[++currProduct].display.show()
            $('#progress').text(`${currProduct+1}/${products.length}`)
        }
    })


    $('#left-btn').click(() => {
        if (currProduct > 0) {
            $('#progress').text(`${currProduct+1}/${products.length}`)
            products[currProduct].display.hide()
            products[--currProduct].display.show()
        }
    })


    $('#upload').click(() => {
        let dialog = $('#confirm-dialog')
        let data = getProductData()

        if (data) {
            dialog.find('.message').text(`Upload ${products.length} products?`)
            dialog.find('#products').val(JSON.stringify(data))

            dialog.show()
            inDialog = true
        }
    })


    $('#cancel').click(() => {
        $('#cancel-dialog').show()
        inDialog = true
    })
})



function makeDisplay(product) {
    let productID = `product-${product.sku}`
    var display = $($("#product-template").html())

    nameField = display.find('.product-name input')
    skuField = display.find('.product-sku input')
    descField = display.find('.product-description')
    sizeFields = appendSizes(display, product.sizes)
    images = appendImages(display, product.swatch)

    nameField.val(product.name.replace('', '™'))
    skuField.val(product.sku)
    descField.html(product.description)
    display.attr('id', productID)

    $('#product-wrapper').append(display)

    descEditor = initEditor(productID)

    display.hide()

    return {
        display: display,
        data: {
            name: nameField, 
            sku: skuField, 
            desc: descEditor,
            sizes: sizeFields,
            swatch: images,
        }
    }
}

function initEditor(id) {
    let editor = new Quill(`#${id} .product-description`, {
        modules: {
            toolbar: [
                ['bold', 'italic', 'underline'],
                [{ list: 'ordered' }, { list: 'bullet' }]
            ]
        },
        placeholder: 'Product description...',
        theme: 'snow'
    })

    return editor.root.innerHTML
}

function appendSizes(display, sizes) {
    return Object.keys(sizes).map(size => {
        price = (Number(sizes[size]) + 15).toFixed(2)

        sizeElem = $(`<th> <label for="${size}"> ${size} </label> </th>`)
        priceElem = $(`<td> <input class="ghost" type="text" name="${price}" value=${price}> </td>`)

        display.find('.size-table .sizes').append(sizeElem)
        display.find('.size-table .prices').append(priceElem)

        return { size, price: priceElem.find('input') }
    })
}

function appendImages(display, swatch) {
    for (color in swatch) {
        let img = $(`<img src="${swatch[color]}" alt="${color}"/>`)

        img.click(function() { 
            display.find('.main-display img').attr('src', this.src) 
        })

        if (color === 'thumbnail')
            display.find('.main-display img').attr('src', img[0].src)

        display.find('.options').append(img)
    }

    return swatch // Set up adding/removing images
}


function getProductData() {
    let getSizes = (sizes) => {
        return sizes.reduce((obj, {price, size}) => {
            obj[size] = price.val()
            return obj
        }, {})
    }

    let getCategories = (display) => {
        return display.find('input:checkbox:checked').map(function() {
            return Number( $(this).val() )
        }).get()
    }

    let data = products.map(p => {
        let product = {
            name: p.data.name.val(),
            sku: p.data.sku.val(),
            desc: p.data.desc,
            swatch: p.data.swatch,
            sizes: getSizes(p.data.sizes),
            categories: getCategories(p.display)
        }

        if (product.categories.length == 0) {
            alert(`Select a category for product "${p.data.name.val()}"`)
            return false
        }

        return product
    })

    return data ? !data.includes(false) : false
}


function closeDialog(id) {
    $(`#${id}`).hide()
    inDialog = false
}

import ProductDisplay from './model/ProductDisplay.js'
import SubMenu from './model/SubMenu.js'

var displays
var active = 0


$(document).ready(() => {
    $('#overlay').hide()

    const products = JSON.parse( $('#product-data').val() )

    console.log(products)

    if (!products.length) {
        const e = 'Could not get data. <br> Check login creditentials, settings, and the URL.'

        $('#error-wrapper').show()
        $('#error-status').html(e)
    
        console['error'](e)
    }

    displays = products.map(p => new ProductDisplay(p))

    $('#load-wrapper').hide()
    $('#import-review').show()
    displays[0].display.show()

    $('#counter').text(`${active+1}/${displays.length}`)


    $('#progress').text(`${active+1} / ${displays.length}`)


    // EVENT HANDLERS 

    $('#right-btn').click(() => {
        if (active !== products.length-1) {
            displays[active].display.hide()
            displays[++active].display.show()

            $('#counter').text(`${active+1}/${displays.length}`)
        }
    })


    $('#left-btn').click(() => {
        if (active > 0) {
            displays[active].display.hide()
            displays[--active].display.show()

            $('#counter').text(`${active+1}/${displays.length}`)
        }
    })


    $('#confirm-modal').on('shown.bs.modal', function (e) {
        let errors = displays.map((p, i) => p.validate(i+1)).join('')

        if (!errors) {
            $(this).find('.message').html(`Upload ${displays.length} product${displays.length > 1 ? 's' : ''}?`)

            $(this).find('#products').val(JSON.stringify(displays.map(p => p.output))) 

            $(this).find('button.confirm').show()

        } else {
            $(this).find('.message').html(`Please fix the following before uploading:<br>${errors}`)

            $(this).find('button.confirm').hide()
        }
    })
})



    // fetch('/scrape', {method: 'GET', credentials: 'same-origin'})
    //     .then(response => response.json())
    //     .then(response => {
    //         return response.items.map(p => new ProductDisplay(p))
    //     })
    //     .then(displays => {
    //         products = displays

    //         console.log(products)

    //         products[0].display.show()

    //         $('#counter').text(`${active+1}/${products.length}`)

    //         $('#import-review').show()

    //         $('#progress').text(`${active+1} / ${products.length}`)

    //         fetch('/categories', {method: 'GET', credentials: 'same-origin'})
    //             .then(response => response.json())
    //             .then(response => response.data)
    //             .then(categories => categories.map(({name, id, parent_id}) => ({name, id, parent_id})))
    //             .then(categories => {
    //                 // Divide categories into parent and children categories
    //                 var [children, parents] = categories.reduce((arr, c) => {
    //                     arr[c.parent_id ? 0 : 1].push(c)
    //                     return arr

    //                 }, [[], []])

    //                 // Map each parent to a new submenu (it will contain more items)
    //                 var submenus = parents.map(p => new SubMenu(p)) /* .sort((a, b) => a.name.localeCompare(b.name)) */

    //                 // Add each parent's children as an item
    //                 submenus.forEach(m => m.addItems(children.filter(c => c.parent_id === m.id)))

    //                 // Append submenues to each product display dropdown
    //                 products.forEach(p => p.display.find('.category .dropdown-menu').append(submenus.map(m => m.dropdown.clone())))
    //             })
    //     })
    //     .catch(error => {
    //         $('#error-wrapper').show()
    //         $('#error-status').html(error)

    //         console['error'](error)
    //     })

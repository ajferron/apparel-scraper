class ProductDisplay {
    constructor({name, sku, description, sizes, swatch}) {
        this.display = sku
        this.name = name
        this.sku = sku
        this.description = description
        this.sizes = sizes
        this.swatch = swatch
    }

    set display(sku) {
        var d = $( $("#product-template").html() )

        $('#product-display').append(d)
        d.hide()

        d.attr('id', sku)

        this._display = d
    }

    get display() {
        return this._display
    }


    set name(n) {
        var input = this.display.find('input[name="name"]')
        input.val(n.replace('', '™'))

        this._name = input
    }

    get name() {
        return this._name.val()
    }


    set sku(s) {
        var input = this.display.find('input[name="sku"]')
        input.val(s.trim())

        this._sku = input
    }

    get sku() {
        return this._sku.val()
    }


    set sizes(sizes) {
        this._sizes = Object.keys(sizes).map(size => {
            var price = (Number(sizes[size]) + 15).toFixed(2)

            this.display.find('.sizes.form-row').append(
               `<div class="col d-flex flex-column align-items-center">
                    <label class="mb-1" for="${size}"> ${size} </label>
                    <input class="form-control text-center" name="${size}" type="text" value=${price}>
                </div>`
            )
    
            return { size, price: this.display.find(`.sizes.form-row input[name='${size}']`) }
        })
    }

    get sizes() {
        return this._sizes.map(({price, size}) => ({size, price: price.val()}))
    }


    set description(d) {
        var editor = this.display.find('.product-description')
            
        editor.html(d)

        this._description = (
            new Quill(`#${this.sku} .product-description`, {
                modules: {
                    toolbar: [
                        ['bold', 'italic', 'underline'],
                        [{ list: 'ordered' }, { list: 'bullet' }]
                    ]
                },
                placeholder: 'Product description...',
                theme: 'snow'
            })
        )
    }

    get description() {
        return this._description.root.innerHTML
    }


    set swatch(s) {
        var carousel = this.display.find('.carousel')

        Object.entries(s).forEach(([color, url], i) => {
            let id = `swatch-carousel-${this.sku}`

            carousel.attr('id', id)

            carousel.find('.side-btn').attr('href', `#${id}`)

            carousel.find('.carousel-inner').append(
                $(
                   `<div class="carousel-item w-auto mx-auto ${i == 1 ? 'active' : ''}">
                        <img src="${url}" alt="${color}">
                        <div class="carousel-caption d-flex justify-content-center">
                            <h5 class="shadow bg-white rounded py-0 px-1"> ${color} </h5>
                        </div>
                    </div>`
                )
            )

            carousel.find('.carousel-indicators').append(
                $(
                   `<li class="${i == 1 ? 'active' : ''} mx-1" data-target="#${id}" data-slide-to=${i}>
                        <img src="${url}" alt="${color}">
                    </li>`
                )
            )
        })

        this._swatch = s
    }


    get swatch() {
        return this._swatch
    }


    get categories() {
        let items = this.display.find('.category.dropdown .dropdown-submenu .dropdown-menu .dropdown-item')

        let selected = items.filter((_, e) => $(e).find('input').prop('checked') )
        let categories = selected.map((_, e) => JSON.parse($(e).find('input').val()) )
        let categoryIDs = categories.map((_, c) => [c.child.id, c.parent.id])

        // Remove duplicate parent IDs
        return Array.from(new Set([].concat(...categoryIDs)))
    }


    get output() {
        return {
            name: this.name,
            sku: this.sku,
            swatch: this.swatch,
            sizes: this.sizes,
            description: this.description,
            categories: this.categories
        }
    }


    validate(i) {
        let result = ''

        if (!this.name.length)
            result += `Provide a name for Product ${i} <br>`

        if (!this.sku.length)
            result += `Provide a SKU for Product ${i} <br>`

        if (!this.categories.length)
            result += `Select a category for Product ${i} <br>`

        if (this.sizes.filter(s => s.price == '').length)
            result += `Set a price for each size of Product ${i} <br>`

        return result
    }
}

export default ProductDisplay

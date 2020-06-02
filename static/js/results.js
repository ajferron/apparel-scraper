var domain = 'https://www.adventnorthcanada.com'

$(document).ready(() => {
    let results = JSON.parse( $('#results').val() )

    results.forEach(result => {
        if (result.json === null)
            $('#passed').append(validProduct(result))
        else
            $('#failed').append(invalidProduct(result))
    });

    setDefaults('#passed')
    setDefaults('#failed')
})


function validProduct(product) {
    let element = $($("#passed-product").html())

    element.find('span').text(product.name)
    element.find('a').attr('href', `${domain}${product.url}`)

    return element
}


function invalidProduct(product) {
    let element = $($("#failed-product").html())

    element.find('span').text(product.name)
    element.find('a').attr('href', `${domain}${product.url || ''}`)

    if ('title' in product.json)
        element.find('.error').text(product.json.title)
    
    return element
}


function setDefaults(group) {
    if ( $(group).children().length == 1 )
        $(group).append('<p> No products </p>')

}

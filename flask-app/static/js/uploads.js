import Upload from './model/SubMenu.js'

$(document).ready(() => {
    fetch('/user-uploads', {method: 'GET', credentials: 'same-origin'})
        .then(response => response.json())
        .then(response => response.uploads.map(u => new Upload(u)))
        .then(uploads => uploads.map(u => u.card.clone()))
        .then(uploads => $('#upload-list').append(uploads))
})
function SubMenu(p) {
    this.id = p.id

    this.dropdown = $(
       `<li class="dropdown-submenu">
            <a class="dropdown-item" onClick="expand(event)">${p.name}</a>
            <div class="dropdown-menu flex-column mb-4"></div>
        </li>`
    )

    this.addItem = (c) => {
        let parent = (({name, id}) => ({name, id}))(p)
        let child = (({name, id}) => ({name, id}))(c)
        let data = JSON.stringify({child, parent})

        let item = $(
           `<div class="dropdown-item" onClick="setCategory(event)">
                <input class="form-check-input" type="checkbox" value='${data}' onClick="setCategory(event)">
                <span class="name" onClick="setCategory(event)">${c.name}</span>
            </div>`
        )

        this.dropdown.find('.dropdown-menu').append(item)
    }

    this.addItems = children => children.forEach(c => this.addItem(c))
}

export default SubMenu

'use strict'

document.addEventListener('DOMContentLoaded', () => {

    document.querySelectorAll('.samaware-list-filter input[type="checkbox"]').forEach((checkbox) => {
        checkbox.addEventListener('change', () => {
            checkbox.form.submit()
        })
    })

    document.querySelectorAll('form.samaware-arrived-form').forEach((form) => {
        // Save original contents of the buttons, as JS from pretalx itself will modify them upon submission
        const buttonContents = new Map()
        form.querySelectorAll('.samaware-btn').forEach((button) => {
            buttonContents.set(button, button.innerHTML)
        })

        form.addEventListener('submit', async (ev) => {
            ev.preventDefault()

            if (await toggleArrived(form)) {
                form.querySelectorAll('.samaware-btn').forEach((button) => {
                    button.classList.toggle('d-none')
                    // Undo modifications performed by pretalx JS
                    button.classList.remove('disabled')
                    button.innerHTML = buttonContents.get(button)
                })
            }
        })
    })

})


async function toggleArrived(form) {

    try {
        const response = await fetch(form.action, {
            method: 'POST',
            body: new FormData(form)
        })
        if (response.status >= 400) {
            return false
        }
        return true
    } catch {
        return false
    }

}

document.addEventListener('DOMContentLoaded', function() {
    const allLinks = document.querySelectorAll('footer a')
    const modelViews = document.querySelectorAll('.model-view')
    const html_for = document.getElementById("user_content_coin_lol")
    const number  = html_for.textContent
    html_for.textContent = formatNumber(number)
    showModelView(1)
    
    allLinks.forEach((link) => {
        link.addEventListener('click', function(event) {
            event.preventDefault()
            allLinks.forEach(l => l.classList.remove('active'))
            this.classList.add('active')
            
            const viewNumber = this.getAttribute('data-view')
            showModelView(viewNumber)
        })
    })
    
    function showModelView(number) {
        
        modelViews.forEach(view => {
            view.classList.remove('active-view')
        })
        
        
        const activeView = document.querySelector(`.model-view[data-view="${number}"]`)
        if (activeView) {
            activeView.classList.add('active-view')
        }
    }
})

function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");}





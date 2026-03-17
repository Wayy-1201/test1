document.addEventListener('DOMContentLoaded', function() {
    const allLinks = document.querySelectorAll('footer a')
    const modelViews = document.querySelectorAll('.model-view')
    const html_for = document.getElementById("user_content_coin_lol")
    const number  = html_for.textContent
    html_for.textContent = formatNumber(number)
    const userStars = document.getElementById("userStars")
    const userUpgrade = document.getElementById("user_upgrade")
    const progressFill = document.getElementById("progress-fill")
    const progressCount = document.getElementById("progress-count")
    const levelSpan = document.getElementById("level")
    const sticker = document.getElementById("sticker")
    
    // Переменные игры
    let balance = 0
    let clickPower = 1
    let level = 1
    let maxLevel = 10
    let requiredForUpgrade = 150
    let currentProgress = 0
    
    // Форматируем начальный баланс
    updateBalanceDisplay()
    
    showModelView(1)
    
    // Клик по стикеру
    sticker.addEventListener('click', function(e) {
        // Создаем эффект +1
        createFloatText(e.clientX, e.clientY, clickPower)
        
        // Увеличиваем баланс
        balance += clickPower
        currentProgress += clickPower
        
        // Обновляем отображение
        updateBalanceDisplay()
        updateProgress()
        
        // Проверка на повышение уровня
        checkLevelUp()
    })
    
    // Функция обновления баланса
    function updateBalanceDisplay() {
        html_for.textContent = formatNumber(balance)
        userStars.textContent = formatNumber(balance)
    }
    
    // Функция обновления прогресса
    function updateProgress() {
        let progressPercent = (currentProgress / requiredForUpgrade) * 100
        if (progressPercent > 100) progressPercent = 100
        
        progressFill.style.width = progressPercent + '%'
        progressCount.innerHTML = `<span id="level">${level}</span>/${maxLevel}`
    }
    
    // Проверка повышения уровня
    function checkLevelUp() {
        if (currentProgress >= requiredForUpgrade && level < maxLevel) {
            // Повышаем уровень
            level++
            clickPower++
            currentProgress = 0
            requiredForUpgrade += 50
            
            // Обновляем интерфейс
            levelSpan.textContent = level
            userUpgrade.textContent = clickPower
            updateProgress()
            
            // Показываем уведомление
            alert(`Уровень повышен! Теперь ${clickPower} за клик`)
        }
    }
    
    // Эффект всплывающего текста
    function createFloatText(x, y, value) {
        const floatText = document.createElement('div')
        floatText.textContent = `+${value}`
        floatText.style.cssText = `
            position: fixed;
            left: ${x}px;
            top: ${y}px;
            color: white;
            font-size: 24px;
            font-weight: bold;
            text-shadow: 0 0 10px blue;
            pointer-events: none;
            z-index: 1000;
            animation: floatUp 1s ease-out forwards;
        `
        document.body.appendChild(floatText)
        
        setTimeout(() => {
            floatText.remove()
        }, 1000)
    }
    
    // Добавляем анимацию в CSS
    const style = document.createElement('style')
    style.textContent = `
        @keyframes floatUp {
            0% {
                opacity: 1;
                transform: translateY(0);
            }
            100% {
                opacity: 0;
                transform: translateY(-50px);
            }
        }
    `
    document.head.appendChild(style)
    
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
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".")
}
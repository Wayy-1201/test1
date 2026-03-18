// ==================== КЛИК ПО СТИКЕРУ ====================
document.addEventListener('DOMContentLoaded', function() {
    const sticker = document.getElementById('sticker')
    const html_for = document.getElementById("user_content_coin_lol")
    
    sticker.addEventListener('click', function(e) {
        // Рассчитываем доход с учетом бонусов
        let earned = userData.clickPower
        
        // Проверка на критический удар
        if (userData.bonusUpgrades.crit.count > 0) {
            const critChance = Math.min(userData.bonusUpgrades.crit.count * 0.05, 0.3) // макс 30%
            if (Math.random() < critChance) {
                earned *= 5
                showNotification('КРИТИЧЕСКИЙ УДАР! x5', true)
            }
        }
        
        // Проверка на удачу (доп. бонус)
        if (userData.bonusUpgrades.luck.count > 0) {
            const luckMultiplier = 1 + (userData.bonusUpgrades.luck.count * 0.05)
            earned = Math.floor(earned * luckMultiplier)
        }
        
        // Донор x2
        if (userData.donors.x2) earned *= 2
        
        // Создаем эффект
        createFloatText(e.clientX, e.clientY, earned)
        
        // Увеличиваем баланс и прогресс
        userData.balance += earned
        userData.progress += userData.clickPower // Прогресс растет от базовой силы
        
        // Обновляем интерфейс
        updateAllDisplays()
        
        // Проверка на повышение уровня
        checkLevelUp()
    })
})

// ==================== ПОВЫШЕНИЕ УРОВНЯ ====================
function checkLevelUp() {
    const required = levelConfig.getRequirement(userData.level)
    
    while (userData.progress >= required && userData.level < 10) {
        userData.progress -= required
        userData.level++
        userData.clickPower++
        
        // Бонус за уровень
        const bonusCoins = 50 * userData.level
        userData.balance += bonusCoins
        
        // ✨ ОБНОВЛЯЕМ БЛОК ПОСЛЕ ПОВЫШЕНИЯ УРОВНЯ
        updateRequiredBlock()
        
        showNotification(`УРОВЕНЬ ${userData.level}! +${bonusCoins} монет`, true)
        updateAllDisplays()
    }
}

// ==================== ЭФФЕКТ ВСПЛЫВАЮЩЕГО ТЕКСТА ====================
function createFloatText(x, y, value) {
    const floatText = document.createElement('div')
    floatText.textContent = `+${value}`
    floatText.style.cssText = `
        position: fixed;
        left: ${x}px;
        top: ${y}px;
        color: #ffd700;
        font-size: 28px;
        font-weight: bold;
        text-shadow: 0 0 15px #ff9900, 2px 2px 2px black;
        pointer-events: none;
        z-index: 1000;
        animation: floatUp 1s ease-out forwards;
    `
    document.body.appendChild(floatText)
    
    setTimeout(() => floatText.remove(), 1000)
}

// ==================== ПАССИВНЫЙ ДОХОД ====================
function updatePassiveIncome() {
    if (userData.passiveIncome <= 0) return
    
    // Рассчитываем пассивный доход
    let income = userData.passiveIncome
    
    // Донор x2 к пассивному доходу
    if (userData.donors.x2sek) income *= 2
    
    userData.balance += income
    updateAllDisplays()
}

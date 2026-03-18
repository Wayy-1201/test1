// ================= ДАННЫЕ =================
let userData = {
    balance: 0, // Для тестирования
    stars: 0,
    level: 1,
    clickPower: 1,
    passiveIncome: 0,
    progress: 0,

    clickUpgrades: {
        power1: { count: 0, base: 100, power: 1 },
        power2: { count: 0, base: 500, power: 3 },
        power3: { count: 0, base: 1000, power: 5 }
    },

    farmUpgrades: {
        worker: { count: 0, base: 200, income: 1 },
        farmer: { count: 0, base: 800, income: 3 },
        harvester: { count: 0, base: 2000, income: 5 }
    },

    bonusUpgrades: {
        luck: { count: 0, base: 300 },
        crit: { count: 0, base: 1500 }
    },

    donors: {
        x2: false,
        x2sek: false,
        superclick: false
    }
}

// ================= ЛЕВЕЛ =================
// ================= ЛЕВЕЛ =================
const levelConfig = {
    base: 150,
    multi: 3,
    get(lvl) {
        return this.base * Math.pow(this.multi, lvl - 1)
    }
}

// Добавляем синоним функции
levelConfig.getRequirement = levelConfig.get

// ================= ЦЕНА =================
function getPrice(base, count) {
    return Math.floor(base * Math.pow(1.5, count))
}

// ================= СОХРАНЕНИЕ =================
function save() {
    localStorage.setItem('game', JSON.stringify(userData))
}

function load() {
    const data = localStorage.getItem('game')
    if (data) {
        const parsed = JSON.parse(data)
        userData = { ...userData, ...parsed }
    }
}

// ================= ФОРМАТ =================
function format(n) {
    if (n >= 1e6) return (n / 1e6).toFixed(1) + 'M'
    if (n >= 1e3) return (n / 1e3).toFixed(1) + 'K'
    return n
}

// ================= УВЕДОМЛЕНИЯ =================
function showNotification(text, isGood) {
    const notification = document.createElement('div')
    notification.textContent = text
    notification.style.cssText = `
        position: fixed;
        top: 50px;
        left: 50%;
        transform: translateX(-50%);
        background: ${isGood ? '#4CAF50' : '#f44336'};
        color: white;
        padding: 10px 20px;
        border-radius: 30px;
        font-weight: bold;
        z-index: 2000;
        animation: fadeOut 2s forwards;
    `
    document.body.appendChild(notification)
    setTimeout(() => notification.remove(), 2000)
}

// ================= ОБНОВЛЕНИЕ ИНТЕРФЕЙСА =================
// ================= ОБНОВЛЕНИЕ ИНТЕРФЕЙСА =================
function updateUI() {
    // Баланс везде
    document.getElementById('user_content_coin_lol').textContent = format(userData.balance)
    document.getElementById('user_content_coin_lol_for_2').textContent = format(userData.balance)
    document.getElementById('user_content_coin_lol_for_3').textContent = format(userData.balance)
    
    // Звезды
    document.getElementById('userStars').textContent = userData.stars
    
    // СИЛА КЛИКА С УЧЕТОМ X2
    let displayClickPower = userData.clickPower
    if (userData.donors.x2) {
        displayClickPower *= 2
    }
    document.getElementById("user_upgrade").textContent = displayClickPower
    
    // ПАССИВНЫЙ ДОХОД С УЧЕТОМ X2sek
    let displayPassiveIncome = userData.passiveIncome
    if (userData.donors.x2sek) {
        displayPassiveIncome *= 2
    }
    document.getElementById("user_upgrade_sek").textContent = displayPassiveIncome

    // Уровень
    const need = levelConfig.get(userData.level)
    const percent = (userData.progress / need) * 100
    document.getElementById('progress-fill').style.width = Math.min(percent, 100) + '%'
    document.getElementById('level').textContent = userData.level
    document.getElementById('required-for-level').textContent = need

    // Цены
    updatePrices()
    
    // Количество улучшений
    updateCounts()
    
    // Донат статус
    updateDonateStatus()
}

// ================= ОБНОВЛЕНИЕ ЦЕН =================
function updatePrices() {
    document.getElementById('price_1').textContent = getPrice(100, userData.clickUpgrades.power1.count)
    document.getElementById('price_2').textContent = getPrice(500, userData.clickUpgrades.power2.count)
    document.getElementById('price_3').textContent = getPrice(1000, userData.clickUpgrades.power3.count)
    document.getElementById('price_2_1').textContent = getPrice(200, userData.farmUpgrades.worker.count)
    document.getElementById('price_2_2').textContent = getPrice(800, userData.farmUpgrades.farmer.count)
    document.getElementById('price_2_3').textContent = getPrice(2000, userData.farmUpgrades.harvester.count)
    document.getElementById('price3_1').textContent = getPrice(300, userData.bonusUpgrades.luck.count)
    document.getElementById('price_3_2').textContent = getPrice(1500, userData.bonusUpgrades.crit.count)
}

// ================= ОБНОВЛЕНИЕ КОЛИЧЕСТВА =================
function updateCounts() {
    // Клики
    document.querySelectorAll('.category-click .upgrade-count')[0].textContent = userData.clickUpgrades.power1.count
    document.querySelectorAll('.category-click .upgrade-count')[1].textContent = userData.clickUpgrades.power2.count
    document.querySelectorAll('.category-click .upgrade-count')[2].textContent = userData.clickUpgrades.power3.count
    
    // Ферма
    document.querySelectorAll('.category-farm .upgrade-count')[0].textContent = userData.farmUpgrades.worker.count
    document.querySelectorAll('.category-farm .upgrade-count')[1].textContent = userData.farmUpgrades.farmer.count
    document.querySelectorAll('.category-farm .upgrade-count')[2].textContent = userData.farmUpgrades.harvester.count
    
    // Бонусы
    document.querySelectorAll('.category-bonus .upgrade-count')[0].textContent = userData.bonusUpgrades.luck.count
    document.querySelectorAll('.category-bonus .upgrade-count')[1].textContent = userData.bonusUpgrades.crit.count
}

// ================= ОБНОВЛЕНИЕ ДОНАТ СТАТУСА =================
function updateDonateStatus() {
    // X2 монет
    const donateX2 = document.getElementById('donate-x2')
    const circleX2 = donateX2?.querySelector('.red_green')
    if (circleX2) {
        circleX2.style.backgroundColor = userData.donors.x2 ? '#00ff00' : 'red'
    }
    
    // X2 в секунду
    const donateX2sek = document.getElementById('donate-x2sek')
    const circleX2sek = donateX2sek?.querySelector('.red_green')
    if (circleX2sek) {
        circleX2sek.style.backgroundColor = userData.donors.x2sek ? '#00ff00' : 'red'
    }
    
    // Супер клик
    const donateSuper = document.getElementById('donate-superclick')
    const circleSuper = donateSuper?.querySelector('.red_green')
    if (circleSuper) {
        circleSuper.style.backgroundColor = userData.donors.superclick ? '#00ff00' : 'red'
    }
    
    // +100k (всегда красный, можно покупать много раз)
    const donate100k = document.getElementById('donate-plus100k')
    const circle100k = donate100k?.querySelector('.red_green')
    if (circle100k) {
        circle100k.style.backgroundColor = 'red'
    }
}

// ================= КЛИК =================
function handleClick(e) {
    let earned = userData.clickPower

    // Крит
    const critChance = userData.bonusUpgrades.crit.count * 0.05
    if (Math.random() < critChance) earned *= 5

    // Удача
    const luck = 1 + userData.bonusUpgrades.luck.count * 0.05
    earned = Math.floor(earned * luck)

    // Донор X2
    if (userData.donors.x2) earned *= 2

    userData.balance += earned
    userData.progress += earned
    
    // Проверка уровня
    checkLevel()
    
    updateUI()
    createFloatText(e.clientX, e.clientY, earned)
}

// ================= ПРОВЕРКА УРОВНЯ =================
function checkLevel() {
    let need = levelConfig.get(userData.level)
    
    while (userData.progress >= need && userData.level < 10) {
        userData.progress -= need
        userData.level++
        userData.clickPower++
        userData.balance += 50 * userData.level
        need = levelConfig.get(userData.level)
        showNotification(`УРОВЕНЬ ${userData.level}!`, true)
    }
}

// ================= ПАССИВНЫЙ ДОХОД =================
function passiveTick() {
    let income = userData.passiveIncome
    if (userData.donors.x2sek) income *= 2
    if (income > 0) {
        userData.balance += income
        updateUI()
    }
}

// ================= ВСПЛЫВАЮЩИЙ ТЕКСТ =================
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
        text-shadow: 0 0 15px #ff9900;
        pointer-events: none;
        z-index: 1000;
        animation: floatUp 1s ease-out forwards;
    `
    document.body.appendChild(floatText)
    setTimeout(() => floatText.remove(), 1000)
}

// ================= ПОКУПКА УЛУЧШЕНИЙ =================
function buyUpgrade(type, key) {
    if (type === 'click') {
        const upg = userData.clickUpgrades[key]
        const price = getPrice(upg.base, upg.count)
        
        if (userData.balance < price) {
            showNotification('Недостаточно монет!', false)
            return
        }
        
        userData.balance -= price
        upg.count++
        userData.clickPower += upg.power
        showNotification(`+${upg.power} к клику!`, true)
    }
    
    if (type === 'farm') {
        const upg = userData.farmUpgrades[key]
        const price = getPrice(upg.base, upg.count)
        
        if (userData.balance < price) {
            showNotification('Недостаточно монет!', false)
            return
        }
        
        userData.balance -= price
        upg.count++
        userData.passiveIncome += upg.income
        showNotification(`+${upg.income} монет/сек!`, true)
    }
    
    if (type === 'bonus') {
        const upg = userData.bonusUpgrades[key]
        const price = getPrice(upg.base, upg.count)
        
        if (userData.balance < price) {
            showNotification('Недостаточно монет!', false)
            return
        }
        
        userData.balance -= price
        upg.count++
        showNotification(`Улучшено!`, true)
    }
    
    updateUI()
    save()
}

// ================= ДОНАТ ПОКУПКИ =================
function initDonateShop() {
    // X2 монет
    document.getElementById('donate-x2')?.addEventListener('click', function() {
        if (userData.stars < 15) {
            showNotification('Нужно 15 ⭐!', false)
            return
        }
        if (userData.donors.x2) {
            showNotification('Уже куплено!', false)
            return
        }
        
        userData.stars -= 15
        userData.donors.x2 = true
        updateUI()
        save()
        showNotification('X2 монет навсегда!', true)
    })
    
    // +100k монет
    document.getElementById('donate-plus100k')?.addEventListener('click', function() {
        if (userData.stars < 20) {
            showNotification('Нужно 20 ⭐!', false)
            return
        }
        
        userData.stars -= 20
        userData.balance += 100000
        updateUI()
        save()
        showNotification('+100 000 монет!', true)
    })
    
    // X2 в секунду
    document.getElementById('donate-x2sek')?.addEventListener('click', function() {
        if (userData.stars < 25) {
            showNotification('Нужно 25 ⭐!', false)
            return
        }
        if (userData.donors.x2sek) {
            showNotification('Уже куплено!', false)
            return
        }
        
        userData.stars -= 25
        userData.donors.x2sek = true
        updateUI()
        save()
        showNotification('X2 монет в секунду!', true)
    })
    
    // Супер клик
    document.getElementById('donate-superclick')?.addEventListener('click', function() {
        if (userData.stars < 30) {
            showNotification('Нужно 30 ⭐!', false)
            return
        }
        if (userData.donors.superclick) {
            showNotification('Уже куплено!', false)
            return
        }
        
        userData.stars -= 30
        userData.donors.superclick = true
        userData.clickPower += 5
        updateUI()
        save()
        showNotification('Супер-клик +5!', true)
    })
}

// ================= РЕКЛАМА =================
function watchAd() {
    userData.stars += 1  // Только 1 звезда за рекламу
    updateUI()
    save()
    showNotification('+1 звезда!', true)
}

// ================= ПЕРЕКЛЮЧЕНИЕ КАТЕГОРИЙ =================
function initCategorySwitching() {
    const blocks = document.querySelectorAll('.category-block')
    
    blocks.forEach(block => {
        block.addEventListener('click', function() {
            blocks.forEach(b => b.classList.remove('active-category'))
            this.classList.add('active-category')
            
            const category = this.getAttribute('data-category')
            
            document.querySelector('.category-click').style.display = 'none'
            document.querySelector('.category-farm').style.display = 'none'
            document.querySelector('.category-bonus').style.display = 'none'
            
            if (category === 'click') document.querySelector('.category-click').style.display = 'block'
            if (category === 'farm') document.querySelector('.category-farm').style.display = 'block'
            if (category === 'bonus') document.querySelector('.category-bonus').style.display = 'block'
        })
    })
}

// ================= НАВИГАЦИЯ =================
function initNavigation() {
    const links = document.querySelectorAll('footer a')
    
    links.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault()
            links.forEach(l => l.classList.remove('active'))
            link.classList.add('active')
            
            const view = link.getAttribute('data-view')
            document.querySelectorAll('.model-view').forEach(v => v.classList.remove('active-view'))
            document.querySelector(`.model-view[data-view="${view}"]`).classList.add('active-view')
        })
    })
}

// ================= ИНИЦИАЛИЗАЦИЯ =================
document.addEventListener('DOMContentLoaded', () => {
    // Загружаем данные
    load()
    
    // Добавляем анимации
    const style = document.createElement('style')
    style.textContent = `
        @keyframes floatUp {
            0% { opacity: 1; transform: translateY(0); }
            100% { opacity: 0; transform: translateY(-100px); }
        }
        @keyframes fadeOut {
            0% { opacity: 1; }
            70% { opacity: 1; }
            100% { opacity: 0; }
        }
    `
    document.head.appendChild(style)
    
    // Обновляем интерфейс
    updateUI()
    
    // Навигация
    initNavigation()
    
    // Категории в магазине
    initCategorySwitching()
    
    // Донат магазин
    initDonateShop()
    
    // Клик по стикеру
    const sticker = document.getElementById('sticker')
    if (sticker) {
        sticker.addEventListener('click', handleClick)
        
        // Lottie
        if (typeof lottie !== 'undefined') {
            sticker.innerHTML = ''
            lottie.loadAnimation({
                container: sticker,
                renderer: 'svg',
                loop: true,
                autoplay: true,
                path: "../imgs/for_img_crystal/AnimatedSticker.json"
            })
        }
    }
    
    // Кнопка рекламы
    document.getElementById('ads-btn')?.addEventListener('click', watchAd)
    
    // Улучшения - добавляем обработчики
    document.querySelectorAll('.category-click .upgrade-item').forEach((item, i) => {
        item.addEventListener('click', () => buyUpgrade('click', ['power1', 'power2', 'power3'][i]))
    })
    
    document.querySelectorAll('.category-farm .upgrade-item').forEach((item, i) => {
        item.addEventListener('click', () => buyUpgrade('farm', ['worker', 'farmer', 'harvester'][i]))
    })
    
    document.querySelectorAll('.category-bonus .upgrade-item').forEach((item, i) => {
        item.addEventListener('click', () => buyUpgrade('bonus', ['luck', 'crit'][i]))
    })
    
    // Пассивный доход и сохранение
    setInterval(passiveTick, 1000)
    setInterval(save, 5000)
})

// Глобальные функции
window.buyUpgrade = buyUpgrade
window.handleClick = handleClick
window.updateAllDisplays = updateUI
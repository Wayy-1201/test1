// ==================== BUBBLES.JS - ШАРИКИ В КОНТЕЙНЕРЕ ====================

window.bubbleSystem = {
    isActive: false,
    currentBubble: null
}

// ==================== ИНИЦИАЛИЗАЦИЯ ====================
document.addEventListener('DOMContentLoaded', function() {
    console.log('Bubbles.js loaded')
    startBubbleSpawner()
})

// ==================== ЗАПУСК ГЕНЕРАЦИИ ====================
function startBubbleSpawner() {
    scheduleNextBubble()
}

// ==================== ПОЛУЧЕНИЕ КОНТЕЙНЕРА ====================
function getGameContainer() {
    return document.querySelector('.all') || document.body
}

// ==================== ПЛАНИРОВАНИЕ СЛЕДУЮЩЕГО ШАРИКА ====================
function scheduleNextBubble() {
    const delay = Math.random() * 15000 + 2000 // 2-6 секунд
    
    setTimeout(function() {
        if (!window.bubbleSystem.isActive) {
            createBubble()
        }
        scheduleNextBubble()
    }, delay)
}

// ==================== СОЗДАНИЕ ШАРИКА ====================
function createBubble() {
    if (window.bubbleSystem.isActive) return
    
    const container = getGameContainer()
    const containerRect = container.getBoundingClientRect()
    
    // Проверяем что контейнер видим
    if (containerRect.width === 0) return
    
    console.log('Creating bubble in container')
    
    const bubble = document.createElement('div')
    bubble.className = 'bubble'
    
    // Размер
    const size = Math.floor(Math.random() * 40) + 30 // 30-70px
    bubble.style.width = size + 'px'
    bubble.style.height = size + 'px'
    
    // Позиция ВНУТРИ контейнера
    const maxLeft = containerRect.width - size
    const left = Math.floor(Math.random() * maxLeft)
    bubble.style.left = left + 'px'
    
    // Начинаем снизу контейнера
    bubble.style.bottom = '0px'
    bubble.style.position = 'absolute'
    
    // Скорость
    const duration = (Math.random() * 2 + 1).toFixed(1) // 3-7 секунд
    bubble.style.animationDuration = duration + 's'
    
    // Награда
    const reward = Math.floor(Math.random() * 500) + 20 // 20-70 монет
    bubble.setAttribute('data-reward', reward)
    bubble.textContent = '+' + reward
    
    // Обработчик клика
    bubble.onclick = function(e) {
        e.stopPropagation()
        
        const reward = parseInt(this.getAttribute('data-reward'))
        
        if (typeof userData !== 'undefined') {
            userData.balance += reward
            showCoinEffect(e.clientX, e.clientY, reward)
            
            if (typeof updateAllDisplays === 'function') {
                updateAllDisplays()
            }
            
            if (typeof showNotification === 'function') {
                showNotification('💰 +' + reward + ' монет!', true)
            }
        }
        
        this.remove()
        window.bubbleSystem.isActive = false
        window.bubbleSystem.currentBubble = null
    }
    
    // Когда шарик долетает до верха
    bubble.onanimationend = function() {
        this.remove()
        window.bubbleSystem.isActive = false
        window.bubbleSystem.currentBubble = null
    }
    
    // Добавляем в контейнер, а не в body
    container.style.position = 'relative' // Убеждаемся что контейнер relative
    container.appendChild(bubble)
    
    window.bubbleSystem.isActive = true
    window.bubbleSystem.currentBubble = bubble
}

// ==================== ЭФФЕКТ МОНЕТОК ====================
function showCoinEffect(x, y, amount) {
    const effect = document.createElement('div')
    effect.textContent = '+' + amount
    effect.style.cssText = `
        position: fixed;
        left: ${x}px;
        top: ${y}px;
        color: #ffd700;
        font-size: 24px;
        font-weight: bold;
        text-shadow: 0 0 10px orange;
        pointer-events: none;
        z-index: 10000;
        animation: coinFloat 1s ease-out forwards;
    `
    
    document.body.appendChild(effect)
    
    setTimeout(function() {
        if (effect.parentNode) {
            effect.remove()
        }
    }, 1000)
}

// ==================== СТИЛИ ====================
if (!document.querySelector('#bubble-styles')) {
    const style = document.createElement('style')
    style.id = 'bubble-styles'
    style.textContent = `
        .bubble {
            position: absolute;
            border-radius: 50%;
            background: rgba(173, 216, 230, 0.9);
            box-shadow: 0 0 20px rgba(173, 216, 230, 0.9);
            cursor: pointer;
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 16px;
            text-shadow: 0 0 5px black;
            animation: floatUp linear;
            pointer-events: auto;
            border: 2px solid white;
            transition: transform 0.1s;
            will-change: transform;
        }
        
        .bubble:hover {
            transform: scale(1.1);
            background: rgba(200, 230, 255, 1);
            box-shadow: 0 0 30px rgba(173, 216, 230, 1);
        }
        
        .bubble:active {
            transform: scale(0.9);
        }
        
        @keyframes floatUp {
            0% {
                transform: translateY(0);
                opacity: 1;
            }
            100% {
                transform: translateY(-350px);
                opacity: 0;
            }
        }
        
        @keyframes coinFloat {
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
}
// ==================== ADS.JS - ТОЛЬКО РЕКЛАМА ====================

document.addEventListener('DOMContentLoaded', function() {
    const adsBtn = document.getElementById('ads-btn')
    
    if (adsBtn) {
        adsBtn.addEventListener('click', function() {
            showSimpleAd()
            userData.stars += 0
        })
    }
})

// ==================== ПРОСТЕЙШАЯ РЕКЛАМА ====================
function showSimpleAd() {
    // Удаляем старое окно если есть
    const oldAd = document.getElementById('simple-ad')
    if (oldAd) oldAd.remove()
    
    // Затемненный фон
    const overlay = document.createElement('div')
    overlay.id = 'simple-ad'
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.8);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 10000;
        transition: 0.3s ease-in-out;
    `
    
    // Белое окно
    const modal = document.createElement('div')
    modal.style.cssText = `
        background: black;
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        background: #fff;
        max-width: 300px;
        width: 90%;
        color: white;
    `
    
    // Текст
    const text = document.createElement('p')
    text.textContent = 'Здесь могла бы быть ваша реклама'
    text.style.cssText = `
        font-size: 18px;
        margin-bottom: 20px;
        color: #333;
    `
    
    // Кнопка
    const button = document.createElement('button')
    button.textContent = 'OK'
    button.style.cssText = `
        background: #4CAF50;
        color: white;
        border: none;
        padding: 10px 30px;
        border-radius: 5px;
        font-size: 16px;
        cursor: pointer;
    `
    
    button.addEventListener('click', () => {
        overlay.remove()
    })
    
    modal.appendChild(text)
    modal.appendChild(button)
    overlay.appendChild(modal)
    document.body.appendChild(overlay)
}




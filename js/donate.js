// ==================== ДОНАТ КНОПКИ ====================
function initDonateButtons() {
    const donateX2 = document.getElementById('donate-x2')
    const donatePlus100k = document.getElementById('donate-plus100k')
    const donateX2sek = document.getElementById('donate-x2sek')
    const donateSuperclick = document.getElementById('donate-superclick')
    
    // Обновляем статус донатов (зеленый/красный)
    updateDonateStatus()
    
    donateX2.addEventListener('click', function() {
        if (userData.donors.x2) {
            showNotification('Уже куплено!', false)
            return
        }
        
        if (userData.stars < 15) {
            showNotification('Недостаточно звезд!', false)
            return
        }
        
        userData.stars -= 15
        userData.donors.x2 = true
        saveUserData()
        updateDonateStatus()
        showNotification('X2 монет навсегда активирован!', true)
    })
    
    donatePlus100k.addEventListener('click', function() {
        if (userData.donors.plus100k) {
            showNotification('Уже куплено!', false)
            return
        }
        
        if (userData.stars < 20) {
            showNotification('Недостаточно звезд!', false)
            return
        }
        
        userData.stars -= 20
        userData.balance += 100000
        userData.donors.plus100k = true
        saveUserData()
        updateDonateStatus()
        updateAllDisplays()
        showNotification('+100 000 монет получено!', true)
    })
    
    donateX2sek.addEventListener('click', function() {
        if (userData.donors.x2sek) {
            showNotification('Уже куплено!', false)
            return
        }
        
        if (userData.stars < 25) {
            showNotification('Недостаточно звезд!', false)
            return
        }
        
        userData.stars -= 25
        userData.donors.x2sek = true
        saveUserData()
        updateDonateStatus()
        showNotification('X2 монет в секунду активирован!', true)
    })
    
    donateSuperclick.addEventListener('click', function() {
        if (userData.donors.superclick) {
            showNotification('Уже куплено!', false)
            return
        }
        
        if (userData.stars < 30) {
            showNotification('Недостаточно звезд!', false)
            return
        }
        
        userData.stars -= 30
        userData.clickPower += 5
        userData.donors.superclick = true
        saveUserData()
        updateDonateStatus()
        updateAllDisplays()
        showNotification('+5 к силе клика навсегда!', true)
    })
}

function updateDonateStatus() {
    const redDots = document.querySelectorAll('.red_green')
    
    redDots.forEach((dot, index) => {
        let isBought = false
        switch(index) {
            case 0: isBought = userData.donors.x2; break
            case 1: isBought = userData.donors.plus100k; break
            case 2: isBought = userData.donors.x2sek; break
            case 3: isBought = userData.donors.superclick; break
        }
        
        dot.style.backgroundColor = isBought ? '#4CAF50' : '#f44336'
    })
}
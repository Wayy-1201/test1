// ==================== УЛУЧШЕНИЯ КЛИКА ====================
function initClickUpgrades() {
    const clickItems = document.querySelectorAll('.category-click .upgrade-item')
    
    clickItems.forEach((item, index) => {
        item.addEventListener('click', function() {
            let upgradeType, powerIncrease
            
            switch(index) {
                case 0:
                    upgradeType = 'power1'
                    powerIncrease = 1
                    break
                case 1:
                    upgradeType = 'power2'
                    powerIncrease = 3
                    break
                case 2:
                    upgradeType = 'power3'
                    powerIncrease = 5
                    break
            }
            
            // Получаем текущую цену по формуле
            const currentCount = userData.clickUpgrades[upgradeType]
            const price = getPrice('click', upgradeType, currentCount)
            
            if (userData.balance < price) {
                showNotification('Недостаточно монет!', false)
                return
            }
            
            // Покупаем
            userData.balance -= price
            userData.clickUpgrades[upgradeType]++
            userData.clickPower += powerIncrease
            
            // Обновляем интерфейс
            updateAllDisplays()
            updateAllPrices()
            
            // Звук если есть
            if (typeof window.playTapSound === 'function') {
                window.playTapSound()
            }
            
            showNotification(`+${powerIncrease} к клику!`, true)
        })
    })
}

// ==================== УЛУЧШЕНИЯ ФЕРМЫ ====================
function initFarmUpgrades() {
    const farmItems = document.querySelectorAll('.category-farm .upgrade-item')
    
    farmItems.forEach((item, index) => {
        item.addEventListener('click', function() {
            let upgradeType, incomeIncrease
            
            switch(index) {
                case 0:
                    upgradeType = 'worker'
                    incomeIncrease = 1
                    break
                case 1:
                    upgradeType = 'farmer'
                    incomeIncrease = 3
                    break
                case 2:
                    upgradeType = 'harvester'
                    incomeIncrease = 5
                    break
            }
            
            const currentCount = userData.farmUpgrades[upgradeType]
            const price = getPrice('farm', upgradeType, currentCount)
            
            if (userData.balance < price) {
                showNotification('Недостаточно монет!', false)
                return
            }
            
            userData.balance -= price
            userData.farmUpgrades[upgradeType]++
            userData.passiveIncome += incomeIncrease
            
            updateAllDisplays()
            updateAllPrices()
            
            if (typeof window.playTapSound === 'function') {
                window.playTapSound()
            }
            
            showNotification(`+${incomeIncrease} монет/сек!`, true)
        })
    })
}

// ==================== БОНУСЫ ====================
function initBonusUpgrades() {
    const bonusItems = document.querySelectorAll('.category-bonus .upgrade-item')
    
    bonusItems.forEach((item, index) => {
        item.addEventListener('click', function() {
            let upgradeType
            
            switch(index) {
                case 0:
                    upgradeType = 'luck'
                    break
                case 1:
                    upgradeType = 'crit'
                    break
            }
            
            const currentCount = userData.bonusUpgrades[upgradeType]
            const price = getPrice('bonus', upgradeType, currentCount)
            
            if (userData.balance < price) {
                showNotification('Недостаточно монет!', false)
                return
            }
            
            userData.balance -= price
            userData.bonusUpgrades[upgradeType]++
            
            updateAllDisplays()
            updateAllPrices()
            
            if (typeof window.playTapSound === 'function') {
                window.playTapSound()
            }
            
            if (upgradeType === 'luck') {
                showNotification(`Удача +5%!`, true)
            } else {
                showNotification(`Шанс крита +5%!`, true)
            }
        })
    })
}

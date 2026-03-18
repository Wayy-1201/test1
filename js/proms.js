// ================= ПРОСТЫЕ ПРОМОКОДЫ =================

// Цены для каждой кнопки
const prices = [500, 1000, 750];
// Статус покупки
let bought = [false, false, false];

// Функция генерации промокода
function generateCode() {
    let code = '';
    let chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    for (let i = 0; i < 8; i++) {
        code += chars[Math.floor(Math.random() * chars.length)];
    }
    return code;
}

// Навешиваем обработчики на кнопки
document.querySelectorAll('.promo-buy-btn').forEach((btn, i) => {
    btn.addEventListener('click', function() {
        // Проверка на уже купленное
        if (bought[i]) {
            alert('Промокод уже куплен!');
            return;
        }
        
        // Проверка денег
        if (userData.balance < prices[i]) {
            alert('Недостаточно монет!');
            return;
        }
        
        // Снимаем деньги
        userData.balance -= prices[i];
        
        // Генерируем промокод
        let promo = generateCode();
        
        // Помечаем как купленное
        bought[i] = true;
        
        // Находим карточку
        let card = btn.closest('.promo-card');
        
        // Создаем элемент с промокодом
        let promoDiv = document.createElement('div');
        promoDiv.textContent = `Промокод: ${promo}`;
        promoDiv.style.cssText = `
            background: #2a2a3a;
            color: #FFD700;
            padding: 10px;
            border-radius: 10px;
            font-family: monospace;
            font-size: 16px;
            text-align: center;
            margin-top: 10px;
            border: 1px dashed #FFD700;
        `;
        
        // Добавляем в карточку
        card.appendChild(promoDiv);
        
        // Меняем кнопку
        btn.textContent = 'Куплено ✓';
        btn.disabled = true;
        btn.style.opacity = '0.5';
        
        // Обновляем интерфейс
        updateUI();
        save();
    });
});
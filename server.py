import os
import json
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, g, render_template_string
from flask_cors import CORS

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

DATABASE = 'crystal_clicker.db'
LEADERBOARD_LIMIT = 100

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = sqlite3.connect(DATABASE)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")

    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT DEFAULT 'Аноним',
            avatar_url TEXT DEFAULT '',
            balance INTEGER DEFAULT 0,
            stars INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            click_power INTEGER DEFAULT 1,
            passive_income INTEGER DEFAULT 0,
            progress INTEGER DEFAULT 0,
            total_clicks INTEGER DEFAULT 0,
            total_earned INTEGER DEFAULT 0,
            click_upgrades TEXT DEFAULT '{"power1":0,"power2":0,"power3":0}',
            farm_upgrades TEXT DEFAULT '{"worker":0,"farmer":0,"harvester":0}',
            bonus_upgrades TEXT DEFAULT '{"luck":0,"crit":0}',
            donors TEXT DEFAULT '{"x2":false,"x2sek":false,"superclick":false}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_sync TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    db.execute('''
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user INTEGER NOT NULL,
            to_user INTEGER NOT NULL,
            score INTEGER NOT NULL CHECK(score >= 1 AND score <= 5),
            comment TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (from_user) REFERENCES users(telegram_id),
            FOREIGN KEY (to_user) REFERENCES users(telegram_id),
            UNIQUE(from_user, to_user)
        )
    ''')

    db.execute('CREATE INDEX IF NOT EXISTS idx_users_balance ON users(balance DESC)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)')
    db.execute('CREATE INDEX IF NOT EXISTS idx_ratings_to_user ON ratings(to_user)')

    db.commit()
    db.close()
    print("База данных инициализирована")

def user_to_dict(row):
    if row is None:
        return None
    return {
        'telegram_id': row['telegram_id'],
        'username': row['username'],
        'avatar_url': row['avatar_url'],
        'balance': row['balance'],
        'stars': row['stars'],
        'level': row['level'],
        'click_power': row['click_power'],
        'passive_income': row['passive_income'],
        'progress': row['progress'],
        'total_clicks': row['total_clicks'],
        'total_earned': row['total_earned'],
        'click_upgrades': json.loads(row['click_upgrades']),
        'farm_upgrades': json.loads(row['farm_upgrades']),
        'bonus_upgrades': json.loads(row['bonus_upgrades']),
        'donors': json.loads(row['donors']),
    }

def validate_telegram_id(telegram_id):
    if telegram_id is None:
        return False
    try:
        return int(telegram_id) > 0
    except (ValueError, TypeError):
        return False

@app.route('/')
def index():
    return render_template_string('''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Кристалл-Кликер</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/lottie-web/5.12.2/lottie.min.js"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap" rel="stylesheet">
    <style>
        *{margin:0;padding:0;box-sizing:border-box;user-select:none;-webkit-tap-highlight-color:transparent;}
        body{background:#000;color:#fff;font-family:'Nunito',sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh;overflow:hidden;}
        .all{width:100%;max-width:500px;height:100vh;display:flex;flex-direction:column;overflow:hidden;}
        nav{display:flex;justify-content:space-between;padding:12px;height:60px;}
        .user-info{display:flex;align-items:center;gap:8px;}
        .user-avatar{width:40px;height:40px;border-radius:50%;background:linear-gradient(135deg,#6111cb,#2575fc);display:flex;align-items:center;justify-content:center;font-weight:800;}
        .users_stars_div{display:flex;align-items:center;gap:4px;}
        .user-stars{font-size:22px;font-weight:800;}
        .models-container{flex:1;position:relative;overflow:hidden;}
        .model-view{position:absolute;bottom:0;left:0;width:100%;height:calc(100vh - 120px);background:#1a1a1a;border-radius:50px 50px 0 0;border-top:3px solid #005eff;transform:translateY(100%);transition:transform 0.55s;overflow-y:auto;padding:20px;}
        .model-view.active-view{transform:translateY(0);}
        .stats-row{display:flex;gap:8px;margin-bottom:15px;}
        .stat-block{flex:1;background:#2a2a2a;padding:8px;border-radius:15px;text-align:center;}
        .stat-label{font-size:12px;font-weight:700;}
        .stat-value{font-size:20px;font-weight:800;display:flex;align-items:center;justify-content:center;gap:5px;}
        .main-image-container{display:flex;justify-content:center;align-items:center;gap:10px;margin:10px 0;}
        .main-counter{font-size:32px;font-weight:900;}
        .progress-container{margin:15px 0;}
        .progress-bar{width:100%;height:14px;background:#2a2a2a;border-radius:10px;overflow:hidden;}
        .progress-fill{height:100%;background:linear-gradient(to right,#6111cb,#2575fc);width:0%;}
        .bottom-section{margin-top:auto;display:flex;justify-content:center;}
        #sticker_container{width:180px;height:180px;cursor:pointer;margin:20px 0;}
        .action-btn{width:48px;height:48px;background:#2a2a2a;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:22px;cursor:pointer;position:absolute;left:10px;}
        .upgrade-categories{display:flex;gap:10px;margin:20px 0;}
        .category-block{flex:1;background:#2a2a2a;padding:10px;border-radius:15px;text-align:center;cursor:pointer;}
        .category-block.active-category{border:2px solid #005eff;}
        .upgrade-item{display:flex;justify-content:space-between;background:#2a2a2a;padding:12px;border-radius:15px;margin-bottom:10px;cursor:pointer;}
        .donate-item{display:flex;justify-content:space-between;background:#2a2a2a;padding:14px;border-radius:15px;margin-bottom:10px;cursor:pointer;}
        .rating-tabs{display:flex;gap:8px;margin:15px 0;}
        .rating-tab{flex:1;padding:10px;background:#2a2a2a;border-radius:15px;text-align:center;cursor:pointer;}
        .rating-tab.active-tab{border:2px solid #005eff;}
        .stats-item{display:flex;align-items:center;gap:10px;background:#2a2a2a;padding:10px;border-radius:12px;margin-bottom:6px;}
        footer{background:#2d2d36;display:flex;justify-content:space-around;padding:8px;height:60px;}
        footer a{color:#fff;text-decoration:none;display:flex;flex-direction:column;align-items:center;gap:2px;min-width:52px;}
        .rate-modal-overlay{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.8);display:flex;align-items:center;justify-content:center;z-index:9999;opacity:0;pointer-events:none;transition:0.25s;}
        .rate-modal-overlay.visible{opacity:1;pointer-events:auto;}
        .rate-modal{background:#1a1a1a;padding:24px;border-radius:20px;max-width:320px;width:90%;text-align:center;}
        .star-select{display:flex;justify-content:center;gap:8px;margin:15px 0;}
        .star-select span{font-size:36px;cursor:pointer;opacity:.3;}
        .star-select span.selected{opacity:1;}
        .game-notification{position:fixed;top:50px;left:50%;transform:translateX(-50%);padding:10px 22px;border-radius:30px;font-weight:700;z-index:9000;animation:notifFade 2s forwards;}
        @keyframes notifFade{0%{opacity:1;}100%{opacity:0;}}
    </style>
</head>
<body>
<div class="all">
    <nav>
        <div class="user-info">
            <div class="user-avatar" id="userAvatar"></div>
            <div class="user-name" id="userName">Загрузка...</div>
        </div>
        <div class="users_stars_div">
            <div class="user-stars" id="userStars">0</div>
            <span>⭐</span>
        </div>
    </nav>

    <div class="models-container">
        <!-- Главная -->
        <div id="model_view_1" class="model-view active-view">
            <div class="stats-row">
                <div class="stat-block"><div class="stat-label">За 1 клик</div><div class="stat-value"><span>💰</span><span id="user_upgrade">1</span></div></div>
                <div class="stat-block"><div class="stat-label">Необходимо</div><div class="stat-value"><span id="required-for-level">150</span></div></div>
                <div class="stat-block"><div class="stat-label">Монет в сек.</div><div class="stat-value"><span>💰</span><span id="user_upgrade_sek">0</span></div></div>
            </div>
            <div class="main-image-container">
                <span>💰</span>
                <div id="user_content_coin_lol" class="main-counter">0</div>
            </div>
            <div class="progress-container">
                <div class="progress-info"><span><span id="level">1</span>/10</span></div>
                <div class="progress-bar"><div class="progress-fill" id="progress-fill"></div></div>
            </div>
            <div class="action-btn" id="ads-btn">📹</div>
            <div class="bottom-section">
                <div id="sticker_container"></div>
            </div>
        </div>

        <!-- Улучшения -->
        <div id="model_view_2" class="model-view">
            <div class="main-image-container"><span>💰</span><div id="user_content_coin_lol_for_2" class="main-counter">0</div></div>
            <div class="upgrade-categories">
                <div class="category-block active-category" data-category="click"><span>👆</span><span>Клик</span></div>
                <div class="category-block" data-category="farm"><span>🌾</span><span>Ферма</span></div>
                <div class="category-block" data-category="bonus"><span>🎁</span><span>Бонус</span></div>
            </div>
            <div class="upgrade-content category-click" id="cat-click">
                <div class="upgrade-item" data-upg="click:power1"><span>👆 Усиленный клик +1</span><span><span id="price_1">100</span> 💰 <span class="upgrade-count">0</span></span></div>
                <div class="upgrade-item" data-upg="click:power2"><span>⚡ Супер клик +3</span><span><span id="price_2">500</span> 💰 <span class="upgrade-count">0</span></span></div>
                <div class="upgrade-item" data-upg="click:power3"><span>💥 Мега клик +5</span><span><span id="price_3">1000</span> 💰 <span class="upgrade-count">0</span></span></div>
            </div>
            <div class="upgrade-content category-farm" id="cat-farm" style="display:none;">
                <div class="upgrade-item" data-upg="farm:worker"><span>👨‍🌾 Рабочий +1/сек</span><span><span id="price_2_1">200</span> 💰 <span class="upgrade-count">0</span></span></div>
                <div class="upgrade-item" data-upg="farm:farmer"><span>🚜 Фермер +3/сек</span><span><span id="price_2_2">800</span> 💰 <span class="upgrade-count">0</span></span></div>
                <div class="upgrade-item" data-upg="farm:harvester"><span>🌽 Комбайн +5/сек</span><span><span id="price_2_3">2000</span> 💰 <span class="upgrade-count">0</span></span></div>
            </div>
            <div class="upgrade-content category-bonus" id="cat-bonus" style="display:none;">
                <div class="upgrade-item" data-upg="bonus:luck"><span>🍀 Удача</span><span><span id="price3_1">300</span> 💰 <span class="upgrade-count">0</span></span></div>
                <div class="upgrade-item" data-upg="bonus:crit"><span>⚡ Крит</span><span><span id="price_3_2">1500</span> 💰 <span class="upgrade-count">0</span></span></div>
            </div>
        </div>

        <!-- Донат -->
        <div id="model_view_3" class="model-view">
            <div class="main-image-container"><span>💰</span><div id="user_content_coin_lol_for_3" class="main-counter">0</div></div>
            <div class="donate-column">
                <div class="donate-item" id="donate-x2"><span>⚡ X2 монет навсегда</span><span>15 ⭐ <span class="red_green"></span></span></div>
                <div class="donate-item" id="donate-plus100k"><span>💰 +100 000 монет</span><span>20 ⭐ <span class="red_green"></span></span></div>
                <div class="donate-item" id="donate-x2sek"><span>⏱️ X2 монет в секунду</span><span>25 ⭐ <span class="red_green"></span></span></div>
                <div class="donate-item" id="donate-superclick"><span>👆 Супер-клик +5</span><span>30 ⭐ <span class="red_green"></span></span></div>
            </div>
        </div>

        <!-- Рейтинг -->
        <div id="model_view_4" class="model-view">
            <div class="rating-tabs">
                <div class="rating-tab active-tab" data-sort="balance">💰 Монеты</div>
                <div class="rating-tab" data-sort="level">⭐ Уровень</div>
                <div class="rating-tab" data-sort="rating">❤️ Рейтинг</div>
            </div>
            <div class="user-rating-card" style="background:#2a2a2a;padding:16px;border-radius:15px;margin-bottom:15px;text-align:center;">
                <div>Мой рейтинг</div>
                <div style="font-size:48px;color:#ffd700;" id="myRatingValue">0.0</div>
                <div id="myRatingStars">☆☆☆☆☆</div>
                <div id="myRatingCount">0 оценок</div>
            </div>
            <div class="stats-list" id="statsList"></div>
        </div>

        <!-- Промокоды -->
        <div id="model_view_5" class="model-view">
            <div class="promos-container">
                <div class="promo-card" style="background:#2a2a3a;padding:14px;border-radius:15px;margin-bottom:10px;">
                    <h2>Промокод на еду:</h2>
                    <button class="promo-buy-btn" data-price="5000000" style="width:100%;padding:12px;background:#fff;border:none;border-radius:30px;">Купить за 5M</button>
                </div>
                <div class="promo-card" style="background:#2a2a3a;padding:14px;border-radius:15px;margin-bottom:10px;">
                    <h2>Промокод на одежду:</h2>
                    <button class="promo-buy-btn" data-price="10000000" style="width:100%;padding:12px;background:#fff;border:none;border-radius:30px;">Купить за 10M</button>
                </div>
                <div class="promo-card" style="background:#2a2a3a;padding:14px;border-radius:15px;margin-bottom:10px;">
                    <h2>Промокод на книги:</h2>
                    <button class="promo-buy-btn" data-price="15000000" style="width:100%;padding:12px;background:#fff;border:none;border-radius:30px;">Купить за 15M</button>
                </div>
            </div>
        </div>
    </div>

    <footer id="footer">
        <a href="#" class="active" data-view="1"><span>💰</span><h4>Главная</h4></a>
        <a href="#" data-view="2"><span>⛏️</span><h4>Улучшения</h4></a>
        <a href="#" data-view="3"><span>💎</span><h4>Донат</h4></a>
        <a href="#" data-view="4"><span>🏆</span><h4>Рейтинг</h4></a>
        <a href="#" data-view="5"><span>🎁</span><h4>Промо</h4></a>
    </footer>
</div>

<div class="rate-modal-overlay" id="rateModalOverlay">
    <div class="rate-modal">
        <h3 id="rateModalTitle">Оценить игрока</h3>
        <div class="star-select" id="starSelect">
            <span data-star="1">⭐</span><span data-star="2">⭐</span><span data-star="3">⭐</span><span data-star="4">⭐</span><span data-star="5">⭐</span>
        </div>
        <textarea id="rateComment" placeholder="Комментарий" style="width:100%;height:60px;background:#2a2a2a;border:none;border-radius:10px;padding:10px;color:#fff;"></textarea>
        <div style="display:flex;gap:8px;margin-top:14px;">
            <button class="cancel-btn" id="rateCancelBtn" style="flex:1;padding:10px;background:#2a2a2a;border:none;border-radius:12px;">Отмена</button>
            <button class="submit-btn" id="rateSubmitBtn" style="flex:1;padding:10px;background:linear-gradient(to right,#9e00f3,#005eff);border:none;border-radius:12px;">Отправить</button>
        </div>
    </div>
</div>

<script>
const API_BASE = '/api';
const userData = {
    telegram_id: 0, username: 'Игрок', balance: 0, stars: 0, level: 1,
    clickPower: 1, passiveIncome: 0, progress: 0, totalClicks: 0, totalEarned: 0,
    clickUpgrades: { power1: { count: 0, base: 100, power: 1 }, power2: { count: 0, base: 500, power: 3 }, power3: { count: 0, base: 1000, power: 5 } },
    farmUpgrades: { worker: { count: 0, base: 200, income: 1 }, farmer: { count: 0, base: 800, income: 3 }, harvester: { count: 0, base: 2000, income: 5 } },
    bonusUpgrades: { luck: { count: 0, base: 300 }, crit: { count: 0, base: 1500 } },
    donors: { x2: false, x2sek: false, superclick: false },
    myRating: { avg: 0, count: 0 }
};

let mySticker = null;
let currentStickerLevel = 1;

const levelConfig = { base: 150, multi: 3, get(lvl) { return this.base * Math.pow(this.multi, lvl - 1); } };

function getPrice(base, count) { return Math.floor(base * Math.pow(1.5, count)); }
function format(n) { if (n >= 1e9) return (n/1e9).toFixed(1)+'B'; if (n>=1e6) return (n/1e6).toFixed(1)+'M'; if (n>=1e3) return (n/1e3).toFixed(1)+'K'; return String(n); }

function showNotification(text, isGood) {
    const n = document.createElement('div');
    n.className = 'game-notification';
    n.textContent = text;
    n.style.background = isGood ? '#4CAF50' : '#f44336';
    document.body.appendChild(n);
    setTimeout(() => n.remove(), 2000);
}

function updateUI() {
    const el = (id) => document.getElementById(id);
    el('user_content_coin_lol').textContent = format(userData.balance);
    el('user_content_coin_lol_for_2').textContent = format(userData.balance);
    el('user_content_coin_lol_for_3').textContent = format(userData.balance);
    el('userStars').textContent = userData.stars;
    el('userName').textContent = userData.username;
    el('userAvatar').textContent = userData.username.charAt(0).toUpperCase();
    
    let displayClick = userData.clickPower;
    if (userData.donors.x2) displayClick *= 2;
    el('user_upgrade').textContent = displayClick;
    
    let displayPassive = userData.passiveIncome;
    if (userData.donors.x2sek) displayPassive *= 2;
    el('user_upgrade_sek').textContent = displayPassive;
    
    const need = levelConfig.get(userData.level);
    const pct = Math.min((userData.progress / need) * 100, 100);
    el('progress-fill').style.width = pct + '%';
    el('level').textContent = userData.level;
    el('required-for-level').textContent = format(need);
    
    el('price_1').textContent = format(getPrice(100, userData.clickUpgrades.power1.count));
    el('price_2').textContent = format(getPrice(500, userData.clickUpgrades.power2.count));
    el('price_3').textContent = format(getPrice(1000, userData.clickUpgrades.power3.count));
    el('price_2_1').textContent = format(getPrice(200, userData.farmUpgrades.worker.count));
    el('price_2_2').textContent = format(getPrice(800, userData.farmUpgrades.farmer.count));
    el('price_2_3').textContent = format(getPrice(2000, userData.farmUpgrades.harvester.count));
    el('price3_1').textContent = format(getPrice(300, userData.bonusUpgrades.luck.count));
    el('price_3_2').textContent = format(getPrice(1500, userData.bonusUpgrades.crit.count));
    
    document.querySelectorAll('.category-click .upgrade-count')[0].textContent = userData.clickUpgrades.power1.count;
    document.querySelectorAll('.category-click .upgrade-count')[1].textContent = userData.clickUpgrades.power2.count;
    document.querySelectorAll('.category-click .upgrade-count')[2].textContent = userData.clickUpgrades.power3.count;
    document.querySelectorAll('.category-farm .upgrade-count')[0].textContent = userData.farmUpgrades.worker.count;
    document.querySelectorAll('.category-farm .upgrade-count')[1].textContent = userData.farmUpgrades.farmer.count;
    document.querySelectorAll('.category-farm .upgrade-count')[2].textContent = userData.farmUpgrades.harvester.count;
    document.querySelectorAll('.category-bonus .upgrade-count')[0].textContent = userData.bonusUpgrades.luck.count;
    document.querySelectorAll('.category-bonus .upgrade-count')[1].textContent = userData.bonusUpgrades.crit.count;
    
    updateDonateStatus();
    
    el('myRatingValue').textContent = userData.myRating.avg.toFixed(1);
    let stars = '';
    for (let i=1; i<=5; i++) stars += i <= Math.round(userData.myRating.avg) ? '★' : '☆';
    el('myRatingStars').textContent = stars;
    el('myRatingCount').textContent = userData.myRating.count + ' оценок';
}

function updateDonateStatus() {
    const items = [
        { id: 'donate-x2', key: 'x2' },
        { id: 'donate-plus100k', key: null },
        { id: 'donate-x2sek', key: 'x2sek' },
        { id: 'donate-superclick', key: 'superclick' }
    ];
    items.forEach(item => {
        const el = document.getElementById(item.id);
        const dot = el ? el.querySelector('.red_green') : null;
        if (dot) dot.style.backgroundColor = (item.key && userData.donors[item.key]) ? '#4CAF50' : '#f44336';
    });
}

function handleClick(e) {
    let earned = userData.clickPower;
    const critChance = Math.min(userData.bonusUpgrades.crit.count * 0.05, 0.3);
    if (critChance > 0 && Math.random() < critChance) {
        earned *= 5;
        showNotification('КРИТ! x5', true);
    }
    if (userData.bonusUpgrades.luck.count > 0) {
        earned = Math.floor(earned * (1 + userData.bonusUpgrades.luck.count * 0.05));
    }
    if (userData.donors.x2) earned *= 2;
    
    userData.balance += earned;
    userData.progress += userData.clickPower;
    userData.totalClicks++;
    userData.totalEarned += earned;
    
    checkLevel();
    updateUI();
    
    const f = document.createElement('div');
    f.textContent = '+' + format(earned);
    f.style.cssText = 'position:fixed;left:'+ (e.clientX||200) +'px;top:'+ (e.clientY||400) +'px;color:#ffd700;font-size:26px;font-weight:900;pointer-events:none;z-index:1000;animation:floatUp 1s forwards;';
    document.body.appendChild(f);
    setTimeout(() => f.remove(), 1000);
}

function checkLevel() {
    let need = levelConfig.get(userData.level);
    while (userData.progress >= need && userData.level < 10) {
        userData.progress -= need;
        userData.level++;
        userData.clickPower++;
        userData.balance += 50 * userData.level;
        need = levelConfig.get(userData.level);
        showNotification('УРОВЕНЬ ' + userData.level + '!', true);
        if (mySticker) loadSticker(userData.level);
    }
}

function loadSticker(level) {
    if (!document.getElementById('sticker_container')) return;
    let path = '/static/imgs/for_img_crystal/AnimatedSticker.json';
    if (level == 1) path = '/static/imgs/for_img_crystal/AnimatedSticker2.json';
    else if (level == 2) path = '/static/imgs/for_img_crystal/AnimatedSticker.json';
    else if (level == 3) path = '/static/imgs/for_img_crystal/AnimatedSticker3.json';
    
    if (mySticker) mySticker.destroy();
    mySticker = lottie.loadAnimation({
        container: document.getElementById('sticker_container'),
        renderer: 'svg',
        loop: true,
        autoplay: true,
        path: path
    });
    currentStickerLevel = level;
}

function buyUpgrade(type, key) {
    let upg, price;
    if (type === 'click') {
        upg = userData.clickUpgrades[key];
        price = getPrice(upg.base, upg.count);
        if (userData.balance < price) { showNotification('Недостаточно монет!', false); return; }
        userData.balance -= price;
        upg.count++;
        userData.clickPower = 1 + userData.clickUpgrades.power1.count*1 + userData.clickUpgrades.power2.count*3 + userData.clickUpgrades.power3.count*5;
        showNotification('+' + upg.power + ' к клику!', true);
    } else if (type === 'farm') {
        upg = userData.farmUpgrades[key];
        price = getPrice(upg.base, upg.count);
        if (userData.balance < price) { showNotification('Недостаточно монет!', false); return; }
        userData.balance -= price;
        upg.count++;
        userData.passiveIncome = userData.farmUpgrades.worker.count*1 + userData.farmUpgrades.farmer.count*3 + userData.farmUpgrades.harvester.count*5;
        showNotification('+' + upg.income + ' монет/сек!', true);
    } else if (type === 'bonus') {
        upg = userData.bonusUpgrades[key];
        price = getPrice(upg.base, upg.count);
        if (userData.balance < price) { showNotification('Недостаточно монет!', false); return; }
        userData.balance -= price;
        upg.count++;
        showNotification(key === 'luck' ? 'Удача +5%!' : 'Шанс крита +5%!', true);
    }
    updateUI();
    syncToServer();
}

function initDonateShop() {
    const handlers = {
        'donate-x2': { stars: 15, key: 'x2', msg: 'X2 монет навсегда!' },
        'donate-plus100k': { stars: 20, key: null, msg: '+100 000 монет!' },
        'donate-x2sek': { stars: 25, key: 'x2sek', msg: 'X2 монет в секунду!' },
        'donate-superclick': { stars: 30, key: 'superclick', msg: 'Супер-клик +5!' }
    };
    Object.entries(handlers).forEach(([id, cfg]) => {
        document.getElementById(id)?.addEventListener('click', () => {
            if (cfg.key && userData.donors[cfg.key]) { showNotification('Уже куплено!', false); return; }
            if (userData.stars < cfg.stars) { showNotification('Нужно ' + cfg.stars + ' ⭐!', false); return; }
            userData.stars -= cfg.stars;
            if (cfg.key) userData.donors[cfg.key] = true;
            if (id === 'donate-plus100k') userData.balance += 100000;
            if (id === 'donate-superclick') userData.clickPower += 5;
            updateUI();
            syncToServer();
            showNotification(cfg.msg, true);
        });
    });
}

function syncToServer() {
    fetch(API_BASE + '/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            telegram_id: userData.telegram_id,
            balance: userData.balance,
            stars: userData.stars,
            level: userData.level,
            click_power: userData.clickPower,
            passive_income: userData.passiveIncome,
            progress: userData.progress,
            total_clicks: userData.totalClicks,
            total_earned: userData.totalEarned,
            click_upgrades: {
                power1: userData.clickUpgrades.power1.count,
                power2: userData.clickUpgrades.power2.count,
                power3: userData.clickUpgrades.power3.count
            },
            farm_upgrades: {
                worker: userData.farmUpgrades.worker.count,
                farmer: userData.farmUpgrades.farmer.count,
                harvester: userData.farmUpgrades.harvester.count
            },
            bonus_upgrades: {
                luck: userData.bonusUpgrades.luck.count,
                crit: userData.bonusUpgrades.crit.count
            },
            donors: userData.donors
        })
    }).catch(() => {});
}

// Навигация
document.querySelectorAll('footer a').forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        document.querySelectorAll('footer a').forEach(l => l.classList.remove('active'));
        link.classList.add('active');
        const view = link.getAttribute('data-view');
        document.querySelectorAll('.model-view').forEach(v => v.classList.remove('active-view'));
        document.querySelector(`.model-view[data-view="${view}"]`)?.classList.add('active-view');
        if (view === '4') loadLeaderboard();
    });
});

// Категории улучшений
document.querySelectorAll('.category-block').forEach(block => {
    block.addEventListener('click', () => {
        document.querySelectorAll('.category-block').forEach(b => b.classList.remove('active-category'));
        block.classList.add('active-category');
        const cat = block.getAttribute('data-category');
        document.getElementById('cat-click').style.display = cat === 'click' ? 'flex' : 'none';
        document.getElementById('cat-farm').style.display = cat === 'farm' ? 'flex' : 'none';
        document.getElementById('cat-bonus').style.display = cat === 'bonus' ? 'flex' : 'none';
    });
});

// Покупка улучшений
document.querySelectorAll('.upgrade-item').forEach(item => {
    item.addEventListener('click', () => {
        const [type, key] = item.getAttribute('data-upg').split(':');
        buyUpgrade(type, key);
    });
});

initDonateShop();

// Рейтинг
let currentSort = 'balance';
let leaderboardData = [];
let currentRateTarget = null;
let selectedStarScore = 0;

function loadLeaderboard() {
    fetch(API_BASE + '/leaderboard?sort=' + currentSort + '&limit=50')
        .then(r => r.json())
        .then(data => {
            if (data.ok) {
                leaderboardData = data.leaderboard;
                document.getElementById('totalUsers').textContent = 'Всего: ' + data.total_users;
                renderLeaderboard();
            }
        })
        .catch(() => {
            document.getElementById('statsList').innerHTML = '<div style="text-align:center;">Ошибка загрузки</div>';
        });
}

function renderLeaderboard() {
    const listEl = document.getElementById('statsList');
    if (!leaderboardData.length) {
        listEl.innerHTML = '<div style="text-align:center;">Нет данных</div>';
        return;
    }
    let html = '';
    leaderboardData.forEach(player => {
        const isMe = player.telegram_id === userData.telegram_id;
        let value = currentSort === 'balance' ? format(player.balance) + ' монет' :
                   currentSort === 'level' ? 'Ур.' + player.level : player.avg_rating.toFixed(1) + ' ★';
        html += `<div class="stats-item${isMe ? ' current-user-highlight' : ''}" data-tid="${player.telegram_id}" data-name="${player.username}">
            <div class="stats-rank">${player.rank}</div>
            <div class="stats-avatar">${player.username.charAt(0)}</div>
            <div class="stats-user-info"><div class="stats-user">${player.username}${isMe ? ' (Вы)' : ''}</div></div>
            <div class="stats-value"><div class="stats-clicks">${value}</div></div>
        </div>`;
    });
    listEl.innerHTML = html;
    
    listEl.querySelectorAll('.stats-item').forEach(item => {
        item.addEventListener('click', () => {
            const tid = parseInt(item.getAttribute('data-tid'));
            const name = item.getAttribute('data-name');
            if (tid === userData.telegram_id) { showNotification('Нельзя оценить себя!', false); return; }
            openRateModal(tid, name);
        });
    });
}

document.querySelectorAll('.rating-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.rating-tab').forEach(t => t.classList.remove('active-tab'));
        tab.classList.add('active-tab');
        currentSort = tab.getAttribute('data-sort');
        loadLeaderboard();
    });
});

function openRateModal(tid, name) {
    currentRateTarget = tid;
    selectedStarScore = 0;
    document.getElementById('rateModalTitle').textContent = 'Оценить: ' + name;
    document.getElementById('rateComment').value = '';
    document.querySelectorAll('#starSelect span').forEach(s => s.classList.remove('selected'));
    document.getElementById('rateModalOverlay').classList.add('visible');
}

function closeRateModal() {
    document.getElementById('rateModalOverlay').classList.remove('visible');
    currentRateTarget = null;
}

document.querySelectorAll('#starSelect span').forEach(star => {
    star.addEventListener('click', () => {
        selectedStarScore = parseInt(star.getAttribute('data-star'));
        document.querySelectorAll('#starSelect span').forEach(s => {
            parseInt(s.getAttribute('data-star')) <= selectedStarScore ? s.classList.add('selected') : s.classList.remove('selected');
        });
    });
});

document.getElementById('rateCancelBtn').addEventListener('click', closeRateModal);
document.getElementById('rateModalOverlay').addEventListener('click', (e) => { if (e.target === e.currentTarget) closeRateModal(); });

document.getElementById('rateSubmitBtn').addEventListener('click', () => {
    if (selectedStarScore < 1) { showNotification('Выберите оценку!', false); return; }
    if (!currentRateTarget) return;
    fetch(API_BASE + '/rate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            from_user: userData.telegram_id,
            to_user: currentRateTarget,
            score: selectedStarScore,
            comment: document.getElementById('rateComment').value.trim()
        })
    })
    .then(r => r.json())
    .then(data => {
        if (data.ok) {
            showNotification('Оценка отправлена!', true);
            closeRateModal();
            loadLeaderboard();
        }
    })
    .catch(() => showNotification('Ошибка', false));
});

// Промокоды
let boughtPromos = [false, false, false];
document.querySelectorAll('.promo-buy-btn').forEach((btn, i) => {
    btn.addEventListener('click', () => {
        if (boughtPromos[i]) { showNotification('Уже куплено!', false); return; }
        const price = parseInt(btn.getAttribute('data-price'));
        if (userData.balance < price) { showNotification('Недостаточно монет!', false); return; }
        userData.balance -= price;
        boughtPromos[i] = true;
        let code = '';
        for (let c = 0; c < 8; c++) code += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'[Math.floor(Math.random() * 36)];
        const promoDiv = document.createElement('div');
        promoDiv.textContent = 'Промокод: ' + code;
        promoDiv.style.cssText = 'background:#2a2a2a;color:#ffd700;padding:10px;border-radius:10px;margin-top:10px;';
        btn.closest('.promo-card').appendChild(promoDiv);
        btn.textContent = 'Куплено ✓';
        btn.disabled = true;
        updateUI();
        syncToServer();
    });
});

// Пузырьки
let bubbleActive = false;
function startBubbles() {
    setInterval(() => {
        if (!bubbleActive) createBubble();
    }, Math.random() * 15000 + 3000);
}

function createBubble() {
    const container = document.getElementById('gameRoot');
    if (!container) return;
    const rect = container.getBoundingClientRect();
    if (rect.width === 0) return;
    
    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    const size = Math.floor(Math.random() * 35) + 30;
    Object.assign(bubble.style, {
        position: 'absolute',
        width: size + 'px',
        height: size + 'px',
        left: Math.floor(Math.random() * (rect.width - size)) + 'px',
        bottom: '0px',
        borderRadius: '50%',
        background: 'rgba(97,17,203,.7)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#fff',
        fontWeight: '800',
        cursor: 'pointer',
        animation: `bubbleRise ${(Math.random() * 2 + 2).toFixed(1)}s linear forwards`
    });
    
    const reward = Math.floor(Math.random() * 500) + 20;
    bubble.textContent = '+' + reward;
    bubble.onclick = (e) => {
        e.stopPropagation();
        userData.balance += reward;
        userData.totalEarned += reward;
        showNotification('+' + reward + ' монет!', true);
        updateUI();
        bubble.remove();
        bubbleActive = false;
    };
    bubble.onanimationend = () => {
        bubble.remove();
        bubbleActive = false;
    };
    container.appendChild(bubble);
    bubbleActive = true;
}

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
    const tg = window.Telegram?.WebApp;
    if (tg?.initDataUnsafe?.user) {
        const u = tg.initDataUnsafe.user;
        userData.telegram_id = u.id;
        userData.username = u.first_name + (u.last_name ? ' ' + u.last_name : '');
        
        fetch(API_BASE + '/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ telegram_id: userData.telegram_id, username: userData.username })
        })
        .then(r => r.json())
        .then(data => {
            if (data.ok && data.user) {
                userData.balance = data.user.balance || 0;
                userData.stars = data.user.stars || 0;
                userData.level = data.user.level || 1;
                userData.clickPower = data.user.click_power || 1;
                userData.passiveIncome = data.user.passive_income || 0;
                userData.progress = data.user.progress || 0;
                userData.totalClicks = data.user.total_clicks || 0;
                userData.totalEarned = data.user.total_earned || 0;
                
                if (data.user.click_upgrades) {
                    userData.clickUpgrades.power1.count = data.user.click_upgrades.power1 || 0;
                    userData.clickUpgrades.power2.count = data.user.click_upgrades.power2 || 0;
                    userData.clickUpgrades.power3.count = data.user.click_upgrades.power3 || 0;
                    userData.clickPower = 1 + userData.clickUpgrades.power1.count*1 + userData.clickUpgrades.power2.count*3 + userData.clickUpgrades.power3.count*5;
                }
                if (data.user.farm_upgrades) {
                    userData.farmUpgrades.worker.count = data.user.farm_upgrades.worker || 0;
                    userData.farmUpgrades.farmer.count = data.user.farm_upgrades.farmer || 0;
                    userData.farmUpgrades.harvester.count = data.user.farm_upgrades.harvester || 0;
                    userData.passiveIncome = userData.farmUpgrades.worker.count*1 + userData.farmUpgrades.farmer.count*3 + userData.farmUpgrades.harvester.count*5;
                }
                if (data.user.bonus_upgrades) {
                    userData.bonusUpgrades.luck.count = data.user.bonus_upgrades.luck || 0;
                    userData.bonusUpgrades.crit.count = data.user.bonus_upgrades.crit || 0;
                }
                if (data.user.donors) {
                    userData.donors = data.user.donors;
                }
                userData.myRating.avg = data.user.rating?.avg || 0;
                userData.myRating.count = data.user.rating?.count || 0;
            }
            updateUI();
            loadSticker(userData.level);
        })
        .catch(() => {
            console.log('Оффлайн режим');
            updateUI();
            loadSticker(userData.level);
        });
    } else {
        userData.telegram_id = Math.floor(Math.random() * 900000) + 100000;
        userData.username = 'Тест_' + (userData.telegram_id % 10000);
        updateUI();
        loadSticker(1);
    }

    document.getElementById('sticker_container')?.addEventListener('click', handleClick);
    document.getElementById('ads-btn')?.addEventListener('click', () => {
        if (confirm('Получить звезду за рекламу?')) {
            userData.stars++;
            updateUI();
            syncToServer();
            showNotification('+1 звезда!', true);
        }
    });

    setInterval(() => {
        let income = userData.passiveIncome;
        if (userData.donors.x2sek) income *= 2;
        if (income > 0) {
            userData.balance += income;
            userData.totalEarned += income;
            updateUI();
        }
    }, 1000);
    
    setInterval(syncToServer, 10000);
    
    // Добавляем стили для анимации
    const style = document.createElement('style');
    style.textContent = '@keyframes floatUp{0%{opacity:1;}100%{opacity:0;transform:translateY(-100px);}} @keyframes bubbleRise{0%{transform:translateY(0);opacity:1;}100%{transform:translateY(-350px);opacity:0;}}';
    document.head.appendChild(style);
});
</script>
</body>
</html>
    ''')

# API endpoints
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data: return jsonify({'ok': False, 'error': 'Нет данных'}), 400
    
    telegram_id = data.get('telegram_id')
    if not validate_telegram_id(telegram_id): return jsonify({'ok': False, 'error': 'Неверный telegram_id'}), 400
    
    username = data.get('username', 'Аноним')[:50]
    avatar_url = data.get('avatar_url', '')
    db = get_db()
    
    existing = db.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,)).fetchone()
    
    if existing:
        db.execute('UPDATE users SET username = ?, avatar_url = ?, updated_at = ? WHERE telegram_id = ?',
                  (username, avatar_url, datetime.now(), telegram_id))
        db.commit()
        user = db.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,)).fetchone()
        rating = db.execute('SELECT AVG(score) as avg, COUNT(*) as count FROM ratings WHERE to_user = ?', (telegram_id,)).fetchone()
        user_dict = user_to_dict(user)
        user_dict['rating'] = {'avg': round(rating['avg'], 1) if rating['avg'] else 0, 'count': rating['count']}
        return jsonify({'ok': True, 'user': user_dict, 'is_new': False})
    
    db.execute('INSERT INTO users (telegram_id, username, avatar_url) VALUES (?, ?, ?)',
              (telegram_id, username, avatar_url))
    db.commit()
    user = db.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,)).fetchone()
    user_dict = user_to_dict(user)
    user_dict['rating'] = {'avg': 0, 'count': 0}
    return jsonify({'ok': True, 'user': user_dict, 'is_new': True})

@app.route('/api/sync', methods=['POST'])
def sync():
    data = request.get_json()
    if not data: return jsonify({'ok': False, 'error': 'Нет данных'}), 400
    
    telegram_id = data.get('telegram_id')
    if not validate_telegram_id(telegram_id): return jsonify({'ok': False, 'error': 'Неверный telegram_id'}), 400
    
    db = get_db()
    existing = db.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,)).fetchone()
    if not existing: return jsonify({'ok': False, 'error': 'Пользователь не найден'}), 404
    
    db.execute('''
        UPDATE users SET
            balance = ?, stars = ?, level = ?, click_power = ?, passive_income = ?,
            progress = ?, total_clicks = ?, total_earned = ?,
            click_upgrades = ?, farm_upgrades = ?, bonus_upgrades = ?, donors = ?,
            updated_at = ?, last_sync = ?
        WHERE telegram_id = ?
    ''', (
        data.get('balance', existing['balance']),
        data.get('stars', existing['stars']),
        data.get('level', existing['level']),
        data.get('click_power', existing['click_power']),
        data.get('passive_income', existing['passive_income']),
        data.get('progress', existing['progress']),
        data.get('total_clicks', existing['total_clicks']),
        data.get('total_earned', existing['total_earned']),
        json.dumps(data.get('click_upgrades', json.loads(existing['click_upgrades']))),
        json.dumps(data.get('farm_upgrades', json.loads(existing['farm_upgrades']))),
        json.dumps(data.get('bonus_upgrades', json.loads(existing['bonus_upgrades']))),
        json.dumps(data.get('donors', json.loads(existing['donors']))),
        datetime.now(), datetime.now(), telegram_id
    ))
    db.commit()
    user = db.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,)).fetchone()
    return jsonify({'ok': True, 'user': user_to_dict(user)})

@app.route('/api/user/<int:telegram_id>', methods=['GET'])
def get_user(telegram_id):
    if not validate_telegram_id(telegram_id): return jsonify({'ok': False, 'error': 'Неверный telegram_id'}), 400
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,)).fetchone()
    if not user: return jsonify({'ok': False, 'error': 'Пользователь не найден'}), 404
    rating = db.execute('SELECT AVG(score) as avg_score, COUNT(*) as count FROM ratings WHERE to_user = ?', (telegram_id,)).fetchone()
    return jsonify({
        'ok': True,
        'user': user_to_dict(user),
        'rating': {
            'avg': round(rating['avg_score'], 1) if rating['avg_score'] else 0,
            'count': rating['count']
        }
    })

@app.route('/api/leaderboard', methods=['GET'])
def leaderboard():
    sort_by = request.args.get('sort', 'balance')
    limit = min(int(request.args.get('limit', 50)), LEADERBOARD_LIMIT)
    offset = max(int(request.args.get('offset', 0)), 0)
    
    order_map = {
        'balance': 'u.balance DESC',
        'total_earned': 'u.total_earned DESC',
        'level': 'u.level DESC, u.balance DESC',
        'rating': 'avg_rating DESC',
        'total_clicks': 'u.total_clicks DESC'
    }
    order = order_map.get(sort_by, 'u.balance DESC')
    db = get_db()
    
    rows = db.execute(f'''
        SELECT u.telegram_id, u.username, u.avatar_url, u.balance, u.level,
               u.total_clicks, u.total_earned,
               COALESCE(avg_r.avg_score, 0) as avg_rating,
               COALESCE(avg_r.rating_count, 0) as rating_count
        FROM users u
        LEFT JOIN (
            SELECT to_user, AVG(score) as avg_score, COUNT(*) as rating_count
            FROM ratings GROUP BY to_user
        ) avg_r ON avg_r.to_user = u.telegram_id
        ORDER BY {order}
        LIMIT ? OFFSET ?
    ''', (limit, offset)).fetchall()
    
    total = db.execute('SELECT COUNT(*) as cnt FROM users').fetchone()['cnt']
    
    leaderboard_list = []
    for i, row in enumerate(rows):
        leaderboard_list.append({
            'rank': offset + i + 1,
            'telegram_id': row['telegram_id'],
            'username': row['username'],
            'avatar_url': row['avatar_url'],
            'balance': row['balance'],
            'level': row['level'],
            'total_clicks': row['total_clicks'],
            'total_earned': row['total_earned'],
            'avg_rating': round(row['avg_rating'], 1),
            'rating_count': row['rating_count']
        })
    
    return jsonify({'ok': True, 'leaderboard': leaderboard_list, 'total_users': total})

@app.route('/api/rate', methods=['POST'])
def rate_user():
    data = request.get_json()
    if not data: return jsonify({'ok': False, 'error': 'Нет данных'}), 400
    
    from_user = data.get('from_user')
    to_user = data.get('to_user')
    score = data.get('score')
    comment = data.get('comment', '')[:200]
    
    if not validate_telegram_id(from_user) or not validate_telegram_id(to_user):
        return jsonify({'ok': False, 'error': 'Неверный telegram_id'}), 400
    if from_user == to_user: return jsonify({'ok': False, 'error': 'Нельзя оценить себя'}), 400
    if not isinstance(score, int) or score < 1 or score > 5:
        return jsonify({'ok': False, 'error': 'Оценка от 1 до 5'}), 400
    
    db = get_db()
    for uid in [from_user, to_user]:
        if not db.execute('SELECT telegram_id FROM users WHERE telegram_id = ?', (uid,)).fetchone():
            return jsonify({'ok': False, 'error': f'Пользователь {uid} не найден'}), 404
    
    db.execute('''
        INSERT INTO ratings (from_user, to_user, score, comment, created_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(from_user, to_user)
        DO UPDATE SET score = ?, comment = ?, created_at = ?
    ''', (from_user, to_user, score, comment, datetime.now(), score, comment, datetime.now()))
    db.commit()
    
    rating = db.execute('SELECT AVG(score) as avg_score, COUNT(*) as count FROM ratings WHERE to_user = ?', (to_user,)).fetchone()
    return jsonify({
        'ok': True,
        'rating': {
            'avg': round(rating['avg_score'], 1) if rating['avg_score'] else 0,
            'count': rating['count']
        }
    })

@app.route('/api/ratings/<int:telegram_id>', methods=['GET'])
def get_ratings(telegram_id):
    if not validate_telegram_id(telegram_id): return jsonify({'ok': False, 'error': 'Неверный telegram_id'}), 400
    limit = min(int(request.args.get('limit', 20)), 50)
    offset = max(int(request.args.get('offset', 0)), 0)
    db = get_db()
    
    avg = db.execute('SELECT AVG(score) as avg_score, COUNT(*) as count FROM ratings WHERE to_user = ?', (telegram_id,)).fetchone()
    ratings = db.execute('''
        SELECT r.from_user, u.username as from_username, r.score, r.comment, r.created_at
        FROM ratings r JOIN users u ON u.telegram_id = r.from_user
        WHERE r.to_user = ? ORDER BY r.created_at DESC LIMIT ? OFFSET ?
    ''', (telegram_id, limit, offset)).fetchall()
    
    return jsonify({
        'ok': True,
        'avg': round(avg['avg_score'], 1) if avg['avg_score'] else 0,
        'count': avg['count'],
        'ratings': [{'from_user': r['from_user'], 'from_username': r['from_username'],
                     'score': r['score'], 'comment': r['comment'], 'created_at': r['created_at']} for r in ratings]
    })

if __name__ == '__main__':
    if not os.path.exists(DATABASE): init_db()
    print("="*50)
    print("  Кристалл-Кликер")
    print("  http://localhost:5000")
    print("="*50)
    app.run(host='0.0.0.0', port=5000, debug=True)

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
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = sqlite3.connect(DATABASE)
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
            UNIQUE(from_user, to_user)
        )
    ''')
    db.commit()
    db.close()

def user_to_dict(row):
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
    try:
        return int(telegram_id) > 0
    except:
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
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        /* ================= RESET & BASE ================= */
        *{margin:0;padding:0;box-sizing:border-box;
          -webkit-tap-highlight-color:transparent;
          -webkit-touch-callout:none;
          -webkit-user-select:none;-moz-user-select:none;
          -ms-user-select:none;user-select:none;}

        :root{
          --bg-main:#000;
          --bg-panel:#1a1a1a;
          --bg-card:#2a2a2a;
          --bg-footer:#2d2d36;
          --border-card:#3a3a3a;
          --accent-blue:#005eff;
          --accent-purple:#9e00f3;
          --accent-gold:#ffd700;
          --text-primary:#fff;
          --text-secondary:#888;
          --success:#4CAF50;
          --error:#f44336;
          --gradient-main:linear-gradient(to right,#9e00f3,#005eff);
          --gradient-progress:linear-gradient(to right,#6111cb,#2575fc);
          --glow-blue:0 -15px 20px rgba(0,60,255,0.5);
          --radius-view:50px;
          --radius-card:15px;
          --radius-pill:30px;
          --font:'Nunito',sans-serif;
        }

        body{
          background:var(--bg-main);
          color:var(--text-primary);
          display:flex;justify-content:center;align-items:center;
          min-height:100vh;width:100%;
          font-family:var(--font);
          overflow:hidden;
        }

        img{width:100%;}
        a{font-weight:bold;text-decoration:none;color:inherit;}

        /* ================= MAIN CONTAINER ================= */
        .all{
          position:relative;width:100%;max-width:500px;
          background:var(--bg-main);height:100vh;
          color:var(--text-primary);
          display:flex;flex-direction:column;overflow:hidden;
        }

        /* ================= NAV ================= */
        .for_nav{width:100%;display:flex;justify-content:center;}
        nav{
          width:100%;display:flex;justify-content:space-between;
          height:50px;text-align:center;align-items:center;
          padding:0 12px;
        }
        .user-info,.users_stars_div{display:flex;align-items:center;gap:6px;}
        .user-avatar{
          width:32px;height:32px;border-radius:50%;
          background:linear-gradient(135deg,#6111cb,#2575fc);
          display:flex;align-items:center;justify-content:center;
          font-size:14px;font-weight:800;color:#fff;
          flex-shrink:0;
        }
        .user-name{font-size:14px;font-weight:700;}
        .user-stars{font-size:22px;font-weight:800;}
        .starsss_img{width:28px;height:28px;display:flex;align-items:center;}
        .starsss_img i{font-size:22px;color:var(--accent-gold);}

        /* ================= VIEWS CONTAINER ================= */
        .models-container{position:relative;flex:1;overflow:hidden;}
        .model-view{
          position:absolute;bottom:0;left:0;width:100%;
          height:calc(100vh - 140px);max-height:calc(100vh - 50px);
          background:var(--bg-panel);
          border-radius:var(--radius-view) var(--radius-view) 0 0;
          border-top:3px solid var(--accent-blue);
          transform:translateY(100%);
          transition:transform 0.55s cubic-bezier(.22,.68,0,1.1);
          color:var(--text-primary);z-index:10;
          overflow-y:auto;overflow-x:hidden;
          scrollbar-width:none;
        }
        .model-view::-webkit-scrollbar{display:none;}
        .model-view.active-view{
          transform:translateY(0);
          box-shadow:var(--glow-blue);
        }
        .model-content{
          padding:20px;min-height:100%;
          display:flex;flex-direction:column;
        }

        /* ================= VIEW 1: MAIN CLICK ================= */
        .stats-row{
          display:flex;justify-content:space-between;
          gap:8px;margin-bottom:15px;flex-shrink:0;
        }
        .stat-block{
          flex:1;text-align:center;display:flex;flex-direction:column;gap:6px;
          background:var(--bg-card);padding:8px 5px;
          border-radius:var(--radius-card);border:1px solid var(--border-card);
          box-shadow:0 4px 0 #0a0a0a;cursor:pointer;transition:.1s ease-in-out;
        }
        .stat-block:hover{transform:translateY(2px);}
        .stat-label{
          font-size:10px;color:#fff;font-weight:700;
          text-transform:uppercase;letter-spacing:.5px;
        }
        .stat-value{
          display:flex;align-items:center;justify-content:center;
          gap:5px;font-size:20px;font-weight:800;color:#fff;
        }
        .stat-icon{width:22px;height:22px;}
        .coin-svg{width:22px;height:22px;flex-shrink:0;}
        .main-image-container{
          display:flex;justify-content:center;align-items:center;
          text-align:center;margin:8px 0;flex-shrink:0;gap:8px;
        }
        .main-coin{width:50px;height:50px;}
        .main-counter,.main-counter2{
          font-size:32px;font-weight:900;color:#fff;letter-spacing:1px;
        }
        .progress-container{margin:12px 0;padding:0 10px;flex-shrink:0;}
        .progress-info{display:flex;justify-content:flex-end;font-size:13px;margin-bottom:4px;font-weight:700;}
        .progress-bar{
          width:100%;height:14px;background:var(--bg-card);
          border-radius:10px;overflow:hidden;border:1px solid var(--border-card);
        }
        .progress-fill{
          height:100%;background:var(--gradient-progress);
          border-radius:10px;transition:width .3s ease;width:0%;
        }
        .action-buttons{
          position:relative;display:flex;justify-content:space-between;
          align-items:center;margin-top:16px;width:100%;pointer-events:none;z-index:15;
        }
        .action-btn{
          position:absolute;display:flex;align-items:center;justify-content:center;
          width:48px;height:48px;
          background:linear-gradient(145deg,#2a2a2a,#1a1a1a);
          border-radius:50%;border:2px solid var(--border-card);
          box-shadow:0 4px 0 #0a0a0a;cursor:pointer;
          transition:.1s ease-in-out;pointer-events:auto;font-size:22px;
        }
        .action-btn:active{transform:translateY(4px);box-shadow:none;}
        .left-btn{left:10px;}
        .bottom-section{
          margin-top:auto;display:flex;flex-direction:column;
          align-items:center;width:100%;flex-shrink:0;
        }
        .tapalka{display:flex;width:100%;justify-content:center;align-items:center;}
        #sticker_container{
          width:180px;height:180px;cursor:pointer;
          margin-bottom:16px;transition:transform .08s;
          display:flex;align-items:center;justify-content:center;
        }
        #sticker_container:active{transform:scale(.92);}
        .crystal-emoji{font-size:140px;filter:drop-shadow(0 0 30px rgba(97,17,203,.6));}

        /* ================= VIEW 2: UPGRADES ================= */
        .donate-title{text-align:center;margin:8px 0 16px;}
        .donate-title p{color:var(--text-secondary);font-size:14px;font-weight:600;}
        .upgrade-categories{
          display:flex;justify-content:space-between;gap:10px;
          margin-bottom:20px;width:100%;
        }
        .category-block{
          flex:1;display:flex;flex-direction:column;align-items:center;gap:4px;
          background:var(--bg-card);padding:10px 5px;
          border-radius:var(--radius-card);border:1px solid var(--border-card);
          cursor:pointer;transition:.15s ease-in-out;
        }
        .category-block span:first-child{font-size:26px;}
        .category-block span:last-child{font-size:13px;font-weight:700;}
        .category-block.active-category{
          border-color:var(--accent-blue);
          box-shadow:0 4px 20px #0044ff;
          background:linear-gradient(145deg,#2a2a2a,rgba(34,34,170,.12));
        }
        .upgrade-content{display:flex;flex-direction:column;gap:10px;}
        .upgrade-item{
          display:flex;justify-content:space-between;align-items:center;
          background:var(--bg-card);padding:12px 14px;
          border-radius:var(--radius-card);border:1px solid var(--border-card);
          cursor:pointer;transition:.12s ease-in-out;
          animation:animateIn .4s forwards ease-out;opacity:0;
        }
        .upgrade-item:nth-child(2){animation-delay:.15s;}
        .upgrade-item:nth-child(3){animation-delay:.3s;}
        @keyframes animateIn{
          0%{opacity:0;transform:translateY(8px);}
          100%{opacity:1;transform:translateY(0);}
        }
        .upgrade-item:active{transform:translateY(2px);}
        .donate-item-left{display:flex;align-items:center;gap:10px;}
        .donate-emoji{font-size:28px;}
        .donate-info{display:flex;flex-direction:column;gap:2px;}
        .donate-name{font-size:15px;font-weight:700;color:#fff;}
        .donate-desc{font-size:12px;color:var(--text-secondary);}
        .upgrade-right{display:flex;align-items:center;gap:8px;}
        .upgrade-price{
          display:flex;align-items:center;gap:4px;
          padding:4px 8px;border-radius:20px;
        }
        .upgrade-price span{font-size:18px;font-weight:800;color:#fff;}
        .upgrade-count{
          color:#fff;font-size:15px;font-weight:800;
          padding:4px 8px;border-radius:20px;min-width:32px;text-align:center;
        }
        .price-icon{width:22px;height:22px;}

        /* ================= VIEW 3: DONATE ================= */
        .donate-column{display:flex;flex-direction:column;gap:10px;margin-top:8px;}
        .donate-item{
          display:flex;justify-content:space-between;align-items:center;
          background:var(--bg-card);padding:14px;border-radius:var(--radius-card);
          border:1px solid var(--border-card);cursor:pointer;transition:.1s ease-in-out;
        }
        .donate-price{display:flex;align-items:center;gap:6px;}
        .price-value{font-size:22px;font-weight:800;color:var(--accent-gold);}
        .price-currency{font-size:14px;color:var(--text-secondary);}
        .red_green{
          width:14px;height:14px;border-radius:50%;
          background-color:var(--error);flex-shrink:0;
          transition:background-color .3s;
        }

        /* ================= VIEW 4: RATING / LEADERBOARD ================= */
        .rating-view{padding:16px;}
        .rating-tabs{
          display:flex;gap:8px;margin-bottom:16px;
        }
        .rating-tab{
          flex:1;padding:10px;text-align:center;
          background:var(--bg-card);border-radius:var(--radius-card);
          border:1px solid var(--border-card);
          cursor:pointer;font-weight:700;font-size:13px;
          transition:.15s;
        }
        .rating-tab.active-tab{
          border-color:var(--accent-blue);
          box-shadow:0 3px 15px rgba(0,68,255,.4);
          background:linear-gradient(145deg,#2a2a2a,rgba(34,34,170,.12));
        }
        .stats-section{width:100%;}
        .stats-title{font-size:16px;font-weight:700;margin-bottom:12px;text-align:center;}
        .stats-title h2{
          display:flex;justify-content:center;align-items:center;gap:8px;
          font-size:20px;
        }
        .stats-title .total-users{
          font-size:13px;color:var(--text-secondary);font-weight:600;
          display:block;margin-top:4px;
        }
        .stats-list{
          display:flex;flex-direction:column;gap:6px;
          padding-bottom:20px;
        }
        .stats-item{
          display:flex;align-items:center;gap:10px;
          padding:10px 12px;background:var(--bg-card);
          border-radius:12px;border:1px solid var(--border-card);
          transition:.15s;
        }
        .stats-item:nth-child(-n+3){
          border:1px solid rgba(255,215,0,.25);
          background:linear-gradient(135deg,rgba(42,42,42,1),rgba(97,17,203,.08));
        }
        .stats-rank{
          width:28px;font-weight:900;font-size:16px;
          color:var(--accent-blue);text-align:center;flex-shrink:0;
        }
        .stats-item:nth-child(1) .stats-rank{color:var(--accent-gold);font-size:20px;}
        .stats-item:nth-child(2) .stats-rank{color:#c0c0c0;font-size:18px;}
        .stats-item:nth-child(3) .stats-rank{color:#cd7f32;font-size:18px;}
        .stats-avatar{
          width:34px;height:34px;border-radius:50%;
          background:linear-gradient(135deg,#6111cb,#2575fc);
          display:flex;align-items:center;justify-content:center;
          font-size:13px;font-weight:800;color:#fff;flex-shrink:0;
        }
        .stats-user-info{flex:1;min-width:0;}
        .stats-user{font-weight:700;font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
        .stats-user-level{font-size:11px;color:var(--text-secondary);font-weight:600;}
        .stats-value{text-align:right;flex-shrink:0;}
        .stats-clicks{font-weight:800;font-size:15px;color:#fff;}
        .stats-sublabel{font-size:10px;color:var(--text-secondary);font-weight:600;}
        .current-user-highlight{
          border:1px solid rgba(0,94,255,.5) !important;
          background:linear-gradient(135deg,rgba(0,94,255,.1),rgba(97,17,203,.1)) !important;
        }

        /* User rating card */
        .user-rating-card{
          background:var(--bg-card);border-radius:var(--radius-card);
          border:1px solid var(--border-card);padding:16px;
          margin-bottom:16px;text-align:center;
        }
        .user-rating-card .rating-big{
          font-size:48px;font-weight:900;color:var(--accent-gold);
          line-height:1;
        }
        .user-rating-card .rating-stars{
          font-size:28px;margin:6px 0;letter-spacing:4px;
        }
        .user-rating-card .rating-count{
          font-size:12px;color:var(--text-secondary);font-weight:600;
        }
        .rate-btn{
          margin-top:10px;padding:8px 20px;border:none;
          background:var(--gradient-main);color:#fff;
          border-radius:var(--radius-pill);font-weight:700;
          font-size:14px;cursor:pointer;font-family:var(--font);
          transition:.15s;
        }
        .rate-btn:active{transform:scale(.96);opacity:.85;}

        /* Rate modal */
        .rate-modal-overlay{
          position:fixed;top:0;left:0;width:100%;height:100%;
          background:rgba(0,0,0,.75);display:flex;
          align-items:center;justify-content:center;z-index:9999;
          opacity:0;pointer-events:none;transition:opacity .25s;
        }
        .rate-modal-overlay.visible{opacity:1;pointer-events:auto;}
        .rate-modal{
          background:var(--bg-panel);border-radius:20px;
          padding:24px;max-width:320px;width:90%;text-align:center;
          border:1px solid var(--border-card);
          transform:scale(.9);transition:transform .25s;
        }
        .rate-modal-overlay.visible .rate-modal{transform:scale(1);}
        .rate-modal h3{font-size:18px;margin-bottom:12px;font-weight:800;}
        .rate-modal .star-select{
          display:flex;justify-content:center;gap:8px;margin:12px 0;
        }
        .rate-modal .star-select span{
          font-size:36px;cursor:pointer;opacity:.35;
          transition:.15s;filter:grayscale(1);
        }
        .rate-modal .star-select span.selected{opacity:1;filter:grayscale(0);transform:scale(1.15);}
        .rate-modal .star-select span:hover{opacity:.7;filter:grayscale(0);}
        .rate-modal textarea{
          width:100%;height:60px;border-radius:10px;border:1px solid var(--border-card);
          background:var(--bg-card);color:#fff;padding:10px;font-size:14px;
          font-family:var(--font);resize:none;outline:none;
        }
        .rate-modal textarea:focus{border-color:var(--accent-blue);}
        .rate-modal-btns{display:flex;gap:8px;margin-top:14px;}
        .rate-modal-btns button{
          flex:1;padding:10px;border:none;border-radius:12px;
          font-weight:700;font-size:14px;cursor:pointer;
          font-family:var(--font);transition:.12s;
        }
        .rate-modal-btns .cancel-btn{background:var(--bg-card);color:#fff;}
        .rate-modal-btns .submit-btn{background:var(--gradient-main);color:#fff;}
        .rate-modal-btns button:active{transform:scale(.96);}

        /* ================= VIEW 5: PROMOS ================= */
        .promos-container{
          display:flex;flex-direction:column;gap:10px;
          max-width:500px;margin:0 auto;width:100%;padding:10px 0;
        }
        .promo-card{background:#2a2a3a;border-radius:var(--radius-card);padding:14px;}
        .promo-card h2{font-size:16px;margin-bottom:8px;font-weight:800;}
        .promo-content{display:flex;align-items:flex-end;gap:10px;}
        .promo-info{flex:0 0 60%;padding-bottom:8px;}
        .promo-buy-btn{
          background:#fff;border:none;border-radius:var(--radius-pill);
          padding:12px;color:#1a1a2e;font-weight:800;font-size:14px;
          cursor:pointer;width:100%;font-family:var(--font);transition:.12s;
        }
        .promo-buy-btn:active{opacity:.8;transform:scale(.97);}
        .promo-image{
          flex:0 0 38%;display:flex;align-items:flex-end;
          justify-content:center;font-size:64px;
        }

        /* ================= FOOTER ================= */
        .for_footer{
          background:#21212a;text-align:center;width:100%;
          flex-shrink:0;
        }
        footer{
          background-color:var(--bg-footer);color:#eee;
          display:flex;padding:6px 4px;align-items:center;
          justify-content:space-around;width:100%;
        }
        footer a{
          padding:5px 3px;position:relative;color:#fff;
          display:flex;flex-direction:column;align-items:center;
          min-width:52px;cursor:pointer;isolation:isolate;gap:2px;
          border-radius:12px;transition:.15s;
        }
        footer a .nav-icon{font-size:22px;line-height:1;}
        footer a h4{font-size:10px;font-weight:600;margin:0;white-space:nowrap;}
        footer a.active::before{
          content:"";position:absolute;inset:0;
          background-image:var(--gradient-main);
          z-index:-1;border-radius:12px;opacity:.3;
        }

        /* ================= NOTIFICATION ================= */
        .game-notification{
          position:fixed;top:50px;left:50%;transform:translateX(-50%);
          padding:10px 22px;border-radius:var(--radius-pill);
          font-weight:700;font-size:14px;z-index:9000;
          animation:notifFade 2s forwards;pointer-events:none;
          font-family:var(--font);white-space:nowrap;
        }
        @keyframes notifFade{
          0%{opacity:1;transform:translateX(-50%) translateY(0);}
          70%{opacity:1;}
          100%{opacity:0;transform:translateX(-50%) translateY(-20px);}
        }

        /* ================= FLOAT TEXT ================= */
        @keyframes floatUp{
          0%{opacity:1;transform:translateY(0);}
          100%{opacity:0;transform:translateY(-100px);}
        }
        @keyframes coinFloat{
          0%{opacity:1;transform:translateY(0);}
          100%{opacity:0;transform:translateY(-50px);}
        }

        /* ================= BUBBLE ================= */
        .bubble{
          position:absolute;border-radius:50%;
          background:rgba(97,17,203,.7);
          box-shadow:0 0 20px rgba(97,17,203,.6);
          cursor:pointer;z-index:999;
          display:flex;align-items:center;justify-content:center;
          color:#fff;font-weight:800;font-size:14px;
          text-shadow:0 0 5px #000;
          animation:bubbleRise linear;pointer-events:auto;
          border:2px solid rgba(255,255,255,.4);
          transition:transform .1s;will-change:transform;
        }
        .bubble:hover{transform:scale(1.1);background:rgba(97,17,203,.9);}
        .bubble:active{transform:scale(.9);}
        @keyframes bubbleRise{
          0%{transform:translateY(0);opacity:1;}
          100%{transform:translateY(-350px);opacity:0;}
        }

        /* ================= RESPONSIVE ================= */
        @media (max-height:650px){
          .crystal-emoji{font-size:100px;}
          #sticker_container{width:140px;height:140px;}
          .main-counter,.main-counter2{font-size:26px;}
          .stat-value{font-size:17px;}
        }
        @media (max-height:550px){
          .crystal-emoji{font-size:80px;}
          #sticker_container{width:110px;height:110px;margin-bottom:8px;}
          .stats-row{margin-bottom:6px;gap:5px;}
          .stat-block{padding:4px 3px;}
          .stat-label{font-size:8px;}
          .stat-value{font-size:15px;}
          .main-counter,.main-counter2{font-size:22px;}
          .progress-bar{height:10px;}
        }

        /* ================= SORT DROPDOWN ================= */
        .sort-selector{
          display:flex;align-items:center;justify-content:center;
          gap:6px;margin-bottom:14px;
        }
        .sort-selector label{font-size:12px;color:var(--text-secondary);font-weight:700;}
        .sort-selector select{
          background:var(--bg-card);color:#fff;border:1px solid var(--border-card);
          border-radius:10px;padding:6px 10px;font-size:13px;
          font-family:var(--font);font-weight:700;outline:none;
          cursor:pointer;
        }

        /* ================= LOADING SKELETON ================= */
        .skeleton{
          background:linear-gradient(90deg,var(--bg-card) 25%,#353535 50%,var(--bg-card) 75%);
          background-size:200% 100%;
          animation:shimmer 1.5s infinite;
          border-radius:12px;
        }
        @keyframes shimmer{
          0%{background-position:200% 0;}
          100%{background-position:-200% 0;}
        }
        .skeleton-item{
          height:52px;margin-bottom:6px;border-radius:12px;
        }
    </style>
</head>
<body>
<div class="all" id="gameRoot">

    <!-- НАВ -->
    <div class="for_nav">
        <nav id="nav_user">
            <div class="user-info">
                <div style="width: 45px; height: 45px;" class="user-avatar" id="userAvatar"></div>
                <div class="user-name" id="userName">Загрузка...</div>
            </div>
            <div class="users_stars_div">
                <div class="user-stars" id="userStars">0</div>
                <div class="starsss_img"><i class="fa-solid fa-star"></i></div>
            </div>
        </nav>
    </div>

    <!-- МОДАЛЬНЫЕ ОКНА -->
    <div class="models-container">

        <!-- ===== VIEW 1: ГЛАВНАЯ ===== -->
        <div id="model_view_1" class="model-view active-view" data-view="1">
            <div class="model-content">
                <div class="stats-row">
                    <div class="stat-block">
                        <div style="font-size: 15px;" class="stat-label">За 1 клик</div>
                        <div class="stat-value">
                            <div style="width: 30px;" class="imgs"><img src="/static/imgs/users_api/monetka.svg" alt=""></div>
                            <span style="font-size: 17px;" id="user_upgrade">1</span>
                        </div>
                    </div>
                    <div class="stat-block">
                        <div style="font-size: 15px ;" class="stat-label">Необходимо</div>
                        <div class="stat-value">
                            <span style="font-size: 25px;" id="required-for-level">150</span>
                        </div>
                    </div>
                    <div class="stat-block">
                        <div style="font-size: 15px;" class="stat-label">Монет в сек.</div>
                        <div class="stat-value">
                            <div style="width: 30px;" class="imgs"><img src="/static/imgs/users_api/monetka.svg" alt=""></div>
                            <span style="font-size: 17px;" id="user_upgrade_sek">0</span>
                        </div>
                    </div>
                </div>

                <div class="main-image-container">
                    <div style="width: 60px;" class="imgs"><img src="/static/imgs/users_api/monetka.svg" alt=""></div>
                    <div id="user_content_coin_lol" class="main-counter">0</div>
                </div>

                <div class="progress-container">
                    <div class="progress-info">
                        <span><span id="level">1</span>/10</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" id="progress-fill"></div>
                    </div>
                </div>

                <div class="action-buttons">
                    <div class="action-btn left-btn" id="ads-btn">📹</div>
                </div>

                <div class="bottom-section">
                    <div class="tapalka">
                        <div id="sticker_container" style="width:180px;height:180px;cursor:pointer;"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- ===== VIEW 2: УЛУЧШЕНИЯ ===== -->
        <div id="model_view_2" class="model-view" data-view="2">
            <div class="model-content">
                <div class="main-image-container">
                    <div style="width: 45px;" class="imgs"><img src="/static/imgs/users_api/monetka.svg" alt=""></div>
                    <div id="user_content_coin_lol_for_2" class="main-counter2">0</div>
                </div>
                <div class="donate-title"><p>Улучшай, Апгрейди, Покупай</p></div>

                <div class="upgrade-categories">
                    <div class="category-block active-category" data-category="click">
                        <span>👆</span><span>Клик</span>
                    </div>
                    <div class="category-block" data-category="farm">
                        <span>🌾</span><span>Ферма</span>
                    </div>
                    <div class="category-block" data-category="bonus">
                        <span>🎁</span><span>Бонус</span>
                    </div>
                </div>

                <!-- КЛИК -->
                <div class="upgrade-content category-click" id="cat-click">
                    <div class="upgrade-item" data-upg="click:power1">
                        <div class="donate-item-left"><span class="donate-emoji">👆</span>
                            <div class="donate-info"><span class="donate-name">Усиленный клик</span><span class="donate-desc">+1 за клик</span></div>
                        </div>
                        <div class="upgrade-right">
                            <div class="upgrade-price"><svg class="price-icon" viewBox="0 0 36 36"><circle cx="18" cy="18" r="16" fill="#ffd700" stroke="#e6ac00" stroke-width="2"/><text x="18" y="23" text-anchor="middle" font-size="16" font-weight="900" fill="#b8860b">$</text></svg><span id="price_1">100</span></div>
                            <div class="upgrade-count">0</div>
                        </div>
                    </div>
                    <div class="upgrade-item" data-upg="click:power2">
                        <div class="donate-item-left"><span class="donate-emoji">⚡</span>
                            <div class="donate-info"><span class="donate-name">Супер клик</span><span class="donate-desc">+3 за клик</span></div>
                        </div>
                        <div class="upgrade-right">
                            <div class="upgrade-price"><svg class="price-icon" viewBox="0 0 36 36"><circle cx="18" cy="18" r="16" fill="#ffd700" stroke="#e6ac00" stroke-width="2"/><text x="18" y="23" text-anchor="middle" font-size="16" font-weight="900" fill="#b8860b">$</text></svg><span id="price_2">500</span></div>
                            <div class="upgrade-count">0</div>
                        </div>
                    </div>
                    <div class="upgrade-item" data-upg="click:power3">
                        <div class="donate-item-left"><span class="donate-emoji">💥</span>
                            <div class="donate-info"><span class="donate-name">Мега клик</span><span class="donate-desc">+5 за клик</span></div>
                        </div>
                        <div class="upgrade-right">
                            <div class="upgrade-price"><svg class="price-icon" viewBox="0 0 36 36"><circle cx="18" cy="18" r="16" fill="#ffd700" stroke="#e6ac00" stroke-width="2"/><text x="18" y="23" text-anchor="middle" font-size="16" font-weight="900" fill="#b8860b">$</text></svg><span id="price_3">1000</span></div>
                            <div class="upgrade-count">0</div>
                        </div>
                    </div>
                </div>

                <!-- ФЕРМА -->
                <div class="upgrade-content category-farm" id="cat-farm" style="display:none;">
                    <div class="upgrade-item" data-upg="farm:worker">
                        <div class="donate-item-left"><span class="donate-emoji">👨‍🌾</span>
                            <div class="donate-info"><span class="donate-name">Рабочий</span><span class="donate-desc">+1 монета/сек</span></div>
                        </div>
                        <div class="upgrade-right">
                            <div class="upgrade-price"><svg class="price-icon" viewBox="0 0 36 36"><circle cx="18" cy="18" r="16" fill="#ffd700" stroke="#e6ac00" stroke-width="2"/><text x="18" y="23" text-anchor="middle" font-size="16" font-weight="900" fill="#b8860b">$</text></svg><span id="price_2_1">200</span></div>
                            <div class="upgrade-count">0</div>
                        </div>
                    </div>
                    <div class="upgrade-item" data-upg="farm:farmer">
                        <div class="donate-item-left"><span class="donate-emoji">🚜</span>
                            <div class="donate-info"><span class="donate-name">Фермер</span><span class="donate-desc">+3 монеты/сек</span></div>
                        </div>
                        <div class="upgrade-right">
                            <div class="upgrade-price"><svg class="price-icon" viewBox="0 0 36 36"><circle cx="18" cy="18" r="16" fill="#ffd700" stroke="#e6ac00" stroke-width="2"/><text x="18" y="23" text-anchor="middle" font-size="16" font-weight="900" fill="#b8860b">$</text></svg><span id="price_2_2">800</span></div>
                            <div class="upgrade-count">0</div>
                        </div>
                    </div>
                    <div class="upgrade-item" data-upg="farm:harvester">
                        <div class="donate-item-left"><span class="donate-emoji">🌽</span>
                            <div class="donate-info"><span class="donate-name">Комбайн</span><span class="donate-desc">+5 монет/сек</span></div>
                        </div>
                        <div class="upgrade-right">
                            <div class="upgrade-price"><svg class="price-icon" viewBox="0 0 36 36"><circle cx="18" cy="18" r="16" fill="#ffd700" stroke="#e6ac00" stroke-width="2"/><text x="18" y="23" text-anchor="middle" font-size="16" font-weight="900" fill="#b8860b">$</text></svg><span id="price_2_3">2000</span></div>
                            <div class="upgrade-count">0</div>
                        </div>
                    </div>
                </div>

                <!-- БОНУС -->
                <div class="upgrade-content category-bonus" id="cat-bonus" style="display:none;">
                    <div class="upgrade-item" data-upg="bonus:luck">
                        <div class="donate-item-left"><span class="donate-emoji">🍀</span>
                            <div class="donate-info"><span class="donate-name">Удача</span><span class="donate-desc">Шанс +1.05x к бонусу</span></div>
                        </div>
                        <div class="upgrade-right">
                            <div class="upgrade-price"><svg class="price-icon" viewBox="0 0 36 36"><circle cx="18" cy="18" r="16" fill="#ffd700" stroke="#e6ac00" stroke-width="2"/><text x="18" y="23" text-anchor="middle" font-size="16" font-weight="900" fill="#b8860b">$</text></svg><span id="price3_1">300</span></div>
                            <div class="upgrade-count">0</div>
                        </div>
                    </div>
                    <div class="upgrade-item" data-upg="bonus:crit">
                        <div class="donate-item-left"><span class="donate-emoji">⚡</span>
                            <div class="donate-info"><span class="donate-name">Критический удар</span><span class="donate-desc">Шанс x5 к награде</span></div>
                        </div>
                        <div class="upgrade-right">
                            <div class="upgrade-price"><svg class="price-icon" viewBox="0 0 36 36"><circle cx="18" cy="18" r="16" fill="#ffd700" stroke="#e6ac00" stroke-width="2"/><text x="18" y="23" text-anchor="middle" font-size="16" font-weight="900" fill="#b8860b">$</text></svg><span id="price_3_2">1500</span></div>
                            <div class="upgrade-count">0</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- ===== VIEW 3: ДОНАТ ===== -->
        <div id="model_view_3" class="model-view" data-view="3">
            <div class="model-content">
                <div class="main-image-container">
                    <div style="width: 45px;" class="imgs"><img src="/static/imgs/users_api/monetka.svg" alt=""></div>
                    <div id="user_content_coin_lol_for_3" class="main-counter2">0</div>
                </div>
                <div class="donate-title"><p>Поддержи проект и получи бонусы</p></div>
                <div class="donate-column">
                    <div class="donate-item" id="donate-x2">
                        <div class="donate-item-left"><span class="donate-emoji">⚡</span>
                            <div class="donate-info"><span class="donate-name">X2 монет навсегда</span><span class="donate-desc">Удвой доход от всех кликов</span></div>
                        </div>
                        <div class="donate-price">
                            <span class="price-value">15</span><span class="price-currency">⭐</span>
                            <div class="red_green"></div>
                        </div>
                    </div>
                    <div class="donate-item" id="donate-plus100k">
                        <div class="donate-item-left"><span class="donate-emoji">💰</span>
                            <div class="donate-info"><span class="donate-name">+100 000 монет</span><span class="donate-desc">Мгновенное пополнение баланса</span></div>
                        </div>
                        <div class="donate-price">
                            <span class="price-value">20</span><span class="price-currency">⭐</span>
                            <div class="red_green"></div>
                        </div>
                    </div>
                    <div class="donate-item" id="donate-x2sek">
                        <div class="donate-item-left"><span class="donate-emoji">⏱️</span>
                            <div class="donate-info"><span class="donate-name">X2 монет в секунду</span><span class="donate-desc">Удвой пассивный доход</span></div>
                        </div>
                        <div class="donate-price">
                            <span class="price-value">25</span><span class="price-currency">⭐</span>
                            <div class="red_green"></div>
                        </div>
                    </div>
                    <div class="donate-item" id="donate-superclick">
                        <div class="donate-item-left"><span class="donate-emoji">👆</span>
                            <div class="donate-info"><span class="donate-name">Супер-клик навсегда</span><span class="donate-desc">+5 к силе клика</span></div>
                        </div>
                        <div class="donate-price">
                            <span class="price-value">30</span><span class="price-currency">⭐</span>
                            <div class="red_green"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- ===== VIEW 4: РЕЙТИНГ ===== -->
        <div id="model_view_4" class="model-view" data-view="4">
            <div class="model-content rating-view">
                <div class="stats-section">
                    <div class="stats-title">
                        <h2>🏆 Рейтинг игроков</h2>
                        <span class="total-users" id="totalUsers"></span>
                    </div>

                    <!-- Табы сортировки -->
                    <div class="rating-tabs">
                        <div class="rating-tab active-tab" data-sort="balance">💰 Монеты</div>
                        <div class="rating-tab" data-sort="level">⭐ Уровень</div>
                        <div class="rating-tab" data-sort="rating">❤️ Рейтинг</div>
                    </div>

                    <!-- Карточка рейтинга текущего пользователя -->
                    <div class="user-rating-card" id="myRatingCard">
                        <div style="font-size:13px;font-weight:700;color:var(--text-secondary);margin-bottom:6px;">Мой рейтинг</div>
                        <div class="rating-big" id="myRatingValue">0.0</div>
                        <div class="rating-stars" id="myRatingStars">☆☆☆☆☆</div>
                        <div class="rating-count" id="myRatingCount">0 оценок</div>
                    </div>

                    <!-- Список лидеров -->
                    <div class="stats-list" id="statsList">
                        <div class="skeleton skeleton-item"></div>
                        <div class="skeleton skeleton-item"></div>
                        <div class="skeleton skeleton-item"></div>
                        <div class="skeleton skeleton-item"></div>
                        <div class="skeleton skeleton-item"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- ===== VIEW 5: ПРОМОКОДЫ ===== -->
        <div id="model_view_5" class="model-view" data-view="5">
            <div class="model-content">
                <div class="promos-container">
                    <div class="promo-card">
                        <h2>Промокод на еду:</h2>
                        <div class="promo-content">
                            <div class="promo-info"><button class="promo-buy-btn" data-price="5000000">Купить за 5M</button></div>
                            <div class="promo-image"><img src="/static/imgs/for_model5/xgV6wg8mPlnCva3A 1.svg" alt=""></div>
                        </div>
                    </div>
                    <div class="promo-card">
                        <h2>Промокод на одежду:</h2>
                        <div class="promo-content">
                            <div class="promo-info"><button class="promo-buy-btn" data-price="10000000">Купить за 10M</button></div>
                            <div class="promo-image"><img src="/static/imgs/for_model5/F3G7qPk-zTwD-qMI 1.svg" alt=""></div>
                        </div>
                    </div>
                    <div class="promo-card">
                        <h2>Промокод на книги:</h2>
                        <div class="promo-content">
                            <div class="promo-info"><button class="promo-buy-btn" data-price="15000000">Купить за 15M</button></div>
                            <div class="promo-image"><img src="/static/imgs/for_model5/qmkOKVxBws0JRoBV 1.svg" alt=""></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- ФУТЕР -->
    <div class="for_footer">
        <footer id="footer">
            <a href="#" class="active" data-view="1">
                <span class="nav-icon"><img src="/static/imgs/for_fyter/dollar.png" alt=""></span>
                <h4>Главная</h4>
            </a>
            <a href="#" data-view="2">
                <span class="nav-icon"><img src="/static/imgs/for_fyter/pickaxe.png" alt=""></span>
                <h4>Улучшения</h4>
            </a>
            <a href="#" data-view="3">
                <span class="nav-icon"><img src="/static/imgs/for_fyter/money.png" alt=""></span>
                <h4>Донат</h4>
            </a>
            <a href="#" data-view="4">
                <span class="nav-icon"><img src="/static/imgs/for_fyter/top_lider.png" alt=""></span>
                <h4>Рейтинг</h4>
            </a>
            <a href="#" data-view="5">
                <span class="nav-icon"><img src="/static/imgs/for_fyter/Gift.png" alt=""></span>
                <h4>Промокоды</h4>
            </a>
        </footer>
    </div>
</div>

<!-- ===== МОДАЛКА ОЦЕНКИ ===== -->
<div class="rate-modal-overlay" id="rateModalOverlay">
    <div class="rate-modal">
        <h3 id="rateModalTitle">Оценить игрока</h3>
        <div class="star-select" id="starSelect">
            <span data-star="1">⭐</span>
            <span data-star="2">⭐</span>
            <span data-star="3">⭐</span>
            <span data-star="4">⭐</span>
            <span data-star="5">⭐</span>
        </div>
        <textarea id="rateComment" placeholder="Комментарий (необязательно)"></textarea>
        <div class="rate-modal-btns">
            <button class="cancel-btn" id="rateCancelBtn">Отмена</button>
            <button class="submit-btn" id="rateSubmitBtn">Отправить</button>
        </div>
    </div>
</div>

<script>
const API_BASE = '/api';

const userData = {
    telegram_id: 0,
    username: 'Игрок',
    balance: 0,
    stars: 0,
    level: 1,
    clickPower: 1,
    passiveIncome: 0,
    progress: 0,
    totalClicks: 0,
    totalEarned: 0,
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
    },
    myRating: { avg: 0, count: 0 }
};

let mySticker = null;
let currentStickerLevel = 1;

const levelConfig = {
    base: 150,
    multi: 3,
    get(lvl) { return this.base * Math.pow(this.multi, lvl - 1); }
};

function getPrice(base, count) {
    return Math.floor(base * Math.pow(1.5, count));
}

function format(n) {
    if (n >= 1e9) return (n / 1e9).toFixed(1) + 'B';
    if (n >= 1e6) return (n / 1e6).toFixed(1) + 'M';
    if (n >= 1e3) return (n / 1e3).toFixed(1) + 'K';
    return String(n);
}

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

    const avatarEl = el('userAvatar');
    avatarEl.textContent = userData.username.charAt(0).toUpperCase();

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
    for (let i = 1; i <= 5; i++) {
        stars += i <= Math.round(userData.myRating.avg) ? '★' : '☆';
    }
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
        if (dot) {
            dot.style.backgroundColor = (item.key && userData.donors[item.key]) ? '#4CAF50' : '#f44336';
        }
    });
}

function handleClick(e) {
    let earned = userData.clickPower;

    const critChance = Math.min(userData.bonusUpgrades.crit.count * 0.05, 0.3);
    if (critChance > 0 && Math.random() < critChance) {
        earned *= 5;
        showNotification('КРИТИЧЕСКИЙ УДАР! x5', true);
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
    f.style.cssText =
        'position:fixed;left:' + (e.clientX || 200) + 'px;top:' + (e.clientY || 400) + 'px;color:#ffd700;font-size:26px;' +
        'font-weight:900;text-shadow:0 0 15px #ff9900;pointer-events:none;' +
        'z-index:1000;animation:floatUp 1s ease-out forwards;';
    document.body.appendChild(f);
    setTimeout(() => f.remove(), 1000);
}

function checkLevel() {
    let need = levelConfig.get(userData.level);
    while (userData.progress >= need && userData.level < 10) {
        userData.progress -= need;
        userData.level++;
        userData.clickPower++;
        const bonus = 50 * userData.level;
        userData.balance += bonus;
        need = levelConfig.get(userData.level);
        showNotification('УРОВЕНЬ ' + userData.level + '! +' + bonus + ' монет', true);
    }
}

function loadSticker(level) {
    const container = document.getElementById('sticker_container');
    if (!container) return;
    
    let path = '/static/imgs/for_img_crystal/AnimatedSticker.json';
    if (level == 1) path = '/static/imgs/for_img_crystal/AnimatedSticker2.json';
    else if (level == 2) path = '/static/imgs/for_img_crystal/AnimatedSticker.json';
    else if (level == 3) path = '/static/imgs/for_img_crystal/AnimatedSticker3.json';
    
    if (mySticker) {
        mySticker.destroy();
        mySticker = null;
    }
    
    mySticker = lottie.loadAnimation({
        container: container,
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
        userData.clickPower = 1 
            + userData.clickUpgrades.power1.count * 1
            + userData.clickUpgrades.power2.count * 3 
            + userData.clickUpgrades.power3.count * 5;
        showNotification('+' + upg.power + ' к клику!', true);
    } else if (type === 'farm') {
        upg = userData.farmUpgrades[key];
        price = getPrice(upg.base, upg.count);
        if (userData.balance < price) { showNotification('Недостаточно монет!', false); return; }
        userData.balance -= price;
        upg.count++;
        userData.passiveIncome = 0
            + userData.farmUpgrades.worker.count * 1
            + userData.farmUpgrades.farmer.count * 3
            + userData.farmUpgrades.harvester.count * 5;
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
        const el = document.getElementById(id);
        if (!el) return;
        el.addEventListener('click', () => {
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
    const payload = {
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
    };

    fetch(API_BASE + '/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
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
        const target = document.querySelector('.model-view[data-view="' + view + '"]');
        if (target) target.classList.add('active-view');
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
    const listEl = document.getElementById('statsList');
    listEl.innerHTML = '<div class="skeleton skeleton-item"></div><div class="skeleton skeleton-item"></div><div class="skeleton skeleton-item"></div>';

    fetch(API_BASE + '/leaderboard?sort=' + currentSort + '&limit=50')
        .then(r => r.json())
        .then(data => {
            if (data.ok) {
                leaderboardData = data.leaderboard;
                document.getElementById('totalUsers').textContent = 'Всего игроков: ' + data.total_users;
                renderLeaderboard();
            }
        })
        .catch(() => {
            listEl.innerHTML = '<div style="text-align:center;padding:20px;">Ошибка загрузки</div>';
        });
}

function renderLeaderboard() {
    const listEl = document.getElementById('statsList');
    if (!leaderboardData.length) {
        listEl.innerHTML = '<div style="text-align:center;padding:20px;">Нет данных</div>';
        return;
    }

    let html = '';
    leaderboardData.forEach(player => {
        const isMe = player.telegram_id === userData.telegram_id;
        const initial = player.username.charAt(0).toUpperCase();
        let valueNum = '';
        if (currentSort === 'balance') valueNum = format(player.balance) + ' монет';
        else if (currentSort === 'level') valueNum = 'Ур. ' + player.level;
        else if (currentSort === 'rating') valueNum = player.avg_rating.toFixed(1) + ' ★';

        html += '<div class="stats-item' + (isMe ? ' current-user-highlight' : '') + '" data-tid="' + player.telegram_id + '" data-name="' + player.username + '">';
        html += '<div class="stats-rank">' + player.rank + '</div>';
        html += '<div class="stats-avatar">' + initial + '</div>';
        html += '<div class="stats-user-info"><div class="stats-user">' + player.username + (isMe ? ' (Вы)' : '') + '</div>';
        html += '<div class="stats-user-level">Уровень ' + player.level + '</div></div>';
        html += '<div class="stats-value"><div class="stats-clicks">' + valueNum + '</div></div></div>';
    });

    listEl.innerHTML = html;

    listEl.querySelectorAll('.stats-item').forEach(item => {
        item.addEventListener('click', () => {
            const tid = parseInt(item.getAttribute('data-tid'));
            const name = item.getAttribute('data-name');
            if (tid === userData.telegram_id) {
                showNotification('Нельзя оценить себя!', false);
                return;
            }
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
            const sv = parseInt(s.getAttribute('data-star'));
            if (sv <= selectedStarScore) s.classList.add('selected');
            else s.classList.remove('selected');
        });
    });
});

document.getElementById('rateCancelBtn').addEventListener('click', closeRateModal);
document.getElementById('rateModalOverlay').addEventListener('click', (e) => {
    if (e.target === e.currentTarget) closeRateModal();
});

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
const boughtPromos = [false, false, false];
document.querySelectorAll('.promo-buy-btn').forEach((btn, i) => {
    btn.addEventListener('click', () => {
        if (boughtPromos[i]) { showNotification('Промокод уже куплен!', false); return; }
        const price = parseInt(btn.getAttribute('data-price'));
        if (userData.balance < price) { showNotification('Недостаточно монет!', false); return; }
        userData.balance -= price;
        boughtPromos[i] = true;
        
        let code = '';
        const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
        for (let c = 0; c < 8; c++) code += chars[Math.floor(Math.random() * chars.length)];
        
        const card = btn.closest('.promo-card');
        const promoDiv = document.createElement('div');
        promoDiv.textContent = 'Промокод: ' + code;
        promoDiv.style.cssText = 'background:#2a2a2a;color:#ffd700;padding:10px;border-radius:10px;margin-top:10px;';
        card.appendChild(promoDiv);
        btn.textContent = 'Куплено ✓';
        btn.disabled = true;
        btn.style.opacity = '0.5';
        updateUI();
        syncToServer();
    });
});

// Пузырьки
let bubbleActive = false;
function startBubbles() {
    scheduleNextBubble();
}

function scheduleNextBubble() {
    const delay = Math.random() * 15000 + 3000;
    setTimeout(() => {
        if (!bubbleActive) createBubble();
        scheduleNextBubble();
    }, delay);
}

function createBubble() {
    const container = document.getElementById('gameRoot');
    if (!container) return;
    const rect = container.getBoundingClientRect();
    if (rect.width === 0) return;

    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    const size = Math.floor(Math.random() * 35) + 30;
    bubble.style.width = size + 'px';
    bubble.style.height = size + 'px';
    bubble.style.left = Math.floor(Math.random() * (rect.width - size)) + 'px';
    bubble.style.bottom = '0px';
    bubble.style.position = 'absolute';
    const dur = (Math.random() * 2 + 2).toFixed(1);
    bubble.style.animation = `bubbleRise ${dur}s linear forwards`;
    const reward = Math.floor(Math.random() * 500) + 20;
    bubble.setAttribute('data-reward', reward);
    bubble.textContent = '+' + reward;
    
    bubble.onclick = (e) => {
        e.stopPropagation();
        const r = parseInt(bubble.getAttribute('data-reward'));
        userData.balance += r;
        userData.totalEarned += r;
        
        const f = document.createElement('div');
        f.textContent = '+' + format(r);
        f.style.cssText = 'position:fixed;left:' + e.clientX + 'px;top:' + e.clientY + 'px;color:#ffd700;font-size:26px;font-weight:900;pointer-events:none;z-index:1000;animation:floatUp 1s ease-out forwards;';
        document.body.appendChild(f);
        setTimeout(() => f.remove(), 1000);
        
        showNotification('+' + r + ' монет!', true);
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
    
    if (tg) {
        tg.ready();
        tg.expand();
        
        const telegramUser = tg.initDataUnsafe?.user;
        if (telegramUser) {
            userData.telegram_id = telegramUser.id;
            userData.username = telegramUser.first_name + (telegramUser.last_name ? ' ' + telegramUser.last_name : '');
            
            fetch(API_BASE + '/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    telegram_id: userData.telegram_id,
                    username: userData.username
                })
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
                    
                    // Загружаем улучшения
                    if (data.user.click_upgrades) {
                        userData.clickUpgrades.power1.count = data.user.click_upgrades.power1 || 0;
                        userData.clickUpgrades.power2.count = data.user.click_upgrades.power2 || 0;
                        userData.clickUpgrades.power3.count = data.user.click_upgrades.power3 || 0;
                        
                        userData.clickPower = 1 
                            + userData.clickUpgrades.power1.count * 1
                            + userData.clickUpgrades.power2.count * 3 
                            + userData.clickUpgrades.power3.count * 5;
                    }
                    
                    if (data.user.farm_upgrades) {
                        userData.farmUpgrades.worker.count = data.user.farm_upgrades.worker || 0;
                        userData.farmUpgrades.farmer.count = data.user.farm_upgrades.farmer || 0;
                        userData.farmUpgrades.harvester.count = data.user.farm_upgrades.harvester || 0;
                        
                        userData.passiveIncome = 0
                            + userData.farmUpgrades.worker.count * 1
                            + userData.farmUpgrades.farmer.count * 3
                            + userData.farmUpgrades.harvester.count * 5;
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
                console.log('Сервер недоступен');
                updateUI();
                loadSticker(userData.level);
            });
        } else {
            userData.telegram_id = Math.floor(Math.random() * 900000) + 100000;
            userData.username = 'Тест_' + (userData.telegram_id % 10000);
            updateUI();
            loadSticker(1);
        }
    } else {
        userData.telegram_id = Math.floor(Math.random() * 900000) + 100000;
        userData.username = 'Дев_' + (userData.telegram_id % 10000);
        updateUI();
        loadSticker(1);
    }

    const container = document.getElementById('sticker_container');
    if (container) container.addEventListener('click', handleClick);

    const adsBtn = document.getElementById('ads-btn');
    if (adsBtn) {
        adsBtn.addEventListener('click', () => {
            const overlay = document.createElement('div');
            overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.8);display:flex;justify-content:center;align-items:center;z-index:10000;';
            const modal = document.createElement('div');
            modal.style.cssText = 'background:#1a1a1a;padding:28px;border-radius:20px;text-align:center;max-width:300px;width:90%;';
            modal.innerHTML = '<p style="margin-bottom:18px;">Получить звезду?</p><button id="getStarBtn" style="background:linear-gradient(to right,#9e00f3,#005eff);color:#fff;border:none;padding:10px 28px;border-radius:30px;">Получить ⭐</button>';
            overlay.appendChild(modal);
            document.body.appendChild(overlay);
            
            document.getElementById('getStarBtn').addEventListener('click', () => {
                userData.stars += 1;
                updateUI();
                syncToServer();
                showNotification('+1 звезда!', true);
                overlay.remove();
            });
            
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) overlay.remove();
            });
        });
    }

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
    
    // Добавляем анимации в head
    const style = document.createElement('style');
    style.textContent = '@keyframes floatUp{0%{opacity:1;transform:translateY(0);}100%{opacity:0;transform:translateY(-100px);}} @keyframes bubbleRise{0%{transform:translateY(0);opacity:1;}100%{transform:translateY(-350px);opacity:0;}}';
    document.head.appendChild(style);
});
</script>
</body>
</html>
    ''')

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({'ok': False, 'error': 'Нет данных'}), 400
    
    telegram_id = data.get('telegram_id')
    if not validate_telegram_id(telegram_id):
        return jsonify({'ok': False, 'error': 'Неверный telegram_id'}), 400
    
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
    if not data:
        return jsonify({'ok': False, 'error': 'Нет данных'}), 400
    
    telegram_id = data.get('telegram_id')
    if not validate_telegram_id(telegram_id):
        return jsonify({'ok': False, 'error': 'Неверный telegram_id'}), 400
    
    db = get_db()
    existing = db.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,)).fetchone()
    if not existing:
        return jsonify({'ok': False, 'error': 'Пользователь не найден'}), 404
    
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
    if not validate_telegram_id(telegram_id):
        return jsonify({'ok': False, 'error': 'Неверный telegram_id'}), 400
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,)).fetchone()
    if not user:
        return jsonify({'ok': False, 'error': 'Пользователь не найден'}), 404
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
    
    sort_map = {
        'balance': 'u.balance DESC',
        'total_earned': 'u.total_earned DESC',
        'level': 'u.level DESC, u.balance DESC',
        'rating': 'avg_rating DESC',
        'total_clicks': 'u.total_clicks DESC'
    }
    order = sort_map.get(sort_by, 'u.balance DESC')
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
    
    result = []
    for i, row in enumerate(rows):
        result.append({
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
    
    return jsonify({'ok': True, 'leaderboard': result, 'total_users': total})

@app.route('/api/rate', methods=['POST'])
def rate_user():
    data = request.get_json()
    if not data:
        return jsonify({'ok': False, 'error': 'Нет данных'}), 400
    
    from_user = data.get('from_user')
    to_user = data.get('to_user')
    score = data.get('score')
    comment = data.get('comment', '')[:200]
    
    if not validate_telegram_id(from_user) or not validate_telegram_id(to_user):
        return jsonify({'ok': False, 'error': 'Неверный telegram_id'}), 400
    if from_user == to_user:
        return jsonify({'ok': False, 'error': 'Нельзя оценить себя'}), 400
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
    if not validate_telegram_id(telegram_id):
        return jsonify({'ok': False, 'error': 'Неверный telegram_id'}), 400
    limit = min(int(request.args.get('limit', 20)), 50)
    offset = max(int(request.args.get('offset', 0)), 0)
    db = get_db()
    
    avg = db.execute('SELECT AVG(score) as avg_score, COUNT(*) as count FROM ratings WHERE to_user = ?', (telegram_id,)).fetchone()
    ratings = db.execute('''
        SELECT r.from_user, u.username as from_username, r.score, r.comment, r.created_at
        FROM ratings r
        JOIN users u ON u.telegram_id = r.from_user
        WHERE r.to_user = ?
        ORDER BY r.created_at DESC
        LIMIT ? OFFSET ?
    ''', (telegram_id, limit, offset)).fetchall()
    
    return jsonify({
        'ok': True,
        'avg': round(avg['avg_score'], 1) if avg['avg_score'] else 0,
        'count': avg['count'],
        'ratings': [{
            'from_user': r['from_user'],
            'from_username': r['from_username'],
            'score': r['score'],
            'comment': r['comment'],
            'created_at': r['created_at']
        } for r in ratings]
    })

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    print("=" * 50)
    print("  Кристалл-Кликер")
    print("  http://localhost:5000")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)


lottie.loadAnimation({
        container: document.getElementById('sticker'),
        renderer: 'svg',
        loop: true,
        autoplay: true,
        path: "../imgs/for_img_crystal/AnimatedSticker.json"
});



// Функция для обновления прогресса
function updateProgress(current, max = 150) {
    const progressFill = document.getElementById('progress-fill');
    const progressCount = document.getElementById('progress-count');
    
    const percent = (current / max) * 100;
    progressFill.style.width = percent + '%';
    progressCount.textContent = "Уровень" +  " " + current + '/' + 10;
}

// Пример использования:
let currentProgress = 0;
updateProgress(currentProgress); // 0/150

// При клике или действии увеличивай:
currentProgress += 1;
updateProgress(currentProgress);
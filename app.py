"""
Темы: маршруты, шаблоны, обработка форм, статические файлы
"""

from flask import Flask, render_template, request, redirect, url_for

# Создаём приложение
app = Flask(__name__)

# Главная страница
@app.route('/')
def index():
    return render_template('index.html', title='Главная')

# Пример страницы "О нас"
@app.route('/about')
def about():
    return render_template('index.html', title='О нас', content='Это учебное приложение на Flask!')

# Страница с формой
@app.route('/greet', methods=['GET', 'POST'])
def greet():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if name:
            return render_template('index.html', title='Приветствие', content=f'Привет, {name}!')
        else:
            return render_template('index.html', title='Ошибка', content='Пожалуйста, введите имя.')
    # Если GET-запрос — просто показываем форму
    return render_template('index.html', title='Введите имя', show_form=True)

# Запуск приложения
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
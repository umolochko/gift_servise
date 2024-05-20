from flask import Flask, render_template, request, g, redirect, url_for
import sqlite3
import openai
import os

app = Flask(__name__)
DATABASE = 'certificates.db'
openai.api_key = os.getenv("sk-proj-cWVTWVnn1vZtLI5VLJmpT3BlbkFJWKS5SbRvpdSXHyMNKyJ9")


# Функция для подключения к базе данных
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


# Функция для закрытия подключения к базе данных
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# Создаем таблицу для сертификатов, если она еще не существует
def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS certificates
                          (id INTEGER PRIMARY KEY AUTOINCREMENT,
                           name TEXT,
                           phone TEXT,
                           email TEXT,
                           event_date TEXT,
                           send_via TEXT,
                           gift_types TEXT)''')
        db.commit()


# Функция для добавления сертификата в базу данных
def add_certificate(name, phone, email, event_date, send_via, gift_types):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO certificates (name, phone, email, event_date, send_via, gift_types) VALUES (?, ?, ?, ?, ?, ?)",
        (name, phone, email, event_date, send_via, gift_types))
    db.commit()


# Главная страница для ввода информации о сертификате
@app.route('/')
def certificate_form():
    return render_template('certificate_form.html')


# Обработка формы сертификата
@app.route('/process_certificate_form', methods=['POST'])
def process_certificate_form():
    name = request.form['name']
    phone = request.form['phone']
    email = request.form['email']
    event_date = request.form['event_date']
    send_via = request.form['send_via']
    return redirect(
        url_for('choose_gift_types', name=name, phone=phone, email=email, event_date=event_date, send_via=send_via))


# Страница выбора типа цифрового подарка
@app.route('/choose_gift_types')
def choose_gift_types():
    name = request.args.get('name')
    phone = request.args.get('phone')
    email = request.args.get('email')
    event_date = request.args.get('event_date')
    send_via = request.args.get('send_via')
    return render_template('gift_types.html', name=name, phone=phone, email=email, event_date=event_date,
                           send_via=send_via)


# Обработка выбора типа цифрового подарка
@app.route('/process_gift_types', methods=['POST'])
def process_gift_types():
    name = request.form['name']
    phone = request.form['phone']
    email = request.form['email']
    event_date = request.form['event_date']
    send_via = request.form['send_via']
    gift_types = request.form.getlist('gift_type')
    gift_types_str = ', '.join(gift_types)
    add_certificate(name, phone, email, event_date, send_via, gift_types_str)

    if 'Quiz' in gift_types:
        return redirect(url_for('quiz_form'))
    else:
        return redirect(url_for('confirmation', name=name, gift_types=gift_types_str))


# Страница подтверждения
@app.route('/confirmation')
def confirmation():
    name = request.args.get('name')
    gift_types = request.args.get('gift_types')
    return render_template('confirmation.html', name=name, gift_types=gift_types)


# Страница сбора информации для квиза
@app.route('/quiz_form')
def quiz_form():
    return render_template('quiz_form.html')


# Обработка формы квиза и генерация вопросов
@app.route('/process_quiz_form', methods=['POST'])
def process_quiz_form():
    age = request.form['age']
    gender = request.form['gender']
    interests = request.form['interests']

    try:
        quiz_questions = generate_quiz(age, gender, interests)
        return render_template('generated_quiz.html', questions=quiz_questions)
    except Exception as e:
        return f"An error occurred: {str(e)}"


def generate_quiz(age, gender, interests):
    prompt = f"Create a quiz with 5 questions for a {age}-year-old {gender} interested in {interests}. Each question should have 4 answer options."

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a quiz generator."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500
    )

    questions = response['choices'][0]['message']['content'].strip().split('\n\n')
    quiz = []

    for question in questions:
        parts = question.split('\n')
        question_text = parts[0]
        options = parts[1:5]
        quiz.append({'question': question_text, 'options': options})

    return quiz


if __name__ == '__main__':
    init_db()  # Инициализируем базу данных перед запуском приложения
    app.run(debug=True)

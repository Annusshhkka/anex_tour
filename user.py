import telebot
from telebot import types
from datetime import datetime, timedelta
import requests
import mysql.connector
import os


token = 'token'
bot = telebot.TeleBot(token)


def create_connection():
    try:
        conn = mysql.connector.connect(host='', user='', password='', database='') 
        return conn
    except Exception as e:
        print(e)


def add_user(message):
    try:
        conn = create_connection()
        c = conn.cursor()
        c.execute('INSERT IGNORE INTO users (id, telegram_name) VALUES (%s, %s)',
                  (message.chat.id, '@' + message.from_user.username))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Произошла ошибка в функции add_user: {e}")


def name(message):
    try:
        conn = create_connection()
        c = conn.cursor()
        c.execute(f"UPDATE users SET name = %s WHERE id = %s",
                  (message.text, message.chat.id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Произошла ошибка в функции name: {e}")


def activity_off(user_id):
    try:
        conn = create_connection()
        c = conn.cursor()
        c.execute(f"UPDATE users SET activity = %s WHERE id = %s",
                  ('0', user_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Произошла ошибка в функции activity_off: {e}")


def vacancyes(user_id):
    conn = create_connection()
    c = conn.cursor()
    c.execute("SELECT DISTINCT id, title FROM vacancy order by id")
    vacancyes_ = c.fetchall()
    conn.close()
    response_message = '\n\n<b>Наши вакансии:</b>\n'
    keyboard_ = types.InlineKeyboardMarkup()
    row = []
    for vacancy_ in vacancyes_:
        response_message += f'\n{vacancy_[0]}. {vacancy_[1]}'
        button_ = types.InlineKeyboardButton(text=vacancy_[0], callback_data=f'vacancy_{vacancy_[0]}')
        row.append(button_)
        if len(row) == 3:
            keyboard_.row(*row)
            row = []
    if row:
        keyboard_.row(*row)
    try:
        bot.send_message(user_id, response_message, parse_mode='HTML', reply_markup=keyboard_)
    except telebot.apihelper.ApiTelegramException as e:
        if e.error_code in [403, 400]:
            activity_off(user_id)
        else:
            print("Ошибка при отправке сообщения:", e)


def vacancy(user_id, vacancy_id):
    try:
        conn = create_connection()
        c = conn.cursor()
        c.execute("SELECT title, description FROM vacancy where id = %s", (vacancy_id,))
        vacancy_info = c.fetchone()
        conn.close()
        keyboard_inline = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton(text="Пройти собеседование", callback_data=f'interview_{vacancy_id}')
        keyboard_inline.add(back)
        response_message = f'<b><i><u>{vacancy_info[0]}</u></i></b>:\n\n{vacancy_info[1]}'
        bot.send_message(user_id, response_message, reply_markup=keyboard_inline, parse_mode="HTML")
    except telebot.apihelper.ApiTelegramException as e:
        if e.error_code in [403, 400]:
            activity_off(user_id)
        else:
            print(f"Произошла ошибка в функции vacancy: {e}")


def info(col_info, col, val, table):
    try:
        conn = create_connection()
        c = conn.cursor()
        c.execute(f"SELECT {col_info} FROM {table} where {col} = %s", (val,))
        result = c.fetchone()
        conn.close()
        if result is not None:
            return result[0]
        else:
            return None
    except Exception as e:
        print(f"Произошла ошибка в функции info: {e}")


def delete_resume(user_id):
    try:
        fail = info('resume', 'id', user_id, 'users')
        if os.path.exists(fail):
            os.remove(fail)
        conn = create_connection()
        c = conn.cursor()
        c.execute(f"update users set resume = NULL WHERE id = %s", (user_id,))
        conn.commit()
        conn.close()
        bot.send_message(user_id, 'Ваше резюме удалено')
    except telebot.apihelper.ApiTelegramException as e:
        if e.error_code in [403, 400]:
            activity_off(user_id)
        else:
            print(f"Произошла ошибка в функции delete_resume: {e}")


def resume(user_id, info_resume):
    try:
        conn = create_connection()
        c = conn.cursor()
        c.execute(f'update users set resume = %s where id = %s', (info_resume, user_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Произошла ошибка в функции resume: {e}")


def interview(user_id, vacancy_id):
    try:
        conn = create_connection()
        c = conn.cursor()
        c.execute('insert ignore into vacancy_users (user_id, vacancy_id) values (%s, %s)',
                  (user_id, vacancy_id))
        c.execute('select id from questions where vacancy_id = %s', (vacancy_id, ))
        rows = c.fetchall()
        if rows:
            for row in rows:
                c.execute('INSERT IGNORE INTO answers (user_id, question_id) VALUES (%s, %s)',
                          (user_id, row[0]))
        conn.commit()
        conn.close()
        questions(user_id, vacancy_id)
    except Exception as e:
        print(f"Произошла ошибка в функции interview: {e}")


def answer(user_id, answer_):
    try:
        conn = create_connection()
        c = conn.cursor()
        c.execute('select v.id from answers a INNER JOIN questions q on a.question_id = q.id '
                  'INNER JOIN vacancy v on v.id = q.vacancy_id '
                  'where a.user_id = %s and a.answer is NULL limit 1', (user_id, ))
        vacancy_id = c.fetchone()[0]
        c.execute('update answers set answer = %s where user_id = %s and answer is NULL limit 1',
                  (answer_, user_id))
        conn.commit()
        conn.close()
        questions(user_id, vacancy_id)
    except Exception as e:
        print(f"Произошла ошибка в функции answer: {e}")


def questions(user_id, vacancy_id):
    try:
        conn = create_connection()
        c = conn.cursor()
        c.execute('select q.question from answers a INNER JOIN questions q on a.question_id = q.id '
                  'where user_id = %s and answer is NULL limit 1',
                  (user_id, ))
        question = c.fetchone()
        conn.close()
        if question:
            bot.send_message(user_id, question[0])
        else:
            keyboard_inline = types.InlineKeyboardMarkup()
            back = types.InlineKeyboardButton(text="Другие вакансии", callback_data='vacancyes')
            keyboard_inline.add(back)
            bot.send_message(user_id, '<i>Вы прошли предварительное собеседование! Ожидайте ответа на Ваш отклик...</i>',
                             parse_mode='HTML', reply_markup=keyboard_inline)
            return user_id, vacancy_id
    except telebot.apihelper.ApiTelegramException as e:
        if e.error_code in [403, 400]:
            activity_off(user_id)
        else:
            print(f"Произошла ошибка в функции questions: {e}")


def generate_next_7_days(call):
    today = datetime.now()
    keyboard_ = types.InlineKeyboardMarkup()
    for i in range(1, 8, 2):
        day = today + timedelta(days=i)
        formatted_date = day.strftime("%Y-%m-%d")
        text_date = day.strftime("%d.%m.%Y")
        day_2 = today + timedelta(days=i+1)
        formatted_date_2 = day_2.strftime("%Y-%m-%d")
        text_date_2 = day_2.strftime("%d.%m.%Y")
        button_ = types.InlineKeyboardButton(text=text_date, callback_data=f'date{call}_{formatted_date}')
        button_2 = types.InlineKeyboardButton(text=text_date_2, callback_data=f'date{call}_{formatted_date_2}')
        keyboard_.add(button_, button_2)
    return keyboard_


def get_weekday(date):
    try:
        weekdays = ['Понедельник', 'Вторник', 'Среду', 'Четверг', 'Пятницу', 'Субботу', 'Воскресенье']
        today_weekday = date.weekday()
        return weekdays[today_weekday]
    except Exception as e:
        print('Ошибка в функции get_weekday:', e)


def download_file(file_url, dest):
    response = requests.get(file_url)
    response.raise_for_status()
    with open(dest, 'wb') as file:
        file.write(response.content)
    return dest

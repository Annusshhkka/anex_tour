from user import *


token = 'token'
bot = telebot.TeleBot(token)


def add_staff(staff_id, first_name):
    try:
        name_ = info('name', 'id', staff_id, 'users')
        conn = create_connection()
        c = conn.cursor()
        c.execute(f"insert into staff(id, telegram_name, name) values (%s, %s, %s)",
                  (staff_id, '@' + first_name, name_))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Произошла ошибка в функции add_staff: {e}")


def add_vacancy(user_id, title_vacancy):
    try:
        conn = create_connection()
        c = conn.cursor()
        c.execute("insert into vacancy (staff_id, title) values (%s, %s)", (user_id, title_vacancy))
        conn.commit()
        conn.close()
        bot.send_message(user_id, 'Теперь напишите описание вакансии: обязаности, требования, условия',
                         parse_mode="HTML")
        return info('id', 'title', title_vacancy, 'vacancy')
    except telebot.apihelper.ApiTelegramException as e:
        if e.error_code in [403, 400]:
            activity_off(user_id)
        else:
            print(f"Произошла ошибка в функции add_vacancy: {e}")


def add_vacancy_description(user_id, vacancy_id, description):
    try:
        conn = create_connection()
        c = conn.cursor()
        c.execute("update vacancy set description = %s where id = %s",
                  (description, vacancy_id))
        conn.commit()
        c.execute("select title, description from vacancy where id = %s",
                  (vacancy_id, ))
        vacancy_info = c.fetchone()
        conn.close()
        bot.send_message(user_id, '<b>Отлично, давайте посмотрим как Ваша вакансия выглядит со стороны:</b>',
                         parse_mode="HTML")
        bot.send_message(user_id, f'<b><i><u>{vacancy_info[0]}</u></i></b>:\n\n{vacancy_info[1]}')
        keyboard_inline = types.InlineKeyboardMarkup()
        yes = types.InlineKeyboardButton(text="Да", callback_data=f'add_questions_{vacancy_id}')
        no = types.InlineKeyboardButton(text="Нет, начать заново", callback_data=f'del_{vacancy_id}')
        keyboard_inline.add(yes, no)
        bot.send_message(user_id, 'Если вы согласны с результатом, давайте перейдем к вопросам')
    except telebot.apihelper.ApiTelegramException as e:
        if e.error_code in [403, 400]:
            activity_off(user_id)
        else:
            print(f"Произошла ошибка в функции add_vacancy_description: {e}")


def delete_vacancy(user_id, vacancy_id):
    try:
        conn = create_connection()
        c = conn.cursor()
        title = info('title', 'id', vacancy_id, 'vacancy')
        c.execute("SELECT id FROM questions WHERE vacancy_id = %s", (vacancy_id,))
        question_ids = c.fetchall()
        if question_ids:
            question_ids_list = [id_[0] for id_ in question_ids]
            question_ids_tuple = tuple(question_ids_list)
            placeholders = ','.join(['%s'] * len(question_ids_tuple))
            query = f"DELETE FROM answers WHERE question_id IN ({placeholders})"
            c.execute(query, question_ids_tuple)
        c.execute("DELETE FROM questions WHERE vacancy_id = %s", (vacancy_id,))
        c.execute("DELETE FROM vacancy WHERE id = %s", (vacancy_id,))
        c.execute("DELETE FROM vacancy_users WHERE vacancy_id = %s", (vacancy_id,))
        conn.commit()
        conn.close()
        bot.send_message(user_id, f'<i>Вакансия <b>{title}</b> удалена</i>', parse_mode="HTML")
    except telebot.apihelper.ApiTelegramException as e:
        if e.error_code in [403, 400]:
            activity_off(user_id)
        else:
            print(f"Произошла ошибка в функции delete_vacancy: {e}")
    except Exception as e:
        print(f"Произошла ошибка при обработке сообщения: {e}")


def vacancy_staff(user_id, all_=None):
    try:
        conn = create_connection()
        c = conn.cursor()
        if all_:
            c.execute('select id, title, description from vacancy')
            bot.send_message(user_id, '<b><u>Все вакансии:</u></b>', parse_mode='HTML')
        else:
            c.execute('select id, title, description from vacancy where staff_id = %s', (user_id, ))
            bot.send_message(user_id, '<b><u>Ваши вакансии:</u></b>', parse_mode='HTML')
        rows = c.fetchall()
        if rows:
            for id_, title, description in rows:
                keyboard_inline = types.InlineKeyboardMarkup()
                del_ = types.InlineKeyboardButton(text="Удалить", callback_data=f'del_{id_}')
                edit = types.InlineKeyboardButton(text="Редактировать", callback_data=f'edit_{id_}')
                see = types.InlineKeyboardButton(text="Посмотреть кандидатов", callback_data=f'see_{id_}')
                keyboard_inline.add(edit, del_)
                keyboard_inline.add(see)
                bot.send_message(user_id, f'<b><i><u>{title}</u></i></b>:\n\n{description}',
                                 reply_markup=keyboard_inline, parse_mode='HTML')
        else:
            bot.send_message(user_id, '<b><u>Вакансий нет</u></b>', parse_mode='HTML')
        conn.close()
    except telebot.apihelper.ApiTelegramException as e:
        if e.error_code in [403, 400]:
            activity_off(user_id)
        else:
            print(f"Произошла ошибка в функции vacancy_staff: {e}")


def edit_(user_id, vacancy_id, col, val):
    try:
        conn = create_connection()
        c = conn.cursor()
        c.execute(f"update vacancy set {col} = %s where id = %s",
                  (val, vacancy_id))
        conn.commit()
        conn.close()
        bot.send_message(user_id, '<b>Вакансия обновлена</b>', parse_mode="HTML")
    except telebot.apihelper.ApiTelegramException as e:
        if e.error_code in [403, 400]:
            activity_off(user_id)
        else:
            print(f"Произошла ошибка в функции edit_: {e}")


def add_questions(user_id, questions_, vacancy_id):
    try:
        conn = create_connection()
        c = conn.cursor()
        questions_ = questions_ + ' '
        questions_ = questions_.split("? ")[:-1]
        for question in questions_:
            c.execute('insert into questions (vacancy_id, question) values (%s, %s)', (vacancy_id, question + '?'))
        conn.commit()
        conn.close()
        bot.send_message(user_id, '<i>Вопросы добавлены</i>', parse_mode='HTML')
    except telebot.apihelper.ApiTelegramException as e:
        if e.error_code in [403, 400]:
            activity_off(user_id)
        else:
            print(f"Произошла ошибка в функции add_questions: {e}")


def questions_staff(user_id, vacancy_id):
    try:
        conn = create_connection()
        c = conn.cursor()
        c.execute('select question from questions where vacancy_id = %s', (vacancy_id, ))
        rows = c.fetchall()
        if rows:
            res = '<b>Вопросы, которые были:</b>\n\n'
            for i, row in enumerate(rows, start=1):
                res += f'{i}. {row[0]}\n'
            c.execute('delete from questions where vacancy_id = %s', (vacancy_id, ))
            conn.commit()
        else:
            res = '<b>У этой вакансии нет вопросов</b>\n\n'
        conn.close()
        bot.send_message(user_id, res, parse_mode='HTML')
    except telebot.apihelper.ApiTelegramException as e:
        if e.error_code in [403, 400]:
            activity_off(user_id)
        else:
            print(f"Произошла ошибка в функции questions: {e}")


def check(user_id, vacancy_id, notification=None):
    try:
        conn = create_connection()
        c = conn.cursor()
        if notification:
            c.execute('select u.id, u.telegram_name, u.name, u.activity from vacancy_users vu '
                      'INNER JOIN users u on u.id=vu.user_id where vacancy_id = %s and u.id = %s and u.activity = 1',
                      (vacancy_id, user_id))
            row = c.fetchone()
            if row:
                staff = info('staff_id', 'id', vacancy_id, 'vacancy')
                vacancy_ = info('title', 'id', vacancy_id, 'vacancy')
                send_file_to_user(staff, row[0], f'НОВЫЙ ОТКЛИК НА ВАКАНСИЮ <b>{vacancy_}\ntelegram_name:</b> '
                                                 f'{row[1]}\n<b>ФИО:</b> {row[2]}'
                                                 f'{answer_staff(user_id, vacancy_id)}\n\n'
                                                 f'<i>Резюме прикреплено</i>')
        else:
            c.execute('select u.id, u.telegram_name, u.name, u.activity from vacancy_users vu '
                      'INNER JOIN users u on u.id=vu.user_id where vacancy_id = %s and u.activity = 1', (vacancy_id, ))
            rows = c.fetchall()
            if rows:
                bot.send_message(user_id, '<b>Все кандидаты:</b>', parse_mode='HTML')
                for row in rows:
                    if row[3] == 1:
                        send_file_to_user(user_id, row[0], f'<b>telegram_name:</b> {row[1]}\n<b>ФИО:</b> {row[2]}'
                                                           f'{answer_staff(user_id, vacancy_id)}\n\n'
                                                           f'<i>Резюме прикреплено</i>')
            else:
                bot.send_message(user_id, '<b>У этой вакансии пока нет кандидатов</b>', parse_mode='HTML')
            conn.close()
    except telebot.apihelper.ApiTelegramException as e:
        if e.error_code in [403, 400]:
            activity_off(user_id)
        else:
            print(f"Произошла ошибка в функции check: {e}")


def answer_staff(user_id, vacancy_id):
    try:
        conn = create_connection()
        c = conn.cursor()
        c.execute('select q.question, a.answer from questions q INNER JOIN answers a on q.id = a.question_id '
                  'where vacancy_id = %s and user_id = %s', (vacancy_id, user_id))
        rows = c.fetchall()
        if rows:
            res = '\n\n<u>Ответы на вопросы:</u>\n\n'
            for i, row in enumerate(rows, start=1):
                res += f'<b>{i}. {row[0]}</b>\n{row[1]}\n\n'
            return res
        conn.close()
    except telebot.apihelper.ApiTelegramException as e:
        if e.error_code in [403, 400]:
            activity_off(user_id)
        else:
            print(f"Произошла ошибка в функции answer_staff: {e}")


def send_file_to_user(staff_id, user_id, text):
    try:
        fail = info('resume', 'id', user_id, 'users')
        with open(fail, 'rb') as file:
            bot.send_document(staff_id, file, caption=text, parse_mode='HTML')
    except telebot.apihelper.ApiTelegramException as e:
        if e.error_code in [403, 400]:
            activity_off(user_id)
        else:
            print(f"Произошла ошибка при отправке файла: {e}")
            bot.send_message(user_id, "Произошла ошибка при отправке файла. Попробуйте позже.")


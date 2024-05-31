import hashlib
from staff import *
from user import *
import requests
import os

token = 'token'
bot = telebot.TeleBot(token)
user_condition = {}


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Здравствуйте, я - бот-помощник Анекси. Как Вас зовут? "
                                      "<i>(Напишите свое ФИО)</i>\n\nПродолжая работу со мной, "
                                      "Вы <b>соглашаетесь</b> на хранение Ваших персональных данных, а именно: "
                                      "<b>Ваши уникальные id, имя пользователя и имя, которое укажете ниже</b>",
                     parse_mode="HTML")
    user_condition[message.chat.id] = 'waiting_name'
    add_user(message)


@bot.message_handler(commands=['vacancy'])
def s(message):
    vacancyes(message.chat.id)


@bot.message_handler(commands=['staff'])
def staff(message):
    staff(message)


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    try:
        if call.data == 'vacancyes':
            vacancyes(call.message.chat.id)
        elif call.data[:8] == 'vacancy_':
            vacancy(call.message.chat.id, call.data[8:])
        elif call.data == 'resume':
            bot.send_message(call.message.chat.id, "<i>Ожидаю файл с вашим резюме...</i>", parse_mode="HTML")
        elif call.data == 'del_resume':
            delete_resume(call.message.chat.id)
        elif call.data[:10] == 'interview_':
            user_condition[call.message.chat.id] = ''
            interview(call.message.chat.id, call.data[10:])
            check(call.message.chat.id, call.data[10:], 'yes')
        elif call.data == 'add_vacancy':
            bot.send_message(call.message.chat.id, 'Напишите название новой вакансии')
            user_condition[call.message.chat.id] = 'waiting_title'
        elif call.data[:4] == 'del_':
            delete_vacancy(call.message.chat.id, call.data[4:])
        elif call.data[:7] == '_title_':
            bot.send_message(call.message.chat.id, '<i>Напишите новое название</i>', parse_mode="HTML")
            user_condition[call.message.chat.id] = f'edit_title_{call.data[7:]}'
        elif call.data[:12] == 'description_':
            bot.send_message(call.message.chat.id, '<i>Напишите новое описание</i>', parse_mode="HTML")
            user_condition[call.message.chat.id] = f'edit_description_{call.data[12:]}'
        elif call.data[:9] == 'question_':
            questions_staff(call.message.chat.id, call.data[9:])
            bot.send_message(call.message.chat.id, '<i>Напишите новые вопросы, которые у Вас есть к кандидату. '
                                                   'Пишите их разделяя знаком вопроса с пробелом. <b>Например:</b></i>',
                             parse_mode='HTML')
            bot.send_message(call.message.chat.id, 'Какой у Вас опыт работы в туризме? Какой самый сложный '
                                                   'случай, с которым вы сталкивались на работе? Какие направления '
                                                   'и страны вы знаете лучше всего?')
            user_condition[call.message.chat.id] = f'waiting_question_{call.data[9:]}'
        elif call.data[:5] == 'edit_':
            keyboard_inline = types.InlineKeyboardMarkup()
            title = types.InlineKeyboardButton(text="Название", callback_data=f'_title_{call.data[5:]}')
            des = types.InlineKeyboardButton(text="Описание", callback_data=f'description_{call.data[5:]}')
            que = types.InlineKeyboardButton(text="Вопросы", callback_data=f'question_{call.data[5:]}')
            keyboard_inline.add(title, des, que)
            bot.send_message(call.message.chat.id, f'Что Вы хотите изменить в вакансии <b>'
                                                   f'{info('title', 'id', call.data[5:], 'vacancy')}</b>?',
                             parse_mode='HTML', reply_markup=keyboard_inline)
        elif call.data[:4] == 'see_':
            check(call.message.chat.id, call.data[4:])
        elif call.data == 'my':
            vacancy_staff(call.message.chat.id)
        elif call.data == 'all':
            vacancy_staff(call.message.chat.id, 'yes')
        elif call.data[:14] == 'add_questions_':
            bot.send_message(call.message.chat.id, '<i>Напишите вопросы, которые у Вас есть к кандидату. '
                                                   'Пишите их разделяя знаком вопроса с пробелом. <b>Например:</b></i>',
                             parse_mode='HTML')
            bot.send_message(call.message.chat.id, 'Какой у Вас опыт работы в туризме? Какой самый сложный '
                                                   'случай, с которым вы сталкивались на работе? Какие направления '
                                                   'и страны вы знаете лучше всего?')
            user_condition[call.message.chat.id] = f'waiting_question_{call.data[14:]}'
    except Exception as e:
        print(f"Произошла ошибка при обработке сообщения: {e}")
        bot.send_message(call.message.chat.id, "Повторите запрос позже")


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        if user_condition.get(message.chat.id) == "waiting_name":
            name(message)
            name_ = message.text.split()[1]
            keyboard_inline = types.InlineKeyboardMarkup()
            back = types.InlineKeyboardButton(text="Отправить резюме", callback_data='resume')
            keyboard_inline.add(back)
            bot.send_message(message.chat.id, f'<i>Приятно познакомится, {name_}</i>.\n'
                                              f'Отправьте нам свое резюме, которое будет использоваться для '
                                              f'рассмотрения на все выбранные вами вакансии. Обязательно укажите в '
                                              f'нем данные, по которым с вами можно будет связаться для дальнейшей '
                                              f'работы', parse_mode='HTML',
                             reply_markup=keyboard_inline)
            user_condition[message.chat.id] = ''
        elif user_condition.get(message.chat.id) == "waiting_pass":
            pas = hashlib.sha256(message.text.encode('utf-8')).hexdigest()
            info_ = info('password', 'password', pas, 'passwords')
            if info_:
                add_staff(message.chat.id, message.from_user.username)
                bot.send_message(message.chat.id, f'<i>{info('name', 'id', message.chat.id, 'staff')}, '
                                                  f'Вы добавлены в базу данных сотрудников, '
                                                  f'чтобы увидеть функции, нужно нажать /staff</i>',
                                 parse_mode="HTML")
                user_condition[message.chat.id] = ''
        elif user_condition.get(message.chat.id) == "":
            answer(message.chat.id, message.text)
        elif user_condition.get(message.chat.id) == "waiting_title":
            id_vacancy = add_vacancy(message.chat.id, message.text)
            user_condition[message.chat.id] = f'waiting_description_{id_vacancy}'
        elif user_condition.get(message.chat.id)[:20] == "waiting_description_":
            add_vacancy_description(message.chat.id, user_condition.get(message.chat.id)[20:], message.text)
        elif user_condition.get(message.chat.id)[:17] == "waiting_question_":
            add_questions(message.chat.id, message.text, user_condition.get(message.chat.id)[17:])
            user_condition[message.chat.id] = ''
        elif user_condition.get(message.chat.id)[:4] == "edit":
            info_ = user_condition.get(message.chat.id).split("_")
            edit_(message.chat.id, info_[2], info_[1], message.text)
    except Exception as e:
        print(f"Произошла ошибка при обработке сообщения: {e}")
        bot.send_message(message.chat.id, "Повторите запрос позже")


@bot.message_handler(content_types=['document'])
def handle_document(message):
    try:
        document = message.document
        file_id = document.file_id
        file_info = bot.get_file(file_id)
        file_url = f'https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}'
        user_id = message.chat.id
        original_filename = file_info.file_path.split('/')[-1]
        file_extension = os.path.splitext(original_filename)[1]
        local_path = f'tmp/{user_id}{file_extension}'
        if not os.path.exists('tmp'):
            os.makedirs('tmp')
        download_file(file_url, local_path)
        resume(message.chat.id, local_path)
        keyboard_inline = types.InlineKeyboardMarkup()
        back = types.InlineKeyboardButton(text="Удалить резюме", callback_data='del_resume')
        keyboard_inline.add(back)
        bot.send_message(message.chat.id, 'Ваше резюме успешно получено\n\n<i>При удалении '
                                          'резюме, наши сотрудники не получат ваши данные</i>',  parse_mode='HTML',
                         reply_markup=keyboard_inline)
        vacancyes(message.chat.id)
    except requests.RequestException as e:
        print(f"Ошибка при скачивании файла: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при скачивании файла. Попробуйте позже.")
    except Exception as e:
        print(f"Произошла ошибка при обработке документа: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при обработке документа. Попробуйте позже.")


def staff(message):
    info_ = info('name', 'id', message.chat.id, 'staff')
    if info_ is None:
        bot.send_message(message.chat.id, f'<i><b>Вы не зарегистрированы как сотрудник.</b></i> '
                                          f'Введите пароль для доступа к функциям сотрудников', parse_mode="HTML")
        user_condition[message.chat.id] = 'waiting_pass'
    else:
        keyboard_inline = types.InlineKeyboardMarkup()
        add = types.InlineKeyboardButton(text='Добавить вакансию', callback_data='add_vacancy')
        my = types.InlineKeyboardButton(text='Посмотреть мои вакансии', callback_data='my')
        all_ = types.InlineKeyboardButton(text='Посмотреть все вакансии', callback_data='all')
        keyboard_inline.add(add)
        keyboard_inline.add(my)
        keyboard_inline.add(all_)
        bot.send_message(message.chat.id, f'{info_.split()[1]}, для Вас доступны следующие функции:',
                         reply_markup=keyboard_inline, parse_mode="HTML")


bot.polling()

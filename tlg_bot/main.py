#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Bauyrzhan Ospan"
__copyright__ = "Copyright 2019"
__version__ = "1.0.1"
__maintainer__ = "Bauyrzhan Ospan"
__email__ = "bospan@cleverest.tech"
__status__ = "Development"

import telebot
from telebot import types
from pprint import pprint
import logging
from pymongo import MongoClient
import pymongo
import datetime
import time


client = MongoClient('mongodb://database:27017/')
db = client.b2u
users = db['users']
problems = db['problems']
msgs = db['messages']
dash = db['dash']


bot = telebot.TeleBot("806603779:AAGXStpRxg5Gks5o2nUKh_JOYziZObKXoCs")
logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)
group_id = -1001438155243


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.forward_message(group_id, message.chat.id, message.message_id)
    hello_string = 'Пройдите регистрацию: укажите свой номер'
    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    reg_button = types.KeyboardButton(text="Пройти регистрацию", request_contact=True)
    keyboard.add(reg_button)

    user = {
        "user": str(message.chat.id),
        "tlgfirstname": str(message.chat.first_name),
        "tlglastname": str(message.chat.last_name),
        "tlgusername": str(message.chat.username),
        "registration": message.date,
        "phone": "",
        "object": "",
        "name": "",
        "surname": ""
        }
    users.insert_one(user)
    
    bot.send_message(message.chat.id, hello_string, reply_markup=keyboard)


@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    bot.forward_message(group_id, message.chat.id, message.message_id)
    if message.contact is not None:
        if users.count_documents({"user": str(message.chat.id)})>0:
            users.update_one({"user": str(message.chat.id)}, { "$set": { "phone": str(message.contact.phone_number)}})
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "Введите фамилию и имя:", reply_markup=markup)
        else:
            user = {
            "user": str(message.chat.id),
            "tlgfirstname": str(message.chat.first_name),
            "tlglastname": str(message.chat.last_name),
            "tlgusername": str(message.chat.username),
            "registration": message.date,
            "phone": str(message.contact.phone_number)
            }
            users.insert_one(user)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "Введите фамилию и имя:", reply_markup=markup)
    else:
        hello_string = 'Регистрация обязательна'
        keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        reg_button = types.KeyboardButton(text="Пройти регистрацию", request_contact=True)
        keyboard.add(reg_button)
        bot.send_message(message.chat.id, hello_string, reply_markup=keyboard)


@bot.message_handler(content_types=['text'])
def text_handler(message):
    bot.forward_message(group_id, message.chat.id, message.message_id)
    
    if message.text.split(" ")[0].lower() == "проблема":
        msg = {
            "from": str(message.chat.id),
            "time": message.date,
            "message": message.text
            }
        problems.insert_one(msg)
        after_registration = "Ваша проблема была зарегестрирована, можете приложить фото"
        bot.send_message(message.chat.id, after_registration)
    else:
        msg = {
            "from": str(message.chat.id),
            "time": message.date,
            "message": message.text
            }
        msgs.insert_one(msg)

    # region: Position
        if message.text.split(":")[0] == 'Позиция':
            if users.count_documents({"user": str(message.chat.id)})>0:
                users.update_one({"user": str(message.chat.id)}, { "$set": { "position": str(message.text.split(" ")[1])}})
                after_registration = "Теперь если есть проблема, то пишите сюда, с указанием объекта, причины и срочности. Срочность может быть от 1 до 9, где 1 - надо решать прям сейчас, а 9 - можно решить через 9 дней."
                bot.send_message(message.chat.id, after_registration)

                after_registration = "Пример сообщения:"
                bot.send_message(message.chat.id, after_registration)

                after_registration = "проблема 1 Больница №2 у нас закончились материалы"
                bot.send_message(message.chat.id, after_registration)

                after_registration = "Где проблема надо писать обязательно, 1 - срочность, знаки препинания не нужны"
                bot.send_message(message.chat.id, after_registration)

                after_registration = "Можно также приложить фото"
                bot.send_message(message.chat.id, after_registration)
            else:
                hello_string = 'Пройдите регистрацию: укажите свой номер'
                keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True)
                reg_button = types.KeyboardButton(text="Пройти регистрацию", request_contact=True)
                keyboard.add(reg_button)
                bot.send_message(message.chat.id, hello_string, reply_markup=keyboard)
        # endregion
    
    # region: Replies
    if message.reply_to_message:

        # region: Name and surname
        if message.reply_to_message.text == 'Введите фамилию и имя:':
            if len(message.text.split(" ")) == 2:
                name = message.text.split(" ")[0]
                surname = message.text.split(" ")[1]
                
                if users.count_documents({"user": str(message.chat.id)})>0:
                    users.update_one({"user": str(message.chat.id)}, { "$set": { "name": str(name), "surname": str(surname)}})
                    after_registration = "Выберите Вашу позицию"
                    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
                    markup.row('Позиция: Снабжение')
                    markup.row('Позиция: Производство')
                    markup.row('Позиция: Бригадир')
                    markup.row('Позиция: Другое')
                    bot.send_message(message.chat.id, after_registration, reply_markup=markup)
                else:
                    hello_string = 'Пройдите регистрацию: укажите свой номер'
                    keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True)
                    reg_button = types.KeyboardButton(text="Пройти регистрацию", request_contact=True)
                    keyboard.add(reg_button)
                    bot.send_message(message.chat.id, hello_string, reply_markup=keyboard)
            else:
                bot.send_message(message.chat.id, "Пример: Иванов Иван")
                bot.send_message(message.chat.id, "Введите фамилию и имя:", reply_markup=markup)
        # endregion

        # region: Checking data

        # region: production
        if message.reply_to_message.text == 'Количество произведенных консолей на 1 газ в общем?':
            msg = {
            "from": str(message.chat.id),
            "time": message.date,
            "data": message.text,
            "type": "p1"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "Количество произведенных консолей на 3 газа в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'Количество произведенных консолей на 3 газа в общем?':
            msg = {
            "from": str(message.chat.id),
            "time": message.date,
            "data": message.text,
            "type": "p2"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "Количество произведенных РШ в общем?", reply_markup=markup)

        if message.reply_to_message.text == 'Количество произведенных РШ в общем?':
            msg = {
            "from": str(message.chat.id),
            "time": message.date,
            "data": message.text,
            "type": "p3"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "Количество произведенных КРБ в общем?", reply_markup=markup)

        if message.reply_to_message.text == 'Количество произведенных КРБ в общем?':
            msg = {
            "from": str(message.chat.id),
            "time": message.date,
            "data": message.text,
            "type": "p4"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "Количество произведенных компрессорных станций в общем?", reply_markup=markup)

        if message.reply_to_message.text == 'Количество произведенных компрессорных станций в общем?':
            msg = {
            "from": str(message.chat.id),
            "time": message.date,
            "data": message.text,
            "type": "p5"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "Количество произведенных вакуумных станций в общем?", reply_markup=markup)

        if message.reply_to_message.text == 'Количество произведенных вакуумных станций в общем?':
            msg = {
            "from": str(message.chat.id),
            "time": message.date,
            "data": message.text,
            "type": "p6"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "Количество произведенных кислородных станций в общем?", reply_markup=markup)

        if message.reply_to_message.text == 'Количество произведенных кислородных станций в общем?':
            msg = {
            "from": str(message.chat.id),
            "time": message.date,
            "data": message.text,
            "type": "p7"
            }
            dash.insert_one(msg)
            bot.send_message(message.chat.id, "Спасибо большое!")

        # endregion

        # region: mount
        if message.reply_to_message.text == 'ГКИБ: Количество проложенных труб в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "ГКИБ",
            "time": message.date,
            "data": message.text,
            "type": "m1"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "ГКИБ: Количество установленных КРБ в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'ГКИБ: Количество установленных КРБ в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "ГКИБ",
            "time": message.date,
            "data": message.text,
            "type": "m2"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "ГКИБ: Количество установленных РШ в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'ГКИБ: Количество установленных РШ в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "ГКИБ",
            "time": message.date,
            "data": message.text,
            "type": "m3"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "ГКИБ: Количество установленных консолей на 1 газ в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'ГКИБ: Количество установленных консолей на 1 газ в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "ГКИБ",
            "time": message.date,
            "data": message.text,
            "type": "m4"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "ГКИБ: Количество установленных консолей на 3 газа в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'ГКИБ: Количество установленных консолей на 3 газа в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "ГКИБ",
            "time": message.date,
            "data": message.text,
            "type": "m5"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "ГКИБ: Количество установленных ваакумных станций в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'ГКИБ: Количество установленных ваакумных станций в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "ГКИБ",
            "time": message.date,
            "data": message.text,
            "type": "m6"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "ГКИБ: Количество установленных станций сжатого воздуха в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'ГКИБ: Количество установленных станций сжатого воздуха в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "ГКИБ",
            "time": message.date,
            "data": message.text,
            "type": "m7"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "ГКИБ: Количество установленных кислородных станций в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'ГКИБ: Количество установленных кислородных станций в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "ГКИБ",
            "time": message.date,
            "data": message.text,
            "type": "m8"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "МИГ: Количество проложенных труб в общем?", reply_markup=markup)
        
        # МИГ
        if message.reply_to_message.text == 'МИГ: Количество проложенных труб в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "МИГ",
            "time": message.date,
            "data": message.text,
            "type": "m1"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "МИГ: Количество установленных КРБ в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'МИГ: Количество установленных КРБ в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "МИГ",
            "time": message.date,
            "data": message.text,
            "type": "m2"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "МИГ: Количество установленных РШ в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'МИГ: Количество установленных РШ в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "МИГ",
            "time": message.date,
            "data": message.text,
            "type": "m3"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "МИГ: Количество установленных консолей на 1 газ в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'МИГ: Количество установленных консолей на 1 газ в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "МИГ",
            "time": message.date,
            "data": message.text,
            "type": "m4"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "МИГ: Количество установленных консолей на 3 газа в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'МИГ: Количество установленных консолей на 3 газа в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "МИГ",
            "time": message.date,
            "data": message.text,
            "type": "m5"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "МИГ: Количество установленных ваакумных станций в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'МИГ: Количество установленных ваакумных станций в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "МИГ",
            "time": message.date,
            "data": message.text,
            "type": "m6"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "МИГ: Количество установленных станций сжатого воздуха в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'МИГ: Количество установленных станций сжатого воздуха в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "МИГ",
            "time": message.date,
            "data": message.text,
            "type": "m7"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "МИГ: Количество установленных кислородных станций в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'МИГ: Количество установленных кислородных станций в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "МИГ",
            "time": message.date,
            "data": message.text,
            "type": "m8"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "ЦГКБ: Количество проложенных труб в общем?", reply_markup=markup)
        
        # ЦГКБ

        if message.reply_to_message.text == 'ЦГКБ: Количество проложенных труб в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "ЦГКБ",
            "time": message.date,
            "data": message.text,
            "type": "m1"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "ЦГКБ: Количество установленных КРБ в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'ЦГКБ: Количество установленных КРБ в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "ЦГКБ",
            "time": message.date,
            "data": message.text,
            "type": "m2"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "ЦГКБ: Количество установленных РШ в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'ЦГКБ: Количество установленных РШ в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "ЦГКБ",
            "time": message.date,
            "data": message.text,
            "type": "m3"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "ЦГКБ: Количество установленных консолей на 1 газ в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'ЦГКБ: Количество установленных консолей на 1 газ в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "ЦГКБ",
            "time": message.date,
            "data": message.text,
            "type": "m4"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "ЦГКБ: Количество установленных консолей на 3 газа в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'ЦГКБ: Количество установленных консолей на 3 газа в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "ЦГКБ",
            "time": message.date,
            "data": message.text,
            "type": "m5"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "ЦГКБ: Количество установленных ваакумных станций в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'ЦГКБ: Количество установленных ваакумных станций в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "ЦГКБ",
            "time": message.date,
            "data": message.text,
            "type": "m6"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "ЦГКБ: Количество установленных станций сжатого воздуха в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'ЦГКБ: Количество установленных станций сжатого воздуха в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "ЦГКБ",
            "time": message.date,
            "data": message.text,
            "type": "m7"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "ЦГКБ: Количество установленных кислородных станций в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'ЦГКБ: Количество установленных кислородных станций в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "ЦГКБ",
            "time": message.date,
            "data": message.text,
            "type": "m8"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "БСМП: Количество проложенных труб в общем?", reply_markup=markup)
        
        # БСМП
        if message.reply_to_message.text == 'БСМП: Количество проложенных труб в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "БСМП",
            "time": message.date,
            "data": message.text,
            "type": "m1"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "БСМП: Количество установленных КРБ в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'БСМП: Количество установленных КРБ в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "БСМП",
            "time": message.date,
            "data": message.text,
            "type": "m2"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "БСМП: Количество установленных РШ в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'БСМП: Количество установленных РШ в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "БСМП",
            "time": message.date,
            "data": message.text,
            "type": "m3"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "БСМП: Количество установленных консолей на 1 газ в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'БСМП: Количество установленных консолей на 1 газ в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "БСМП",
            "time": message.date,
            "data": message.text,
            "type": "m4"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "БСМП: Количество установленных консолей на 3 газа в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'БСМП: Количество установленных консолей на 3 газа в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "БСМП",
            "time": message.date,
            "data": message.text,
            "type": "m5"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "БСМП: Количество установленных ваакумных станций в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'БСМП: Количество установленных ваакумных станций в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "БСМП",
            "time": message.date,
            "data": message.text,
            "type": "m6"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "БСМП: Количество установленных станций сжатого воздуха в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'БСМП: Количество установленных станций сжатого воздуха в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "БСМП",
            "time": message.date,
            "data": message.text,
            "type": "m7"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "БСМП: Количество установленных кислородных станций в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'БСМП: Количество установленных кислородных станций в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "БСМП",
            "time": message.date,
            "data": message.text,
            "type": "m8"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "ДГКИБ: Количество проложенных труб в общем?", reply_markup=markup)
        # ДКГИБ
        if message.reply_to_message.text == 'ДГКИБ: Количество проложенных труб в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "ДГКИБ",
            "time": message.date,
            "data": message.text,
            "type": "m1"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "ДГКИБ: Количество установленных КРБ в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'ДГКИБ: Количество установленных КРБ в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "ДГКИБ",
            "time": message.date,
            "data": message.text,
            "type": "m2"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "ДГКИБ: Количество установленных РШ в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'ДГКИБ: Количество установленных РШ в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "ДГКИБ",
            "time": message.date,
            "data": message.text,
            "type": "m3"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "ДГКИБ: Количество установленных консолей на 1 газ в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'ДГКИБ: Количество установленных консолей на 1 газ в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "ДГКИБ",
            "time": message.date,
            "data": message.text,
            "type": "m4"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "ДГКИБ: Количество установленных консолей на 3 газа в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'ДГКИБ: Количество установленных консолей на 3 газа в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "ДГКИБ",
            "time": message.date,
            "data": message.text,
            "type": "m5"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "ДГКИБ: Количество установленных ваакумных станций в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'ДГКИБ: Количество установленных ваакумных станций в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "ДГКИБ",
            "time": message.date,
            "data": message.text,
            "type": "m6"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "ДГКИБ: Количество установленных станций сжатого воздуха в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'ДГКИБ: Количество установленных станций сжатого воздуха в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "ДГКИБ",
            "time": message.date,
            "data": message.text,
            "type": "m7"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "ДГКИБ: Количество установленных кислородных станций в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'ДГКИБ: Количество установленных кислородных станций в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "ДГКИБ",
            "time": message.date,
            "data": message.text,
            "type": "m8"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "ЦФ: Количество проложенных труб в общем?", reply_markup=markup)
        # ЦФ
        if message.reply_to_message.text == 'ЦФ: Количество проложенных труб в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "ЦФ",
            "time": message.date,
            "data": message.text,
            "type": "m1"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "ЦФ: Количество установленных КРБ в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'ЦФ: Количество установленных КРБ в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "ЦФ",
            "time": message.date,
            "data": message.text,
            "type": "m2"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "ЦФ: Количество установленных РШ в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'ЦФ: Количество установленных РШ в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "ЦФ",
            "time": message.date,
            "data": message.text,
            "type": "m3"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "ЦФ: Количество установленных консолей на 1 газ в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'ЦФ: Количество установленных консолей на 1 газ в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "ЦФ",
            "time": message.date,
            "data": message.text,
            "type": "m4"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "ЦФ: Количество установленных консолей на 3 газа в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'ЦФ: Количество установленных консолей на 3 газа в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "ЦФ",
            "time": message.date,
            "data": message.text,
            "type": "m5"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "ЦФ: Количество установленных ваакумных станций в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'ЦФ: Количество установленных ваакумных станций в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "ЦФ",
            "time": message.date,
            "data": message.text,
            "type": "m6"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "ЦФ: Количество установленных станций сжатого воздуха в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'ЦФ: Количество установленных станций сжатого воздуха в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "ЦФ",
            "time": message.date,
            "data": message.text,
            "type": "m7"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "ЦФ: Количество установленных кислородных станций в общем?", reply_markup=markup)
        if message.reply_to_message.text == 'ЦФ: Количество установленных кислородных станций в общем?':
            msg = {
            "from": str(message.chat.id),
            "object": "ЦФ",
            "time": message.date,
            "data": message.text,
            "type": "m8"
            }
            dash.insert_one(msg)
            bot.send_message(message.chat.id, "Спасибо большое!")
        
        # endregion

        # region: Anvar
        if message.reply_to_message.text == 'Какое количество произведенных станций в КНР сейчас?':
            msg = {
            "from": str(message.chat.id),
            "time": message.date,
            "data": message.text,
            "type": "a1"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "Какое количество произведенных станций без компрессора в КНР сейчас?", reply_markup=markup)
        if message.reply_to_message.text == 'Какое количество произведенных станций без компрессора в КНР сейчас?':
            msg = {
            "from": str(message.chat.id),
            "time": message.date,
            "data": message.text,
            "type": "a7"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "Какое количество доставленных в РК станций сейчас?", reply_markup=markup)
        if message.reply_to_message.text == 'Какое количество доставленных в РК станций сейчас?':
            msg = {
            "from": str(message.chat.id),
            "time": message.date,
            "data": message.text,
            "type": "a2"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "Какое количество произведенных вакуумных станций в КНР сейчас?", reply_markup=markup)
        if message.reply_to_message.text == 'Какое количество произведенных вакуумных станций в КНР сейчас?':
            msg = {
            "from": str(message.chat.id),
            "time": message.date,
            "data": message.text,
            "type": "a3"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "Какое количество доставленных в РК вакуумных станций сейчас?", reply_markup=markup)
        if message.reply_to_message.text == 'Какое количество доставленных в РК вакуумных станций сейчас?':
            msg = {
            "from": str(message.chat.id),
            "time": message.date,
            "data": message.text,
            "type": "a4"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "Какое количество произведенных комп. станций в КНР сейчас?", reply_markup=markup)
        if message.reply_to_message.text == 'Какое количество произведенных комп. станций в КНР сейчас?':
            msg = {
            "from": str(message.chat.id),
            "time": message.date,
            "data": message.text,
            "type": "a5"
            }
            dash.insert_one(msg)
            markup = types.ForceReply(selective=False)
            bot.send_message(message.chat.id, "Какое количество доставленных в РК комп. станций сейчас?", reply_markup=markup)
        if message.reply_to_message.text == 'Какое количество доставленных в РК комп. станций сейчас?':
            msg = {
            "from": str(message.chat.id),
            "time": message.date,
            "data": message.text,
            "type": "a6"
            }
            dash.insert_one(msg)
            bot.send_message(message.chat.id, "От души! Анвар - красавчик!")
            
        # endregion
        
        # endregion
    
    # endregion


@bot.message_handler(content_types=['image'])
def text_handler2(message):
    bot.forward_message(group_id, message.chat.id, message.message_id)



if __name__ == "__main__":
    bot.polling()
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


# region: Constants
client = MongoClient('mongodb://database:27017/')
db = client.admin
col_names = db.list_collection_names()
users = db['users']
u_log = db['log']
messages = db['messages']
settings = db['settings']

if settings.find_one():
    setting = settings.find_one()
else:
    default_settings = {
        "ID админа": "Можно группы (в начале -), но в начале сделайте бота админом в группе",
        "Hash бота": "1424341547:AAE0d0Gtgfcf_iT8kMawbcni7gQvQ9TpXx8",
        "Собирать контакты пользователей?": True,
        "Текст для сообщения регистрации": "Пройдите регистрацию: укажите свой номер",
        "Текст ошибки": "Простите, бот сломался, идите нахуй"
        }
    settings.insert_one(default_settings)
    hello_strings = [{
        "level": 0,
        "button": "Домой",
        "text": "Тут подробная информация\nВот так делать вторую строку\n[Вот так делать ссылку, или спрятать картинку](https://danahub.com/wp-content/uploads/2020/01/TextLogoDanaHub-1536x516.png)",
        "parent": -1,
        "children": [10, 11]
        },
        {
        "level": 10,
        "button": "Первый уровень - 1",
        "text": "Тут подробная информация",
        "parent": 0,
        "children": [200]
        },
        {
        "level": 11,
        "button": "Первый уровень - 2",
        "text": "Тут подробная информация",
        "parent": 0,
        "children": [210]
        },
        {
        "level": 200,
        "button": "Второй уровень - 1",
        "text": "Тут подробная информация",
        "parent": 10,
        "children": []
        },
        {
        "level": 210,
        "button": "Второй уровень - 2",
        "text": "Тут подробная информация",
        "parent": 11,
        "children": []
        }
    ]
    messages.insert_many(hello_strings)

setting = settings.find_one()
bot = telebot.TeleBot(setting["Hash бота"])
logger = telebot.logger
telebot.logger.setLevel(logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)
group_id = setting["ID админа"]
collect_phone = setting["Собирать контакты пользователей?"]
phone_collect_text = setting["Текст для сообщения регистрации"]
# endregion


# region: Функции работы
def send_answer(msg, message):
    text = msg["text"]
    parent = msg["parent"]
    child = msg["children"]
    buttons = []
    markup = types.ReplyKeyboardMarkup(row_width=1, one_time_keyboard=True)

    if len(child) > 0:
        for c in child:
            buttons.append(types.KeyboardButton(str(messages.find_one({"level": c})["button"])))

    if parent != -1:
        buttons.append(types.KeyboardButton("Назад: " + str(messages.find_one({"level": parent})["button"])))

    buttons.append(types.KeyboardButton(str(messages.find_one({"level": 0})["button"])))

    for button in buttons:
        markup.add(button)

    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode= 'Markdown')

def find_msg(message):
    button = message.text
    if len(button.split("азад: ")) > 1:
        try:
            return messages.find_one({"button": button.split("зад: ")[1]})
        except:
            return False
    else:
        try:
            return messages.find_one({"button": button})
        except:
            return False

def send_error(message):
    markup = types.ReplyKeyboardMarkup(row_width=1, one_time_keyboard=True)
    markup.add(types.KeyboardButton(str(messages.find_one({"level": 0})["button"])))
    bot.send_message(message.chat.id, str(setting["Текст ошибки"]), reply_markup=markup, parse_mode= 'Markdown')
# endregion


# Приветсвие
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if collect_phone:
        keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        reg_button = types.KeyboardButton(text="Пройти регистрацию", request_contact=True)
        keyboard.add(reg_button)
        user = {
            "user": str(message.chat.id),
            "firstname": str(message.chat.first_name),
            "lastname": str(message.chat.last_name),
            "username": str(message.chat.username),
            "registration": message.date,
            "phone": "",
            }
        users.insert_one(user)
        bot.send_message(message.chat.id, phone_collect_text, reply_markup=keyboard, parse_mode= 'Markdown')
    else:
        try:
            send_answer(messages.find_one({"level": 0}), message)
        except:
            bot.send_message(message.chat.id, "Бот еще не настроен для работы", parse_mode= 'Markdown')


# Сбор контакта
@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    if message.contact is not None:
        if users.count_documents({"user": str(message.chat.id)})>0:
            users.update_one({"user": str(message.chat.id)}, { "$set": { "phone": str(message.contact.phone_number)}})
            send_answer(messages.find_one({"level": 0}), message)
        else:
            user = {
                "user": str(message.chat.id),
                "firstname": str(message.chat.first_name),
                "lastname": str(message.chat.last_name),
                "username": str(message.chat.username),
                "registration": message.date,
                "phone": str(message.contact.phone_number)
                }
            users.insert_one(user)
            send_answer(messages.find_one({"level": 0}), message)
    else:
        hello_string = 'Регистрация обязательна'
        keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        reg_button = types.KeyboardButton(text="Пройти регистрацию", request_contact=True)
        keyboard.add(reg_button)
        bot.send_message(message.chat.id, hello_string, reply_markup=keyboard)


@bot.message_handler(content_types=['text'])
def text_handler(message):
    log_m = {
        "from": str(message.chat.id),
        "time": message.date,
        "message": message.text
        }
    u_log.insert_one(log_m)
    
    msg = find_msg(message)

    if msg == False:
        send_error(message)
    else:
        send_answer(msg, message)


if __name__ == "__main__":
    bot.polling()
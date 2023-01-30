from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton

# Main Menu
btnCatalog = KeyboardButton('Каталог')
btnOrder = KeyboardButton('Сделать заказ')
btnInfo = KeyboardButton('Информация')
mainMenu = ReplyKeyboardMarkup(resize_keyboard=True).add(btnCatalog, btnOrder, btnInfo)


# Other



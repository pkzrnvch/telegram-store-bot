import os

import redis
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler
from telegram.ext import Filters, Updater, CallbackContext

from elastic_path_api import (fetch_cart,
                              fetch_product,
                              fetch_products,
                              create_customer,
                              get_product_image,
                              add_product_to_cart,
                              delete_product_from_cart)
from reply_markups_and_message_texts import (get_main_menu_reply_markup,
                                             get_cart_reply_markup,
                                             get_product_details_reply_markup,
                                             form_cart_message,
                                             form_product_details_message)

_database = None


def start(update: Update, context: CallbackContext):
    products = fetch_products()
    reply_markup = get_main_menu_reply_markup(products)
    message_text = 'Hello! Please, choose a product you are interested in'
    update.message.reply_text(text=message_text, reply_markup=reply_markup)
    return 'HANDLE_MENU'


def handle_menu(update: Update, context: CallbackContext):
    if update.message:
        return 'HANDLE_MENU'
    callback_data = update.callback_query.data
    chat_id = update.callback_query.message.chat_id
    if callback_data == 'cart':
        cart = fetch_cart(chat_id)
        cart_message = form_cart_message(cart)
        reply_markup = get_cart_reply_markup(cart)
        context.bot.send_message(
            chat_id=chat_id,
            text=cart_message,
            reply_markup=reply_markup
        )
        context.bot.delete_message(
            chat_id=chat_id,
            message_id=update.callback_query.message.message_id
        )
        return 'HANDLE_CART'
    product_id = update.callback_query.data
    product_details = fetch_product(product_id)
    product_image_id = (product_details['relationships']
                        ['main_image']['data']['id'])
    product_image = get_product_image(product_image_id)
    product_details_message = form_product_details_message(product_details)
    reply_markup = get_product_details_reply_markup(product_id)
    with open(product_image, 'rb') as product_image:
        context.bot.send_photo(
            chat_id=chat_id,
            photo=product_image,
            caption=product_details_message,
            reply_markup=reply_markup
        )
    context.bot.delete_message(
        chat_id=chat_id,
        message_id=update.callback_query.message.message_id
    )
    return 'HANDLE_DESCRIPTION'


def handle_cart(update: Update, context: CallbackContext):
    if update.message:
        return 'HANDLE_CART'
    callback_data = update.callback_query.data
    chat_id = update.callback_query.message.chat_id
    if callback_data == 'main_menu':
        message_text = 'Hello! Please, choose a product you are interested in'
        products = fetch_products()
        reply_markup = get_main_menu_reply_markup(products)
        context.bot.send_message(
            chat_id=chat_id,
            text=message_text,
            reply_markup=reply_markup
        )
        context.bot.delete_message(
            chat_id=chat_id,
            message_id=update.callback_query.message.message_id
        )
        return 'HANDLE_MENU'
    elif callback_data == 'order':
        context.bot.send_message(
            chat_id=chat_id,
            text='Please, enter your name',
        )
        context.bot.delete_message(
            chat_id=chat_id,
            message_id=update.callback_query.message.message_id
        )
        return 'WAITING_CONTACT_INFO'
    else:
        product_to_delete_id = callback_data
        cart = delete_product_from_cart(
            product_to_delete_id,
            chat_id
        )
        cart_message = form_cart_message(cart)
        reply_markup = get_cart_reply_markup(cart)
        context.bot.send_message(
            chat_id=chat_id,
            text=cart_message,
            reply_markup=reply_markup
        )
        context.bot.delete_message(
            chat_id=chat_id,
            message_id=update.callback_query.message.message_id
        )
        return 'HANDLE_CART'


def handle_description(update: Update, context: CallbackContext):
    if update.message:
        return 'HANDLE_DESCRIPTION'
    callback_data = update.callback_query.data
    chat_id = update.callback_query.message.chat_id
    if callback_data == 'main_menu':
        message_text = 'Hello! Please, choose a product you are interested in'
        products = fetch_products()
        reply_markup = get_main_menu_reply_markup(products)
        context.bot.send_message(
            chat_id=chat_id,
            text=message_text,
            reply_markup=reply_markup
        )
        context.bot.delete_message(
            chat_id=chat_id,
            message_id=update.callback_query.message.message_id
        )
        return 'HANDLE_MENU'
    elif callback_data == 'cart':
        cart = fetch_cart(chat_id)
        cart_message = form_cart_message(cart)
        reply_markup = get_cart_reply_markup(cart)
        context.bot.send_message(
            chat_id=chat_id,
            text=cart_message,
            reply_markup=reply_markup
        )
        context.bot.delete_message(
            chat_id=chat_id,
            message_id=update.callback_query.message.message_id
        )
        return 'HANDLE_CART'
    else:
        product_id, quantity = callback_data.split('_')
        add_product_to_cart(
            product_id,
            int(quantity),
            chat_id
        )
        update.callback_query.answer()
        return 'HANDLE_DESCRIPTION'


def handle_contact_info(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if 'name' not in context.user_data:
        context.user_data['name'] = update.message.text
        context.bot.send_message(
            chat_id=chat_id,
            text='Please, enter your email'
        )
        return 'WAITING_CONTACT_INFO'
    name = context.user_data['name']
    email = update.message.text
    customer = create_customer(name, email)
    products = fetch_products()
    reply_markup = get_main_menu_reply_markup(products)
    context.bot.send_message(
        chat_id=chat_id,
        text='Thank you! We will contact you shortly',
        reply_markup=reply_markup
    )
    return 'HANDLE_MENU'


def handle_users_reply(update: Update, context: CallbackContext):
    db = get_database_connection()
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return
    if user_reply == '/start':
        user_state = 'START'
    else:
        user_state = db.get(chat_id).decode('utf-8')

    states_functions = {
        'START': start,
        'HANDLE_MENU': handle_menu,
        'HANDLE_DESCRIPTION': handle_description,
        'HANDLE_CART': handle_cart,
        'WAITING_CONTACT_INFO': handle_contact_info
    }
    state_handler = states_functions[user_state]
    try:
        next_state = state_handler(update, context)
        db.set(chat_id, next_state)
    except Exception as err:
        print(err)


def get_database_connection():
    global _database
    if _database is None:
        database_password = os.getenv('REDIS_DB_PASSWORD')
        database_host = os.getenv('REDIS_DB_HOST')
        database_port = int(os.getenv('REDIS_DB_PORT'))
        _database = redis.Redis(
            host=database_host,
            port=database_port,
            password=database_password
        )
    return _database


if __name__ == '__main__':
    load_dotenv()
    token = os.getenv('TG_BOT_TOKEN')
    updater = Updater(token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))
    updater.start_polling()

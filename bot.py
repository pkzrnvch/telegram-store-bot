import os

import redis
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler
from telegram.ext import Filters, Updater, CallbackContext

import elastic_path_api

_database = None


def start(update: Update, context: CallbackContext):
    reply_markup = get_main_menu_reply_markup()
    message_text = 'Hello! Please, choose a product you are interested in'
    update.message.reply_text(text=message_text, reply_markup=reply_markup)
    return 'HANDLE_MENU'


def handle_menu(update: Update, context: CallbackContext):
    if update.message:
        return 'HANDLE_MENU'
    callback_data = update.callback_query.data
    chat_id = update.callback_query.message.chat_id
    if callback_data == 'cart':
        cart = elastic_path_api.fetch_cart(chat_id)
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
    product_details = elastic_path_api.fetch_product(product_id)
    product_image_id = (product_details['relationships']
                        ['main_image']['data']['id'])
    product_image = elastic_path_api.get_product_image(product_image_id)
    product_name = product_details['name']
    product_description = product_details['description']
    product_price = (product_details['meta']['display_price']
                     ['with_tax']['formatted'])
    product_price_text = f'{product_price} per kg'
    product_amount_in_stock = \
        f"{product_details['meta']['stock']['level']} kg on stock"
    message_text = '\n\n'.join([
        product_name,
        product_price_text,
        product_amount_in_stock,
        product_description
    ])
    keyboard = []
    selection_raw = []
    quantity_options = [1, 5, 10]
    for quantity in quantity_options:
        selection_raw.append(InlineKeyboardButton(
            f'{quantity} kg',
            callback_data=f'{product_id}_{quantity}'
        ))
    keyboard.append(selection_raw)
    cart_button = [InlineKeyboardButton('Show cart', callback_data='cart')]
    keyboard.append(cart_button)
    return_button = [InlineKeyboardButton(
        'Main menu',
        callback_data='main_menu'
    )]
    keyboard.append(return_button)
    reply_markup = InlineKeyboardMarkup(keyboard)
    with open(product_image, 'rb') as product_image:
        context.bot.send_photo(
            chat_id=chat_id,
            photo=product_image,
            caption=message_text,
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
        reply_markup = get_main_menu_reply_markup()
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
        cart = elastic_path_api.delete_product_from_cart(
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
        reply_markup = get_main_menu_reply_markup()
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
        cart = elastic_path_api.fetch_cart(chat_id)
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
        elastic_path_api.add_product_to_cart(
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
    customer = elastic_path_api.create_customer(name, email)
    reply_markup = get_main_menu_reply_markup()
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


def get_main_menu_reply_markup():
    keyboard = []
    products = elastic_path_api.fetch_products()
    for product in products:
        product_button = [InlineKeyboardButton(
            product['name'],
            callback_data=product['id']
        )]
        keyboard.append(product_button)
    cart_button = [InlineKeyboardButton('Show cart', callback_data='cart')]
    keyboard.append(cart_button)
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def get_cart_reply_markup(cart):
    keyboard = []
    for item in cart['data']:
        keyboard.append([InlineKeyboardButton(
            f"Remove {item['name']} from cart",
            callback_data=item['id']
        )])
    return_button = [InlineKeyboardButton(
        'Main menu',
        callback_data='main_menu'
    )]
    order_button = [InlineKeyboardButton(
        'Make order',
        callback_data='order'
    )]
    keyboard.append(return_button)
    keyboard.append(order_button)
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def get_database_connection():
    global _database
    if _database is None:
        database_password = os.getenv('REDIS_DB_PASSWORD')
        database_host = os.getenv('REDIS_DB_HOST')
        database_port = os.getenv('REDIS_DB_PORT')
        _database = redis.Redis(
            host=database_host,
            port=database_port,
            password=database_password
        )
    return _database


def form_cart_message(cart):
    if not cart['data']:
        cart_message = 'Your cart is empty at the moment'
    else:
        cart_total = (cart['meta']['display_price']
                      ['with_tax']['formatted'])
        cart_items = cart['data']
        cart_items_texts = []
        for cart_item in cart_items:
            cart_item_price = (cart_item['meta']['display_price']
                               ['with_tax']['unit']['formatted'])
            cart_item_value = (cart_item['meta']['display_price']
                               ['with_tax']['value']['formatted'])
            cart_item_text = '\n'.join([
                cart_item['name'],
                f'{cart_item_price} per kg',
                f'{cart_item["quantity"]} kg in cart for {cart_item_value}'
            ])
            cart_items_texts.append(cart_item_text)
        total_text = f'Total: {cart_total}'
        cart_items_texts.append(total_text)
        cart_message = '\n\n'.join(cart_items_texts)
    return cart_message


if __name__ == '__main__':
    load_dotenv()
    token = os.getenv('TG_BOT_TOKEN')
    updater = Updater(token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))
    updater.start_polling()

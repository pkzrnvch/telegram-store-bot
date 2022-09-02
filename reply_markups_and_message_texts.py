from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu_reply_markup(products, page=1):
    keyboard = []
    chunk_size = 2
    chunked_products = [products[i:i + chunk_size] for i in range(
        0,
        len(products),
        chunk_size
    )]
    chunk_number = page - 1
    for product in chunked_products[chunk_number]:
        product_button = [InlineKeyboardButton(
            product['name'],
            callback_data=product['id']
        )]
        keyboard.append(product_button)
    cart_button = [InlineKeyboardButton('Show cart', callback_data='cart')]
    keyboard.append(cart_button)
    if len(chunked_products) > 1:
        if page == 1:
            previous_button = InlineKeyboardButton(
                'Previous',
                callback_data='inactive'
            )
        else:
            previous_button = InlineKeyboardButton(
                'Previous',
                callback_data=f'page_{page - 1}'
            )
        if page == len(chunked_products):
            next_button = InlineKeyboardButton(
                'Next',
                callback_data='inactive'
            )
        else:
            next_button = InlineKeyboardButton(
                'Next',
                callback_data=f'page_{page + 1}'
            )
        navigation_buttons = [
            previous_button,
            next_button
        ]
        keyboard.append(navigation_buttons)
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


def get_product_details_reply_markup(product_id):
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
    return reply_markup


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


def form_product_details_message(product_details, product_in_cart):
    product_name = product_details['name']
    product_description = product_details['description']
    product_price = (product_details['meta']['display_price']
    ['with_tax']['formatted'])
    product_price_text = f'{product_price} per kg'
    product_amount_in_stock = \
        f"{product_details['meta']['stock']['level']} kg on stock"
    product_details_message = '\n\n'.join([
        product_name,
        product_price_text,
        product_amount_in_stock,
        product_description,
    ])
    if product_in_cart:
        product_quantity = product_in_cart['quantity']
        product_value = (product_in_cart['meta']['display_price']
                                        ['with_tax']['value']['formatted'])
        product_in_cart_text = \
            f'{product_quantity} kg for {product_value} already in cart'
        product_details_message = '\n\n'.join([
            product_details_message,
            product_in_cart_text
        ])
    return product_details_message

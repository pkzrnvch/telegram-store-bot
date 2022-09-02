import os
import time
from pathlib import Path

import requests

ACCESS_TOKEN = None
EXPIRATION_TIME = None


def get_elastic_path_access_token():
    global ACCESS_TOKEN
    global EXPIRATION_TIME
    current_time = time.time()
    if ACCESS_TOKEN is None or EXPIRATION_TIME - 60 < current_time:
        client_id = os.getenv('ELASTIC_PATH_CLIENT_ID')
        client_secret = os.getenv('ELASTIC_PATH_CLIENT_SECRET')
        url = 'https://api.moltin.com/oauth/access_token'
        data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'client_credentials'
        }
        response = requests.post(url, data=data)
        response.raise_for_status()
        decoded_response = response.json()
        ACCESS_TOKEN = decoded_response['access_token']
        EXPIRATION_TIME = decoded_response['expires']
    return ACCESS_TOKEN


def fetch_products():
    access_token = get_elastic_path_access_token()
    url = 'https://api.moltin.com/v2/products'
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    products = response.json()['data']
    return products


def fetch_product(product_id):
    access_token = get_elastic_path_access_token()
    url = f'https://api.moltin.com/v2/products/{product_id}'
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    product = response.json()['data']
    return product


def get_product_image(file_id):
    access_token = get_elastic_path_access_token()
    url = f'https://api.moltin.com/v2/files/{file_id}'
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    image_metadata = response.json()['data']
    image_directory = Path('./images')
    Path.mkdir(image_directory, exist_ok=True)
    image_path = Path(image_directory, image_metadata['file_name'])
    if not image_path.exists():
        response = requests.get(image_metadata['link']['href'])
        response.raise_for_status()
        with open(image_path, 'wb') as file:
            file.write(response.content)
    return image_path


def add_product_to_cart(product_id, quantity, cart_id):
    access_token = get_elastic_path_access_token()
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items'
    headers = {'Authorization': f'Bearer {access_token}'}
    payload = {
        'data': {
            'id': product_id,
            'type': 'cart_item',
            'quantity': quantity
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    cart = response.json()
    return cart


def delete_product_from_cart(product_id, cart_id):
    access_token = get_elastic_path_access_token()
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items/{product_id}'
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.delete(url, headers=headers)
    response.raise_for_status()
    cart = response.json()
    return cart


def fetch_cart(cart_id):
    access_token = get_elastic_path_access_token()
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items'
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    cart = response.json()
    return cart


def create_customer(customer_name, customer_email):
    access_token = get_elastic_path_access_token()
    url = 'https://api.moltin.com/v2/customers'
    headers = {'Authorization': f'Bearer {access_token}'}
    payload = {
        'data': {
            'type': 'customer',
            'name': customer_name,
            'email': customer_email
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    customer = response.json()['data']
    return customer

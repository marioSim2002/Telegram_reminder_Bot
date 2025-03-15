import requests
from bs4 import BeautifulSoup
import json


# Function to fetch and parse HTML
def fetch_html(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"Failed to fetch {url}. Status code: {response.status_code}")


# Function to extract product data
def extract_product_data(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    products = []

    # Example: Extracting product names and prices
    for product in soup.find_all('div', class_='product-item'):
        name = product.find('div', class_='name').text.strip()
        price = product.find('span', class_='price').text.strip()
        products.append({
            'name': name,
            'price': price,
        })
        # Print each product
        print(f"Product: {name}, Price: {price}")

    return products


# Main function
def main():
    url = 'https://shoppy.co.il/collections/all'
    html_content = fetch_html(url)
    products = extract_product_data(html_content)

    # Save to JSON file
    with open('products_data.json', 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=4)

    print(f"Successfully extracted {len(products)} products and saved to 'products_data.json'.")


if __name__ == '__main__':
    main()

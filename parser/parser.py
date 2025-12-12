import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

def scrape_books():
    
    base_url = "http://books.toscrape.com/"
    all_books = []
    
    for page_num in range(1, 4):
        if page_num == 1:
            url = base_url
        else:
            url = f"{base_url}catalogue/page-{page_num}.html"
        
        print(f"Парсинг страницы: {url}")
        
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        book_items = soup.find_all('article', class_='product_pod')
        
        for book in book_items:
            title_tag = book.h3.a
            title = title_tag['title']
            
            price = book.find('p', class_='price_color').text.strip()
            price = float(price.replace('£', '').replace(',', ''))
            
            rating_class = book.find('p', class_='star-rating')['class'][1]
            rating_map = {
                'One': 1, 'Two': 2, 'Three': 3, 
                'Four': 4, 'Five': 5
            }
            rating = rating_map.get(rating_class, 0)
            
            all_books.append({
                'Название': title,
                'Цена (£)': price,
                'Рейтинг': rating,
                'Страница': page_num
            })
        
        time.sleep(1)
    
    return all_books

def save_to_excel(books_data, filename='books_toscrape.xlsx'):
    df = pd.DataFrame(books_data)
    df.to_excel(filename, index=False, engine='openpyxl')
    print(f"Данные сохранены в файл: {filename}")
    print(f"Всего найдено книг: {len(books_data)}")

if __name__ == "__main__":
    books = scrape_books()
    save_to_excel(books)
    
    print("\nПервые 5 книг:")
    print(pd.DataFrame(books).head())

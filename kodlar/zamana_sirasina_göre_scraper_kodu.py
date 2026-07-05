from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
import pandas as pd
from datetime import datetime
import sqlite3


BASE_URL = 'https://www.hepsiburada.com/cata-zaman-ayarli-mekanik-priz-cata-zaman-saati-ct-9180-p-HBCV000008G3D5'
#BASE_URL = 'https://www.hepsiburada.com/yunusoglu-home-isiya-dayanikli-cam-tencere-tava-kapagi-metal-kulplu-buhar-delikli-yedek-kapak-p-HBCV0000BU1LIV-yorumlari'

sayfa: int = 1
global_review_counter = 1
excel_datas = []
seen_ids = set()
product_details = {}

SORT_PARAM = f'?sirala=createdAt'
main_url = f"{BASE_URL}-yorumlari{SORT_PARAM}"

options = webdriver.ChromeOptions()
options.add_argument('--start-maximized')
options.add_experimental_option('detach', True)

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

wait = WebDriverWait(driver, 10)
action = ActionChains(driver)
driver.get(main_url)


def cookies():
    try:
        accept_button = wait.until(
            EC.presence_of_element_located((By.ID, "onetrust-accept-btn-handler"))
        )
        accept_button.click()
        sleep(1)
    except:
        pass


def product_info():
    product_id = BASE_URL.split('-yor')[0].split('-')[-1]
    product_url = BASE_URL.split('-yor')[0]

    title_element = driver.find_element(By.XPATH, "//span[@itemprop='name']")
    product_title = title_element.text.replace('Değerlendirmeleri', '')

    average_rating_element = driver.find_element(By.CSS_SELECTOR, 'span[itemprop="ratingValue"]')
    average_rating = average_rating_element.text.replace(',', '.')

    review_count_element = driver.find_element(By.XPATH,
                                               "//h1[contains(text(), '(') and contains(text(), 'Değerlendirme')]")
    review_count = review_count_element.text.split('(')[-1].split(' ')[0]

    review_count_in_page: int = 10
    max_rating: int = 5

    if int(review_count) > 0:
        total_page = (int(review_count) // review_count_in_page) + (
            1 if int(review_count) % review_count_in_page != 0 else 0)
    else:
        total_page = 1

    global product_details
    product_details['product_id'] = product_id
    product_details['product_url'] = product_url
    product_details['product_title'] = product_title.strip()
    product_details['average_rating'] = float(average_rating)
    product_details['review_count'] = int(review_count)
    product_details['total_page'] = total_page
    product_details['review_count_in_page'] = review_count_in_page
    product_details['max_rating'] = max_rating

    print(
        f"{product_id} - {product_url} - {product_title} - {float(average_rating)} - {int(review_count)} - {total_page}")
    return review_count_in_page, total_page


REVIEW_CONTAINER_CLASS = "hermes-ReviewCard-module-BJtQZy5Ub3goN_D0yNOP"


def scrolling_filtering():
    try:
        review_elements = driver.find_elements(By.CLASS_NAME, REVIEW_CONTAINER_CLASS)
        length = len(review_elements)
        print(f"\n {length} review_elements found")

        if review_elements:
            last_review = review_elements[-1]
            driver.execute_script("arguments[0].scrollIntoView(true);", last_review)
            sleep(2)
    except Exception:
        pass

import hashlib

def get_id(text, date):
    return hashlib.md5(f"{text}_{date}".encode()).hexdigest()

def reviews(current_page_number):
    global global_review_counter
    reviews_block = driver.find_elements(By.CSS_SELECTOR, 'div.hermes-ReviewCard-module-BJtQZy5Ub3goN_D0yNOP')

    if reviews_block:
        for review in reviews_block:
            try:
                review_text_element = review.find_element(By.CSS_SELECTOR,
                                                          'div.hermes-ReviewCard-module-KaU17BbDowCWcTZ9zzxw span').text
                # Boşsa veya NOT yazıyorsa None yap (Veritabanına NULL gitsin)
                if review_text_element and review_text_element.strip() != "NOT":
                    review_text = review_text_element.strip()
                else:
                    review_text = None
            except:
                review_text = None

            try:
                rating_container = review.find_element(By.CSS_SELECTOR,
                                                       'div.hermes-RatingPointer-module-UefD0t2XvgGWsKdLkNoX')
                star_elements = rating_container.find_elements(By.CLASS_NAME, 'star')
                review_rating = len(star_elements)
            except:
                review_rating = 0

            try:
                date_element = review.find_element(By.CSS_SELECTOR, 'span[content]')
                review_date_content = date_element.get_attribute('content')

                if review_date_content:
                    date_obj = datetime.strptime(review_date_content, '%Y-%m-%d')
                    formatted_date = date_obj.strftime('%d/%m/%Y')
                else:
                    formatted_date = None

            except:
                formatted_date = None

            if review_text:
                review_id = get_id(review_text, formatted_date)

                #  duplicate kontrolü
                if review_id in seen_ids:
                    print("⚠️ Duplicate yakalandı, atlandı")
                    continue

                seen_ids.add(review_id)

                row_data = {
                    # Ürün bilgileri
                    'product_id': product_details.get('product_id'),
                    'product_url': product_details.get('product_url'),
                    'product_title': product_details.get('product_title'),
                    'average_rating': product_details.get('average_rating'),
                    'review_count': product_details.get('review_count'),
                    'total_page': product_details.get('total_page'),
                    'max_rating': product_details.get('max_rating'),
                    'review_count_in_page': product_details.get('review_count_in_page'),

                    # Yorum bilgileri
                    'review_text': review_text,  # None ise NULL gider
                    'review_rating': review_rating,
                    'page_no': current_page_number,
                    'review_position': global_review_counter,
                    'review_date': formatted_date,
                }
                excel_datas.append(row_data)

            print(
                f"{global_review_counter}.Yorum [Sayfa {current_page_number}] = {formatted_date} -- {review_text} - {review_rating} Puan")
            global_review_counter += 1

    else:
        print(f"Reviews Block Bulunamadı (Sayfa {current_page_number})")


def wait_page_change(old_element):
    try:
        WebDriverWait(driver, 10).until(
            EC.staleness_of(old_element)
        )
    except:
        print("Sayfa değişimi algılanamadı")

def go_to_page(page):
    try:
        wait = WebDriverWait(driver, 10)

        # span text'i page olan elementi bul
        page_button = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, f"//li[.//span[text()='{page}']]")
            )
        )

        driver.execute_script("arguments[0].click();", page_button)

    except Exception as e:
        print(f"Sayfa {page} tıklanamadı:", e)
        return False

    return True

try:
    cookies()
    review_count_in_page, total_page = product_info()

    while sayfa <= total_page:
        scrolling_filtering()
        reviews(sayfa)
        sayfa += 1
        try:
            if sayfa <= total_page:
                reviews_block = driver.find_elements(By.CSS_SELECTOR,
                                                     'div.hermes-ReviewCard-module-BJtQZy5Ub3goN_D0yNOP')

                old_element = reviews_block[0] if reviews_block else None

                success = go_to_page(sayfa)

                if success and old_element:
                    wait_page_change(old_element)
                sleep(2)
        except Exception as e:
            print("Sonraki sayfa yok veya tıklama hatası:", e)
            break

finally:
    # driver.quit()
    pass


if excel_datas:
    print(f"\nToplam {len(excel_datas)} satır veri işleniyor...")

    conn = sqlite3.connect("ecommerce.db")
    cursor = conn.cursor()

    try:
        first_row = excel_datas[0]

        # Ürün tablosu yoksa oluştur
        cursor.execute('''CREATE TABLE IF NOT EXISTS products (
                            product_id TEXT PRIMARY KEY,
                            product_url TEXT, product_title TEXT, average_rating REAL,
                            review_count INTEGER, total_page INTEGER, max_rating INTEGER,
                            review_count_in_page INTEGER)''')

        # Veriyi hazırla
        product_data = (
            first_row['product_id'], first_row['product_url'], first_row['product_title'],
            first_row['average_rating'], first_row['review_count'], first_row['total_page'],
            first_row['max_rating'], first_row['review_count_in_page']
        )

        # Ürünü ekle (Varsa atla/ignore)
        cursor.execute("INSERT OR IGNORE INTO products VALUES (?,?,?,?,?,?,?,?)", product_data)
        print("✅ Ürün bilgisi 'products' tablosuna kontrol edildi/eklendi.")

        # 2. ADIM: YORUM TABLOSUNU DOLDUR (Reviews)
        # DataFrame oluştur
        df = pd.DataFrame(excel_datas)

        # Sadece yorum sütunlarını ve product_id'yi seç
        review_cols = ['product_id', 'review_text', 'review_rating', 'page_no', 'review_position', 'review_date']
        df_reviews = df[review_cols]

        # Yorum tablosu yoksa oluştur (AUTOINCREMENT review_id ile)
        cursor.execute('''CREATE TABLE IF NOT EXISTS reviews (
                            review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            product_id TEXT, review_text TEXT, review_rating INTEGER,
                            page_no INTEGER, review_position INTEGER, review_date TEXT,
                            FOREIGN KEY(product_id) REFERENCES products(product_id))''')

        # Yorumları bas (review_id'yi göndermiyoruz, DB kendi üretiyor)
        for row in df_reviews.itertuples(index=False):
            cursor.execute("""
                INSERT INTO reviews
                (product_id, review_text, review_rating, page_no, review_position, review_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, row)

        conn.commit()

        print(f"✅ {len(df_reviews)} adet yorum 'reviews' tablosuna eklendi.")
        cursor.execute("SELECT COUNT(*) FROM reviews")
        count = cursor.fetchone()[0]
        print("DB toplam review:", count)

    except Exception as e:
        print(f"❌ Veritabanı Hatası: {e}")

    finally:
        conn.close()
else:
    print("⚠️ Hiç veri çekilemediği için kayıt yapılmadı.")
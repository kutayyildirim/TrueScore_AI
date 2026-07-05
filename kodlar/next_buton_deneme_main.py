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


#sistem sıkıntıları
# aynı ürünü bir daha link verdiğimde duplicate sorunu olur ve de tüm yorumları tekrar çeker bunu tarihe göre ayarlamam lazım

BASE_URL = 'https://www.hepsiburada.com/varol-gold-serisi-1200gr-nano-jel-yastik-50x70cm-p-HBV00000SAFZN-yorumlari'
#BASE_URL = 'https://www.hepsiburada.com/yunusoglu-home-isiya-dayanikli-cam-tencere-tava-kapagi-metal-kulplu-buhar-delikli-yedek-kapak-p-HBCV0000BU1LIV-yorumlari'

sayfa: int = 1
global_review_counter = 1
excel_datas = []
product_details = {}

SORT_PARAM = f'?sirala=star,asc&sayfa={sayfa}'
main_url = f"{BASE_URL}{SORT_PARAM}"

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


def reviews(current_page_number):
    global global_review_counter
    reviews_block = driver.find_elements(By.CSS_SELECTOR, 'div.hermes-ReviewCard-module-BJtQZy5Ub3goN_D0yNOP')

    if reviews_block:
        for review in reviews_block:
            # --- YORUM METNİ (GÜNCELLENDİ) ---
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

            # --- KAYIT (GÜNCELLENDİ: ARTIK BOŞ YORUMLARI DA ALIYORUZ) ---
            if review_text:
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

def go_to_page(page):
    try:
        wait = WebDriverWait(driver, 10)

        # span text'i page olan elementi bul
        page_button = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, f"//span[text()='{page}']")
            )
        )

        # parent li'ye tıkla (daha sağlam olur)
        driver.execute_script("arguments[0].click();", page_button)

    except Exception as e:
        print(f"Sayfa {page} tıklanamadı:", e)
        return False

    return True

try:
    cookies()
    review_count_in_page, total_page = product_info()

    while sayfa <= 300:
        scrolling_filtering()
        reviews(sayfa)
        sayfa += 1
        try:
            if sayfa <= 300:
                success = go_to_page(sayfa)

                if not success:
                    print("Sonraki sayfa yok veya hata")
                    break
                sleep(2)
        except Exception as e:
            print("Sonraki sayfa yok veya tıklama hatası:", e)
            break

finally:
    # driver.quit()
    pass

# --- DATABASE KISMI (TAMAMEN YENİLENDİ - 2 TABLO SİSTEMİ) ---
if excel_datas:
    print(f"\nToplam {len(excel_datas)} satır veri işleniyor...")

    conn = sqlite3.connect("ecommerce.db")
    cursor = conn.cursor()

    try:
        # 1. ADIM: ÜRÜN TABLOSUNU DOLDUR (Products)
        # Listeden sadece ilk satırı alıp ürün bilgilerini çekiyoruz (Hepsi aynı zaten)
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
        df_reviews.to_sql("reviews", conn, if_exists="append", index=False)

        print(f"✅ {len(df_reviews)} adet yorum 'reviews' tablosuna eklendi.")

    except Exception as e:
        print(f"❌ Veritabanı Hatası: {e}")

    finally:
        conn.close()
else:
    print("⚠️ Hiç veri çekilemediği için kayıt yapılmadı.")
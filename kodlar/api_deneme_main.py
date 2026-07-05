from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from time import sleep
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
import pandas as pd
from datetime import datetime
import sqlite3


def veri_cek_ve_kaydet(urun_linki, urun_id):
    print(f"🚀 {urun_id} ID'li ürün için Scraping başlatıldı...")

    # --- 1. VERİTABANINDAN MEVCUT YORUMLARI ÇEK (DUPLICATE ÖNLEYİCİ) ---
    mevcut_yorumlar = set()
    try:
        conn = sqlite3.connect("ecommerce.db")
        cursor = conn.cursor()
        # Tablo yoksa hata vermemesi için önce tablo kontrolü yapıyoruz
        cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='reviews'")
        if cursor.fetchone()[0] == 1:
            cursor.execute("SELECT review_text FROM reviews WHERE product_id = ?", (urun_id,))
            mevcut_yorumlar = {row[0] for row in cursor.fetchall() if row[0]}
        conn.close()
    except Exception as e:
        print(f"⚠️ Eski yorumlar okunurken hata: {e}")

    if mevcut_yorumlar:
        print(f"ℹ️ Veritabanında bu ürüne ait {len(mevcut_yorumlar)} adet kayıtlı yorum bulundu.")

    # --- 2. SELENIUM AYARLARI ---
    sayfa = 1
    excel_datas = []
    product_details = {}
    global_review_counter = 1
    stop_scraping = False  # Kazımayı erken durdurmak için bayrak

    # Eğer linkin sonunda "-yorumlari" yoksa ekleyelim (Güvenlik)
    if "-yorumlari" not in urun_linki:
        urun_linki = f"{urun_linki}-yorumlari"

    # Tarihe göre en yenileri çekiyoruz ki, eskilere rastladığımızda işlemi keselim
    SORT_PARAM = f'?sirala=enyeni&sayfa={sayfa}'
    main_url = f"{urun_linki}{SORT_PARAM}"

    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_argument('--headless')  # API arka planda çalışırken Chrome penceresi açılmaz
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 10)

    try:
        driver.get(main_url)

        # Çerezleri Kabul Et
        try:
            accept_button = wait.until(EC.presence_of_element_located((By.ID, "onetrust-accept-btn-handler")))
            accept_button.click()
            sleep(1)
        except:
            pass

        # --- 3. ÜRÜN BİLGİLERİNİ ÇEKME ---
        try:
            title_element = driver.find_element(By.XPATH, "//span[@itemprop='name']")
            product_title = title_element.text.replace('Değerlendirmeleri', '').strip()

            average_rating_element = driver.find_element(By.CSS_SELECTOR, 'span[itemprop="ratingValue"]')
            average_rating = float(average_rating_element.text.replace(',', '.'))

            review_count_element = driver.find_element(By.XPATH,
                                                       "//h1[contains(text(), '(') and contains(text(), 'Değerlendirme')]")
            review_count = int(review_count_element.text.split('(')[-1].split(' ')[0])

            review_count_in_page = 10
            max_rating = 5
            total_page = (review_count // review_count_in_page) + (
                1 if review_count % review_count_in_page != 0 else 0) if review_count > 0 else 1

            product_details = {
                'product_id': urun_id,
                'product_url': urun_linki,
                'product_title': product_title,
                'average_rating': average_rating,
                'review_count': review_count,
                'total_page': total_page,
                'max_rating': max_rating,
                'review_count_in_page': review_count_in_page
            }
        except Exception as e:
            print("Ürün bilgileri çekilemedi:", e)
            return False  # Bilgiler yoksa iptal et

        # --- 4. SAYFALARI DOLAŞMA VE YORUM ÇEKME ---
        while sayfa <= min(total_page, 300):  # Maksimum 300 sayfa (Hepsiburada sınırı)
            if stop_scraping:
                break

            # Scroll işlemi
            try:
                review_elements = driver.find_elements(By.CLASS_NAME, "hermes-ReviewCard-module-BJtQZy5Ub3goN_D0yNOP")
                if review_elements:
                    driver.execute_script("arguments[0].scrollIntoView(true);", review_elements[-1])
                    sleep(2)
            except:
                pass

            reviews_block = driver.find_elements(By.CSS_SELECTOR, 'div.hermes-ReviewCard-module-BJtQZy5Ub3goN_D0yNOP')

            if reviews_block:
                for review in reviews_block:
                    # Yorum Metni
                    try:
                        review_text_element = review.find_element(By.CSS_SELECTOR,
                                                                  'div.hermes-ReviewCard-module-KaU17BbDowCWcTZ9zzxw span').text
                        review_text = review_text_element.strip() if review_text_element and review_text_element.strip() != "NOT" else None
                    except:
                        review_text = None

                    # AKILLI KONTROL: Bu yorum zaten veritabanında var mı?
                    if review_text and review_text in mevcut_yorumlar:
                        print(
                            f"🛑 Zaten kayıtlı olan eski bir yoruma ulaşıldı. Sayfa {sayfa}'da kazıma işlemi durduruluyor.")
                        stop_scraping = True
                        break  # İç döngüyü (yorumları) kır

                    # Puan
                    try:
                        star_elements = review.find_element(By.CSS_SELECTOR,
                                                            'div.hermes-RatingPointer-module-UefD0t2XvgGWsKdLkNoX').find_elements(
                            By.CLASS_NAME, 'star')
                        review_rating = len(star_elements)
                    except:
                        review_rating = 0

                    # Tarih
                    try:
                        review_date_content = review.find_element(By.CSS_SELECTOR, 'span[content]').get_attribute(
                            'content')
                        formatted_date = datetime.strptime(review_date_content, '%Y-%m-%d').strftime(
                            '%d/%m/%Y') if review_date_content else None
                    except:
                        formatted_date = None

                    if review_text:
                        excel_datas.append({
                            'product_id': urun_id,
                            'review_text': review_text,
                            'review_rating': review_rating,
                            'page_no': sayfa,
                            'review_position': global_review_counter,
                            'review_date': formatted_date,
                        })
                        print(f"   [+] Yeni Yorum Eklendi: {review_rating} Puan | Sayfa {sayfa}")

                    global_review_counter += 1

            # Sonraki Sayfaya Geç
            if not stop_scraping:
                sayfa += 1
                try:
                    page_button = wait.until(EC.element_to_be_clickable((By.XPATH, f"//span[text()='{sayfa}']")))
                    driver.execute_script("arguments[0].click();", page_button)
                    sleep(2)
                except:
                    print("Sonraki sayfaya geçilemedi veya son sayfaya gelindi.")
                    break

    finally:
        driver.quit()  # Chrome'u kapatmayı unutmuyoruz, yoksa RAM dolar.

    # --- 5. YENİ VERİLERİ VERİTABANINA YAZMA ---
    if excel_datas:
        conn = sqlite3.connect("ecommerce.db")
        cursor = conn.cursor()
        try:
            # Products tablosu
            cursor.execute('''CREATE TABLE IF NOT EXISTS products (
                                product_id TEXT PRIMARY KEY, product_url TEXT, product_title TEXT, 
                                average_rating REAL, review_count INTEGER, total_page INTEGER, 
                                max_rating INTEGER, review_count_in_page INTEGER)''')

            p = product_details
            cursor.execute("INSERT OR IGNORE INTO products VALUES (?,?,?,?,?,?,?,?)",
                           (p['product_id'], p['product_url'], p['product_title'], p['average_rating'],
                            p['review_count'], p['total_page'], p['max_rating'], p['review_count_in_page']))

            # Reviews tablosu
            cursor.execute('''CREATE TABLE IF NOT EXISTS reviews (
                                review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                                product_id TEXT, review_text TEXT, review_rating INTEGER,
                                page_no INTEGER, review_position INTEGER, review_date TEXT,
                                FOREIGN KEY(product_id) REFERENCES products(product_id))''')

            df = pd.DataFrame(excel_datas)
            df_reviews = df[['product_id', 'review_text', 'review_rating', 'page_no', 'review_position', 'review_date']]
            df_reviews.to_sql("reviews", conn, if_exists="append", index=False)

            print(f"✅ {len(df_reviews)} adet YENİ yorum DB'ye eklendi.")
            return True
        except Exception as e:
            print(f"❌ Veritabanı Hatası: {e}")
            return False
        finally:
            conn.close()
    else:
        print("ℹ️ Çekilecek yeni yorum bulunamadı (Hepsi güncel).")
        return True  # Hata yok, sadece yeni veri yok. İşlem başarılı.


# Dosya tek başına çalıştırıldığında test etmek istersen (API dışında)
if __name__ == "__main__":
    test_link = "https://www.hepsiburada.com/varol-gold-serisi-1200gr-nano-jel-yastik-50x70cm-p-HBV00000SAFZN"
    veri_cek_ve_kaydet(test_link, "HBV00000SAFZN")
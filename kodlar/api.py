import re
import sqlite3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from analyzer import analiz_et
from api_deneme_main import veri_cek_ve_kaydet

app = FastAPI(title="TrueScore AI", description="Gerçek Müşteri Memnuniyeti Analiz API'si")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Artık ID değil, URL (Link) bekliyoruz
class ProductRequest(BaseModel):
    url: str


@app.post("/analiz-et/")
def analiz_baslat(istek: ProductRequest):

    match = re.search(r'HB[A-Z0-9]+', istek.url)
    if not match:
        return {"durum": "Başarısız",
                "hata_mesaji": "Geçerli bir ürün linki bulunamadı. Lütfen doğru linki girdiğinizden emin olun."}

    urun_id = match.group(0)

    # 2. VERİTABANINDA VAR MI KONTROLÜ
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    # Bu ID'ye ait yorum var mı sayıyoruz
    cursor.execute("SELECT COUNT(*) FROM reviews WHERE product_id = ?", (urun_id,))
    yorum_sayisi = cursor.fetchone()[0]
    conn.close()

    # 3. YORUM YOKSA SCRAPING (KAZIMA) İŞLEMİNİ BAŞLAT
    if yorum_sayisi == 0:
        print(f"Ürün veritabanında bulunamadı. Scraping başlatılıyor: {urun_id}")
        basarili_mi = veri_cek_ve_kaydet(istek.url, urun_id)

        if not basarili_mi:
            return {"durum": "Başarısız", "hata_mesaji": "Ürün yorumları internetten çekilirken bir hata oluştu."}

    # 4. MODEL İLE ANALİZ ET VE SONUCU GÖNDER
    gercek_sonuc = analiz_et(urun_id)

    if "hata" in gercek_sonuc:
        return {"durum": "Başarısız", "hata_mesaji": gercek_sonuc["hata"]}

    return {
        "urun_id": urun_id,
        "durum": "Başarılı",
        "analiz_sonucu": gercek_sonuc
    }

# uvicorn api:app --reload
# http://127.0.0.1:8000/docs
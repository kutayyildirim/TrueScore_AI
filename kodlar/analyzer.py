import sqlite3
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# 1. MODELİ DIŞARI ALDIK: Model sadece bir kere yüklenecek.
# Böylece her istekte beklemeyeceğiz, API çok hızlı çalışacak.
MODEL_YOLU = "./electra_production_model_V2"
tokenizer = AutoTokenizer.from_pretrained(MODEL_YOLU)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_YOLU)


def tahmin_uret(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=128)
    with torch.no_grad():
        outputs = model(**inputs)

    probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
    return torch.argmax(probs).item()


# 2. FONKSİYON ARTIK İÇİNE 'urun_id' ALIYOR
def analiz_et(urun_id):
    # Veritabanı Bağlantısı
    conn = sqlite3.connect('ecommerce.db')

    sorgu = """
        SELECT review_text, review_rating
        FROM reviews
        WHERE product_id = ?
        """

    try:
        df = pd.read_sql_query(sorgu, conn, params=(urun_id,))
    except Exception as e:
        return {"hata": f"Veritabanı bağlantı hatası: {e}"}
    finally:
        conn.close()

    # Veri Boş mu Kontrolü
    if df.empty:
        return {"hata": "Bu ürün ID'sine ait yorum bulunamadı."}

    # Veri Temizleme
    df = df.dropna(subset=['review_text'])
    df = df[df['review_text'].str.strip() != ""]

    if df.empty:
        return {"hata": "İncelenecek metin bulunamadı (Tüm yorumlar boş)."}

    # Modelin Tahmin Yürütmesi
    df['etiket'] = df['review_text'].apply(tahmin_uret)

    # 3. HESAPLAMA (Senin etiketleme mantığınla '0' Alakalı)
    alakali_df = df[df['etiket'] == 0]

    genel_ortalama = float(df['review_rating'].mean())

    if not alakali_df.empty:
        gercek_ortalama = float(alakali_df['review_rating'].mean())
        alakali_sayisi = int(len(alakali_df))
    else:
        gercek_ortalama = 0.0
        alakali_sayisi = 0

    # 4. PRINT YERİNE RETURN KULLANIYORUZ
    # API'ler yazıları okuyamaz, onlara veriyi böyle sözlük (JSON) gibi dönmeliyiz.
    return {
        "toplam_yorum": int(len(df)),
        "alakali_yorum_sayisi": alakali_sayisi,
        "genel_puan": round(genel_ortalama, 2),
        "gercek_puan": round(gercek_ortalama, 2),
        "fark": round(gercek_ortalama - genel_ortalama, 2)
    }
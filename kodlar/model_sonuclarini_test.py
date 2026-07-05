# import sqlite3
# import pandas as pd
# import torch
# from transformers import AutoTokenizer, AutoModelForSequenceClassification
#
#
# def analiz_et():
#     # 1. VERİTABANI BAĞLANTISI
#     conn = sqlite3.connect('ecommerce.db')
#
#     urun_id = "HBCV00009MYJZC"
#
#     sorgu = """
#         SELECT review_text, review_rating
#         FROM reviews
#         WHERE product_id = ?
#         """
#
#     # SADECE BU SATIR KALSIN: params=(urun_id,) kısmına dikkat,
#     # tek elemanlı bir tuple olduğu için sonuna virgül koymalısın.
#     try:
#         df = pd.read_sql_query(sorgu, conn, params=(urun_id,))
#         print(f"Veritabanından {len(df)} adet yorum çekildi.")
#     except Exception as e:
#         print(f"Hata oluştu: {e}")
#     finally:
#         conn.close()
#
#     # Eğer veri boş gelirse devam etmemesi için kontrol:
#     if df.empty:
#         print("Bu ürün ID'sine ait yorum bulunamadı. Lütfen ID'yi kontrol et.")
#         return
#
#
#
#     # 2. VERİ TEMİZLEME
#     # Yorum kısmı boş olanları (None/NaN) siliyoruz
#     df = df.dropna(subset=['review_text'])
#     # Sadece içinde metin olanları filtreleyelim (boş stringler dahil olmasın)
#     df = df[df['review_text'].str.strip() != ""]
#
#     print(f"Toplam {len(df)} adet yorum analiz edilecek...")
#
#     # 3. MODELİ YÜKLEME
#     # Drive'dan indirdiğin klasörün yolunu buraya yaz
#     model_yolu = "./electra_production_model_V2"
#     tokenizer = AutoTokenizer.from_pretrained(model_yolu)
#     model = AutoModelForSequenceClassification.from_pretrained(model_yolu)
#
#     # 4. TAHMİN FONKSİYONU
#     def tahmin_uret(text):
#         inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=128)
#         with torch.no_grad():
#             outputs = model(**inputs)
#
#         # En yüksek olasılıklı sınıfı seç (0: Alakasız, 1: Alakalı)
#         probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
#         return torch.argmax(probs).item()
#
#     # 5. MODELİ VERİLERE UYGULA
#     print("Model tahmin yürütüyor, bu işlem veriye göre biraz sürebilir...")
#     df['etiket'] = df['review_text'].apply(tahmin_uret)
#
#     # 6. ANALİZ VE SONUÇ
#     # Sadece alakalı (1) olanların puan ortalaması
#     alakali_df = df[df['etiket'] == 0]
#
#     if not alakali_df.empty:
#         gercek_ortalama = alakali_df['review_rating'].mean()
#         genel_ortalama = df['review_rating'].mean()
#
#         print("\n--- ANALİZ SONUÇLARI ---")
#         print(f"Toplam Yorum: {len(df)}")
#         print(f"Alakalı Bulunan Yorum Sayısı: {len(alakali_df)}")
#         print(f"Genel Puan Ortalaması: {genel_ortalama:.2f}")
#         print(f"Alakalı Yorumların Puan Ortalaması (Gerçek Puan): {gercek_ortalama:.2f}")
#         print(f"Fark: {gercek_ortalama - genel_ortalama:.2f}")
#     else:
#         print("Hiç alakalı yorum bulunamadı.")
#
#
#     # Sadece alakalı (0) olarak işaretlenen ilk 10 yorumu ve puanını görelim
#     print("\n--- MODELİN 'ALAKALI' DEDİĞİ BAZI YORUMLAR ---")
#     # pd.set_option ile metnin tamamını görmeyi sağlayalım
#     pd.set_option('display.max_colwidth', None)
#     print(alakali_df[['review_text', 'review_rating']].head(10))
#
#     # Bir de modelin 'ALAKASIZ' dediklerine bakalım (doğru mu ayırmış?)
#     alakasiz_df = df[df['etiket'] != 0]
#     print("\n--- MODELİN 'ALAKASIZ' DEDİĞİ YORUMLAR ---")
#     print(alakasiz_df[['review_text', 'review_rating']])
#
#
# if __name__ == "__main__":
#     analiz_et()

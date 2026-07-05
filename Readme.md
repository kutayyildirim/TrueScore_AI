🤖 TrueAiScore: E-Ticaret Yorum Filtreleme ve Gerçek Puan Motoru
E-ticaret platformlarındaki kullanıcı yorumları, satın alma kararlarını etkileyen en kritik faktörlerden biridir. Ancak botlar tarafından oluşturulan sahte yorumlar ve ürünün kalitesinden bağımsız olan lojistik/kargo şikayetleri, ürünlerin gerçek performansını gölgelemektedir.

TrueAiScore, e-ticaret sitelerinden kazınan ham yorum verilerini Doğal Dil İşleme (NLP) ve Makine Öğrenimi (ML) algoritmalarıyla analiz ederek bilgi kirliliğini ortadan kaldıran ve ürünler için manipülasyondan arındırılmış şeffaf bir "Gerçek Puan" hesaplayan bir yapay zeka motorudur.

🚀 Projenin Temel Özellikleri
Dinamik Veri Kazıma: Selenium altyapısı ile e-ticaret ürün sayfalarından (örneğin Hepsiburada) yorumların, tarihlerin ve puanların otomatize şekilde toplanması.

NLP Tabanlı Metin Ön İşleme: Gürültülü metinlerin durdurma kelimelerinden (stopwords), emojilerden ve noktalama işaretlerinden temizlenerek köklerine (lemmatization) indirgenmesi.

İki Aşamalı AI Filtreleme Süzgeci:

Bağlam Analizi: Yorumun ürünle mi yoksa dış faktörlerle mi ilgili olduğunun tespiti.

Organiklik Analizi: Yorumun gerçek bir insan tarafından mı yoksa bot/spam olarak mı yazıldığının tespiti.

Şeffaf Skorlama: Sadece "Gerçek" ve "Alakalı" etiketini alan yorumların puanları baz alınarak nihai TrueAiScore değerinin hesaplanması.

📊 Veri Etiketleme ve Filtreleme Mantığı
Projenin temel amacı, klasik duygu analizinin (Sentiment Analysis) ötesine geçerek yorumun bağlamını anlamaktır. Modelimizin eğitildiği etiketleme stratejisine dair örnekler aşağıda sunulmuştur:

🟢 1. Alakalı (Puanlamaya Dahil Edilir)
Ürünün fiziksel özelliklerini, kullanımını, donanımını veya kalitesini değerlendiren organik yorumlardır.

"Ürünün malzeme kalitesi çok iyi, şarjı da anlatıldığı gibi 2 gün gidiyor. Kesinlikle tavsiye ederim."

🔴 2. Alakasız / Lojistik Şikayeti (Puanlamadan Çıkarılır)
Ürün kusursuz olsa bile, kargo firmasının hatası, paketlemenin ezilmesi veya satıcının gecikmesi yüzünden verilen adaletsiz düşük (veya yüksek) puanlardır.

"Ürün elime 5 günde zor ulaştı, X kargo yine şaşırtmadı, kutusu da ezilmişti. 1 yıldız veriyorum."

🔴 3. Sahte / Bot Yorum (Puanlamadan Çıkarılır)
Satıcıların puan yükseltmek veya rakipleri karalamak için bot hesaplarla attırdığı, mantıksal bir bağlam içermeyen manipülatif spam verilerdir.

"harika mükemmel harika mükemmel alın aldırın süper"

🧠 Model Mimarisi ve Performans Metrikleri
Proje kapsamında geleneksel Makine Öğrenimi algoritmalarından, gelişmiş Transformer tabanlı (Transfer Learning) dil modellerine kadar geniş bir yelpaze test edilmiş ve sonuçları karşılaştırılmıştır.

Test edilen ve metrikleri (Accuracy, Confusion Matrix) /Model_Sonuclari_Metrikleri klasöründe sunulan modeller şunlardır:

Geleneksel ML Modelleri: Decision Tree (Karar Ağacı - Sınıflandırma görevinde aşırı öğrenmeye düşmeden oldukça istikrarlı sonuçlar vermiştir), Logistic Regression, Naive Bayes, SVM, XGBoost, CatBoost.

Ensemble (Topluluk) Modelleri: Voltran, Random Search optimizasyonları.

Büyük Dil Modelleri (Transfer Learning): ELECTRA, BERTürk, ConvBERT, RoBERTa.

(Modellerin eğitim süreçlerini, hiperparametre ayarlarını ve test kodlarını /collab_model_kodlari dizinindeki Jupyter Notebook dosyalarında, uygulama arka plan kodlarını ise /kodlar dizininde inceleyebilirsiniz.)

🔮 Gelecek Adımlar ve Entegrasyon (B2B)
TrueAiScore, son kullanıcı cihazlarında lokal olarak çalışmak (veya kurulmak) üzere değil, büyük sistemlerin kalbine entegre edilmek üzere tasarlanmış ölçeklenebilir bir analiz motorudur. Bu doğrultuda hedeflenen gelecek adımlar:

E-Ticaret Platformu Entegrasyonu (API): Pazar yerlerinin kendi yorum sistemlerini temizlemek ve müşterilerine daha şeffaf bir alışveriş deneyimi sunmak için doğrudan backend sistemlerine API olarak entegre edilmesi.

Tarayıcı Eklentisi (Browser Extension): Tüketiciler e-ticaret sitelerinde gezinirken, arka planda TrueAiScore sunucularına istek atarak anlık "Gerçek Puan" analizi yapabilen bir Chrome/Edge eklentisine dönüştürülmesi.

LLM Tabanlı Sarkazm Tespiti: Gelecekte modelin ince ayar (fine-tuning) süreçlerinin genişletilerek, Türkçedeki kinayeli (sarkastik) yorumların çok daha yüksek bir hassasiyetle yakalanması.
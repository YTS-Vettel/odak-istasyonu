# 🚀 Odak İstasyonu V4.1

Spotify API entegrasyonu ile geliştirilmiş, çalışma seanslarınızı müzikle senkronize ederek verimliliğinizi artıran profesyonel bir odaklanma otomasyonudur.

## 🛠️ Proje Mimarisi

### 1. 🧠 Ana Kontrol Merkezi (`main.py`)
Uygulamanın çekirdek yazılımıdır. 
* **Güvenli Erişim:** Spotify **PKCE** (Proof Key for Code Exchange) protokolünü kullanarak kullanıcı şifresine ihtiyaç duymadan güvenli bağlantı kurar.
* **Akıllı Otomasyon:** Belirlenen odaklanma süresi tamamlandığında müzik akışını otomatik olarak durdurarak kullanıcıyı uyarır.

### 2. 🛡️ Güvenlik ve Gizlilik (`.gitignore`)
Projenin güvenlik kalkanıdır. Aşağıdaki hassas ve yerel dosyaların GitHub ortamına sızmasını engeller:
* `.cache` (Spotify erişim anahtarları)
* `focus_settings.json` (Kişisel tercihler)
* `.idea/` ve `__pycache__` (Sistem dosyaları)

### 3. 📦 Bağımlılıklar (`requirements.txt`)
Projenin sorunsuz çalışması için gerekli kütüphane listesini içerir:
* `spotipy`: Spotify Web API istemcisi.
* `colorama`: Terminal arayüzü görselleştirme.
* `art`: ASCII sanat tasarımları.

## 🚀 Kurulum ve Başlatma

1. **Depoyu bilgisayarınıza klonlayın:**
   ```bash
   git clone [https://github.com/YTS-Vettel/odak-istasyonu-v41.git](https://github.com/YTS-Vettel/odak-istasyonu-v41.git)

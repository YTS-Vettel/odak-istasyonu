import cv2
import time
import threading
import customtkinter as ctk
import spotipy
from spotipy.oauth2 import SpotifyPKCE
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from tkinter import messagebox
import json
import os

# --- GÜVENLİ TİCARİ SPOTIFY AYARLARI ---
SPOTIPY_CLIENT_ID = 'ce2dc70c2bdd425bbd4a9203dd7c39f5'
SPOTIPY_REDIRECT_URI = 'http://127.0.0.1:8888/callback'
scope = "user-modify-playback-state user-read-playback-state user-top-read"

ctk.set_appearance_mode("dark")


class OdakIstasyonu(ctk.CTk):
    CONFIG_FILE = "focus_settings.json"

    def __init__(self):
        super().__init__()
        self.title("Odak İstasyonu - V41 (Crash-Proof)")
        self.geometry("600x820")

        self.is_running = False
        self.driver = None
        self.sp = None
        self.top_tracks_dict = {}
        self.is_music_paused = False
        self.is_video_active = False
        self.driver_ready = False

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.label = ctk.CTkLabel(self, text="ODAK İSTASYONU", font=("Helvetica", 24, "bold"), text_color="#1DB954")
        self.label.pack(pady=(15, 5))

        self.tabview = ctk.CTkTabview(self, width=540, height=480, segmented_button_selected_color="#1DB954")
        self.tabview.pack(pady=5)

        self.tabview.add("YouTube / GIF Modu")
        self.tabview.add("Spotify Modu")
        self.tabview.add("Yardım & Rehber")

        # --- YOUTUBE / GIF İÇERİĞİ ---
        self.yt_label = ctk.CTkLabel(self.tabview.tab("YouTube / GIF Modu"),
                                     text="Odak bozulunca tetiklenecek Video veya GIF:", font=("Helvetica", 14))
        self.yt_label.pack(pady=10)
        self.media_url_entry = ctk.CTkEntry(self.tabview.tab("YouTube / GIF Modu"), placeholder_text="Link girin...",
                                            width=400)

        son_link = self.ayarlari_yukle()
        self.media_url_entry.insert(0, son_link)
        self.media_url_entry.pack(pady=10)

        # --- SPOTIFY İÇERİĞİ ---
        self.baglanti_durumu = ctk.CTkLabel(self.tabview.tab("Spotify Modu"), text="Durum: Bekleniyor...",
                                            text_color="orange", font=("Helvetica", 12, "bold"))
        self.baglanti_durumu.pack(pady=(10, 5))

        self.sp_login_btn = ctk.CTkButton(self.tabview.tab("Spotify Modu"), text="Spotify Hesabına Bağlan",
                                          fg_color="#1DB954", hover_color="#1ed760", command=self.spotify_giris_yap)
        self.sp_login_btn.pack(pady=5)

        self.device_var = ctk.StringVar(value="Otomatik (Aktif Cihaz)")
        self.device_menu = ctk.CTkOptionMenu(self.tabview.tab("Spotify Modu"),
                                             values=["Otomatik (Aktif Cihaz)", "Bilgisayar (PC)", "Telefon"],
                                             variable=self.device_var, fg_color="#1DB954")
        self.device_menu.pack(pady=10)

        self.link_frame = ctk.CTkFrame(self.tabview.tab("Spotify Modu"), fg_color="transparent")
        self.link_frame.pack(pady=5)

        self.sp_link_entry = ctk.CTkEntry(self.link_frame, placeholder_text="Boşsa son şarkıdan devam eder...",
                                          width=320)
        self.sp_link_entry.pack(side="left", padx=5)

        self.manuel_cal_btn = ctk.CTkButton(self.link_frame, text="Çal", width=60, fg_color="#1DB954",
                                            command=self.manuel_link_tetikle)
        self.manuel_cal_btn.pack(side="left", padx=5)

        self.fav_button = ctk.CTkButton(self.tabview.tab("Spotify Modu"), text="Top 10 Şarkımı Getir",
                                        command=self.favorileri_getir, fg_color="#191414", border_width=1,
                                        border_color="#1DB954")
        self.fav_button.pack(pady=10)

        self.top10_var = ctk.StringVar(value="Liste seçin...")
        self.top10_menu = ctk.CTkOptionMenu(self.tabview.tab("Spotify Modu"), values=["Liste seçin..."],
                                            variable=self.top10_var, command=self.top10_secildi, width=300)
        self.top10_menu.pack(pady=5)

        # --- YARDIM & REHBER ---
        help_text = """📌 ODAK İSTASYONU REHBERİ

🎵 SPOTIFY MODU
• Önce bağlantı kurun, ardından "OTURUMU BAŞLAT" butonuna basın.
• Oturum başlamadan şarkı seçemez veya değiştiremezsiniz.
• Odağınız koparsa müzik durur!

📺 YOUTUBE / GIF MODU
• Odak bozulduğunda (5 sn sabır süresi sonrası) video tam ekran fırlar.
• Odaklandığınızda pencere yavaşça aşağı kayarak gizlenir.
• Güvenlik gereği sadece http:// veya https:// ile başlayan gerçek linkler çalışır.

Geliştirici: Yasir Tapar - YTS_Vettel"""

        self.help_textbox = ctk.CTkTextbox(self.tabview.tab("Yardım & Rehber"), width=480, height=220,
                                           font=("Helvetica", 12))
        self.help_textbox.pack(pady=10, padx=10)
        self.help_textbox.insert("0.0", help_text)
        self.help_textbox.configure(state="disabled")

        # --- ANA KONTROLLER ---
        self.camera_mode = ctk.CTkSwitch(self, text="Kamera Görüntüsünü Göster")
        self.camera_mode.pack(pady=10)

        self.start_button = ctk.CTkButton(self, text="OTURUMU BAŞLAT", command=self.toggle_system, height=50,
                                          font=("Helvetica", 16, "bold"), fg_color="#1DB954")
        self.start_button.pack(pady=10)

        self.exit_button = ctk.CTkButton(self, text="UYGULAMAYI KAPAT", command=self.on_closing, height=32,
                                         fg_color="#D32F2F")
        self.exit_button.pack(pady=(5, 5))

        self.credits_label = ctk.CTkLabel(self, text="Geliştirici: Yasir Tapar - YTS_Vettel",
                                          font=("Helvetica", 10, "italic"), text_color="gray")
        self.credits_label.pack(pady=(0, 10))

    # --- SPOTIFY OAUTH ---
    def spotify_giris_yap(self):
        try:
            auth_manager = SpotifyPKCE(client_id=SPOTIPY_CLIENT_ID, redirect_uri=SPOTIPY_REDIRECT_URI, scope=scope)
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
            kullanici = self.sp.current_user()
            kullanici_adi = kullanici.get('display_name', 'Kullanıcı')
            self.baglanti_durumu.configure(text=f"Durum: Bağlandı ({kullanici_adi})", text_color="#1DB954")
            self.sp_login_btn.configure(text="Hesap Bağlandı", state="disabled", fg_color="gray")
        except Exception as e:
            self.sp = None
            messagebox.showerror("Bağlantı Hatası", "Giriş yapılamadı.")

    def ayarlari_yukle(self):
        default_link = "https://www.youtube.com/watch?v=ZY4bKcczPLw"
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f).get("son_medya_linki", default_link)
            except:
                return default_link
        return default_link

    def ayarlari_kaydet(self):
        # Kaydetmeden önce basit bir temizlik yapıyoruz
        link = self.media_url_entry.get().strip()
        if len(link) > 300: link = "https://www.youtube.com/watch?v=ZY4bKcczPLw"  # Çok uzunsa defaulta dön

        with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"son_medya_linki": link}, f)

    # --- KONTROL MEKANİZMALARI (CRASH ÖNLEYİCİ) ---
    def manuel_link_tetikle(self):
        if not self.is_running:
            messagebox.showwarning("Oturum Kapalı", "Şarkı çalmak için önce 'OTURUMU BAŞLAT' butonuna basmalısınız!")
            return
        if not self.sp:
            messagebox.showwarning("Uyarı", "Lütfen önce Spotify hesabınıza bağlanın!")
            return

        raw_link = self.sp_link_entry.get().strip()
        if not raw_link: return

        # GÜNCEL: Spotify Manuel Link Sınırı (Maximum 150 Karakter)
        if len(raw_link) > 150:
            messagebox.showerror("Güvenlik", "Girdiğiniz Spotify linki çok uzun! Çökme riskine karşı engellendi.")
            self.sp_link_entry.delete(0, 'end')
            return

        try:
            uri = self.linki_uriye_cevir(raw_link)
            if not uri:
                messagebox.showerror("Hata", "Geçersiz Spotify linki formatı!")
                self.sp_link_entry.delete(0, 'end')
                return

            hid = self.hedef_cihaz_id_bul()
            if "track" in uri:
                self.sp.start_playback(device_id=hid, uris=[uri]) if hid else self.sp.start_playback(uris=[uri])
            else:
                self.sp.start_playback(device_id=hid, context_uri=uri) if hid else self.sp.start_playback(
                    context_uri=uri)
            self.is_music_paused = False
        except Exception as e:
            print("Spotify Çalma Hatası:", e)

    def top10_secildi(self, secim):
        if not self.is_running:
            messagebox.showwarning("Oturum Kapalı",
                                   "Şarkı değiştirmek için önce 'OTURUMU BAŞLAT' butonuna basmalısınız!")
            return
        uri = self.top_tracks_dict.get(secim, "")
        if uri and self.sp:
            self.sp_link_entry.delete(0, 'end');
            self.sp_link_entry.insert(0, uri)
            hid = self.hedef_cihaz_id_bul()
            try:
                self.sp.start_playback(device_id=hid, uris=[uri]) if hid else self.sp.start_playback(
                    uris=[uri]); self.is_music_paused = False
            except:
                pass

    def favorileri_getir(self):
        if not self.sp: messagebox.showwarning("Uyarı", "Lütfen önce Spotify hesabınıza bağlanın!"); return
        try:
            top_tracks = self.sp.current_user_top_tracks(limit=10, time_range='short_term')
            if top_tracks['items']:
                self.top_tracks_dict.clear()
                display_list = [f"{i + 1}. {t['artists'][0]['name']} - {t['name']}" for i, t in
                                enumerate(top_tracks['items'])]
                for i, t in enumerate(top_tracks['items']): self.top_tracks_dict[display_list[i]] = t['uri']
                self.top10_menu.configure(values=display_list)
                messagebox.showinfo("Başarılı", "Top 10 şarkın yüklendi!")
        except:
            pass

    def load_browser_thread(self):
        try:
            opt = Options()
            opt.add_argument("--autoplay-policy=no-user-gesture-required")
            opt.add_argument("--window-position=-10000,-10000")
            self.driver = webdriver.Chrome(options=opt)
            self.driver.minimize_window()
            self.driver.get(self.media_url_entry.get().strip())
            time.sleep(2)
            self.driver_ready = True
        except:
            self.driver_ready = True

    def animate_minimize_thread(self):
        try:
            sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
            self.driver.execute_script("var v=document.getElementsByTagName('video'); if(v.length>0) v[0].pause();")
            for step in range(1, 16):
                y_pos = int((sh / 15) * step)
                self.driver.set_window_rect(0, y_pos, sw, sh - y_pos)
                time.sleep(0.01)
            self.driver.minimize_window()
            self.is_video_active = False
        except:
            self.is_video_active = False

    def linki_uriye_cevir(self, link):
        link = link.strip().split('?')[0]
        if link.startswith("spotify:"): return link
        parts = link.split("/")
        for i, part in enumerate(parts):
            if part in ["track", "album", "playlist", "artist"]:
                if i + 1 < len(parts): return f"spotify:{part}:{parts[i + 1]}"
        return None

    def hedef_cihaz_id_bul(self):
        try:
            secim = self.device_var.get()
            if secim == "Otomatik (Aktif Cihaz)": return None
            cihazlar = self.sp.devices().get('devices', [])
            hedef_id, aktif_id = None, None
            for cihaz in cihazlar:
                if cihaz.get('is_active'): aktif_id = cihaz['id']
                if secim == "Telefon" and cihaz['type'] == 'Smartphone':
                    hedef_id = cihaz['id']
                elif secim == "Bilgisayar (PC)" and cihaz['type'] == 'Computer':
                    hedef_id = cihaz['id']
            return hedef_id if hedef_id else aktif_id
        except:
            return None

    def toggle_system(self):
        if not self.is_running:
            mode = self.tabview.get()

            # GÜNCEL: YouTube / GIF Güvenlik Duvarı
            if mode == "YouTube / GIF Modu":
                yt_link = self.media_url_entry.get().strip()
                if not yt_link:
                    messagebox.showerror("Hata", "Lütfen bir medya linki girin!")
                    return
                if len(yt_link) > 300:
                    messagebox.showerror("Güvenlik", "Girdiğiniz link çok uzun! Programın çökmemesi için engellendi.")
                    self.media_url_entry.delete(0, 'end')
                    return
                if not (yt_link.startswith("http://") or yt_link.startswith("https://")):
                    messagebox.showerror("Hata",
                                         "Lütfen 'http://' veya 'https://' ile başlayan geçerli bir link girin.")
                    return

            # GÜNCEL: Spotify Güvenlik Duvarı
            if mode == "Spotify Modu":
                sp_link = self.sp_link_entry.get().strip()
                if sp_link and len(sp_link) > 150:
                    messagebox.showerror("Güvenlik", "Girdiğiniz Spotify linki çok uzun!")
                    self.sp_link_entry.delete(0, 'end')
                    return

            self.is_running = True
            self.start_button.configure(text="OTURUMU BİTİR", fg_color="#E91E63")
            self.ayarlari_kaydet()

            if mode == "Spotify Modu" and self.sp:
                hid = self.hedef_cihaz_id_bul()
                uri = None
                if sp_link:
                    uri = self.linki_uriye_cevir(sp_link)
                try:
                    if uri:
                        if "track" in uri:
                            self.sp.start_playback(device_id=hid, uris=[uri]) if hid else self.sp.start_playback(
                                uris=[uri])
                        else:
                            self.sp.start_playback(device_id=hid, context_uri=uri) if hid else self.sp.start_playback(
                                context_uri=uri)
                    else:
                        self.sp.start_playback(device_id=hid) if hid else self.sp.start_playback()
                    self.is_music_paused = False
                except:
                    pass

            self.thread = threading.Thread(target=self.run_logic, daemon=True)
            self.thread.start()
        else:
            self.is_running = False
            self.start_button.configure(text="OTURUMU BAŞLAT", fg_color="#1DB954")
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
            if self.sp:
                try:
                    hid = self.hedef_cihaz_id_bul(); self.sp.pause_playback(
                        device_id=hid) if hid else self.sp.pause_playback()
                except:
                    pass

    def on_closing(self):
        self.is_running = False
        self.ayarlari_kaydet()
        if self.sp:
            try:
                hid = self.hedef_cihaz_id_bul(); self.sp.pause_playback(
                    device_id=hid) if hid else self.sp.pause_playback()
            except:
                pass
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
        self.destroy()

    def run_logic(self):
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        cap = cv2.VideoCapture(0)
        focus_lost_start, focus_back_start = None, None
        is_yt_playing = False
        mode = self.tabview.get()

        if mode == "YouTube / GIF Modu":
            self.driver_ready = False
            threading.Thread(target=self.load_browser_thread, daemon=True).start()
        else:
            self.driver_ready = True

        while self.is_running:
            ret, frame = cap.read()
            if not ret: break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            focus_active = False
            if not self.driver_ready and mode == "YouTube / GIF Modu":
                cv2.putText(frame, "TARAYICI HAZIRLANIYOR...", (20, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 165, 0),
                            2)
            for (x, y, w, h) in faces:
                roi_gray = gray[y: y + int(h / 1.8), x: x + w]
                if len(eye_cascade.detectMultiScale(roi_gray, 1.1, 10)) >= 1: focus_active = True

            mode = self.tabview.get()
            if not focus_active:
                focus_back_start = None
                if focus_lost_start is None: focus_lost_start = time.time()
                lost_time = round(5 - (time.time() - focus_lost_start), 1)
                if lost_time > 0 and self.driver_ready:
                    cv2.putText(frame, f"ODAK KAYBI! TESPIT: {lost_time}s", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                                (0, 255, 255), 2)
                if time.time() - focus_lost_start > 5 and self.driver_ready:
                    if mode == "YouTube / GIF Modu" and self.driver and not is_yt_playing:
                        try:
                            self.driver.set_window_rect(0, 0, self.winfo_screenwidth(), self.winfo_screenheight())
                            self.driver.execute_script(
                                "var v=document.getElementsByTagName('video'); if(v.length>0) v[0].play();")
                            is_yt_playing = True
                        except:
                            pass
                    elif mode == "Spotify Modu" and self.sp and not self.is_music_paused:
                        try:
                            hid = self.hedef_cihaz_id_bul(); self.sp.pause_playback(
                                device_id=hid) if hid else self.sp.pause_playback(); self.is_music_paused = True
                        except:
                            pass
            else:
                focus_lost_start = None
                if mode == "YouTube / GIF Modu" and self.driver and is_yt_playing:
                    if focus_back_start is None: focus_back_start = time.time()
                    rem = round(5 - (time.time() - focus_back_start), 1)
                    if rem > 0: cv2.putText(frame, f"ODAKLANDIN! ALTA ALMAYA: {rem}s", (50, 50),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    if time.time() - focus_back_start > 5:
                        threading.Thread(target=self.animate_minimize_thread, daemon=True).start()
                        is_yt_playing = False;
                        focus_back_start = None
                elif mode == "Spotify Modu" and self.sp and self.is_music_paused:
                    try:
                        hid = self.hedef_cihaz_id_bul(); self.sp.start_playback(
                            device_id=hid) if hid else self.sp.start_playback(); self.is_music_paused = False
                    except:
                        pass

            if self.camera_mode.get():
                cv2.imshow('Odak Istasyonu - Yasir Tapar', frame); cv2.waitKey(1)
            else:
                cv2.destroyAllWindows()

        cap.release();
        cv2.destroyAllWindows()


if __name__ == "__main__":
    app = OdakIstasyonu();
    app.mainloop()
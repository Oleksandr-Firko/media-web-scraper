import os
import threading
import requests
import time
from datetime import datetime
from tkinter import *
from tkinter import messagebox, filedialog, ttk
import webbrowser
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class MediaDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Media Scraper")
        self.root.geometry("500x300")
        self.root.configure(bg="#2e2e2e")

        self.url_var = StringVar()
        self.status_var = StringVar(value="Ready")
        self.download_images = BooleanVar(value=True)
        self.download_videos = BooleanVar(value=True)
        self.download_gifs = BooleanVar(value=True)
        self.scroll_delay = DoubleVar(value=2.0)

        self.driver = None
        self.img_urls = set()
        self.video_urls = set()
        self.gif_urls = set()
        self.scrolling = False

        self.setup_ui()

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", background="#2e2e2e", foreground="white")
        style.configure("TButton", padding=6, relief="flat", background="#4CAF50", foreground="white")
        style.configure("TCheckbutton", background="#2e2e2e", foreground="white", font=("Arial", 10))

        Label(self.root, text="🔗 Page URL:", bg="#2e2e2e", fg="white").pack(pady=5)
        Entry(self.root, textvariable=self.url_var, width=70, bg="#444", fg="white", insertbackground='white').pack(pady=5)

        check_frame = Frame(self.root, bg="#2e2e2e")
        check_frame.pack(pady=5)

        self.photo_checkbox = Checkbutton(check_frame, text="📸 Download photos", variable=self.download_images, bg="#2e2e2e", fg="white", selectcolor="#4CAF50")
        self.photo_checkbox.pack(side=LEFT, padx=10)
        self.video_checkbox = Checkbutton(check_frame, text="🎥 Download videos", variable=self.download_videos, bg="#2e2e2e", fg="white", selectcolor="#4CAF50")
        self.video_checkbox.pack(side=LEFT, padx=10)
        self.gif_checkbox = Checkbutton(check_frame, text="🎞 Download GIFs", variable=self.download_gifs, bg="#2e2e2e", fg="white", selectcolor="#4CAF50")
        self.gif_checkbox.pack(side=LEFT, padx=10)

        delay_frame = Frame(self.root, bg="#2e2e2e")
        delay_frame.pack(pady=5)
        Label(delay_frame, text="⏱️ Scroll delay (sec):", bg="#2e2e2e", fg="white").pack(side=LEFT, padx=5)
        Entry(delay_frame, textvariable=self.scroll_delay, width=10, bg="#444", fg="white", insertbackground='white').pack(side=LEFT)

        self.progress = ttk.Progressbar(self.root, orient=HORIZONTAL, length=400, mode='determinate', style="Horizontal.TProgressbar")
        self.progress.pack(pady=10)

        button_frame = Frame(self.root, bg="#2e2e2e")
        button_frame.pack(pady=10)
        Button(button_frame, text="🚀 Start", command=self.start).pack(side=LEFT, padx=5)
        Button(button_frame, text="⛔ Stop scrolling", command=self.stop_scroll).pack(side=LEFT, padx=5)
        Button(button_frame, text="💾 Download found", command=self.download).pack(side=LEFT, padx=5)

        Label(self.root, textvariable=self.status_var, fg="lightgreen", bg="#2e2e2e").pack(pady=5)

        credit_frame = Frame(self.root, bg="#2e2e2e")
        credit_frame.pack(side=BOTTOM, pady=5)
        Label(credit_frame, text="Author: Oleksandr Firko | GitHub: Oleksandr-Firko", fg="lightgreen", bg="#2e2e2e").pack(side=LEFT, padx=5)
        Button(credit_frame, text="GitHub", command=lambda: webbrowser.open("https://github.com/Oleksandr-Firko")).pack(side=LEFT)

    def update_status(self, msg):
        self.status_var.set(msg)
        print(msg)
        with open("media_downloader.log", "a", encoding="utf-8") as log_file:
            log_file.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n")

    def connect_driver(self):
        options = Options()
        options.debugger_address = "127.0.0.1:9222"
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122 Safari/537.36")
        self.driver = webdriver.Chrome(options=options)

    def start(self):
        threading.Thread(target=self._start_process).start()

    def _start_process(self):
        url = self.url_var.get().strip()
        if not url:
            self.update_status("❌ Please enter a URL")
            return

        self.connect_driver()
        self.driver.get(url)
        time.sleep(3)
        self.img_urls = set()
        self.video_urls = set()
        self.gif_urls = set()
        self.scrolling = True
        self.update_status("🔃 Scrolling...")
        self.auto_scroll_and_collect()

    def stop_scroll(self):
        self.scrolling = False
        self.update_status(f"🛑 Scrolling stopped. Photos: {len(self.img_urls)}, Videos: {len(self.video_urls)}, GIFs: {len(self.gif_urls)}")

    def fix_url(self, src):
        if not src:
            return None
        if src.startswith("//"):
            return "https:" + src
        if src.startswith("/") and not src.startswith("//"):
            base = self.driver.current_url.split("/")[0] + "//" + self.driver.current_url.split("/")[2]
            return base + src
        if src.startswith("http"):
            return src
        return None

    def auto_scroll_and_collect(self):
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        while self.scrolling:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(self.scroll_delay.get())

            imgs = self.driver.find_elements("tag name", "img")
            for img in imgs:
                src = img.get_attribute("src") or img.get_attribute("data-src")
                src = self.fix_url(src)
                if src and any(ext in src for ext in [".jpg", ".jpeg", ".png"]):
                    self.img_urls.add(src)
                if src and ".gif" in src:
                    self.gif_urls.add(src)

            videos = self.driver.find_elements("tag name", "video")
            for video in videos:
                src = video.get_attribute("src") or video.get_attribute("data-src")
                src = self.fix_url(src)
                if src and any(ext in src for ext in [".mp4", ".webm"]):
                    self.video_urls.add(src)

            sources = self.driver.find_elements("tag name", "source")
            for src_elem in sources:
                src = src_elem.get_attribute("src") or src_elem.get_attribute("data-src")
                src = self.fix_url(src)
                if src and any(ext in src for ext in [".mp4", ".webm"]):
                    self.video_urls.add(src)

            meta_video_tags = self.driver.find_elements("xpath", '//meta[starts-with(@property, "og:video") or starts-with(@property, "og:video:url") or starts-with(@property, "og:video:secure_url")]')
            for tag in meta_video_tags:
                src = tag.get_attribute("content")
                src = self.fix_url(src)
                if src and any(ext in src for ext in [".mp4", ".webm"]):
                    self.video_urls.add(src)

            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        self.update_status(f"📸 Images: {len(self.img_urls)}, 🎥 Videos: {len(self.video_urls)}, 🎞 GIFs: {len(self.gif_urls)}")

    def download(self):
        threading.Thread(target=self._download_media).start()

    def _download_media(self):
        download_dir = os.path.join(os.getcwd(), "downloads")
        os.makedirs(download_dir, exist_ok=True)

        base_folder = self.url_var.get().replace("https://", "").replace("http://", "").replace("/", "_")
        date_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        base_path = os.path.join(download_dir, f"{base_folder}_{date_str}")

        photo_path = os.path.join(base_path, "photos")
        video_path = os.path.join(base_path, "videos")
        gif_path = os.path.join(base_path, "gifs")
        os.makedirs(photo_path, exist_ok=True)
        os.makedirs(video_path, exist_ok=True)
        os.makedirs(gif_path, exist_ok=True)

        total_items = 0
        if self.download_images.get():
            total_items += len(self.img_urls)
        if self.download_videos.get():
            total_items += len(self.video_urls)
        if self.download_gifs.get():
            total_items += len(self.gif_urls)
        self.progress["maximum"] = total_items
        self.progress["value"] = 0

        if self.download_images.get():
            self._download_files(self.img_urls, photo_path)

        if self.download_videos.get():
            self._download_files(self.video_urls, video_path)

        if self.download_gifs.get():
            self._download_files(self.gif_urls, gif_path)

        self.update_status("✅ Download completed")

    def _download_files(self, urls, folder):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122 Safari/537.36',
            'Referer': self.url_var.get(),
        }
        session = requests.Session() 
        for i, url in enumerate(urls):
            try:
                ext = url.split('.')[-1].split('?')[0].split('&')[0][:5]
                filename = os.path.join(folder, f"file_{i}.{ext}")
                r = session.get(url, headers=headers, timeout=15)
                r.raise_for_status()
                with open(filename, 'wb') as f:
                    f.write(r.content)
                self.progress["value"] += 1
                self.update_status(f"⬇️ {filename} from {url}")
            except Exception as e:
                error_msg = f"❌ Error downloading {url}: {e}"
                self.update_status(error_msg)
                with open("media_downloader_errors.log", "a", encoding="utf-8") as log_file:
                    log_file.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {error_msg}\n")

if __name__ == "__main__":
    root = Tk()
    app = MediaDownloaderGUI(root)
    root.mainloop()

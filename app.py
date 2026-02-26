import customtkinter as ctk
from tkinter import filedialog, messagebox
import yt_dlp
import os
import sys
import threading
import requests
import re
from io import BytesIO
from pathlib import Path
from moviepy import VideoFileClip, AudioFileClip, ColorClip
import static_ffmpeg
import subprocess
import ctypes
from PIL import Image


# --- CONFIGURAÇÃO DE CAMINHOS DO EXECUTÁVEL ---
def resource_path(relative_path):
    """Garante o acesso a arquivos como o logo.ico dentro do EXE."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# --- OTIMIZAÇÃO DE INTERFACE E CODECS ---
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass
static_ffmpeg.add_paths()


class ShiftMeltUltra:
    def __init__(self, root):
        self.root = root
        self.root.title("SHIFTMELT")
        self.root.geometry("900x850")
        self.root.minsize(850, 700)

        self.pasta_downloads = str(Path.home() / "Downloads")
        self.path_v = ""
        self.path_i = ""

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Layout Responsivo
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        # --- CABEÇALHO ---
        self.header_frame = ctk.CTkFrame(root, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, pady=(20, 10))

        try:
            img_path = resource_path("logo.ico")
            self.logo_img = ctk.CTkImage(Image.open(img_path), size=(65, 65))
            ctk.CTkLabel(self.header_frame, text="", image=self.logo_img).pack(side="left", padx=15)
        except:
            pass

        ctk.CTkLabel(self.header_frame, text="SHIFTMELT", font=("Impact", 60), text_color="#2ecc71").pack(side="left")

        # --- ABAS PRINCIPAIS ---
        self.tabs = ctk.CTkTabview(root, corner_radius=25)
        self.tabs.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

        self.tabs.add("YouTube Auto")
        self.tabs.add("Conversor Mídia")
        self.tabs.add("Imagens")

        self.setup_yt_tab()
        self.setup_video_tab()
        self.setup_image_tab()

        # --- BARRA DE STATUS E PROGRESSO ---
        self.footer = ctk.CTkFrame(root, fg_color="transparent")
        self.footer.grid(row=2, column=0, pady=15, sticky="ew")
        self.footer.grid_columnconfigure(0, weight=1)

        self.status_bar = ctk.CTkLabel(self.footer, text="Pronto para operar", font=("Roboto", 12))
        self.status_bar.pack()

        self.prog = ctk.CTkProgressBar(self.footer, width=650, height=12, progress_color="#2ecc71")
        self.prog.pack(pady=10);
        self.prog.set(0)

        ctk.CTkButton(self.footer, text="ABRIR PASTA DE DOWNLOADS", fg_color="transparent", border_width=1,
                      command=self.open_f).pack()

    # --- ABA YOUTUBE: DOWNLOAD E ANÁLISE ---
    def setup_yt_tab(self):
        tab = self.tabs.tab("YouTube Auto")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(tab, text="COLE O LINK DO VÍDEO", font=("Roboto", 14, "bold")).grid(row=0, column=0, pady=(15, 5))
        self.url_var = ctk.StringVar()
        self.url_var.trace_add("write", self.on_url_change)
        self.entry_url = ctk.CTkEntry(tab, textvariable=self.url_var, placeholder_text="Aguardando link...", width=600,
                                      height=45)
        self.entry_url.grid(row=1, column=0, pady=5)

        self.thumb_frame = ctk.CTkFrame(tab, fg_color="#101010", corner_radius=20, border_width=1,
                                        border_color="#2ecc71")
        self.thumb_frame.grid(row=2, column=0, padx=40, pady=10, sticky="nsew")
        self.lbl_thumb = ctk.CTkLabel(self.thumb_frame, text="A prévia aparecerá aqui automaticamente",
                                      text_color="gray")
        self.lbl_thumb.pack(expand=True, fill="both")

        self.bottom_yt = ctk.CTkFrame(tab, fg_color="transparent")
        self.bottom_yt.grid(row=3, column=0, pady=15)
        self.lbl_video_title = ctk.CTkLabel(self.bottom_yt, text="", font=("Roboto", 12, "bold"), wraplength=600)
        self.lbl_video_title.pack()

        self.combo_q = ctk.CTkComboBox(self.bottom_yt,
                                       values=["1080p (MP4)", "720p (MP4)", "480p (MP4)", "MP3 (Áudio)"], width=200)
        self.combo_q.pack(pady=8);
        self.combo_q.set("720p (MP4)")

        self.btn_yt = ctk.CTkButton(self.bottom_yt, text="INICIAR DOWNLOAD", fg_color="#e74c3c",
                                    font=("Roboto", 16, "bold"), width=300, height=55, command=self.download_yt)
        self.btn_yt.pack(pady=5)

    def on_url_change(self, *args):
        url = self.url_var.get()
        video_id_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
        if video_id_match:
            video_id = video_id_match.group(1)
            threading.Thread(target=self._carregar_capa_force, args=(video_id, url), daemon=True).start()

    def _carregar_capa_force(self, video_id, full_url):
        try:
            thumb_url = f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"
            res = requests.get(thumb_url, timeout=5)
            img_raw = Image.open(BytesIO(res.content))
            ctk_thumb = ctk.CTkImage(img_raw, size=(580, 320))
            self.lbl_thumb.configure(image=ctk_thumb, text="")
            self.root.update_idletasks()  # Força renderização
            with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True}) as ydl:
                info = ydl.extract_info(full_url, download=False)
                self.lbl_video_title.configure(text=info.get('title', 'Vídeo Identificado'))
        except:
            pass

    def download_yt(self):
        url = self.entry_url.get()
        if not url: return
        self.btn_yt.configure(state="disabled")
        threading.Thread(target=self._thread_yt, args=(url, self.combo_q.get()), daemon=True).start()

    def _thread_yt(self, url, q):
        # Travado para MP4
        fmt = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
        if "1080p" in q:
            fmt = "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]"
        elif "720p" in q:
            fmt = "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]"
        elif "MP3" in q:
            fmt = "bestaudio/best"

        opts = {
            'outtmpl': os.path.join(self.pasta_downloads, "%(title)s.%(ext)s"),
            'format': fmt,
            'merge_output_format': 'mp4',
            'progress_hooks': [self.hook],
            'concurrent_fragment_downloads': 5,
            'quiet': True,
            'nocheckcertificate': True  # Evita erro de SSL
        }
        if "MP3" in q:
            opts['postprocessors'] = [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
            self.root.after(0, lambda: messagebox.showinfo("SHIFTMELT", "Download concluído com sucesso!"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Erro", f"Download falhou: {str(e)}"))
        finally:
            self.btn_yt.configure(state="normal");
            self.prog.set(0)

    def hook(self, d):
        if d['status'] == 'downloading':
            p = d.get('_percent_str', '0%').replace('%', '')
            try:
                self.prog.set(float(p) / 100)
                self.status_bar.configure(text=f"Processando: {p}% | ETA: {d.get('_eta_str', '--')}")
            except:
                pass

    # --- ABA CONVERSOR MÍDIA: MP3 E MP4 (INCLUI MP3 -> MP4) ---
    def setup_video_tab(self):
        tab = self.tabs.tab("Conversor Mídia")
        tab.grid_columnconfigure(0, weight=1)
        ctk.CTkButton(tab, text="📂 SELECIONAR ARQUIVO LOCAL", command=self.sel_v, height=45).pack(pady=40)
        self.lbl_v = ctk.CTkLabel(tab, text="Aguardando seleção...", text_color="gray");
        self.lbl_v.pack()
        self.v_fmt = ctk.CTkSegmentedButton(tab, values=["MP3", "MP4"], width=300);
        self.v_fmt.pack(pady=30);
        self.v_fmt.set("MP3")
        ctk.CTkButton(tab, text="CONVERTER AGORA", command=self.conv_v, height=55, font=("Roboto", 14, "bold")).pack(
            pady=20)

    def sel_v(self):
        self.path_v = filedialog.askopenfilename()
        if self.path_v: self.lbl_v.configure(text=os.path.basename(self.path_v))

    def conv_v(self):
        if not self.path_v: return
        threading.Thread(target=self._thread_conv_v, daemon=True).start()

    def _thread_conv_v(self):
        fmt = self.v_fmt.get().lower()
        ext_origem = Path(self.path_v).suffix.lower()
        out = os.path.join(self.pasta_downloads, Path(self.path_v).stem + f"_convertido.{fmt}")
        self.status_bar.configure(text=f"Processando {fmt.upper()}...", text_color="yellow")
        self.prog.start()
        try:
            # Caso especial: MP3 para MP4 (Cria tela preta)
            if fmt == "mp4" and ext_origem == ".mp3":
                audio = AudioFileClip(self.path_v)
                black_clip = ColorClip(size=(1280, 720), color=(0, 0, 0), duration=audio.duration)
                black_clip = black_clip.set_audio(audio)
                black_clip.write_videofile(out, fps=24, logger=None, codec="libx264")
                audio.close();
                black_clip.close()
            elif fmt == "mp3":
                audio = AudioFileClip(self.path_v)
                audio.write_audiofile(out, logger=None)
                audio.close()
            else:
                clip = VideoFileClip(self.path_v)
                clip.write_videofile(out, codec="libx264", audio_codec="aac", logger=None)
                clip.close()

            self.root.after(0, lambda: messagebox.showinfo("SHIFTMELT", "Conversão Concluída!"))
            self.status_bar.configure(text="Sucesso!", text_color="#2ecc71")
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Erro", f"Falha na conversão: {str(e)}"))
        finally:
            self.prog.stop();
            self.prog.set(0)

    # --- ABA IMAGENS ---
    def setup_image_tab(self):
        tab = self.tabs.tab("Imagens")
        tab.grid_columnconfigure(0, weight=1)
        ctk.CTkButton(tab, text="🖼️ SELECIONAR IMAGEM", command=self.sel_i, height=45).pack(pady=40)
        self.lbl_i = ctk.CTkLabel(tab, text="Aguardando imagem...", text_color="gray");
        self.lbl_i.pack()
        self.i_fmt = ctk.CTkSegmentedButton(tab, values=["JPG", "PNG", "WEBP"], width=400);
        self.i_fmt.pack(pady=30);
        self.i_fmt.set("JPG")
        ctk.CTkButton(tab, text="CONVERTER IMAGEM", command=self.conv_i, height=55, fg_color="#2e7d32",
                      font=("Roboto", 14, "bold")).pack(pady=20)

    def sel_i(self):
        self.path_i = filedialog.askopenfilename()
        if self.path_i: self.lbl_i.configure(text=os.path.basename(self.path_i))

    def conv_i(self):
        if not self.path_i: return
        threading.Thread(target=self._thread_conv_i, daemon=True).start()

    def _thread_conv_i(self):
        self.status_bar.configure(text="Convertendo imagem...", text_color="yellow")
        try:
            img = Image.open(self.path_i)
            fmt = self.i_fmt.get().lower()
            out = os.path.join(self.pasta_downloads, Path(self.path_i).stem + f"_processada.{fmt}")
            if self.i_fmt.get() == "JPG": img = img.convert("RGB")
            img.save(out)
            self.root.after(0, lambda: messagebox.showinfo("SHIFTMELT", "Imagem pronta!"))
            self.status_bar.configure(text="Concluído!", text_color="#2ecc71")
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Erro", str(e)))
        finally:
            self.status_bar.configure(text="Pronto", text_color="white")

    def open_f(self):
        subprocess.Popen(f'explorer "{self.pasta_downloads}"')


if __name__ == "__main__":
    app_root = ctk.CTk()
    ShiftMeltUltra(app_root)
    app_root.mainloop()
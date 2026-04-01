import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk
import threading
import queue
import os
import sys
import traceback
import locale
from urllib.parse import urlparse
import asyncio
import dumpall  # Import the dumpall package

# Language dictionaries
LANGUAGES = {
    "en": {
        "title": "Dumpall GUI",
        "target_url": "Target URL:",
        "output_directory": "Output Directory:",
        "browse": "Browse",
        "proxy": "Proxy:",
        "force_download": "Force Download",
        "debug_mode": "Debug Mode",
        "start_dumpall": "Start Dumpall",
        "subtitle": "A cleaner desktop client for fast source discovery.",
        "advanced_options": "Advanced Options",
        "logs": "Logs:",
        "url_empty_error": "Error: Target URL cannot be empty!\n",
        "starting_process": "Starting Dumpall process...\n",
        "target": "Target:",
        "output_dir": "Output Directory:",
        "process_finished": "\nDumpall process finished.\n",
        "exit_message": "Exit.",
        "manual_ulimit": "Please manually modify the open file limit.",
        "language": "Language:"
    },
    "zh": {
        "title": "Dumpall 图形界面",
        "target_url": "目标URL:",
        "output_directory": "输出目录:",
        "browse": "浏览",
        "proxy": "代理:",
        "force_download": "强制下载",
        "debug_mode": "调试模式",
        "start_dumpall": "开始下载",
        "subtitle": "更清爽的桌面客户端，更快开始站点文件探测。",
        "advanced_options": "高级选项",
        "logs": "日志:",
        "url_empty_error": "错误: 目标URL不能为空!\n",
        "starting_process": "开始Dumpall进程...\n",
        "target": "目标:",
        "output_dir": "输出目录:",
        "process_finished": "\nDumpall进程结束.\n",
        "exit_message": "退出.",
        "manual_ulimit": "请手动修改打开文件数量限制.",
        "language": "语言:"
    }
}

class QueueLogger:
    def __init__(self, queue):
        self.queue = queue

    def write(self, message):
        self.queue.put(message)

    def flush(self):
        pass

class DumpallGUI:
    def __init__(self, master):
        self.master = master
        self.set_language()
        master.title(LANGUAGES[self.current_language]["title"])
        master.configure(bg="#eef3f8")
        master.geometry("980x680")
        master.minsize(860, 620)

        self.setup_style()

        self.create_widgets()
        self.update_ui_language()

        self.log_queue = queue.Queue()
        sys.stdout = QueueLogger(self.log_queue)
        sys.stderr = QueueLogger(self.log_queue)

        self.master.after(100, self.poll_log_queue)

    def set_language(self):
        try:
            lang_code, _ = locale.getdefaultlocale()
            if lang_code and lang_code.lower().startswith('zh'):
                self.current_language = "zh"
            else:
                self.current_language = "en"
        except Exception:
            self.current_language = "en"  # Default to English on error

    def setup_style(self):
        self.colors = {
            "app_bg": "#eef3f8",
            "surface": "#ffffff",
            "surface_alt": "#f7f9fc",
            "text": "#243447",
            "muted": "#6b7a90",
            "border": "#d7e0ea",
            "primary": "#42b883",
            "primary_hover": "#32976b",
            "accent": "#35495e",
            "log_bg": "#0f1722",
            "log_fg": "#d7e3f1"
        }

        self.style = ttk.Style()
        if "clam" in self.style.theme_names():
            self.style.theme_use("clam")

        self.style.configure("App.TFrame", background=self.colors["app_bg"])
        self.style.configure("Card.TFrame", background=self.colors["surface"], relief="flat")
        self.style.configure("Section.TLabelframe", background=self.colors["surface"], borderwidth=0)
        self.style.configure(
            "Section.TLabelframe.Label",
            background=self.colors["surface"],
            foreground=self.colors["accent"],
            font=("Segoe UI Semibold", 11)
        )
        self.style.configure(
            "Title.TLabel",
            background=self.colors["app_bg"],
            foreground=self.colors["accent"],
            font=("Segoe UI Semibold", 24)
        )
        self.style.configure(
            "Subtitle.TLabel",
            background=self.colors["app_bg"],
            foreground=self.colors["muted"],
            font=("Segoe UI", 10)
        )
        self.style.configure(
            "FieldLabel.TLabel",
            background=self.colors["surface"],
            foreground=self.colors["text"],
            font=("Segoe UI Semibold", 10)
        )
        self.style.configure(
            "Primary.TButton",
            background=self.colors["primary"],
            foreground="#ffffff",
            borderwidth=0,
            focusthickness=0,
            focuscolor=self.colors["primary"],
            font=("Segoe UI Semibold", 10),
            padding=(18, 12)
        )
        self.style.map(
            "Primary.TButton",
            background=[("active", self.colors["primary_hover"]), ("pressed", self.colors["primary_hover"])]
        )
        self.style.configure(
            "Secondary.TButton",
            background=self.colors["surface_alt"],
            foreground=self.colors["accent"],
            bordercolor=self.colors["border"],
            lightcolor=self.colors["surface_alt"],
            darkcolor=self.colors["surface_alt"],
            font=("Segoe UI", 10),
            padding=(14, 10)
        )
        self.style.map(
            "Secondary.TButton",
            background=[("active", "#edf3f8")]
        )
        self.style.configure(
            "Switch.TCheckbutton",
            background=self.colors["surface"],
            foreground=self.colors["text"],
            font=("Segoe UI", 10)
        )

    def create_widgets(self):
        self.main_frame = ttk.Frame(self.master, padding=24, style="App.TFrame")
        self.main_frame.grid(row=0, column=0, sticky="nsew")

        self.header_title = ttk.Label(self.main_frame, style="Title.TLabel")
        self.header_title.grid(row=0, column=0, sticky="w")
        self.header_subtitle = ttk.Label(self.main_frame, style="Subtitle.TLabel")
        self.header_subtitle.grid(row=1, column=0, sticky="w", pady=(6, 22))

        self.content_frame = ttk.Frame(self.main_frame, style="App.TFrame")
        self.content_frame.grid(row=2, column=0, sticky="nsew")

        self.form_card = ttk.Frame(self.content_frame, padding=24, style="Card.TFrame")
        self.form_card.grid(row=0, column=0, sticky="nsew", padx=(0, 18))

        self.log_card = ttk.Frame(self.content_frame, padding=20, style="Card.TFrame")
        self.log_card.grid(row=0, column=1, sticky="nsew")

        self.url_label = ttk.Label(self.form_card, style="FieldLabel.TLabel")
        self.url_label.grid(row=0, column=0, sticky="w", pady=(0, 8))
        self.url_entry = ttk.Entry(self.form_card, width=60, font=("Segoe UI", 11))
        self.url_entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 16), ipady=7)

        self.outdir_label = ttk.Label(self.form_card, style="FieldLabel.TLabel")
        self.outdir_label.grid(row=2, column=0, sticky="w", pady=(0, 8))
        self.outdir_entry = ttk.Entry(self.form_card, width=60, font=("Segoe UI", 11))
        self.outdir_entry.grid(row=3, column=0, sticky="ew", pady=(0, 16), ipady=7)
        self.outdir_button = ttk.Button(
            self.form_card,
            command=self.browse_outdir,
            style="Secondary.TButton"
        )
        self.outdir_button.grid(row=3, column=1, sticky="ew", padx=(12, 0), pady=(0, 16))

        self.proxy_label = ttk.Label(self.form_card, style="FieldLabel.TLabel")
        self.proxy_label.grid(row=4, column=0, sticky="w", pady=(0, 8))
        self.proxy_entry = ttk.Entry(self.form_card, width=60, font=("Segoe UI", 11))
        self.proxy_entry.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(0, 18), ipady=7)

        self.options_frame = ttk.LabelFrame(self.form_card, padding=16, style="Section.TLabelframe")
        self.options_frame.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(0, 18))

        self.force_var = tk.BooleanVar()
        self.force_check = ttk.Checkbutton(self.options_frame, variable=self.force_var, style="Switch.TCheckbutton")
        self.force_check.grid(row=0, column=0, sticky="w", padx=(0, 24))

        self.debug_var = tk.BooleanVar()
        self.debug_check = ttk.Checkbutton(self.options_frame, variable=self.debug_var, style="Switch.TCheckbutton")
        self.debug_check.grid(row=0, column=1, sticky="w")

        self.start_button = ttk.Button(
            self.form_card,
            command=self.start_dumpall_thread,
            style="Primary.TButton"
        )
        self.start_button.grid(row=7, column=0, columnspan=2, sticky="ew")

        self.log_label = ttk.Label(self.log_card, style="FieldLabel.TLabel")
        self.log_label.grid(row=0, column=0, sticky="w", pady=(0, 10))
        self.log_text = scrolledtext.ScrolledText(
            self.log_card,
            width=80,
            height=20,
            state='disabled',
            wrap=tk.WORD,
            relief="flat",
            borderwidth=0,
            bg=self.colors["log_bg"],
            fg=self.colors["log_fg"],
            insertbackground="#ffffff",
            font=("Consolas", 10),
            padx=16,
            pady=16
        )
        self.log_text.grid(row=1, column=0, sticky="nsew")

        self.form_card.grid_columnconfigure(0, weight=1)
        self.options_frame.grid_columnconfigure(0, weight=1)
        self.options_frame.grid_columnconfigure(1, weight=1)
        self.log_card.grid_rowconfigure(1, weight=1)
        self.log_card.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=3)
        self.content_frame.grid_columnconfigure(1, weight=4)
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(2, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(0, weight=1)

    def update_ui_language(self):
        lang = LANGUAGES[self.current_language]

        self.master.title(lang["title"])
        self.header_title.config(text=lang["title"])
        self.header_subtitle.config(text=lang["subtitle"])
        self.url_label.config(text=lang["target_url"])
        self.outdir_label.config(text=lang["output_directory"])
        self.proxy_label.config(text=lang["proxy"])
        self.log_label.config(text=lang["logs"])
        self.options_frame.config(text=lang["advanced_options"])

        self.outdir_button.config(text=lang["browse"])
        self.start_button.config(text=lang["start_dumpall"])
        self.force_check.config(text=lang["force_download"])
        self.debug_check.config(text=lang["debug_mode"])

    def browse_outdir(self):
        directory = filedialog.askdirectory()
        if directory:
            self.outdir_entry.delete(0, tk.END)
            self.outdir_entry.insert(0, directory)

    def update_log(self, message):
        self.log_text.configure(state='normal')
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)
        self.log_text.configure(state='disabled')

    def poll_log_queue(self):
        while True:
            try:
                message = self.log_queue.get(block=False)
                self.update_log(message)
            except queue.Empty:
                break
        self.master.after(100, self.poll_log_queue)

    def run_dumpall(self, url, outdir, proxy, force, debug):
        lang = LANGUAGES[self.current_language]

        original_secho = dumpall.click.secho
        def gui_secho(message, fg=None):
            self.log_queue.put(message + "\n")
        dumpall.click.secho = gui_secho

        if not outdir:
            url_obj = urlparse(url)
            outdir = os.path.join(os.getcwd(), "%s_%s" % (url_obj.hostname, url_obj.port if url_obj.port else "80"))
        
        basedir = outdir
        i = 1
        while os.path.exists(outdir):
            outdir = "%s_%s" % (basedir, i)
            i += 1
        outdir = os.path.abspath(outdir)
        os.makedirs(outdir, exist_ok=True)

        self.update_log(f"{lang['target']} {url}\n")
        self.update_log(f"{lang['output_dir']} {outdir}\n\n")

        try:
            dumpall.start(url, outdir, proxy=proxy, force=force, debug=debug)
        except KeyboardInterrupt as e:
            self.update_log(f"{lang['exit_message']}\n")
        except Exception as e:
            self.update_log(f"Error: {e}\n")
            self.update_log(traceback.format_exc() + "\n")
        finally:
            dumpall.click.secho = original_secho
            self.update_log(lang["process_finished"])

    def start_dumpall_thread(self):
        lang = LANGUAGES[self.current_language]

        url = self.url_entry.get()
        outdir = self.outdir_entry.get()
        proxy = self.proxy_entry.get()
        force = self.force_var.get()
        debug = self.debug_var.get()

        if not url:
            self.update_log(lang["url_empty_error"])
            return

        self.update_log(lang["starting_process"])
        self.log_text.configure(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state='disabled')

        dumpall_thread = threading.Thread(target=self.run_dumpall, args=(url, outdir, proxy, force, debug))
        dumpall_thread.daemon = True
        dumpall_thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    gui = DumpallGUI(root)
    root.mainloop()

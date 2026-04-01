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

    def create_widgets(self):
        self.main_frame = ttk.Frame(self.master, padding="10")
        self.main_frame.grid(row=0, column=0, sticky="nsew")

        # Language Selection (removed, now automatic)

        # URL
        ttk.Label(self.main_frame, text=LANGUAGES[self.current_language]["target_url"]).grid(row=0, column=0, sticky="w", pady=5)
        self.url_entry = ttk.Entry(self.main_frame, width=60)
        self.url_entry.grid(row=0, column=1, columnspan=2, sticky="ew", pady=5)

        # Output Directory
        ttk.Label(self.main_frame, text=LANGUAGES[self.current_language]["output_directory"]).grid(row=1, column=0, sticky="w", pady=5)
        self.outdir_entry = ttk.Entry(self.main_frame, width=60)
        self.outdir_entry.grid(row=1, column=1, sticky="ew", pady=5)
        self.outdir_button = ttk.Button(self.main_frame, text=LANGUAGES[self.current_language]["browse"], command=self.browse_outdir)
        self.outdir_button.grid(row=1, column=2, sticky="w", padx=5, pady=5)

        # Proxy
        ttk.Label(self.main_frame, text=LANGUAGES[self.current_language]["proxy"]).grid(row=2, column=0, sticky="w", pady=5)
        self.proxy_entry = ttk.Entry(self.main_frame, width=60)
        self.proxy_entry.grid(row=2, column=1, columnspan=2, sticky="ew", pady=5)

        # Checkboxes
        self.force_var = tk.BooleanVar()
        self.force_check = ttk.Checkbutton(self.main_frame, text=LANGUAGES[self.current_language]["force_download"], var=self.force_var)
        self.force_check.grid(row=3, column=0, sticky="w", pady=5)

        self.debug_var = tk.BooleanVar()
        self.debug_check = ttk.Checkbutton(self.main_frame, text=LANGUAGES[self.current_language]["debug_mode"], var=self.debug_var)
        self.debug_check.grid(row=3, column=1, sticky="w", pady=5)

        # Start Button
        self.start_button = ttk.Button(self.main_frame, text=LANGUAGES[self.current_language]["start_dumpall"], command=self.start_dumpall_thread)
        self.start_button.grid(row=4, column=0, columnspan=3, pady=15)

        # Log Area
        ttk.Label(self.main_frame, text=LANGUAGES[self.current_language]["logs"]).grid(row=5, column=0, sticky="w", pady=5)
        self.log_text = scrolledtext.ScrolledText(self.main_frame, width=80, height=20, state='disabled', wrap=tk.WORD)
        self.log_text.grid(row=6, column=0, columnspan=3, sticky="nsew", pady=5)

        # Configure grid to expand
        self.main_frame.grid_rowconfigure(6, weight=1)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(0, weight=1)

    def update_ui_language(self):
        lang = LANGUAGES[self.current_language]

        self.master.title(lang["title"])
        # Update labels
        self.main_frame.children["!label"].config(text=lang["target_url"])
        self.main_frame.children["!label2"].config(text=lang["output_directory"])
        self.main_frame.children["!label3"].config(text=lang["proxy"])
        self.main_frame.children["!label4"].config(text=lang["logs"])
        
        # Update buttons
        self.outdir_button.config(text=lang["browse"])
        self.start_button.config(text=lang["start_dumpall"])

        # Update checkboxes
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

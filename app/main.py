import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from content_features import analyze_video
import threading
import random
from report import calculate_video_similarity
from compressor import compress_video
import os

from db_engine import (
    DB_PATH,
    init_db,
    save_preset,
    get_preset_by_id,
    get_user_presets,
    user_exists,
    create_user,
    authenticate_user
)

class VideoCompressionApp:
    def __init__(self, root):
        try:
            if not os.path.exists(DB_PATH):
                init_db()
        except Exception as e:
            messagebox.showerror(
                "Ошибка БД",
                f"Не удалось инициализировать БД:\n{e}"
            )

        self.save_preset_window = None
        self.load_preset_window = None

        self.root = root
        self.root.title("Система анализа и сжатия видео")
        self.root.geometry("1000x700")

        self.video_path = ""
        self.parameters_selected = False

        self.spatial_information = 0
        self.temporal_information = 0
        self.scene_cut_frequency = 0
        self.noise_level = 0
        self.texture_complexity = 0
        self.motion_magnitude = 0
        self.entropy_value = 0
        self.content_type = ""

        self.original_video_path = None
        self.compressed_video_path = None
        self.current_user = None
        self.main_container = ttk.Frame(root)
        self.main_container.pack(fill="both", expand=True)

        self.show_login_screen()

    def show_login_screen(self):
        self.clear_container()

        frame = ttk.Frame(self.main_container, padding=20)
        frame.pack(expand=True)

        ttk.Label(
            frame,
            text="Авторизация",
            font=("Arial", 18)
        ).pack(pady=15)

        ttk.Label(frame, text="Логин").pack(anchor="w")

        self.login_var = tk.StringVar()

        ttk.Entry(
            frame,
            textvariable=self.login_var,
            width=35
        ).pack(pady=5)

        ttk.Label(frame, text="Пароль").pack(anchor="w")

        self.password_var = tk.StringVar()

        ttk.Entry(
            frame,
            textvariable=self.password_var,
            show="*",
            width=35
        ).pack(pady=5)

        self.auth_message = tk.StringVar()

        ttk.Label(
            frame,
            textvariable=self.auth_message,
            foreground="red"
        ).pack(pady=10)

        buttons = ttk.Frame(frame)
        buttons.pack(pady=10)

        ttk.Button(
            buttons,
            text="Зарегистрировать пользователя",
            command=self.register_user
        ).pack(side="left", padx=5)

        ttk.Button(
            buttons,
            text="Войти в систему",
            command=self.login_user
        ).pack(side="left", padx=5)

    def register_user(self):
        login = self.login_var.get().strip()
        password = self.password_var.get()

        if not login or not password:
            self.auth_message.set("Введите логин и пароль.")
            return

        if user_exists(login):
            self.auth_message.set("Пользователь уже существует.")
            return

        if create_user(login, password):
            self.auth_message.set("Пользователь успешно зарегистрирован.")
        else:
            self.auth_message.set("Не удалось зарегистрировать пользователя.")

    def login_user(self):
        login = self.login_var.get().strip()
        password = self.password_var.get()

        if not login or not password:
            self.auth_message.set("Введите логин и пароль.")
            return

        if authenticate_user(login, password):
            self.current_user = login
            self.show_file_selection()
        else:
            self.auth_message.set("Неверный логин или пароль.")

    def close_auxiliary_windows(self):
        if (
                self.save_preset_window is not None
                and self.save_preset_window.winfo_exists()
        ):
            self.save_preset_window.destroy()

        if (
                self.load_preset_window is not None
                and self.load_preset_window.winfo_exists()
        ):
            self.load_preset_window.destroy()

        self.save_preset_window = None
        self.load_preset_window = None

    def clear_container(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

    # ==========================
    # ЭКРАН ВЫБОРА ФАЙЛА
    # ==========================
    def show_file_selection(self):
        self.clear_container()

        frame = ttk.Frame(self.main_container, padding=20)
        frame.pack(expand=True)

        ttk.Label(
            frame,
            text="Выберите видеофайл для анализа",
            font=("Arial", 16)
        ).pack(pady=15)

        self.path_var = tk.StringVar()

        ttk.Entry(
            frame,
            textvariable=self.path_var,
            width=70
        ).pack(pady=10)

        ttk.Button(
            frame,
            text="Выбрать файл",
            command=self.select_video
        ).pack(pady=10)

        self.analyze_button = ttk.Button(
            frame,
            text="Начать анализ",
            state="disabled",
            command=self.show_analysis_screen
        )
        self.analyze_button.pack(pady=20)

    def select_video(self):
        path = filedialog.askopenfilename(
            title="Выберите видео",
            filetypes=[
                ("Видео", "*.mp4 *.avi *.mkv *.mov"),
                ("Все файлы", "*.*")
            ]
        )

        if not path:
            return

        self.original_video_path = path
        self.video_path = path

        self.path_var.set(path)

        self.analyze_button.config(state="normal")

    # ==========================
    # ЭКРАН АНАЛИЗА
    # ==========================
    def show_analysis_screen(self):
        self.clear_container()

        frame = ttk.Frame(self.main_container)
        frame.pack(expand=True)

        ttk.Label(
            frame,
            text="Извлечение данных из видео...",
            font=("Arial", 16)
        ).pack(pady=20)

        self.analysis_progress = ttk.Progressbar(
            frame,
            length=400,
            mode="indeterminate"
        )
        self.analysis_progress.pack(pady=20)
        self.analysis_progress.start()

        threading.Thread(
            target=self.run_analysis,
            daemon=True
        ).start()

    def run_analysis(self):
        try:
            result = analyze_video(self.original_video_path)

            (
                self.spatial_information,
                self.temporal_information,
                self.scene_cut_frequency,
                self.noise_level,
                self.texture_complexity,
                self.motion_magnitude,
                self.entropy_value,
                self.content_type
            ) = result

            self.root.after(
                0,
                self.show_parameter_screen
            )

        except Exception as e:
            self.root.after(
                0,
                lambda: messagebox.showerror(
                    "Ошибка анализа",
                    str(e)
                )
            )

    def analysis_finished(self):
        self.show_parameter_screen()

    # ==========================
    # ЭКРАН ПАРАМЕТРОВ
    # ==========================
    def show_parameter_screen(self):
        self.clear_container()

        container = ttk.Frame(self.main_container)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        left_frame = ttk.LabelFrame(
            container,
            text="Информация о видео"
        )
        left_frame.pack(side="left", fill="both", expand=True, padx=10)

        video_info = [
            f"Spatial Information: {self.spatial_information:.4f}",
            f"Temporal Information: {self.temporal_information:.4f}",
            f"Scene Cut Frequency: {self.scene_cut_frequency:.4f}",
            f"Noise Level: {self.noise_level:.4f}",
            f"Texture Complexity: {self.texture_complexity:.4f}",
            f"Motion Magnitude: {self.motion_magnitude:.4f}",
            f"Entropy: {self.entropy_value:.4f}",
            f"Content Type: {self.content_type}"
        ]

        for item in video_info:
            ttk.Label(left_frame, text=item).pack(
                anchor="w",
                padx=10,
                pady=5
            )

        right_frame = ttk.LabelFrame(
            container,
            text="Параметры кодирования"
        )
        right_frame.pack(side="right", fill="both", expand=True, padx=10)

        self.crf_var = tk.StringVar()
        self.preset_var = tk.StringVar()
        self.aq_var = tk.StringVar()
        self.bf_var = tk.StringVar()

        ttk.Label(right_frame, text="CRF").pack(anchor="w", padx=10, pady=5)
        crf = ttk.Combobox(
            right_frame,
            textvariable=self.crf_var,
            values=[18, 20, 22, 24, 26]
        )
        crf.pack(fill="x", padx=10)

        ttk.Label(right_frame, text="Preset").pack(anchor="w", padx=10, pady=5)
        preset = ttk.Combobox(
            right_frame,
            textvariable=self.preset_var,
            values=[
                "ultrafast",
                "fast",
                "medium",
                "slow",
                "veryslow"
            ]
        )
        preset.pack(fill="x", padx=10)

        ttk.Label(right_frame, text="AQ Mode").pack(anchor="w", padx=10, pady=5)
        aq = ttk.Combobox(
            right_frame,
            textvariable=self.aq_var,
            values=[0, 1, 2, 3]
        )
        aq.pack(fill="x", padx=10)

        ttk.Label(right_frame, text="B-Frames").pack(anchor="w", padx=10, pady=5)
        bf = ttk.Combobox(
            right_frame,
            textvariable=self.bf_var,
            values=[0, 2, 4, 8]
        )
        bf.pack(fill="x", padx=10)

        for widget in [crf, preset, aq, bf]:
            widget.bind("<<ComboboxSelected>>", self.check_parameters)

        bottom = ttk.Frame(self.main_container)
        bottom.pack(fill="x", padx=20, pady=10)

        self.save_preset_button = ttk.Button(
            bottom,
            text="Сохранить в пресет",
            command=self.show_save_preset_form,
            state="disabled"
        )

        self.save_preset_button.pack(
            side="left",
            padx=5
        )

        ttk.Button(
            bottom,
            text="Загрузить из пресета",
            command=self.show_load_preset_form
        ).pack(side="left", padx=5)

        ttk.Button(
            bottom,
            text="Подобрать параметры",
            command=self.auto_select
        ).pack(side="left", padx=5)

        self.compress_button = ttk.Button(
            bottom,
            text="Начать сжатие",
            state="disabled",
            command=self.show_compression_screen
        )
        self.compress_button.pack(side="right", padx=5)

    def apply_preset(self, preset):
        if preset is None:
            raise ValueError("Пресет не найден")

        self.crf_var.set(str(preset[4]))  # crf
        self.preset_var.set(preset[5])  # preset
        self.aq_var.set(str(preset[6]))  # aq_mode
        self.bf_var.set(str(preset[7]))  # bf

        self.check_parameters()

    def close_load_window(self):
        if (
                self.load_preset_window is not None
                and self.load_preset_window.winfo_exists()
        ):
            self.load_preset_window.destroy()

        self.load_preset_window = None

    def show_load_preset_form(self):

        if (
                self.load_preset_window is not None
                and self.load_preset_window.winfo_exists()
        ):
            self.load_preset_window.lift()
            self.load_preset_window.focus_force()
            return

        if (
                self.save_preset_window is not None
                and self.save_preset_window.winfo_exists()
        ):
            self.save_preset_window.lift()
            self.save_preset_window.focus_force()
            return

        presets = get_user_presets(
            "H264",
            self.current_user
        )

        self.load_preset_window = tk.Toplevel(self.root)
        window = self.load_preset_window

        window.title("Загрузка пресета")
        window.geometry("450x250")

        window.protocol(
            "WM_DELETE_WINDOW",
            self.close_load_window
        )

        ttk.Label(
            window,
            text="Выберите пресет"
        ).pack(pady=10)

        self.selected_preset = tk.StringVar()

        preset_combobox = ttk.Combobox(
            window,
            textvariable=self.selected_preset,
            state="readonly",
            width=45
        )

        preset_combobox["values"] = [
            f"{preset[0]} | {preset[2]}"
            for preset in presets
        ]

        preset_combobox.pack(
            padx=10,
            pady=10
        )

        ttk.Button(
            window,
            text="Загрузить",
            command=self.load_selected_preset
        ).pack(pady=15)

    def load_selected_preset(self):

        if not self.selected_preset.get():
            messagebox.showwarning(
                "Ошибка",
                "Выберите пресет."
            )
            return

        preset_id = int(
            self.selected_preset.get().split("|")[0].strip()
        )

        preset = get_preset_by_id(
            "H264",
            preset_id
        )

        print(preset)

        if preset is None:
            messagebox.showerror(
                "Ошибка",
                "Пресет не найден."
            )
            return

        self.apply_preset(preset)

        self.close_load_window()

    def close_save_window(self):
        if (
            self.save_preset_window is not None
            and self.save_preset_window.winfo_exists()
        ):
            self.save_preset_window.destroy()

        self.save_preset_window = None

    def show_save_preset_form(self):
        # Уже открыто окно сохранения
        if (
                self.save_preset_window is not None
                and self.save_preset_window.winfo_exists()
        ):
            self.save_preset_window.lift()
            self.save_preset_window.focus_force()
            return

        # Уже открыто окно загрузки
        if (
                self.load_preset_window is not None
                and self.load_preset_window.winfo_exists()
        ):
            self.load_preset_window.lift()
            self.load_preset_window.focus_force()
            return

        self.save_preset_window = tk.Toplevel(self.root)

        window = self.save_preset_window

        window.protocol(
            "WM_DELETE_WINDOW",
            self.close_save_window
        )

        window.title("Сохранение пресета")
        window.geometry("400x250")

        ttk.Label(window, text="Название пресета").pack(pady=5)

        name_var = tk.StringVar()

        ttk.Entry(
            window,
            textvariable=name_var
        ).pack(fill="x", padx=10)

        ttk.Label(window, text="Описание").pack(pady=5)

        description_text = tk.Text(
            window,
            height=5
        )
        description_text.pack(
            fill="both",
            expand=True,
            padx=10
        )

        def do_save():
            name = name_var.get().strip()
            description = description_text.get(
                "1.0",
                "end"
            ).strip()

            if not name:
                messagebox.showwarning(
                    "Ошибка",
                    "Введите название пресета"
                )
                return

            preset_data = (
                name,
                description,
                int(self.crf_var.get()),
                self.preset_var.get(),
                int(self.aq_var.get()),
                int(self.bf_var.get())
            )

            save_preset(
                "H264",
                self.current_user,
                preset_data
            )

            messagebox.showinfo(
                "Успешно",
                "Пресет сохранён"
            )

            window.destroy()

        ttk.Button(
            window,
            text="Сохранить",
            command=do_save
        ).pack(pady=10)

    def check_parameters(self, event=None):
        fields = [
            self.crf_var.get().strip(),
            self.preset_var.get().strip(),
            self.aq_var.get().strip(),
            self.bf_var.get().strip()
        ]

        enabled = all(fields)

        self.compress_button.config(
            state="normal" if enabled else "disabled"
        )

        self.save_preset_button.config(
            state="normal" if enabled else "disabled"
        )

    def save_preset(self):
        messagebox.showinfo(
            "Пресет",
            "Пресет сохранён"
        )

    def load_preset(self):
        self.crf_var.set("22")
        self.preset_var.set("medium")
        self.aq_var.set("2")
        self.bf_var.set("4")

        self.check_parameters()

    def auto_select(self):
        params = self.predict_encoding_parameters()

        self.crf_var.set(params["crf"])
        self.preset_var.set(params["preset"])
        self.aq_var.set(params["aq"])
        self.bf_var.set(params["bf"])

        self.check_parameters()

    def predict_encoding_parameters(self):
        si = self.spatial_information
        ti = self.temporal_information
        noise = self.noise_level
        texture = self.texture_complexity
        motion = self.motion_magnitude
        entropy = self.entropy_value
        content = self.content_type

        # Базовый CRF
        crf = 24

        # Детализированные видео требуют меньшего CRF
        if si > 40:
            crf -= 2

        if texture > 0.5:
            crf -= 1

        if entropy > 6:
            crf -= 1

        # Шумное видео лучше сжимать сильнее
        if noise > 0.15:
            crf += 2

        # Большое движение ухудшает сжатие
        if motion > 10:
            crf -= 1

        crf += random.choice([-1, 0, 1])

        crf = max(18, min(30, crf))

        # Preset
        complexity_score = si + texture * 20 + entropy

        if complexity_score > 70:
            preset = "veryslow"
        elif complexity_score > 55:
            preset = "slow"
        elif complexity_score > 40:
            preset = "medium"
        else:
            preset = "fast"

        # AQ Mode
        if texture > 0.6:
            aq_mode = 3
        elif texture > 0.3:
            aq_mode = 2
        else:
            aq_mode = 1

        # B-frames
        if motion > 15:
            bf = 2
        elif motion > 7:
            bf = 4
        else:
            bf = 8

        # Контентно-зависимая коррекция
        content = str(content).lower()

        if "animation" in content:
            crf += 1
            bf = 8

        elif "sport" in content:
            crf -= 1
            bf = 2

        elif "movie" in content:
            preset = "slow"

        return {
            "crf": str(crf),
            "preset": preset,
            "aq": str(aq_mode),
            "bf": str(bf)
        }

    # ==========================
    # ЭКРАН СЖАТИЯ
    # ==========================
    def show_compression_screen(self):

        self.close_auxiliary_windows()

        self.clear_container()

        frame = ttk.Frame(self.main_container)
        frame.pack(expand=True)

        ttk.Label(
            frame,
            text="Выполняется сжатие видео...",
            font=("Arial", 16)
        ).pack(pady=20)

        self.compression_progress = ttk.Progressbar(
            frame,
            length=400,
            mode="indeterminate"
        )

        self.compression_progress.pack(pady=20)
        self.compression_progress.start()

        self.root.after(
            5000,
            self.compression_finished
        )

    # ==========================
    # ЭКРАН ЗАВЕРШЕНИЯ
    # ==========================
    def compression_finished(self):

        similarity = 0.0

        self.clear_container()

        ttk.Label(
            self.main_container,
            text="Сжатие успешно завершено",
            font=("Arial", 18)
        ).pack(pady=15)

        content = ttk.Frame(self.main_container)
        content.pack(fill="both", expand=True, padx=20)

        left = ttk.LabelFrame(
            content,
            text="Результат кодирования"
        )

        left.pack(
            side="left",
            fill="both",
            expand=True,
            padx=10
        )

        ttk.Label(
            left,
            text=f"Схожесть видео: {similarity:.4f}"
        ).pack(anchor="w", padx=10, pady=5)

        right = ttk.LabelFrame(
            content,
            text="Content Features"
        )

        right.pack(
            side="right",
            fill="both",
            expand=True,
            padx=10
        )

        features = [
            f"Spatial Information: {self.spatial_information:.4f}",
            f"Temporal Information: {self.temporal_information:.4f}",
            f"Scene Cut Frequency: {self.scene_cut_frequency:.4f}",
            f"Noise Level: {self.noise_level:.4f}",
            f"Texture Complexity: {self.texture_complexity:.4f}",
            f"Motion Magnitude: {self.motion_magnitude:.4f}",
            f"Entropy: {self.entropy_value:.4f}",
            f"Content Type: {self.content_type}"
        ]

        for feature in features:
            ttk.Label(
                right,
                text=feature
            ).pack(anchor="w", padx=10, pady=3)

        buttons = ttk.Frame(self.main_container)
        buttons.pack(pady=20)

        ttk.Button(
            buttons,
            text="Сохранить результат кодирования",
            command=self.save_encoding_result
        ).pack(side="left", padx=10)

        ttk.Button(
            buttons,
            text="Вернуться к параметрам",
            command=self.show_parameter_screen
        ).pack(side="left", padx=10)

        ttk.Button(
            buttons,
            text="Выход",
            command=self.root.destroy
        ).pack(side="left", padx=10)

    def save_encoding_result(self):
        pass


if __name__ == "__main__":
    root = tk.Tk()
    app = VideoCompressionApp(root)
    root.mainloop()
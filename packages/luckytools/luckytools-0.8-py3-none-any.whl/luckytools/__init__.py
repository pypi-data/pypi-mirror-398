import time
import math
import sys
import shutil
import os
import json
import urllib.request
import urllib.error
import webbrowser

class LuckyTools:
    def __init__(self, prefix_name="⌊ LuckyTools ⌉ »", prefix_hex="00FF5A", prefix_short="⌊ LT ⌉ »", show_warns=True,
                 show_init=True, api_url="http://lt.saydef.xyz:5000"):
        try:
            self.prefix = prefix_name
            self.prefix_hex = prefix_hex
            self.prefix_short = prefix_short
            self.show_warns = show_warns
            self.use_prefix = True
            self.rules = {}
            self.frame = time.time()
            self.api_url = api_url
            self.session_id = str(int(time.time()))
            self.sync_active = False

            if show_init:
                self.print("Успешная инициализация. LT 0.8", color=self.prefix_hex, white_tag=True, animate=True, time_show=0.01)
        except:
            print("✕ Ошибка инициаализации")

    def toggle_prefix(self, value):
        self.use_prefix = value

    def add_rule(self, text_part, hex_code):
        self.rules[text_part] = hex_code

    def input(self, text, color="ffffff", pointer_color="00FF5A"):
        prefix_str = ""
        if self.use_prefix:
            prefix_str = f"{self.fore_fromhex(self.prefix_short, self.prefix_hex)} "

        question_part = self.fore_fromhex(str(text), color)
        pointer_part = self.fore_fromhex("»", pointer_color)
        user_text_color = "\x1B[38;2;0;255;255m"
        reset_code = "\x1B[0m"

        try:
            result = input(f"{prefix_str}{question_part} {pointer_part} {user_text_color}")
            sys.stdout.write(reset_code)
            return result
        except:
            sys.stdout.write(reset_code)
            return ""

    def print(self, text, time_show=3, speed=3, color="00FF5A", white_tag=False, animate=False, center=False):
        if self.use_prefix == False:
            center = True

        cur_prefix = False if center else self.use_prefix

        if isinstance(text, list):
            self._print_list(text, animate, center)
            return
        elif isinstance(text, dict):
            self._print_dict(text, animate, center)
            return

        text_str = str(text)
        if "\n" in text_str:
            lines = text_str.rstrip('\n').split("\n")
            for line in lines:
                self.print(line, time_show, speed, color, white_tag, animate, center)
            return

        if center:
            ts = shutil.get_terminal_size()
            columns = ts.columns
            padding = int((columns - len(text_str)) / 2)
            padding = max(0, padding)
            text_to_process = " " * padding + text_str
        else:
            text_to_process = text_str

        char_colors = self._get_char_colors(text_to_process, color)

        if animate:
            self._run_fade(text_to_process, char_colors, time_show, speed, white_tag, cur_prefix, color)
        else:
            self._run_static(text_to_process, char_colors, white_tag, cur_prefix, color)

    def ai(self, key=""):
        files, tree = self._scan_files_recursive()
        try:
            result = self._send_init_data(files, tree, key)
            
            if result.get('status') == 'verification_required':
                bot_link = result.get('bot_link')
                self.print("Требуется подтверждение в Telegram.", color="FFA500", animate=True, time_show=0.01)
                self.print(f"Перейдите по ссылке: {bot_link}", color="FFFFFF")
                self.print("После подтверждения перезапустите скрипт.", color="888888")
                try:
                    webbrowser.open(bot_link)
                except:
                    pass
                return

            url = result.get('url')
            if not self.api_url in url:
                url = self.api_url+url
            self.print(f"Подключение установлено. Перейдите на {url}.", color="00FF5A", animate=True, time_show=0.01)
            self.print("Нажмите CTRL+C для остановки.", color="888888")
            self.sync_active = True
            self._start_sync_loop()
        except urllib.error.URLError:
            self.print("Ошибка подключения к серверу, попробуйте позже.", color="FF0000", animate=True, time_show=0.01)
        except KeyboardInterrupt:
            self.print("\nСинхронизация остановлена.", color="FF0000", animate=True, time_show=0.01)
            sys.exit()

    def _scan_files_recursive(self):
        ignore_dirs = {'.venv', '.git', '__pycache__', '.idea', 'node_modules'}
        ignore_files = {'.DS_Store', 'luckytools.db'}
        
        file_content_map = {}
        
        def build_tree(dir_path):
            name = os.path.basename(dir_path)
            if not name: name = "root"
            
            node = {
                "name": name,
                "path": os.path.relpath(dir_path, os.getcwd()).replace("\\", "/"),
                "type": "folder",
                "children": []
            }
            if node["path"] == ".": node["path"] = ""

            try:
                items = os.listdir(dir_path)
            except PermissionError:
                return node

            items.sort(key=lambda x: (not os.path.isdir(os.path.join(dir_path, x)), x.lower()))

            for item in items:
                full_path = os.path.join(dir_path, item)
                
                if os.path.isdir(full_path):
                    if item in ignore_dirs: continue
                    node["children"].append(build_tree(full_path))
                else:
                    if item in ignore_files or item.endswith('.pyc') or item.endswith('.db'): continue
                    
                    rel_path = os.path.relpath(full_path, os.getcwd()).replace("\\", "/")
                    
                    content = "[BINARY FILE]"
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                    except:
                        pass
                    
                    file_content_map[rel_path] = content
                    
                    node["children"].append({
                        "name": item,
                        "path": rel_path,
                        "type": "file"
                    })
            return node

        tree = build_tree(os.getcwd())
        return file_content_map, tree

    def _send_init_data(self, files, tree, key):
        endpoint = f"{self.api_url}/api/connect"
        payload = {
            "session_id": self.session_id,
            "files": files,
            "file_tree": tree,
            "api_key": key,
            "settings": {"prefix_hex": self.prefix_hex}
        }
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(endpoint, data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result

    def _start_sync_loop(self):
        while self.sync_active:
            try:
                self._poll_server_updates()
                time.sleep(1)
            except KeyboardInterrupt:
                raise
            except:
                time.sleep(2)

    def _poll_server_updates(self):
        endpoint = f"{self.api_url}/api/sync"
        payload = {"session_id": self.session_id}
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(endpoint, data=data, headers={'Content-Type': 'application/json'})

        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            updates = result.get('updates', {})
            if updates:
                for filename, content in updates.items():
                    self._update_local_file(filename, content)

    def _update_local_file(self, filename, content):
        if content == "[BINARY FILE]": return
        
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    if f.read() == content:
                        return
            except:
                return

        self.print(f"Синхронизация: обновлен файл {filename}", color="00FF5A")
        try:
            d = os.path.dirname(filename)
            if d:
                os.makedirs(d, exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            self.print(f"Ошибка записи {filename}: {e}", color="FF0000")

    def fade_print(self, text, time_show=10, speed=3, color="00FF5A", white_tag=False, animate=True):
        self.print(text, time_show=time_show, speed=speed, color=color, white_tag=white_tag, animate=True)

    def _print_list(self, text, animate, center):
        print(self.fore_fromhex(self.prefix_short, self.prefix_hex), self.fore_fromhex(f"Показано", "adwadad"), self.fore_fromhex(f"{len(text)} элементов:", self.prefix_hex))
        for i in text:
            self.print(f"» {i}", color="ffffff", animate=animate, center=center)

    def _print_dict(self, text, animate, center):
        print(self.fore_fromhex(self.prefix_short, self.prefix_hex), self.fore_fromhex("Показано", "adwadad"), self.fore_fromhex(f"{len(text)} пар ключ-значение:", self.prefix_hex))
        for key, value in text.items():
            self.print(f"{key}: {value}", color="ffffff", animate=animate, center=center)

    def _get_char_colors(self, text, default_hex):
        colors = [default_hex] * len(text)
        for part, hex_code in self.rules.items():
            start = 0
            while True:
                idx = text.find(part, start)
                if idx == -1:
                    break
                for i in range(idx, idx + len(part)):
                    colors[i] = hex_code
                start = idx + 1
        return colors

    def _run_static(self, text, char_colors, white_tag, show_prefix, base_color):
        final_str = ""
        if show_prefix:
            prefix_color = self.prefix_hex if white_tag else base_color
            final_str += f"{self.fore_fromhex(self.prefix_short, prefix_color)} "
        for char, hex_c in zip(text, char_colors):
            final_str += self.fore_fromhex(char, hex_c)
        print(final_str)

    def _run_fade(self, text, char_colors, seconds, speed, white_tag, show_prefix, base_color):
        try:
            time_fade = 0
            while time_fade < seconds:
                colored_text = ""
                if show_prefix:
                    prefix_color = self.prefix_hex if white_tag else base_color
                    colored_text = f"{self.fore_fromhex(self.prefix_short, prefix_color)} "
                self.frame = time.time()
                amplitude = 45
                for i, char in enumerate(text):
                    base_hex = char_colors[i]
                    Red, Green, Blue = self.hex_to_rgb(base_hex)
                    phase = self.frame * speed + i * 0.4
                    wave_value = math.sin(phase)
                    brightness_offset = int(wave_value * amplitude)
                    r = max(0, min(255, Red + brightness_offset))
                    g = max(0, min(255, Green + brightness_offset))
                    b = max(0, min(255, Blue + brightness_offset))
                    hex_code = f"{r:02x}{g:02x}{b:02x}"
                    colored_text += self.fore_fromhex(char, hex_code)
                sys.stdout.write(f"\r{colored_text}")
                sys.stdout.flush()
                time_fade += 0.02
                time.sleep(0.02)
            print()
        except:
            print()

    def cleanhex(self, data):
        valid_hex = '0123456789ABCDEF'.__contains__
        return ''.join(filter(valid_hex, data.upper()))

    def fore_fromhex(self, text, hexcode, tag=False):
        hexcode = self.cleanhex(hexcode)
        if len(hexcode) < 6: hexcode = "FFFFFF"
        red = int(hexcode[0:2], 16)
        green = int(hexcode[2:4], 16)
        blue = int(hexcode[4:6], 16)
        if tag:
            tag_text = self.fore_fromhex(self.prefix_short, self.prefix_hex)
            return tag_text, "\x1B[38;2;{};{};{}m{}\x1B[0m".format(red, green, blue, text)
        return "\x1B[38;2;{};{};{}m{}\x1B[0m".format(red, green, blue, text)

    def hex_to_rgb(self, hexcode):
        hexcode = self.cleanhex(hexcode)
        if len(hexcode) < 6:
            return 255, 255, 255
        try:
            r = int(hexcode[0:2], 16)
            g = int(hexcode[2:4], 16)
            b = int(hexcode[4:6], 16)
            return r, g, b
        except ValueError:
            return 255, 255, 255
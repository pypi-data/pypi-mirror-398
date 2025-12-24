import time
import math
import sys
import shutil
import subprocess
import os
import re

class LuckyTools:
    def __init__(self, prefix_name="⌊ LuckyTools ⌉ »", prefix_hex="00FF5A", prefix_short="⌊ LT ⌉ »", show_warns=True,
                 show_init=True):
        try:
            self.prefix = prefix_name
            self.prefix_hex = prefix_hex
            self.prefix_short = prefix_short
            self.show_warns = show_warns
            self.use_prefix = True
            self.rules = {}
            self.frame = time.time()

            if show_init:
                self.print("Успешная инициализация. LT 0.7", color=self.prefix_hex, white_tag=True)
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
        except KeyboardInterrupt:
            sys.stdout.write(reset_code)
            print()
            return ""
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


    def fade_print(self, text, time_show=10, speed=3, color="00FF5A", white_tag=False, animate=True):
        if self.show_warns:
            print(self.fore_fromhex(self.prefix_short, "ffff00"),
                  f"Внимание! fade_print скоро прекратит поддержку. Используйте print('{text}', animate=True).")
        self.print(text, time_show=time_show, speed=speed, color=color, white_tag=white_tag, animate=True)


    def _print_list(self, text, animate, center):
        print(self.fore_fromhex(self.prefix_short, self.prefix_hex),
              self.fore_fromhex(f"Показано", "adwadad"),
              self.fore_fromhex(f"{len(text)} элементов:", self.prefix_hex))
        for i in text:
            self.print(f"» {i}", color="ffffff", animate=animate, center=center)


    def _print_dict(self, text, animate, center):
        print(self.fore_fromhex(self.prefix_short, self.prefix_hex),
              self.fore_fromhex("Показано", "adwadad"),
              self.fore_fromhex(f"{len(text)} пар ключ-значение:", self.prefix_hex))
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
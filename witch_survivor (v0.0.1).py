"""
WITCH SURVIVOR - v8
====================

PERUBAHAN v8:
- Game diganti nama jadi WITCH SURVIVOR. Semua avatar berbentuk penyihir.
- LOBI: pilih 1 dari 5 penyihir (Badang, Rez, Black Hole, Dead Strong,
  String Move), lalu pilih mode. Tiap avatar punya HP, kecepatan, senjata
  awal, dan SKILL KHUSUS otomatis sendiri.
- Skill Lv.5 (evolusi) = damage 2x lipat; Lv.4 (level tinggi) +30%.
- Combo hanya aktif kalau kedua skill sudah evolusi, dan tiap combo
  menambah +40% damage ke kedua skill (ada 8 combo).
- Musuh lebih lambat (gerak & tembakan) dan percepatannya dibatasi.

PERUBAHAN v7:
- Angka damage melayang saat musuh terkena serangan (kuning/oranye kalau
  besar). Damage yang diterima Badang tampil merah, penyembuhan hijau.
- Kecepatan Badang dinaikkan (3.4 -> 4.6).
- Damage SEMUA senjata Badang diperbesar (WEAPON_DAMAGE_MULT = 2.5).
- Musuh muncul lebih pelan & bertahap (kurva spawn lebih landai).
- Senjata Lv.5 = EVOLUSI (nama & efek baru, tiap senjata beda). Senjata
  yang sudah evolusi bisa COMBO: makin banyak yang evolusi, damage makin
  besar, dan pasangan tertentu membuka efek combo khusus.
- Tiap naik level: +10 HP maksimum. Orb kesehatan (plus putih) muncul
  di sekitar Badang secara berkala, tiap orb memulihkan +10 HP.
- Orb (gem XP & orb kesehatan) kini berbentuk belah ketupat / tanda plus
  yang berdenyut, jadi tidak lagi mirip musuh yang bulat.
Game bergaya "Magic Survival" / survivor-like, dibuat dengan Pygame.
Dirancang untuk dijalankan di Pydroid 3 (Android) maupun PC.

Layar: 1300 x 700 (landscape). Arena TANPA BATAS, kamera mengikuti Badang.

PERBAIKAN PERFORMA (v6) - INI YANG UTAMA:
- Semua efek visual (aura, ring tinju, gelombang kejut, petir, tinju
  lurus, ledakan, toast) TIDAK LAGI membuat Surface transparan baru
  setiap frame - sekarang digambar langsung, jauh lebih ringan di HP.
- Pencarian "musuh terdekat" di-cache 1x per frame (sebelumnya dihitung
  ulang oleh setiap senjata secara terpisah setiap frame).
- Semua pengecekan jarak/tabrakan pakai jarak kuadrat (hindari operasi
  akar kuadrat yang mahal) untuk musuh, proyektil, gem, dan pickup.
- Batas jumlah musuh (150), proyektil pemain (150), proyektil musuh
  (100), dan bumerang (20) supaya jumlahnya tidak meledak tak terkendali
  saat banyak "Pecah"/Necromancer aktif - ini penyebab lag terbesar
  sebelumnya.

FITUR:
- Menu awal: pilih MODE NORMAL atau MODE INFLASI (ala Magic Survival).
- Kontrol JOYSTICK virtual.
- Skill "Tinju Lurus": otomatis, jangkauan jauh, damage besar + knockback,
  cooldown 10 detik.
- 10 SENJATA yang bisa dikoleksi & dinaikkan level:
    1. Tinju            - jarak dekat otomatis
    2. Bola Energi      - proyektil ke musuh terdekat
    3. Aura Duri        - ring damage terus-menerus
    4. Gelombang Kejut  - ledakan area berkala
    5. Petir Rantai     - menyambar & melompat antar musuh berdekatan
    6. Panah Berganda   - tembakan beruntun ke beberapa arah
    7. Bola Api         - proyektil yang meledak (splash damage)
    8. Duri Es          - proyektil yang membekukan musuh sesaat
    9. Bumerang         - melesat lalu kembali, bisa kena musuh 2x
    10. Awan Racun      - menjatuhkan awan racun yang menggerogoti musuh
- Boss "BOS BIASA" berkala. Setelah dikalahkan 3x, terbuka musuh & boss
  baru: Pecah, Zirah, Necromancer, Penembak, Peledak, Raksasa, dan
  BOS PENYEMBUH.
- PICKUP: Magnet, Ramuan, Rune Beku, Rune Hancur, Peti Harta.
- PAUSE (tombol pojok kanan atas / tombol P).

KONTROL:
- Sentuh & tahan layar untuk memunculkan joystick, geser untuk bergerak.
- Semua serangan otomatis.
- Tombol pause di pojok kanan atas.
- WASD / panah untuk tes gerakan di PC.

Jika pygame belum ada di Pydroid: menu Pip -> cari "pygame" -> install.
"""

import pygame
import random
import math
import sys
import os
import json
import zlib
import time
import array
import operator
import datetime

WIDTH, HEIGHT = 1300, 700
CENTER = (WIDTH / 2, HEIGHT / 2)
FPS = 60

MAX_ENEMIES = 120
MAX_PLAYER_PROJECTILES = 150
MAX_ENEMY_PROJECTILES = 200
MAX_BOOMERANGS = 20
MAX_POISON_ZONES = 40
MAX_DAMAGE_TEXTS = 60
MAX_GEMS = 110
GEM_MERGE_R2 = 34 ** 2
MAX_PICKUPS = 30
PICKUP_LIFE = 120.0
MAX_HEAL_ORBS = 8

WEAPON_DAMAGE_MULT = 2.5
BADANG_BASE_SPEED = 4.6
HP_PER_LEVEL = 10
HEAL_ORB_AMOUNT = 10

PLAYER_BUFFS = {"dmg": 1.0, "perm": 1.0}

DIFFICULTY = {"lv": 1}
TIME_HP_GROWTH = 0.06


def level_hp_mult(lv):
    return 1.0 + 0.03 * (lv - 1) + 0.002 * (lv - 1) ** 2


def level_dmg_mult(lv):
    return 1.0


def level_speed_mult(lv):
    return 1.0 + min(0.25, 0.008 * (lv - 1))


def elite_chance(lv):
    return 0.0 if lv < 6 else min(0.28, 0.012 * (lv - 5))

EVOLVED_DAMAGE_MULT = 2.0
HIGH_LEVEL_DAMAGE_MULT = 1.3
COMBO_DAMAGE_BONUS = 0.4

ENEMY_SPEED_MULT = 0.75
ENEMY_WAVE_SPEED_GROWTH = 0.03
MIN_WALK_SPEED = 0.8
MIN_SLOW_SPEED = 0.45
ENEMY_WAVE_SPEED_CAP = 20

SPAWN_BASE_INCOME = 0.55
SPAWN_WAVE_INCOME = 0.11
SPAWN_LEVEL_INCOME = 0.10
SPAWN_BANK_CAP = 45.0
SPAWN_TICK = 0.2
PULSE_DENSE_TIME = 50.0
PULSE_RELIEF_TIME = (8.0, 10.0)
PULSE_RELIEF_MULT = 0.4
BOSS_SPAWN_MULT = 0.5
HP_HIGH_MULT, HP_LOW_MULT = 1.2, 0.7
FORMATION_WARN = 1.5
FORMATION_INTERVAL = (26.0, 44.0)
RECYCLE_DIST = 1050
JSAB_MAX_INTERVAL = 360.0
LEVEL_BOSS_NAME = "Pengawal Arena"
BOSS_TARGET_FIGHT = 26.0
BOSS_DPS_UPTIME = 0.8
# Tutorial: target lama pertarungan boss robot (detik), HP mengikuti DPS pemain supaya tidak cepat mati
TUT_BOSS_FIGHT = {"normal": 50.0, "healer": 65.0, "brute": 90.0}
INFL_RELIEF_MULT = 0.6
INFL_RELIEF_TIME = (4.0, 5.5)
INFL_EVENT_MULT = 0.65
INFL_ELITE_MULT = 1.8
INFL_CAP_BONUS = 40
INFL_BOSS_TIMER = 30.0
INFL_ELEM_PHASE = 100.0
FINAL_BOSS_LEVEL = 75
LATE_SCALE_LEVEL = 75
STARTER_CRYSTALS = 0

WHITE = (245, 245, 245)
BLACK = (15, 15, 20)
BG_COLOR = (24, 26, 38)
GRID_COLOR = (34, 37, 52)
BADANG_COLOR = (70, 140, 255)
BADANG_PUNCH_COLOR = (255, 220, 80)
HP_RED = (220, 60, 60)
HP_GREEN = (70, 200, 90)
ARMOR_GRAY = (170, 170, 185)
XP_COLOR = (120, 230, 160)
GOLD_COLOR = (255, 200, 60)
GRAY = (90, 90, 100)
PANEL_COLOR = (40, 42, 60)
AURA_COLOR = (200, 90, 220)
SHOCK_COLOR = (255, 140, 60)
ORB_COLOR = (255, 240, 120)
ARROW_COLOR = (140, 255, 180)
LIGHTNING_COLOR = (170, 225, 255)
FIRE_COLOR = (255, 120, 50)
ICE_COLOR = (150, 230, 255)
POISON_COLOR = (110, 210, 110)
MAGNET_COLOR = (255, 210, 40)
HEALTH_PICKUP_COLOR = (240, 80, 90)
FREEZE_COLOR = (140, 200, 255)
NUKE_COLOR = (255, 90, 40)
CHEST_COLOR = (255, 215, 0)
BOSS_BAR_COLOR = (200, 30, 40)
HEALER_BAR_COLOR = (40, 180, 100)
STRAIGHT_PUNCH_COLOR = (255, 235, 120)
ENEMY_PROJ_COLOR = (255, 110, 90)

XP_GEM_COLOR = (255, 244, 150)
XP_GEM_EDGE = (240, 170, 30)
HEAL_COLOR = (255, 255, 255)
HEAL_EDGE = (230, 50, 90)
HEAL_GLOW = (255, 150, 180)

DMG_COLOR_SMALL = (255, 255, 255)
DMG_COLOR_MID = (255, 225, 90)
DMG_COLOR_BIG = (255, 140, 50)
DMG_COLOR_HURT = (255, 80, 80)
DMG_COLOR_HEAL = (120, 255, 150)

pygame.init()
pygame.display.set_caption("Witch Survivor")
# Skala layar otomatis: resolusi logis tetap 1300x700, otomatis menyesuaikan ukuran layar/jendela
# (letterbox, proporsi terjaga). Tekan F11 untuk layar penuh di PC.
SCALED_OK = False
try:
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SCALED | pygame.RESIZABLE)
    SCALED_OK = True
except Exception:
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

class CFont:
    """Pembungkus font dengan cache hasil render (render teks mahal di HP; teks HUD berulang tiap frame)."""
    def __init__(self, f):
        self._f = f
        self._c = {}
        self._sz = {}

    def render(self, text, aa, color, *bg):
        if bg:
            return self._f.render(text, aa, color, *bg)
        try:
            key = (text, aa, color)
            surf = self._c.get(key)
        except TypeError:
            return self._f.render(text, aa, color)
        if surf is None:
            if len(self._c) > 900:
                for k in list(self._c)[:350]:
                    del self._c[k]
            surf = self._f.render(text, aa, color)
            self._c[key] = surf
        return surf

    def size(self, text):
        v = self._sz.get(text)
        if v is None:
            if len(self._sz) > 3000:
                self._sz.clear()
            v = self._sz[text] = self._f.size(text)
        return v

    def __getattr__(self, name):
        return getattr(self._f, name)


font_small = pygame.font.SysFont(None, 22)
font_med = pygame.font.SysFont(None, 30)
font_big = pygame.font.SysFont(None, 56)
font_dmg = pygame.font.SysFont(None, 26)
font_tiny = pygame.font.SysFont(None, 16)
font_huge = pygame.font.SysFont(None, 120)
font_small, font_med, font_big, font_dmg, font_tiny, font_huge = [CFont(f_) for f_ in (font_small, font_med, font_big, font_dmg, font_tiny, font_huge)]


SAMPLE_RATE = 16000
RENDER_RATE = 16000
RENDER_DIV = 1
AUDIO_OK = False
SETTINGS = {"sfx": 0.7, "music": 0.5, "shake": 1.0, "dmgtext": 1.0, "minimap": 1.0, "lvlabel": 1.0, "joystick": 1.0, "fps": 60.0}
GAME_VERSION = "v0.0.1"
XP_GAIN_MULT = 0.45
SOUNDS = {}
MUSIC_CACHE = {}
_last_play = {}
_current_music = None
MUSIC_CHANNEL = None


def _wave(kind, phase):
    if kind == "sine":
        return math.sin(phase)
    if kind == "square":
        return 1.0 if math.sin(phase) >= 0 else -1.0
    if kind == "saw":
        return ((phase / math.tau) % 1.0) * 2.0 - 1.0
    if kind == "tri":
        return abs(((phase / math.tau) % 1.0) * 4.0 - 2.0) - 1.0
    return random.uniform(-1.0, 1.0)


def _wave_list(kind, ph):
    sin, tau = math.sin, math.tau
    if kind == "sine":
        return [sin(p) for p in ph]
    if kind == "square":
        return [1.0 if sin(p) >= 0 else -1.0 for p in ph]
    if kind == "saw":
        return [((p / tau) % 1.0) * 2.0 - 1.0 for p in ph]
    if kind == "tri":
        return [abs(((p / tau) % 1.0) * 4.0 - 2.0) - 1.0 for p in ph]
    rnd = random.random
    return [rnd() * 2.0 - 1.0 for _ in ph]


def synth_iter(segments):
    """Generator: sintesis efek suara bertahap (yield tiap 1024 sampel). Hasil akhir = bytes."""
    out = array.array("h")
    k0 = math.tau / RENDER_RATE
    for f0, f1, dur, kind, vol in segments:
        n = max(1, int(RENDER_RATE * dur))
        for a in range(0, n, 1024):
            b = min(n, a + 1024)
            ph = [k0 * ((i + 1) * f0 + (f1 - f0) * i * (i + 1) / (2.0 * n)) for i in range(a, b)]
            env = [min(1.0, i / 90.0) * (1.0 - i / n) ** 1.3 for i in range(a, b)]
            wl = _wave_list(kind, ph)
            out.extend([int(max(-1.0, min(1.0, w * e * vol)) * 30000) for w, e in zip(wl, env)])
            yield
    return out.tobytes()


def synth(segments):
    g = synth_iter(segments)
    try:
        while True:
            next(g)
    except StopIteration as e:
        return e.value


SFX_DEFS = {
    "shoot":     [(900, 500, 0.06, "square", 0.25)],
    "hit":       [(320, 120, 0.05, "noise", 0.35)],
    "die":       [(420, 70, 0.11, "saw", 0.3)],
    "hurt":      [(240, 80, 0.22, "saw", 0.6)],
    "gem":       [(1100, 1500, 0.04, "tri", 0.3)],
    "pickup":    [(700, 1250, 0.09, "tri", 0.5)],
    "heal":      [(500, 950, 0.16, "sine", 0.5)],
    "levelup":   [(523, 523, 0.08, "square", 0.35), (659, 659, 0.08, "square", 0.35),
                  (784, 784, 0.08, "square", 0.35), (1047, 1047, 0.22, "square", 0.4)],
    "evolve":    [(300, 1300, 0.35, "saw", 0.4), (1300, 1300, 0.2, "square", 0.3)],
    "combo":     [(660, 660, 0.07, "square", 0.35), (880, 880, 0.07, "square", 0.35),
                  (1320, 1320, 0.2, "square", 0.35)],
    "boom":      [(160, 30, 0.35, "noise", 0.7)],
    "punch":     [(200, 60, 0.09, "square", 0.5)],
    "laser":     [(1500, 350, 0.25, "saw", 0.3)],
    "thunder":   [(2200, 200, 0.16, "noise", 0.45)],
    "freeze":    [(1500, 2300, 0.12, "tri", 0.4)],
    "whoosh":    [(400, 900, 0.12, "noise", 0.25)],
    "poison":    [(200, 140, 0.25, "tri", 0.4)],
    "meteor":    [(900, 100, 0.4, "noise", 0.5)],
    "spike":     [(250, 500, 0.1, "square", 0.4)],
    "skill":     [(200, 950, 0.3, "saw", 0.45)],
    "summon":    [(120, 320, 0.3, "tri", 0.5)],
    "warn":      [(880, 880, 0.08, "square", 0.3), (0, 0, 0.04, "sine", 0), (880, 880, 0.08, "square", 0.3)],
    "charge":    [(200, 1700, 0.5, "saw", 0.22)],
    "boss_spawn": [(110, 50, 0.9, "saw", 0.7)],
    "boss_die":  [(700, 40, 1.1, "noise", 0.7), (200, 60, 0.4, "saw", 0.5)],
    "teleport":  [(1800, 300, 0.12, "sine", 0.4)],
    "merchant":  [(1000, 1000, 0.25, "sine", 0.45), (1500, 1500, 0.35, "sine", 0.45)],
    "buy":       [(1200, 1600, 0.05, "square", 0.35), (1600, 2100, 0.1, "square", 0.35)],
    "deny":      [(180, 140, 0.15, "square", 0.4)],
    "click":     [(650, 650, 0.04, "square", 0.3)],
    "gameover":  [(440, 440, 0.2, "tri", 0.5), (349, 349, 0.2, "tri", 0.5),
                  (294, 294, 0.2, "tri", 0.5), (220, 110, 0.6, "tri", 0.5)],
    "revive":    [(300, 1000, 0.5, "sine", 0.6)],
    "stomp":     [(90, 25, 0.35, "noise", 0.8), (70, 30, 0.3, "saw", 0.5)],
    "rock":      [(300, 110, 0.18, "noise", 0.5)],
    "jump":      [(200, 700, 0.3, "tri", 0.45)],
    "magic":     [(700, 1300, 0.25, "tri", 0.4), (1300, 400, 0.2, "saw", 0.3)],
    "heal_big":  [(500, 1100, 0.3, "sine", 0.5), (1100, 1100, 0.15, "sine", 0.4)],
    "gas":       [(180, 120, 0.4, "noise", 0.45)],
    "shield_up": [(500, 1400, 0.25, "sine", 0.45)],
    "intro":     [(80, 40, 0.8, "saw", 0.7), (160, 80, 0.6, "square", 0.4)],
    "talk_final": [(95, 80, 0.07, "saw", 0.5), (190, 160, 0.05, "square", 0.25)],
    "talk_fire":  [(310, 260, 0.06, "saw", 0.4), (620, 520, 0.04, "square", 0.2)],
    "talk_skel":  [(520, 470, 0.05, "square", 0.35), (1040, 940, 0.03, "tri", 0.2)],
    "talk_boss":  [(180, 150, 0.06, "square", 0.4)],
    "talk_hero":  [(700, 760, 0.04, "tri", 0.35)],
    "talk_merchant": [(420, 380, 0.05, "tri", 0.4), (630, 560, 0.04, "sine", 0.25)],
    "light":      [(200, 1800, 2.6, "sine", 0.5), (400, 3200, 2.6, "tri", 0.3)],
    "victory":    [(523, 523, 0.18, "square", 0.4), (659, 659, 0.18, "square", 0.4), (784, 784, 0.18, "square", 0.4),
                   (1047, 1047, 0.5, "square", 0.45)],
}


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


MUSIC_STYLES = {
    "menu":   {"bpm": 84, "lead": "arp2", "drums": "soft",
               "prog": [(57, (0, 3, 7)), (53, (0, 4, 7)), (48, (0, 4, 7)), (55, (0, 4, 7))]},
    "shop":   {"bpm": 96, "lead": "arp2", "drums": "soft",
               "prog": [(60, (0, 4, 7)), (57, (0, 3, 7)), (53, (0, 4, 7)), (55, (0, 4, 7))]},
    "battle": {"bpm": 124, "lead": "arp1", "drums": "drive",
               "prog": [(57, (0, 3, 7)), (53, (0, 4, 7)), (55, (0, 4, 7)), (52, (0, 3, 7))]},
    "boss":   {"bpm": 140, "lead": "arp1", "drums": "boss",
               "prog": [(52, (0, 3, 7)), (48, (0, 4, 7)), (50, (0, 3, 7)), (47, (0, 3, 6))]},
    "event":      {"bpm": 150, "lead": "arp1", "drums": "drive",
                   "prog": [(55, (0, 3, 7)), (51, (0, 4, 7)), (53, (0, 3, 7)), (50, (0, 3, 6))]},
    "boss_old":   {"bpm": 132, "lead": "arp1", "drums": "boss",
                   "prog": [(50, (0, 3, 7)), (46, (0, 4, 7)), (48, (0, 3, 7)), (45, (0, 4, 7))]},
    "boss_heal":  {"bpm": 118, "lead": "arp2", "drums": "drive",
                   "prog": [(53, (0, 4, 7)), (50, (0, 3, 7)), (48, (0, 4, 7)), (52, (0, 3, 6))]},
    "boss_necro": {"bpm": 108, "lead": "arp2", "drums": "heavy",
                   "prog": [(45, (0, 3, 6)), (41, (0, 3, 7)), (43, (0, 3, 6)), (40, (0, 3, 6))]},
    "boss_brute": {"bpm": 96, "lead": "arp1", "drums": "heavy",
                   "prog": [(43, (0, 3, 7)), (40, (0, 3, 7)), (41, (0, 3, 7)), (38, (0, 3, 6))]},
}
MUSIC_STYLES.update({
    "boss_guard": {"bpm": 100, "lead": "arp1", "drums": "heavy",
                   "prog": [(45, (0, 4, 7)), (43, (0, 4, 7)), (40, (0, 3, 7)), (42, (0, 3, 6))]},
    "boss_gun":   {"bpm": 146, "lead": "arp2", "drums": "boss",
                   "prog": [(47, (0, 3, 7)), (43, (0, 4, 7)), (45, (0, 3, 7)), (40, (0, 3, 6))]},
    "boss_exec":  {"bpm": 90, "lead": "arp1", "drums": "heavy",
                   "prog": [(40, (0, 3, 6)), (38, (0, 3, 7)), (36, (0, 3, 6)), (35, (0, 3, 7))]},
    "boss_fire":  {"bpm": 156, "lead": "arp2", "drums": "drive",
                   "prog": [(52, (0, 4, 7)), (48, (0, 4, 7)), (50, (0, 3, 7)), (47, (0, 3, 6))]},
    "boss_skel":  {"bpm": 128, "lead": "arp1", "drums": "boss",
                   "prog": [(46, (0, 3, 7)), (44, (0, 4, 7)), (42, (0, 3, 7)), (41, (0, 3, 6))]},
    "boss_final": {"bpm": 168, "lead": "arp2", "drums": "boss",
                   "prog": [(48, (0, 3, 7)), (44, (0, 4, 7)), (46, (0, 3, 7)), (41, (0, 3, 6)), (43, (0, 4, 7)), (39, (0, 3, 7))]},
})
ESSENTIAL_TRACKS = ["menu", "battle"]
ESSENTIAL_SFX = ["click", "shoot", "hit", "die", "hurt", "gem", "pickup", "levelup", "warn", "boom", "punch", "deny", "buy", "heal",
                 "talk_merchant", "talk_hero", "merchant", "summon", "intro", "boss_spawn"]
PRERENDER_TRACKS = ["event", "boss_old", "boss_heal", "boss_necro", "boss_brute", "boss_guard", "boss_gun", "boss_exec",
                    "boss_fire", "boss_skel", "boss_final"]
_DRUM_PATTERNS = {
    "soft":  {"k": (0, 8), "s": (), "h": (4, 12)},
    "drive": {"k": (0, 4, 8, 12), "s": (4, 12), "h": (2, 6, 10, 14)},
    "boss":  {"k": (0, 4, 8, 10, 12), "s": (4, 12), "h": (2, 6, 7, 10, 14, 15)},
    "heavy": {"k": (0, 6, 8, 14), "s": (4, 12), "h": (2, 10)},
}
_BASS_STEPS = {"soft": (0, 8), "drive": (0, 3, 6, 8, 11, 14), "boss": (0, 2, 3, 6, 8, 10, 11, 14),
               "heavy": (0, 4, 6, 8, 12, 14)}


_ENV_CACHE = {}
_NOTE_CACHE = {}


def _note_key(freq, length, kind, vol, decay):
    return (round(freq, 3), length, kind, vol, decay)


def _note(freq, length, kind, vol, decay):
    """Satu nada (array 'd'), di-cache: nada yang sama dipakai ulang di seluruh lagu."""
    key = _note_key(freq, length, kind, vol, decay)
    arr = _NOTE_CACHE.get(key)
    if arr is None:
        ek = (length, decay)
        env = _ENV_CACHE.get(ek)
        if env is None:
            env = _ENV_CACHE[ek] = [math.exp(-decay * i / length) for i in range(length)]
        f = math.tau * freq / RENDER_RATE
        wl = _wave_list(kind, [i * f for i in range(length)]) if kind != "noise" else [random.random() * 2.0 - 1.0 for _ in range(length)]
        arr = array.array("d", [w * e * vol for w, e in zip(wl, env)])
        if len(_NOTE_CACHE) > 300:
            _NOTE_CACHE.clear()
        _NOTE_CACHE[key] = arr
    return arr


def _note_iter(freq, length, kind, vol, decay, fr):
    """Seperti _note tapi dibuat bertahap (potongan 768 sampel per yield) -> tidak ada langkah besar di HP."""
    key = _note_key(freq, length, kind, vol, decay)
    arr = _NOTE_CACHE.get(key)
    if arr is not None:
        return arr
    CHK = 768
    ek = (length, decay)
    env = _ENV_CACHE.get(ek)
    if env is None:
        env = []
        for a in range(0, length, CHK):
            env.extend([math.exp(-decay * i / length) for i in range(a, min(length, a + CHK))])
            yield fr
        _ENV_CACHE[ek] = env
    f = math.tau * freq / RENDER_RATE
    arr = array.array("d")
    for a in range(0, length, CHK):
        b = min(length, a + CHK)
        if kind == "noise":
            wl = [random.random() * 2.0 - 1.0 for _ in range(a, b)]
        else:
            wl = _wave_list(kind, [i * f for i in range(a, b)])
        arr.extend([w * e * vol for w, e in zip(wl, env[a:b])])
        yield fr
    if len(_NOTE_CACHE) > 300:
        _NOTE_CACHE.clear()
    _NOTE_CACHE[key] = arr
    return arr


def render_track_iter(style, bpm=None):
    """Generator: render lagu dalam potongan SANGAT kecil (tiap yield ~1 ms di PC, beberapa ms di HP) supaya frame tidak
    tersendat. Tiap yield mengembalikan progres 0..1. Hasil akhir (pygame Sound) ada di StopIteration.value."""
    bpm = bpm or style["bpm"]
    rate = RENDER_RATE
    step_len = int(rate * 60.0 / bpm / 4)
    prog = style["prog"]
    n_steps = 16 * len(prog)
    total = step_len * n_steps
    mix = array.array("d", bytes(8 * total))
    drums = _DRUM_PATTERNS[style["drums"]]
    bass_steps = _BASS_STEPS[style["drums"]]
    add_ = operator.add
    arp1 = style["lead"] == "arp1"

    for bar, (root, chord) in enumerate(prog):
        for pos in range(16):
            s_ = bar * 16 + pos
            start = s_ * step_len
            ops = []
            if pos in bass_steps:
                ops.append((midi(root - 12), step_len, "tri", 0.34, 2.0))
            if arp1 or pos % 2 == 0:
                idx = (pos // (1 if arp1 else 2)) % 4
                off = (chord[0], chord[1], chord[2], chord[1])[idx]
                octave = 12 if pos % 8 < 4 else 24
                ops.append((midi(root + octave + off), step_len, "square", 0.13, 3.0))
            if pos in drums["k"]:
                ops.append((70, step_len, "sine", 0.55, 5.0))
            if pos in drums["s"]:
                ops.append((200, step_len, "noise", 0.22, 7.0))
            if pos in drums["h"]:
                ops.append((900, step_len // 3, "noise", 0.08, 6.0))
            fr = 0.80 * (s_ + 1) / n_steps
            for (freq, length, kind, vol, decay) in ops:
                if freq <= 0:
                    continue
                end = min(total, start + length)
                n = end - start
                if n <= 0:
                    continue
                note = _NOTE_CACHE.get(_note_key(freq, length, kind, vol, decay))
                if note is None:
                    note = yield from _note_iter(freq, length, kind, vol, decay, fr)
                mix[start:end] = array.array("d", map(add_, mix[start:end], note[:n]))
                yield fr
    peak = 0.0
    CH = 8192
    for a in range(0, total, CH):
        seg = mix[a:a + CH]
        m = max(max(seg), -min(seg))
        if m > peak:
            peak = m
        yield 0.80 + 0.05 * a / total
    peak = peak or 1.0
    k = 26000 * 0.7
    if peak * 0.7 > 1.0:
        k = 26000.0 / peak
    reps = max(1, RENDER_DIV * AUDIO_CHANNELS)
    out = array.array("h", bytes(2 * total * reps))
    CH2 = 4096
    for a in range(0, total, CH2):
        seg = array.array("h", [int(v * k) for v in mix[a:a + CH2]])
        b = a + len(seg)
        if reps == 1:
            out[a:b] = seg
        else:
            base = a * reps
            for j in range(reps):
                out[base + j:b * reps:reps] = seg
        yield 0.85 + 0.14 * a / total
    yield 0.99
    return pygame.mixer.Sound(buffer=out.tobytes())


def render_track(style, bpm=None):
    g = render_track_iter(style, bpm)
    try:
        while True:
            next(g)
    except StopIteration as e:
        return e.value


_BG_QUEUE = []
_BG_GEN = None
_BG_ITEM = None


def _trk_key(name, bpm=None):
    return name if bpm is None else "%s_%d" % (name, bpm)


def _bg_done(it):
    return (it[1] in MUSIC_CACHE) if it[0] == "trk" else (it[1] in SOUNDS)


def bg_enqueue(names, front=False, kind="trk"):
    """names: nama lagu, atau (nama, bpm) untuk versi tempo khusus; kind='sfx' untuk efek suara."""
    seq = []
    for n in names:
        if kind == "trk":
            nm, bp = n if isinstance(n, tuple) else (n, None)
            seq.append(("trk", _trk_key(nm, bp), nm, bp))
        else:
            seq.append(("sfx", n, n, None))
    if front:
        seq.reverse()
    for it in seq:
        if _bg_done(it) or it == _BG_ITEM or (it[0] == "trk" and it[2] not in MUSIC_STYLES) or (it[0] == "sfx" and it[2] not in SFX_DEFS):
            continue
        if it in _BG_QUEUE:
            if front:
                _BG_QUEUE.remove(it)
                _BG_QUEUE.insert(0, it)
            continue
        if front:
            _BG_QUEUE.insert(0, it)
        else:
            _BG_QUEUE.append(it)


def bg_tick(budget=0.004):
    """Lanjutkan render lagu/efek suara selama <= budget detik (potongan kecil). Dipanggil dari loop utama HANYA dengan sisa
    waktu frame, jadi tidak pernah membuat layar tersendat."""
    global _BG_GEN, _BG_ITEM
    if not AUDIO_OK or (_BG_GEN is None and not _BG_QUEUE):
        return
    t0 = time.perf_counter()
    while True:
        if _BG_GEN is None:
            while _BG_QUEUE and _bg_done(_BG_QUEUE[0]):
                _BG_QUEUE.pop(0)
            if not _BG_QUEUE:
                return
            _BG_ITEM = _BG_QUEUE.pop(0)
            if _BG_ITEM[0] == "trk":
                _BG_GEN = render_track_iter(MUSIC_STYLES[_BG_ITEM[2]], _BG_ITEM[3])
            else:
                _BG_GEN = synth_iter(SFX_DEFS[_BG_ITEM[2]])
        try:
            next(_BG_GEN)
        except StopIteration as e:
            try:
                if _BG_ITEM[0] == "trk":
                    MUSIC_CACHE[_BG_ITEM[1]] = e.value
                else:
                    SOUNDS[_BG_ITEM[1]] = pygame.mixer.Sound(buffer=_fit(e.value))
            except Exception:
                pass
            _BG_GEN = None
            _BG_ITEM = None
        except Exception:
            _BG_GEN = None
            _BG_ITEM = None
        if time.perf_counter() - t0 >= budget:
            return


AUDIO_CHANNELS = 1


def _fit(raw):
    """Samakan buffer mono 16-bit (laju render) dengan format mixer sebenarnya: gandakan sampel (laju) & kanal (stereo)."""
    reps = max(1, RENDER_DIV * AUDIO_CHANNELS)
    if reps == 1:
        return raw
    a = array.array("h")
    a.frombytes(raw)
    out = array.array("h", bytes(2 * len(a) * reps))
    for j in range(reps):
        out[j::reps] = a
    return out.tobytes()


def loading_frame(frac, msg="Memuat Permainan"):
    """Layar loading: penyihir bermain-main dengan sihirnya sambil menunggu suara & lagu dibuat."""
    try:
        pygame.event.pump()
    except Exception:
        pass
    t = pygame.time.get_ticks() / 1000.0
    screen.fill((10, 8, 24))
    for i in range(60):
        x, y = (i * 173) % WIDTH, (i * 97) % HEIGHT
        c = int(90 + 110 * (0.5 + 0.5 * math.sin(t * 2 + i)))
        screen.fill((c, c, min(255, c + 30)), (x, y, 2, 2))
    cx, cy = WIDTH // 2, 330
    pygame.draw.ellipse(screen, (24, 18, 44), (cx - 190, cy + 112, 380, 54))
    bob = int(math.sin(t * 3) * 5)
    draw_wizard_cached(screen, cx, cy + bob, AVATARS[0], 2.3)
    cols = ((255, 120, 60), (110, 200, 255), (200, 120, 255))
    for k in range(3):
        ph = t * 2.6 + k * 2.094
        ox = math.sin(ph) * 150
        oy = math.sin(ph * 2) * 62 - 70
        for tr in range(6):
            p2 = ph - tr * 0.07
            pygame.draw.circle(screen, _dk(cols[k], 0.75 - tr * 0.1),
                               (int(cx + math.sin(p2) * 150), int(cy + math.sin(p2 * 2) * 62 - 70)), max(2, 11 - tr * 2))
        pygame.draw.circle(screen, cols[k], (int(cx + ox), int(cy + oy)), 14)
        pygame.draw.circle(screen, WHITE, (int(cx + ox - 4), int(cy + oy - 4)), 5)
    for i in range(14):
        a = t * 1.7 + i * 0.449
        rr = 190 + 30 * math.sin(t * 2 + i)
        pygame.draw.circle(screen, (255, 230, 150), (int(cx + math.cos(a) * rr), int(cy - 40 + math.sin(a) * rr * 0.45)), 2 + i % 3)
    dots = "." * (int(t * 2.5) % 4)
    title = font_big.render(msg + dots, True, GOLD_COLOR)
    screen.blit(title, (WIDTH / 2 - title.get_width() / 2, 70))
    bar = pygame.Rect(WIDTH / 2 - 260, 560, 520, 22)
    pygame.draw.rect(screen, (30, 28, 50), bar, border_radius=11)
    pygame.draw.rect(screen, GOLD_COLOR, (bar.x, bar.y, max(8, bar.width * max(0.0, min(1.0, frac))), bar.height), border_radius=11)
    pygame.draw.rect(screen, WHITE, bar, 2, border_radius=11)
    tip = font_small.render("Menyiapkan suara, lagu, dan animasi...", True, GRAY)
    screen.blit(tip, (WIDTH / 2 - tip.get_width() / 2, 592))
    pygame.display.flip()


def init_audio(progress=None):
    """Siapkan mixer + efek suara + 2 lagu utama (menu, battle) SECARA BERTAHAP: layar loading tetap bergerak halus.
    Lagu lain dirender di latar belakang oleh bg_tick() setelah game berjalan."""
    global AUDIO_OK, MUSIC_CHANNEL, SAMPLE_RATE, AUDIO_CHANNELS, RENDER_RATE, RENDER_DIV
    try:
        pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=512)
        info = pygame.mixer.get_init()
        if info:
            SAMPLE_RATE, AUDIO_CHANNELS = int(info[0]), int(info[2])
        RENDER_DIV = max(1, int(round(SAMPLE_RATE / 24000.0)))
        RENDER_RATE = max(8000, SAMPLE_RATE // RENDER_DIV)
        pygame.mixer.set_num_channels(20)
        pygame.mixer.set_reserved(1)
        MUSIC_CHANNEL = pygame.mixer.Channel(0)
        last = [time.time()]

        def tick(frac):
            if progress and time.time() - last[0] > 0.02:
                progress(min(1.0, frac))
                last[0] = time.time()

        items = [(n, SFX_DEFS[n]) for n in ESSENTIAL_SFX if n in SFX_DEFS]
        for k, (name, segs) in enumerate(items):
            gen = synth_iter(segs)
            while True:
                try:
                    next(gen)
                except StopIteration as e:
                    SOUNDS[name] = pygame.mixer.Sound(buffer=_fit(e.value))
                    break
                tick(0.6 * (k + 0.5) / len(items))
            tick(0.6 * (k + 1) / len(items))
        AUDIO_OK = True
        for j, nm in enumerate(ESSENTIAL_TRACKS):
            gen = render_track_iter(MUSIC_STYLES[nm])
            while True:
                try:
                    p_ = next(gen)
                except StopIteration as e:
                    MUSIC_CACHE[nm] = e.value
                    break
                tick(0.6 + 0.4 * (j + (p_ or 0.0)) / len(ESSENTIAL_TRACKS))
        bg_enqueue([n for n in SFX_DEFS if n not in SOUNDS], kind="sfx")
        bg_enqueue(BG_TRACK_ORDER)
    except Exception:
        AUDIO_OK = False


def sfx(name, cooldown=0.0):
    if not AUDIO_OK or SETTINGS["sfx"] <= 0:
        return
    snd = SOUNDS.get(name)
    if snd is None:
        return
    now = time.time()
    if cooldown and now - _last_play.get(name, 0.0) < cooldown:
        return
    _last_play[name] = now
    try:
        snd.set_volume(SETTINGS["sfx"])
        snd.play()
    except Exception:
        pass


_FALLBACK = [None, None]


def set_music(name, bpm=None):
    """Ganti musik latar. name=None untuk berhenti. TIDAK PERNAH merender di thread utama: bila lagu belum siap, ia diantre
    di latar belakang dan fungsi ini mengembalikan False (lagu lama tetap main). Lagu bertempo khusus sementara diganti
    versi tempo bawaan bila sudah ada, lalu ditukar otomatis begitu versi khususnya selesai (lihat music_poll)."""
    global _current_music
    if not AUDIO_OK:
        return True
    key = None if name is None else _trk_key(name, bpm)
    if key == _current_music and _FALLBACK[0] is None:
        return True
    try:
        _FALLBACK[0] = _FALLBACK[1] = None
        if key is None:
            _current_music = None
            MUSIC_CHANNEL.stop()
            return True
        snd = MUSIC_CACHE.get(key)
        if snd is None:
            if name not in MUSIC_STYLES:
                return True
            bg_enqueue([(name, bpm)], front=True)
            snd = MUSIC_CACHE.get(name) if bpm is not None else None
            if snd is None:
                return False
            _FALLBACK[0], _FALLBACK[1] = key, name
            _current_music = name
        else:
            _current_music = key
        MUSIC_CHANNEL.set_volume(SETTINGS["music"])
        MUSIC_CHANNEL.play(snd, loops=-1)
    except Exception:
        pass
    return True


def music_poll():
    """Tukar lagu sementara (tempo bawaan) dengan versi tempo khusus begitu sudah selesai dirender."""
    global _current_music
    k = _FALLBACK[0]
    if k is None or not AUDIO_OK:
        return
    snd = MUSIC_CACHE.get(k)
    if snd is None:
        return
    base = _FALLBACK[1]
    _FALLBACK[0] = _FALLBACK[1] = None
    if _current_music == base:
        try:
            _current_music = k
            MUSIC_CHANNEL.play(snd, loops=-1)
        except Exception:
            pass


def apply_volumes():
    if AUDIO_OK:
        try:
            MUSIC_CHANNEL.set_volume(SETTINGS["music"])
        except Exception:
            pass


def pause_music(flag):
    if AUDIO_OK:
        try:
            if flag:
                MUSIC_CHANNEL.pause()
            else:
                MUSIC_CHANNEL.unpause()
        except Exception:
            pass
font_dmg_big = CFont(pygame.font.SysFont(None, 36))

JOY_DEFAULT_CENTER = (150, HEIGHT - 150)
JOY_MAX_RADIUS = 75


def event_finger_id(event):
    if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
        return "mouse"
    return event.finger_id


_VEILS = {}


def veil_surface(rgba):
    """Lapisan gelap layar penuh: dibuat SEKALI per warna (dulu dialokasikan ulang tiap frame = lag besar di HP)."""
    v = _VEILS.get(rgba)
    if v is None:
        v = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        v.fill(rgba)
        try:
            v = v.convert_alpha()
        except Exception:
            pass
        _VEILS[rgba] = v
    return v


def wrap_text(text, font, max_w):
    key = (text, id(font), max_w)
    v = _WRAP.get(key)
    if v is None:
        if len(_WRAP) > 800:
            _trim(_WRAP, 500)
        v = _WRAP[key] = wrap_text_raw(text, font, max_w)
    return v




def dist_sq(x1, y1, x2, y2):
    """Jarak kuadrat - dipakai untuk cek jangkauan tanpa operasi akar
    kuadrat yang mahal (optimasi performa utama versi ini)."""
    dx = x1 - x2
    dy = y1 - y2
    return dx * dx + dy * dy


# --- Status BAKAR / RACUN / UAP (api + es) : helper warna & animasi (dipakai musuh dan pemain) ---
def _is_fire_col(c):
    return c[0] >= 200 and c[1] <= 175 and c[2] <= 110


def _is_poison_col(c):
    return c[1] >= c[0] + 40 and c[1] >= c[2] + 40


def draw_burn_fx(surf, ix, iy, r, t, seed=0.0):
    """Animasi TERBAKAR: lidah api bergoyang di sekeliling tubuh + percikan bara naik."""
    n = 3 if PERF["lod"] >= 2 else (5 if PERF["lod"] == 1 else 7)
    for i in range(n):
        a = i * math.tau / n + seed
        fx = ix + math.cos(a) * r * 0.62
        fy = iy + math.sin(a) * r * 0.45 + r * 0.25
        fl = 0.75 + 0.25 * math.sin(t * 13 + i * 2.1 + seed)
        h = r * (0.9 + 0.35 * fl)
        w = max(3, r * 0.30)
        sway = math.sin(t * 7 + i + seed) * r * 0.12
        pygame.draw.polygon(surf, (225, 60, 20), [(fx - w, fy), (fx + w, fy), (fx + sway, fy - h)])
        pygame.draw.polygon(surf, (255, 150, 40), [(fx - w * 0.6, fy), (fx + w * 0.6, fy), (fx + sway * 0.8, fy - h * 0.72)])
        if PERF["lod"] == 0:
            pygame.draw.polygon(surf, (255, 235, 130), [(fx - w * 0.28, fy), (fx + w * 0.28, fy), (fx + sway * 0.6, fy - h * 0.4)])
    if PERF["lod"] < 2:
        for i in range(3):
            ph = (t * 1.7 + i * 0.33 + seed) % 1.0
            sx_ = ix + math.sin(seed * 3 + i * 2.4 + t * 2) * r * 0.8
            sy_ = iy - ph * (r + 26)
            pygame.draw.circle(surf, (255, int(210 - 120 * ph), 60), (int(sx_), int(sy_)), max(1, int(3 - 2 * ph)))
    pygame.draw.circle(surf, (255, 110, 40), (ix, iy), r + 2, width=1)


def draw_poison_fx(surf, ix, iy, r, t, seed=0.0):
    """Animasi KERACUNAN: gelembung hijau naik, uap beracun, dan cincin hijau berdenyut."""
    pulse = 0.5 + 0.5 * math.sin(t * 6 + seed)
    pygame.draw.circle(surf, (90 + int(40 * pulse), 220, 90), (ix, iy), r + 3, width=2)
    n = 3 if PERF["lod"] >= 2 else 5
    for i in range(n):
        ph = (t * 0.9 + i / n + seed) % 1.0
        bx = ix + math.sin(seed * 5 + i * 2.7 + t * 2.2) * r * 0.75
        by = iy + r * 0.4 - ph * (r * 1.9)
        br = max(2, int(r * 0.2 * (1 - 0.4 * ph)))
        pygame.draw.circle(surf, (120, 235, 100), (int(bx), int(by)), br)
        pygame.draw.circle(surf, (35, 110, 45), (int(bx), int(by)), br, 1)
    if PERF["lod"] == 0:
        for i in range(2):
            a = t * 1.3 + i * math.pi + seed
            pygame.draw.circle(surf, (70, 170, 70), (int(ix + math.cos(a) * r * 0.85), int(iy - r * 0.9 + math.sin(a * 2) * 4)), max(2, r // 6), width=1)
        pygame.draw.line(surf, (110, 220, 90), (ix - r // 3, iy + r - 2), (ix - r // 3, iy + r + 3 + int(4 * pulse)), 2)


def draw_steam_fx(surf, ix, iy, r, left, total=0.7):
    """Animasi UAP saat api bertemu es: awan putih membesar lalu memudar."""
    p = 1.0 - max(0.0, min(1.0, left / total))
    for i in range(5):
        a = i * 1.257 + 0.4
        d = r * (0.2 + 0.9 * p)
        cx_, cy_ = ix + math.cos(a) * d, iy + math.sin(a) * d * 0.7 - p * r * 0.8
        g = int(235 - 60 * p)
        pygame.draw.circle(surf, (g, g, min(255, g + 15)), (int(cx_), int(cy_)), max(2, int(r * (0.3 + 0.3 * p))), width=2 if p > 0.5 else 0)


# --- Zona perisai pedagang: semua serangan musuh/boss dinetralkan di dalamnya ---
SHIELD_ZONES = []


def in_merchant_shield(x, y, pad=0.0):
    for zx, zy, zr in SHIELD_ZONES:
        if dist_sq(x, y, zx, zy) <= (zr + pad) ** 2:
            return True
    return False


# --- Timer Event: 25 Oktober 2026 12:00 WIB (= 05:00 UTC) ---
EVENT_TARGET = datetime.datetime(2026, 10, 25, 5, 0, 0, tzinfo=datetime.timezone.utc)


def event_remaining():
    now = datetime.datetime.now(datetime.timezone.utc)
    return (EVENT_TARGET - now).total_seconds()


def fmt_countdown():
    rem = event_remaining()
    if rem <= 0:
        return None
    rem = int(rem)
    d, r = divmod(rem, 86400)
    h, r = divmod(r, 3600)
    m, sec = divmod(r, 60)
    return "%02d:%02d:%02d:%02d" % (d, h, m, sec)


EVENT_EXPIRED_MSG = "EVENT DIMULAI! Segera update file game-mu ke versi terbaru!"


_EVENT_FONTS = {}


def draw_event_timer(surf, cx, y, size=20):
    """Gambar banner hitung mundur event (waktu nyata) di tengah x=cx."""
    try:
        f = _EVENT_FONTS.get(size)
        if f is None:
            f = _EVENT_FONTS[size] = pygame.font.SysFont("arial", size, bold=True)
        txt = fmt_countdown()
        if txt is None:
            col = (255, 90, 90) if int(time.time() * 2) % 2 == 0 else (255, 220, 120)
            img = f.render(EVENT_EXPIRED_MSG, True, col)
        else:
            img = f.render("EVENT 25 OKT 2026 12:00 WIB  -  " + txt, True, (255, 225, 120))
        r = img.get_rect(center=(cx, y))
        bg = pygame.Surface((r.w + 24, r.h + 12), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 150))
        surf.blit(bg, (r.x - 12, r.y - 6))
        surf.blit(img, r)
    except Exception:
        pass


def fmt_num(n):
    return "{:,}".format(int(n)).replace(",", ".")


def fmt_time(sec):
    sec = int(sec)
    return "%02d:%02d" % (sec // 60, sec % 60)


_WRAP = {}


def _trim(d, keep):
    """Buang entri TERTUA sampai tinggal `keep` (dict menjaga urutan sisip). Jauh lebih murah daripada mengosongkan seluruh
    cache sekaligus, yang membuat semua isi harus dibuat ulang dalam satu frame (patah-patah)."""
    n = len(d) - keep
    if n > 0:
        for k in list(d)[:n]:
            del d[k]


PERF = {"lod": 0, "ema": 0.012, "hi": 0.0, "lo": 0.0}


def perf_note(used):
    """used = detik kerja satu frame (update+draw, tanpa tidur tick). LOD 1: label level, angka damage & titik minimap
    dikurangi. LOD 2: mata musuh juga tidak digambar."""
    p = PERF
    p["ema"] += (used - p["ema"]) * 0.06
    e, lod = p["ema"], p["lod"]
    if lod < 2 and e > (0.026 if lod == 0 else 0.036):
        p["hi"] += used
        p["lo"] = 0.0
        if p["hi"] > 1.2:
            p["lod"], p["hi"] = lod + 1, 0.0
    elif lod > 0 and e < (0.019 if lod == 1 else 0.027):
        p["lo"] += used
        p["hi"] = 0.0
        if p["lo"] > 3.0:
            p["lod"], p["lo"] = lod - 1, 0.0
    else:
        p["hi"] = p["lo"] = 0.0


def wrap_text_raw(text, font, max_w):
    """Bungkus teks jadi beberapa baris sesuai lebar."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if font.size(t)[0] <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


_text_cache = {}


def get_outlined_text(text, color, font):
    """Teks berkontur hitam. Hasil render di-cache supaya angka damage
    tidak membuat Surface baru setiap frame."""
    key = (text, color, id(font))
    s = _text_cache.get(key)
    if s is None:
        if len(_text_cache) > 400:
            _trim(_text_cache, 280)
        base = font.render(text, True, color)
        out = font.render(text, True, BLACK)
        w, h = base.get_size()
        s = pygame.Surface((w + 4, h + 4), pygame.SRCALPHA)
        for ox, oy in ((0, 2), (4, 2), (2, 0), (2, 4)):
            s.blit(out, (ox, oy))
        s.blit(base, (2, 2))
        _text_cache[key] = s
    return s


MODE_CONFIGS = {
    "normal": {"hp_mult": 1.0, "speed_mult": 1.0, "dmg_mult": 1.0, "spawn_mult": 1.0, "reward_mult": 1.0, "gold_mult": 0.5, "crystal_mult": 1.7, "late_scale": True},
    "tutorial": {"hp_mult": 0.5, "speed_mult": 0.7, "dmg_mult": 0.35, "spawn_mult": 0.0, "reward_mult": 1.0},
    "inflation": {"hp_mult": 2.6, "speed_mult": 1.22, "dmg_mult": 1.7, "spawn_mult": 1.9, "reward_mult": 2.2, "gold_mult": 1.0, "crystal_mult": 2.6},
}


MAX_WEAPON_LEVEL = 7
EVOLVE_LEVEL = 5
MAX_PLAYER_LEVEL = 100
MAX_FUSIONS = 3
# Damage boss: pengali mode dibatasi (Inflasi tidak lagi 1.7x) dan diturunkan sedikit supaya tidak terlalu besar
BOSS_DMG_MODE_CAP = 1.0
BOSS_DMG_FACTOR = 0.7


def boss_dmg_scale(mc):
    return min(mc["dmg_mult"], BOSS_DMG_MODE_CAP) * (BOSS_DMG_FACTOR if mc["dmg_mult"] >= 1.0 else 1.0)


RUN_RULES = {"slots": 6, "owned": None, "avatar_dmg": 1.0, "books": None}

RARITIES = ["Common", "Uncommon", "Rare", "Super Rare", "Legendary", "Mythic"]
RARITY_COLORS = [(185, 185, 195), (110, 215, 110), (90, 165, 255), (195, 110, 255), (255, 170, 50), (255, 70, 125)]
RARITY_MULT = [1.0, 1.08, 1.18, 1.32, 1.5, 1.75]
RARITY_REFUND = [60, 140, 280, 560, 1100, 2000]
GACHA_BAD_LUCK_STEP = 0.25   # tiap hasil ganda berturut-turut: refund +25% (maks +150%)
WEAPON_RARITY = {"PunchWeapon": 0, "OrbWeapon": 0, "MultiArrowWeapon": 0, "KnifeWeapon": 0, "BoomerangWeapon": 0,
                 "AuraWeapon": 1, "ShockwaveWeapon": 1, "IceSpikeWeapon": 1, "PoisonCloudWeapon": 1,
                 "FireballWeapon": 2, "ChainLightningWeapon": 2, "FireTrailWeapon": 2, "GroundSpikeWeapon": 2,
                 "TornadoWeapon": 3, "ShieldWeapon": 3, "HomingSpiritWeapon": 3,
                 "LaserWeapon": 4, "MeteorWeapon": 4,
                 "SkyLightningWeapon": 5, "BounceOrbWeapon": 5,
                 "SpearWeapon": 1, "MineWeapon": 2, "ScytheWeapon": 3, "FireBirdWeapon": 4}
STARTER_SKILLS = ["PunchWeapon", "OrbWeapon", "MultiArrowWeapon", "KnifeWeapon", "BoomerangWeapon", "AuraWeapon"]
CHESTS = [("Peti Kayu", 600, [60, 28, 10, 2, 0, 0], (150, 105, 55)),
          ("Peti Perak", 1800, [20, 35, 30, 12, 3, 0], (200, 205, 215)),
          ("Peti Emas", 5400, [0, 10, 35, 35, 17, 3], (255, 205, 70))]

ACTIVE_COMBOS = set()


def fan_angles(base, n, spread_deg):
    """Sudut tembakan menyebar (kipas) berpusat di sudut 'base'."""
    if n <= 1:
        return [base]
    spread = math.radians(spread_deg)
    start = base - spread * (n - 1) / 2
    return [start + spread * i for i in range(n)]


TUT_DAMAGE_MULT = 0.2   # Tutorial: damage semua skill diperkecil agar musuh/boss tidak cepat mati


def evo_enabled():
    """Evolusi skill hanya bisa dipakai bila Buku Evolusi dimiliki (tutorial: selalu aktif).
    Dengan buku, skill langsung berbentuk evolusi sejak Lv.1 dan upgrade Lv.1-7 adalah upgrade evolusi."""
    b = RUN_RULES.get("books")
    return b is None or "evo" in b


class Weapon:
    display_name = "Senjata"
    evolved_name = "Evolusi"
    evolved_desc = ""
    base_desc = "Buka senjata baru"
    sfx_name = "shoot"
    evo_form = False
    evo_base = None
    hud_color = None

    def __init__(self, level=1):
        self.level = level
        self.evolved = evo_enabled()
        self.combo_bonus = 1.0
        self.inner = []

    @property
    def rarity(self):
        return WEAPON_RARITY.get(type(self).__name__, 0)

    @property
    def hud_label(self):
        base = f"EVO: {self.evolved_name} Lv.{self.level}" if self.evolved else f"{self.display_name} Lv.{self.level}"
        if self.inner:
            base += f"  [Fusi +{len(self.inner)}]"
        return base

    def level_up(self):
        if self.level < MAX_WEAPON_LEVEL:
            self.level += 1
        for w in self.inner:
            w.level_up()

    def apply_evolution(self, value):
        """Damage akhir = dasar x pengali global senjata x bonus evolusi
        (Lv.5) x bonus combo (banyaknya skill evolusi lain)."""
        mult = WEAPON_DAMAGE_MULT * PLAYER_BUFFS["dmg"] * PLAYER_BUFFS["perm"] * RARITY_MULT[self.rarity]
        if self.evolved:
            mult *= EVOLVED_DAMAGE_MULT * min(1.0, 0.65 + 0.0875 * (self.level - 1))
            mult *= 1.0 + 0.18 * max(0, self.level - EVOLVE_LEVEL)
        elif self.level >= 4:
            mult *= HIGH_LEVEL_DAMAGE_MULT * (1.0 + 0.15 * max(0, self.level - 4))
        mult *= self.combo_bonus * RUN_RULES["avatar_dmg"]
        mult *= 1.0 + 0.35 * len(self.inner)
        return value * mult

    def update(self, dt, game):
        pass

    def draw(self, surf, game):
        pass


class PunchWeapon(Weapon):
    display_name = "Tinju"
    evolved_name = "Tinju Badai"
    evolved_desc = "hantam SEMUA musuh di jangkauan"

    def __init__(self, level=1):
        super().__init__(level)
        self.timer = 0.0

    @property
    def damage(self):
        return self.apply_evolution(14 + self.level * 6)

    @property
    def range_(self):
        r = (110 + self.level * 10) * SKILL_SCALE
        return int(r * 1.35) if self.evolved else int(r)

    @property
    def cooldown(self):
        cd = max(0.16, 0.6 - self.level * 0.045)
        return cd * 0.7 if self.evolved else cd

    def update(self, dt, game):
        self.timer -= dt
        if self.timer <= 0:
            self.timer = self.cooldown
            bx, by = game.badang.x, game.badang.y
            r2 = self.range_ ** 2
            if self.evolved:
                hit = False
                dmg = self.damage
                for e in game.enemies:
                    if e.dead:
                        continue
                    if dist_sq(e.x, e.y, bx, by) <= r2:
                        game.damage_enemy(e, dmg)
                        hit = True
                if hit:
                    game.badang.punch_flash = 0.15
                    game.badang.punch_range_visual = self.range_
                return
            target = game.find_nearest_enemy()
            if target:
                if dist_sq(target.x, target.y, bx, by) <= r2:
                    game.badang.punch_flash = 0.15
                    game.badang.punch_range_visual = self.range_
                    game.damage_enemy(target, self.damage, pierce=False)

    def draw(self, surf, game):
        b = game.badang
        if b.punch_flash > 0:
            r = int(b.punch_range_visual)
            pygame.draw.circle(surf, BADANG_PUNCH_COLOR, CENTER, r, width=2)
            fx, fy = b.facing
            ang = math.atan2(fy, fx)
            d = r * 0.8
            draw_fist(surf, CENTER[0] + math.cos(ang) * d, CENTER[1] + math.sin(ang) * d, ang, int(18 * SKILL_SCALE))


class OrbWeapon(Weapon):
    display_name = "Bola Energi"
    evolved_name = "Bola Energi Ganda"
    evolved_desc = "menembak 3 bola sekaligus"

    def __init__(self, level=1):
        super().__init__(level)
        self.timer = 0.0

    @property
    def damage(self):
        return self.apply_evolution(10 + self.level * 5)

    @property
    def cooldown(self):
        return max(0.45, 1.4 - self.level * 0.16)

    @property
    def proj_speed(self):
        return 7 + self.level * 0.6

    @property
    def count(self):
        n = 1
        if self.evolved:
            n += 2
        if "orb_arrow" in ACTIVE_COMBOS:
            n += 2
        return n

    def update(self, dt, game):
        self.timer -= dt
        if self.timer <= 0:
            self.timer = self.cooldown
            target = game.find_nearest_enemy()
            if not target:
                return
            bx, by = game.badang.x, game.badang.y
            base = math.atan2(target.y - by, target.x - bx)
            dmg = self.damage
            for ang in fan_angles(base, self.count, 12):
                if len(game.projectiles) >= MAX_PLAYER_PROJECTILES:
                    break
                game.projectiles.append(
                    Projectile(bx, by, bx + math.cos(ang) * 200, by + math.sin(ang) * 200,
                               self.proj_speed, dmg, ORB_COLOR, style="orb")
                )


class AuraWeapon(Weapon):
    display_name = "Aura Duri"
    evolved_name = "Aura Neraka"
    evolved_desc = "lebih luas & lebih cepat"

    def __init__(self, level=1):
        super().__init__(level)
        self.tick_timer = 0.0

    @property
    def radius(self):
        r = (90 + self.level * 14) * SKILL_SCALE
        if self.evolved:
            r *= 1.3
        if "toxic_aura" in ACTIVE_COMBOS:
            r *= 1.25
        return int(r)

    @property
    def dps(self):
        return self.apply_evolution(7 + self.level * 3.5)

    def update(self, dt, game):
        self.tick_timer -= dt
        if self.tick_timer <= 0:
            interval = 0.25 if self.evolved else 0.4
            self.tick_timer = interval
            dmg = self.dps * interval
            r2 = self.radius ** 2
            for e in game.enemies:
                if e.dead:
                    continue
                if dist_sq(e.x, e.y, game.badang.x, game.badang.y) <= r2:
                    game.damage_enemy(e, dmg)

    def draw(self, surf, game):
        t = pygame.time.get_ticks() / 1000.0
        color = (255, 90, 160) if self.evolved else AURA_COLOR
        r = self.radius
        pygame.draw.circle(surf, color, CENTER, r, width=2)
        n = 20 if self.evolved else 14
        for i in range(n):
            a = t * (1.4 if self.evolved else 0.9) + i * math.tau / n
            pts = [(CENTER[0] + math.cos(a) * (r + 12), CENTER[1] + math.sin(a) * (r + 12)),
                   (CENTER[0] + math.cos(a + 0.07) * (r - 3), CENTER[1] + math.sin(a + 0.07) * (r - 3)),
                   (CENTER[0] + math.cos(a - 0.07) * (r - 3), CENTER[1] + math.sin(a - 0.07) * (r - 3))]
            pygame.draw.polygon(surf, color, pts)
        if self.evolved:
            pygame.draw.circle(surf, AURA_COLOR, CENTER, int(r * 0.7), width=2)


class ShockwaveWeapon(Weapon):
    display_name = "Gelombang Kejut"
    evolved_name = "Gelombang Dahsyat"
    evolved_desc = "lebih luas, musuh terpental"

    def __init__(self, level=1):
        super().__init__(level)
        self.timer = 0.0
        self.effect_timer = 0.0

    @property
    def cooldown(self):
        cd = max(1.3, 3.4 - self.level * 0.32)
        return cd * 0.8 if self.evolved else cd

    @property
    def damage(self):
        return self.apply_evolution(20 + self.level * 11)

    @property
    def radius(self):
        r = (150 + self.level * 16) * SKILL_SCALE
        return int(r * 1.35) if self.evolved else int(r)

    def update(self, dt, game):
        self.timer -= dt
        if self.effect_timer > 0:
            self.effect_timer -= dt
        if self.timer <= 0:
            self.timer = self.cooldown
            self.effect_timer = 0.3
            r2 = self.radius ** 2
            bx, by = game.badang.x, game.badang.y
            dmg = self.damage
            for e in game.enemies:
                if e.dead:
                    continue
                if dist_sq(e.x, e.y, bx, by) <= r2:
                    game.damage_enemy(e, dmg)
                    if self.evolved and not e.dead and not e.is_boss:
                        nx, ny = e.x - bx, e.y - by
                        m = math.hypot(nx, ny) or 1
                        e.kb_vx = nx / m * 14
                        e.kb_vy = ny / m * 14
                        e.kb_timer = 0.25
            if "storm" in ACTIVE_COMBOS:
                for w in game.badang.all_weapons():
                    if isinstance(w, ChainLightningWeapon):
                        w.timer = 0

    def draw(self, surf, game):
        if self.effect_timer > 0:
            progress = 1 - (self.effect_timer / 0.3)
            r = max(1, int(self.radius * progress))
            pygame.draw.circle(surf, SHOCK_COLOR, CENTER, r, width=6)
            pygame.draw.circle(surf, (255, 235, 190), CENTER, r, width=2)
            if r > 30:
                pygame.draw.circle(surf, SHOCK_COLOR, CENTER, int(r * 0.78), width=2)


class ChainLightningWeapon(Weapon):
    display_name = "Petir Rantai"
    evolved_name = "Petir Dewa"
    evolved_desc = "lompat +3 musuh, lebih ganas"

    def __init__(self, level=1):
        super().__init__(level)
        self.timer = 0.0
        self.effect_timer = 0.0
        self.lines = []

    @property
    def damage(self):
        return self.apply_evolution(12 + self.level * 5)

    @property
    def cooldown(self):
        return max(0.7, 1.8 - self.level * 0.15)

    @property
    def chain_count(self):
        return 2 + self.level // 2 + (3 if self.evolved else 0)

    @property
    def chain_range(self):
        return 240 if self.evolved else 180

    def update(self, dt, game):
        self.timer -= dt
        if self.effect_timer > 0:
            self.effect_timer -= dt
        if self.timer <= 0:
            self.timer = self.cooldown
            current = game.find_nearest_enemy()
            if not current:
                return
            self.lines = []
            hit_ids = set()
            dmg = self.damage
            falloff = 0.7 if self.evolved else 0.5
            prev_pos = (game.badang.x, game.badang.y)
            hops = 0
            r2 = self.chain_range ** 2
            while current is not None and hops < self.chain_count and id(current) not in hit_ids:
                game.damage_enemy(current, dmg, pierce=False)
                hit_ids.add(id(current))
                self.lines.append((prev_pos[0], prev_pos[1], current.x, current.y))
                prev_pos = (current.x, current.y)
                dmg *= falloff
                hops += 1
                candidates = [
                    e for e in game.enemies
                    if not e.dead and id(e) not in hit_ids
                    and dist_sq(e.x, e.y, prev_pos[0], prev_pos[1]) <= r2
                ]
                current = min(candidates, key=lambda e: dist_sq(e.x, e.y, prev_pos[0], prev_pos[1])) \
                    if candidates else None
            self.effect_timer = 0.2

    def draw(self, surf, game):
        if self.effect_timer <= 0 or not self.lines:
            return
        cam_x, cam_y = game.get_camera()
        for (x1, y1, x2, y2) in self.lines:
            draw_bolt(surf, x1 - cam_x, y1 - cam_y, x2 - cam_x, y2 - cam_y, LIGHTNING_COLOR,
                      7 if self.evolved else 4, 7, 12)


class MultiArrowWeapon(Weapon):
    display_name = "Panah Berganda"
    evolved_name = "Hujan Panah"
    evolved_desc = "+4 panah sekali tembak"

    def __init__(self, level=1):
        super().__init__(level)
        self.timer = 0.0

    @property
    def damage(self):
        return self.apply_evolution(9 + self.level * 4)

    @property
    def cooldown(self):
        return max(0.6, 1.6 - self.level * 0.12)

    @property
    def count(self):
        return 3 + self.level // 2 + (4 if self.evolved else 0)

    def update(self, dt, game):
        self.timer -= dt
        if self.timer <= 0:
            self.timer = self.cooldown
            target = game.find_nearest_enemy()
            if target:
                base_angle = math.atan2(target.y - game.badang.y, target.x - game.badang.x)
            else:
                base_angle = math.atan2(game.badang.facing[1], game.badang.facing[0])
            dmg = self.damage
            for ang in fan_angles(base_angle, self.count, 16):
                if len(game.projectiles) >= MAX_PLAYER_PROJECTILES:
                    break
                tx = game.badang.x + math.cos(ang) * 200
                ty = game.badang.y + math.sin(ang) * 200
                game.projectiles.append(
                    Projectile(game.badang.x, game.badang.y, tx, ty,
                               8 + self.level * 0.4, dmg, ARROW_COLOR, style="arrow")
                )


class FireballWeapon(Weapon):
    """Bola api yang mengelilingi Badang terus-menerus. Setiap naik
    level, jumlah bola yang mengorbit bertambah satu."""
    display_name = "Bola Api"
    evolved_name = "Lingkaran Api"
    evolved_desc = "+2 bola, lebih besar & cepat"

    def __init__(self, level=1):
        super().__init__(level)
        self.angle = 0.0
        self.tick_timer = 0.0

    @property
    def count(self):
        return 1 + self.level + (2 if self.evolved else 0)

    @property
    def orbit_radius(self):
        return int((125 if self.evolved else 95) * SKILL_SCALE)

    @property
    def rotation_speed(self):
        return 3.2 if self.evolved else 2.2

    @property
    def damage(self):
        return self.apply_evolution(6 + self.level * 3)

    @property
    def hit_radius(self):
        return int((22 if self.evolved else 16) * SKILL_SCALE)

    def ball_positions(self, game):
        pts = []
        step = (2 * math.pi) / self.count
        for i in range(self.count):
            ang = self.angle + i * step
            x = game.badang.x + math.cos(ang) * self.orbit_radius
            y = game.badang.y + math.sin(ang) * self.orbit_radius
            pts.append((x, y))
        return pts

    def update(self, dt, game):
        self.angle += self.rotation_speed * dt
        self.tick_timer -= dt
        if self.tick_timer <= 0:
            self.tick_timer = 0.15
            r2 = self.hit_radius ** 2
            dmg = self.damage
            freeze = "steam" in ACTIVE_COMBOS
            for (bx, by) in self.ball_positions(game):
                for e in game.enemies:
                    if e.dead:
                        continue
                    if dist_sq(bx, by, e.x, e.y) <= r2:
                        game.damage_enemy(e, dmg)
                        if not e.dead:
                            game.ignite_enemy(e, max(2.0, dmg * 0.25), 3.0)
                        if freeze and not e.dead and not e.is_boss:
                            e.frozen_timer = max(e.frozen_timer, 0.7)

    def draw(self, surf, game):
        cam_x, cam_y = game.get_camera()
        r = int((14 if self.evolved else 10) * SKILL_SCALE)
        t = pygame.time.get_ticks() / 1000.0
        for (bx, by) in self.ball_positions(game):
            sx, sy = bx - cam_x, by - cam_y
            a = math.atan2(by - game.badang.y, bx - game.badang.x) + math.pi / 2
            draw_proj_shape(surf, "fire", sx, sy, a, r, FIRE_COLOR, t)


class IceSpikeWeapon(Weapon):
    display_name = "Duri Es"
    evolved_name = "Badai Es"
    evolved_desc = "3 duri, beku lebih lama"

    def __init__(self, level=1):
        super().__init__(level)
        self.timer = 0.0

    @property
    def damage(self):
        return self.apply_evolution(5 + self.level * 2)

    @property
    def cooldown(self):
        return max(0.5, 1.3 - self.level * 0.1)

    @property
    def proj_speed(self):
        return 8 + self.level * 0.5

    @property
    def freeze_duration(self):
        d = 1.2 + self.level * 0.15
        return d * 1.5 if self.evolved else d

    @property
    def count(self):
        return 3 if self.evolved else 1

    def update(self, dt, game):
        self.timer -= dt
        if self.timer <= 0:
            self.timer = self.cooldown
            target = game.find_nearest_enemy()
            if not target:
                return
            bx, by = game.badang.x, game.badang.y
            base = math.atan2(target.y - by, target.x - bx)
            dmg = self.damage
            for ang in fan_angles(base, self.count, 14):
                if len(game.projectiles) >= MAX_PLAYER_PROJECTILES:
                    break
                game.projectiles.append(
                    Projectile(bx, by, bx + math.cos(ang) * 200, by + math.sin(ang) * 200,
                               self.proj_speed, dmg, ICE_COLOR,
                               freeze_on_hit=True, freeze_duration=self.freeze_duration, style="ice")
                )


class BoomerangWeapon(Weapon):
    display_name = "Bumerang"
    evolved_name = "Bumerang Kembar"
    evolved_desc = "melempar 3 bumerang besar"

    def __init__(self, level=1):
        super().__init__(level)
        self.timer = 0.0

    @property
    def damage(self):
        return self.apply_evolution(9 + self.level * 4)

    @property
    def cooldown(self):
        return max(0.9, 2.2 - self.level * 0.15)

    @property
    def count(self):
        n = 1
        if self.evolved:
            n += 2
        if "fist_boom" in ACTIVE_COMBOS:
            n += 1
        return n

    def update(self, dt, game):
        self.timer -= dt
        if self.timer <= 0:
            self.timer = self.cooldown
            target = game.find_nearest_enemy()
            if target:
                angle = math.atan2(target.y - game.badang.y, target.x - game.badang.x)
            else:
                angle = math.atan2(game.badang.facing[1], game.badang.facing[0])
            dmg = self.damage
            radius = 13 if self.evolved else 9
            for ang in fan_angles(angle, self.count, 24):
                if len(game.boomerangs) >= MAX_BOOMERANGS:
                    break
                game.boomerangs.append(
                    Boomerang(game.badang.x, game.badang.y, ang, 9 + self.level * 0.5, dmg, radius=radius)
                )


class PoisonCloudWeapon(Weapon):
    display_name = "Awan Racun"
    evolved_name = "Kabut Pekat"
    evolved_desc = "2 awan, lebih besar & lama"

    def __init__(self, level=1):
        super().__init__(level)
        self.timer = 0.0

    @property
    def cooldown(self):
        return max(2.0, 4.5 - self.level * 0.3)

    @property
    def radius(self):
        r = 70 + self.level * 10
        return int(r * 1.4) if self.evolved else r

    @property
    def dmg_per_tick(self):
        return self.apply_evolution(3 + self.level * 1.5)

    @property
    def duration(self):
        d = 3.0 + self.level * 0.4
        if self.evolved:
            d *= 1.5
        if "toxic_aura" in ACTIVE_COMBOS:
            d *= 1.5
        return d

    def update(self, dt, game):
        self.timer -= dt
        if self.timer <= 0:
            self.timer = self.cooldown
            target = game.find_nearest_enemy()
            x, y = (target.x, target.y) if target else (game.badang.x, game.badang.y)
            if len(game.poison_zones) < MAX_POISON_ZONES:
                game.poison_zones.append(
                    PoisonZone(x, y, self.radius, self.dmg_per_tick, 0.5, self.duration)
                )
                if self.evolved and target and len(game.poison_zones) < MAX_POISON_ZONES:
                    game.poison_zones.append(
                        PoisonZone(game.badang.x, game.badang.y, self.radius,
                                   self.dmg_per_tick, 0.5, self.duration)
                    )


def seg_dist_sq(px, py, x1, y1, x2, y2):
    """Jarak kuadrat titik ke ruas garis (untuk laser & sinar)."""
    dx, dy = x2 - x1, y2 - y1
    l2 = dx * dx + dy * dy
    if l2 <= 0:
        return dist_sq(px, py, x1, y1)
    t = ((px - x1) * dx + (py - y1) * dy) / l2
    t = 0.0 if t < 0 else 1.0 if t > 1 else t
    return dist_sq(px, py, x1 + dx * t, y1 + dy * t)


class PlayerStrike:
    """Serangan area tertunda milik pemain (meteor, duri bumi, kilat langit):
    ada tanda peringatan, lalu menghantam."""

    def __init__(self, x, y, radius, damage, warn, color, stun=0.0, kind="blast", zone=None):
        self.x, self.y = x, y
        self.radius = radius
        self.damage = damage
        self.warn = max(0.05, warn)
        self.timer = self.warn
        self.color = color
        self.stun = stun
        self.kind = kind
        self.zone = zone
        self.hit = False
        self.fx = 0.3
        self.alive = True

    def update(self, dt, game):
        if not self.hit:
            self.timer -= dt
            if self.timer <= 0:
                self.hit = True
                for e in game.enemies:
                    if e.dead:
                        continue
                    if dist_sq(e.x, e.y, self.x, self.y) <= (self.radius + e.radius * 0.6) ** 2:
                        game.damage_enemy(e, self.damage)
                        if self.stun > 0 and not e.dead and not e.is_boss:
                            e.frozen_timer = max(e.frozen_timer, self.stun)
                if self.zone and len(game.poison_zones) < MAX_POISON_ZONES:
                    zr, zd, zt, zc = self.zone
                    game.poison_zones.append(PoisonZone(self.x, self.y, zr, zd, 0.5, zt, zc))
                if self.kind == "meteor":
                    sfx("boom", 0.08)
                elif self.kind == "spike":
                    sfx("spike", 0.06)
                else:
                    sfx("thunder", 0.06)
        else:
            self.fx -= dt
            if self.fx <= 0:
                self.alive = False

    def draw(self, surf, cam_x, cam_y):
        sx, sy = int(self.x - cam_x), int(self.y - cam_y)
        if not (-200 <= sx <= WIDTH + 200 and -200 <= sy <= HEIGHT + 200):
            return
        r = int(self.radius)
        if not self.hit:
            prog = 1.0 - max(self.timer, 0.0) / self.warn
            pygame.draw.circle(surf, self.color, (sx, sy), r, 2)
            pygame.draw.circle(surf, self.color, (sx, sy), max(2, int(r * prog)), 1)
            if self.kind == "meteor":
                mx, my = sx + int((1 - prog) * 140), sy - int((1 - prog) * 440)
                pygame.draw.polygon(surf, (255, 140, 40), [(mx - 14, my - 6), (mx + 60, my - 150), (mx + 12, my + 8)])
                pygame.draw.polygon(surf, (255, 225, 120), [(mx - 8, my - 4), (mx + 34, my - 90), (mx + 6, my + 4)])
                rock = [(mx + math.cos(i * 0.785 + 0.3) * (17 if i % 2 == 0 else 13),
                         my + math.sin(i * 0.785 + 0.3) * (17 if i % 2 == 0 else 13)) for i in range(8)]
                pygame.draw.polygon(surf, (95, 65, 50), rock)
                pygame.draw.polygon(surf, (40, 25, 20), rock, 2)
                pygame.draw.circle(surf, (255, 120, 40), (mx - 4, my + 3), 4)
            elif self.kind == "bolt":
                pygame.draw.line(surf, LIGHTNING_COLOR, (sx, sy - 500), (sx, sy), 1)
        else:
            k = max(self.fx, 0.0) / 0.3
            rr = int(r * (0.65 + 0.35 * (1 - k)))
            if self.kind == "spike":
                for i in range(6):
                    a = i * math.tau / 6
                    cx, cy = sx + math.cos(a) * rr * 0.6, sy + math.sin(a) * rr * 0.6
                    pts = [(cx + math.cos(a) * rr * 0.5, cy + math.sin(a) * rr * 0.5),
                           (cx + math.cos(a + 1.9) * 9, cy + math.sin(a + 1.9) * 9),
                           (cx + math.cos(a - 1.9) * 9, cy + math.sin(a - 1.9) * 9)]
                    pygame.draw.polygon(surf, self.color, pts)
                    pygame.draw.polygon(surf, (60, 40, 20), pts, 2)
                pygame.draw.circle(surf, WHITE, (sx, sy), max(2, int(rr * 0.25)))
            elif self.kind == "meteor":
                pygame.draw.circle(surf, (255, 140, 40), (sx, sy), rr)
                pygame.draw.circle(surf, (255, 230, 140), (sx, sy), max(2, int(rr * 0.55)))
                for i in range(8):
                    a = i * math.tau / 8
                    pygame.draw.line(surf, (255, 200, 90), (sx + math.cos(a) * rr * 0.6, sy + math.sin(a) * rr * 0.6),
                                     (sx + math.cos(a) * rr * 1.15, sy + math.sin(a) * rr * 1.15), 3)
            else:
                pygame.draw.circle(surf, self.color, (sx, sy), rr)
                pygame.draw.circle(surf, WHITE, (sx, sy), max(2, int(rr * 0.5)))
                if self.kind == "bolt":
                    draw_bolt(surf, sx + 8, sy - 520, sx, sy, LIGHTNING_COLOR, 9, 9, 22)


class Tornado:
    """Puting beliung bergerak: menyedot musuh & melukai terus-menerus."""

    def __init__(self, x, y, vx, vy, radius, dmg, life, knock=False):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.radius = radius
        self.dmg = dmg
        self.life = life
        self.knock = knock
        self.tick = 0.0
        self.alive = True

    def update(self, dt, game):
        self.life -= dt
        if self.life <= 0:
            self.alive = False
            return
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        self.tick -= dt
        do_tick = self.tick <= 0
        if do_tick:
            self.tick = 0.25
        r2 = self.radius ** 2
        pull2 = (self.radius * 1.7) ** 2
        for e in game.enemies:
            if e.dead:
                continue
            d2 = dist_sq(e.x, e.y, self.x, self.y)
            if d2 > pull2:
                continue
            if not e.is_boss and d2 > 100:
                d = math.sqrt(d2)
                step = min(3.0 * dt * 60, d)
                e.x += (self.x - e.x) / d * step
                e.y += (self.y - e.y) / d * step
            if do_tick and d2 <= r2:
                game.damage_enemy(e, self.dmg)
                if self.knock and not e.dead and not e.is_boss:
                    e.kb_vx = (e.x - self.x) * 0.05
                    e.kb_vy = (e.y - self.y) * 0.05
                    e.kb_timer = 0.15

    def draw(self, surf, cam_x, cam_y):
        sx, sy = self.x - cam_x, self.y - cam_y
        if not (-150 <= sx <= WIDTH + 150 and -150 <= sy <= HEIGHT + 150):
            return
        t = pygame.time.get_ticks() / 1000.0
        for i in range(7):
            w = max(8, int(self.radius * (1.0 - 0.11 * i) * 2))
            oy = -52 + i * 14
            ox = math.sin(t * 7 + i) * 7
            rect = pygame.Rect(int(sx - w / 2 + ox), int(sy + oy), w, 14)
            pygame.draw.ellipse(surf, (95, 120, 150), rect)
            pygame.draw.ellipse(surf, (210, 235, 255), rect, 2)
        for i in range(5):
            a = t * 6 + i * 1.26
            pygame.draw.circle(surf, (190, 170, 120), (int(sx + math.cos(a) * self.radius * 0.9),
                                                       int(sy - 20 + math.sin(a * 1.3) * 26)), 3)


class LaserWeapon(Weapon):
    display_name = "Laser Sihir"
    evolved_name = "Laser Nova"
    evolved_desc = "3 sinar lebar menembus semua musuh"
    base_desc = "Sinar laser menembus barisan musuh"
    sfx_name = "laser"

    def __init__(self, level=1):
        super().__init__(level)
        self.timer = 0.0
        self.beam_timer = 0.0
        self.beams = []

    @property
    def damage(self):
        return self.apply_evolution(16 + self.level * 7)

    @property
    def cooldown(self):
        return max(0.9, 2.2 - self.level * 0.2)

    @property
    def width(self):
        w = 22 + self.level * 3
        return int(w * 1.5) if self.evolved else w

    @property
    def count(self):
        return 3 if self.evolved else 1

    def update(self, dt, game):
        self.timer -= dt
        if self.beam_timer > 0:
            self.beam_timer -= dt
        if self.timer > 0:
            return
        target = game.find_nearest_enemy()
        if not target:
            self.timer = 0.2
            return
        self.timer = self.cooldown
        bx, by = game.badang.x, game.badang.y
        base = math.atan2(target.y - by, target.x - bx)
        length = 900 if self.evolved else 760
        dmg = self.damage
        freeze = "laser_ice" in ACTIVE_COMBOS
        storm = "laser_storm" in ACTIVE_COMBOS
        self.beams = []
        hw = self.width / 2
        for ang in fan_angles(base, self.count, 22):
            x2, y2 = bx + math.cos(ang) * length, by + math.sin(ang) * length
            self.beams.append((bx, by, x2, y2))
            for e in game.enemies:
                if e.dead:
                    continue
                if seg_dist_sq(e.x, e.y, bx, by, x2, y2) <= (hw + e.radius) ** 2:
                    game.damage_enemy(e, dmg)
                    if freeze and not e.dead and not e.is_boss:
                        e.frozen_timer = max(e.frozen_timer, 1.2)
                    if storm and not e.dead and random.random() < 0.3 and len(game.strikes) < 40:
                        game.strikes.append(PlayerStrike(e.x, e.y, 55, dmg * 0.6, 0.2, LIGHTNING_COLOR, kind="bolt"))
        self.beam_timer = 0.22

    def draw(self, surf, game):
        if self.beam_timer <= 0:
            return
        cam_x, cam_y = game.get_camera()
        w = max(2, int(self.width * self.beam_timer / 0.22))
        for (x1, y1, x2, y2) in self.beams:
            p1, p2 = (x1 - cam_x, y1 - cam_y), (x2 - cam_x, y2 - cam_y)
            pygame.draw.line(surf, (150, 20, 60), p1, p2, w + 8)
            pygame.draw.line(surf, (255, 60, 100), p1, p2, w)
            pygame.draw.line(surf, WHITE, p1, p2, max(1, w // 3))
            pygame.draw.circle(surf, (255, 200, 220), (int(p1[0]), int(p1[1])), w // 2 + 6)
            pygame.draw.circle(surf, WHITE, (int(p1[0]), int(p1[1])), w // 3 + 2)


class MeteorWeapon(Weapon):
    display_name = "Meteor"
    evolved_name = "Hujan Meteor"
    evolved_desc = "+4 meteor raksasa tiap jatuhan"
    base_desc = "Meteor jatuh menghantam musuh"
    sfx_name = "meteor"

    def __init__(self, level=1):
        super().__init__(level)
        self.timer = 0.0

    @property
    def damage(self):
        return self.apply_evolution(28 + self.level * 12)

    @property
    def cooldown(self):
        cd = max(1.6, 4.0 - self.level * 0.4)
        return cd * 0.7 if self.evolved else cd

    @property
    def count(self):
        return 1 + self.level // 2 + (4 if self.evolved else 0)

    @property
    def radius(self):
        r = 80 + self.level * 8
        return int(r * 1.3) if self.evolved else r

    def update(self, dt, game):
        self.timer -= dt
        if self.timer > 0:
            return
        bx, by = game.badang.x, game.badang.y
        pool = game.enemies_in_range(bx, by, 640)
        if not pool:
            self.timer = 0.3
            return
        self.timer = self.cooldown
        zone = None
        if "meteor_fire" in ACTIVE_COMBOS:
            zone = (self.radius * 0.8, self.damage * 0.12, 3.0, FIRE_COLOR)
        for e in random.sample(pool, min(self.count, len(pool))):
            if len(game.strikes) >= 40:
                break
            game.strikes.append(PlayerStrike(e.x, e.y, self.radius, self.damage, 0.7,
                                             (255, 140, 40), kind="meteor", zone=zone))


class KnifeWeapon(Weapon):
    display_name = "Pisau Terbang"
    evolved_name = "Hujan Pisau"
    evolved_desc = "+4 pisau, menembus semua musuh"
    base_desc = "Pisau menembus musuh ke arah bidikan"
    sfx_name = "whoosh"

    def __init__(self, level=1):
        super().__init__(level)
        self.timer = 0.0

    @property
    def damage(self):
        return self.apply_evolution(8 + self.level * 4)

    @property
    def cooldown(self):
        cd = max(0.45, 1.1 - self.level * 0.1)
        return cd * 0.7 if self.evolved else cd

    @property
    def count(self):
        return 2 + self.level // 2 + (4 if self.evolved else 0) + (3 if "knife_shock" in ACTIVE_COMBOS else 0)

    @property
    def pierce(self):
        return 99 if self.evolved else 2 + self.level

    def update(self, dt, game):
        self.timer -= dt
        if self.timer > 0:
            return
        target = game.find_nearest_enemy()
        if not target:
            self.timer = 0.2
            return
        self.timer = self.cooldown
        bx, by = game.badang.x, game.badang.y
        base = math.atan2(target.y - by, target.x - bx)
        dmg = self.damage
        for ang in fan_angles(base, self.count, 10):
            if len(game.projectiles) >= MAX_PLAYER_PROJECTILES:
                break
            game.projectiles.append(
                Projectile(bx, by, bx + math.cos(ang) * 200, by + math.sin(ang) * 200, 10.5, dmg,
                           (230, 232, 245), radius=6, pierce=self.pierce, life=0.9, style="knife"))


class TornadoWeapon(Weapon):
    display_name = "Angin Puyuh"
    evolved_name = "Topan Raksasa"
    evolved_desc = "2 topan lebih besar, musuh terlempar"
    base_desc = "Puting beliung menyedot & melukai musuh"
    sfx_name = "whoosh"

    def __init__(self, level=1):
        super().__init__(level)
        self.timer = 0.0

    @property
    def damage(self):
        return self.apply_evolution(4 + self.level * 2.2)

    @property
    def cooldown(self):
        return max(2.2, 5.0 - self.level * 0.4)

    @property
    def radius(self):
        r = 60 + self.level * 6
        if self.evolved:
            r *= 1.4
        if "tornado_fire" in ACTIVE_COMBOS:
            r *= 1.3
        return int(r)

    def update(self, dt, game):
        self.timer -= dt
        if self.timer > 0:
            return
        target = game.find_nearest_enemy()
        if not target:
            self.timer = 0.3
            return
        self.timer = self.cooldown
        bx, by = game.badang.x, game.badang.y
        base = math.atan2(target.y - by, target.x - bx)
        n = 2 if self.evolved else 1
        for ang in fan_angles(base, n, 30):
            if len(game.tornados) >= 8:
                break
            game.tornados.append(Tornado(bx, by, math.cos(ang) * 2.6, math.sin(ang) * 2.6,
                                         self.radius, self.damage, 3.5 + self.level * 0.3,
                                         knock=self.evolved))


class FireTrailWeapon(Weapon):
    display_name = "Jejak Api"
    evolved_name = "Jalur Neraka"
    evolved_desc = "jejak api lebih besar & tahan lama"
    base_desc = "Api menyala di jejak langkahmu"

    def __init__(self, level=1):
        super().__init__(level)
        self.drop_timer = 0.0
        self.last = None

    @property
    def radius(self):
        r = (38 + self.level * 4) * SKILL_SCALE
        return int(r * 1.4) if self.evolved else int(r)

    @property
    def dmg_tick(self):
        return self.apply_evolution(3 + self.level * 1.5)

    @property
    def duration(self):
        d = 2.2 + self.level * 0.3
        return d * 1.6 if self.evolved else d

    def update(self, dt, game):
        self.drop_timer -= dt
        b = game.badang
        if self.last is None:
            self.last = (b.x, b.y)
        if self.drop_timer <= 0 and dist_sq(b.x, b.y, self.last[0], self.last[1]) >= 24 ** 2:
            self.drop_timer = 0.22
            self.last = (b.x, b.y)
            if len(game.poison_zones) < MAX_POISON_ZONES:
                game.poison_zones.append(
                    PoisonZone(b.x, b.y, self.radius, self.dmg_tick, 0.4, self.duration, FIRE_COLOR))


class ShieldWeapon(Weapon):
    display_name = "Perisai Cahaya"
    evolved_name = "Benteng Cahaya"
    evolved_desc = "+2 perisai, kebal 30%, hancurkan peluru"
    base_desc = "Perisai berputar: melukai musuh & blok peluru"

    def __init__(self, level=1):
        super().__init__(level)
        self.angle = 0.0
        self.tick_timer = 0.0

    @property
    def count(self):
        return 2 + self.level // 2 + (2 if self.evolved else 0)

    @property
    def orbit(self):
        return int((100 if self.evolved else 72) * SKILL_SCALE)

    @property
    def hit_radius(self):
        return int((25 if self.evolved else 19) * SKILL_SCALE)

    @property
    def damage(self):
        return self.apply_evolution(5 + self.level * 2.5)

    @property
    def reduction(self):
        r = 0.3 if self.evolved else 0.08 + 0.02 * self.level
        if "shield_spike" in ACTIVE_COMBOS:
            r += 0.15
        return min(r, 0.6)

    def positions(self, game):
        step = math.tau / self.count
        return [(game.badang.x + math.cos(self.angle + i * step) * self.orbit,
                 game.badang.y + math.sin(self.angle + i * step) * self.orbit) for i in range(self.count)]

    def update(self, dt, game):
        self.angle += 2.8 * dt
        game.badang.dr_weapon = self.reduction
        pos = self.positions(game)
        hr = self.hit_radius + 8
        for p in game.enemy_projectiles:
            if not p.alive:
                continue
            for (px, py) in pos:
                if dist_sq(p.x, p.y, px, py) <= (hr + p.radius) ** 2:
                    p.alive = False
                    break
        self.tick_timer -= dt
        if self.tick_timer <= 0:
            self.tick_timer = 0.2
            dmg = self.damage
            r2 = (self.hit_radius + 4) ** 2
            for (px, py) in pos:
                for e in game.enemies:
                    if not e.dead and dist_sq(px, py, e.x, e.y) <= r2 + e.radius * e.radius:
                        game.damage_enemy(e, dmg)

    def draw(self, surf, game):
        cam_x, cam_y = game.get_camera()
        b = game.badang
        for (px, py) in self.positions(game):
            sx, sy = px - cam_x, py - cam_y
            a = math.atan2(py - b.y, px - b.x)
            draw_shield_shape(surf, sx, sy, a, self.hit_radius, (150, 205, 240), WHITE)


class GroundSpikeWeapon(Weapon):
    display_name = "Duri Bumi"
    evolved_name = "Gerbang Duri"
    evolved_desc = "+3 duri lebih besar, musuh pingsan lama"
    base_desc = "Duri tajam muncul dari tanah di bawah musuh"
    sfx_name = "spike"

    def __init__(self, level=1):
        super().__init__(level)
        self.timer = 0.0

    @property
    def damage(self):
        return self.apply_evolution(20 + self.level * 9)

    @property
    def cooldown(self):
        cd = max(1.0, 2.6 - self.level * 0.25)
        return cd * 0.75 if self.evolved else cd

    @property
    def count(self):
        return 2 + self.level // 2 + (3 if self.evolved else 0) + (2 if "shield_spike" in ACTIVE_COMBOS else 0)

    @property
    def radius(self):
        return 72 if self.evolved else 52

    def update(self, dt, game):
        self.timer -= dt
        if self.timer > 0:
            return
        pool = game.enemies_in_range(game.badang.x, game.badang.y, 520)
        if not pool:
            self.timer = 0.3
            return
        self.timer = self.cooldown
        stun = 1.4 if self.evolved else 0.6
        for e in random.sample(pool, min(self.count, len(pool))):
            if len(game.strikes) >= 40:
                break
            game.strikes.append(PlayerStrike(e.x, e.y, self.radius, self.damage, 0.45,
                                             (185, 135, 70), stun=stun, kind="spike"))


class HomingSpiritWeapon(Weapon):
    display_name = "Roh Pemburu"
    evolved_name = "Legiun Roh"
    evolved_desc = "+3 roh, menembus 3 musuh"
    base_desc = "Roh mengejar musuh sendiri"
    sfx_name = "summon"

    def __init__(self, level=1):
        super().__init__(level)
        self.timer = 0.0

    @property
    def damage(self):
        return self.apply_evolution(7 + self.level * 3.5)

    @property
    def cooldown(self):
        return max(0.8, 1.9 - self.level * 0.17)

    @property
    def count(self):
        return 1 + self.level // 2 + (3 if self.evolved else 0) + (2 if "spirit_poison" in ACTIVE_COMBOS else 0)

    def update(self, dt, game):
        self.timer -= dt
        if self.timer > 0:
            return
        if not game.find_nearest_enemy():
            self.timer = 0.3
            return
        self.timer = self.cooldown
        bx, by = game.badang.x, game.badang.y
        dmg = self.damage
        for _ in range(self.count):
            if len(game.projectiles) >= MAX_PLAYER_PROJECTILES:
                break
            a = random.uniform(0, math.tau)
            game.projectiles.append(
                Projectile(bx, by, bx + math.cos(a) * 100, by + math.sin(a) * 100, 5.2, dmg,
                           (205, 175, 255), radius=8, pierce=3 if self.evolved else 1,
                           life=3.5, homing=True, style="spirit"))


class BounceOrbWeapon(Weapon):
    display_name = "Bola Pantul"
    evolved_name = "Bola Pelangi"
    evolved_desc = "2 bola, memantul jauh lebih banyak"
    base_desc = "Bola memantul dari musuh ke musuh"
    sfx_name = "shoot"

    def __init__(self, level=1):
        super().__init__(level)
        self.timer = 0.0

    @property
    def damage(self):
        return self.apply_evolution(9 + self.level * 4)

    @property
    def cooldown(self):
        return max(0.9, 2.0 - self.level * 0.17)

    @property
    def bounces(self):
        n = 3 + self.level + (8 if self.evolved else 0)
        if "bounce_chain" in ACTIVE_COMBOS:
            n += 4
        return n

    def update(self, dt, game):
        self.timer -= dt
        if self.timer > 0:
            return
        target = game.find_nearest_enemy()
        if not target:
            self.timer = 0.2
            return
        self.timer = self.cooldown
        bx, by = game.badang.x, game.badang.y
        base = math.atan2(target.y - by, target.x - bx)
        for ang in fan_angles(base, 2 if self.evolved else 1, 16):
            if len(game.projectiles) >= MAX_PLAYER_PROJECTILES:
                break
            game.projectiles.append(
                Projectile(bx, by, bx + math.cos(ang) * 200, by + math.sin(ang) * 200, 8.5,
                           self.damage, (255, 150, 255), radius=12 if self.evolved else 9,
                           bounce=self.bounces, life=6.0, style="orb"))


class SkyLightningWeapon(Weapon):
    display_name = "Kilat Langit"
    evolved_name = "Murka Langit"
    evolved_desc = "+4 sambaran, musuh tersambar pingsan"
    base_desc = "Petir menyambar musuh-musuh acak"
    sfx_name = "thunder"

    def __init__(self, level=1):
        super().__init__(level)
        self.timer = 0.0

    @property
    def damage(self):
        return self.apply_evolution(18 + self.level * 8)

    @property
    def cooldown(self):
        cd = max(1.1, 2.6 - self.level * 0.22)
        return cd * 0.7 if self.evolved else cd

    @property
    def count(self):
        return 2 + self.level // 2 + (4 if self.evolved else 0)

    @property
    def radius(self):
        return 75 if self.evolved else 55

    def update(self, dt, game):
        self.timer -= dt
        if self.timer > 0:
            return
        pool = game.enemies_in_range(game.badang.x, game.badang.y, 680)
        if not pool:
            self.timer = 0.3
            return
        self.timer = self.cooldown
        stun = 0.6 if self.evolved else 0.0
        for e in random.sample(pool, min(self.count, len(pool))):
            if len(game.strikes) >= 40:
                break
            game.strikes.append(PlayerStrike(e.x, e.y, self.radius, self.damage, 0.3,
                                             LIGHTNING_COLOR, stun=stun, kind="bolt"))


class MineWeapon(Weapon):
    display_name = "Ranjau Sihir"
    evolved_name = "Ranjau Berantai"
    evolved_desc = "Ranjau lebih banyak & besar, musuh yang kena pingsan"
    base_desc = "Menanam ranjau di sekitarmu yang meledak setelah jeda"
    sfx_name = "boom"

    def __init__(self, level=1):
        super().__init__(level)
        self.timer = 0.0

    @property
    def damage(self):
        return self.apply_evolution(40 + self.level * 14)

    @property
    def cooldown(self):
        return max(1.4, 3.2 - self.level * 0.2)

    def update(self, dt, game):
        self.timer -= dt
        if self.timer > 0:
            return
        b = game.badang
        if not game.enemies_in_range(b.x, b.y, 520):
            self.timer = 0.3
            return
        self.timer = self.cooldown
        n = 1 + self.level // 3 + (2 if self.evolved else 0)
        for _ in range(n):
            if len(game.strikes) >= 40:
                break
            a, d = random.uniform(0, math.tau), random.uniform(50, 150)
            game.strikes.append(PlayerStrike(b.x + math.cos(a) * d, b.y + math.sin(a) * d, 115 if self.evolved else 85, self.damage,
                                             1.3, (255, 200, 80), stun=0.8 if self.evolved else 0.0, kind="blast"))


class SpearWeapon(Weapon):
    display_name = "Tombak Cahaya"
    evolved_name = "Tombak Langit"
    evolved_desc = "Tiga tombak menembus semua musuh"
    base_desc = "Melempar tombak cahaya yang menembus beberapa musuh"
    sfx_name = "whoosh"

    def __init__(self, level=1):
        super().__init__(level)
        self.timer = 0.0

    @property
    def damage(self):
        return self.apply_evolution(20 + self.level * 8)

    @property
    def cooldown(self):
        return max(0.7, 1.5 - self.level * 0.1)

    def update(self, dt, game):
        self.timer -= dt
        if self.timer > 0:
            return
        t = game.find_nearest_enemy()
        if t is None:
            self.timer = 0.2
            return
        self.timer = self.cooldown
        b = game.badang
        base = math.atan2(t.y - b.y, t.x - b.x)
        for a in fan_angles(base, 3 if self.evolved else 1, 10):
            if len(game.projectiles) >= MAX_PLAYER_PROJECTILES:
                break
            game.projectiles.append(Projectile(b.x, b.y, b.x + math.cos(a) * 200, b.y + math.sin(a) * 200, 9.0, self.damage,
                                               (235, 240, 255), radius=12, pierce=99 if self.evolved else 3, life=1.3, style="spear"))


class ScytheWeapon(Weapon):
    display_name = "Sabit Hantu"
    evolved_name = "Sabit Maut"
    evolved_desc = "Delapan tebasan melingkar & musuh terpental pingsan"
    base_desc = "Tebasan sabit melingkar di sekelilingmu"
    sfx_name = "whoosh"

    def __init__(self, level=1):
        super().__init__(level)
        self.timer = 0.0
        self.spin = 0.0

    @property
    def damage(self):
        return self.apply_evolution(26 + self.level * 10)

    @property
    def cooldown(self):
        return max(1.0, 2.4 - self.level * 0.2)

    def update(self, dt, game):
        self.timer -= dt
        if self.timer > 0:
            return
        b = game.badang
        if not game.enemies_in_range(b.x, b.y, 420):
            self.timer = 0.3
            return
        self.timer = self.cooldown
        n = 8 if self.evolved else 4
        self.spin += 0.4
        for i in range(n):
            if len(game.strikes) >= 40:
                break
            a = self.spin + i * math.tau / n
            game.strikes.append(PlayerStrike(b.x + math.cos(a) * 110, b.y + math.sin(a) * 110, 72, self.damage, 0.15 + 0.05 * i,
                                             (190, 120, 255), stun=0.5 if self.evolved else 0.0, kind="blast"))


class FireBirdWeapon(Weapon):
    display_name = "Burung Api"
    evolved_name = "Phoenix Api"
    evolved_desc = "Dua phoenix mengejar & ledakan lebih luas"
    base_desc = "Burung api mengejar musuh dan meledak"
    sfx_name = "shoot"

    def __init__(self, level=1):
        super().__init__(level)
        self.timer = 0.0

    @property
    def damage(self):
        return self.apply_evolution(30 + self.level * 11)

    @property
    def cooldown(self):
        return max(1.0, 2.3 - self.level * 0.18)

    def update(self, dt, game):
        self.timer -= dt
        if self.timer > 0:
            return
        t = game.find_nearest_enemy()
        if t is None:
            self.timer = 0.2
            return
        self.timer = self.cooldown
        b = game.badang
        base = math.atan2(t.y - b.y, t.x - b.x)
        for a in fan_angles(base, 2 if self.evolved else 1, 40):
            if len(game.projectiles) >= MAX_PLAYER_PROJECTILES:
                break
            d = self.damage
            game.projectiles.append(Projectile(b.x, b.y, b.x + math.cos(a) * 200, b.y + math.sin(a) * 200, 6.0, d, (255, 140, 40),
                                               splash_radius=130 if self.evolved else 90, splash_damage=d * 0.6, radius=12,
                                               life=3.5, homing=True, style="fire"))


NEW_WEAPON_CLASSES = [
    MineWeapon, SpearWeapon, ScytheWeapon, FireBirdWeapon, LaserWeapon, MeteorWeapon, KnifeWeapon, TornadoWeapon, FireTrailWeapon,
    ShieldWeapon, GroundSpikeWeapon, HomingSpiritWeapon, BounceOrbWeapon, SkyLightningWeapon,
]


WEAPON_CLASSES = [
    PunchWeapon, OrbWeapon, AuraWeapon, ShockwaveWeapon, ChainLightningWeapon,
    MultiArrowWeapon, FireballWeapon, IceSpikeWeapon, BoomerangWeapon, PoisonCloudWeapon,
] + NEW_WEAPON_CLASSES
PLAYER_SCALE = 0.72
SKILL_SCALE = 0.85

for _cls, _nm in ((PunchWeapon, 'punch'), (ShockwaveWeapon, 'boom'), (ChainLightningWeapon, 'thunder'),
                  (IceSpikeWeapon, 'freeze'), (BoomerangWeapon, 'whoosh'), (PoisonCloudWeapon, 'poison'),
                  (FireballWeapon, 'shoot'), (MultiArrowWeapon, 'shoot'), (OrbWeapon, 'shoot')):
    _cls.sfx_name = _nm

FUSION_DAMAGE_MULT = 1.8
_EVO_CLASSES = {}


def evo_class(cls):
    """Bentuk evolusi sebuah sihir. Sihir lama DIHAPUS dan diganti sihir evolusi (nama baru).
    Nama kelas sengaja sama dengan kelas dasar agar tabel rarity/tag/ikon tetap berlaku, dan
    isinstance(dasar) tetap True agar kombo & 'sudah dimiliki' tetap bekerja."""
    c = _EVO_CLASSES.get(cls)
    if c is None:
        c = type(cls.__name__, (cls,), {"display_name": cls.evolved_name, "evo_form": True, "evo_base": cls})
        _EVO_CLASSES[cls] = c
    return c


def evolved_form(w):
    new = evo_class(type(w))(level=w.level)
    new.combo_bonus = w.combo_bonus
    return new


FUSION_STEM = {
    "PunchWeapon": ("Tinju", (255, 190, 120)), "OrbWeapon": ("Energi", (120, 200, 255)), "MultiArrowWeapon": ("Panah", (200, 230, 140)),
    "KnifeWeapon": ("Belati", (225, 228, 240)), "BoomerangWeapon": ("Bumerang", (255, 215, 120)), "AuraWeapon": ("Aura", (255, 120, 190)),
    "ShockwaveWeapon": ("Kejut", (255, 200, 130)), "IceSpikeWeapon": ("Es", (170, 225, 255)), "PoisonCloudWeapon": ("Racun", (140, 220, 90)),
    "FireballWeapon": ("Api", (255, 130, 50)), "ChainLightningWeapon": ("Petir", (255, 240, 120)), "FireTrailWeapon": ("Bara", (255, 100, 40)),
    "GroundSpikeWeapon": ("Duri", (190, 150, 90)), "TornadoWeapon": ("Angin", (190, 235, 235)), "ShieldWeapon": ("Perisai", (150, 200, 255)),
    "HomingSpiritWeapon": ("Arwah", (205, 175, 255)), "LaserWeapon": ("Laser", (255, 80, 120)), "MeteorWeapon": ("Meteor", (255, 150, 60)),
    "SkyLightningWeapon": ("Kilat", (255, 245, 150)), "BounceOrbWeapon": ("Pantul", (255, 150, 255)),
}
FUSION_FX_OF = {"FireballWeapon": "burn", "FireTrailWeapon": "burn", "MeteorWeapon": "burn", "IceSpikeWeapon": "freeze",
                "PoisonCloudWeapon": "poison", "ShockwaveWeapon": "stun", "ChainLightningWeapon": "stun", "SkyLightningWeapon": "stun",
                "LaserWeapon": "stun", "GroundSpikeWeapon": "stun", "ShieldWeapon": "stun", "PunchWeapon": "stun", "TornadoWeapon": "pull"}
FUSION_TPL_OF = {"AuraWeapon": "nova", "ShockwaveWeapon": "nova", "PunchWeapon": "nova", "ShieldWeapon": "nova", "FireballWeapon": "nova",
                 "PoisonCloudWeapon": "nova", "KnifeWeapon": "blades", "BoomerangWeapon": "blades", "TornadoWeapon": "blades",
                 "FireTrailWeapon": "blades", "LaserWeapon": "beam", "OrbWeapon": "barrage", "MultiArrowWeapon": "barrage",
                 "HomingSpiritWeapon": "barrage", "BounceOrbWeapon": "barrage", "IceSpikeWeapon": "barrage", "MeteorWeapon": "storm",
                 "SkyLightningWeapon": "storm", "GroundSpikeWeapon": "storm", "ChainLightningWeapon": "chain"}
FUSION_FX_TEXT = {"freeze": "membekukan", "burn": "membakar", "poison": "meracuni", "stun": "melumpuhkan", "pull": "menarik musuh"}
FUSION_TPL_NOUN = {"nova": "Ledakan", "blades": "Bilah", "beam": "Sinar", "barrage": "Hujan", "storm": "Badai", "chain": "Rantai"}
FUSION_TPL_TEXT = {"nova": "ledakan cincin di sekelilingmu", "blades": "bilah menembus ke segala arah",
                   "beam": "sinar lebar menembus barisan musuh", "barrage": "peluru pengejar yang meledak",
                   "storm": "serangan jatuh dari langit ke musuh", "chain": "sambaran rantai melompat antar musuh"}
FUSION_TPL_TAGS = {"nova": ["AOE", "Fusi"], "blades": ["Pierce", "Fusi"], "beam": ["Pierce", "Beam", "Fusi"],
                   "barrage": ["Homing", "Projectile", "Fusi"], "storm": ["AOE", "Burst", "Fusi"], "chain": ["Chain", "Fusi"]}

_FR = {}


def _fr(a, b, name, tpl, col, fx, desc):
    _FR[tuple(sorted((a, b)))] = (name, tpl, col, fx, desc)


_fr("FireballWeapon", "IceSpikeWeapon", "Prisma Uap", "nova", (215, 235, 255), "freeze+burn", "Ledakan uap panas-dingin yang membekukan dan membakar musuh di sekitarmu")
_fr("ShockwaveWeapon", "ChainLightningWeapon", "Guntur Gempa", "nova", (255, 225, 140), "stun", "Gelombang guntur yang melumpuhkan semua musuh dekat")
_fr("OrbWeapon", "MultiArrowWeapon", "Meriam Bintang", "barrage", (140, 215, 255), "", "Hujan peluru bintang yang mengejar musuh dan meledak")
_fr("AuraWeapon", "PoisonCloudWeapon", "Wabah Senyap", "nova", (150, 235, 110), "poison", "Cincin wabah yang meracuni semua yang ada di dekatmu")
_fr("PunchWeapon", "BoomerangWeapon", "Palu Elang", "blades", (255, 205, 130), "stun", "Bilah palu berputar menembus barisan musuh")
_fr("FireballWeapon", "AuraWeapon", "Matahari Mini", "nova", (255, 170, 70), "burn", "Ledakan matahari kecil yang membakar musuh di sekitarmu")
_fr("IceSpikeWeapon", "ShockwaveWeapon", "Gempa Salju", "nova", (185, 230, 255), "freeze", "Gelombang salju yang membekukan semua musuh di dekatmu")
_fr("PoisonCloudWeapon", "ChainLightningWeapon", "Petir Bisa", "chain", (190, 245, 110), "poison", "Rantai petir beracun yang melompat antar musuh")
_fr("LaserWeapon", "SkyLightningWeapon", "Sinar Langit", "beam", (255, 240, 150), "stun", "Sinar petir lebar yang melumpuhkan semua yang tertembus")
_fr("MeteorWeapon", "FireTrailWeapon", "Hujan Magma", "storm", (255, 110, 40), "burn", "Meteor magma jatuh dan meninggalkan lahar membara")
_fr("TornadoWeapon", "FireballWeapon", "Pusaran Api", "nova", (255, 150, 60), "pull+burn", "Pusaran api menyeret musuh ke arahmu lalu membakarnya")
_fr("HomingSpiritWeapon", "PoisonCloudWeapon", "Arwah Bisa", "barrage", (190, 225, 150), "poison", "Arwah beracun memburu musuh dan meledakkan racun")
_fr("KnifeWeapon", "ShockwaveWeapon", "Badai Belati", "blades", (235, 235, 255), "stun", "Lingkaran belati menembus dan melumpuhkan musuh")
_fr("ShieldWeapon", "GroundSpikeWeapon", "Benteng Duri", "storm", (210, 170, 100), "stun", "Duri bumi menghantam dan melumpuhkan musuh di sekitar sasaran")
_fr("BounceOrbWeapon", "ChainLightningWeapon", "Listrik Pantul", "chain", (255, 170, 255), "stun", "Rantai listrik yang memantul tanpa henti antar musuh")
_fr("LaserWeapon", "IceSpikeWeapon", "Sinar Kristal", "beam", (160, 225, 255), "freeze", "Sinar kristal yang membekukan semua musuh yang tertembus")
_fr("MeteorWeapon", "IceSpikeWeapon", "Komet Beku", "storm", (180, 230, 255), "freeze", "Komet es jatuh dan membekukan musuh di sekitar sasaran")
_fr("TornadoWeapon", "SkyLightningWeapon", "Badai Sempurna", "storm", (210, 240, 240), "pull+stun", "Kilat jatuh bersama angin yang menarik musuh mendekat")
_fr("KnifeWeapon", "BoomerangWeapon", "Bilah Pulang", "blades", (240, 225, 160), "", "Bilah berputar ke segala arah, cepat dan menembus")
_fr("OrbWeapon", "BounceOrbWeapon", "Planet Pantul", "barrage", (190, 170, 255), "", "Peluru planet pengejar yang meledak di sasaran")
_fr("HomingSpiritWeapon", "FireballWeapon", "Arwah Api", "barrage", (255, 160, 90), "burn", "Arwah api memburu musuh dan membakarnya")
_fr("PunchWeapon", "ShockwaveWeapon", "Tinju Gempa", "nova", (255, 190, 110), "stun", "Hantaman tinju yang mengguncang semua musuh di dekatmu")


def fusion_recipe(a, b):
    """Resep fusi untuk pasangan kelas dasar (nama). Bernama bila ada di tabel; selain itu hasilnya
    TETAP (deterministik) dari kedua sihir."""
    key = tuple(sorted((a, b)))
    r = _FR.get(key)
    if r is not None:
        name, tpl, col, fx, desc = r
        return {"name": name, "tpl": tpl, "col": col, "fx": [f for f in fx.split("+") if f], "desc": desc, "named": True, "key": key}
    h = zlib.crc32(("|".join(key)).encode())
    rar = lambda n: WEAPON_RARITY.get(n, 0)
    top = key[0] if rar(key[0]) >= rar(key[1]) else key[1]
    if rar(key[0]) == rar(key[1]):
        top = key[h % 2]
    tpl = FUSION_TPL_OF.get(top, "nova")
    fx = []
    for n in key:
        f = FUSION_FX_OF.get(n)
        if f and f not in fx:
            fx.append(f)
    sa, sb = FUSION_STEM.get(key[0], ("Sihir", (200, 90, 255))), FUSION_STEM.get(key[1], ("Sihir", (200, 90, 255)))
    col = tuple((x + y) // 2 for x, y in zip(sa[1], sb[1]))
    name = "%s %s-%s" % (FUSION_TPL_NOUN[tpl], sa[0], sb[0])
    fxt = ", ".join(FUSION_FX_TEXT[f] for f in fx) if fx else "tanpa efek khusus"
    desc = "%s; efek: %s" % (FUSION_TPL_TEXT[tpl].capitalize(), fxt)
    return {"name": name, "tpl": tpl, "col": col, "fx": fx, "desc": desc, "named": False, "key": key}


def fusion_recipe_rarity(a, b):
    return min(5, max(WEAPON_RARITY.get(a, 0), WEAPON_RARITY.get(b, 0)) + 1)


class FusionWeapon(Weapon):
    """SENJATA FUSI: hasil melebur DUA sihir. Kedua sihir asal HILANG; yang ada hanya senjata baru ini
    (nama, bentuk serangan, dan efek ditentukan resep)."""
    display_name = "Senjata Fusi"
    evolved_name = "Senjata Fusi"
    SFX = {"nova": "boom", "blades": "whoosh", "beam": "laser", "barrage": "shoot", "storm": "thunder", "chain": "thunder"}

    def __init__(self, level=3, a="PunchWeapon", b="OrbWeapon"):
        super().__init__(level)
        rec = fusion_recipe(a, b)
        self.a, self.b, self.rec = a, b, rec
        self.display_name = self.evolved_name = rec["name"]
        self.evolved_desc = self.base_desc = rec["desc"]
        self.tpl, self.col, self.fx = rec["tpl"], rec["col"], rec["fx"]
        self.tags = FUSION_TPL_TAGS[self.tpl]
        self.sfx_name = self.SFX[self.tpl]
        self.evolved = False
        self._rar = fusion_recipe_rarity(a, b)
        self.hud_color = (225, 150, 255)
        self.timer = 0.0
        self.effect_timer = 0.0
        self.beam_timer = 0.0
        self.beams = []
        self.lines = []
        self.vis_r = 100
        self.zone_budget = 0

    @property
    def rarity(self):
        return self._rar

    @property
    def hud_label(self):
        return "FUSI: %s Lv.%d" % (self.display_name, self.level)

    def level_up(self):
        if self.level < MAX_WEAPON_LEVEL:
            self.level += 1

    def apply_evolution(self, value):
        mult = WEAPON_DAMAGE_MULT * PLAYER_BUFFS["dmg"] * PLAYER_BUFFS["perm"] * RARITY_MULT[self.rarity]
        mult *= FUSION_DAMAGE_MULT * (1.0 + 0.16 * max(0, self.level - 3))
        mult *= RUN_RULES["avatar_dmg"]
        return value * mult

    @property
    def damage(self):
        lv = self.level
        base = {"nova": 28 + lv * 12, "blades": 14 + lv * 6, "beam": 22 + lv * 9, "barrage": 12 + lv * 5,
                "storm": 26 + lv * 11, "chain": 16 + lv * 7}[self.tpl]
        return self.apply_evolution(base)

    @property
    def cooldown(self):
        lv = self.level
        return {"nova": max(1.4, 3.2 - lv * 0.25), "blades": max(0.8, 1.9 - lv * 0.15), "beam": max(1.0, 2.4 - lv * 0.2),
                "barrage": max(0.8, 1.7 - lv * 0.13), "storm": max(1.2, 3.0 - lv * 0.25), "chain": max(0.6, 1.5 - lv * 0.12)}[self.tpl]

    @property
    def radius(self):
        return int((170 + self.level * 16) * SKILL_SCALE)

    def side_fx(self, game, e, dmg, ox, oy):
        """Efek tambahan (beku/lumpuh/bakar/racun/tarik) pada musuh yang kena. (ox,oy) = pusat tarikan."""
        if e.dead:
            return
        for f in self.fx:
            if f == "freeze":
                if not e.is_boss and not getattr(e, "ice_immune", False):
                    e.frozen_timer = max(e.frozen_timer, 1.2 + 0.12 * self.level)
            elif f == "stun":
                if not e.is_boss:
                    e.frozen_timer = max(e.frozen_timer, 0.8 + 0.05 * self.level)
            elif f in ("burn", "poison"):
                if not e.dead:
                    if f == "burn":
                        game.ignite_enemy(e, max(2.0, dmg * 0.15), 3.0)
                    else:
                        game.poison_enemy(e, max(2.0, dmg * 0.15), 4.0)
                if self.zone_budget > 0 and len(game.poison_zones) < MAX_POISON_ZONES and random.random() < 0.4:
                    self.zone_budget -= 1
                    game.poison_zones.append(PoisonZone(e.x, e.y, 48, dmg * 0.10, 0.5, 2.4, FIRE_COLOR if f == "burn" else POISON_COLOR))
            elif f == "pull":
                if not e.is_boss:
                    dx, dy = ox - e.x, oy - e.y
                    m = math.hypot(dx, dy) or 1.0
                    e.kb_vx, e.kb_vy, e.kb_timer = dx / m * 12, dy / m * 12, 0.3

    def freeze_args(self):
        if "freeze" in self.fx:
            return True, 1.2 + 0.12 * self.level
        if "stun" in self.fx:
            return True, 0.8 + 0.05 * self.level
        return False, 0

    def area_fx(self, game, tx, ty, dmg):
        """Efek area untuk template berbasis peluru: zona bakar/racun di sasaran, tarikan musuh sekitar."""
        for f in self.fx:
            if f in ("burn", "poison") and len(game.poison_zones) < MAX_POISON_ZONES:
                game.poison_zones.append(PoisonZone(tx, ty, 60, dmg * 0.10, 0.5, 2.6, FIRE_COLOR if f == "burn" else POISON_COLOR))
            elif f == "pull":
                for e in game.enemies_in_range(tx, ty, 260):
                    if not e.is_boss and not e.dead:
                        dx, dy = tx - e.x, ty - e.y
                        m = math.hypot(dx, dy) or 1.0
                        e.kb_vx, e.kb_vy, e.kb_timer = dx / m * 10, dy / m * 10, 0.3

    def update(self, dt, game):
        self.timer -= dt
        if self.effect_timer > 0:
            self.effect_timer -= dt
        if self.beam_timer > 0:
            self.beam_timer -= dt
        if self.timer > 0:
            return
        self.zone_budget = 4
        getattr(self, "fire_" + self.tpl)(game)

    def fire_nova(self, game):
        bx, by = game.badang.x, game.badang.y
        r = self.radius
        targets = game.enemies_in_range(bx, by, r)
        if not targets:
            self.timer = 0.25
            return
        self.timer = self.cooldown
        self.effect_timer = 0.35
        self.vis_r = r
        dmg = self.damage
        for e in list(targets):
            if e.dead:
                continue
            if "pull" in self.fx and not e.is_boss:
                self.side_fx_pull_only(e, bx, by)
            game.damage_enemy(e, dmg)
            self.side_fx(game, e, dmg, bx, by)

    def side_fx_pull_only(self, e, ox, oy):
        dx, dy = ox - e.x, oy - e.y
        m = math.hypot(dx, dy) or 1.0
        e.kb_vx, e.kb_vy, e.kb_timer = dx / m * 12, dy / m * 12, 0.3

    def fire_blades(self, game):
        target = game.find_nearest_enemy()
        if target is None or dist_sq(target.x, target.y, game.badang.x, game.badang.y) > 620 ** 2:
            self.timer = 0.25
            return
        self.timer = self.cooldown
        bx, by = game.badang.x, game.badang.y
        n = 6 + self.level // 2
        off = random.random() * math.tau
        dmg = self.damage
        fz, fd = self.freeze_args()
        for i in range(n):
            if len(game.projectiles) >= MAX_PLAYER_PROJECTILES:
                break
            a = off + i * math.tau / n
            game.projectiles.append(Projectile(bx, by, bx + math.cos(a) * 200, by + math.sin(a) * 200, 9.5, dmg, self.col,
                                               radius=9, pierce=99, life=0.85, freeze_on_hit=fz, freeze_duration=fd, style="knife"))
        self.area_fx(game, target.x, target.y, dmg)

    def fire_beam(self, game):
        target = game.find_nearest_enemy()
        if target is None:
            self.timer = 0.2
            return
        self.timer = self.cooldown
        bx, by = game.badang.x, game.badang.y
        base = math.atan2(target.y - by, target.x - bx)
        dmg = self.damage
        hw = (26 + self.level * 3) / 2
        self.beams = []
        self.beam_w = hw * 2
        for ang in fan_angles(base, 3 if self.level >= 5 else 2, 24):
            x2, y2 = bx + math.cos(ang) * 820, by + math.sin(ang) * 820
            self.beams.append((bx, by, x2, y2))
            for e in game.enemies:
                if e.dead:
                    continue
                if seg_dist_sq(e.x, e.y, bx, by, x2, y2) <= (hw + e.radius) ** 2:
                    game.damage_enemy(e, dmg)
                    self.side_fx(game, e, dmg, bx, by)
        self.beam_timer = 0.22

    def fire_barrage(self, game):
        target = game.find_nearest_enemy()
        if target is None:
            self.timer = 0.25
            return
        self.timer = self.cooldown
        bx, by = game.badang.x, game.badang.y
        base = math.atan2(target.y - by, target.x - bx)
        dmg = self.damage
        n = 3 + self.level
        fz, fd = self.freeze_args()
        for ang in fan_angles(base, n, 20):
            if len(game.projectiles) >= MAX_PLAYER_PROJECTILES:
                break
            game.projectiles.append(Projectile(bx, by, bx + math.cos(ang) * 200, by + math.sin(ang) * 200, 7.5, dmg, self.col,
                                               splash_radius=55, splash_damage=dmg * 0.5, radius=8, life=2.4, homing=True,
                                               freeze_on_hit=fz, freeze_duration=fd, style="orb"))
        self.area_fx(game, target.x, target.y, dmg)

    def fire_storm(self, game):
        bx, by = game.badang.x, game.badang.y
        pool = game.enemies_in_range(bx, by, 640)
        if not pool:
            self.timer = 0.3
            return
        self.timer = self.cooldown
        dmg = self.damage
        rad = 60 + self.level * 5
        stun = 1.6 if "freeze" in self.fx else (1.0 if "stun" in self.fx else 0.0)
        kind = "meteor" if "burn" in self.fx else ("spike" if ("freeze" in self.fx or "poison" in self.fx) else "bolt")
        zone = None
        if "burn" in self.fx:
            zone = (rad * 0.7, dmg * 0.12, 2.5, FIRE_COLOR)
        elif "poison" in self.fx:
            zone = (rad * 0.7, dmg * 0.12, 2.5, POISON_COLOR)
        for e in random.sample(pool, min(2 + self.level // 2 + (1 if self.level >= 5 else 0), len(pool))):
            if len(game.strikes) >= 40:
                break
            game.strikes.append(PlayerStrike(e.x, e.y, rad, dmg, 0.6, self.col, stun=stun, kind=kind, zone=zone))
            if "pull" in self.fx:
                self.area_fx(game, e.x, e.y, dmg)

    def fire_chain(self, game):
        current = game.find_nearest_enemy()
        if current is None:
            self.timer = 0.25
            return
        self.timer = self.cooldown
        self.lines = []
        hit_ids = set()
        dmg = self.damage
        prev = (game.badang.x, game.badang.y)
        hops, max_hops = 0, 4 + self.level + (2 if self.level >= 5 else 0)
        r2 = 230 ** 2
        while current is not None and hops < max_hops and id(current) not in hit_ids:
            game.damage_enemy(current, dmg, pierce=False)
            self.side_fx(game, current, dmg, prev[0], prev[1])
            hit_ids.add(id(current))
            self.lines.append((prev[0], prev[1], current.x, current.y))
            prev = (current.x, current.y)
            dmg *= 0.8
            hops += 1
            cands = [e for e in game.enemies if not e.dead and id(e) not in hit_ids and dist_sq(e.x, e.y, prev[0], prev[1]) <= r2]
            current = min(cands, key=lambda e: dist_sq(e.x, e.y, prev[0], prev[1])) if cands else None
        self.effect_timer = 0.22

    def draw(self, surf, game):
        t = pygame.time.get_ticks() / 1000.0
        col = self.col
        for k in range(3):
            a = t * 2.2 + k * math.tau / 3
            px = int(CENTER[0] + math.cos(a) * 34 * SKILL_SCALE)
            py = int(CENTER[1] + math.sin(a) * 34 * SKILL_SCALE)
            pygame.draw.polygon(surf, col, [(px, py - 5), (px + 4, py), (px, py + 5), (px - 4, py)])
            pygame.draw.polygon(surf, WHITE, [(px, py - 5), (px + 4, py), (px, py + 5), (px - 4, py)], 1)
        tpl = self.tpl
        if tpl == "nova" and self.effect_timer > 0:
            prog = 1 - self.effect_timer / 0.35
            r = max(1, int(self.vis_r * prog))
            pygame.draw.circle(surf, _dk(col, 0.6), CENTER, r, 9)
            pygame.draw.circle(surf, col, CENTER, r, 6)
            pygame.draw.circle(surf, WHITE, CENTER, r, 2)
            if r > 30:
                pygame.draw.circle(surf, _lt(col, 0.4), CENTER, int(r * 0.78), 2)
        elif tpl == "beam" and self.beam_timer > 0 and self.beams:
            cam_x, cam_y = game.get_camera()
            w = max(2, int(getattr(self, "beam_w", 30) * self.beam_timer / 0.22))
            for (x1, y1, x2, y2) in self.beams:
                p1, p2 = (x1 - cam_x, y1 - cam_y), (x2 - cam_x, y2 - cam_y)
                pygame.draw.line(surf, _dk(col, 0.55), p1, p2, w + 8)
                pygame.draw.line(surf, col, p1, p2, w)
                pygame.draw.line(surf, WHITE, p1, p2, max(1, w // 3))
                pygame.draw.circle(surf, _lt(col, 0.6), (int(p1[0]), int(p1[1])), w // 2 + 6)
        elif tpl == "chain" and self.effect_timer > 0 and self.lines:
            cam_x, cam_y = game.get_camera()
            for (x1, y1, x2, y2) in self.lines:
                draw_bolt(surf, x1 - cam_x, y1 - cam_y, x2 - cam_x, y2 - cam_y, col, 6, 7, 12)


COMBO_DEFS = [
    ("steam", (FireballWeapon, IceSpikeWeapon), "Uap Beku", "Bola Api membekukan musuh"),
    ("storm", (ShockwaveWeapon, ChainLightningWeapon), "Badai Petir", "Kejut memicu Petir"),
    ("orb_arrow", (OrbWeapon, MultiArrowWeapon), "Hujan Bintang", "Bola Energi +2 tembakan"),
    ("toxic_aura", (AuraWeapon, PoisonCloudWeapon), "Kabut Maut", "Aura & racun lebih luas/lama"),
    ("fist_boom", (PunchWeapon, BoomerangWeapon), "Tinju Bumerang", "Bumerang +1 lemparan"),
    ("inferno", (FireballWeapon, AuraWeapon), "Neraka Api", "Bola Api & Aura menyala"),
    ("frost_quake", (IceSpikeWeapon, ShockwaveWeapon), "Gempa Es", "Duri Es & Kejut menghantam"),
    ("venom_bolt", (PoisonCloudWeapon, ChainLightningWeapon), "Petir Beracun", "Racun & Petir menyatu"),
    ("laser_storm", (LaserWeapon, SkyLightningWeapon), "Laser Badai", "Laser memicu sambaran petir"),
    ("meteor_fire", (MeteorWeapon, FireTrailWeapon), "Meteor Api", "Meteor meninggalkan api membara"),
    ("tornado_fire", (TornadoWeapon, FireballWeapon), "Puting Api", "Tornado jadi 30% lebih besar"),
    ("spirit_poison", (HomingSpiritWeapon, PoisonCloudWeapon), "Roh Racun", "Roh Pemburu +2 roh"),
    ("knife_shock", (KnifeWeapon, ShockwaveWeapon), "Pisau Kejut", "Pisau Terbang +3 pisau"),
    ("shield_spike", (ShieldWeapon, GroundSpikeWeapon), "Benteng Bumi", "Perisai kebal +15%, Duri +2"),
    ("bounce_chain", (BounceOrbWeapon, ChainLightningWeapon), "Bola Listrik", "Bola memantul +4 kali"),
    ("laser_ice", (LaserWeapon, IceSpikeWeapon), "Laser Beku", "Laser membekukan musuh"),
]
COMBO_TITLES = {k: t for (k, _c, t, _d) in COMBO_DEFS}
COMBO_DESCS = {k: d + " (+40% damage)" for (k, _c, _t, d) in COMBO_DEFS}
COMBO_COLOR = (255, 170, 255)
COMBO_CLASSES = {k: c for (k, c, _t, _d) in COMBO_DEFS}
COMBO_COLORS = {
    "steam": (170, 225, 255), "storm": (255, 235, 110), "orb_arrow": (130, 190, 255), "toxic_aura": (140, 220, 100),
    "fist_boom": (255, 185, 110), "inferno": (255, 110, 50), "frost_quake": (140, 200, 255), "venom_bolt": (190, 240, 90),
    "laser_storm": (255, 90, 140), "meteor_fire": (255, 150, 60), "tornado_fire": (255, 170, 90), "spirit_poison": (200, 160, 255),
    "knife_shock": (225, 230, 245), "shield_spike": (205, 165, 100), "bounce_chain": (255, 150, 255), "laser_ice": (120, 235, 245),
}
COMBO_RING = {k: i for i, k in enumerate(COMBO_COLORS)}


class Boomerang:
    def __init__(self, x, y, angle, speed, damage, radius=9, out_duration=0.35):
        self.x, self.y = x, y
        self.vx, self.vy = math.cos(angle) * speed, math.sin(angle) * speed
        self.speed = speed
        self.damage = damage
        self.radius = radius
        self.phase = "out"
        self.out_timer = out_duration
        self.alive = True
        self.hit_ids = set()

    def update(self, dt, badang):
        if self.phase == "out":
            self.x += self.vx * dt * 60
            self.y += self.vy * dt * 60
            self.out_timer -= dt
            if self.out_timer <= 0:
                self.phase = "back"
                self.hit_ids = set()
        else:
            dx, dy = badang.x - self.x, badang.y - self.y
            d = math.hypot(dx, dy) or 1
            self.x += dx / d * self.speed * dt * 60
            self.y += dy / d * self.speed * dt * 60
            if d < 24:
                self.alive = False

    def draw(self, surf, cam_x, cam_y):
        sx, sy = self.x - cam_x, self.y - cam_y
        if -30 <= sx <= WIDTH + 30 and -30 <= sy <= HEIGHT + 30:
            draw_boomerang_shape(surf, sx, sy, pygame.time.get_ticks() / 1000.0 * 14, self.radius)


class StraightPunchSkill:
    """Otomatis menyerang musuh terdekat setiap 10 detik: pukulan garis
    lurus, jangkauan jauh, damage besar, dan knockback."""

    def __init__(self):
        self.name = "Tinju Lurus"
        self.cooldown = 10.0
        self.timer = 0.0
        self.effect_timer = 0.0
        self.effect_duration = 0.2
        self.length = 320
        self.width = 100
        self.damage = 55 * WEAPON_DAMAGE_MULT
        self.knockback = 22
        self.engage_range = 560

    @property
    def ready(self):
        return self.timer <= 0

    def update(self, dt, game):
        if self.timer > 0:
            self.timer -= dt
        if self.effect_timer > 0:
            self.effect_timer -= dt
        if self.ready:
            target = game.find_nearest_enemy()
            if target:
                if dist_sq(target.x, target.y, game.badang.x, game.badang.y) <= self.engage_range ** 2:
                    fx, fy = target.x - game.badang.x, target.y - game.badang.y
                    m = math.hypot(fx, fy) or 1
                    game.badang.facing = (fx / m, fy / m)
                    self.trigger(game)

    def trigger(self, game):
        if not self.ready:
            return False
        self.timer = self.cooldown
        self.effect_timer = self.effect_duration
        fx, fy = game.badang.facing
        bx, by = game.badang.x, game.badang.y
        for e in game.enemies:
            if e.dead:
                continue
            dx, dy = e.x - bx, e.y - by
            forward = dx * fx + dy * fy
            perp = dx * (-fy) + dy * fx
            if 0 <= forward <= self.length and abs(perp) <= self.width / 2 + e.radius:
                game.damage_enemy(e, self.damage)
                if not e.dead:
                    e.kb_vx = fx * self.knockback
                    e.kb_vy = fy * self.knockback
                    e.kb_timer = 0.35
        return True

    def draw(self, surf, game):
        if self.effect_timer <= 0:
            return
        fx, fy = game.badang.facing
        progress = 1 - (self.effect_timer / self.effect_duration)
        length = self.length * min(1.0, progress * 2.4)
        ang = math.atan2(fy, fx)
        for k in range(-2, 3):
            off = k * 18
            x0 = CENTER[0] + math.cos(ang) * 22 - math.sin(ang) * off
            y0 = CENTER[1] + math.sin(ang) * 22 + math.cos(ang) * off
            pygame.draw.line(surf, STRAIGHT_PUNCH_COLOR, (x0, y0), (x0 + math.cos(ang) * length * 0.85,
                                                                  y0 + math.sin(ang) * length * 0.85), 2)
        draw_fist(surf, CENTER[0] + math.cos(ang) * (22 + length), CENTER[1] + math.sin(ang) * (22 + length), ang, 28)
        pygame.draw.circle(surf, WHITE, (int(CENTER[0] + math.cos(ang) * (48 + length)),
                                         int(CENTER[1] + math.sin(ang) * (48 + length))), 8, 2)


class SpecialSkill:
    """Dasar skill khusus avatar: otomatis aktif saat siap & ada musuh."""
    name = "Skill Khusus"
    cooldown = 10.0
    engage_range = 450

    def __init__(self):
        self.timer = 2.0
        self.effect_timer = 0.0

    @property
    def ready(self):
        return self.timer <= 0

    def scale(self, game):
        """Damage skill khusus ikut naik seiring level Badang."""
        return WEAPON_DAMAGE_MULT * PLAYER_BUFFS["dmg"] * PLAYER_BUFFS["perm"] * (1 + 0.05 * (game.badang.level - 1))

    def should_trigger(self, game):
        t = game.find_nearest_enemy()
        return t is not None and dist_sq(t.x, t.y, game.badang.x, game.badang.y) <= self.engage_range ** 2

    def trigger(self, game):
        pass

    def update(self, dt, game):
        if self.timer > 0:
            self.timer -= dt
        if self.effect_timer > 0:
            self.effect_timer -= dt
        if self.ready and self.should_trigger(game):
            self.timer = self.cooldown
            self.trigger(game)

    def draw(self, surf, game):
        pass


class RezDashSkill(SpecialSkill):
    """REZ - Tebasan Kilat: melesat menembus musuh, menebas, kebal sesaat."""
    name = "Tebasan Kilat"
    cooldown = 7.0
    dash_dist = 260
    width = 100
    engage_range = 420

    def __init__(self):
        super().__init__()
        self.line = None

    def trigger(self, game):
        t = game.find_nearest_enemy()
        b = game.badang
        fx, fy = t.x - b.x, t.y - b.y
        m = math.hypot(fx, fy) or 1
        fx, fy = fx / m, fy / m
        b.facing = (fx, fy)
        length = self.dash_dist + 60
        dmg = 38 * self.scale(game)
        for e in game.enemies:
            if e.dead:
                continue
            dx, dy = e.x - b.x, e.y - b.y
            forward = dx * fx + dy * fy
            perp = dx * (-fy) + dy * fx
            if -20 <= forward <= length and abs(perp) <= self.width / 2 + e.radius:
                game.damage_enemy(e, dmg)
        self.line = (b.x, b.y, b.x + fx * self.dash_dist, b.y + fy * self.dash_dist)
        b.x += fx * self.dash_dist
        b.y += fy * self.dash_dist
        b.invuln_timer = max(b.invuln_timer, 0.7)
        self.effect_timer = 0.3

    def draw(self, surf, game):
        if self.effect_timer <= 0 or not self.line:
            return
        cam_x, cam_y = game.get_camera()
        x1, y1, x2, y2 = self.line
        k = self.effect_timer / 0.3
        p1, p2 = (x1 - cam_x, y1 - cam_y), (x2 - cam_x, y2 - cam_y)
        w = max(3, int(16 * k))
        draw_bolt(surf, p1[0], p1[1], p2[0], p2[1], (255, 235, 110), w, 9, 20)
        pygame.draw.line(surf, (255, 250, 210), p1, p2, max(1, w // 4))
        ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
        for i in (-1, 0, 1):
            a = ang + i * 0.8
            pygame.draw.line(surf, WHITE, (p2[0] - math.cos(a) * 55 * k, p2[1] - math.sin(a) * 55 * k),
                             (p2[0] + math.cos(a) * 55 * k, p2[1] + math.sin(a) * 55 * k), max(1, int(5 * k)))
        if k > 0.35:
            draw_wizard(surf, int(p1[0]), int(p1[1]), game.badang.avatar, 1.0, True)


class BlackHoleSkill(SpecialSkill):
    """BLACK HOLE - Lubang Hitam: menyedot & menggerus musuh di area."""
    name = "Lubang Hitam"
    cooldown = 16.0
    radius = 280
    duration = 4.5
    engage_range = 520

    def __init__(self):
        super().__init__()
        self.holes = []

    def trigger(self, game):
        t = game.find_nearest_enemy()
        self.holes.append([t.x, t.y, self.duration, 0.0])
        self.effect_timer = 0.3

    def update(self, dt, game):
        super().update(dt, game)
        if not self.holes:
            return
        dmg = 30 * self.scale(game) * 0.4
        r2 = self.radius ** 2
        dmg_r2 = (self.radius * 0.9) ** 2
        for h in self.holes:
            h[2] -= dt
            h[3] -= dt
            do_tick = h[3] <= 0
            if do_tick:
                h[3] = 0.4
            for e in game.enemies:
                if e.dead:
                    continue
                d2 = dist_sq(e.x, e.y, h[0], h[1])
                if d2 > r2:
                    continue
                d = math.sqrt(d2) or 1
                if d > 8:
                    step = min((2.2 if e.is_boss else 4.5) * dt * 60, d)
                    e.x += (h[0] - e.x) / d * step
                    e.y += (h[1] - e.y) / d * step
                if do_tick and d2 <= dmg_r2:
                    game.damage_enemy(e, dmg)
        self.holes = [h for h in self.holes if h[2] > 0]

    def draw(self, surf, game):
        if not self.holes:
            return
        cam_x, cam_y = game.get_camera()
        t = pygame.time.get_ticks() / 1000.0
        for x, y, life, _tick in self.holes:
            sx, sy = int(x - cam_x), int(y - cam_y)
            if not (-350 <= sx <= WIDTH + 350 and -350 <= sy <= HEIGHT + 350):
                continue
            R = self.radius
            pygame.draw.circle(surf, (70, 35, 120), (sx, sy), R, 1)
            for arm in range(4):
                pts = []
                for i in range(14):
                    rr = 26 + i * (R * 0.55 - 26) / 13
                    a = arm * math.pi / 2 + t * 2.8 + rr * 0.035
                    pts.append((sx + math.cos(a) * rr, sy + math.sin(a) * rr * 0.55))
                pygame.draw.lines(surf, (150, 90, 235) if arm % 2 else (95, 55, 175), False, pts, 3)
            for i in range(10):
                f = ((t * 0.7 + i / 10.0) % 1.0)
                rr = R * (1 - f)
                a = i * 0.63 + t * 1.5
                pygame.draw.circle(surf, (200, 160, 255), (int(sx + math.cos(a) * rr), int(sy + math.sin(a) * rr)),
                                   max(1, int(4 * (1 - f))))
            pygame.draw.circle(surf, (8, 3, 16), (sx, sy), 26)
            pygame.draw.circle(surf, (230, 200, 255), (sx, sy), 27, 2)
            pygame.draw.circle(surf, (170, 90, 255), (sx, sy), 32 + int(2 * math.sin(t * 8)), 2)


class RageSkill(SpecialSkill):
    """DEAD STRONG - Amukan Kuat: damage semua skill x1.7 & lebih cepat."""
    name = "Amukan Kuat"
    cooldown = 18.0
    duration = 5.0
    dmg_mult = 1.7
    speed_mult = 1.25

    def __init__(self):
        super().__init__()
        self.active_timer = 0.0

    def should_trigger(self, game):
        b = game.badang
        near = 0
        for e in game.enemies:
            if e.dead:
                continue
            if dist_sq(e.x, e.y, b.x, b.y) <= 300 ** 2:
                if e.is_boss:
                    return True
                near += 1
                if near >= 3:
                    return True
        return False

    def trigger(self, game):
        self.active_timer = self.duration
        self.effect_timer = 0.4
        b = game.badang
        dmg = 30 * self.scale(game)
        for e in game.enemies:
            if e.dead:
                continue
            if dist_sq(e.x, e.y, b.x, b.y) <= 200 ** 2:
                game.damage_enemy(e, dmg)
                if not e.dead and not e.is_boss:
                    nx, ny = e.x - b.x, e.y - b.y
                    m = math.hypot(nx, ny) or 1
                    e.kb_vx = nx / m * 16
                    e.kb_vy = ny / m * 16
                    e.kb_timer = 0.3
        game.show_toast("AMUKAN KUAT!")

    def update(self, dt, game):
        super().update(dt, game)
        if self.active_timer > 0:
            self.active_timer -= dt
        active = self.active_timer > 0
        PLAYER_BUFFS["dmg"] = self.dmg_mult if active else 1.0
        game.badang.speed_buff = self.speed_mult if active else 1.0

    def draw(self, surf, game):
        t = pygame.time.get_ticks() / 1000.0
        if self.active_timer > 0:
            for i in range(14):
                a = i * math.tau / 14 + t * 1.2
                h = 26 + 12 * math.sin(t * 10 + i * 1.7)
                bx, by = CENTER[0] + math.cos(a) * 36, CENTER[1] + math.sin(a) * 36
                pygame.draw.polygon(surf, (255, 70, 40), [(bx - math.sin(a) * 8, by + math.cos(a) * 8),
                                                          (bx + math.sin(a) * 8, by - math.cos(a) * 8),
                                                          (bx + math.cos(a) * h, by + math.sin(a) * h)])
                pygame.draw.polygon(surf, (255, 200, 80), [(bx - math.sin(a) * 4, by + math.cos(a) * 4),
                                                           (bx + math.sin(a) * 4, by - math.cos(a) * 4),
                                                           (bx + math.cos(a) * h * 0.55, by + math.sin(a) * h * 0.55)])
        if self.effect_timer > 0:
            prog = 1 - self.effect_timer / 0.4
            r = max(1, int(200 * prog))
            pygame.draw.circle(surf, (255, 150, 60), CENTER, r, 5)
            for i in range(16):
                a = i * math.tau / 16
                pygame.draw.line(surf, (255, 230, 150), (CENTER[0] + math.cos(a) * r, CENTER[1] + math.sin(a) * r),
                                 (CENTER[0] + math.cos(a) * (r + 22), CENTER[1] + math.sin(a) * (r + 22)), 3)


class StringWebSkill(SpecialSkill):
    """STRING MOVE - Jaring Benang: 8 benang melukai & mengikat musuh."""
    name = "Jaring Benang"
    cooldown = 8.0
    length = 380
    width = 44
    threads = 8
    bind_time = 1.8
    engage_range = 420

    def __init__(self):
        super().__init__()
        self.lines = []

    def trigger(self, game):
        b = game.badang
        base = random.uniform(0, math.tau)
        dmg = 26 * self.scale(game)
        hit = set()
        self.lines = []
        for i in range(self.threads):
            ang = base + i * math.tau / self.threads
            fx, fy = math.cos(ang), math.sin(ang)
            self.lines.append((b.x, b.y, b.x + fx * self.length, b.y + fy * self.length))
            for e in game.enemies:
                if e.dead or id(e) in hit:
                    continue
                dx, dy = e.x - b.x, e.y - b.y
                forward = dx * fx + dy * fy
                perp = dx * (-fy) + dy * fx
                if 0 <= forward <= self.length and abs(perp) <= self.width / 2 + e.radius:
                    hit.add(id(e))
                    game.damage_enemy(e, dmg)
                    if not e.dead and not e.is_boss:
                        e.frozen_timer = max(e.frozen_timer, self.bind_time)
        self.effect_timer = 0.5

    def draw(self, surf, game):
        if self.effect_timer <= 0 or not self.lines:
            return
        cam_x, cam_y = game.get_camera()
        for (x1, y1, x2, y2) in self.lines:
            p1, p2 = (x1 - cam_x, y1 - cam_y), (x2 - cam_x, y2 - cam_y)
            pygame.draw.line(surf, (130, 255, 200), p1, p2, 3)
            ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
            for f in (0.3, 0.55, 0.8):
                cx_, cy_ = p1[0] + (p2[0] - p1[0]) * f, p1[1] + (p2[1] - p1[1]) * f
                for sgn in (-1, 1):
                    a = ang + sgn * 1.2
                    pygame.draw.line(surf, (200, 255, 230), (cx_, cy_), (cx_ + math.cos(a) * 14, cy_ + math.sin(a) * 14), 1)
            pygame.draw.circle(surf, WHITE, (int(p2[0]), int(p2[1])), 6)
            pygame.draw.circle(surf, (130, 255, 200), (int(p2[0]), int(p2[1])), 6, 2)


def crowd_near(game, radius, n):
    """True bila ada >= n musuh (atau 1 bos) dalam jarak 'radius' dari pemain."""
    b = game.badang
    r2 = radius * radius
    cnt = 0
    for e in game.enemies:
        if e.dead:
            continue
        if dist_sq(e.x, e.y, b.x, b.y) <= r2:
            if e.is_boss:
                return True
            cnt += 1
            if cnt >= n:
                return True
    return False


class FastLightSkill(SpecialSkill):
    """FAST LIGHT - Kilat Cahaya: lari super cepat, jejak cahaya melukai musuh."""
    name = "Kilat Cahaya"
    cooldown = 12.0
    duration = 4.5
    speed_mult = 1.8

    def __init__(self):
        super().__init__()
        self.active_timer = 0.0
        self.tick = 0.0
        self.trail = []

    def should_trigger(self, game):
        return crowd_near(game, 380, 3)

    def trigger(self, game):
        self.active_timer = self.duration
        self.effect_timer = 0.3
        game.show_toast("KILAT CAHAYA!")

    def update(self, dt, game):
        super().update(dt, game)
        b = game.badang
        active = self.active_timer > 0
        if active:
            self.active_timer -= dt
            self.tick -= dt
            self.trail.append([b.x, b.y, 0.6])
            if self.tick <= 0:
                self.tick = 0.12
                dmg = 14 * self.scale(game)
                for e in game.enemies:
                    if not e.dead and dist_sq(e.x, e.y, b.x, b.y) <= 80 ** 2:
                        game.damage_enemy(e, dmg)
        b.speed_buff = self.speed_mult if active else 1.0
        for p in self.trail:
            p[2] -= dt
        self.trail = [p for p in self.trail if p[2] > 0][-45:]

    def draw(self, surf, game):
        cam_x, cam_y = game.get_camera()
        n = len(self.trail)
        for idx, (x, y, life) in enumerate(self.trail):
            r = max(2, int(14 * life / 0.6))
            sx, sy = int(x - cam_x), int(y - cam_y)
            pygame.draw.circle(surf, (255, 255, 160), (sx, sy), r)
            if idx % 3 == 0 and n > 3:
                pygame.draw.line(surf, WHITE, (sx, sy), (sx + random.randint(-14, 14), sy + random.randint(-14, 14)), 2)
        if self.active_timer > 0:
            t = pygame.time.get_ticks() / 1000.0
            pygame.draw.circle(surf, (255, 255, 200), CENTER, 44 + int(4 * math.sin(t * 14)), 2)


class YomatodaSkill(SpecialSkill):
    """YOMATODA - Gerbang Yomi: menguras musuh sekitar, memulihkan HP, melepas roh."""
    name = "Gerbang Yomi"
    cooldown = 14.0
    radius = 380

    def should_trigger(self, game):
        return crowd_near(game, 360, 4)

    def trigger(self, game):
        b = game.badang
        dmg = 38 * self.scale(game)
        hit = 0
        r2 = self.radius ** 2
        for e in game.enemies:
            if not e.dead and dist_sq(e.x, e.y, b.x, b.y) <= r2:
                game.damage_enemy(e, dmg)
                hit += 1
        heal = min(60, 20 + hit * 2)
        b.hp = min(b.max_hp, b.hp + heal)
        game.add_damage_text(b.x, b.y - 42, "+%d" % heal, DMG_COLOR_HEAL, big=True)
        for i in range(6):
            if len(game.projectiles) >= MAX_PLAYER_PROJECTILES:
                break
            a = i * math.tau / 6
            game.projectiles.append(Projectile(b.x, b.y, b.x + math.cos(a) * 100, b.y + math.sin(a) * 100,
                                               5.5, 15 * self.scale(game), (205, 175, 255), radius=8,
                                               pierce=2, life=3.5, homing=True, style="spirit"))
        self.effect_timer = 0.6

    def draw(self, surf, game):
        if self.effect_timer > 0:
            prog = 1 - self.effect_timer / 0.6
            r = max(1, int(self.radius * prog))
            t = pygame.time.get_ticks() / 1000.0
            pygame.draw.circle(surf, (170, 110, 230), CENTER, r, 6)
            pygame.draw.circle(surf, (120, 255, 200), CENTER, max(1, int(r * 0.7)), 2)
            for i in range(12):
                a = i * math.tau / 12 + t * 1.5
                rx, ry = CENTER[0] + math.cos(a) * r * 0.85, CENTER[1] + math.sin(a) * r * 0.85
                pygame.draw.rect(surf, (200, 255, 230), (rx - 4, ry - 4, 8, 8), 2)
                pygame.draw.polygon(surf, (150, 255, 210), [(rx, ry - 20 * prog - 8), (rx + 5, ry - 20 * prog), (rx - 5, ry - 20 * prog)])


class SrukenSkill(SpecialSkill):
    """SRUKEN - Badai Shuriken: 20 shuriken menembus ke segala arah."""
    name = "Badai Shuriken"
    cooldown = 6.0
    engage_range = 450

    def trigger(self, game):
        b = game.badang
        dmg = 16 * self.scale(game)
        off = random.uniform(0, math.tau)
        for i in range(20):
            if len(game.projectiles) >= MAX_PLAYER_PROJECTILES:
                break
            a = off + i * math.tau / 20
            game.projectiles.append(Projectile(b.x, b.y, b.x + math.cos(a) * 100, b.y + math.sin(a) * 100,
                                               9.0, dmg, (225, 225, 235), radius=7, pierce=3, life=1.3, style="shuriken"))
        self.effect_timer = 0.25

    def draw(self, surf, game):
        if self.effect_timer > 0:
            prog = 1 - self.effect_timer / 0.25
            r = 50 + 150 * prog
            t = pygame.time.get_ticks() / 1000.0
            pygame.draw.circle(surf, (230, 230, 240), CENTER, int(r), 2)
            for i in range(8):
                a = i * math.tau / 8 + t * 2
                draw_proj_shape(surf, "shuriken", CENTER[0] + math.cos(a) * r, CENTER[1] + math.sin(a) * r, a, 8, (225, 225, 235), t)


class MuscleSkill(SpecialSkill):
    """MUSCLE SKRIM - Hantaman Gunung: menghantam tanah, musuh pingsan, tubuh lebih kebal."""
    name = "Hantaman Gunung"
    cooldown = 11.0
    radius = 340

    def __init__(self):
        super().__init__()
        self.active_timer = 0.0

    def should_trigger(self, game):
        return crowd_near(game, 300, 3)

    def trigger(self, game):
        b = game.badang
        dmg = 55 * self.scale(game)
        for e in game.enemies:
            if e.dead or dist_sq(e.x, e.y, b.x, b.y) > self.radius ** 2:
                continue
            game.damage_enemy(e, dmg)
            if not e.dead and not e.is_boss:
                e.frozen_timer = max(e.frozen_timer, 2.0)
                nx, ny = e.x - b.x, e.y - b.y
                m = math.hypot(nx, ny) or 1
                e.kb_vx, e.kb_vy, e.kb_timer = nx / m * 12, ny / m * 12, 0.25
        b.invuln_timer = max(b.invuln_timer, 1.0)
        self.active_timer = 5.0
        self.effect_timer = 0.45
        game.show_toast("HANTAMAN GUNUNG!")

    def update(self, dt, game):
        super().update(dt, game)
        if self.active_timer > 0:
            self.active_timer -= dt
        game.badang.dr_skill = 0.4 if self.active_timer > 0 else 0.0

    def draw(self, surf, game):
        if self.effect_timer > 0:
            prog = 1 - self.effect_timer / 0.45
            r = max(1, int(self.radius * prog))
            pygame.draw.circle(surf, (190, 140, 80), CENTER, r, 9)
            random.seed(int(self.timer * 7))
            for i in range(12):
                a = i * math.tau / 12 + 0.2
                pts = [(CENTER[0], CENTER[1])]
                for j in range(1, 6):
                    rr = r * j / 5
                    aa = a + random.uniform(-0.12, 0.12)
                    pts.append((CENTER[0] + math.cos(aa) * rr, CENTER[1] + math.sin(aa) * rr))
                pygame.draw.lines(surf, (80, 55, 30), False, pts, 3)
            random.seed()
        if self.active_timer > 0:
            t = pygame.time.get_ticks() / 1000.0
            for i in range(6):
                a = i * math.tau / 6 + t
                px, py = CENTER[0] + math.cos(a) * 54, CENTER[1] + math.sin(a) * 54
                pygame.draw.polygon(surf, (150, 120, 85), [(px - 8, py + 6), (px - 5, py - 8), (px + 6, py - 7), (px + 9, py + 5)])
                pygame.draw.polygon(surf, (70, 50, 30), [(px - 8, py + 6), (px - 5, py - 8), (px + 6, py - 7), (px + 9, py + 5)], 2)


class MonsterSkill(SpecialSkill):
    """BRUDAL MONGSKTER - Amarah Monster: membesar, damage x1.5, pulih cepat, aura melukai."""
    name = "Amarah Monster"
    cooldown = 20.0
    duration = 6.0
    aura = 110

    def __init__(self):
        super().__init__()
        self.active_timer = 0.0
        self.tick = 0.0

    @property

    def should_trigger(self, game):
        return crowd_near(game, 320, 4)

    def trigger(self, game):
        self.active_timer = self.duration
        self.effect_timer = 0.4
        game.show_toast("AMARAH MONSTER!")

    def update(self, dt, game):
        super().update(dt, game)
        b = game.badang
        active = self.active_timer > 0
        if active:
            self.active_timer -= dt
            b.hp = min(b.max_hp, b.hp + 6 * dt)
            self.tick -= dt
            if self.tick <= 0:
                self.tick = 0.3
                dmg = 28 * self.scale(game)
                for e in game.enemies:
                    if not e.dead and dist_sq(e.x, e.y, b.x, b.y) <= self.aura ** 2:
                        game.damage_enemy(e, dmg)
        PLAYER_BUFFS["dmg"] = 1.5 if active else 1.0
        b.speed_buff = 1.1 if active else 1.0
        b.draw_scale = 1.35 if active else 1.0

    def draw(self, surf, game):
        t = pygame.time.get_ticks() / 1000.0
        if self.active_timer > 0:
            r = self.aura + int(5 * math.sin(t * 9))
            pygame.draw.circle(surf, (255, 60, 60), CENTER, r, 3)
            for i in range(18):
                a = i * math.tau / 18 + t * 0.8
                l = 14 + 8 * math.sin(t * 8 + i)
                pygame.draw.polygon(surf, (255, 90, 60), [(CENTER[0] + math.cos(a - 0.08) * r, CENTER[1] + math.sin(a - 0.08) * r),
                                                          (CENTER[0] + math.cos(a + 0.08) * r, CENTER[1] + math.sin(a + 0.08) * r),
                                                          (CENTER[0] + math.cos(a) * (r + l), CENTER[1] + math.sin(a) * (r + l))])
        if self.effect_timer > 0:
            pygame.draw.circle(surf, (255, 140, 60), CENTER, max(1, int(200 * (1 - self.effect_timer / 0.4))), 6)


NEW_AVATARS = [
    {"key": "fast_light", "name": "Fast Light", "color": (235, 245, 255), "hat": (130, 190, 255),
     "accent": (255, 255, 120), "hp": 80, "speed": 1.3, "deco": "bolt",
     "start": LaserWeapon, "special": FastLightSkill,
     "role": "Secepat cahaya, mulai Laser Sihir.",
     "skill_name": "Kilat Cahaya",
     "skill_desc": "Lari super cepat 4,5 dtk, jejak cahaya melukai. CD 12 dtk."},
    {"key": "yomatoda", "name": "Yomatoda", "color": (115, 65, 135), "hat": (40, 15, 60),
     "accent": (120, 255, 200), "hp": 105, "speed": 0.95, "deco": "ghost",
     "start": HomingSpiritWeapon, "special": YomatodaSkill,
     "role": "Penyihir alam baka, mulai Roh Pemburu.",
     "skill_name": "Gerbang Yomi",
     "skill_desc": "Menguras musuh, memulihkan HP, melepas roh. CD 14 dtk."},
    {"key": "sruken", "name": "Sruken", "color": (60, 70, 95), "hat": (20, 25, 40),
     "accent": (255, 80, 80), "hp": 90, "speed": 1.2, "deco": "mask",
     "start": KnifeWeapon, "special": SrukenSkill,
     "role": "Ninja-penyihir lincah, mulai Pisau Terbang.",
     "skill_name": "Badai Shuriken",
     "skill_desc": "Melempar 20 shuriken ke segala arah. CD 6 dtk."},
    {"key": "muscle_skrim", "name": "Muscle Skrim", "color": (205, 135, 75), "hat": (110, 60, 25),
     "accent": (255, 220, 150), "hp": 190, "speed": 0.85, "deco": "muscle",
     "start": GroundSpikeWeapon, "special": MuscleSkill,
     "role": "Kekar & tangguh, mulai Duri Bumi.",
     "skill_name": "Hantaman Gunung",
     "skill_desc": "Hantam tanah, musuh pingsan, kebal 40%. CD 11 dtk."},
    {"key": "brudal_mongskter", "name": "Brudal Mongskter", "color": (75, 165, 65), "hat": (30, 80, 25),
     "accent": (255, 60, 60), "hp": 150, "speed": 0.95, "deco": "horns",
     "start": TornadoWeapon, "special": MonsterSkill,
     "role": "Monster buas, mulai Angin Puyuh.",
     "skill_name": "Amarah Monster",
     "skill_desc": "Membesar 6 dtk: damage x1.5, pulih cepat, aura. CD 20 dtk."},
]



AVATARS = [
    {"key": "badang", "name": "Badang", "color": (70, 140, 255), "hat": (35, 70, 170),
     "accent": (255, 220, 80), "hp": 100, "speed": 1.0,
     "start": PunchWeapon, "special": StraightPunchSkill,
     "role": "Petarung seimbang, mulai dengan Tinju.",
     "skill_name": "Tinju Lurus",
     "skill_desc": "Tinju sihir lurus jauh, damage besar, musuh terpental. CD 10 dtk."},
    {"key": "rez", "name": "Rez", "color": (255, 190, 50), "hat": (160, 100, 15),
     "accent": (255, 255, 150), "hp": 85, "speed": 1.15,
     "start": ChainLightningWeapon, "special": RezDashSkill,
     "role": "Lincah tapi HP tipis, mulai Petir Rantai.",
     "skill_name": "Tebasan Kilat",
     "skill_desc": "Melesat menebas musuh dan kebal sesaat. CD 7 dtk."},
    {"key": "black_hole", "name": "Black Hole", "color": (140, 70, 210), "hat": (50, 20, 90),
     "accent": (60, 20, 100), "hp": 100, "speed": 1.0,
     "start": OrbWeapon, "special": BlackHoleSkill,
     "role": "Ahli gravitasi, mulai Bola Energi.",
     "skill_name": "Lubang Hitam",
     "skill_desc": "Lubang hitam menyedot & menggerus musuh 4,5 dtk. CD 16 dtk."},
    {"key": "dead_strong", "name": "Dead Strong", "color": (215, 65, 65), "hat": (105, 20, 25),
     "accent": (255, 140, 60), "hp": 160, "speed": 0.9,
     "start": ShockwaveWeapon, "special": RageSkill,
     "role": "HP besar tapi lambat, mulai Gelombang Kejut.",
     "skill_name": "Amukan Kuat",
     "skill_desc": "Mengamuk 5 dtk: damage semua skill x1.7 & lebih cepat. CD 18 dtk."},
    {"key": "string_move", "name": "String Move", "color": (70, 210, 150), "hat": (25, 110, 80),
     "accent": (200, 255, 230), "hp": 95, "speed": 1.05,
     "start": MultiArrowWeapon, "special": StringWebSkill,
     "role": "Licin & cepat, mulai Panah Berganda.",
     "skill_name": "Jaring Benang",
     "skill_desc": "8 benang menyambar, melukai & mengikat musuh. CD 8 dtk."},
]
AVATARS.extend(NEW_AVATARS)
AVATAR_PRICES = {"badang": 0, "rez": 900, "black_hole": 1350, "dead_strong": 1350, "string_move": 1500,
                 "fast_light": 2100, "yomatoda": 2400, "sruken": 2400, "muscle_skrim": 2700, "brudal_mongskter": 3000}
for _a in AVATARS:
    _a["price"] = AVATAR_PRICES.get(_a["key"], 500)


SKIN_TONE = (255, 222, 185)


def _eyes(surf, cx, cy, S, color=(25, 25, 35), spread=4.5, h=3.4, w=2.2):
    """Mata: sepasang oval gelap polos (tanpa pupil, mulut, alis)."""
    for k in (-1, 1):
        pygame.draw.ellipse(surf, color, (cx + k * S(spread) - S(w), cy - S(h), max(2, S(w * 2)), max(3, S(h * 2))))


def _head(surf, cx, cy, S, lw, tone=SKIN_TONE, r=10):
    pygame.draw.circle(surf, tone, (cx, cy), S(r))
    pygame.draw.circle(surf, BLACK, (cx, cy), S(r), lw)


def _robe(surf, cx, cy, S, lw, col, top=11, bot=23, y0=-8, y1=29):
    pts = [(cx - S(bot), cy + S(y1)), (cx + S(bot), cy + S(y1)), (cx + S(top), cy + S(y0)), (cx - S(top), cy + S(y0))]
    pygame.draw.polygon(surf, col, pts)
    pygame.draw.polygon(surf, BLACK, pts, lw)


def _staff(surf, x, y0, y1, S, color=(140, 95, 50)):
    pygame.draw.line(surf, color, (x, y0), (x, y1), max(2, S(4)))


def _skin_badang(surf, cx, cy, S, lw, robe, hat, acc):
    sx = cx + S(27)
    _staff(surf, sx, cy + S(30), cy - S(28), S)
    pygame.draw.circle(surf, acc, (sx, cy - S(33)), S(8))
    pygame.draw.circle(surf, WHITE, (sx, cy - S(33)), S(8), lw)
    _robe(surf, cx, cy, S, lw, robe)
    pygame.draw.line(surf, GOLD_COLOR, (cx - S(16), cy + S(12)), (cx + S(16), cy + S(12)), max(2, S(3)))
    _head(surf, cx, cy - S(15), S, lw)
    _eyes(surf, cx, cy - S(15), S)
    cone = [(cx - S(13), cy - S(21)), (cx + S(13), cy - S(21)), (cx + S(6), cy - S(58))]
    pygame.draw.polygon(surf, hat, cone)
    pygame.draw.polygon(surf, BLACK, cone, lw)
    brim = pygame.Rect(cx - S(20), cy - S(25), S(40), S(9))
    pygame.draw.ellipse(surf, hat, brim)
    pygame.draw.ellipse(surf, BLACK, brim, lw)
    pygame.draw.line(surf, GOLD_COLOR, (cx - S(12), cy - S(27)), (cx + S(12), cy - S(27)), max(2, S(3)))
    pygame.draw.circle(surf, GOLD_COLOR, (cx + S(2), cy - S(40)), max(2, S(3)))


def _skin_rez(surf, cx, cy, S, lw, robe, hat, acc):
    pygame.draw.polygon(surf, hat, [(cx - S(12), cy - S(6)), (cx + S(12), cy - S(6)), (cx + S(26), cy + S(30)), (cx - S(26), cy + S(30))])
    zz = [(cx + S(26), cy + S(30)), (cx + S(31), cy + S(10)), (cx + S(25), cy + S(10)), (cx + S(31), cy - S(12)), (cx + S(27), cy - S(24))]
    pygame.draw.lines(surf, (255, 245, 120), False, zz, max(2, S(3)))
    pygame.draw.circle(surf, WHITE, (cx + S(27), cy - S(26)), S(5))
    _robe(surf, cx, cy, S, lw, robe, 10, 19, -8, 28)
    bolt = [(cx + S(3), cy - S(4)), (cx - S(5), cy + S(8)), (cx, cy + S(8)), (cx - S(4), cy + S(22))]
    pygame.draw.lines(surf, WHITE, False, bolt, max(2, S(3)))
    _head(surf, cx, cy - S(15), S, lw)
    _eyes(surf, cx, cy - S(15), S)
    bend = [(cx - S(13), cy - S(21)), (cx + S(13), cy - S(21)), (cx + S(24), cy - S(40)), (cx + S(30), cy - S(36)), (cx + S(10), cy - S(50)), (cx - S(2), cy - S(42))]
    pygame.draw.polygon(surf, hat, bend)
    pygame.draw.polygon(surf, BLACK, bend, lw)
    pygame.draw.ellipse(surf, hat, (cx - S(19), cy - S(25), S(38), S(8)))
    pygame.draw.line(surf, acc, (cx - S(13), cy - S(26)), (cx + S(13), cy - S(26)), max(2, S(2)))


def _skin_black_hole(surf, cx, cy, S, lw, robe, hat, acc):
    sx = cx + S(27)
    _staff(surf, sx, cy + S(30), cy - S(24), S, (70, 50, 100))
    pygame.draw.circle(surf, (10, 4, 20), (sx, cy - S(32)), S(7))
    pygame.draw.circle(surf, (180, 110, 255), (sx, cy - S(32)), S(11), max(1, S(2)))
    pygame.draw.circle(surf, (180, 110, 255), (sx, cy - S(32)), S(7), 1)
    _robe(surf, cx, cy, S, lw, robe, 12, 25)
    for i in range(3):
        pygame.draw.circle(surf, (190, 130, 255), (cx, cy + S(10)), S(4 + i * 4), 1)
    hood = [(cx - S(15), cy - S(6)), (cx + S(15), cy - S(6)), (cx + S(11), cy - S(34)), (cx, cy - S(44)), (cx - S(11), cy - S(34))]
    pygame.draw.polygon(surf, hat, hood)
    pygame.draw.polygon(surf, BLACK, hood, lw)
    pygame.draw.circle(surf, (14, 8, 26), (cx, cy - S(18)), S(9))
    for k in (-1, 1):
        pygame.draw.ellipse(surf, (235, 215, 255), (cx + k * S(4) - S(2), cy - S(21), S(4), S(7)))


def _skin_dead_strong(surf, cx, cy, S, lw, robe, hat, acc):
    hx = cx + S(26)
    _staff(surf, hx, cy + S(30), cy - S(14), S, (110, 80, 50))
    pygame.draw.rect(surf, (90, 90, 100), (hx - S(10), cy - S(28), S(20), S(14)))
    pygame.draw.rect(surf, BLACK, (hx - S(10), cy - S(28), S(20), S(14)), lw)
    _robe(surf, cx, cy, S, lw, robe, 14, 24, -10, 29)
    for sgn in (-1, 1):
        pygame.draw.circle(surf, hat, (cx + sgn * S(16), cy - S(6)), S(8))
        pygame.draw.circle(surf, BLACK, (cx + sgn * S(16), cy - S(6)), S(8), lw)
    pygame.draw.line(surf, (60, 15, 20), (cx - S(12), cy + S(4)), (cx + S(12), cy + S(4)), max(2, S(3)))
    pygame.draw.line(surf, (60, 15, 20), (cx - S(14), cy + S(16)), (cx + S(14), cy + S(16)), max(2, S(3)))
    _head(surf, cx, cy - S(17), S, lw)
    _eyes(surf, cx, cy - S(17), S)
    dome = pygame.Rect(cx - S(14), cy - S(34), S(28), S(20))
    pygame.draw.ellipse(surf, hat, dome)
    pygame.draw.ellipse(surf, BLACK, dome, lw)
    for sx2 in (-8, 0, 8):
        pygame.draw.polygon(surf, (225, 225, 230), [(cx + S(sx2) - S(3), cy - S(31)), (cx + S(sx2) + S(3), cy - S(31)), (cx + S(sx2), cy - S(42))])


def _skin_string_move(surf, cx, cy, S, lw, robe, hat, acc):
    bx = cx + S(26)
    pygame.draw.arc(surf, (120, 80, 40), pygame.Rect(bx - S(10), cy - S(26), S(20), S(52)), -1.5, 1.5, max(2, S(3)))
    pygame.draw.line(surf, (235, 255, 245), (bx + S(1), cy - S(25)), (bx + S(1), cy + S(25)), 1)
    _robe(surf, cx, cy, S, lw, robe, 10, 21)
    pygame.draw.line(surf, hat, (cx - S(11), cy - S(6)), (cx + S(12), cy + S(22)), max(2, S(3)))
    _head(surf, cx, cy - S(15), S, lw)
    _eyes(surf, cx, cy - S(15), S)
    pygame.draw.polygon(surf, hat, [(cx - S(11), cy - S(15)), (cx + S(11), cy - S(15)), (cx + S(9), cy - S(28)), (cx - S(9), cy - S(28)), (cx - S(4), cy - S(36))])
    pygame.draw.polygon(surf, BLACK, [(cx - S(11), cy - S(15)), (cx - S(9), cy - S(28)), (cx - S(4), cy - S(36)), (cx + S(9), cy - S(28)), (cx + S(11), cy - S(15))], lw)
    pygame.draw.line(surf, (255, 255, 255), (cx + S(6), cy - S(27)), (cx + S(16), cy - S(40)), max(2, S(2)))
    pygame.draw.line(surf, acc, (cx + S(6), cy - S(27)), (cx + S(14), cy - S(37)), max(1, S(1)))
    pygame.draw.polygon(surf, acc, [(cx - S(10), cy - S(5)), (cx + S(10), cy - S(5)), (cx + S(7), cy + S(1)), (cx - S(7), cy + S(1))])


def _skin_fast_light(surf, cx, cy, S, lw, robe, hat, acc):
    for i in range(3):
        pygame.draw.line(surf, (190, 225, 255), (cx - S(24), cy - S(8) + i * S(12)), (cx - S(46), cy - S(8) + i * S(12)), max(1, S(2)))
    _robe(surf, cx, cy, S, lw, robe, 9, 17, -8, 28)
    pygame.draw.line(surf, hat, (cx - S(8), cy - S(4)), (cx + S(8), cy + S(24)), max(2, S(4)))
    for sgn in (-1, 1):
        pygame.draw.polygon(surf, WHITE, [(cx + sgn * S(10), cy + S(28)), (cx + sgn * S(26), cy + S(20)), (cx + sgn * S(22), cy + S(31))])
    _head(surf, cx, cy - S(15), S, lw)
    _eyes(surf, cx, cy - S(15), S)
    pygame.draw.rect(surf, hat, (cx - S(11), cy - S(23), S(22), S(5)))
    pygame.draw.polygon(surf, hat, [(cx - S(11), cy - S(22)), (cx - S(24), cy - S(26)), (cx - S(24), cy - S(18))])
    for k in (-1, 1):
        pygame.draw.circle(surf, acc, (cx + k * S(5), cy - S(25)), S(4))
        pygame.draw.circle(surf, BLACK, (cx + k * S(5), cy - S(25)), S(4), 1)


def _skin_yomatoda(surf, cx, cy, S, lw, robe, hat, acc):
    sx = cx + S(27)
    _staff(surf, sx, cy + S(30), cy - S(30), S, (90, 70, 60))
    pygame.draw.rect(surf, (60, 50, 40), (sx - S(5), cy - S(26), S(10), S(13)), border_radius=2)
    pygame.draw.rect(surf, acc, (sx - S(3), cy - S(24), S(6), S(9)), border_radius=2)
    _robe(surf, cx, cy, S, lw, robe, 12, 24)
    hood = [(cx - S(14), cy - S(6)), (cx + S(14), cy - S(6)), (cx + S(10), cy - S(30)), (cx, cy - S(40)), (cx - S(10), cy - S(30))]
    pygame.draw.polygon(surf, hat, hood)
    pygame.draw.polygon(surf, BLACK, hood, lw)
    pygame.draw.circle(surf, (225, 215, 235), (cx, cy - S(17)), S(9))
    _eyes(surf, cx, cy - S(17), S, (20, 10, 40))
    for k in range(3):
        px, py = cx - S(30) + k * S(3), cy - S(22) + k * S(15)
        pygame.draw.polygon(surf, acc, [(px, py - S(8)), (px + S(4), py), (px - S(4), py)])
        pygame.draw.circle(surf, acc, (px, py), S(4))


def _skin_sruken(surf, cx, cy, S, lw, robe, hat, acc):
    pygame.draw.line(surf, (160, 160, 175), (cx - S(18), cy + S(24)), (cx + S(16), cy - S(30)), max(2, S(3)))
    pygame.draw.line(surf, acc, (cx + S(10), cy - S(20)), (cx + S(18), cy - S(26)), max(2, S(3)))
    for i in range(2):
        pygame.draw.line(surf, acc, (cx - S(8), cy - S(18) + i * S(4)), (cx - S(30) - i * S(6), cy - S(10) + i * S(8)), max(2, S(3)))
    _robe(surf, cx, cy, S, lw, robe, 10, 19, -8, 28)
    pygame.draw.line(surf, acc, (cx - S(10), cy + S(8)), (cx + S(10), cy + S(8)), max(2, S(3)))
    _head(surf, cx, cy - S(15), S, lw, hat)
    pygame.draw.rect(surf, SKIN_TONE, (cx - S(9), cy - S(19), S(18), S(7)))
    _eyes(surf, cx, cy - S(15.5), S, (25, 25, 35), 4.2, 2.0, 1.8)
    pygame.draw.line(surf, acc, (cx - S(10), cy - S(22)), (cx + S(10), cy - S(22)), max(2, S(3)))
    for sx2 in (-6, 0, 6):
        pygame.draw.circle(surf, (200, 200, 215), (cx + S(sx2), cy + S(14)), max(1, S(2)))


def _skin_muscle(surf, cx, cy, S, lw, robe, hat, acc):
    pygame.draw.polygon(surf, robe, [(cx - S(18), cy - S(4)), (cx + S(18), cy - S(4)), (cx + S(12), cy + S(29)), (cx - S(12), cy + S(29))])
    pygame.draw.polygon(surf, BLACK, [(cx - S(18), cy - S(4)), (cx + S(18), cy - S(4)), (cx + S(12), cy + S(29)), (cx - S(12), cy + S(29))], lw)
    pygame.draw.rect(surf, hat, (cx - S(13), cy + S(18), S(26), S(8)))
    for sgn in (-1, 1):
        pygame.draw.circle(surf, robe, (cx + sgn * S(23), cy + S(2)), S(10))
        pygame.draw.circle(surf, BLACK, (cx + sgn * S(23), cy + S(2)), S(10), lw)
        pygame.draw.circle(surf, robe, (cx + sgn * S(26), cy + S(16)), S(7))
        pygame.draw.circle(surf, BLACK, (cx + sgn * S(26), cy + S(16)), S(7), lw)
    for sgn in (-1, 1):
        pygame.draw.arc(surf, hat, pygame.Rect(cx + sgn * S(7) - S(6), cy - S(2), S(12), S(10)), 3.4, 6.0, max(1, S(2)))
    _head(surf, cx, cy - S(16), S, lw, robe, 10)
    _eyes(surf, cx, cy - S(16), S)
    pygame.draw.rect(surf, (220, 60, 60), (cx - S(11), cy - S(24), S(22), S(5)))
    pygame.draw.polygon(surf, (220, 60, 60), [(cx + S(11), cy - S(23)), (cx + S(22), cy - S(18)), (cx + S(20), cy - S(27))])


def _skin_monster(surf, cx, cy, S, lw, robe, hat, acc):
    hx = cx + S(27)
    _staff(surf, hx, cy + S(30), cy - S(14), S, (120, 85, 50))
    pygame.draw.ellipse(surf, (130, 95, 55), (hx - S(8), cy - S(34), S(16), S(24)))
    pygame.draw.ellipse(surf, BLACK, (hx - S(8), cy - S(34), S(16), S(24)), lw)
    for ay, ax in ((-32, -8), (-22, 8), (-14, -8)):
        pygame.draw.polygon(surf, (235, 235, 215), [(hx + S(ax), cy + S(ay) - S(2)), (hx + S(ax), cy + S(ay) + S(2)), (hx + S(ax * 1.7), cy + S(ay))])
    _robe(surf, cx, cy, S, lw, robe, 13, 24, -9, 29)
    pygame.draw.polygon(surf, hat, [(cx - S(13), cy + S(18)), (cx + S(13), cy + S(18)), (cx + S(9), cy + S(29)), (cx - S(9), cy + S(29))])
    for sgn in (-1, 1):
        pygame.draw.polygon(surf, (235, 235, 215), [(cx + sgn * S(11), cy - S(8)), (cx + sgn * S(22), cy - S(18)), (cx + sgn * S(17), cy - S(4))])
    _head(surf, cx, cy - S(16), S, lw, robe, 11)
    _eyes(surf, cx, cy - S(17), S, (255, 235, 60), 4.8, 3.0, 2.4)
    for sgn in (-1, 1):
        pygame.draw.polygon(surf, (240, 240, 220), [(cx + sgn * S(8), cy - S(24)), (cx + sgn * S(18), cy - S(42)), (cx + sgn * S(14), cy - S(22))])
        pygame.draw.polygon(surf, BLACK, [(cx + sgn * S(8), cy - S(24)), (cx + sgn * S(18), cy - S(42)), (cx + sgn * S(14), cy - S(22))], 1)


SKIN_DRAWERS = {"badang": _skin_badang, "rez": _skin_rez, "black_hole": _skin_black_hole, "dead_strong": _skin_dead_strong,
                "string_move": _skin_string_move, "fast_light": _skin_fast_light, "yomatoda": _skin_yomatoda,
                "sruken": _skin_sruken, "muscle_skrim": _skin_muscle, "brudal_mongskter": _skin_monster}


def draw_wizard(surf, cx, cy, avatar, scale=1.0, flash=False):
    """Gambar avatar. Tiap avatar punya SKIN sendiri; wajah hanya mata tanpa pupil."""
    def S(v):
        return int(v * scale)

    robe, hat, acc = avatar["color"], avatar["hat"], avatar["accent"]
    if flash:
        robe = tuple(min(255, c + 70) for c in robe)
    fn = SKIN_DRAWERS.get(avatar.get("key"), _skin_badang)
    fn(surf, int(cx), int(cy), S, max(2, S(2)), robe, hat, acc)



class MeteorStormSkill(SpecialSkill):
    """ARCHMAGE AURELIA - Hujan Meteor Agung: meteor besar jatuh ke 10 musuh sekaligus."""
    name = "Hujan Meteor Agung"
    cooldown = 10.0

    def should_trigger(self, game):
        return crowd_near(game, 520, 3)

    def trigger(self, game):
        b = game.badang
        near = sorted([e for e in game.enemies if not e.dead and dist_sq(e.x, e.y, b.x, b.y) < 650 ** 2],
                      key=lambda e: dist_sq(e.x, e.y, b.x, b.y))[:10]
        for i, e in enumerate(near):
            game.strikes.append(PlayerStrike(e.x, e.y, 100, 80 * self.scale(game), 0.6 + 0.1 * i, (255, 150, 50), stun=1.0, kind="meteor"))
        self.effect_timer = 0.6
        game.show_toast("HUJAN METEOR AGUNG!")
        sfx("magic")

    def draw(self, surf, game):
        if self.effect_timer > 0:
            k = 1 - self.effect_timer / 0.6
            pygame.draw.circle(surf, (255, 190, 80), CENTER, int(60 + 220 * k), 4)
            for i in range(10):
                a = i * math.tau / 10 + k * 3
                pygame.draw.circle(surf, (255, 230, 150), (int(CENTER[0] + math.cos(a) * (50 + 160 * k)), int(CENTER[1] + math.sin(a) * (50 + 160 * k))), 6)


class SpearVolleySkill(SpecialSkill):
    """VALKYRIE SERA - Tombak Langit: tujuh tombak cahaya menembus barisan musuh."""
    name = "Tombak Langit"
    cooldown = 9.0
    engage_range = 650

    def __init__(self):
        super().__init__()
        self.rays = []

    def trigger(self, game):
        b = game.badang
        t = game.find_nearest_enemy()
        base = math.atan2(t.y - b.y, t.x - b.x)
        dmg = 90 * self.scale(game)
        self.rays = []
        for a in fan_angles(base, 7, 9):
            x2, y2 = b.x + math.cos(a) * 900, b.y + math.sin(a) * 900
            self.rays.append((b.x, b.y, x2, y2, a))
            for e in game.enemies:
                if not e.dead and seg_dist_sq(e.x, e.y, b.x, b.y, x2, y2) <= (e.radius + 26) ** 2:
                    game.damage_enemy(e, dmg)
        self.effect_timer = 0.4
        sfx("whoosh", 0.05)

    def draw(self, surf, game):
        if self.effect_timer > 0 and self.rays:
            cam_x, cam_y = game.get_camera()
            k = self.effect_timer / 0.4
            for (x1, y1, x2, y2, a) in self.rays:
                pygame.draw.line(surf, (255, 245, 180), (x1 - cam_x, y1 - cam_y), (x2 - cam_x, y2 - cam_y), max(2, int(8 * k)))
                px, py = x1 + (x2 - x1) * (1 - k) - cam_x, y1 + (y2 - y1) * (1 - k) - cam_y
                draw_proj_shape(surf, "spear", px, py, a, 10, (255, 245, 180), 0)


class SingularitySkill(SpecialSkill):
    """VOID EMPEROR NOX - Singularitas: lubang hitam raksasa menyedot dan menghancurkan."""
    name = "Singularitas"
    cooldown = 16.0
    radius = 430

    def __init__(self):
        super().__init__()
        self.holes = []

    def should_trigger(self, game):
        return crowd_near(game, 520, 4)

    def trigger(self, game):
        b = game.badang
        near = [e for e in game.enemies if not e.dead and dist_sq(e.x, e.y, b.x, b.y) < 600 ** 2]
        cx = sum(e.x for e in near) / len(near) if near else b.x
        cy = sum(e.y for e in near) / len(near) if near else b.y
        self.holes.append([cx, cy, 5.0, 0.0])
        game.show_toast("SINGULARITAS!")
        sfx("magic")

    def update(self, dt, game):
        super().update(dt, game)
        for h in self.holes:
            h[2] -= dt
            h[3] -= dt
            for e in game.enemies:
                if e.dead:
                    continue
                d2 = dist_sq(e.x, e.y, h[0], h[1])
                if d2 < self.radius ** 2 and not e.is_boss:
                    d = math.sqrt(d2) or 1
                    e.x += (h[0] - e.x) / d * 7 * dt * 60
                    e.y += (h[1] - e.y) / d * 7 * dt * 60
            if h[3] <= 0:
                h[3] = 0.3
                for e in game.enemies:
                    if not e.dead and dist_sq(e.x, e.y, h[0], h[1]) < self.radius ** 2:
                        game.damage_enemy(e, 24 * self.scale(game), show_text=False)
        self.holes = [h for h in self.holes if h[2] > 0]

    def draw(self, surf, game):
        cam_x, cam_y = game.get_camera()
        t = pygame.time.get_ticks() / 1000.0
        for x, y, life, _tk in self.holes:
            sx, sy = int(x - cam_x), int(y - cam_y)
            if not (-500 <= sx <= WIDTH + 500 and -500 <= sy <= HEIGHT + 500):
                continue
            R = self.radius
            pygame.draw.circle(surf, (70, 35, 120), (sx, sy), R, 1)
            for arm in range(5):
                pts = [(sx + math.cos(arm * 1.2566 + t * 3 + (26 + i * 25) * 0.03) * (26 + i * 25), sy + math.sin(arm * 1.2566 + t * 3 + (26 + i * 25) * 0.03) * (26 + i * 25) * 0.6) for i in range(15)]
                pygame.draw.lines(surf, (150, 90, 235) if arm % 2 else (95, 55, 175), False, pts, 3)
            pygame.draw.circle(surf, (4, 2, 10), (sx, sy), 38)
            pygame.draw.circle(surf, (230, 200, 255), (sx, sy), 40, 3)


class TimeStopSkill(SpecialSkill):
    """CHRONO LYRA - Henti Waktu: semua musuh membeku 4 detik."""
    name = "Henti Waktu"
    cooldown = 18.0

    def should_trigger(self, game):
        return crowd_near(game, 650, 5) or any(e.is_boss and dist_sq(e.x, e.y, game.badang.x, game.badang.y) < 700 ** 2 for e in game.enemies)

    def trigger(self, game):
        b = game.badang
        for e in game.enemies:
            if e.dead or dist_sq(e.x, e.y, b.x, b.y) > 900 ** 2:
                continue
            game.damage_enemy(e, 45 * self.scale(game), show_text=False)
            if not e.dead:
                e.frozen_timer = max(e.frozen_timer, 2.0 if e.is_boss else 4.0)
        for p in game.enemy_projectiles:
            p.alive = False
        self.effect_timer = 1.2
        game.show_toast("HENTI WAKTU!")
        sfx("magic")

    def draw(self, surf, game):
        if self.effect_timer > 0:
            k = 1 - self.effect_timer / 1.2
            r = int(80 + 700 * k)
            pygame.draw.circle(surf, (150, 220, 255), CENTER, r, 5)
            pygame.draw.circle(surf, WHITE, CENTER, max(1, int(r * 0.6)), 2)
            for i in range(12):
                a = i * math.tau / 12
                pygame.draw.line(surf, (200, 235, 255), (CENTER[0] + math.cos(a) * r * 0.85, CENTER[1] + math.sin(a) * r * 0.85),
                                 (CENTER[0] + math.cos(a) * r, CENTER[1] + math.sin(a) * r), 4)
            a = k * 12
            pygame.draw.line(surf, WHITE, CENTER, (CENTER[0] + math.cos(a) * 60, CENTER[1] + math.sin(a) * 60), 4)


class RebirthSkill(SpecialSkill):
    """PHOENIX IGNIS - Kelahiran Kembali: ledakan api, pulih 35% HP, kebal 2,5 dtk."""
    name = "Kelahiran Kembali"
    cooldown = 24.0

    def should_trigger(self, game):
        b = game.badang
        return crowd_near(game, 380, 5) or (b.hp < b.max_hp * 0.45 and crowd_near(game, 450, 2))

    def trigger(self, game):
        b = game.badang
        for e in game.enemies:
            if not e.dead and dist_sq(e.x, e.y, b.x, b.y) < 470 ** 2:
                game.damage_enemy(e, 130 * self.scale(game))
        b.hp = min(b.max_hp, b.hp + b.max_hp * 0.35)
        b.invuln_timer = max(b.invuln_timer, 2.5)
        self.effect_timer = 0.8
        game.show_toast("KELAHIRAN KEMBALI!")
        sfx("boom", 0.1)

    def draw(self, surf, game):
        if self.effect_timer > 0:
            k = 1 - self.effect_timer / 0.8
            for j in range(3):
                pygame.draw.circle(surf, [(255, 90, 30), (255, 170, 50), (255, 235, 150)][j], CENTER, max(1, int((470 - j * 60) * k)), 8 - j * 2)
            for i in range(14):
                a = i * math.tau / 14
                rr = 470 * k
                pygame.draw.polygon(surf, (255, 140, 40), [(CENTER[0] + math.cos(a - 0.1) * rr, CENTER[1] + math.sin(a - 0.1) * rr),
                                                           (CENTER[0] + math.cos(a + 0.1) * rr, CENTER[1] + math.sin(a + 0.1) * rr),
                                                           (CENTER[0] + math.cos(a) * (rr + 40), CENTER[1] + math.sin(a) * (rr + 40))])


class DragonBreathSkill(SpecialSkill):
    """DEWA NAGA RYU - Napas Naga: semburan api naga menyapu kerucut panjang selama 1,6 detik."""
    name = "Napas Naga"
    cooldown = 13.0
    engage_range = 650

    def __init__(self):
        super().__init__()
        self.active = 0.0
        self.ang = 0.0
        self.tick = 0.0

    def trigger(self, game):
        b = game.badang
        t = game.find_nearest_enemy()
        self.ang = math.atan2(t.y - b.y, t.x - b.x)
        self.active = 1.6
        game.show_toast("NAPAS NAGA!")
        sfx("boom", 0.1)

    def update(self, dt, game):
        super().update(dt, game)
        if self.active > 0:
            self.active -= dt
            self.tick -= dt
            b = game.badang
            t = game.find_nearest_enemy()
            if t is not None:
                want = math.atan2(t.y - b.y, t.x - b.x)
                self.ang += ((want - self.ang + math.pi) % math.tau - math.pi) * min(1.0, dt * 2.0)
            if self.tick <= 0:
                self.tick = 0.1
                for e in game.enemies:
                    if e.dead:
                        continue
                    dx, dy = e.x - b.x, e.y - b.y
                    d = math.hypot(dx, dy)
                    if d < 740 and abs((math.atan2(dy, dx) - self.ang + math.pi) % math.tau - math.pi) < 0.42:
                        game.damage_enemy(e, 20 * self.scale(game), show_text=False)

    def draw(self, surf, game):
        if self.active > 0:
            t = pygame.time.get_ticks() / 1000.0
            for col, wid in (((255, 90, 30), 0.42), ((255, 170, 50), 0.3), ((255, 240, 160), 0.16)):
                L = 740 * min(1.0, (1.6 - self.active) * 6 + 0.2)
                pts = [CENTER, (CENTER[0] + math.cos(self.ang - wid) * L, CENTER[1] + math.sin(self.ang - wid) * L),
                       (CENTER[0] + math.cos(self.ang) * (L + 30 + 12 * math.sin(t * 20)), CENTER[1] + math.sin(self.ang) * (L + 30 + 12 * math.sin(t * 20))),
                       (CENTER[0] + math.cos(self.ang + wid) * L, CENTER[1] + math.sin(self.ang + wid) * L)]
                pygame.draw.polygon(surf, col, pts)


def _skin_aurelia(surf, cx, cy, S, lw, robe, hat, acc):
    pygame.draw.polygon(surf, (90, 30, 130), [(cx - S(24), cy + S(30)), (cx + S(24), cy + S(30)), (cx + S(18), cy - S(8)), (cx - S(18), cy - S(8))])
    _robe(surf, cx, cy, S, lw, robe, 10, 17)
    for k in range(3):
        pygame.draw.circle(surf, GOLD_COLOR, (cx, cy + S(2 + k * 8)), max(2, S(2)))
    _head(surf, cx, cy - S(15), S, lw)
    _eyes(surf, cx, cy - S(15), S)
    cone = [(cx - S(12), cy - S(22)), (cx + S(12), cy - S(22)), (cx, cy - S(66))]
    pygame.draw.polygon(surf, hat, cone)
    pygame.draw.polygon(surf, BLACK, cone, lw)
    pygame.draw.polygon(surf, GOLD_COLOR, [(cx + S(sg * 3), cy - S(60)) for sg in (0,)] + [(cx - S(7), cy - S(70)), (cx + S(7), cy - S(70))])
    for k in range(5):
        a = k * 1.2566 - 1.57
        pygame.draw.circle(surf, acc, (int(cx + math.cos(a) * S(30)), int(cy - S(40) + math.sin(a) * S(30))), max(2, S(3)))
    sx = cx + S(28)
    _staff(surf, sx, cy + S(30), cy - S(34), S, (200, 160, 60))
    pygame.draw.polygon(surf, (255, 190, 80), [(sx, cy - S(48)), (sx + S(8), cy - S(36)), (sx, cy - S(24)), (sx - S(8), cy - S(36))])


def _skin_sera(surf, cx, cy, S, lw, robe, hat, acc):
    for sg in (-1, 1):
        pygame.draw.polygon(surf, WHITE, [(cx + sg * S(8), cy - S(10)), (cx + sg * S(40), cy - S(34)), (cx + sg * S(34), cy - S(4)), (cx + sg * S(36), cy + S(14)), (cx + sg * S(10), cy + S(8))])
        pygame.draw.polygon(surf, (190, 205, 235), [(cx + sg * S(8), cy - S(10)), (cx + sg * S(40), cy - S(34)), (cx + sg * S(34), cy - S(4)), (cx + sg * S(36), cy + S(14)), (cx + sg * S(10), cy + S(8))], 2)
    _robe(surf, cx, cy, S, lw, robe, 11, 17)
    pygame.draw.polygon(surf, (190, 200, 220), [(cx - S(12), cy - S(8)), (cx + S(12), cy - S(8)), (cx + S(9), cy + S(8)), (cx - S(9), cy + S(8))])
    pygame.draw.polygon(surf, BLACK, [(cx - S(12), cy - S(8)), (cx + S(12), cy - S(8)), (cx + S(9), cy + S(8)), (cx - S(9), cy + S(8))], lw)
    _head(surf, cx, cy - S(16), S, lw)
    _eyes(surf, cx, cy - S(16), S, (30, 90, 160))
    pygame.draw.arc(surf, (205, 212, 232), pygame.Rect(cx - S(13), cy - S(31), S(26), S(26)), 0, math.pi, max(2, S(5)))
    for sg in (-1, 1):
        pygame.draw.polygon(surf, WHITE, [(cx + sg * S(12), cy - S(22)), (cx + sg * S(26), cy - S(32)), (cx + sg * S(16), cy - S(16))])
    sx = cx - S(28)
    pygame.draw.line(surf, (140, 100, 60), (sx, cy + S(32)), (sx, cy - S(40)), max(2, S(4)))
    pygame.draw.polygon(surf, (235, 240, 250), [(sx, cy - S(54)), (sx - S(6), cy - S(38)), (sx + S(6), cy - S(38))])


def _skin_nox(surf, cx, cy, S, lw, robe, hat, acc):
    for k in range(3):
        pygame.draw.circle(surf, (120, 60, 190), (cx, cy - S(4)), S(36 - k * 6), 1)
    _robe(surf, cx, cy, S, lw, (20, 10, 34), 13, 27)
    pygame.draw.polygon(surf, (60, 20, 100), [(cx - S(27), cy + S(30)), (cx - S(34), cy - S(2)), (cx - S(14), cy - S(6))])
    pygame.draw.polygon(surf, (60, 20, 100), [(cx + S(27), cy + S(30)), (cx + S(34), cy - S(2)), (cx + S(14), cy - S(6))])
    pygame.draw.circle(surf, (4, 2, 10), (cx, cy + S(8)), S(8))
    pygame.draw.circle(surf, (190, 120, 255), (cx, cy + S(8)), S(11), 2)
    pygame.draw.circle(surf, (14, 8, 26), (cx, cy - S(16)), S(11))
    for k in (-1, 1):
        pygame.draw.ellipse(surf, (210, 150, 255), (cx + k * S(4.5) - S(2), cy - S(20), S(4), S(8)))
    crown = [(cx - S(13), cy - S(26))] + [(cx - S(13) + i * S(6.5), cy - S(26) - (S(10) if i % 2 == 0 else S(2))) for i in range(1, 5)] + [(cx + S(13), cy - S(26))]
    pygame.draw.polygon(surf, (70, 30, 120), crown)
    pygame.draw.polygon(surf, (200, 140, 255), crown, max(1, S(2)))


def _skin_lyra(surf, cx, cy, S, lw, robe, hat, acc):
    pygame.draw.circle(surf, (190, 230, 255), (cx, cy - S(10)), S(34), max(1, S(2)))
    for k in range(12):
        a = k * math.tau / 12
        pygame.draw.line(surf, WHITE, (cx + math.cos(a) * S(30), cy - S(10) + math.sin(a) * S(30)), (cx + math.cos(a) * S(34), cy - S(10) + math.sin(a) * S(34)), max(1, S(2)))
    pygame.draw.line(surf, WHITE, (cx, cy - S(10)), (cx + S(12), cy - S(22)), max(1, S(3)))
    _robe(surf, cx, cy, S, lw, robe, 9, 18, -8, 28)
    pygame.draw.circle(surf, GOLD_COLOR, (cx, cy + S(6)), S(7))
    pygame.draw.circle(surf, BLACK, (cx, cy + S(6)), S(7), 1)
    _head(surf, cx, cy - S(15), S, lw)
    _eyes(surf, cx, cy - S(15), S, (40, 90, 170))
    pygame.draw.rect(surf, hat, (cx - S(11), cy - S(26), S(22), S(7)))
    for k in (-1, 1):
        pygame.draw.circle(surf, GOLD_COLOR, (cx + k * S(14), cy - S(20)), S(5))
        pygame.draw.circle(surf, BLACK, (cx + k * S(14), cy - S(20)), S(5), 1)


def _skin_ignis(surf, cx, cy, S, lw, robe, hat, acc):
    for sg in (-1, 1):
        for j in range(4):
            pygame.draw.polygon(surf, [(255, 90, 30), (255, 150, 40), (255, 210, 90), (255, 245, 170)][j],
                                [(cx + sg * S(8), cy - S(8) + j * S(5)), (cx + sg * S(42 - j * 4), cy - S(36) + j * S(10)), (cx + sg * S(30 - j * 3), cy + S(8) + j * S(3))])
    _robe(surf, cx, cy, S, lw, robe, 10, 18)
    pygame.draw.polygon(surf, (255, 200, 80), [(cx - S(6), cy + S(4)), (cx + S(6), cy + S(4)), (cx, cy + S(24))])
    _head(surf, cx, cy - S(15), S, lw)
    _eyes(surf, cx, cy - S(15), S, (160, 30, 20))
    for k in range(5):
        ox = (k - 2) * S(5)
        pygame.draw.polygon(surf, [(255, 80, 30), (255, 130, 40), (255, 190, 60), (255, 130, 40), (255, 80, 30)][k],
                            [(cx + ox - S(4), cy - S(22)), (cx + ox + S(4), cy - S(22)), (cx + ox, cy - S(40 + (3 - abs(k - 2)) * 5))])


def _skin_ryu(surf, cx, cy, S, lw, robe, hat, acc):
    pygame.draw.polygon(surf, (30, 110, 70), [(cx + S(14), cy + S(26)), (cx + S(44), cy + S(8)), (cx + S(34), cy + S(20)), (cx + S(48), cy + S(22)), (cx + S(18), cy + S(32))])
    _robe(surf, cx, cy, S, lw, robe, 12, 22)
    for r_ in range(3):
        for c_ in range(3):
            pygame.draw.arc(surf, (20, 90, 55), pygame.Rect(cx - S(14) + c_ * S(10), cy - S(4) + r_ * S(9), S(10), S(8)), 3.14, 6.28, max(1, S(2)))
    pygame.draw.polygon(surf, (255, 210, 80), [(cx - S(14), cy - S(8)), (cx + S(14), cy - S(8)), (cx + S(10), cy), (cx - S(10), cy)])
    _head(surf, cx, cy - S(16), S, lw, (110, 200, 150), 11)
    _eyes(surf, cx, cy - S(17), S, (255, 200, 40), 4.8, 3.0, 2.4)
    for sg in (-1, 1):
        pygame.draw.polygon(surf, (245, 225, 170), [(cx + sg * S(7), cy - S(24)), (cx + sg * S(22), cy - S(48)), (cx + sg * S(14), cy - S(22))])
        pygame.draw.polygon(surf, BLACK, [(cx + sg * S(7), cy - S(24)), (cx + sg * S(22), cy - S(48)), (cx + sg * S(14), cy - S(22))], 1)
        pygame.draw.line(surf, (255, 210, 80), (cx + sg * S(8), cy - S(18)), (cx + sg * S(30), cy - S(14)), max(1, S(3)))


SKIN_DRAWERS.update({"aurelia": _skin_aurelia, "sera": _skin_sera, "nox": _skin_nox, "lyra": _skin_lyra, "ignis": _skin_ignis, "ryu": _skin_ryu})
EXTRA_AVATARS = [
    {"key": "aurelia", "name": "Archmage Aurelia", "color": (150, 60, 210), "hat": (110, 40, 170), "accent": (255, 200, 90), "hp": 170, "speed": 1.1,
     "deco": "star", "start": MeteorWeapon, "special": MeteorStormSkill, "dmg": 1.25, "price": 3750,
     "role": "Penyihir agung, mulai Meteor. Damage +25%.", "skill_name": "Hujan Meteor Agung", "skill_desc": "Meteor besar jatuh ke 10 musuh. CD 10 dtk."},
    {"key": "sera", "name": "Valkyrie Sera", "color": (225, 232, 250), "hat": (205, 212, 232), "accent": (255, 240, 170), "hp": 230, "speed": 1.15,
     "deco": "wings", "start": ShieldWeapon, "special": SpearVolleySkill, "dmg": 1.25, "price": 4800,
     "role": "Pejuang bersayap, mulai Perisai. HP besar.", "skill_name": "Tombak Langit", "skill_desc": "7 tombak cahaya menembus musuh. CD 9 dtk."},
    {"key": "nox", "name": "Void Emperor Nox", "color": (90, 40, 150), "hat": (70, 30, 120), "accent": (200, 140, 255), "hp": 190, "speed": 1.05,
     "deco": "crown", "start": BounceOrbWeapon, "special": SingularitySkill, "dmg": 1.35, "price": 6000,
     "role": "Kaisar kehampaan, mulai Bola Pantul. Damage +35%.", "skill_name": "Singularitas", "skill_desc": "Lubang hitam raksasa 5 dtk. CD 16 dtk."},
    {"key": "lyra", "name": "Chrono Lyra", "color": (120, 190, 255), "hat": (70, 130, 220), "accent": (255, 215, 90), "hp": 160, "speed": 1.3,
     "deco": "clock", "start": LaserWeapon, "special": TimeStopSkill, "dmg": 1.3, "price": 7200,
     "role": "Penjaga waktu, mulai Laser. Sangat cepat.", "skill_name": "Henti Waktu", "skill_desc": "Bekukan semua musuh 4 dtk. CD 18 dtk."},
    {"key": "ignis", "name": "Phoenix Ignis", "color": (255, 120, 50), "hat": (255, 180, 70), "accent": (255, 230, 120), "hp": 260, "speed": 1.1,
     "deco": "flame", "start": FireballWeapon, "special": RebirthSkill, "dmg": 1.4, "price": 8400,
     "role": "Burung api, mulai Bola Api. Bangkit dari abu.", "skill_name": "Kelahiran Kembali", "skill_desc": "Ledakan api, pulih 35% HP, kebal 2,5 dtk. CD 24 dtk."},
    {"key": "ryu", "name": "Dewa Naga Ryu", "color": (60, 170, 110), "hat": (30, 110, 70), "accent": (255, 210, 80), "hp": 300, "speed": 1.15,
     "deco": "dragon", "start": TornadoWeapon, "special": DragonBreathSkill, "dmg": 1.5, "price": 12000,
     "role": "Dewa naga, mulai Angin Puyuh. Damage +50%.", "skill_name": "Napas Naga", "skill_desc": "Semburan api naga 1,6 dtk. CD 13 dtk."},
]
AVATARS.extend(EXTRA_AVATARS)
AVATAR_PRICES.update({a["key"]: a["price"] for a in EXTRA_AVATARS})


# ================= AVATAR & SKILL BARU =================
def _enemies_near(game, r):
    b = game.badang
    r2 = r * r
    return [e for e in game.enemies if not e.dead and dist_sq(e.x, e.y, b.x, b.y) <= r2]


class FrostNovaSkill(SpecialSkill):
    """GLACIA - Nova Es: ledakan es membekukan semua musuh di sekitar."""
    name = "Nova Es"
    cooldown = 12.0

    def should_trigger(self, game):
        return crowd_near(game, 380, 3)

    def trigger(self, game):
        for e in _enemies_near(game, 420):
            game.damage_enemy(e, 55 * self.scale(game), show_text=False)
            if not e.dead and not e.is_boss:
                e.frozen_timer = max(e.frozen_timer, 2.2)
        self.effect_timer = 0.6
        game.show_toast("NOVA ES!")
        sfx("magic")

    def draw(self, surf, game):
        if self.effect_timer > 0:
            k = 1 - self.effect_timer / 0.6
            pygame.draw.circle(surf, (170, 230, 255), CENTER, int(40 + 380 * k), 5)
            pygame.draw.circle(surf, (230, 250, 255), CENTER, int(20 + 300 * k), 2)


class StormCallSkill(SpecialSkill):
    """ZEPHYR - Panggil Badai: petir menyambar 8 musuh acak."""
    name = "Panggil Badai"
    cooldown = 11.0
    engage_range = 700

    def __init__(self):
        super().__init__()
        self.bolts = []

    def trigger(self, game):
        near = _enemies_near(game, 760)
        random.shuffle(near)
        self.bolts = []
        for e in near[:8]:
            game.damage_enemy(e, 85 * self.scale(game))
            self.bolts.append((e.x, e.y))
        self.effect_timer = 0.35
        game.show_toast("PANGGIL BADAI!")
        sfx("magic")

    def draw(self, surf, game):
        if self.effect_timer > 0 and self.bolts:
            cam_x, cam_y = game.get_camera()
            for (x, y) in self.bolts:
                sx, sy = int(x - cam_x), int(y - cam_y)
                pts = [(sx + random.randint(-14, 14), sy - 420 + i * 70) for i in range(6)] + [(sx, sy)]
                pygame.draw.lines(surf, (255, 255, 170), False, pts, 4)
                pygame.draw.circle(surf, (255, 255, 220), (sx, sy), 22, 3)


class ToxicCloudSkill(SpecialSkill):
    """VENNA - Wabah: awan racun besar di sekitar penyihir selama 6 detik."""
    name = "Wabah"
    cooldown = 14.0

    def should_trigger(self, game):
        return crowd_near(game, 400, 3)

    def trigger(self, game):
        b = game.badang
        if len(game.poison_zones) < MAX_POISON_ZONES:
            game.poison_zones.append(PoisonZone(b.x, b.y, 260, 14 * self.scale(game), 0.4, 6.0, (110, 220, 90)))
        game.show_toast("WABAH!")
        sfx("magic")


class EarthBulwarkSkill(SpecialSkill):
    """TERRA - Benteng Bumi: kebal 3 detik dan gelombang kejut menyetrum musuh."""
    name = "Benteng Bumi"
    cooldown = 20.0

    def should_trigger(self, game):
        return crowd_near(game, 300, 4)

    def trigger(self, game):
        b = game.badang
        b.invuln_timer = max(b.invuln_timer, 3.0)
        for e in _enemies_near(game, 340):
            game.damage_enemy(e, 70 * self.scale(game), show_text=False)
            if not e.dead and not e.is_boss:
                e.frozen_timer = max(e.frozen_timer, 1.2)
        self.effect_timer = 3.0
        game.show_toast("BENTENG BUMI!")
        sfx("boom", 0.1)

    def draw(self, surf, game):
        if self.effect_timer > 0:
            pygame.draw.circle(surf, (170, 130, 80), CENTER, 70, 5)
            pygame.draw.circle(surf, (210, 175, 110), CENTER, 82, 2)


class ShadowSlashSkill(SpecialSkill):
    """KAGE - Tebasan Bayangan: tiga tebasan beruntun ke semua musuh dekat, kebal sesaat."""
    name = "Tebasan Bayangan"
    cooldown = 9.0

    def should_trigger(self, game):
        return crowd_near(game, 330, 2)

    def trigger(self, game):
        b = game.badang
        b.invuln_timer = max(b.invuln_timer, 0.9)
        for e in _enemies_near(game, 340):
            for _ in range(3):
                if not e.dead:
                    game.damage_enemy(e, 38 * self.scale(game), show_text=False)
        self.effect_timer = 0.35
        sfx("whoosh", 0.05)

    def draw(self, surf, game):
        if self.effect_timer > 0:
            for i in range(3):
                a = i * 2.1 + self.effect_timer * 8
                pygame.draw.line(surf, (200, 160, 255), (CENTER[0] + math.cos(a) * 320, CENTER[1] + math.sin(a) * 320),
                                 (CENTER[0] - math.cos(a) * 320, CENTER[1] - math.sin(a) * 320), 4)


class HolyLightSkill(SpecialSkill):
    """LUMI - Cahaya Suci: pulihkan 25% HP dan lukai musuh sekitar."""
    name = "Cahaya Suci"
    cooldown = 20.0

    def should_trigger(self, game):
        b = game.badang
        return b.hp < b.max_hp * 0.75 and crowd_near(game, 450, 1)

    def trigger(self, game):
        b = game.badang
        b.hp = min(b.max_hp, b.hp + b.max_hp * 0.25)
        for e in _enemies_near(game, 400):
            game.damage_enemy(e, 60 * self.scale(game), show_text=False)
        self.effect_timer = 0.7
        game.show_toast("CAHAYA SUCI!")
        sfx("magic")

    def draw(self, surf, game):
        if self.effect_timer > 0:
            k = 1 - self.effect_timer / 0.7
            pygame.draw.circle(surf, (255, 250, 190), CENTER, int(30 + 380 * k), 6)


class ChainBlastSkill(SpecialSkill):
    """PYRA - Ledakan Beruntun: enam ledakan jatuh bergantian ke musuh terdekat."""
    name = "Ledakan Beruntun"
    cooldown = 10.0
    engage_range = 650

    def trigger(self, game):
        near = sorted(_enemies_near(game, 700), key=lambda e: dist_sq(e.x, e.y, game.badang.x, game.badang.y))[:6]
        for i, e in enumerate(near):
            game.strikes.append(PlayerStrike(e.x, e.y, 90, 75 * self.scale(game), 0.3 + 0.2 * i, (255, 130, 40), kind="meteor"))
        self.effect_timer = 0.4
        game.show_toast("LEDAKAN BERUNTUN!")
        sfx("boom", 0.1)


class SoulDrainSkill(SpecialSkill):
    """MORTA - Sedot Jiwa: melukai semua musuh dalam jangkauan dan memulihkan HP per musuh."""
    name = "Sedot Jiwa"
    cooldown = 15.0

    def should_trigger(self, game):
        return crowd_near(game, 450, 3)

    def trigger(self, game):
        b = game.badang
        n = 0
        for e in _enemies_near(game, 500):
            game.damage_enemy(e, 65 * self.scale(game), show_text=False)
            n += 1
        b.hp = min(b.max_hp, b.hp + min(b.max_hp * 0.3, n * b.max_hp * 0.02))
        self.effect_timer = 0.6
        game.show_toast("SEDOT JIWA!")
        sfx("magic")

    def draw(self, surf, game):
        if self.effect_timer > 0:
            k = self.effect_timer / 0.6
            pygame.draw.circle(surf, (120, 255, 160), CENTER, int(60 + 440 * k), 4)


def _make_skin(deco):
    def fn(surf, cx, cy, S, lw, robe, hat, acc):
        P = pygame.draw
        _robe(surf, cx, cy, S, lw, robe, 10, 19)
        _head(surf, cx, cy - S(15), S, lw)
        _eyes(surf, cx, cy - S(15), S)
        if deco in ("snow", "storm", "leaf", "holy", "skull"):
            cone = [(cx - S(12), cy - S(22)), (cx + S(12), cy - S(22)), (cx, cy - S(64))]
            P.polygon(surf, hat, cone)
            P.polygon(surf, BLACK, cone, lw)
        elif deco == "ninja":
            P.rect(surf, hat, (cx - S(11), cy - S(25), S(22), S(9)))
            P.line(surf, acc, (cx + S(11), cy - S(21)), (cx + S(26), cy - S(14)), max(2, S(3)))
        elif deco == "earth":
            P.rect(surf, hat, (cx - S(13), cy - S(30), S(26), S(12)))
            P.rect(surf, BLACK, (cx - S(13), cy - S(30), S(26), S(12)), lw)
        elif deco == "bomb":
            P.circle(surf, hat, (cx, cy - S(28)), S(12))
            P.line(surf, acc, (cx, cy - S(40)), (cx + S(6), cy - S(50)), max(2, S(2)))
            P.circle(surf, acc, (cx + S(6), cy - S(52)), S(4))
        if deco == "snow":
            for k in range(6):
                a = k * math.tau / 6
                P.line(surf, acc, (cx + math.cos(a) * S(30), cy - S(10) + math.sin(a) * S(30)), (cx + math.cos(a) * S(38), cy - S(10) + math.sin(a) * S(38)), max(2, S(2)))
        elif deco == "storm":
            pts = [(cx + S(26), cy - S(20)), (cx + S(18), cy - S(4)), (cx + S(24), cy - S(4)), (cx + S(16), cy + S(14))]
            P.lines(surf, acc, False, pts, max(2, S(3)))
        elif deco == "leaf":
            for sg in (-1, 1):
                P.ellipse(surf, acc, (cx + sg * S(22) - S(6), cy - S(2), S(12), S(20)))
        elif deco == "holy":
            P.circle(surf, acc, (cx, cy - S(70)), S(9), max(2, S(2)))
        elif deco == "skull":
            P.circle(surf, acc, (cx, cy + S(2)), S(6))
            P.rect(surf, acc, (cx - S(3), cy + S(6), S(6), S(4)))
        elif deco == "earth":
            for sg in (-1, 1):
                P.circle(surf, acc, (cx + sg * S(22), cy - S(4)), S(7))
                P.circle(surf, BLACK, (cx + sg * S(22), cy - S(4)), S(7), 1)
    return fn


SKIN_DRAWERS.update({k: _make_skin(d) for k, d in (("glacia", "snow"), ("zephyr", "storm"), ("venna", "leaf"), ("terra", "earth"),
                                                    ("kage", "ninja"), ("lumi", "holy"), ("pyra", "bomb"), ("morta", "skull"))})

NEW_AVATARS = [
    {"key": "glacia", "name": "Ratu Es Glacia", "color": (140, 200, 245), "hat": (90, 150, 215), "accent": (235, 250, 255), "hp": 150, "speed": 1.05,
     "deco": "snow", "start": IceSpikeWeapon, "special": FrostNovaSkill, "dmg": 1.2, "price": 5200,
     "role": "Ratu es, mulai Duri Es. Pembeku massal.", "skill_name": "Nova Es", "skill_desc": "Bekukan musuh sekitar 2,2 dtk. CD 12 dtk."},
    {"key": "zephyr", "name": "Zephyr Badai", "color": (255, 235, 110), "hat": (200, 170, 40), "accent": (255, 255, 200), "hp": 140, "speed": 1.25,
     "deco": "storm", "start": SkyLightningWeapon, "special": StormCallSkill, "dmg": 1.25, "price": 5800,
     "role": "Penyihir badai, mulai Kilat Langit. Gesit.", "skill_name": "Panggil Badai", "skill_desc": "Petir menyambar 8 musuh acak. CD 11 dtk."},
    {"key": "venna", "name": "Tabib Racun Venna", "color": (90, 190, 90), "hat": (50, 130, 60), "accent": (190, 255, 130), "hp": 160, "speed": 1.05,
     "deco": "leaf", "start": PoisonCloudWeapon, "special": ToxicCloudSkill, "dmg": 1.2, "price": 4400,
     "role": "Ahli racun, mulai Awan Racun.", "skill_name": "Wabah", "skill_desc": "Awan racun besar 6 dtk. CD 14 dtk."},
    {"key": "terra", "name": "Penjaga Terra", "color": (170, 130, 80), "hat": (120, 90, 50), "accent": (240, 210, 140), "hp": 290, "speed": 0.95,
     "deco": "earth", "start": GroundSpikeWeapon, "special": EarthBulwarkSkill, "dmg": 1.1, "price": 6600,
     "role": "Penjaga bumi, mulai Duri Bumi. HP sangat besar.", "skill_name": "Benteng Bumi", "skill_desc": "Kebal 3 dtk + kejut. CD 20 dtk."},
    {"key": "kage", "name": "Bayangan Kage", "color": (60, 50, 90), "hat": (30, 25, 55), "accent": (200, 160, 255), "hp": 110, "speed": 1.35,
     "deco": "ninja", "start": KnifeWeapon, "special": ShadowSlashSkill, "dmg": 1.3, "price": 7000,
     "role": "Pembunuh senyap, mulai Pisau. Sangat cepat.", "skill_name": "Tebasan Bayangan", "skill_desc": "3 tebasan beruntun + kebal. CD 9 dtk."},
    {"key": "lumi", "name": "Pendeta Lumi", "color": (255, 245, 210), "hat": (240, 220, 150), "accent": (255, 215, 90), "hp": 200, "speed": 1.05,
     "deco": "holy", "start": HomingSpiritWeapon, "special": HolyLightSkill, "dmg": 1.15, "price": 5600,
     "role": "Pendeta suci, mulai Roh Pengejar.", "skill_name": "Cahaya Suci", "skill_desc": "Pulihkan 25% HP + lukai musuh. CD 20 dtk."},
    {"key": "pyra", "name": "Pyra Peledak", "color": (255, 110, 60), "hat": (170, 50, 30), "accent": (255, 220, 90), "hp": 170, "speed": 1.1,
     "deco": "bomb", "start": MeteorWeapon, "special": ChainBlastSkill, "dmg": 1.3, "price": 8000,
     "role": "Ahli ledakan, mulai Meteor.", "skill_name": "Ledakan Beruntun", "skill_desc": "6 ledakan beruntun. CD 10 dtk."},
    {"key": "morta", "name": "Necromancer Morta", "color": (50, 90, 70), "hat": (25, 55, 40), "accent": (140, 255, 170), "hp": 220, "speed": 1.0,
     "deco": "skull", "start": OrbWeapon, "special": SoulDrainSkill, "dmg": 1.4, "price": 9500,
     "role": "Pemanggil arwah, mulai Bola Energi.", "skill_name": "Sedot Jiwa", "skill_desc": "Lukai musuh & pulihkan HP. CD 15 dtk."},
]
AVATARS.extend(NEW_AVATARS)
AVATAR_PRICES.update({a["key"]: a["price"] for a in NEW_AVATARS})


_WIZ = {}


def _wiz_entry(avatar, scale=1.0, flash=False):
    key = (avatar.get("key"), round(scale, 2), flash)
    ent = _WIZ.get(key)
    if ent is None:
        h = int(82 * scale) + 8
        sp = pygame.Surface((2 * h, 2 * h), pygame.SRCALPHA)
        draw_wizard(sp, h, h, avatar, scale, flash)
        try:
            sp = sp.convert_alpha()
        except Exception:
            pass
        ent = _WIZ[key] = (sp, h)
    return ent


def draw_wizard_cached(surf, cx, cy, avatar, scale=1.0, flash=False):
    """Avatar dari sprite hasil cache (1 blit, bukan ~30 draw call) - dipakai di menu/loading/judul."""
    ent = _wiz_entry(avatar, scale, flash)
    surf.blit(ent[0], (int(cx) - ent[1], int(cy) - ent[1]))


MERCHANT_SKINS = [
    {"turban": (200, 60, 60), "vest": (60, 120, 170), "robe": (230, 200, 120), "gem": (90, 230, 255)},
    {"turban": (60, 150, 90), "vest": (170, 90, 40), "robe": (235, 225, 190), "gem": (255, 120, 200)},
    {"turban": (230, 190, 60), "vest": (110, 60, 140), "robe": (210, 170, 130), "gem": (255, 90, 90)},
]


_MERCH_SPR = {}


def _merchant_sprite(skin, scale):
    """Badan pedagang digambar SEKALI ke sprite (dulu ~25 draw call tiap frame), pada skala yang sama dengan pemain."""
    key = (skin % len(MERCHANT_SKINS), round(scale, 3))
    ent = _MERCH_SPR.get(key)
    if ent is None:
        sk = MERCHANT_SKINS[skin % len(MERCHANT_SKINS)]

        def S(v):
            return int(round(v * scale))

        def W(v):
            return max(1, int(round(v * scale)))

        h = S(44) + 6
        sp = pygame.Surface((2 * h, 2 * h), pygame.SRCALPHA)
        cx = cy = h
        pack = (cx - S(34), cy - S(18), S(20), S(38))
        pygame.draw.rect(sp, (120, 80, 45), pack, border_radius=S(6))
        pygame.draw.rect(sp, BLACK, pack, W(2), border_radius=S(6))
        pygame.draw.circle(sp, (230, 170, 70), (cx - S(28), cy - S(22)), S(7))
        pygame.draw.polygon(sp, sk["robe"], [(cx - S(20), cy + S(28)), (cx + S(20), cy + S(28)), (cx + S(12), cy - S(8)), (cx - S(12), cy - S(8))])
        pygame.draw.polygon(sp, sk["vest"], [(cx - S(12), cy - S(8)), (cx - S(3), cy - S(8)), (cx - S(6), cy + S(28)), (cx - S(18), cy + S(28))])
        pygame.draw.polygon(sp, sk["vest"], [(cx + S(12), cy - S(8)), (cx + S(3), cy - S(8)), (cx + S(6), cy + S(28)), (cx + S(18), cy + S(28))])
        pygame.draw.line(sp, GOLD_COLOR, (cx - S(14), cy + S(12)), (cx + S(14), cy + S(12)), W(3))
        pygame.draw.circle(sp, SKIN_TONE, (cx, cy - S(15)), S(10))
        pygame.draw.circle(sp, BLACK, (cx, cy - S(15)), S(10), W(2))
        for k in (-1, 1):
            pygame.draw.ellipse(sp, (25, 25, 35), (cx + k * S(4) - S(2), cy - S(18), max(2, S(4)), max(3, S(7))))
        pygame.draw.ellipse(sp, sk["turban"], (cx - S(13), cy - S(32), S(26), S(16)))
        pygame.draw.ellipse(sp, BLACK, (cx - S(13), cy - S(32), S(26), S(16)), W(2))
        pygame.draw.arc(sp, WHITE, pygame.Rect(cx - S(11), cy - S(30), S(22), S(12)), 0.3, 2.8, W(2))
        pygame.draw.circle(sp, sk["gem"], (cx, cy - S(25)), max(2, S(4)))
        try:
            sp = sp.convert_alpha()
        except Exception:
            pass
        ent = _MERCH_SPR[key] = (sp, h)
    return ent


def draw_merchant_char(surf, ix, iy, skin=0, t=0.0, scale=PLAYER_SCALE):
    """Pedagang: serban + rompi + ransel + lentera (ukuran sama dengan penyihir pemain). Mata tanpa pupil, tanpa mulut."""
    sp, h = _merchant_sprite(skin, scale)
    surf.blit(sp, (ix - h, iy - h))
    lx, ly = ix + int(round(28 * scale)), iy + int(round(6 * scale)) + int(math.sin(t * 3) * 2 * scale)
    pygame.draw.line(surf, (110, 85, 55), (lx, ly - int(26 * scale)), (lx, ly - int(6 * scale)), max(1, int(2 * scale)))
    pygame.draw.rect(surf, (70, 55, 40), (lx - int(6 * scale), ly - int(8 * scale), max(4, int(12 * scale)), max(5, int(16 * scale))), border_radius=2)
    pygame.draw.rect(surf, (255, 225, 120), (lx - int(4 * scale), ly - int(6 * scale), max(3, int(8 * scale)), max(4, int(12 * scale))), border_radius=1)


class Badang:
    def all_weapons(self):
        """Semua senjata aktif termasuk yang sudah difusikan (tersimpan di dalam senjata utama)."""
        out = []
        for w in self.weapons:
            out.append(w)
            out.extend(getattr(w, "inner", ()))
        return out

    """Pemain (penyihir). Nama kelas dipertahankan; avatar menentukan statnya."""

    def __init__(self, avatar=None):
        avatar = avatar or AVATARS[0]
        self.avatar = avatar
        self.x = 0.0
        self.y = 0.0
        self.size = max(12, int(26 * PLAYER_SCALE))
        self.speed = BADANG_BASE_SPEED * avatar["speed"]
        self.speed_buff = 1.0
        self.max_hp = avatar["hp"]
        self.hp = self.max_hp
        self.level = 1
        self.xp = 0
        self.xp_needed = 10

        self.weapons = [avatar["start"](level=1)]
        self.fusions = 0
        self.pickup_radius = 55
        self.regen = 0.0
        self.facing = (1.0, 0.0)
        self.special = avatar["special"]()

        self.punch_flash = 0.0
        self.punch_range_visual = 70
        self.invuln_timer = 0.0
        self.hit_events = []
        self.dr_weapon = 0.0
        self.dr_skill = 0.0
        self.draw_scale = 1.0
        self.kb_vx = 0.0
        self.kb_vy = 0.0
        self.kb_timer = 0.0
        self.slow_t = 0.0
        self.dr_shop = 0.0
        self.xp_gain_mult = 1.0
        self.burn_t = 0.0
        self.burn_dps = 0.0
        self.poison_t = 0.0
        self.poison_dps = 0.0
        self._dot_tick = 0.0
        self.dot_events = []

    def set_burn(self, dps, dur=2.5):
        if in_merchant_shield(self.x, self.y):
            return
        self.burn_t = max(self.burn_t, dur)
        self.burn_dps = max(self.burn_dps, dps)

    def set_poison(self, dps, dur=3.5):
        if in_merchant_shield(self.x, self.y):
            return
        self.poison_t = max(self.poison_t, dur)
        self.poison_dps = max(self.poison_dps, dps)

    def clear_statuses(self):
        self.burn_t = self.poison_t = 0.0
        self.burn_dps = self.poison_dps = 0.0

    def update_statuses(self, dt, game):
        """Damage berkala bakar/racun pada pemain (tidak memicu invuln/suara sakit tiap tick)."""
        if self.burn_t <= 0 and self.poison_t <= 0:
            return
        if self.burn_t > 0:
            self.burn_t -= dt
        if self.poison_t > 0:
            self.poison_t -= dt
        if in_merchant_shield(self.x, self.y):
            self.burn_t = self.poison_t = 0.0
            return
        self._dot_tick -= dt
        if self._dot_tick > 0:
            return
        self._dot_tick = 0.5
        red = 1.0 - min(0.8, self.dr_weapon + self.dr_skill + self.dr_shop)
        for kind, on, dps in (("burn", self.burn_t > -0.0 and self.burn_dps > 0, self.burn_dps),
                              ("poison", self.poison_dps > 0, self.poison_dps)):
            active = (self.burn_t > 0) if kind == "burn" else (self.poison_t > 0)
            if on and active:
                amt = max(1.0, dps * 0.5) * red
                self.hp -= amt
                self.dot_events.append((amt, kind))
        if self.burn_t <= 0:
            self.burn_dps = 0.0
        if self.poison_t <= 0:
            self.poison_dps = 0.0

    def apply_knockback(self, dx, dy, force):
        d = math.hypot(dx, dy) or 1.0
        self.kb_vx, self.kb_vy = dx / d * force, dy / d * force
        self.kb_timer = 0.35

    def move(self, vec, dt):
        mag = math.hypot(vec[0], vec[1])
        if mag > 0.001:
            nx, ny = vec[0] / mag, vec[1] / mag
            if mag > 0.15:
                self.facing = (nx, ny)
            speed_scale = min(mag, 1.0)
            sl = 0.55 if self.slow_t > 0 else 1.0
            self.x += nx * self.speed * self.speed_buff * speed_scale * sl * dt * 60
            self.y += ny * self.speed * self.speed_buff * speed_scale * sl * dt * 60

    def gain_xp(self, amount):
        if self.level >= MAX_PLAYER_LEVEL:
            return False
        amt = amount * XP_GAIN_MULT * self.xp_gain_mult + getattr(self, "xp_frac", 0.0)
        whole = int(amt)
        self.xp_frac = amt - whole
        self.xp += whole
        leveled = False
        while self.xp >= self.xp_needed:
            self.xp -= self.xp_needed
            self.level += 1
            self.max_hp += HP_PER_LEVEL
            self.hp = min(self.max_hp, self.hp + HP_PER_LEVEL)
            self.xp_needed = int(self.xp_needed * 1.28) + 12 if self.level < 25 else int(self.xp_needed * 1.035) + 40
            leveled = True
        return leveled

    def take_damage(self, amount):
        if in_merchant_shield(self.x, self.y):
            return False
        if self.invuln_timer <= 0:
            amount *= 1.0 - min(0.8, self.dr_weapon + self.dr_skill + self.dr_shop)
            self.hp -= amount
            self.invuln_timer = 0.5
            self.hit_events.append(amount)
            return True
        return False

    def has_weapon(self, cls):
        return any(isinstance(w, cls) for w in self.all_weapons())

    def fusable(self):
        """Sihir yang boleh difusikan (senjata fusi tidak bisa difusikan lagi)."""
        return [w for w in self.weapons if not isinstance(w, FusionWeapon)]

    def can_fuse(self):
        return self.fusions < MAX_FUSIONS and len(self.fusable()) >= 2

    def fuse(self, w1, w2):
        """FUSI: dua sihir DIHAPUS dan diganti satu SENJATA FUSI baru. Slot terbuka satu. Mengembalikan senjata baru."""
        if w1 is w2 or w1 not in self.weapons or w2 not in self.weapons or self.fusions >= MAX_FUSIONS:
            return None
        if isinstance(w1, FusionWeapon) or isinstance(w2, FusionWeapon):
            return None
        new = FusionWeapon(level=min(MAX_WEAPON_LEVEL, max(w1.level, w2.level)), a=type(w1).__name__, b=type(w2).__name__)
        pos = min(self.weapons.index(w1), self.weapons.index(w2))
        self.weapons = [w for w in self.weapons if w is not w1 and w is not w2]
        self.weapons.insert(min(pos, len(self.weapons)), new)
        self.fusions += 1
        return new

    def refresh_evolutions(self):
        """EVOLUSI: sihir yang mencapai Lv.5 DIGANTI (sihir lama dihapus) oleh sihir evolusinya."""
        for i, w in enumerate(self.weapons):
            if w.evolved and not w.evo_form and not isinstance(w, FusionWeapon):
                self.weapons[i] = evolved_form(w)

    def update(self, dt):
        if self.slow_t > 0:
            self.slow_t -= dt
        if self.kb_timer > 0:
            self.kb_timer -= dt
            self.x += self.kb_vx * dt * 60
            self.y += self.kb_vy * dt * 60
            self.kb_vx *= 0.88
            self.kb_vy *= 0.88
        if self.invuln_timer > 0:
            self.invuln_timer -= dt
        if self.punch_flash > 0:
            self.punch_flash -= dt
        if self.regen > 0 and self.hp < self.max_hp:
            self.hp = min(self.max_hp, self.hp + self.regen * dt)

    def draw(self, surf, game):
        for w in self.all_weapons():
            if isinstance(w, AuraWeapon):
                w.draw(surf, game)

        flash = self.invuln_timer > 0 and int(self.invuln_timer * 20) % 2 == 0
        draw_wizard(surf, int(CENTER[0]), int(CENTER[1]), self.avatar, self.draw_scale * PLAYER_SCALE, flash)
        if self.poison_t > 0 or self.burn_t > 0:
            _t = pygame.time.get_ticks() / 1000.0
            _cx, _cy, _r = int(CENTER[0]), int(CENTER[1]), max(14, int(self.size * 0.9))
            if self.poison_t > 0:
                draw_poison_fx(surf, _cx, _cy, _r, _t, 1.3)
            if self.burn_t > 0:
                draw_burn_fx(surf, _cx, _cy, _r, _t, 0.7)

        fx, fy = self.facing
        tip = (CENTER[0] + fx * (self.size + 12), CENTER[1] + fy * (self.size + 12))
        pygame.draw.circle(surf, GOLD_COLOR, (int(tip[0]), int(tip[1])), 3)

        for w in self.all_weapons():
            if not isinstance(w, AuraWeapon):
                w.draw(surf, game)

        self.special.draw(surf, game)

        label = font_small.render(self.avatar["name"], True, WHITE)
        surf.blit(label, (CENTER[0] - label.get_width() / 2, CENTER[1] - int(78 * PLAYER_SCALE) - 6))



def _dk(c, f=0.5):
    return (int(c[0] * f), int(c[1] * f), int(c[2] * f))


def _lt(c, f=0.5):
    return (int(c[0] + (255 - c[0]) * f), int(c[1] + (255 - c[1]) * f), int(c[2] + (255 - c[2]) * f))


_ARMOR_STYLES = 7


def draw_armor_plates(surf, ix, iy, r, name, dark_body):
    """Armor FISIK (pelat, helm, duri, cangkang...). Gaya berbeda tiap jenis musuh (dipilih dari nama)."""
    h = zlib.crc32(name.encode("utf-8"))
    styles = [h % _ARMOR_STYLES]
    if r >= 26:
        styles.append((h // 7 + 3) % _ARMOR_STYLES)
    steel = (176, 182, 198) if dark_body else (140, 146, 162)
    edge = (40, 45, 60)
    trim = (230, 195, 90)
    lw = 2 if r < 30 else 3
    for st in dict.fromkeys(styles):
        if st == 0:
            for sg in (-1, 1):
                pts = [(ix + sg * r * 0.55, iy - r * 0.62), (ix + sg * r * 1.08, iy - r * 0.45), (ix + sg * r * 1.0, iy - r * 0.05), (ix + sg * r * 0.5, iy - r * 0.2)]
                pygame.draw.polygon(surf, steel, pts)
                pygame.draw.polygon(surf, edge, pts, lw)
                pygame.draw.line(surf, trim, pts[0], pts[2], 1)
        elif st == 1:
            pts = [(ix - r * 0.78, iy - r * 0.32), (ix - r * 0.6, iy - r * 0.8), (ix, iy - r * 1.02), (ix + r * 0.6, iy - r * 0.8), (ix + r * 0.78, iy - r * 0.32), (ix, iy - r * 0.5)]
            pygame.draw.polygon(surf, steel, pts)
            pygame.draw.polygon(surf, edge, pts, lw)
            pygame.draw.polygon(surf, trim, [(ix - r * 0.07, iy - r * 1.02), (ix + r * 0.07, iy - r * 1.02), (ix, iy - r * 1.32)])
        elif st == 2:
            pl = pygame.Rect(ix - r * 0.52, iy + r * 0.12, r * 1.04, r * 0.62)
            pygame.draw.rect(surf, steel, pl, border_radius=int(r * 0.14))
            pygame.draw.rect(surf, edge, pl, lw, border_radius=int(r * 0.14))
            pygame.draw.line(surf, edge, (ix, pl.y), (ix, pl.bottom), 2)
            for ax_ in (-0.38, 0.38):
                pygame.draw.circle(surf, trim, (int(ix + ax_ * r), int(pl.y + r * 0.12)), max(1, int(r * 0.05)))
        elif st == 3:
            for k in range(7):
                a = -math.pi + 0.35 + k * (math.pi - 0.7) / 6
                pygame.draw.polygon(surf, steel, [(ix + math.cos(a - 0.14) * r * 0.9, iy + math.sin(a - 0.14) * r * 0.9),
                                                  (ix + math.cos(a + 0.14) * r * 0.9, iy + math.sin(a + 0.14) * r * 0.9),
                                                  (ix + math.cos(a) * r * 1.3, iy + math.sin(a) * r * 1.3)])
        elif st == 4:
            for k in range(3):
                seg = pygame.Rect(ix - r * (0.82 - k * 0.08), iy + r * (0.18 + k * 0.2), r * (1.64 - k * 0.16), r * 0.2)
                pygame.draw.rect(surf, steel, seg, border_radius=int(r * 0.09))
                pygame.draw.rect(surf, edge, seg, 2, border_radius=int(r * 0.09))
        elif st == 5:
            pygame.draw.rect(surf, steel, (ix - r * 0.72, iy + r * 0.52, r * 1.44, r * 0.26), border_radius=int(r * 0.1))
            pygame.draw.rect(surf, edge, (ix - r * 0.72, iy + r * 0.52, r * 1.44, r * 0.26), 2, border_radius=int(r * 0.1))
            for sg in (-1, 1):
                pygame.draw.polygon(surf, steel, [(ix + sg * r * 0.78, iy - r * 0.1), (ix + sg * r * 0.98, iy + r * 0.1), (ix + sg * r * 0.7, iy + r * 0.42)])
        else:
            for sg in (-1, 1):
                pl = pygame.Rect(ix + sg * r * 1.0 - r * 0.2, iy - r * 0.08, r * 0.4, r * 0.7)
                pygame.draw.rect(surf, steel, pl, border_radius=int(r * 0.12))
                pygame.draw.rect(surf, edge, pl, lw, border_radius=int(r * 0.12))
                pygame.draw.line(surf, trim, (pl.x + 2, pl.y + r * 0.25), (pl.right - 2, pl.y + r * 0.25), 1)


_SPRITES = {}
SPRITE_GEARS = set()   # gear beranimasi/berputar digambar langsung tiap frame (bukan sprite 4 frame) supaya berputar penuh 360 derajat
HAZ_LOD = False
ROBOT_MODE = False
FACE_DETAIL = True


_EYE_SPR = {}
_FACE_REC = None


def _eye_sprite(r, style, red, lb):
    """Sepasang mata (tanpa pupil) yang bergeser ke arah pandang (16 arah). Anchor = pusat wajah."""
    key = (r, style, red, lb)
    ent = _EYE_SPR.get(key)
    if ent is None:
        if len(_EYE_SPR) > 1800:
            _trim(_EYE_SPR, 1300)
        a = lb * math.tau / 16.0
        fx, fy = math.cos(a), math.sin(a)
        er = max(2, int(r * 0.2))
        W, H = int(r * 1.0) + er + 4, int(r * 0.5) + er * 2 + 4
        spr = pygame.Surface((W * 2, H * 2), pygame.SRCALPHA)
        shx, shy = fx * r * 0.14 + fx * er * 0.3, fy * r * 0.10
        for k in (-1, 1):
            wide = 1.0 + 0.14 * k * fx
            ew = max(2, int(er * wide))
            px, py = int(W + k * r * 0.36 + shx), int(H - r * 0.1 + shy)
            rect = (px - ew, py - int(er * 1.2), ew * 2, int(er * 2.4))
            if style == "ninja":
                pygame.draw.line(spr, WHITE, (int(W + k * r * 0.2 + shx), int(H + shy - 3 + r * 0.1)), (int(W + k * r * 0.55 + shx), int(H + shy - 6 + r * 0.1)), 2)
            elif style == "skull":
                pygame.draw.ellipse(spr, (16, 16, 22), rect)
            elif style == "ghost":
                pygame.draw.ellipse(spr, (25, 30, 48), (px - ew, py - int(er * 1.3), ew * 2, int(er * 2.6)))
            else:
                pygame.draw.ellipse(spr, WHITE, rect)
                pygame.draw.ellipse(spr, (255, 90, 80) if red else BLACK, rect, 1)
        try:
            spr = spr.convert_alpha()
        except Exception:
            pass
        ent = _EYE_SPR[key] = (spr, W, H)
    return ent


def draw_face(surf, cx, cy, r, look=0.0, style="angry", mood=0.0, t=0.0):
    """Wajah musuh/boss: HANYA sepasang mata tanpa pupil (tanpa mulut dan alis). Mata melihat ke arah `look` (pemain)."""
    if r < 5:
        return
    if _FACE_REC is not None:
        _FACE_REC.append(("face", cx, cy, r, style, mood))
        return
    lb = int(((look % math.tau) / math.tau) * 16 + 0.5) % 16
    spr, W, H = _eye_sprite(int(r), style, mood > 0.6, lb)
    surf.blit(spr, (int(cx) - W, int(cy) - H))


def draw_led_pair(surf, cx, cy, sep, w, h, led, look, r, flick=1.0):
    """LED mata robot (tanpa pupil) yang bergeser ke arah pemain."""
    if _FACE_REC is not None:
        _FACE_REC.append(("led", cx, cy, sep, w, h, led, r))
        return
    dx, dy = math.cos(look) * r * 0.1, math.sin(look) * r * 0.06
    col = tuple(int(c * flick) for c in led)
    for sg in (-1, 1):
        pygame.draw.rect(surf, col, (cx + sg * sep - w / 2 + dx, cy - h / 2 + dy, w, h), border_radius=2)


def replay_faces(surf, faces, ix, iy, look, t):
    for f in faces:
        if f[0] == "face":
            draw_face(surf, ix + f[1], iy + f[2], f[3], look, f[4], f[5], t)
        else:
            draw_led_pair(surf, ix + f[1], iy + f[2], f[3], f[4], f[5], f[6], look, f[7], 0.75 + 0.25 * math.sin(t * 9))


def draw_proj_shape(surf, style, sx, sy, ang, r, color, t=0.0):
    """Bentuk proyektil: anak panah, pisau, kristal es, bola api, roh, shuriken, batu."""
    ix, iy = int(sx), int(sy)
    c, sn = math.cos(ang), math.sin(ang)
    if style == "arrow":
        L = 14 + r
        tail = (sx - c * L, sy - sn * L)
        neck = (sx + c * L * 0.55, sy + sn * L * 0.55)
        pygame.draw.line(surf, (150, 105, 55), tail, neck, 3)
        tip = (sx + c * (L * 0.55 + 10), sy + sn * (L * 0.55 + 10))
        pygame.draw.polygon(surf, (215, 220, 230), [tip, (neck[0] - sn * 4, neck[1] + c * 4),
                                                    (neck[0] + sn * 4, neck[1] - c * 4)])
        for off in (0, 5):
            b = (sx - c * (L - off), sy - sn * (L - off))
            pygame.draw.line(surf, color, b, (b[0] - c * 5 - sn * 5, b[1] - sn * 5 + c * 5), 2)
            pygame.draw.line(surf, color, b, (b[0] - c * 5 + sn * 5, b[1] - sn * 5 - c * 5), 2)
        return
    if style == "knife":
        k = max(0.8, r / 6.0)
        blade = rot_pts([(x * k, y * k) for x, y in [(16, 0), (3, -4), (-8, -4), (-8, 4), (3, 4)]], sx, sy, ang)
        pygame.draw.polygon(surf, (225, 230, 240), blade)
        pygame.draw.polygon(surf, (90, 95, 110), blade, 1)
        pygame.draw.polygon(surf, (200, 160, 60), rot_pts([(-8 * k, -7 * k), (-11 * k, -7 * k), (-11 * k, 7 * k),
                                                           (-8 * k, 7 * k)], sx, sy, ang))
        pygame.draw.polygon(surf, (110, 70, 35), rot_pts([(-11 * k, -3 * k), (-20 * k, -3 * k), (-20 * k, 3 * k),
                                                          (-11 * k, 3 * k)], sx, sy, ang))
        return
    if style == "ice":
        k = max(0.9, r / 7.0)
        pts = rot_pts([(x * k, y * k) for x, y in [(17, 0), (4, -6), (-9, -4), (-15, 0), (-9, 4), (4, 6)]], sx, sy, ang)
        pygame.draw.polygon(surf, color, pts)
        pygame.draw.polygon(surf, WHITE, pts, 2)
        a, b2 = rot_pts([(15 * k, 0), (-12 * k, 0)], sx, sy, ang)
        pygame.draw.line(surf, WHITE, a, b2, 1)
        return
    if style == "fire":
        flick = 1 + 0.15 * math.sin(t * 20)
        pygame.draw.polygon(surf, (255, 150, 40), [(sx - sn * r, sy + c * r),
                                                   (sx - c * r * 3.2 * flick, sy - sn * r * 3.2 * flick),
                                                   (sx + sn * r, sy - c * r)])
        pygame.draw.polygon(surf, (255, 230, 120), [(sx - sn * r * .6, sy + c * r * .6),
                                                    (sx - c * r * 2.0, sy - sn * r * 2.0),
                                                    (sx + sn * r * .6, sy - c * r * .6)])
        pygame.draw.circle(surf, color, (ix, iy), r)
        pygame.draw.circle(surf, (255, 240, 150), (ix, iy), max(2, int(r * 0.55)))
        return
    if style == "spear":
        L = 34 + r
        tail = (sx - c * L, sy - sn * L)
        neck = (sx + c * L * 0.4, sy + sn * L * 0.4)
        pygame.draw.line(surf, (140, 100, 60), tail, neck, 5)
        tip = (sx + c * (L * 0.4 + 26), sy + sn * (L * 0.4 + 26))
        pygame.draw.polygon(surf, (225, 230, 240), [tip, (neck[0] - sn * 8, neck[1] + c * 8), (neck[0] - c * 8, neck[1] - sn * 8),
                                                    (neck[0] + sn * 8, neck[1] - c * 8)])
        pygame.draw.polygon(surf, (70, 75, 90), [tip, (neck[0] - sn * 8, neck[1] + c * 8), (neck[0] - c * 8, neck[1] - sn * 8),
                                                 (neck[0] + sn * 8, neck[1] - c * 8)], 2)
        return
    if style == "bullet":
        pygame.draw.line(surf, (255, 230, 150), (sx - c * 9, sy - sn * 9), (sx, sy), max(2, r))
        pygame.draw.circle(surf, (255, 250, 220), (ix, iy), max(2, r - 1))
        return
    if style == "orb":
        pygame.draw.circle(surf, _dk(color, 0.55), (ix, iy), r + 3, 2)
        pygame.draw.circle(surf, color, (ix, iy), r)
        pygame.draw.circle(surf, WHITE, (ix - r // 3, iy - r // 3), max(2, r // 3))
        return
    if style == "spirit":
        for i in range(1, 4):
            wob = math.sin(t * 12 + i) * r * 0.5
            pygame.draw.circle(surf, _dk(color, 0.7),
                               (int(sx - c * r * i * 0.9 - sn * wob), int(sy - sn * r * i * 0.9 + c * wob)),
                               max(2, int(r * (1 - i * 0.2))))
        pygame.draw.circle(surf, color, (ix, iy), r)
        for k in (-1, 1):
            pygame.draw.circle(surf, (20, 15, 40), (int(ix + k * r * 0.35), iy - r // 4), max(1, r // 5))
        return
    if style == "shuriken":
        pts = []
        for i in range(8):
            rr = r * 1.7 if i % 2 == 0 else r * 0.55
            a = t * 18 + i * math.pi / 4
            pts.append((sx + math.cos(a) * rr, sy + math.sin(a) * rr))
        pygame.draw.polygon(surf, color, pts)
        pygame.draw.polygon(surf, (70, 70, 85), pts, 1)
        pygame.draw.circle(surf, (70, 70, 85), (ix, iy), max(1, r // 3))
        return
    if style == "rock":
        pts = []
        for i in range(9):
            a = t * 3 + i * math.tau / 9
            rr = r * (1.0 if i % 2 == 0 else 0.78)
            pts.append((sx + math.cos(a) * rr, sy + math.sin(a) * rr))
        pygame.draw.polygon(surf, color, pts)
        pygame.draw.polygon(surf, _dk(color, 0.45), pts, 3)
        return
    pygame.draw.circle(surf, color, (ix, iy), r)
    pygame.draw.circle(surf, BLACK, (ix, iy), r, 1)


def bolt_points(x1, y1, x2, y2, segs=6, jit=10):
    dx, dy = x2 - x1, y2 - y1
    d = math.hypot(dx, dy) or 1
    nx, ny = -dy / d, dx / d
    pts = [(x1, y1)]
    for i in range(1, segs):
        f = i / segs
        o = random.uniform(-jit, jit)
        pts.append((x1 + dx * f + nx * o, y1 + dy * f + ny * o))
    pts.append((x2, y2))
    return pts


def draw_bolt(surf, x1, y1, x2, y2, color, width=4, segs=6, jit=10):
    pts = bolt_points(x1, y1, x2, y2, segs, jit)
    pygame.draw.lines(surf, color, False, pts, width)
    pygame.draw.lines(surf, WHITE, False, pts, max(1, width // 3))


def draw_gauntlet(surf, x, y, side, S, mode, t):
    """Tangan terbang Raja Inflasi: sarung tangan baja biru-indigo berlis emas, rune cyan bercahaya, tanpa lengan (melayang)."""
    base, plate, trim, glow = (50, 60, 150), (95, 120, 215), (240, 200, 90), (90, 235, 255)
    fist = mode != "idle"
    ang = math.pi if fist else 0.0
    def P(L):
        return rot_pts([(px * S, py * S) for px, py in L], x, y, ang)
    for k in range(5):
        a = (k + 1) * 0.42
        pygame.draw.circle(surf, _dk(glow, 0.9 - k * 0.14), (int(x - side * S * 0.2 * (k + 1)), int(y + S * (0.9 + 0.38 * (k + 1)) * (-1 if fist else 1))), max(1, int(S * (0.30 - 0.045 * k))))
    cuff = P([(-0.55, 0.78), (0.55, 0.78), (0.64, 1.18), (-0.64, 1.18)])
    pygame.draw.polygon(surf, base, cuff)
    pygame.draw.polygon(surf, BLACK, cuff, max(1, int(S * 0.05)))
    for sx_ in (-0.4, 0.0, 0.4):
        pygame.draw.polygon(surf, trim, P([(sx_ - 0.12, 1.18), (sx_ + 0.12, 1.18), (sx_, 1.5)]))
    pygame.draw.polygon(surf, trim, P([(-0.6, 0.8), (0.6, 0.8), (0.62, 0.9), (-0.62, 0.9)]))
    palm = P([(-0.62, 0.8), (0.62, 0.8), (0.72, -0.05), (0.5, -0.5), (-0.5, -0.5), (-0.72, -0.05)])
    pygame.draw.polygon(surf, plate, palm)
    pygame.draw.polygon(surf, BLACK, palm, max(1, int(S * 0.06)))
    th = P([(-0.62 * side, 0.4), (-1.08 * side, 0.0), (-1.0 * side, -0.4), (-0.6 * side, -0.05)])
    pygame.draw.polygon(surf, base, th)
    pygame.draw.polygon(surf, BLACK, th, max(1, int(S * 0.05)))
    for i in range(4):
        fx = -0.45 + i * 0.3
        if fist:
            seg = P([(fx - 0.15, -0.38), (fx + 0.15, -0.38), (fx + 0.15, -0.78), (fx - 0.15, -0.78)])
            pygame.draw.polygon(surf, base, seg)
            pygame.draw.polygon(surf, BLACK, seg, max(1, int(S * 0.045)))
            pygame.draw.polygon(surf, trim, P([(fx - 0.1, -0.64), (fx + 0.1, -0.64), (fx + 0.1, -0.76), (fx - 0.1, -0.76)]))
        else:
            tilt = (i - 1.5) * 0.12
            for j, (y0, y1) in enumerate(((-0.45, -0.95), (-0.95, -1.4))):
                seg = P([(fx - 0.12 + tilt * (j + 1) * 0.5, y0), (fx + 0.12 + tilt * (j + 1) * 0.5, y0),
                         (fx + 0.1 + tilt * (j + 2) * 0.5, y1), (fx - 0.1 + tilt * (j + 2) * 0.5, y1)])
                pygame.draw.polygon(surf, base if j == 0 else plate, seg)
                pygame.draw.polygon(surf, BLACK, seg, max(1, int(S * 0.04)))
    pulse = 0.5 + 0.5 * math.sin(t * 6)
    cx_, cy_ = rot_pts([(0.0, 0.2 * S)], x, y, ang)[0]
    pygame.draw.circle(surf, _dk(glow, 0.5), (int(cx_), int(cy_)), max(2, int(S * 0.27)))
    pygame.draw.circle(surf, glow, (int(cx_), int(cy_)), max(1, int(S * (0.15 + 0.05 * pulse))))
    pygame.draw.circle(surf, glow, (int(x), int(y)), max(4, int(S * (1.42 + 0.06 * pulse))), max(1, int(S * 0.04)))


def draw_fist(surf, sx, sy, ang, s=18):
    skin, edge = (240, 190, 140), (120, 70, 40)
    palm = rot_pts([(-s, -s * .8), (s * .6, -s * .8), (s * .6, s * .8), (-s, s * .8)], sx, sy, ang)
    pygame.draw.polygon(surf, skin, palm)
    pygame.draw.polygon(surf, edge, palm, 2)
    for i in range(4):
        ky = (-0.56 + i * 0.373) * s
        kx, kyy = rot_pts([(s * .62, ky)], sx, sy, ang)[0]
        pygame.draw.circle(surf, skin, (int(kx), int(kyy)), max(3, int(s * .3)))
        pygame.draw.circle(surf, edge, (int(kx), int(kyy)), max(3, int(s * .3)), 2)
    thumb = rot_pts([(-s * .1, s * .8), (s * .5, s * .8), (s * .4, s * 1.2), (-s * .2, s * 1.1)], sx, sy, ang)
    pygame.draw.polygon(surf, skin, thumb)
    pygame.draw.polygon(surf, edge, thumb, 2)


def draw_boomerang_shape(surf, sx, sy, spin, r):
    R = r * 2.2
    for sign in (-1, 1):
        a = spin + sign * 0.9
        tip = (sx + math.cos(a) * R, sy + math.sin(a) * R)
        pygame.draw.line(surf, (120, 75, 30), (sx, sy), tip, max(4, int(r * 0.9)))
        pygame.draw.line(surf, (205, 150, 80), (sx, sy), tip, max(2, int(r * 0.4)))
        pygame.draw.circle(surf, (120, 75, 30), (int(tip[0]), int(tip[1])), max(2, int(r * 0.45)))
    pygame.draw.circle(surf, (120, 75, 30), (int(sx), int(sy)), max(3, int(r * 0.6)))


def draw_shield_shape(surf, sx, sy, ang, r, base=(170, 200, 235), edge=WHITE):
    """Perisai bentuk 'heater' (runcing ke luar) dengan lambang salib."""
    pts = rot_pts([(-r * .8, -r * .9), (-r * .8, r * .9), (r * .1, r * .9), (r * 1.1, 0), (r * .1, -r * .9)], sx, sy, ang)
    pygame.draw.polygon(surf, base, pts)
    pygame.draw.polygon(surf, edge, pts, 3)
    a, b = rot_pts([(-r * .55, 0), (r * .8, 0)], sx, sy, ang)
    pygame.draw.line(surf, edge, a, b, 3)
    a, b = rot_pts([(-r * .1, -r * .6), (-r * .1, r * .6)], sx, sy, ang)
    pygame.draw.line(surf, edge, a, b, 3)


ENEMY_TYPES = [
    {"name": "Merah", "color": (230, 70, 70), "radius": 12, "speed": 1.7, "hp": 15, "xp": 3, "dmg": 6, "gold": 1, "min_wave": 0, "pickup_chance": 0.02},
    {"name": "Hijau", "color": (80, 200, 120), "radius": 17, "speed": 1.1, "hp": 34, "xp": 5, "dmg": 8, "gold": 2, "min_wave": 0, "pickup_chance": 0.03},
    {"name": "Ungu", "color": (170, 90, 220), "radius": 10, "speed": 2.6, "hp": 10, "xp": 4, "dmg": 5, "gold": 2, "min_wave": 0, "pickup_chance": 0.02},
    {"name": "Oranye", "color": (240, 150, 60), "radius": 23, "speed": 0.85, "hp": 65, "xp": 10, "dmg": 13, "gold": 4, "min_wave": 0.5, "pickup_chance": 0.05},
    {"name": "Cyan", "color": (90, 210, 220), "radius": 8, "speed": 3.1, "hp": 7, "xp": 2, "dmg": 4, "gold": 1, "min_wave": 1, "pickup_chance": 0.01},
    {"name": "Hitam", "color": (60, 60, 70), "radius": 19, "speed": 1.6, "hp": 90, "xp": 16, "dmg": 16, "gold": 8, "min_wave": 2.2, "pickup_chance": 0.22},
]

SPLIT_TYPE = {"name": "Pecah", "color": (255, 120, 180), "radius": 15, "speed": 1.3, "hp": 26, "xp": 6,
              "dmg": 9, "gold": 3, "min_wave": 0, "pickup_chance": 0.04, "splits": True}
SPLIT_CHILD_TYPE = {"name": "Pecahan", "color": (255, 165, 205), "radius": 8, "speed": 3.6, "hp": 6, "xp": 1,
                     "dmg": 4, "gold": 1, "min_wave": 0, "pickup_chance": 0.0}
ARMORED_TYPE = {"name": "Zirah", "color": (120, 120, 140), "radius": 20, "speed": 1.0, "hp": 40, "xp": 9,
                 "dmg": 10, "gold": 5, "min_wave": 0, "pickup_chance": 0.05, "armor": 45}
NECRO_TYPE = {"name": "Necromancer", "color": (90, 40, 130), "radius": 18, "speed": 0.9, "hp": 55, "xp": 14,
              "dmg": 8, "gold": 6, "min_wave": 0, "pickup_chance": 0.08, "summoner": True}
SKELETON_TYPE = {"name": "Tengkorak", "color": (220, 220, 200), "radius": 9, "speed": 2.0, "hp": 12, "xp": 2,
                  "dmg": 6, "gold": 1, "min_wave": 0, "pickup_chance": 0.0}
SHOOTER_TYPE = {"name": "Penembak", "color": (200, 80, 40), "radius": 14, "speed": 1.2, "hp": 24, "xp": 8,
                 "dmg": 5, "gold": 4, "min_wave": 0, "pickup_chance": 0.06, "shooter": True}
EXPLODER_TYPE = {"name": "Peledak", "color": (255, 70, 35), "radius": 15, "speed": 1.5, "hp": 18, "xp": 7,
                  "dmg": 6, "gold": 3, "min_wave": 0, "pickup_chance": 0.05, "explodes": True,
                  "explode_radius": 95, "explode_damage": 20}
GIANT_TYPE = {"name": "Raksasa", "color": (110, 75, 40), "shape": "giant", "radius": 38, "speed": 0.5, "hp": 230, "xp": 25,
              "dmg": 22, "gold": 12, "min_wave": 0, "pickup_chance": 0.12}

ADVANCED_ENEMY_TYPES = [SPLIT_TYPE, ARMORED_TYPE, NECRO_TYPE, SHOOTER_TYPE, EXPLODER_TYPE, GIANT_TYPE]

BOSS_TYPE = {"name": "Bos Biasa", "color": (140, 10, 30), "radius": 46, "speed": 0.9,
             "hp": 1100, "xp": 90, "dmg": 24, "gold": 90, "pickup_chance": 1.0}
HEALER_BOSS_TYPE = {"name": "Bos Penyembuh", "color": (30, 150, 90), "radius": 48, "speed": 0.75,
                     "hp": 1500, "xp": 100, "dmg": 24, "gold": 100, "pickup_chance": 1.0, "healer": True}

PICKUP_DROP_KINDS = ["magnet", "health", "freeze", "nuke"]


BAT_TYPE = {"name": "Kelelawar", "color": (130, 70, 160), "radius": 9, "speed": 3.0, "hp": 9, "xp": 3,
            "dmg": 5, "gold": 2, "min_wave": 0, "min_lv": 3, "pickup_chance": 0.02,
            "shape": "bat", "bat": True}
DASHER_TYPE = {"name": "Penerjang", "color": (255, 150, 50), "radius": 14, "speed": 1.0, "hp": 42, "xp": 9,
               "dmg": 12, "gold": 4, "min_wave": 0, "min_lv": 4, "pickup_chance": 0.05,
               "shape": "triangle", "dasher": True}
SHIELD_TYPE = {"name": "Prajurit Perisai", "color": (90, 130, 200), "radius": 19, "speed": 0.9, "hp": 95,
               "xp": 12, "dmg": 12, "gold": 5, "min_wave": 0, "min_lv": 5, "pickup_chance": 0.06,
               "shape": "square", "reduction": 0.55}
TELEPORT_TYPE = {"name": "Hantu Kedip", "color": (170, 245, 245), "radius": 13, "speed": 1.3, "hp": 34,
                 "xp": 10, "dmg": 9, "gold": 4, "min_wave": 0, "min_lv": 6, "pickup_chance": 0.05,
                 "shape": "ghost", "teleporter": True}
LASER_TYPE = {"name": "Penembak Laser", "color": (255, 60, 110), "radius": 14, "speed": 0.8, "hp": 48,
              "xp": 14, "dmg": 14, "gold": 6, "min_wave": 0, "min_lv": 7, "pickup_chance": 0.07,
              "shape": "diamond", "laser": True, "stop_range": 420}
NINJA_TYPE = {"name": "Ninja Bayangan", "color": (45, 45, 70), "radius": 12, "speed": 2.2, "hp": 32,
              "xp": 11, "dmg": 8, "gold": 5, "min_wave": 0, "min_lv": 8, "pickup_chance": 0.05,
              "shape": "ninja", "ninja": True, "stop_range": 300}
BOMBER_TYPE = {"name": "Pelempar Bom", "color": (190, 150, 70), "radius": 16, "speed": 0.9, "hp": 55,
               "xp": 13, "dmg": 10, "gold": 6, "min_wave": 0, "min_lv": 9, "pickup_chance": 0.07,
               "shape": "circle", "bomber": True, "stop_range": 380}
SNIPER_TYPE = {"name": "Penembak Jitu", "color": (70, 170, 90), "radius": 13, "speed": 0.7, "hp": 30,
               "xp": 13, "dmg": 8, "gold": 6, "min_wave": 0, "min_lv": 10, "pickup_chance": 0.06,
               "shape": "triangle", "sniper": True, "stop_range": 520}
BUFFER_TYPE = {"name": "Dukun Semangat", "color": (255, 225, 120), "radius": 15, "speed": 0.9, "hp": 65,
               "xp": 16, "dmg": 8, "gold": 8, "min_wave": 0, "min_lv": 11, "pickup_chance": 0.08,
               "shape": "diamond", "buffer": True}
TOXIC_TYPE = {"name": "Racun Berjalan", "color": (130, 225, 60), "radius": 14, "speed": 1.3, "hp": 38,
              "xp": 12, "dmg": 9, "gold": 5, "min_wave": 0, "min_lv": 12, "pickup_chance": 0.05,
              "shape": "circle", "toxic": True}
GOLEM_TYPE = {"name": "Golem Baja", "color": (135, 135, 155), "radius": 34, "speed": 0.45, "hp": 420,
              "xp": 45, "dmg": 26, "gold": 22, "min_wave": 0, "min_lv": 13, "pickup_chance": 0.2,
              "shape": "square", "armor": 160, "slam": True, "reduction": 0.25}

NEW_ENEMY_TYPES = [BAT_TYPE, DASHER_TYPE, SHIELD_TYPE, TELEPORT_TYPE, LASER_TYPE, NINJA_TYPE,
                   BOMBER_TYPE, SNIPER_TYPE, BUFFER_TYPE, TOXIC_TYPE, GOLEM_TYPE]


FAST_GIANT_TYPE = {"name": "Raksasa Cepat", "color": (190, 110, 50), "radius": 36, "speed": 1.35, "hp": 210,
                   "xp": 30, "dmg": 20, "gold": 14, "min_wave": 0, "min_lv": 10, "pickup_chance": 0.12,
                   "shape": "giant"}
THUNDER_TYPE = {"name": "Penyambar Petir", "color": (255, 240, 110), "radius": 13, "speed": 2.4, "hp": 42,
                "xp": 14, "dmg": 8, "gold": 6, "min_wave": 0, "min_lv": 9, "pickup_chance": 0.06,
                "shape": "diamond", "thunder": True}
SUPER_GIANT_TYPE = {"name": "Raksasa Super", "color": (95, 60, 35), "radius": 54, "speed": 0.4, "hp": 760,
                    "xp": 70, "dmg": 34, "gold": 30, "min_wave": 0, "min_lv": 16, "pickup_chance": 0.25,
                    "shape": "giant"}
FAST_GSKEL_TYPE = {"name": "Tengkorak Raksasa Cepat", "color": (225, 225, 205), "radius": 30, "speed": 1.9,
                   "hp": 170, "xp": 26, "dmg": 18, "gold": 12, "min_wave": 0, "min_lv": 7,
                   "pickup_chance": 0.1, "shape": "skull"}
GSKEL_TYPE = {"name": "Tengkorak Raksasa", "color": (215, 215, 195), "radius": 30, "speed": 0.95, "hp": 150,
              "xp": 22, "dmg": 17, "gold": 10, "min_wave": 0, "min_lv": 99, "pickup_chance": 0.05,
              "shape": "skull"}
SPLIT_MID_TYPE = {"name": "Raksasa Sedang", "color": (150, 100, 60), "radius": 24, "speed": 1.0, "hp": 90,
                  "xp": 10, "dmg": 12, "gold": 5, "min_wave": 0, "pickup_chance": 0.03, "shape": "giant",
                  "split_child": SPLIT_TYPE, "split_n": 2}
SPLIT_GIANT_TYPE = {"name": "Raksasa Pecah", "color": (125, 85, 55), "radius": 40, "speed": 0.55, "hp": 260,
                    "xp": 30, "dmg": 20, "gold": 14, "min_wave": 0, "min_lv": 11, "pickup_chance": 0.12,
                    "shape": "giant", "split_child": SPLIT_MID_TYPE, "split_n": 2}
TANKER_TYPE = {"name": "Tanker Raksasa", "color": (105, 115, 100), "radius": 42, "speed": 0.85, "hp": 520,
               "xp": 60, "dmg": 26, "gold": 24, "min_wave": 0, "min_lv": 14, "pickup_chance": 0.2,
               "shape": "giant", "variant": "spiked", "cls": "Tank", "armor": 320, "reduction": 0.2, "explodes": True, "explode_radius": 150,
               "explode_damage": 26, "gas": (135, 6.0)}
FAST_TANK_TYPE = {"name": "Tank Raksasa Cepat", "color": (90, 110, 80), "radius": 40, "speed": 1.75, "hp": 460,
                  "xp": 55, "dmg": 28, "gold": 22, "min_wave": 0, "min_lv": 18, "pickup_chance": 0.18,
                  "shape": "giant", "variant": "runner", "cls": "Tank", "armor": 240, "reduction": 0.25}
NEW_ENEMY_TYPES += [FAST_GIANT_TYPE, THUNDER_TYPE, SUPER_GIANT_TYPE, FAST_GSKEL_TYPE, SPLIT_GIANT_TYPE,
                    TANKER_TYPE, FAST_TANK_TYPE]

NECRO_BOSS_TYPE = {"name": "Bos Necromancer", "shield": 700, "shield_style": "runic", "color": (95, 40, 140), "radius": 44, "speed": 0.7, "hp": 1900,
                   "xp": 130, "dmg": 26, "gold": 120, "pickup_chance": 1.0, "necro": True, "reward": 1}
BRUTE_BOSS_TYPE = {"name": "Brute Berkepala Dua", "shield": 700, "shield_style": "plates", "color": (150, 95, 60), "radius": 56, "speed": 0.85,
                   "hp": 2600, "xp": 150, "dmg": 30, "gold": 140, "pickup_chance": 1.0, "brute": True,
                   "reward": 2}

for _k, _lv in ((SPLIT_TYPE, 3), (ARMORED_TYPE, 4), (NECRO_TYPE, 6), (SHOOTER_TYPE, 4), (EXPLODER_TYPE, 5),
                (GIANT_TYPE, 8), (ENEMY_TYPES[2], 2), (ENEMY_TYPES[4], 2), (ENEMY_TYPES[5], 5)):
    _k["min_lv"] = _lv
ALL_SPAWN_TYPES = ENEMY_TYPES + ADVANCED_ENEMY_TYPES + NEW_ENEMY_TYPES

GIANT_VARIANTS = {"Raksasa Cepat": "runner", "Raksasa Super": "hulk", "Raksasa Pecah": "hunch", "Raksasa Sedang": "hunch",
                  "Algojo Raksasa": "horned", "Raksasa Perisai": "plated", "Ksatria Raksasa": "plated", "Raksasa Induk": "hunch",
                  "Raksasa Shotgun": "cyclops", "Ketua Raksasa": "horned", "Raksasa Minigun": "bulwark", "Raksasa Reaper": "hunch",
                  "Raksasa Salju": "hulk", "Raksasa Lava": "horned", "Raksasa Racun": "hunch", "Raksasa Badai": "cyclops",
                  "Golem Batu": "bulwark", "Raksasa Batu": "hulk", "Golem Magma": "bulwark", "Golem Es": "bulwark", "Raksasa": "brute"}
ENEMY_COST = {"Merah": 1, "Hijau": 2, "Ungu": 1, "Oranye": 3, "Cyan": 1, "Hitam": 4, "Pecah": 2, "Zirah": 4,
              "Necromancer": 5, "Penembak": 3, "Peledak": 3, "Raksasa": 10, "Kelelawar": 1, "Penerjang": 3,
              "Prajurit Perisai": 4, "Hantu Kedip": 3, "Penembak Laser": 4, "Ninja Bayangan": 3,
              "Pelempar Bom": 4, "Penembak Jitu": 4, "Dukun Semangat": 5, "Racun Berjalan": 3,
              "Golem Baja": 10, "Raksasa Cepat": 9, "Penyambar Petir": 4, "Raksasa Super": 18,
              "Tengkorak Raksasa Cepat": 7, "Raksasa Pecah": 9, "Tanker Raksasa": 14, "Tank Raksasa Cepat": 15}


EVENT2_KINDS = {"rockfall", "blizzard", "pincer", "spiral", "skeleton_horde", "bomb_run", "meteor_shower", "storm", "gas_field", "frenzy",
                "elite_squad", "giant_charge"}
EVENT_LABELS = {"ring": "KEPUNGAN!", "wall": "TEMBOK MUSUH!", "bats": "KAWANAN KELELAWAR!", "pincer": "TANG! DUA TEMBOK!",
                "spiral": "PUSARAN MUSUH!", "skeleton_horde": "PASUKAN TENGKORAK!", "bomb_run": "SERBUAN PELEDAK!",
                "meteor_shower": "HUJAN METEOR!", "storm": "BADAI PETIR!", "gas_field": "KABUT BERACUN!",
                "frenzy": "AMUK MASSAL!", "elite_squad": "PASUKAN ELIT!", "giant_charge": "SERBUAN RAKSASA!",
                "rockfall": "HUJAN BATU!", "blizzard": "BADAI SALJU!"}
EVENT_ALL_SIDES = {"rockfall", "blizzard", "ring", "spiral", "skeleton_horde", "bomb_run", "meteor_shower", "storm", "gas_field", "frenzy"}


EVENT_HINTS = {"ring": "Musuh mengepung dari semua sisi", "wall": "Tembok musuh dari satu sisi - cari celahnya",
               "bats": "Kelelawar terbang searah dari satu sisi", "pincer": "Dua tembok dari sisi berlawanan",
               "spiral": "Musuh berputar mengitarimu", "skeleton_horde": "Pasukan tengkorak dari segala arah",
               "bomb_run": "Musuh peledak menyerbu - jaga jarak!", "meteor_shower": "Meteor jatuh - hindari lingkaran merah",
               "storm": "Petir menyambar - hindari lingkaran, ada penyambar petir", "gas_field": "Awan racun muncul di sekitarmu",
               "frenzy": "Semua musuh biasa jadi lebih cepat", "elite_squad": "Musuh elit (lebih kuat) dari satu sisi",
               "giant_charge": "Raksasa menyerbu cepat dari satu sisi", "rockfall": "Batu jatuh dari langit",
               "blizzard": "Badai salju: musuh es dan zona yang melambatkan"}
FINAL_ATTACKS = ["hand_slam", "hand_laser", "meteors", "lightning", "minigun", "sonic", "rocks", "rings", "summon", "mimic",
                 "frenzy", "fire_spiral", "gas", "spear_rain"]
FINAL_LABELS = {"hand_slam": "TANGAN MENGHANTAM", "hand_laser": "LASER TANGAN", "meteors": "HUJAN METEOR", "lightning": "BADAI PETIR",
                "minigun": "MINIGUN", "sonic": "SONIC BOOM", "rocks": "LEMPAR BATU", "rings": "GELOMBANG CINCIN", "summon": "PANGGIL PASUKAN",
                "mimic": "JURUS PENIRU", "frenzy": "PERINTAH SERANG", "fire_spiral": "SPIRAL API", "gas": "KABUT RACUN", "spear_rain": "HUJAN TOMBAK"}


def enemy_cost(kind):
    c = ENEMY_COST.get(kind["name"])
    if c is None:
        c = max(1, min(18, int(round(kind["hp"] / 30.0))))
    return c


_LV_CACHE = {}


_BOT_CACHE = {}


def _bot_label(name):
    surf = _BOT_CACHE.get(name)
    if surf is None:
        surf = font_tiny.render("SIM: " + name, True, (120, 235, 255))
        _BOT_CACHE[name] = surf
    return surf


def _lv_label(n, elite=False):
    key = (n, elite)
    surf = _LV_CACHE.get(key)
    if surf is None:
        surf = font_tiny.render(("Lv.%d" % n) + ("*" if elite else ""), True,
                                GOLD_COLOR if elite else (200, 205, 220))
        _LV_CACHE[key] = surf
    return surf



def _nt(name, color, radius, speed, hp, xp, dmg, gold, min_lv, **kw):
    d = {"name": name, "color": color, "radius": radius, "speed": speed, "hp": hp, "xp": xp, "dmg": dmg,
         "gold": gold, "min_wave": 0, "min_lv": min_lv, "pickup_chance": kw.pop("pickup_chance", 0.12), "shape": "giant"}
    d.update(kw)
    return d


WARDEN_TYPE = _nt("Warden", (22, 58, 68), 38, 0.75, 650, 70, 38, 30, 20, shape="warden", warden=True, pickup_chance=0.25)
MIMIC_TYPE = _nt("Peniru Sihir", (190, 120, 255), 16, 0.9, 190, 22, 12, 10, 12, shape="circle", gear="runes", mimic=True)
TANK_IRON_TYPE = _nt("Tank Besi", (95, 105, 110), 26, 1.25, 300, 30, 20, 14, 8, shape="giant", variant="bulwark", cls="Tank", armor=180, reduction=0.1, shield=160, shield_style="plates")
GHOST_GIANT_TYPE = _nt("Raksasa Hantu", (170, 200, 235), 40, 0.7, 340, 36, 22, 16, 13, shape="ghost", ethereal=True)
EXEC_GIANT_TYPE = _nt("Algojo Raksasa", (120, 70, 60), 44, 0.55, 520, 55, 36, 26, 15, gear="hammer", hammer=True, armor=120)
SHIELD_GIANT_TYPE = _nt("Raksasa Perisai", (110, 120, 140), 42, 0.5, 480, 55, 26, 24, 17, gear="bigshield", protector=True,
                        armor=160, shield=400, shield_style="plates")
KNIGHT_GIANT_TYPE = _nt("Ksatria Raksasa", (140, 145, 160), 42, 0.7, 560, 58, 34, 26, 19, gear="sword", slash=True, armor=220, shield=140, shield_style="bubble")
ICE_GOLEM_TYPE = _nt("Golem Es", (150, 215, 255), 30, 0.7, 330, 34, 20, 16, 9, gear="ice", ice_immune=True, armor=60, shield=110, shield_style="ice")
MOTHER_GIANT_TYPE = _nt("Raksasa Induk", (150, 110, 130), 46, 0.5, 700, 70, 24, 34, 21, gear="belly", mother=True)
CRYSTAL_MAGE_TYPE = _nt("Penyihir Kristal", (120, 200, 255), 15, 0.8, 130, 24, 8, 12, 14, shape="circle", gear="crystal", crystal_mage=True)
TWIN_TANKER_TYPE = _nt("Tanker Kepala Dua", (115, 90, 80), 34, 2.3, 380, 50, 24, 22, 22, shape="giant", variant="runner", cls="Tank", gear="twinheads",
                       two_heads=True, armor=200)
SHOTGUN_GIANT_TYPE = _nt("Raksasa Shotgun", (130, 100, 70), 40, 0.6, 420, 48, 18, 22, 16, gear="shotgun", shotgun=True)
CHIEF_GIANT_TYPE = _nt("Ketua Raksasa", (170, 90, 60), 44, 0.55, 600, 62, 28, 30, 18, gear="banner", chief=True)
MINIGUN_GIANT_TYPE = _nt("Raksasa Minigun", (90, 100, 90), 42, 0.3, 520, 60, 24, 28, 20, gear="minigun", minigunner=True, armor=100)
REAPER_GIANT_TYPE = _nt("Raksasa Reaper", (45, 40, 70), 44, 0.6, 560, 66, 30, 32, 24, gear="scythe", reaper=True)
MOTHER_MINI_TYPE = _nt("Raksasa Induk Mini", (190, 140, 160), 17, 1.5, 60, 6, 11, 4, 99, shape="giant", variant="hunch", pickup_chance=0.02)
ENEMY_COST["Raksasa Induk Mini"] = 2
NEW_ENEMY_TYPES += [WARDEN_TYPE, MIMIC_TYPE, TANK_IRON_TYPE, GHOST_GIANT_TYPE, EXEC_GIANT_TYPE, SHIELD_GIANT_TYPE,
                    KNIGHT_GIANT_TYPE, ICE_GOLEM_TYPE, MOTHER_GIANT_TYPE, CRYSTAL_MAGE_TYPE, TWIN_TANKER_TYPE,
                    SHOTGUN_GIANT_TYPE, CHIEF_GIANT_TYPE, MINIGUN_GIANT_TYPE, REAPER_GIANT_TYPE]
ALL_SPAWN_TYPES = ENEMY_TYPES + ADVANCED_ENEMY_TYPES + NEW_ENEMY_TYPES
ENEMY_COST.update({"Warden": 20, "Peniru Sihir": 6, "Tank Besi": 8, "Raksasa Hantu": 9, "Algojo Raksasa": 14,
                   "Raksasa Perisai": 15, "Ksatria Raksasa": 15, "Golem Es": 7, "Raksasa Induk": 18,
                   "Penyihir Kristal": 6, "Tanker Kepala Dua": 14, "Raksasa Shotgun": 12, "Ketua Raksasa": 16,
                   "Raksasa Minigun": 16, "Raksasa Reaper": 18})
TANK_POOL = [TANK_IRON_TYPE, FAST_TANK_TYPE, TANKER_TYPE, ARMORED_TYPE]


class ReturnAxe:
    """Kapak lempar: melesat ke arah pemain lalu KEMBALI ke pemiliknya. Menembus (tidak hilang saat kena)."""
    pierce_player = True
    home = 0
    style = "axe"

    def __init__(self, owner, tx, ty, speed, damage, out_time=0.8, radius=22):
        self.owner = owner
        self.x, self.y = owner.x, owner.y
        dx, dy = tx - self.x, ty - self.y
        d = math.hypot(dx, dy) or 1.0
        self.vx, self.vy = dx / d * speed, dy / d * speed
        self.speed = speed
        self.damage = damage
        self.radius = radius
        self.color = (210, 215, 225)
        self.t_out = out_time
        self.phase = "out"
        self.life = 12.0
        self.alive = True
        self.spin = 0.0
        self.home_target = None

    def update(self, dt):
        self.spin += dt * 16
        self.life -= dt
        if self.life <= 0 or self.owner.dead:
            self.alive = False
            return
        if self.phase == "out":
            self.x += self.vx * dt * 60
            self.y += self.vy * dt * 60
            self.t_out -= dt
            if self.t_out <= 0:
                self.phase = "back"
        else:
            dx, dy = self.owner.x - self.x, self.owner.y - self.y
            d = math.hypot(dx, dy) or 1.0
            self.x += dx / d * self.speed * 1.15 * dt * 60
            self.y += dy / d * self.speed * 1.15 * dt * 60
            if d < 36:
                self.alive = False

    def draw(self, surf, cam_x, cam_y):
        sx, sy = self.x - cam_x, self.y - cam_y
        if -60 <= sx <= WIDTH + 60 and -60 <= sy <= HEIGHT + 60:
            if self.style == "boom":
                draw_boomerang_shape(surf, sx, sy, self.spin, self.radius)
            else:
                draw_axe_shape(surf, sx, sy, self.spin, self.radius)


def draw_axe_shape(surf, sx, sy, ang, r):
    """Kapak: gagang kayu + bilah baja melengkung di ujung."""
    c, sn = math.cos(ang), math.sin(ang)
    pygame.draw.line(surf, (120, 80, 45), (sx - c * r, sy - sn * r), (sx + c * r, sy + sn * r), max(3, int(r * 0.22)))
    blade = rot_pts([(r * 0.35, 0), (r * 0.95, -r * 0.7), (r * 1.15, -r * 0.1), (r * 1.15, r * 0.5), (r * 0.95, r * 0.9),
                     (r * 0.35, r * 0.35)], sx, sy, ang)
    pygame.draw.polygon(surf, (215, 220, 232), blade)
    pygame.draw.polygon(surf, (70, 75, 90), blade, 2)
    pygame.draw.circle(surf, (70, 75, 90), (int(sx - c * r), int(sy - sn * r)), max(2, int(r * 0.15)))


def draw_gear(surf, gear, ix, iy, r, face, t, e=None):
    """Senjata/atribut raksasa (palu, pedang, perisai, shotgun, minigun, spanduk, sabit, ...)."""
    c, sn = math.cos(face), math.sin(face)
    st = e.bstate if e is not None else None
    if gear == "hammer":
        pivot = (ix + c * r * 0.75 - sn * r * 0.1, iy + sn * r * 0.75 + c * r * 0.1)
        a = face + (-1.35 if st == "slam_wind" else (1.15 if st == "slam" else 0.45))
        L = r * 1.7
        end = (pivot[0] + math.cos(a) * L, pivot[1] + math.sin(a) * L)
        pygame.draw.line(surf, (115, 78, 45), pivot, end, max(4, int(r * 0.16)))
        head = rot_pts([(-r * 0.2, -r * 0.45), (r * 0.5, -r * 0.45), (r * 0.5, r * 0.45), (-r * 0.2, r * 0.45)], end[0], end[1], a)
        pygame.draw.polygon(surf, (100, 105, 118), head)
        pygame.draw.polygon(surf, BLACK, head, 3)
    elif gear == "sword":
        a = face + (math.sin(t * 6) * 0.1 if st != "slash_wind" else -0.9)
        p0 = (ix + math.cos(a) * r * 0.7, iy + math.sin(a) * r * 0.7)
        blade = rot_pts([(0, -r * 0.1), (r * 1.7, -r * 0.1), (r * 2.0, 0), (r * 1.7, r * 0.1), (0, r * 0.1)], p0[0], p0[1], a)
        pygame.draw.polygon(surf, (225, 230, 240), blade)
        pygame.draw.polygon(surf, (80, 85, 100), blade, 2)
        guard = rot_pts([(0, -r * 0.34), (r * 0.1, -r * 0.34), (r * 0.1, r * 0.34), (0, r * 0.34)], p0[0], p0[1], a)
        pygame.draw.polygon(surf, GOLD_COLOR, guard)
        pygame.draw.circle(surf, GOLD_COLOR, (int(p0[0] - math.cos(a) * r * 0.2), int(p0[1] - math.sin(a) * r * 0.2)), max(3, int(r * 0.12)))
    elif gear == "bigshield":
        up = e is not None and e.shield > 0
        draw_shield_shape(surf, ix + c * r * 1.2, iy + sn * r * 1.2, face, r * 0.95,
                          (120, 150, 200) if up else (105, 105, 110), (235, 240, 255) if up else (150, 150, 155))
    elif gear == "shotgun":
        a = face
        p0 = (ix + c * r * 0.5, iy + sn * r * 0.5)
        for off in (-3, 3):
            pygame.draw.line(surf, (50, 50, 58), (p0[0] - sn * off, p0[1] + c * off), (p0[0] + c * r * 1.7 - sn * off, p0[1] + sn * r * 1.7 + c * off), 4)
        stock = rot_pts([(-r * 0.7, -r * 0.1), (0, -r * 0.14), (0, r * 0.14), (-r * 0.7, r * 0.22)], p0[0], p0[1], a)
        pygame.draw.polygon(surf, (120, 80, 45), stock)
        if st == "aim":
            pygame.draw.circle(surf, (255, 200, 90), (int(p0[0] + c * r * 1.8), int(p0[1] + sn * r * 1.8)), 5)
    elif gear == "minigun":
        a = face
        p0 = (ix + c * r * 0.4, iy + sn * r * 0.4)
        spin = t * (30 if st == "fire" else 8 if st == "spin" else 0.5)
        pygame.draw.rect(surf, (60, 62, 68), (p0[0] - 10, p0[1] - 10, 20, 20), border_radius=4)
        for k in range(3):
            off = math.sin(spin + k * 2.094) * 6
            pygame.draw.line(surf, (155, 160, 170), (p0[0] - sn * off, p0[1] + c * off),
                             (p0[0] + c * r * 1.6 - sn * off, p0[1] + sn * r * 1.6 + c * off), 3)
        pygame.draw.circle(surf, (80, 82, 90), (int(p0[0] + c * r * 1.6), int(p0[1] + sn * r * 1.6)), 6, 2)
        for k in range(4):
            pygame.draw.circle(surf, (230, 190, 60), (int(ix - c * r * 0.2 - sn * (k - 1.5) * 5), int(iy + r * 0.5 + (k % 2) * 3)), 3)
        if st == "fire":
            pygame.draw.circle(surf, (255, 235, 150), (int(p0[0] + c * r * 1.85), int(p0[1] + sn * r * 1.85)), 6 + int(3 * math.sin(t * 40)))
    elif gear == "banner":
        px, py = ix - c * r * 0.7, iy - sn * r * 0.5 - r * 0.2
        pygame.draw.line(surf, (110, 80, 50), (px, py + r), (px, py - r * 1.7), 4)
        w = math.sin(t * 5) * 5
        pygame.draw.polygon(surf, (200, 50, 50), [(px, py - r * 1.7), (px + r * 1.0, py - r * 1.45 + w), (px, py - r * 1.05)])
        pygame.draw.polygon(surf, GOLD_COLOR, [(px, py - r * 1.7), (px + r * 1.0, py - r * 1.45 + w), (px, py - r * 1.05)], 2)
        if st == "command":
            pygame.draw.circle(surf, (255, 170, 70), (ix, iy), int(r * 1.5), 3)
    elif gear == "scythe":
        (px, py), (tx, ty) = rot_pts([(r * 0.8, r * 0.9), (r * 0.8, -r * 1.8)], ix, iy, face)
        pygame.draw.line(surf, (110, 85, 60), (px, py), (tx, ty), 4)
        blade = rot_pts([(r * 0.8, -r * 1.8), (r * 0.8 - r * 1.2, -r * 1.8 - r * 0.2), (r * 0.8 - r * 1.5, -r * 1.8 + r * 0.5),
                         (r * 0.8 - r * 0.9, -r * 1.8 + r * 0.1), (r * 0.8, -r * 1.8 + r * 0.25)], ix, iy, face)
        pygame.draw.polygon(surf, (190, 200, 215), blade)
        pygame.draw.polygon(surf, (50, 50, 70), blade, 2)
        hood = [(ix - r * 0.9, iy - r * 0.2), (ix + r * 0.9, iy - r * 0.2), (ix, iy - r * 1.35)]
        pygame.draw.polygon(surf, (35, 30, 55), hood)
        pygame.draw.polygon(surf, (90, 70, 130), hood, 2)
    elif gear == "belly":
        pygame.draw.circle(surf, (205, 160, 180), (ix, iy + int(r * 0.4)), int(r * 0.62))
        pygame.draw.circle(surf, (110, 60, 80), (ix, iy + int(r * 0.4)), int(r * 0.62), 2)
        pulse = 1 + 0.12 * math.sin(t * 5)
        for k in (-1, 0, 1):
            pygame.draw.circle(surf, (230, 130, 160), (ix + int(k * r * 0.25), iy + int(r * 0.4)), max(2, int(r * 0.1 * pulse)))
        if e is not None and e.mother_n:
            for k in range(e.mother_n):
                pygame.draw.line(surf, (110, 40, 60), (ix - r * 0.4 + k * r * 0.25, iy + r * 0.1), (ix - r * 0.3 + k * r * 0.25, iy + r * 0.7), 2)
    elif gear == "flames":
        for k in range(6):
            a = t * 2.2 + k * 1.047
            fx, fy = ix + math.cos(a) * (r + 3), iy + math.sin(a) * (r + 3) * 0.8 - r * 0.3
            h = 7 + 4 * math.sin(t * 9 + k)
            pygame.draw.polygon(surf, (255, 110, 30), [(fx - 4, fy), (fx + 4, fy), (fx, fy - h - 4)])
            pygame.draw.polygon(surf, (255, 220, 110), [(fx - 2, fy), (fx + 2, fy), (fx, fy - h * 0.6)])
    elif gear == "bubbles":
        for k in range(5):
            a = t * 1.4 + k * 1.257
            bx_, by_ = ix + math.cos(a) * (r * 0.75), iy + math.sin(a * 1.3) * (r * 0.6) - ((t * 20 + k * 9) % 14)
            pygame.draw.circle(surf, (150, 235, 90), (int(bx_), int(by_)), 4 + k % 3, 2)
    elif gear == "sparks":
        for k in range(4):
            a = t * 3 + k * 1.571
            x1, y1 = ix + math.cos(a) * (r + 2), iy + math.sin(a) * (r + 2)
            pygame.draw.lines(surf, (255, 245, 120), False, [(x1, y1), (x1 + math.cos(a + 0.6) * 7, y1 + math.sin(a + 0.6) * 7),
                                                              (x1 + math.cos(a - 0.4) * 11, y1 + math.sin(a - 0.4) * 11)], 2)
    elif gear == "rocks":
        for k in range(5):
            a = k * 1.257 + 0.3
            px, py = ix + math.cos(a) * r * 0.92, iy + math.sin(a) * r * 0.92
            pygame.draw.polygon(surf, (135, 125, 110), [(px - 6, py + 4), (px - 3, py - 6), (px + 5, py - 5), (px + 7, py + 3)])
            pygame.draw.polygon(surf, (60, 52, 44), [(px - 6, py + 4), (px - 3, py - 6), (px + 5, py - 5), (px + 7, py + 3)], 2)
    elif gear == "ice":
        for k in range(7):
            a = -math.pi + k * math.pi / 6
            bx, by = ix + math.cos(a) * r * 0.85, iy + math.sin(a) * r * 0.85
            pygame.draw.polygon(surf, (225, 245, 255), [(bx - math.sin(a) * 5, by + math.cos(a) * 5), (bx + math.sin(a) * 5, by - math.cos(a) * 5),
                                                        (bx + math.cos(a) * r * 0.55, by + math.sin(a) * r * 0.55)])
    elif gear == "crystal":
        bx, by = ix, iy - r - 10 + math.sin(t * 3) * 3
        pygame.draw.circle(surf, (140, 215, 255), (int(bx), int(by)), 9)
        pygame.draw.circle(surf, WHITE, (int(bx), int(by)), 9, 2)
        pygame.draw.circle(surf, WHITE, (int(bx - 3), int(by - 3)), 3)
        for k in range(3):
            a = t * 2 + k * 2.094
            pygame.draw.circle(surf, (180, 235, 255), (int(bx + math.cos(a) * 15), int(by + math.sin(a) * 6)), 2)
    elif gear == "runes":
        for k in range(4):
            a = t * 2.5 + k * math.pi / 2
            rx, ry = ix + math.cos(a) * (r + 9), iy + math.sin(a) * (r + 9)
            pygame.draw.rect(surf, (230, 200, 255), (rx - 4, ry - 4, 8, 8), 2)
    elif gear == "twinheads":
        heads = e.heads if e is not None else 2
        for k, off in enumerate((-1, 1)):
            hx, hy = ix + off * r * 0.5, iy - r * 0.85
            if heads == 1 and k == 1:
                pygame.draw.circle(surf, (120, 30, 30), (int(hx), int(hy + r * 0.2)), max(3, int(r * 0.2)))
                continue
            pygame.draw.circle(surf, _lt((115, 90, 80), 0.1), (int(hx), int(hy)), int(r * 0.45))
            pygame.draw.circle(surf, BLACK, (int(hx), int(hy)), int(r * 0.45), 2)
            draw_face(surf, hx, hy, r * 0.45, e.look if e is not None else face, "angry", 0.9 if heads == 1 else 0.4, t)
        if heads == 1:
            pygame.draw.circle(surf, (255, 60, 40), (ix, iy), int(r + 5 + 2 * math.sin(t * 12)), 2)



GUARDIAN_BOSS_TYPE = {"name": "Penjaga Gerbang", "shield": 1500, "shield_style": "plates", "color": (125, 135, 155), "radius": 50, "speed": 0.6, "hp": 3600, "xp": 170,
                      "dmg": 34, "gold": 160, "pickup_chance": 1.0, "armor": 900, "reduction": 0.15, "reward": 2}
MINIGUN_BOSS_TYPE = {"name": "Komandan Minigun", "shield": 1000, "shield_style": "plates", "color": (90, 110, 80), "radius": 48, "speed": 0.5, "hp": 3300, "xp": 170,
                     "dmg": 30, "gold": 160, "pickup_chance": 1.0, "armor": 800, "reward": 2}
EXEC_BOSS_TYPE = {"name": "Executioner", "shield": 900, "shield_style": "runic", "color": (55, 55, 70), "radius": 46, "speed": 0.75, "hp": 3000, "xp": 180,
                  "dmg": 38, "gold": 170, "pickup_chance": 1.0, "armor": 1200, "reduction": 0.25, "reward": 2}
FIRE_BOSS_TYPE = {"name": "Raja Api", "shield": 1200, "shield_style": "flame", "color": (255, 140, 40), "radius": 52, "speed": 0.7, "hp": 3500, "xp": 200,
                  "dmg": 34, "gold": 200, "pickup_chance": 1.0, "reward": 3}
SKEL_BOSS_TYPE = {"name": "Tengkorak Penembak", "shield": 1000, "shield_style": "bubble", "color": (228, 228, 208), "radius": 46, "speed": 0.7, "hp": 3300, "xp": 200,
                  "dmg": 30, "gold": 200, "pickup_chance": 1.0, "reward": 3}
FINAL_BOSS_TYPE = {"name": "Raja Inflasi", "color": (120, 30, 60), "radius": 320, "speed": 0.22, "hp": 75000000, "xp": 5000,
                   "dmg": 22, "gold": 9999, "pickup_chance": 1.0, "reward": 6}
BOSS_TYPES_BY_KIND = {"normal": BOSS_TYPE, "healer": HEALER_BOSS_TYPE, "necro": NECRO_BOSS_TYPE, "brute": BRUTE_BOSS_TYPE,
                      "guardian": GUARDIAN_BOSS_TYPE, "minigun": MINIGUN_BOSS_TYPE, "exec": EXEC_BOSS_TYPE,
                      "fire": FIRE_BOSS_TYPE, "skel": SKEL_BOSS_TYPE, "final": FINAL_BOSS_TYPE}

LORE = {
    "Merah": "Prajurit paling umum. Ia selalu datang berkelompok dan tak pernah belajar dari kawannya yang gugur.",
    "Hijau": "Lebih lincah dan bandel dari si Merah. Dulu ia penjaga ladang sebelum kabut sihir mengubahnya.",
    "Ungu": "Tubuhnya kecil tapi cepat. Konon ia lahir dari sisa ramuan penyihir yang gagal.",
    "Oranye": "Kuat dan keras kepala. Ia menyerbu apa pun yang bergerak.",
    "Cyan": "Makhluk dingin yang meluncur senyap di antara bayangan.",
    "Hitam": "Berat dan lamban, tetapi pukulannya mengguncang tanah.",
    "Pecah": "Begitu dikalahkan, tubuhnya terbelah menjadi dua pecahan yang lebih kecil.",
    "Zirah": "Ksatria berbaju besi tebal. Tebasan biasa hanya membuatnya berdenting.",
    "Necromancer": "Pemanggil tulang. Setiap beberapa detik ia membangkitkan tengkorak dari tanah.",
    "Penembak": "Memilih menembak dari jauh. Peluru sihirnya lambat tapi tak berhenti datang.",
    "Peledak": "Ia hidup hanya untuk satu hal: meledak di dekatmu.",
    "Raksasa": "Tinggi, kuat, dan sangat sulit dijatuhkan. Langkahnya terdengar dari jauh.",
    "Kelelawar": "Terbang zig-zag dalam kawanan. Sayapnya tajam, tubuhnya rapuh.",
    "Penerjang": "Membidik dengan garis merah lalu menerjang sekencang kilat.",
    "Prajurit Perisai": "Perisainya menahan serangan dari depan. Serang dari sisi atau belakang.",
    "Hantu Kedip": "Menghilang dan muncul di tempat lain. Tak ada yang tahu ia menuju ke mana.",
    "Penembak Laser": "Mengisi daya lalu menembakkan sinar panjang yang menembus segalanya.",
    "Ninja Bayangan": "Melompat dalam gelap dan melempar shuriken sebelum kau sempat menoleh.",
    "Pelempar Bom": "Gemar melempar bom ke tempatmu berdiri. Jangan diam di lingkaran merah.",
    "Penembak Jitu": "Sabar membidik, lalu menembak lurus ke arahmu dengan peluru cepat.",
    "Dukun Semangat": "Menyalakan semangat musuh di sekitarnya hingga bergerak lebih cepat.",
    "Racun Berjalan": "Meninggalkan genangan beracun di setiap langkahnya.",
    "Golem Baja": "Dipahat dari baja tua. Darah dan zirahnya nyaris tak ada habisnya.",
    "Raksasa Cepat": "Raksasa yang tak mau lagi lamban. Ia berlari seperti kuda.",
    "Penyambar Petir": "Memanggil petir yang menyambar dirinya dan kawan di sekitarnya hingga jadi cepat.",
    "Raksasa Super": "Lebih besar dari raksasa mana pun. Bayangannya saja menutupi layar kecil.",
    "Tengkorak Raksasa Cepat": "Tulang raksasa yang berlari tanpa lelah. Tak ada daging untuk diperlambat.",
    "Raksasa Pecah": "Mati sekali, lalu pecah jadi dua raksasa sedang, lalu pecah lagi menjadi musuh pecah biasa.",
    "Tanker Raksasa": "Berlapis zirah. Saat tumbang ia meledak dan melepas gas beracun beberapa detik.",
    "Tank Raksasa Cepat": "Baja berukuran raksasa yang ngebut. Zirahnya tebal dan sulit ditembus.",
    "Warden": "Penjaga kegelapan yang buta. Ia mendengar langkahmu lalu melepaskan sonic boom yang menembus zirah.",
    "Peniru Sihir": "Meniru jurus pemain secara acak: bola energi, meteor, laser, apa saja.",
    "Tank Besi": "Tank kecil berzirah. Pelan, tapi sulit dihancurkan.",
    "Raksasa Hantu": "Roh raksasa yang kadang menembus apa pun. Saat berwujud hantu, serangan nyaris tak melukainya.",
    "Algojo Raksasa": "Membawa palu penghancur. Hantamannya meninggalkan lingkaran maut.",
    "Raksasa Perisai": "Perisai besarnya menyerap serangan: perisai habis dulu, lalu zirah, baru darah. Kawan di belakangnya ikut terlindungi.",
    "Ksatria Raksasa": "Ksatria bertubuh raksasa dengan pedang lebar. Satu tebasan menyapu sepetak luas.",
    "Golem Es": "Dibentuk dari es abadi. Kebal pembekuan dan nyaris kebal serangan es.",
    "Raksasa Induk": "Tiap kali terluka, tubuhnya melahirkan tiga Raksasa Induk Mini sambil memulihkan diri.",
    "Raksasa Induk Mini": "Anak raksasa induk: kecil, gesit, dan selalu datang bertiga.",
    "Penyihir Kristal": "Melempar bola kristal ke satu musuh: jadi kuat, cepat, atau keduanya.",
    "Tanker Kepala Dua": "Berlari sangat cepat. Saat 'mati', hanya satu kepalanya yang putus; yang satu lagi mengamuk.",
    "Raksasa Shotgun": "Membawa senapan pemburu. Satu tembakan menyebar sembilan peluru.",
    "Ketua Raksasa": "Berteriak memberi perintah. Musuh di sekitarnya langsung bergerak cepat.",
    "Raksasa Minigun": "Lambat berjalan tapi memuntahkan hujan peluru setelah laras berputar.",
    "Raksasa Reaper": "Berjubah gelap dengan sabit. Ia memanggil tank-tank acak dari alam baka.",
    "Tengkorak": "Tulang belulang bangkitan. Rapuh, tetapi datang bergerombol.",
    "Pecahan": "Serpihan musuh Pecah. Kecil dan cepat.",
    "Tengkorak Raksasa": "Kerangka raksasa panggilan Necromancer.",
    "Raksasa Sedang": "Tahap tengah dari Raksasa Pecah. Akan pecah sekali lagi.",
    "Bos Biasa": "Pemimpin pasukan kecil. Menembakkan cincin peluru dan menerjang.",
    "Bos Penyembuh": "Menyembuhkan dirinya dan semua musuh sekitar, termasuk bos lain.",
    "Bos Necromancer": "Dalang sihir gelap. Memanggil tiga Tengkorak Raksasa dan menghujani sihir.",
    "Brute Berkepala Dua": "Dua kepala, satu amarah. Menghentak, melempar batu, melompat, dan meninju hingga terpental.",
    "Penjaga Gerbang": "Penjaga berzirah tebal dengan tombak suci. Memanggil meteor, petir, dan pasukan acak.",
    "Komandan Minigun": "Menyapu medan dengan minigun. Darah dan zirahnya tebal.",
    "Executioner": "Algojo berzirah penuh. Kapaknya dilempar lalu kembali ke tangannya.",
    "Raja Api": "Api oranye yang ganas. Saat terdesak, nyalanya berubah menjadi api biru yang lebih ganas.",
    "Tengkorak Penembak": "Koboi tengkorak: revolver di tangan, dan tas yang mengeluarkan minigun.",
    "Raja Inflasi": "Penguasa angka yang menggelembung. Dua tangan terbangnya menjatuhkan seluruh kemampuan musuh sekaligus.",
}
SKILL_LORE = {
    "MineWeapon": "Ranjau sihir yang ditanam diam-diam lalu meledak setelah jeda singkat.",
    "SpearWeapon": "Tombak cahaya yang melesat lurus dan menembus barisan musuh.",
    "ScytheWeapon": "Sabit hantu yang menebas melingkar di sekeliling penyihir.",
    "FireBirdWeapon": "Burung api yang mengejar musuh lalu meledak menjadi kobaran.",
    "PunchWeapon": "Tinju sihir pertama yang diajarkan pada setiap calon penyihir.",
    "OrbWeapon": "Bola energi murni yang mengejar musuh terdekat.",
    "AuraWeapon": "Lingkaran duri yang menyakiti siapa pun yang mendekat.",
    "ShockwaveWeapon": "Gelombang kejut yang menyapu musuh di sekelilingmu.",
    "ChainLightningWeapon": "Petir yang melompat dari satu musuh ke musuh berikutnya.",
    "MultiArrowWeapon": "Panah sihir yang menyebar seperti kipas.",
    "FireballWeapon": "Bola api yang mengorbit penyihir dan membakar siapa pun yang tersentuh.",
    "IceSpikeWeapon": "Duri es yang membekukan musuh sesaat.",
    "BoomerangWeapon": "Bumerang kayu yang selalu pulang ke tangan pemiliknya.",
    "PoisonCloudWeapon": "Awan racun menggenang di tanah dan menggerogoti musuh.",
    "LaserWeapon": "Sinar sihir terfokus yang menembus barisan musuh.",
    "MeteorWeapon": "Batu langit yang dipanggil menghantam target.",
    "KnifeWeapon": "Pisau terbang dilempar beruntun dengan presisi.",
    "TornadoWeapon": "Angin puyuh yang berjalan dan menyedot musuh.",
    "FireTrailWeapon": "Meninggalkan jejak api di setiap langkah penyihir.",
    "ShieldWeapon": "Perisai cahaya berputar melindungi dan melukai.",
    "GroundSpikeWeapon": "Duri batu muncul dari tanah di bawah kaki musuh.",
    "HomingSpiritWeapon": "Roh pemburu yang mengejar musuh sendirian.",
    "BounceOrbWeapon": "Bola pantul yang melenting dari musuh ke musuh.",
    "SkyLightningWeapon": "Kilat dari langit menyambar target acak.",
}
BADGES = [("welcome", "Selamat Datang", "Diberikan saat pertama kali memasuki dunia Witch Survivor.", None),
          ("tutorial", "Murid Teladan", "Selesaikan Tutorial dan kalahkan boss simulasinya.", "tutorial")]
for _k, _t in (("normal", "Bos Biasa"), ("healer", "Bos Penyembuh"), ("necro", "Bos Necromancer"),
               ("brute", "Brute Berkepala Dua"), ("guardian", "Penjaga Gerbang"), ("minigun", "Komandan Minigun"),
               ("exec", "Executioner"), ("fire", "Raja Api"), ("skel", "Tengkorak Penembak"), ("final", "Raja Inflasi")):
    BADGES.append((_k, "Pemburu " + _t, "Kalahkan %s." % _t, _k))


BADGE_COLORS = {"welcome": (80, 140, 255), "tutorial": (90, 220, 230), "normal": (110, 200, 110), "healer": (80, 220, 150),
                "necro": (170, 100, 230), "brute": (220, 150, 80), "guardian": (170, 180, 210), "minigun": (130, 170, 100),
                "exec": (190, 190, 215), "fire": (255, 140, 50), "skel": (225, 225, 205), "final": (255, 80, 110)}


BOSS_ORDER = ["normal", "healer", "necro", "brute", "guardian", "minigun", "exec", "fire", "skel", "final"]
BOSS_RANK = {"normal": "Pemimpin Pasukan", "healer": "Tabib Medan Perang", "necro": "Dalang Tulang", "brute": "Penghancur Berkepala Dua",
             "guardian": "Penjaga Gerbang", "minigun": "Komandan Garis Depan", "exec": "Algojo Berzirah", "fire": "Penguasa Api",
             "skel": "Koboi Tulang", "final": "Penguasa Terakhir Inflasi"}


def all_badges():
    out = list(BADGES[:2])
    for _i, _d in enumerate(BOSS_DEFS):
        out.append(("lvb_%d" % _i, "Penakluk " + _d["name"].title(), "Kalahkan %s (%s)." % (_d["name"].title(), _d.get("title", "Pengawal Arena")), "lvb_%d" % _i))
    rest = {b[0]: b for b in BADGES[2:]}
    for k in BOSS_ORDER:
        if k in rest:
            out.append(rest[k])
    return out


WEAPON_TAGS = {"PunchWeapon": ["Single", "Melee"], "OrbWeapon": ["Single", "Projectile"], "AuraWeapon": ["AOE", "DOT", "Aura"],
               "ShockwaveWeapon": ["AOE", "Knockback"], "ChainLightningWeapon": ["Chain", "Multi-target"],
               "MultiArrowWeapon": ["Pierce", "Projectile", "Spread"], "FireballWeapon": ["AOE", "Orbit"],
               "IceSpikeWeapon": ["Single", "Freeze", "Projectile"], "BoomerangWeapon": ["Pierce", "Returning"],
               "PoisonCloudWeapon": ["AOE", "DOT", "Zone"], "LaserWeapon": ["Pierce", "Beam"], "MeteorWeapon": ["AOE", "Burst"],
               "KnifeWeapon": ["Pierce", "Projectile", "Rapid"], "TornadoWeapon": ["AOE", "Pull", "Moving"],
               "FireTrailWeapon": ["AOE", "DOT", "Zone"], "ShieldWeapon": ["Defense", "Orbit"], "GroundSpikeWeapon": ["AOE", "Burst"],
               "HomingSpiritWeapon": ["Homing", "Pierce"], "BounceOrbWeapon": ["Bounce", "Projectile"], "SkyLightningWeapon": ["Single", "Random", "Burst"],
               "MineWeapon": ["AOE", "Zone", "Burst"], "SpearWeapon": ["Pierce", "Projectile"], "ScytheWeapon": ["AOE", "Melee", "Orbit"],
               "FireBirdWeapon": ["Homing", "AOE", "Projectile"]}
AVATAR_SKILL_TAGS = {"glacia": ["AOE", "Freeze"], "zephyr": ["Burst", "Chain"], "venna": ["AOE", "DOT"], "terra": ["Defense", "AOE"],
                     "kage": ["Dash", "Burst"], "lumi": ["Heal", "AOE"], "pyra": ["AOE", "Burst"], "morta": ["Heal", "AOE"], "badang": ["Pierce", "Line"], "rez": ["Dash", "Pierce"], "black_hole": ["AOE", "Pull", "DOT"], "dead_strong": ["Buff", "AOE"],
                     "string_move": ["Chain", "Line"], "fast_light": ["Buff", "Speed"], "yomatoda": ["AOE", "Burst"],
                     "sruken": ["AOE", "Projectile"], "muscle_skrim": ["AOE", "Defense"], "brudal_mongskter": ["Buff", "AOE"]}


def enemy_class(kind):
    """Kelas/tipe musuh: Normal, Cepat, Lambat, Tank, Raksasa, Jarak Jauh, Pendukung, Terbang, ..."""
    out = []
    tank = kind.get("cls") == "Tank" or kind.get("armor", 0) >= 150 or kind.get("shield") or kind.get("reduction", 0) >= 0.15
    ranged = any(kind.get(f) for f in ("shooter", "sniper", "laser", "bomber", "minigunner", "shotgun", "warden", "mimic", "ninja")) \
        or any(a["t"] in ("shoot", "lob", "beam", "bolt", "spit", "cone", "ring") for a in kind.get("abil", []))
    support = any(kind.get(f) for f in ("healer", "buffer", "chief", "crystal_mage", "reaper", "thunder", "summoner", "mother", "necro")) \
        or any(a["t"] in ("summon", "healaoe") for a in kind.get("abil", []))
    if kind.get("shape") == "bat":
        out.append("Terbang")
    if kind["radius"] >= 30 or kind.get("shape") == "giant":
        out.append("Raksasa")
    if tank:
        out.append("Tank")
    if ranged:
        out.append("Jarak Jauh")
    if support:
        out.append("Pendukung")
    if kind["speed"] >= 1.7:
        out.append("Cepat")
    elif kind["speed"] <= 0.6 and "Raksasa" not in out:
        out.append("Lambat")
    elif kind["speed"] <= 0.55:
        out.append("Lambat")
    if kind.get("elem"):
        out.append("Elemen")
    if not out:
        out.append("Normal")
    return " / ".join(out)


def enemy_flags_text(kind):
    """Daftar kemampuan singkat dari penanda pada data musuh."""
    m = {"summoner": "memanggil tengkorak", "shooter": "menembak", "healer": "menyembuhkan", "dasher": "menerjang",
         "teleporter": "berteleportasi", "laser": "menembak laser", "ninja": "melempar shuriken", "bomber": "melempar bom",
         "sniper": "menembak jitu", "buffer": "mempercepat kawan", "toxic": "meninggalkan racun", "slam": "menghantam tanah",
         "thunder": "petir mempercepat", "explodes": "meledak saat mati", "warden": "sonic boom", "mimic": "meniru skill pemain",
         "hammer": "palu penghancur", "protector": "perisai pelindung", "slash": "tebasan pedang", "mother": "melahirkan 3 mini tiap terluka + sembuh",
         "crystal_mage": "buff kristal", "shotgun": "tembakan menyebar", "chief": "memberi perintah cepat",
         "minigunner": "minigun", "reaper": "memanggil tank", "ethereal": "menembus (hantu)", "ice_immune": "kebal es",
         "two_heads": "dua kepala", "splits": "terbelah", "necro": "sihir & panggil tengkorak", "brute": "hentak/lompat/tinju"}
    out = [v for k, v in m.items() if kind.get(k)]
    if kind.get("split_child"):
        out.append("pecah bertahap")
    if kind.get("elem"):
        out.insert(0, "elemen " + kind["elem"].replace("ice", "es").replace("fire", "api").replace("thunder", "petir").replace("rock", "batu"))
        names = {"trail": "jejak", "aura": "aura", "spit": "semburan", "shoot": "tembakan", "nova": "gelombang", "bolt": "petir",
                 "lob": "lemparan", "cone": "semburan api", "beam": "sinar", "roll": "menggulung", "ring": "cincin peluru",
                 "blink": "berteleportasi", "summon": "memanggil", "healaoe": "menyembuhkan sekitar"}
        out.append("serangan: " + ", ".join(sorted({names.get(a["t"], a["t"]) for a in kind["abil"]})))
    if kind.get("armor"):
        out.append("berzirah")
    return out


EL_COL = {"ice": (170, 225, 255), "fire": (255, 120, 40), "toxic": (110, 200, 60), "thunder": (255, 240, 90), "rock": (150, 138, 120)}
EL_GEAR = {"ice": "ice", "fire": "flames", "toxic": "bubbles", "thunder": "sparks", "rock": "rocks"}
EL_NAME = {"ice": "Es", "fire": "Api", "toxic": "Racun", "thunder": "Petir", "rock": "Batu"}


def _el(elem, name, radius, speed, hp, xp, dmg, min_lv, cost, shape, abil, **kw):
    col = kw.pop("color", EL_COL[elem])
    d = _nt(name, col, radius, speed, hp, xp, dmg, int(8 + cost * 2), min_lv, shape=shape, gear=EL_GEAR[elem],
            elem=elem, mode="inflation", abil=abil, pickup_chance=0.1 + cost * 0.01, **kw)
    if elem == "ice":
        d["ice_immune"] = True
    ENEMY_COST[name] = cost
    return d


ELEM_TYPES = [
    _el("ice", "Serigala Es", 14, 2.2, 75, 14, 14, 3, 2, "triangle",
        [{"t": "trail", "cd": (0.45, 0.7), "col": (150, 215, 255), "r": 42, "dur": 3.0, "slow": True, "dm": 0.4}]),
    _el("ice", "Penyihir Es", 15, 0.8, 115, 20, 12, 5, 4, "circle",
        [{"t": "shoot", "cd": (2.6, 3.4), "n": 3, "sp": 11, "spd": 4.6, "style": "ice", "col": (170, 225, 255), "r": 8, "slow": True, "range": 650}]),
    _el("ice", "Pembeku", 17, 0.7, 170, 26, 12, 8, 5, "circle",
        [{"t": "nova", "cd": (4.5, 6.0), "r": 270, "col": (170, 225, 255), "slow": True, "dm": 0.7, "range": 330}]),
    _el("ice", "Raksasa Salju", 40, 0.55, 540, 58, 24, 15, 13, "giant",
        [{"t": "lob", "cd": (3.6, 4.6), "n": 3, "spread": 140, "r": 75, "col": (200, 235, 255), "warn": 1.2, "dm": 0.9},
         {"t": "aura", "cd": (3.0, 3.6), "r": 140, "dur": 2.4, "col": (190, 230, 255), "slow": True, "dm": 0.3}], armor=120),
    _el("fire", "Imp Api", 13, 2.0, 62, 13, 14, 3, 2, "triangle",
        [{"t": "trail", "cd": (0.5, 0.8), "col": (255, 120, 40), "r": 38, "dur": 2.2, "dm": 0.45}]),
    _el("fire", "Penyembur Api", 16, 0.8, 145, 22, 14, 6, 4, "circle",
        [{"t": "cone", "cd": (3.2, 4.0), "n": 3, "length": 270, "width": 62, "col": (255, 130, 40), "range": 330, "dm": 0.9}]),
    _el("fire", "Kelelawar Api", 10, 3.0, 42, 10, 10, 4, 2, "bat",
        [{"t": "shoot", "cd": (2.6, 3.4), "n": 1, "sp": 0, "spd": 4.8, "style": "fire", "col": (255, 130, 40), "r": 9, "range": 600}]),
    _el("fire", "Golem Magma", 34, 0.5, 620, 55, 24, 11, 11, "giant", [{"t": "aura", "cd": (3.5, 4.5), "r": 95, "dur": 2.0, "col": (255, 110, 30), "dm": 0.35}],
        armor=200, explodes=True, explode_radius=120, explode_damage=22, gas=(140, 5.0), gas_col=(255, 120, 40), color=(190, 70, 30)),
    _el("fire", "Raksasa Lava", 44, 0.5, 740, 72, 28, 18, 16, "giant",
        [{"t": "lob", "cd": (3.8, 5.0), "n": 4, "spread": 220, "r": 80, "col": (255, 120, 40), "warn": 1.3, "dm": 1.0}],
        gas=(150, 5.0), gas_col=(255, 120, 40), explodes=True, explode_radius=130, explode_damage=26, color=(150, 50, 25)),
    _el("toxic", "Kodok Racun", 14, 1.4, 85, 14, 12, 3, 2, "circle",
        [{"t": "trail", "cd": (0.6, 0.9), "col": (110, 200, 60), "r": 40, "dur": 4.0, "dm": 0.4}]),
    _el("toxic", "Penyembur Racun", 16, 0.8, 155, 22, 12, 6, 4, "circle",
        [{"t": "spit", "cd": (3.8, 4.8), "r": 95, "dur": 3.5, "col": (110, 200, 60), "range": 620, "dm": 0.35}]),
    _el("toxic", "Ular Beracun", 12, 2.0, 66, 14, 12, 5, 3, "diamond",
        [{"t": "shoot", "cd": (2.2, 3.0), "n": 3, "sp": 14, "spd": 5.0, "style": "orb", "col": (110, 220, 70), "r": 7, "range": 560}]),
    _el("toxic", "Jamur Beracun", 18, 0.6, 130, 20, 10, 7, 4, "circle", [{"t": "aura", "cd": (3.0, 4.0), "r": 90, "dur": 2.5, "col": (140, 210, 70), "dm": 0.3}],
        explodes=True, explode_radius=90, explode_damage=10, gas=(130, 5.0), gas_col=(110, 200, 60)),
    _el("toxic", "Raksasa Racun", 42, 0.5, 620, 62, 24, 14, 13, "giant",
        [{"t": "aura", "cd": (2.6, 3.2), "r": 160, "dur": 2.8, "col": (110, 200, 60), "dm": 0.45}], gas=(170, 6.0), gas_col=(110, 200, 60), explodes=True,
        explode_radius=100, explode_damage=14),
    _el("thunder", "Bola Petir", 12, 2.4, 55, 13, 12, 4, 3, "circle",
        [{"t": "bolt", "cd": (2.8, 3.6), "n": 1, "spread": 0, "warn": 0.85, "dm": 0.9, "range": 520}]),
    _el("thunder", "Elang Petir", 11, 2.8, 62, 14, 12, 6, 3, "bat",
        [{"t": "beam", "cd": (3.0, 4.0), "length": 480, "width": 22, "col": (255, 240, 90), "warn": 0.7, "dm": 0.8, "range": 520}]),
    _el("thunder", "Penyetrum", 15, 0.9, 135, 22, 12, 9, 5, "diamond",
        [{"t": "bolt", "cd": (3.5, 4.5), "n": 3, "spread": 90, "warn": 0.8, "dm": 0.9, "range": 480}]),
    _el("thunder", "Raksasa Badai", 42, 0.55, 600, 66, 26, 16, 14, "giant",
        [{"t": "bolt", "cd": (3.6, 4.6), "n": 6, "spread": 240, "warn": 0.9, "dm": 0.9},
         {"t": "nova", "cd": (6.0, 7.0), "r": 300, "col": (255, 240, 90), "dm": 0.7, "range": 380}], armor=100),
    _el("rock", "Pelempar Batu", 16, 0.7, 165, 22, 14, 5, 4, "circle",
        [{"t": "shoot", "cd": (3.0, 3.8), "n": 1, "sp": 0, "spd": 4.4, "style": "rock", "col": (150, 138, 120), "r": 12, "range": 640}]),
    _el("rock", "Armadillo Batu", 17, 0.9, 230, 28, 16, 7, 5, "circle", [{"t": "roll", "cd": (4.5, 6.0), "range": 520}], armor=150),
    _el("rock", "Golem Batu", 36, 0.5, 470, 48, 22, 10, 11, "giant",
        [{"t": "lob", "cd": (3.4, 4.4), "n": 2, "spread": 120, "r": 90, "col": (150, 138, 120), "warn": 1.2, "dm": 1.0}], armor=260, reduction=0.2),
    _el("rock", "Raksasa Batu", 46, 0.45, 820, 78, 30, 20, 17, "giant",
        [{"t": "nova", "cd": (5.0, 6.0), "r": 340, "col": (150, 138, 120), "dm": 0.9, "range": 330},
         {"t": "lob", "cd": (4.0, 5.0), "n": 4, "spread": 240, "r": 85, "col": (150, 138, 120), "warn": 1.2, "dm": 1.0}], armor=220),
]
NEW_ENEMY_TYPES += ELEM_TYPES
ALL_SPAWN_TYPES = ENEMY_TYPES + ADVANCED_ENEMY_TYPES + NEW_ENEMY_TYPES
for _k in ALL_SPAWN_TYPES + [SPLIT_MID_TYPE]:
    if _k["name"] in GIANT_VARIANTS and "variant" not in _k:
        _k["variant"] = GIANT_VARIANTS[_k["name"]]
MINIGUN_GIANT_TYPE["slow"] = True
LORE.update({
    "Serigala Es": "Serigala dari gletser. Jejaknya membekukan tanah dan memperlambat langkahmu.",
    "Penyihir Es": "Menembakkan duri es yang membuatmu terlambat. Kebal beku.",
    "Pembeku": "Melepas gelombang dingin yang menyapu sekeliling.",
    "Raksasa Salju": "Melempar bola salju raksasa dan menebar kabut dingin.",
    "Imp Api": "Iblis kecil yang berlari sambil meninggalkan api.",
    "Penyembur Api": "Menyemburkan api dalam kipas pendek. Jangan dekat-dekat.",
    "Kelelawar Api": "Kelelawar bersayap bara yang meludahkan bola api.",
    "Golem Magma": "Batu yang masih membara. Saat hancur ia meledak dan meninggalkan genangan api.",
    "Raksasa Lava": "Menghujani tanah dengan meteor lava. Saat tumbang, apinya menggenang.",
    "Kodok Racun": "Melompat riang sambil meninggalkan genangan racun.",
    "Penyembur Racun": "Memuntahkan awan racun tepat di tempatmu berdiri.",
    "Ular Beracun": "Menyemburkan tiga peluru racun sekaligus.",
    "Jamur Beracun": "Jamur raksasa yang menyebar spora dan meledak jadi kabut racun.",
    "Raksasa Racun": "Tubuhnya mengepulkan gas beracun tanpa henti.",
    "Bola Petir": "Bola listrik lincah yang menyambar tempatmu berdiri.",
    "Elang Petir": "Elang listrik yang menembakkan garis petir lurus.",
    "Penyetrum": "Memanggil tiga sambaran petir di sekitarmu.",
    "Raksasa Badai": "Membawa badai sendiri: hujan petir dan gelombang listrik.",
    "Pelempar Batu": "Melempar batu besar dari kejauhan.",
    "Armadillo Batu": "Menggulung diri dan menerjang sangat cepat. Zirahnya keras.",
    "Golem Batu": "Melempar bongkahan batu yang jatuh dari langit.",
    "Raksasa Batu": "Menghentak bumi dan menjatuhkan hujan batu.",
})

def _st(name, color, radius, speed, hp, xp, dmg, min_lv, cost, shape, abil, variant=None, gear=None, mode=None, **kw):
    d = _nt(name, color, radius, speed, hp, xp, dmg, int(10 + cost * 2), min_lv, shape=shape, abil=abil, pickup_chance=0.2, **kw)
    if variant:
        d["variant"] = variant
    if gear:
        d["gear"] = gear
    if mode:
        d["mode"] = mode
    ENEMY_COST[name] = cost
    return d


SPIDER_MINI_TYPE = _nt("Laba-laba Kecil", (75, 55, 90), 11, 2.3, 70, 8, 10, 6, 99, shape="spider", pickup_chance=0.03,
                       abil=[{"t": "trail", "cd": (0.9, 1.3), "col": (110, 200, 60), "r": 30, "dur": 2.5, "dm": 0.3}])
ENEMY_COST["Laba-laba Kecil"] = 2

STRONG_TYPES = [
    _st("Pembantai Baja", (120, 125, 145), 40, 1.1, 950, 80, 34, 24, 17, "giant",
        [{"t": "nova", "cd": (4.5, 5.5), "r": 320, "col": (200, 205, 225), "dm": 0.9, "range": 330}, {"t": "roll", "cd": (5.0, 6.5), "range": 600}],
        "plated", armor=520, cls="Tank"),
    _st("Kapten Bayangan", (60, 50, 90), 18, 1.6, 420, 60, 28, 22, 14, "ninja",
        [{"t": "blink", "cd": (4.0, 5.0), "d": 260}, {"t": "ring", "cd": (3.0, 3.8), "n": 10, "spd": 4.4, "col": (150, 120, 220), "style": "shuriken", "r": 8},
         {"t": "shoot", "cd": (2.6, 3.2), "n": 5, "sp": 9, "spd": 6.2, "style": "knife", "col": (230, 232, 245), "r": 6, "range": 560}]),
    _st("Pendeta Gelap", (110, 60, 150), 20, 0.9, 520, 70, 22, 26, 16, "circle",
        [{"t": "healaoe", "cd": (4.0, 5.0), "r": 340, "pct": 0.12}, {"t": "bolt", "cd": (3.4, 4.2), "n": 3, "spread": 120, "warn": 0.9, "dm": 1.0}], gear="runes"),
    _st("Naga Kecil", (200, 90, 60), 30, 1.3, 760, 80, 30, 30, 18, "giant",
        [{"t": "cone", "cd": (3.2, 4.0), "n": 5, "length": 320, "width": 66, "col": (255, 130, 40), "range": 380, "dm": 1.0},
         {"t": "shoot", "cd": (2.8, 3.4), "n": 3, "sp": 12, "spd": 5.0, "style": "fire", "col": (255, 130, 40), "r": 10, "range": 640}], "horned"),
    _st("Ratu Laba-laba", (60, 40, 70), 34, 0.9, 880, 85, 28, 28, 18, "spider",
        [{"t": "summon", "cd": (5.0, 6.0), "kind": "Laba-laba Kecil", "n": 3}, {"t": "spit", "cd": (3.4, 4.2), "r": 100, "dur": 3.5, "col": (110, 200, 60), "range": 620, "dm": 0.4}]),
    _st("Golem Kristal", (130, 200, 245), 38, 0.9, 1150, 95, 30, 34, 20, "giant",
        [{"t": "ring", "cd": (3.4, 4.2), "n": 14, "spd": 4.0, "col": (170, 230, 255), "style": "ice", "r": 8}], "bulwark", armor=700, reduction=0.3, cls="Tank"),
    _st("Pemburu Malam", (30, 30, 50), 16, 2.2, 480, 70, 30, 32, 15, "ninja",
        [{"t": "blink", "cd": (3.0, 4.0), "d": 220}, {"t": "roll", "cd": (3.5, 4.5), "range": 520}]),
    _st("Kolosus", (150, 110, 80), 56, 0.9, 2600, 150, 44, 40, 28, "giant",
        [{"t": "nova", "cd": (5.0, 6.0), "r": 380, "col": (220, 170, 120), "dm": 1.1, "range": 400},
         {"t": "lob", "cd": (3.8, 4.8), "n": 4, "spread": 240, "r": 90, "col": (200, 150, 100), "warn": 1.2, "dm": 1.1},
         {"t": "summon", "cd": (8.0, 9.0), "kind": "Tengkorak Raksasa Cepat", "n": 1}], "hulk", armor=600),
    _st("Penguasa Bayangan", (40, 30, 70), 36, 1.0, 2100, 140, 40, 45, 26, "ghost",
        [{"t": "blink", "cd": (4.5, 5.5), "d": 280}, {"t": "ring", "cd": (3.0, 3.8), "n": 16, "spd": 4.2, "col": (150, 100, 220), "style": "spirit", "r": 9},
         {"t": "summon", "cd": (7.0, 8.0), "kind": "Hantu Kedip", "n": 2}]),
    _st("Titan Perang", (110, 80, 60), 62, 0.9, 3400, 180, 50, 50, 32, "giant",
        [{"t": "lob", "cd": (3.4, 4.2), "n": 6, "spread": 300, "r": 95, "col": (220, 140, 80), "warn": 1.2, "dm": 1.2},
         {"t": "nova", "cd": (5.0, 6.0), "r": 420, "col": (220, 160, 100), "dm": 1.2, "range": 440}, {"t": "roll", "cd": (6.0, 7.0), "range": 700}],
        "horned", armor=900, cls="Tank"),
    _st("Archon Cahaya", (255, 240, 170), 30, 1.1, 1900, 150, 38, 55, 26, "ghost",
        [{"t": "beam", "cd": (3.0, 3.8), "length": 700, "width": 36, "col": (255, 245, 170), "warn": 0.8, "dm": 1.0, "range": 700},
         {"t": "bolt", "cd": (3.6, 4.4), "n": 5, "spread": 220, "warn": 0.9, "dm": 1.0}]),
    _st("Malaikat Maut", (50, 40, 80), 54, 1.0, 3000, 200, 52, 60, 34, "giant",
        [{"t": "summon", "cd": (6.0, 7.0), "kind": "Tank Raksasa Cepat", "n": 2}, {"t": "nova", "cd": (5.0, 6.0), "r": 400, "col": (160, 110, 230), "dm": 1.2, "range": 420},
         {"t": "healaoe", "cd": (7.0, 8.0), "r": 420, "pct": 0.1}], "hunch", gear="scythe"),
]
INFL_TYPES = [
    _st("Penguasa Es", (190, 235, 255), 52, 1.0, 1400, 110, 36, 20, 22, "giant",
        [{"t": "nova", "cd": (4.0, 5.0), "r": 340, "col": (190, 235, 255), "slow": True, "dm": 0.9, "range": 380},
         {"t": "lob", "cd": (3.6, 4.4), "n": 4, "spread": 220, "r": 85, "col": (200, 235, 255), "warn": 1.2, "dm": 1.0}], "hulk", mode="inflation", ice_immune=True, armor=300),
    _st("Phoenix Muda", (255, 150, 60), 22, 2.4, 620, 80, 30, 22, 16, "bat",
        [{"t": "shoot", "cd": (2.4, 3.0), "n": 5, "sp": 8, "spd": 5.2, "style": "fire", "col": (255, 130, 40), "r": 9, "range": 650}, {"t": "blink", "cd": (5.0, 6.0), "d": 300}], mode="inflation", gear="flames"),
    _st("Raja Racun", (110, 190, 70), 48, 0.95, 1500, 110, 34, 25, 22, "giant",
        [{"t": "aura", "cd": (2.6, 3.2), "r": 190, "dur": 3.0, "col": (110, 200, 60), "dm": 0.5}, {"t": "spit", "cd": (3.2, 4.0), "r": 105, "dur": 3.5, "col": (110, 200, 60), "range": 650, "dm": 0.4},
         {"t": "summon", "cd": (7.0, 8.0), "kind": "Kodok Racun", "n": 3}], "hunch", mode="inflation", gear="bubbles"),
    _st("Dewa Petir", (255, 240, 120), 46, 1.2, 1500, 120, 36, 28, 22, "giant",
        [{"t": "bolt", "cd": (3.0, 3.8), "n": 8, "spread": 260, "warn": 0.85, "dm": 1.0}, {"t": "nova", "cd": (5.5, 6.5), "r": 340, "col": (255, 240, 100), "dm": 0.9, "range": 380}],
        "cyclops", mode="inflation", gear="sparks"),
    _st("Raja Batu", (150, 140, 120), 54, 0.9, 1900, 130, 40, 31, 24, "giant",
        [{"t": "lob", "cd": (3.4, 4.2), "n": 6, "spread": 280, "r": 92, "col": (150, 138, 120), "warn": 1.2, "dm": 1.1}, {"t": "roll", "cd": (5.5, 6.5), "range": 620}],
        "hulk", mode="inflation", gear="rocks", armor=700, reduction=0.2, cls="Tank"),
    _st("Ratu Salju", (210, 240, 255), 30, 1.3, 1300, 110, 32, 35, 20, "ghost",
        [{"t": "shoot", "cd": (2.8, 3.4), "n": 7, "sp": 10, "spd": 5.0, "style": "ice", "col": (180, 230, 255), "r": 8, "slow": True, "range": 650},
         {"t": "nova", "cd": (5.0, 6.0), "r": 320, "col": (190, 235, 255), "slow": True, "dm": 0.8, "range": 360},
         {"t": "summon", "cd": (8.0, 9.0), "kind": "Serigala Es", "n": 3}], mode="inflation", ice_immune=True, gear="ice"),
    _st("Iblis Magma", (230, 90, 30), 50, 1.0, 2200, 150, 42, 38, 26, "giant",
        [{"t": "cone", "cd": (3.0, 3.8), "n": 5, "length": 340, "width": 70, "col": (255, 120, 40), "range": 400, "dm": 1.1},
         {"t": "lob", "cd": (3.6, 4.4), "n": 5, "spread": 240, "r": 88, "col": (255, 120, 40), "warn": 1.2, "dm": 1.1}], "horned", mode="inflation", gear="flames",
        explodes=True, explode_radius=140, explode_damage=30, gas=(160, 6.0), gas_col=(255, 120, 40)),
    _st("Hantu Wabah", (140, 200, 110), 28, 1.4, 1100, 100, 30, 41, 19, "ghost",
        [{"t": "spit", "cd": (2.8, 3.4), "r": 100, "dur": 4.0, "col": (130, 210, 80), "range": 640, "dm": 0.4}, {"t": "aura", "cd": (3.0, 3.6), "r": 130, "dur": 2.6, "col": (130, 210, 80), "dm": 0.4},
         {"t": "summon", "cd": (7.0, 8.0), "kind": "Jamur Beracun", "n": 2}], mode="inflation", gear="bubbles"),
    _st("Elemental Badai", (255, 245, 140), 36, 1.4, 1800, 130, 36, 44, 24, "diamond",
        [{"t": "bolt", "cd": (2.8, 3.4), "n": 10, "spread": 300, "warn": 0.85, "dm": 0.9}, {"t": "beam", "cd": (3.4, 4.2), "length": 760, "width": 30, "col": (255, 245, 110), "warn": 0.7, "dm": 1.0, "range": 700}],
        mode="inflation", gear="sparks"),
    _st("Gargoyle Granit", (110, 105, 110), 44, 1.1, 2600, 150, 40, 47, 25, "giant",
        [{"t": "lob", "cd": (3.4, 4.2), "n": 5, "spread": 260, "r": 92, "col": (140, 135, 140), "warn": 1.2, "dm": 1.1}, {"t": "roll", "cd": (4.5, 5.5), "range": 680}],
        "plated", mode="inflation", gear="rocks", armor=1100, reduction=0.35, cls="Tank"),
    _st("Kaisar Es Abadi", (170, 225, 255), 62, 1.0, 3600, 200, 50, 52, 32, "giant",
        [{"t": "nova", "cd": (4.0, 5.0), "r": 420, "col": (190, 235, 255), "slow": True, "dm": 1.1, "range": 450},
         {"t": "lob", "cd": (3.4, 4.2), "n": 6, "spread": 300, "r": 95, "col": (200, 235, 255), "warn": 1.2, "dm": 1.1},
         {"t": "shoot", "cd": (3.0, 3.6), "n": 9, "sp": 8, "spd": 5.2, "style": "ice", "col": (180, 230, 255), "r": 9, "slow": True, "range": 700}],
        "hulk", mode="inflation", ice_immune=True, armor=800, gear="ice"),
    _st("Raja Neraka", (200, 40, 30), 60, 1.0, 4200, 220, 54, 58, 34, "giant",
        [{"t": "cone", "cd": (2.8, 3.4), "n": 7, "length": 380, "width": 74, "col": (255, 100, 40), "range": 440, "dm": 1.2},
         {"t": "lob", "cd": (3.2, 4.0), "n": 7, "spread": 320, "r": 92, "col": (255, 110, 40), "warn": 1.2, "dm": 1.2},
         {"t": "ring", "cd": (3.4, 4.0), "n": 18, "spd": 4.4, "col": (255, 120, 40), "style": "fire", "r": 9}, {"t": "summon", "cd": (8.0, 9.0), "kind": "Imp Api", "n": 4}],
        "horned", mode="inflation", gear="flames"),
    _st("Maha Racun", (90, 170, 60), 64, 0.9, 4600, 230, 50, 64, 34, "giant",
        [{"t": "aura", "cd": (2.4, 3.0), "r": 230, "dur": 3.2, "col": (110, 200, 60), "dm": 0.6}, {"t": "spit", "cd": (2.8, 3.4), "r": 120, "dur": 4.0, "col": (110, 200, 60), "range": 700, "dm": 0.5},
         {"t": "summon", "cd": (6.0, 7.0), "kind": "Jamur Beracun", "n": 3}], "hunch", mode="inflation", gear="bubbles", gas=(220, 7.0), gas_col=(110, 200, 60), explodes=True,
        explode_radius=120, explode_damage=24),
    _st("Murka Langit", (255, 235, 120), 58, 1.3, 5200, 250, 54, 69, 36, "giant",
        [{"t": "bolt", "cd": (2.6, 3.2), "n": 12, "spread": 340, "warn": 0.85, "dm": 1.0}, {"t": "nova", "cd": (5.0, 6.0), "r": 420, "col": (255, 240, 100), "dm": 1.2, "range": 440},
         {"t": "beam", "cd": (3.4, 4.0), "length": 820, "width": 38, "col": (255, 245, 110), "warn": 0.7, "dm": 1.1, "range": 760}, {"t": "blink", "cd": (6.0, 7.0), "d": 320}],
        "cyclops", mode="inflation", gear="sparks", armor=900),
    _st("Penjaga Inflasi", (255, 200, 80), 60, 1.2, 6500, 300, 58, 62, 28, "giant",
        [{"t": "ring", "cd": (2.8, 3.4), "n": 20, "spd": 4.6, "col": (255, 210, 90), "style": "orb", "r": 9}, {"t": "blink", "cd": (5.0, 6.0), "d": 300},
         {"t": "summon", "cd": (7.0, 8.0), "kind": "Golem Batu", "n": 1}, {"t": "lob", "cd": (3.4, 4.0), "n": 8, "spread": 340, "r": 95, "col": (255, 200, 80), "warn": 1.2, "dm": 1.2}],
        "plated", mode="inflation", armor=1400, reduction=0.25, cls="Tank"),
]
NEW_ENEMY_TYPES += STRONG_TYPES + INFL_TYPES + [SPIDER_MINI_TYPE]
ALL_SPAWN_TYPES = ENEMY_TYPES + ADVANCED_ENEMY_TYPES + NEW_ENEMY_TYPES
KIND_BY_NAME = {k["name"]: k for k in ALL_SPAWN_TYPES + [SKELETON_TYPE, GSKEL_TYPE, SPLIT_MID_TYPE, SPLIT_CHILD_TYPE, MOTHER_MINI_TYPE]}
LORE.update({
    "Pembantai Baja": "Raksasa berzirah yang menyapu medan dengan gelombang kejut lalu menggulung ke arahmu.",
    "Kapten Bayangan": "Ninja elit: menghilang, muncul di dekatmu, lalu menghujani shuriken dan pisau.",
    "Pendeta Gelap": "Menyembuhkan semua kawan di sekitarnya sambil memanggil petir.",
    "Naga Kecil": "Anak naga yang menyemburkan api dalam kipas dan melontarkan bola api.",
    "Ratu Laba-laba": "Memanggil anak-anak laba-labanya dan menyemburkan awan racun.",
    "Laba-laba Kecil": "Anak Ratu Laba-laba. Cepat, rapuh, dan meninggalkan jejak racun.",
    "Golem Kristal": "Tubuh kristalnya nyaris tak tertembus; ia menembakkan cincin pecahan es.",
    "Pemburu Malam": "Berkedip lalu menerjang tanpa suara. Hindari saat ia hilang.",
    "Kolosus": "Raksasa raksasa. Hentakan, hujan batu, dan tengkorak cepat panggilannya.",
    "Penguasa Bayangan": "Muncul dari kegelapan, memanggil hantu dan menebar cincin roh.",
    "Titan Perang": "Panglima raksasa berzirah tebal: hujan lemparan, gelombang kejut, dan terjangan.",
    "Archon Cahaya": "Utusan cahaya yang memanah dengan sinar dan menyambar dengan petir.",
    "Malaikat Maut": "Memanggil tank dari alam baka dan menyembuhkan sekutunya.",
    "Penguasa Es": "Penguasa gletser. Gelombang dinginnya memperlambatmu. Kebal beku.",
    "Phoenix Muda": "Burung api lincah yang berkedip dan menembakkan lima bola api.",
    "Raja Racun": "Aura racun luas, semburan gas, dan kodok-kodok panggilan.",
    "Dewa Petir": "Menjatuhkan delapan sambaran sekaligus lalu melepas gelombang listrik.",
    "Raja Batu": "Raksasa batu: hujan bongkahan dan terjangan menggulung.",
    "Ratu Salju": "Hantu es yang menembakkan duri pelambat dan memanggil serigala salju.",
    "Iblis Magma": "Lima semburan api dan hujan lava; saat tumbang, apinya menggenang.",
    "Hantu Wabah": "Mengepung dengan racun dan memanggil jamur peledak.",
    "Elemental Badai": "Badai hidup: sepuluh petir sekaligus dan sinar listrik panjang.",
    "Gargoyle Granit": "Pelindung granit nyaris tak tergores; melempar batu dan menggulung.",
    "Kaisar Es Abadi": "Kaisar es: gelombang beku raksasa, hujan es, dan tembakan pelambat.",
    "Raja Neraka": "Penguasa api neraka: kipas api, hujan lava, cincin api, dan imp-imp panggilan.",
    "Maha Racun": "Pusat wabah: aura gas raksasa dan jamur-jamur peledak.",
    "Murka Langit": "Dua belas petir, sinar, dan teleportasi. Hanya muncul menjelang akhir Inflasi.",
    "Penjaga Inflasi": "Penjaga terakhir sebelum Raja Inflasi: cincin emas, teleportasi, dan golem panggilan.",
})

class Enemy:
    # Status BAKAR / RACUN / UAP (default level kelas, jadi tidak perlu diinisialisasi satu-satu)
    burn_t = 0.0
    burn_dps = 0.0
    burn_tick = 0.0
    poison_t = 0.0
    poison_dps = 0.0
    poison_tick = 0.0
    steam_t = 0.0
    steam_dmg = 0.0
    _frozen = 0.0

    @property
    def frozen_timer(self):
        return self._frozen

    @frozen_timer.setter
    def frozen_timer(self, v):
        # Setiap sumber es/beku di game lewat sini: kalau musuh sedang TERBAKAR lalu terkena es,
        # api padam (kembali normal) dan musuh menerima damage uap.
        if v > self._frozen + 1e-6 and self.burn_t > 0 and not self.dead and not getattr(self, "ice_immune", False):
            self.burn_t = 0.0
            self.steam_dmg = max(self.steam_dmg, 8.0, self.burn_dps * 4.0)
            self.steam_t = 0.7
        self._frozen = v

    def __init__(self, kind, wave_mult, origin_x, origin_y, is_boss=False, boss_scale=1.0,
                 spawn_at=None, mode_config=None, elite=False):
        self.kind = kind
        self.is_boss = is_boss
        self.boss_kind = "normal"
        mc = mode_config or MODE_CONFIGS["normal"]
        lv = DIFFICULTY["lv"]
        cost_ = enemy_cost(kind) if not is_boss else 0
        tier_ = 0 if cost_ <= 2 else 1 if cost_ <= 4 else 2 if cost_ <= 9 else 3
        self.elv = max(1, lv) if is_boss else max(1, lv + int(wave_mult * 0.05) + tier_)

        self.radius = kind["radius"]
        if is_boss:
            self.radius = int(self.radius * min(1.6, 1 + boss_scale * 0.15))
            self.speed = kind["speed"] * mc["speed_mult"] * ENEMY_SPEED_MULT
            self.max_hp = int(kind["hp"] * (1 + boss_scale * 0.35) * (1 + 0.03 * (lv - 1)) * mc["hp_mult"])
            dmg_lv = 1.0
        else:
            wave_speed = 1 + min(wave_mult, ENEMY_WAVE_SPEED_CAP) * ENEMY_WAVE_SPEED_GROWTH
            self.speed = kind["speed"] * wave_speed * level_speed_mult(self.elv) * mc["speed_mult"] * ENEMY_SPEED_MULT
            self.max_hp = int(kind["hp"] * (1 + wave_mult * TIME_HP_GROWTH) * level_hp_mult(self.elv) * mc["hp_mult"])
            dmg_lv = level_dmg_mult(self.elv)
            if not kind.get("stationary"):
                self.speed = max(self.speed, MIN_SLOW_SPEED if kind.get("slow") else MIN_WALK_SPEED)
        self.elite = bool(elite) and not is_boss
        xp_mult = 1.0 if is_boss else (1 + wave_mult * 0.15) * (1 + 0.04 * (lv - 1))
        gold_mult = 1.0
        pickup_bonus = 0.0
        if self.elite:
            self.max_hp = int(self.max_hp * 2.6)
            self.radius = int(self.radius * 1.25)
            self.speed *= 1.1
            xp_mult *= 3
            gold_mult = 3
            pickup_bonus = 0.25
        self.hp = self.max_hp
        self.xp = int(kind["xp"] * xp_mult * mc["reward_mult"])
        self.dmg = kind["dmg"] * (boss_dmg_scale(mc) if is_boss else mc["dmg_mult"]) * dmg_lv * (1.3 if self.elite else 1.0)
        over = max(0, lv - LATE_SCALE_LEVEL) if mc.get("late_scale") and not is_boss else 0
        if over:
            self.max_hp = int(self.max_hp * (1.08 ** over))
            self.speed *= min(2.4, 1.035 ** over)
        self.gold = max(0.15, kind["gold"] * gold_mult * mc.get("gold_mult", mc["reward_mult"]))
        self.color = kind["color"]
        self.pickup_chance = min(1.0, kind["pickup_chance"] + pickup_bonus)
        self.dead = False
        self.frozen_timer = 0.0
        self.kb_vx = 0.0
        self.kb_vy = 0.0
        self.kb_timer = 0.0
        self.haste = 0.0
        self.look = 0.0
        self.preview = False
        self.face = 0.0
        self.phase_t = random.uniform(0, 6.28)
        self.shape = kind.get("shape", "circle")
        self.reduction = kind.get("reduction", 0.0)
        self.stop_range = kind.get("stop_range", 0)

        self.armor_max = kind.get("armor", 0)
        self.armor = self.armor_max

        self.is_summoner = kind.get("summoner", False)
        if self.is_summoner:
            self.summon_timer = 3.0
            self.summon_interval = 11.0

        self.is_shooter = kind.get("shooter", False)
        if self.is_shooter:
            self.rarity = "rare" if random.random() < 0.22 else "common"
            mult = 1.6 if self.rarity == "rare" else 1.0
            self.shoot_timer = random.uniform(2.0, 3.5)
            self.shoot_interval = max(2.2, 4.4 / mult)
            self.shoot_damage = int(7 * mult * mc["dmg_mult"] * dmg_lv)
            self.shoot_speed = 3.8 * mult

        self.is_healer = kind.get("healer", False)
        if self.is_healer:
            self.heal_timer = 4.0
            self.heal_interval = 4.5
            self.heal_amount = 60
            self.heal_radius = 260

        self.is_dasher = kind.get("dasher", False)
        self.is_bat = kind.get("bat", False)
        self.is_teleporter = kind.get("teleporter", False)
        self.is_laser = kind.get("laser", False)
        self.is_ninja = kind.get("ninja", False)
        self.is_bomber = kind.get("bomber", False)
        self.is_sniper = kind.get("sniper", False)
        self.is_buffer = kind.get("buffer", False)
        self.is_toxic = kind.get("toxic", False)
        self.is_slam = kind.get("slam", False)
        self.ability_timer = random.uniform(1.5, 4.0)
        self.dash_state = 0
        self.dash_timer = 0.0
        self.dash_cd = (3.0, 5.0)
        self.ddx = self.ddy = 0.0
        self.atk_timer = 2.5
        self.atk_index = 0
        self.enraged = False

        self.face_style = kind.get("face") or ("ghost" if self.shape == "ghost" else "skull" if self.shape == "skull" else "angry")
        self.is_thunder = kind.get("thunder", False)
        self.is_necro_boss = kind.get("necro", False)
        self.is_brute_boss = kind.get("brute", False)
        self.reward = kind.get("reward", 0)
        self.intro_t = 0.0
        self.busy = False
        self.air_h = 0.0
        self.fixed_dir = None
        self.life = None
        self.haste_mult = 1.4
        self.bstate = None
        self.bstate_t = 0.0
        self.bdata = None
        self.no_recycle = False
        self.from_event = False
        self.axe = None
        self.form = "orange"
        self.tell = None
        self.dmg_in_mult = 1.0
        self.walk_phase = 0.0
        self._lx = None
        self._ly = None
        self.hands = None
        self.dying = False

        self.gear = kind.get("gear")
        self.is_warden = kind.get("warden", False)
        self.is_mimic = kind.get("mimic", False)
        self.is_hammer = kind.get("hammer", False)
        self.is_protector = kind.get("protector", False)
        self.is_slash = kind.get("slash", False)
        self.is_mother = kind.get("mother", False)
        self.is_crystal = kind.get("crystal_mage", False)
        self.is_shotgun = kind.get("shotgun", False)
        self.is_chief = kind.get("chief", False)
        self.is_minigunner = kind.get("minigunner", False)
        self.is_reaper = kind.get("reaper", False)
        self.is_ethereal = kind.get("ethereal", False)
        self.ice_immune = kind.get("ice_immune", False)
        self.heads = 2 if kind.get("two_heads") else 1
        self.mother_n = 0
        self.mother_cd = 0.0
        self.ethereal_t = 0.0
        self.crystal_buff = None
        self.shield_max = int(kind.get("shield", 0) * self.max_hp / max(1, kind["hp"])) if kind.get("shield") else 0
        self.shield = self.shield_max
        self.has_elem = bool(kind.get("abil"))
        self.abil_t = None
        self.has_new = (self.is_warden or self.is_mimic or self.is_hammer or self.is_protector or self.is_slash
                        or self.is_mother or self.is_crystal or self.is_shotgun or self.is_chief
                        or self.is_minigunner or self.is_reaper or self.is_ethereal)

        if spawn_at is not None:
            self.x, self.y = spawn_at
        else:
            margin = 70
            half_w, half_h = WIDTH / 2 + margin, HEIGHT / 2 + margin
            side = random.choice(["top", "bottom", "left", "right"])
            if side == "top":
                self.x = origin_x + random.uniform(-half_w, half_w)
                self.y = origin_y - half_h
            elif side == "bottom":
                self.x = origin_x + random.uniform(-half_w, half_w)
                self.y = origin_y + half_h
            elif side == "left":
                self.x = origin_x - half_w
                self.y = origin_y + random.uniform(-half_h, half_h)
            else:
                self.x = origin_x + half_w
                self.y = origin_y + random.uniform(-half_h, half_h)

    def update(self, target, dt):
        if self.intro_t > 0:
            self.intro_t -= dt
            return
        if self.ice_immune:
            self.frozen_timer = 0.0
        if self.life is not None:
            self.life -= dt
            if self.life <= 0:
                self.life = None
                self.fixed_dir = None
                self.no_recycle = False
        if self.busy:
            return
        if self.kb_timer > 0:
            self.kb_timer -= dt
            self.x += self.kb_vx * dt * 60
            self.y += self.kb_vy * dt * 60
            self.kb_vx *= 0.85
            self.kb_vy *= 0.85
            return
        if self.frozen_timer > 0:
            self.frozen_timer -= dt
            return
        dx, dy = target[0] - self.x, target[1] - self.y
        dist = math.hypot(dx, dy) or 1
        dx, dy = dx / dist, dy / dist
        self.face = math.atan2(dy, dx)
        spd = self.speed
        if self.haste > 0:
            self.haste -= dt
            spd *= self.haste_mult
            if self.haste <= 0:
                self.haste_mult = 1.4
        if self.ethereal_t > 0:
            self.ethereal_t -= dt
            spd *= 1.5
        if self.fixed_dir is not None:
            if (self.x - target[0]) * self.fixed_dir[0] + (self.y - target[1]) * self.fixed_dir[1] > 40:
                self.fixed_dir = None
                self.life = None
                self.no_recycle = False
            else:
                self.x += self.fixed_dir[0] * spd * dt * 60
                self.y += self.fixed_dir[1] * spd * dt * 60
                self.face = math.atan2(self.fixed_dir[1], self.fixed_dir[0])
                return

        if self.is_dasher:
            if self.dash_state == 0:
                self.ability_timer -= dt
                if self.ability_timer <= 0 and dist < 700:
                    self.dash_state = 1
                    self.dash_timer = 0.6
                    self.ddx, self.ddy = dx, dy
            elif self.dash_state == 1:
                self.dash_timer -= dt
                self.ddx, self.ddy = dx, dy
                if self.dash_timer <= 0:
                    self.dash_state = 2
                    self.dash_timer = 0.45
                return
            else:
                self.dash_timer -= dt
                self.x += self.ddx * max(spd, 1.0) * 5.5 * dt * 60
                self.y += self.ddy * max(spd, 1.0) * 5.5 * dt * 60
                if self.dash_timer <= 0:
                    self.dash_state = 0
                    self.ability_timer = random.uniform(*self.dash_cd)
                return

        if self.stop_range and dist <= self.stop_range:
            if dist < self.stop_range * 0.55:
                self.x -= dx * spd * 0.7 * dt * 60
                self.y -= dy * spd * 0.7 * dt * 60
            else:
                sg = 1 if (id(self) // 16) % 2 else -1
                self.x += -dy * sg * spd * 0.6 * dt * 60
                self.y += dx * sg * spd * 0.6 * dt * 60
            return

        if self.is_bat:
            px, py = -dy, dx
            w = math.sin(pygame.time.get_ticks() / 1000.0 * 6 + self.phase_t) * 1.3
            mx, my = dx + px * w, dy + py * w
            m = math.hypot(mx, my) or 1
            dx, dy = mx / m, my / m

        self.x += dx * spd * dt * 60
        self.y += dy * spd * dt * 60

    def draw_giant_body(self, surf, ix, iy, r, color, outline, ow, t):
        """Badan raksasa dengan siluet berbeda per varian. Mengembalikan (pusat wajah x, y, radius wajah)."""
        v = self.kind.get("variant", "brute")
        dark, light = _dk(color, 0.7), _lt(color, 0.15)
        ph = self.walk_phase
        if v == "runner":
            lean = math.cos(self.face) * r * 0.25
            for sg in (-1, 1):
                sw = math.sin(ph + (0 if sg > 0 else math.pi)) * r * 0.5
                pygame.draw.line(surf, dark, (ix + sg * r * 0.25, iy + r * 0.4), (ix + sg * r * 0.3 + sw, iy + r * 1.3), max(4, int(r * 0.22)))
                pygame.draw.circle(surf, dark, (int(ix + sg * r * 0.3 + sw), int(iy + r * 1.3)), max(3, int(r * 0.17)))
            for k in range(3):
                pygame.draw.line(surf, _lt(color, 0.5), (ix - math.cos(self.face) * (r + 6 + k * 6), iy - r * 0.4 + k * r * 0.4),
                                 (ix - math.cos(self.face) * (r + 22 + k * 6), iy - r * 0.4 + k * r * 0.4), 2)
            body = pygame.Rect(ix - r * 0.72 + lean, iy - r * 0.8, r * 1.44, r * 1.35)
            pygame.draw.ellipse(surf, color, body)
            pygame.draw.ellipse(surf, outline, body, ow)
            hx = ix + lean * 1.8
            pygame.draw.circle(surf, light, (int(hx), int(iy - r * 0.62)), int(r * 0.52))
            pygame.draw.circle(surf, outline, (int(hx), int(iy - r * 0.62)), int(r * 0.52), ow)
            return hx, iy - r * 0.62, r * 0.52
        if v == "hunch":
            pygame.draw.circle(surf, dark, (ix - int(r * 0.35), iy - int(r * 0.55)), int(r * 0.62))
            for sg in (-1, 1):
                pygame.draw.line(surf, dark, (ix + sg * r * 0.7, iy - r * 0.1), (ix + sg * r * 1.0, iy + r * 0.95), max(5, int(r * 0.3)))
                pygame.draw.circle(surf, light, (int(ix + sg * r * 1.0), int(iy + r * 1.0)), int(r * 0.3))
                pygame.draw.circle(surf, outline, (int(ix + sg * r * 1.0), int(iy + r * 1.0)), int(r * 0.3), ow)
            pygame.draw.circle(surf, color, (ix, iy), r)
            pygame.draw.circle(surf, outline, (ix, iy), r, ow)
            pygame.draw.circle(surf, light, (ix + int(r * 0.12), iy - int(r * 0.4)), int(r * 0.5))
            pygame.draw.circle(surf, outline, (ix + int(r * 0.12), iy - int(r * 0.4)), int(r * 0.5), ow)
            return ix + r * 0.12, iy - r * 0.4, r * 0.5
        if v == "plated":
            for sg in (-1, 1):
                pygame.draw.circle(surf, light, (ix + int(sg * r * 0.95), iy + int(r * 0.35)), int(r * 0.34))
            pygame.draw.circle(surf, color, (ix, iy), r)
            pygame.draw.circle(surf, outline, (ix, iy), r, ow)
            for sg in (-1, 1):
                pad = pygame.Rect(ix + sg * r * 0.78 - r * 0.28, iy - r * 0.55, r * 0.56, r * 0.4)
                pygame.draw.rect(surf, (150, 155, 170), pad, border_radius=5)
                pygame.draw.rect(surf, (50, 55, 70), pad, 2, border_radius=5)
            chest = pygame.Rect(ix - r * 0.5, iy + r * 0.0, r * 1.0, r * 0.7)
            pygame.draw.rect(surf, (150, 155, 170), chest, border_radius=6)
            pygame.draw.rect(surf, (50, 55, 70), chest, 2, border_radius=6)
            pygame.draw.line(surf, (50, 55, 70), (ix, iy), (ix, iy + r * 0.7), 2)
            pygame.draw.circle(surf, (170, 175, 190), (ix, iy - int(r * 0.35)), int(r * 0.5))
            pygame.draw.arc(surf, (50, 55, 70), pygame.Rect(ix - r * 0.5, iy - r * 0.85, r, r), 0, math.pi, 3)
            return ix, iy - r * 0.32, r * 0.46
        if v == "horned":
            for sg in (-1, 1):
                pygame.draw.polygon(surf, (235, 225, 200), [(ix + sg * r * 0.35, iy - r * 0.8), (ix + sg * r * 1.0, iy - r * 1.45), (ix + sg * r * 0.85, iy - r * 0.4)])
                pygame.draw.polygon(surf, outline, [(ix + sg * r * 0.35, iy - r * 0.8), (ix + sg * r * 1.0, iy - r * 1.45), (ix + sg * r * 0.85, iy - r * 0.4)], 2)
                pygame.draw.circle(surf, light, (ix + int(sg * r * 1.0), iy + int(r * 0.3)), int(r * 0.34))
            pygame.draw.circle(surf, color, (ix, iy), r)
            pygame.draw.circle(surf, dark, (ix, iy + int(r * 0.5)), int(r * 0.5))
            pygame.draw.circle(surf, outline, (ix, iy), r, ow)
            return ix, iy - r * 0.05, r * 0.8
        if v == "cyclops":
            for sg in (-1, 1):
                pygame.draw.circle(surf, light, (ix + int(sg * r * 1.0), iy + int(r * 0.4)), int(r * 0.34))
                pygame.draw.circle(surf, outline, (ix + int(sg * r * 1.0), iy + int(r * 0.4)), int(r * 0.34), ow)
            pygame.draw.circle(surf, color, (ix, iy), r)
            pygame.draw.circle(surf, outline, (ix, iy), r, ow)
            eye = pygame.Rect(ix - r * 0.38, iy - r * 0.5, r * 0.76, r * 0.62)
            pygame.draw.ellipse(surf, WHITE, eye)
            pygame.draw.ellipse(surf, (220, 60, 60), eye, 3)
            return ix, iy + r * 0.5, 0.0
        if v == "bulwark":
            torso = pygame.Rect(ix - r * 0.95, iy - r * 0.5, r * 1.9, r * 1.5)
            for sg in (-1, 1):
                arm = pygame.Rect(ix + sg * r * 1.1 - r * 0.25, iy - r * 0.25, r * 0.5, r * 1.05)
                pygame.draw.rect(surf, dark, arm, border_radius=6)
                pygame.draw.rect(surf, outline, arm, 2, border_radius=6)
            pygame.draw.rect(surf, color, torso, border_radius=int(r * 0.25))
            pygame.draw.rect(surf, outline, torso, ow, border_radius=int(r * 0.25))
            for ax_ in (-0.7, 0.7):
                for ay_ in (-0.25, 0.7):
                    pygame.draw.circle(surf, dark, (int(ix + ax_ * r), int(iy + ay_ * r)), max(2, int(r * 0.07)))
            head = pygame.Rect(ix - r * 0.45, iy - r * 1.0, r * 0.9, r * 0.7)
            pygame.draw.rect(surf, light, head, border_radius=5)
            pygame.draw.rect(surf, outline, head, ow, border_radius=5)
            return ix, iy - r * 0.65, r * 0.42
        if v == "spiked":
            for k in range(10):
                a = k * math.tau / 10 + 0.15
                pygame.draw.polygon(surf, (190, 195, 205), [(ix + math.cos(a - 0.12) * r * 0.92, iy + math.sin(a - 0.12) * r * 0.92),
                                                            (ix + math.cos(a + 0.12) * r * 0.92, iy + math.sin(a + 0.12) * r * 0.92),
                                                            (ix + math.cos(a) * r * 1.28, iy + math.sin(a) * r * 1.28)])
            pygame.draw.rect(surf, (110, 190, 70), (ix - r * 0.35, iy - r * 1.22, r * 0.7, r * 0.55), border_radius=6)
            pygame.draw.rect(surf, (40, 70, 30), (ix - r * 0.35, iy - r * 1.22, r * 0.7, r * 0.55), 2, border_radius=6)
            pygame.draw.circle(surf, color, (ix, iy), r)
            pygame.draw.circle(surf, outline, (ix, iy), r, ow)
            for sg in (-1, 1):
                pygame.draw.circle(surf, light, (ix + int(sg * r * 0.6), iy + int(r * 0.5)), int(r * 0.25))
            pygame.draw.circle(surf, light, (ix, iy - int(r * 0.3)), int(r * 0.46))
            return ix, iy - r * 0.3, r * 0.46
        if v == "hulk":
            for sg in (-1, 1):
                pygame.draw.circle(surf, light, (ix + int(sg * r * 0.95), iy + int(r * 0.5)), int(r * 0.5))
                pygame.draw.circle(surf, outline, (ix + int(sg * r * 0.95), iy + int(r * 0.5)), int(r * 0.5), ow)
            pygame.draw.circle(surf, color, (ix, iy + int(r * 0.15)), int(r * 0.95))
            pygame.draw.circle(surf, outline, (ix, iy + int(r * 0.15)), int(r * 0.95), ow)
            pygame.draw.circle(surf, light, (ix, iy - int(r * 0.7)), int(r * 0.42))
            pygame.draw.circle(surf, outline, (ix, iy - int(r * 0.7)), int(r * 0.42), ow)
            return ix, iy - r * 0.7, r * 0.42
        for sg in (-1, 1):
            pygame.draw.circle(surf, light, (ix + int(sg * r * 1.0), iy + int(r * 0.35)), int(r * 0.36))
            pygame.draw.circle(surf, outline, (ix + int(sg * r * 1.0), iy + int(r * 0.35)), int(r * 0.36), ow)
        pygame.draw.circle(surf, color, (ix, iy), r)
        pygame.draw.circle(surf, dark, (ix, iy + int(r * 0.45)), int(r * 0.5))
        pygame.draw.circle(surf, outline, (ix, iy), r, ow)
        return ix, iy, r * 0.85

    def draw_brute(self, surf, ix, iy, r, color, t):
        dark = _dk(color, 0.6)
        for k in (-1, 1):
            pygame.draw.circle(surf, dark, (ix + int(k * r * 0.45), iy + int(r * 0.85)), int(r * 0.3))
        for k in (-1, 1):
            fx, fy = ix + k * r * 1.0, iy + r * 0.2 + math.sin(t * 3 + k) * 3
            fang = 0.0 if k == 1 else math.pi
            if k == 1 and self.bstate in ("punch_wind", "punch") and self.bdata:
                a = self.bdata["ang"]
                ext = -r * 0.5 if self.bstate == "punch_wind" else r * 1.5
                fx, fy = ix + math.cos(a) * ext, iy + math.sin(a) * ext
                fang = a
            pygame.draw.line(surf, dark, (ix + k * r * 0.6, iy), (fx, fy), max(4, int(r * 0.3)))
            draw_fist(surf, fx, fy, fang, max(8, int(r * 0.3)))
        pygame.draw.circle(surf, color, (ix, iy), r)
        pygame.draw.circle(surf, GOLD_COLOR, (ix, iy), r, 3)
        pygame.draw.arc(surf, dark, pygame.Rect(ix - int(r * 0.6), iy - int(r * 0.1), int(r * 1.2), int(r * 0.9)),
                        3.5, 5.9, 3)
        for k in (-1, 1):
            hx, hy, hr = ix + int(k * r * 0.5), iy - int(r * 0.72), int(r * 0.5)
            pygame.draw.polygon(surf, (235, 225, 200), [(hx + k * hr * 0.4, hy - hr * 0.7), (hx + k * hr * 1.0, hy - hr * 1.5),
                                                        (hx + k * hr * 0.9, hy - hr * 0.4)])
            pygame.draw.circle(surf, _lt(color, 0.12), (hx, hy), hr)
            pygame.draw.circle(surf, GOLD_COLOR, (hx, hy), hr, 3)
            draw_face(surf, hx, hy, hr, self.look, "angry", 1.0, t)

    def draw_boss_custom(self, surf, ix, iy, r, color, t):
        k = self.boss_kind
        st = self.bstate
        face = self.face
        c, sn = math.cos(face), math.sin(face)
        edx, edy = math.cos(self.look) * r * 0.1, math.sin(self.look) * r * 0.06
        if k == "guardian":
            pygame.draw.polygon(surf, (150, 40, 50), [(ix - r * 0.8, iy - r * 0.2), (ix + r * 0.8, iy - r * 0.2), (ix + r * 0.5, iy + r * 1.3), (ix - r * 0.5, iy + r * 1.3)])
            for sg in (-1, 1):
                pygame.draw.circle(surf, _lt(color, 0.1), (ix + int(sg * r * 0.85), iy - int(r * 0.2)), int(r * 0.38))
                pygame.draw.circle(surf, GOLD_COLOR, (ix + int(sg * r * 0.85), iy - int(r * 0.2)), int(r * 0.38), 3)
            pygame.draw.circle(surf, color, (ix, iy), r)
            pygame.draw.circle(surf, GOLD_COLOR, (ix, iy), r, 4)
            pygame.draw.rect(surf, _dk(color, 0.6), (ix - r * 0.55, iy - r * 0.35, r * 1.1, r * 0.3), border_radius=4)
            for sg in (-1, 1):
                pygame.draw.ellipse(surf, (120, 240, 255), (ix + sg * r * 0.25 - 5 + edx, iy - r * 0.38 + edy, 10, 14))
            pygame.draw.polygon(surf, (190, 40, 50), [(ix - 6, iy - r), (ix + 6, iy - r), (ix + 18, iy - r * 1.6), (ix, iy - r * 1.3), (ix - 18, iy - r * 1.6)])
            up = st in ("raise",)
            sx_, sy_ = ix + r * 1.15, iy + r * 0.9
            ex_, ey_ = (ix + r * 1.15, iy - r * 1.9) if up else (ix + c * r * 1.2 + r * 0.6, iy + sn * r * 0.8 - r * 0.9)
            if st == "thrust":
                ex_, ey_ = ix + c * r * 2.4, iy + sn * r * 2.4
                sx_, sy_ = ix + c * r * 0.4, iy + sn * r * 0.4
            pygame.draw.line(surf, (140, 100, 60), (sx_, sy_), (ex_, ey_), 6)
            a = math.atan2(ey_ - sy_, ex_ - sx_)
            head = rot_pts([(0, 0), (-r * 0.2, -r * 0.2), (r * 0.5, 0), (-r * 0.2, r * 0.2)], ex_, ey_, a)
            pygame.draw.polygon(surf, (235, 240, 250) if not up else (255, 210, 120), head)
            pygame.draw.polygon(surf, (70, 75, 90), head, 2)
            if up:
                pygame.draw.circle(surf, (255, 190, 90), (int(ex_), int(ey_)), int(12 + 4 * math.sin(t * 12)), 3)
        elif k == "minigun":
            pygame.draw.rect(surf, (60, 70, 55), (ix - r * 1.0, iy - r * 0.2, r * 2.0, r * 1.25), border_radius=8)
            pygame.draw.circle(surf, color, (ix, iy), r)
            pygame.draw.circle(surf, GOLD_COLOR, (ix, iy), r, 3)
            pygame.draw.arc(surf, (45, 55, 40), pygame.Rect(ix - r, iy - r, r * 2, r * 2), 0.2, 2.9, int(r * 0.5))
            for sg in (-1, 1):
                pygame.draw.ellipse(surf, WHITE, (ix + sg * r * 0.32 - 5 + edx, iy - r * 0.2 + edy, 10, 14))
                pygame.draw.ellipse(surf, BLACK, (ix + sg * r * 0.32 - 5 + edx, iy - r * 0.2 + edy, 10, 14), 1)
            spin = t * (32 if st in ("mg_fire", "mg_sweep") else 9 if st == "mg_spin" else 0.4)
            p0 = (ix + c * r * 0.5, iy + sn * r * 0.5 + r * 0.25)
            pygame.draw.rect(surf, (55, 58, 64), (p0[0] - 14, p0[1] - 14, 28, 28), border_radius=5)
            for kk in range(4):
                off = math.sin(spin + kk * 1.571) * 8
                pygame.draw.line(surf, (160, 165, 175), (p0[0] - sn * off, p0[1] + c * off),
                                 (p0[0] + c * r * 2.0 - sn * off, p0[1] + sn * r * 2.0 + c * off), 4)
            pygame.draw.circle(surf, (85, 88, 96), (int(p0[0] + c * r * 2.0), int(p0[1] + sn * r * 2.0)), 9, 3)
            for kk in range(7):
                pygame.draw.circle(surf, (230, 190, 60), (int(ix - r * 0.9 + kk * 7), int(iy + r * 0.75 + (kk % 2) * 4)), 4)
            if st in ("mg_fire", "mg_sweep"):
                pygame.draw.circle(surf, (255, 235, 150), (int(p0[0] + c * r * 2.25), int(p0[1] + sn * r * 2.25)), 9 + int(4 * math.sin(t * 40)))
        elif k == "exec":
            pygame.draw.polygon(surf, (30, 28, 38), [(ix - r * 0.9, iy + r * 1.2), (ix + r * 0.9, iy + r * 1.2), (ix + r * 0.5, iy - r * 0.3), (ix - r * 0.5, iy - r * 0.3)])
            for sg in (-1, 1):
                pygame.draw.circle(surf, (85, 88, 105), (ix + int(sg * r * 0.8), iy - int(r * 0.15)), int(r * 0.4))
                pygame.draw.circle(surf, (190, 190, 205), (ix + int(sg * r * 0.8), iy - int(r * 0.15)), int(r * 0.4), 3)
            pygame.draw.circle(surf, color, (ix, iy), r)
            pygame.draw.circle(surf, (190, 190, 205), (ix, iy), r, 4)
            hood = [(ix - r * 0.85, iy + r * 0.1), (ix + r * 0.85, iy + r * 0.1), (ix, iy - r * 1.35)]
            pygame.draw.polygon(surf, (20, 18, 26), hood)
            pygame.draw.polygon(surf, (110, 110, 130), hood, 2)
            pygame.draw.rect(surf, (8, 8, 12), (ix - r * 0.5, iy - r * 0.5, r * 1.0, r * 0.45), border_radius=6)
            for sg in (-1, 1):
                pygame.draw.ellipse(surf, (255, 90, 80), (ix + sg * r * 0.22 - 4 + edx, iy - r * 0.42 + edy, 8, 12))
            if not (self.axe is not None and self.axe.alive):
                a = face + (-1.2 if st == "cleave" else 0.5 + math.sin(t * 3) * 0.1)
                draw_axe_shape(surf, ix + math.cos(a) * r * 1.1, iy + math.sin(a) * r * 1.1, a, r * 0.95)
        elif k == "fire":
            blue = self.form == "blue"
            outer, mid, core = ((40, 90, 230), (90, 170, 255), (210, 245, 255)) if blue else ((220, 70, 20), (255, 150, 40), (255, 240, 150))
            for kk in range(12):
                a = kk * math.tau / 12 + t * (1.8 if blue else 1.0)
                h = r * (1.35 + 0.35 * math.sin(t * 9 + kk * 1.7))
                pygame.draw.polygon(surf, outer, [(ix + math.cos(a - 0.2) * r * 0.8, iy + math.sin(a - 0.2) * r * 0.8),
                                                  (ix + math.cos(a + 0.2) * r * 0.8, iy + math.sin(a + 0.2) * r * 0.8),
                                                  (ix + math.cos(a) * h, iy + math.sin(a) * h)])
            pygame.draw.circle(surf, mid, (ix, iy), int(r * 0.95))
            pygame.draw.circle(surf, core, (ix, iy), int(r * 0.6))
            for sg in (-1, 1):
                pygame.draw.ellipse(surf, (30, 10, 5) if not blue else (10, 15, 50), (ix + sg * r * 0.28 - 6 + edx, iy - r * 0.25 + edy, 12, 18))
        elif k == "final":
            phase = getattr(self, "phase_seen", 1)
            cam_x, cam_y = getattr(self, "_cam", (0, 0))
            hot = (255, 70, 80) if phase >= 3 else (255, 190, 90)
            for kk in range(24):
                a = kk * math.tau / 24 + t * (0.4 + 0.2 * phase)
                h = r * (1.16 + 0.08 * math.sin(t * 5 + kk))
                pygame.draw.polygon(surf, hot, [(ix + math.cos(a - 0.07) * r * 0.98, iy + math.sin(a - 0.07) * r * 0.98),
                                                (ix + math.cos(a + 0.07) * r * 0.98, iy + math.sin(a + 0.07) * r * 0.98),
                                                (ix + math.cos(a) * h, iy + math.sin(a) * h)])
            pygame.draw.polygon(surf, (50, 10, 30), [(ix - r * 1.15, iy + r * 1.1), (ix + r * 1.15, iy + r * 1.1), (ix + r * 0.6, iy - r * 0.2), (ix - r * 0.6, iy - r * 0.2)])
            pygame.draw.circle(surf, (110, 25, 55), (ix, iy), r)
            pygame.draw.circle(surf, (150, 40, 75), (ix, iy), int(r * 0.82))
            pygame.draw.circle(surf, (185, 60, 95), (ix, iy), int(r * 0.58))
            pygame.draw.circle(surf, GOLD_COLOR, (ix, iy), r, 8)
            crown = [(ix - r * 0.62, iy - r * 0.78)]
            for kk in range(7):
                crown += [(ix - r * 0.62 + (kk + 0.5) * r * 1.24 / 7, iy - r * 1.18 - (r * 0.12 if kk % 2 == 0 else 0)),
                          (ix - r * 0.62 + (kk + 1) * r * 1.24 / 7, iy - r * 0.78)]
            pygame.draw.polygon(surf, GOLD_COLOR, crown)
            pygame.draw.polygon(surf, (120, 80, 10), crown, 4)
            for kk in range(7):
                pygame.draw.circle(surf, (90, 230, 255) if kk % 2 else (255, 80, 110), (int(ix - r * 0.62 + (kk + 0.5) * r * 1.24 / 7), int(iy - r * 0.9)), 9)
            for sg in (-1, 1):
                eye = pygame.Rect(ix + sg * r * 0.34 - r * 0.16 + edx, iy - r * 0.34 + edy, r * 0.32, r * 0.46)
                pygame.draw.ellipse(surf, WHITE, eye)
                pygame.draw.ellipse(surf, hot, eye, 6)
            pygame.draw.circle(surf, GOLD_COLOR, (ix, int(iy + r * 0.38)), int(r * 0.2))
            pygame.draw.circle(surf, (120, 80, 10), (ix, int(iy + r * 0.38)), int(r * 0.2), 5)
            if r >= 200:
                ct = font_big.render("$", True, (120, 80, 10))
                surf.blit(ct, (ix - ct.get_width() / 2, iy + r * 0.38 - ct.get_height() / 2))
            else:
                bar = max(1, int(r * 0.03))
                pygame.draw.line(surf, (120, 80, 10), (ix, iy + r * 0.26), (ix, iy + r * 0.5), bar + 1)
            hs = r / 320.0
            for h in (self.hands or []):
                hx, hy = h["x"] - cam_x, h["y"] - cam_y
                draw_gauntlet(surf, hx, hy, h["side"], max(3.0, 60.0 * hs), h["mode"], t)
        elif k == "skel":
            pygame.draw.rect(surf, (100, 70, 45), (ix - r * 1.1, iy - r * 0.2, r * 0.7, r * 1.0), border_radius=6)
            pygame.draw.rect(surf, (50, 35, 20), (ix - r * 1.1, iy - r * 0.2, r * 0.7, r * 1.0), 3, border_radius=6)
            if st in ("bag_open", "bag_fire"):
                for kk in range(3):
                    pygame.draw.line(surf, (150, 155, 165), (ix - r * 0.8, iy + kk * 5 - 4), (ix + c * r * 1.8, iy + sn * r * 1.8 + kk * 5 - 4), 4)
            for kk in range(4):
                pygame.draw.line(surf, (235, 235, 215), (ix - r * 0.55, iy + r * 0.2 + kk * r * 0.2), (ix + r * 0.55, iy + r * 0.2 + kk * r * 0.2), 4)
            pygame.draw.line(surf, (235, 235, 215), (ix, iy + r * 0.1), (ix, iy + r * 0.95), 5)
            pygame.draw.circle(surf, color, (ix, iy - int(r * 0.3)), int(r * 0.78))
            pygame.draw.circle(surf, (60, 60, 60), (ix, iy - int(r * 0.3)), int(r * 0.78), 3)
            pygame.draw.rect(surf, (35, 28, 22), (ix - r * 0.85, iy - r * 0.62, r * 1.7, r * 0.18))
            pygame.draw.polygon(surf, (35, 28, 22), [(ix - r * 0.5, iy - r * 0.62), (ix + r * 0.5, iy - r * 0.62), (ix + r * 0.3, iy - r * 1.05), (ix - r * 0.3, iy - r * 1.05)])
            for sg in (-1, 1):
                pygame.draw.ellipse(surf, (16, 16, 22), (ix + sg * r * 0.3 - 6 + edx, iy - r * 0.45 + edy, 12, 18))
            if st not in ("bag_open", "bag_fire"):
                p0 = (ix + c * r * 0.7, iy + sn * r * 0.7 + r * 0.3)
                pygame.draw.line(surf, (70, 72, 80), p0, (p0[0] + c * r * 1.0, p0[1] + sn * r * 1.0), 7)
                pygame.draw.circle(surf, (110, 112, 120), (int(p0[0]), int(p0[1])), 9)
                if st == "rev":
                    pygame.draw.circle(surf, (255, 235, 150), (int(p0[0] + c * r * 1.15), int(p0[1] + sn * r * 1.15)), 6 + int(3 * math.sin(t * 40)))

    def draw_robot(self, surf, ix, iy, r, color, t):
        boss = self.is_boss
        st = ROBOT_STYLE.get(self.kind["name"], ROBOT_STYLE_DEFAULT)
        steel = tuple(min(235, int(62 + c * 0.55)) for c in color)
        dark, lt = _dk(steel, 0.5), _lt(steel, 0.28)
        led = st.get("led", (255, 80, 70) if boss else (90, 235, 255))
        ph = self.walk_phase
        ink = (22, 24, 30)
        ow = 4 if boss else 2
        if self.shape == "bat":
            for sg in (-1, 1):
                rx = ix + sg * r * 1.3
                pygame.draw.line(surf, dark, (ix, iy), (rx, iy - r * 0.4), 3)
                a = t * 30 + sg
                pygame.draw.line(surf, lt, (rx - math.cos(a) * r * 0.9, iy - r * 0.4), (rx + math.cos(a) * r * 0.9, iy - r * 0.4), 3)
            pygame.draw.ellipse(surf, steel, (ix - r, iy - r * 0.6, r * 2, r * 1.2))
            pygame.draw.ellipse(surf, ink, (ix - r, iy - r * 0.6, r * 2, r * 1.2), 2)
            pygame.draw.circle(surf, color, (ix, int(iy + r * 0.45)), max(2, int(r * 0.22)))
            draw_led_pair(surf, ix, iy - r * 0.04, r * 0.35, r * 0.3, r * 0.22, led, self.look, r)
            return
        body_k, legs_k = st["body"], st["legs"]
        eyes_k, arms_k, extra = st["eyes"], st["arms"], st.get("extra")
        bw, bh = {"box": (1.8, 1.5), "round": (1.7, 1.7), "tall": (1.3, 1.9), "wide": (2.2, 1.3), "tri": (1.9, 1.5), "dome": (1.6, 1.5)}[body_k]
        body = pygame.Rect(ix - r * bw / 2, iy - r * bh * 0.5, r * bw, r * bh)
        foot_y = body.bottom
        if legs_k == "legs":
            for sg in (-1, 1):
                off = math.sin(ph + (0 if sg > 0 else math.pi)) * r * 0.2
                pygame.draw.rect(surf, dark, (ix + sg * r * 0.45 - r * 0.17, foot_y - r * 0.2 + off, r * 0.34, r * 0.6), border_radius=3)
                pygame.draw.rect(surf, ink, (ix + sg * r * 0.45 - r * 0.3, foot_y + r * 0.35 + off, r * 0.6, r * 0.2), border_radius=3)
        elif legs_k == "stomp":
            for sg in (-1, 1):
                off = abs(math.sin(ph + (0 if sg > 0 else math.pi))) * r * 0.12
                pygame.draw.rect(surf, dark, (ix + sg * r * 0.62 - r * 0.28, foot_y - r * 0.2 - off, r * 0.56, r * 0.5), border_radius=4)
                pygame.draw.rect(surf, ink, (ix + sg * r * 0.62 - r * 0.38, foot_y + r * 0.25 - off, r * 0.76, r * 0.24), border_radius=4)
        elif legs_k == "tread":
            tr = pygame.Rect(ix - r * 1.05, foot_y - r * 0.15, r * 2.1, r * 0.5)
            pygame.draw.rect(surf, ink, tr, border_radius=int(r * 0.25))
            for k in range(5):
                wx = tr.x + r * 0.2 + k * (tr.width - r * 0.4) / 4
                pygame.draw.circle(surf, lt, (int(wx), tr.centery), max(2, int(r * 0.11)))
            pygame.draw.line(surf, dark, (tr.x + r * 0.2, tr.y + 2), (tr.right - r * 0.2, tr.y + 2), 2)
        elif legs_k == "wheel":
            wr = max(4, int(r * 0.45))
            pygame.draw.circle(surf, ink, (ix, int(foot_y + wr * 0.35)), wr)
            pygame.draw.circle(surf, lt, (ix, int(foot_y + wr * 0.35)), max(2, wr // 2))
            a = ph * 2
            pygame.draw.line(surf, dark, (ix, int(foot_y + wr * 0.35)), (ix + math.cos(a) * wr * 0.8, foot_y + wr * 0.35 + math.sin(a) * wr * 0.8), 2)
        elif legs_k == "hover":
            fl = 0.7 + 0.3 * math.sin(t * 20)
            pygame.draw.ellipse(surf, (255, 170, 60), (ix - r * 0.45, foot_y + r * 0.05, r * 0.9, r * 0.5 * fl))
            pygame.draw.ellipse(surf, (255, 240, 170), (ix - r * 0.25, foot_y + r * 0.05, r * 0.5, r * 0.3 * fl))
            pygame.draw.rect(surf, dark, (ix - r * 0.5, foot_y - r * 0.1, r, r * 0.22), border_radius=3)
        elif legs_k == "spider":
            for k in range(4):
                sg = -1 if k < 2 else 1
                wob = math.sin(ph + k * 1.6) * r * 0.15
                kx = ix + sg * r * (0.7 + 0.4 * (k % 2))
                ky = foot_y + r * (0.45 + 0.2 * (k % 2)) + wob
                pygame.draw.line(surf, dark, (ix + sg * r * 0.3, foot_y - r * 0.2), (kx, ky), max(2, int(r * 0.12)))
        if arms_k in ("arms", "claw", "cannon", "shieldarm"):
            for sg in (-1, 1):
                ax = ix + sg * (body.width / 2 + r * 0.12)
                if arms_k == "claw":
                    pygame.draw.rect(surf, dark, (ax - r * 0.2, body.y + r * 0.1, r * 0.4, r * 0.8), border_radius=4)
                    sw = math.sin(t * 5 + sg) * 0.25
                    for q in (-1, 1):
                        pygame.draw.line(surf, lt, (ax, body.y + r * 0.9), (ax + q * r * 0.28 + sg * r * 0.05, body.y + r * (1.25 + sw * q)), max(3, int(r * 0.12)))
                elif arms_k == "cannon":
                    ca = self.look if boss else 0.35
                    pygame.draw.circle(surf, dark, (int(ax), int(body.y + r * 0.45)), max(3, int(r * 0.22)))
                    ex, ey = ax + math.cos(ca) * r * (1.0 if boss else 0.8), body.y + r * 0.45 + math.sin(ca) * r * (1.0 if boss else 0.8)
                    pygame.draw.line(surf, ink, (ax, body.y + r * 0.45), (ex, ey), max(4, int(r * 0.24)))
                    pygame.draw.circle(surf, (255, 190, 80), (int(ex), int(ey)), max(2, int(r * 0.1)))
                elif arms_k == "shieldarm":
                    if sg > 0:
                        pl = pygame.Rect(ax - r * 0.1, body.y - r * 0.1, r * 0.55, r * 1.5)
                        pygame.draw.rect(surf, lt, pl, border_radius=int(r * 0.15))
                        pygame.draw.rect(surf, ink, pl, 2, border_radius=int(r * 0.15))
                        pygame.draw.line(surf, color, (pl.centerx, pl.y + 4), (pl.centerx, pl.bottom - 4), 3)
                    else:
                        pygame.draw.rect(surf, dark, (ax - r * 0.17, body.y + r * 0.2, r * 0.34, r * 0.8), border_radius=4)
                else:
                    pygame.draw.rect(surf, dark, (ax - r * 0.17, body.y + r * 0.2, r * 0.34, r * 0.9), border_radius=4)
                    pygame.draw.circle(surf, lt, (int(ax), int(body.y + r * 1.15)), max(3, int(r * 0.2)))
        if body_k == "round":
            pygame.draw.ellipse(surf, steel, body)
            pygame.draw.ellipse(surf, ink, body, ow)
        elif body_k == "dome":
            pygame.draw.rect(surf, steel, (body.x, body.centery, body.width, body.height / 2), border_radius=int(r * 0.2))
            pygame.draw.ellipse(surf, steel, (body.x, body.y, body.width, body.height * 1.1))
            pygame.draw.ellipse(surf, ink, (body.x, body.y, body.width, body.height * 1.1), ow)
        elif body_k == "tri":
            pts = [(body.centerx, body.y - r * 0.15), (body.right, body.bottom), (body.x, body.bottom)]
            pygame.draw.polygon(surf, steel, pts)
            pygame.draw.polygon(surf, ink, pts, ow)
        else:
            pygame.draw.rect(surf, steel, body, border_radius=int(r * (0.12 if body_k == "tall" else 0.25)))
            pygame.draw.rect(surf, ink, body, ow, border_radius=int(r * (0.12 if body_k == "tall" else 0.25)))
        pygame.draw.rect(surf, color, (body.x + r * 0.15, body.bottom - r * 0.34, body.width - r * 0.3, r * 0.2), border_radius=3)
        for sg in (-1, 1):
            pygame.draw.circle(surf, dark, (int(body.centerx + sg * body.width * 0.36), int(body.y + r * 0.2)), max(2, int(r * 0.06)))
        ey = body.y + body.height * (0.42 if body_k != "tri" else 0.62)
        flick = 0.75 + 0.25 * math.sin(t * 9)
        if eyes_k == "visor":
            visor = pygame.Rect(body.x + body.width * 0.12, ey - r * 0.22, body.width * 0.76, r * 0.46)
            pygame.draw.rect(surf, (16, 20, 30), visor, border_radius=int(r * 0.12))
            draw_led_pair(surf, visor.centerx, visor.centery, r * 0.36, r * 0.3, r * 0.2, led, self.look, r, flick)
        elif eyes_k == "cyclops":
            pygame.draw.circle(surf, (16, 20, 30), (ix, int(ey)), max(4, int(r * 0.42)))
            draw_led_pair(surf, ix, ey, 0, r * 0.4, r * 0.4, led, self.look, r, flick)
        elif eyes_k == "triple":
            pygame.draw.rect(surf, (16, 20, 30), (body.x + body.width * 0.1, ey - r * 0.2, body.width * 0.8, r * 0.4), border_radius=int(r * 0.12))
            draw_led_pair(surf, ix, ey, r * 0.4, r * 0.2, r * 0.2, led, self.look, r, flick)
            draw_led_pair(surf, ix, ey, 0, r * 0.2, r * 0.2, led, self.look, r, flick)
        else:
            pygame.draw.rect(surf, (16, 20, 30), (body.x + body.width * 0.08, ey - r * 0.12, body.width * 0.84, r * 0.24), border_radius=int(r * 0.1))
            draw_led_pair(surf, ix, ey, 0, body.width * 0.62, r * 0.12, led, self.look, r, flick)
        top = body.y
        blink = (255, 70, 60) if int(t * 3) % 2 == 0 else (110, 30, 30)
        if extra in (None, "plates", "cross", "bomb", "saw", "tank", "gas", "spikes"):
            pygame.draw.line(surf, dark, (ix, top), (ix, top - r * 0.4), 3)
            pygame.draw.circle(surf, blink, (ix, int(top - r * 0.45)), max(3, int(r * 0.1)))
        if extra == "spring":
            pts = [(ix + math.sin(k * 1.4 + t * 6) * r * 0.12, top - k * r * 0.1) for k in range(6)]
            pygame.draw.lines(surf, lt, False, pts, 2)
            pygame.draw.circle(surf, blink, (int(pts[-1][0]), int(pts[-1][1])), max(3, int(r * 0.12)))
        elif extra == "dish":
            pygame.draw.line(surf, dark, (ix, top), (ix, top - r * 0.5), 3)
            pygame.draw.arc(surf, lt, (ix - r * 0.35, top - r * 0.85, r * 0.7, r * 0.7), math.pi, math.tau, 3)
            pygame.draw.circle(surf, blink, (ix, int(top - r * 0.62)), max(2, int(r * 0.08)))
        elif extra == "bolt":
            for sg in (-1, 1):
                pygame.draw.line(surf, dark, (ix + sg * r * 0.4, top), (ix + sg * r * 0.55, top - r * 0.5), 3)
                pygame.draw.circle(surf, (255, 240, 110), (int(ix + sg * r * 0.55), int(top - r * 0.52)), max(3, int(r * 0.1 + 1.5 * math.sin(t * 15) ** 2)))
        elif extra == "cross":
            cw = max(2, int(r * 0.1))
            pygame.draw.rect(surf, (120, 255, 170), (body.centerx - cw, body.y + body.height * 0.58, cw * 2, r * 0.46))
            pygame.draw.rect(surf, (120, 255, 170), (body.centerx - r * 0.23, body.y + body.height * 0.58 + r * 0.18, r * 0.46, cw * 2))
        elif extra == "saw":
            sx_, sy_ = ix, int(body.centery + r * 0.2)
            for k in range(8):
                a = t * 12 + k * math.tau / 8
                pygame.draw.line(surf, lt, (sx_, sy_), (sx_ + math.cos(a) * r * 0.62, sy_ + math.sin(a) * r * 0.62), 3)
            pygame.draw.circle(surf, ink, (sx_, sy_), int(r * 0.62), 2)
        elif extra == "bomb":
            bx_, by_ = int(ix + r * 0.55), int(top - r * 0.2)
            pygame.draw.circle(surf, ink, (bx_, by_), max(4, int(r * 0.32)))
            pygame.draw.line(surf, (255, 190, 70), (bx_, by_ - r * 0.3), (bx_ + r * 0.12, by_ - r * 0.55), 2)
            pygame.draw.circle(surf, blink, (int(bx_ + r * 0.12), int(by_ - r * 0.57)), max(2, int(r * 0.07)))
        elif extra == "fuse":
            pygame.draw.line(surf, (255, 190, 70), (ix, top), (ix + r * 0.15, top - r * 0.5), 2)
            pygame.draw.circle(surf, blink, (int(ix + r * 0.15), int(top - r * 0.52)), max(3, int(r * 0.12)))
        elif extra == "tank":
            ta = self.look if boss else 0.0
            pygame.draw.rect(surf, dark, (ix - r * 0.45, top - r * 0.22, r * 0.9, r * 0.3), border_radius=4)
            pygame.draw.line(surf, ink, (ix, top - r * 0.08), (ix + math.cos(ta) * r * 1.1, top - r * 0.08 + math.sin(ta) * r * 0.5), max(4, int(r * 0.22)))
        elif extra == "gas":
            for sg in (-1, 1):
                gx_ = int(body.centerx + sg * body.width * 0.3)
                pygame.draw.rect(surf, dark, (gx_ - r * 0.1, body.y - r * 0.15, r * 0.2, r * 0.25))
                pygame.draw.circle(surf, (130, 225, 60), (gx_, int(body.y - r * 0.3 - (t * 20 + sg * 5) % (r * 0.5))), max(2, int(r * 0.08)))
        elif extra == "spikes":
            for q in range(-2, 3):
                pygame.draw.polygon(surf, lt, [(ix + q * r * 0.32 - r * 0.1, top + 2), (ix + q * r * 0.32 + r * 0.1, top + 2), (ix + q * r * 0.32, top - r * 0.32)])
        elif extra == "plates":
            for sg in (-1, 1):
                pygame.draw.rect(surf, lt, (body.centerx + sg * body.width * 0.3 - r * 0.22, body.y + r * 0.05, r * 0.44, r * 0.3), border_radius=3)
                pygame.draw.rect(surf, ink, (body.centerx + sg * body.width * 0.3 - r * 0.22, body.y + r * 0.05, r * 0.44, r * 0.3), 2, border_radius=3)
        if boss:
            for sg in (-1, 1):
                pygame.draw.line(surf, dark, (ix + sg * r * 0.5, top), (ix + sg * r * 0.7, top - r * 0.5), 4)
                pygame.draw.circle(surf, blink, (int(ix + sg * r * 0.7), int(top - r * 0.52)), max(3, int(r * 0.08)))
            pygame.draw.circle(surf, led, (ix, int(body.y + body.height * 0.78)), max(4, int(r * 0.16)))
            if extra == "gears":
                for k, sg in enumerate((-1, 1)):
                    gx_, gy_ = int(ix + sg * r * 0.85), int(body.y + r * 0.1)
                    for q in range(6):
                        a = t * (2 if k else -2) + q * math.tau / 6
                        pygame.draw.line(surf, lt, (gx_, gy_), (gx_ + math.cos(a) * r * 0.3, gy_ + math.sin(a) * r * 0.3), 4)
                    pygame.draw.circle(surf, ink, (gx_, gy_), int(r * 0.3), 2)
            if extra == "pods":
                for sg in (-1, 1):
                    for q in range(3):
                        pygame.draw.rect(surf, ink, (ix + sg * r * 0.3 + (q - 1) * r * 0.2 - r * 0.08, top - r * 0.7, r * 0.16, r * 0.4), border_radius=3)
                        pygame.draw.circle(surf, (255, 120, 60), (int(ix + sg * r * 0.3 + (q - 1) * r * 0.2), int(top - r * 0.7)), max(2, int(r * 0.07)))

    def draw_necro(self, surf, ix, iy, r, color, t):
        robe = [(ix - r * 1.1, iy + r * 1.05), (ix + r * 1.1, iy + r * 1.05), (ix + r * 0.5, iy - r * 0.2),
                (ix - r * 0.5, iy - r * 0.2)]
        pygame.draw.polygon(surf, color, robe)
        pygame.draw.polygon(surf, GOLD_COLOR, robe, 3)
        pygame.draw.polygon(surf, _dk(color, 0.7), [(ix - r * .9, iy + r * .95), (ix + r * .9, iy + r * .95),
                                                    (ix, iy + r * .55)])
        pygame.draw.polygon(surf, _dk(color, 0.7), [(ix, iy - r * 1.3), (ix + r * 0.85, iy - r * 0.1),
                                                    (ix - r * 0.85, iy - r * 0.1)])
        pygame.draw.circle(surf, (228, 228, 212), (ix, int(iy - r * 0.4)), int(r * 0.52))
        draw_face(surf, ix, iy - r * 0.4, r * 0.52, self.look, "skull", 1.0, t)
        stx = ix + r * 1.15
        pygame.draw.line(surf, (110, 80, 50), (stx, iy + r), (stx, iy - r), 5)
        pygame.draw.circle(surf, (190, 90, 255), (int(stx), int(iy - r * 1.05)), max(4, int(r * 0.22)))
        for i in range(3):
            a = t * 2 + i * 2.094
            pygame.draw.circle(surf, (170, 80, 240), (int(ix + math.cos(a) * r * 1.35),
                                                      int(iy + math.sin(a) * r * 0.5 - r * 0.1)), 6)

    def draw_boss_blob(self, surf, ix, iy, r, color, t):
        for k in (-1, 1):
            pygame.draw.polygon(surf, (235, 225, 200), [(ix + k * r * 0.35, iy - r * 0.8),
                                                        (ix + k * r * 0.95, iy - r * 1.35),
                                                        (ix + k * r * 0.85, iy - r * 0.45)])
        pygame.draw.circle(surf, color, (ix, iy), r)
        pygame.draw.circle(surf, GOLD_COLOR, (ix, iy), r, 4)
        if self.boss_kind == "healer":
            pygame.draw.circle(surf, (120, 255, 170), (ix, iy), int(r + 8 + 3 * math.sin(t * 4)), 2)
            pygame.draw.rect(surf, WHITE, (ix - 3, int(iy - r * 0.84), 6, int(r * 0.3)))
            pygame.draw.rect(surf, WHITE, (int(ix - r * 0.15), int(iy - r * 0.72), int(r * 0.3), 6))
        draw_face(surf, ix, iy + r * 0.1, r * 0.85, self.look, "angry", 1.0, t)

    def draw_regular(self, surf, ix, iy, r, color, outline, ow, mood, t):
        """Badan musuh biasa (bukan boss). Dipanggil langsung atau untuk membuat sprite cache."""
        shape = self.shape
        special = self.is_boss or self.elite
        if ROBOT_MODE:
            self.draw_robot(surf, ix, iy, r, color, t)
            return
        fr = r
        fcx, fcy = ix, iy
        if shape not in ("bat", "ghost") and self.kind.get("variant") != "runner":
            for sg_ in (-1, 1):
                ft = math.sin(self.walk_phase + (0 if sg_ > 0 else math.pi)) * r * 0.16
                pygame.draw.ellipse(surf, (35, 30, 30), (ix + sg_ * r * 0.42 - r * 0.22, iy + r * 0.88 + ft, r * 0.44, r * 0.26))
        if shape == "square":
            rect = pygame.Rect(ix - r, iy - r, r * 2, r * 2)
            pygame.draw.rect(surf, color, rect, border_radius=4)
            pygame.draw.rect(surf, outline, rect, width=ow, border_radius=4)
        elif shape in ("triangle", "diamond"):
            a = self.face
            if shape == "triangle":
                pts = [(ix + math.cos(a) * r * 1.25, iy + math.sin(a) * r * 1.25),
                       (ix + math.cos(a + 2.45) * r, iy + math.sin(a + 2.45) * r),
                       (ix + math.cos(a - 2.45) * r, iy + math.sin(a - 2.45) * r)]
            else:
                pts = [(ix, iy - r * 1.2), (ix + r, iy), (ix, iy + r * 1.2), (ix - r, iy)]
            pygame.draw.polygon(surf, color, pts)
            pygame.draw.polygon(surf, outline, pts, ow)
            fr = r * 0.8
            if self.is_thunder:
                pygame.draw.polygon(surf, WHITE, [(ix + 3, iy - r * 1.7), (ix - 5, iy - r * 1.15),
                                                  (ix + 1, iy - r * 1.15), (ix - 3, iy - r * 0.7),
                                                  (ix + 6, iy - r * 1.3), (ix + 1, iy - r * 1.3)])
        elif shape == "bat":
            flap = math.sin(t * 14 + self.phase_t) * r * 0.5
            pygame.draw.polygon(surf, color, [(ix, iy), (ix - r * 1.7, iy - r * 0.6 + flap), (ix - r * 0.8, iy + r * 0.5)])
            pygame.draw.polygon(surf, color, [(ix, iy), (ix + r * 1.7, iy - r * 0.6 + flap), (ix + r * 0.8, iy + r * 0.5)])
            pygame.draw.circle(surf, color, (ix, iy), r)
            pygame.draw.circle(surf, outline, (ix, iy), r, ow)
            for k in (-1, 1):
                pygame.draw.polygon(surf, color, [(ix + k * r * 0.2, iy - r * 0.8), (ix + k * r * 0.8, iy - r * 1.5),
                                                  (ix + k * r * 0.9, iy - r * 0.5)])
            fr = r * 0.9
        elif shape == "giant":
            fcx, fcy, fr = self.draw_giant_body(surf, ix, iy, r, color, outline, ow, t)
            if self.kind.get("variant") == "cyclops":
                fr = 0
        elif shape == "skull":
            jaw = pygame.Rect(ix - int(r * 0.55), iy + int(r * 0.5), int(r * 1.1), int(r * 0.55))
            pygame.draw.rect(surf, color, jaw, border_radius=4)
            pygame.draw.rect(surf, outline, jaw, ow, border_radius=4)
            pygame.draw.circle(surf, color, (ix, iy), r)
            pygame.draw.circle(surf, outline, (ix, iy), r, ow)
            fr = r * 0.95
        elif shape == "warden":
            pulse = 0.5 + 0.5 * math.sin(t * 3)
            if self.bstate == "charge":
                pulse = 1.0
            for k in (-1, 1):
                pygame.draw.line(surf, _dk(color, 0.8), (ix + k * r * 0.55, iy - r * 0.2), (ix + k * r * 1.15, iy + r * 0.9), max(6, int(r * 0.3)))
                pygame.draw.circle(surf, _dk(color, 0.7), (ix + int(k * r * 1.15), iy + int(r * 0.95)), int(r * 0.28))
                pygame.draw.polygon(surf, _dk(color, 0.65), [(ix + k * r * 0.45, iy - r * 0.95), (ix + k * r * 1.25, iy - r * 1.35),
                                                              (ix + k * r * 0.95, iy - r * 0.7)])
            torso = [(ix - r * 0.8, iy + r * 1.0), (ix + r * 0.8, iy + r * 1.0), (ix + r * 0.6, iy - r * 0.55), (ix - r * 0.6, iy - r * 0.55)]
            pygame.draw.polygon(surf, color, torso)
            pygame.draw.polygon(surf, (10, 25, 30), torso, ow)
            for k in range(3):
                yy = iy - r * 0.1 + k * r * 0.28
                pygame.draw.line(surf, (70, 220, 215), (ix - r * 0.5, yy), (ix + r * 0.5, yy), 2)
            pygame.draw.circle(surf, (60, int(140 + 90 * pulse), int(150 + 80 * pulse)), (ix, int(iy + r * 0.15)), int(r * (0.2 + 0.08 * pulse)))
            head = pygame.Rect(ix - r * 0.6, iy - r * 1.05, r * 1.2, r * 0.7)
            pygame.draw.rect(surf, _lt(color, 0.05), head, border_radius=6)
            pygame.draw.rect(surf, (10, 25, 30), head, ow, border_radius=6)
            for k in (-1, 1):
                pygame.draw.ellipse(surf, (8, 20, 24), (ix + k * r * 0.25 - 4, iy - r * 0.82, 8, 12))
            fr = 0
        elif shape == "spider":
            ph = self.walk_phase
            leg_col = _dk(color, 0.65)
            lw_ = max(2, int(r * 0.14))
            for sd_ in (-1, 1):
                for k_ in range(4):
                    sw_ = math.sin(ph + k_ * 1.3 + (0 if sd_ > 0 else math.pi)) * r * 0.22
                    knee = (ix + sd_ * r * 1.05, iy + (k_ - 1.5) * r * 0.42 - r * 0.62 + sw_)
                    foot = (ix + sd_ * r * 1.75, iy + (k_ - 1.5) * r * 0.62 + r * 0.30 + sw_ * 0.6)
                    pygame.draw.lines(surf, leg_col, False, [(ix, iy), knee, foot], lw_)
            pygame.draw.circle(surf, color, (ix, int(iy + r * 0.2)), int(r * 0.88))
            pygame.draw.circle(surf, outline, (ix, int(iy + r * 0.2)), int(r * 0.88), ow)
            pygame.draw.polygon(surf, (205, 55, 55), [(ix, int(iy + r * 0.2)), (ix - r * 0.22, iy + r * 0.55), (ix + r * 0.22, iy + r * 0.55)])
            pygame.draw.polygon(surf, (205, 55, 55), [(ix, int(iy + r * 0.2)), (ix - r * 0.22, iy - r * 0.05), (ix + r * 0.22, iy - r * 0.05)])
            hy = int(iy - r * 0.62)
            pygame.draw.circle(surf, color, (ix, hy), int(r * 0.52))
            pygame.draw.circle(surf, outline, (ix, hy), int(r * 0.52), ow)
            fcx, fcy, fr = ix, hy, r * 0.5
        elif shape == "tank":
            for ty_ in (-1, 1):
                tread = pygame.Rect(ix - r - 3, iy + (-int(r * 0.98) if ty_ < 0 else int(r * 0.58)), r * 2 + 6, int(r * 0.4))
                pygame.draw.rect(surf, (45, 48, 52), tread, border_radius=5)
                for wx in range(-3, 4):
                    pygame.draw.circle(surf, (110, 115, 120), (ix + int(wx * r * 0.3), tread.centery), max(2, int(r * 0.12)))
            body = pygame.Rect(ix - r, iy - int(r * 0.65), r * 2, int(r * 1.3))
            pygame.draw.rect(surf, color, body, border_radius=6)
            pygame.draw.rect(surf, outline, body, ow, border_radius=6)
            pygame.draw.line(surf, _dk(color, 0.5), (ix, iy), (ix + math.cos(self.face) * r * 1.35,
                                                                iy + math.sin(self.face) * r * 1.35), max(4, int(r * 0.2)))
            pygame.draw.circle(surf, _lt(color, 0.12), (ix, iy), int(r * 0.55))
            pygame.draw.circle(surf, outline, (ix, iy), int(r * 0.55), ow)
            fr = 0 if self.gear == "twinheads" else r * 0.55
        else:
            pygame.draw.circle(surf, color, (ix, iy), r)
            if shape == "ghost":
                for k in (-1, 0, 1):
                    pygame.draw.circle(surf, color, (ix + k * int(r * 0.6), iy + int(r * 0.85)), max(2, r // 3))
            pygame.draw.circle(surf, outline, (ix, iy), r, ow)
            if shape == "ninja":
                pygame.draw.line(surf, (230, 50, 50), (ix - r, iy - 2), (ix + r, iy - 2), 4)
        if shape == "ninja":
            draw_face(surf, ix, iy, r, self.look, "ninja", 0.0, t)
        else:
            draw_face(surf, fcx, fcy, fr, self.look, self.face_style, mood, t)

    def cacheable(self):
        return (not self.is_boss) and self.air_h <= 0

    def get_sprite(self, color, outline, ow, mood, t):
        r = self.radius
        shape = self.shape
        var = self.kind.get("variant")
        wb = int(self.walk_phase / (math.pi / 2)) % 4
        fb = int(((self.face % math.tau) / math.tau) * 24) % 24 if (shape == "triangle" or var == "runner") else 0
        animated = shape == "bat" or ROBOT_MODE or self.gear in SPRITE_GEARS
        ab = int(t * 8) % 4 if animated else 0
        armored = self.armor_max > 0 and self.armor > 0 and not ROBOT_MODE
        key = (self.kind["name"], r, color, outline == GOLD_COLOR, mood > 0.6, wb, fb, ab, ROBOT_MODE, armored)
        ent = _SPRITES.get(key)
        if ent is not None:
            del _SPRITES[key]
            _SPRITES[key] = ent
        else:
            if len(_SPRITES) > 520:
                _trim(_SPRITES, 380)
            pad = int(r * 1.8) + 18
            spr = pygame.Surface((2 * pad, 2 * pad), pygame.SRCALPHA)
            saved = (self.walk_phase, self.face, self.phase_t)
            self.walk_phase, self.face, self.phase_t = wb * (math.pi / 2), fb * math.tau / 24, 0.0
            tt = 100.0 + ab * 0.0715
            global _FACE_REC
            _FACE_REC = []
            try:
                self.draw_regular(spr, pad, pad, r, color, outline, ow, mood, tt)
                recorded = _FACE_REC
                _FACE_REC = None
                faces = []
                for f in recorded:
                    f = list(f)
                    f[1] -= pad
                    f[2] -= pad
                    faces.append(tuple(f))
                if armored:
                    draw_armor_plates(spr, pad, pad, r, self.kind["name"], sum(color) < 380)
                if self.gear in SPRITE_GEARS and not ROBOT_MODE:
                    draw_gear(spr, self.gear, pad, pad, r, self.face, tt, self)
            finally:
                _FACE_REC = None
                self.walk_phase, self.face, self.phase_t = saved
            try:
                spr = spr.convert_alpha()
            except Exception:
                pass
            ent = _SPRITES[key] = (spr, pad, tuple(faces))
        return ent

    def draw(self, surf, cam_x, cam_y):
        sx, sy = self.x - cam_x, self.y - cam_y
        mg = max(130, self.radius + 80)
        if not (-mg <= sx <= WIDTH + mg and -mg - 20 <= sy <= HEIGHT + mg):
            return
        self._cam = (cam_x, cam_y)
        global _FACE_REC
        _FACE_REC = None
        if self.preview:
            self.look = 0.5
        else:
            self.look = math.atan2(CENTER[1] - sy, CENTER[0] - sx)
        if self._lx is not None:
            self.walk_phase += math.hypot(self.x - self._lx, self.y - self._ly) * 0.16
        self._lx, self._ly = self.x, self.y
        ix, iy = int(sx), int(sy)
        r = self.radius
        color = FREEZE_COLOR if self.frozen_timer > 0 else self.color
        shape = self.shape
        special = self.is_boss or self.elite
        outline = GOLD_COLOR if special else BLACK
        ow = 3 if special else 2
        t = pygame.time.get_ticks() / 1000.0
        mood = 1.0 if self.is_boss else min(0.9, 0.3 + 0.03 * self.elv + (0.3 if self.elite else 0.0))

        if self.dash_state == 1:
            pygame.draw.line(surf, (255, 70, 70), (ix, iy), (ix + self.ddx * 220, iy + self.ddy * 220), 3)

        if self.air_h > 0:
            pygame.draw.ellipse(surf, (8, 8, 14), (ix - r, iy + r // 2, r * 2, max(6, r // 2)))
            iy -= int(self.air_h)

        gear_done = False
        if ROBOT_MODE and self.is_boss:
            self.draw_robot(surf, ix, iy, r, color, t)
        elif self.is_brute_boss:
            self.draw_brute(surf, ix, iy, r, color, t)
        elif self.is_necro_boss:
            self.draw_necro(surf, ix, iy, r, color, t)
        elif self.boss_kind in ("guardian", "minigun", "exec", "fire", "skel", "final"):
            self.draw_boss_custom(surf, ix, iy, r, color, t)
        elif self.is_boss:
            self.draw_boss_blob(surf, ix, iy, r, color, t)
        else:
            if self.cacheable():
                spr, pad, faces = self.get_sprite(color, outline, ow, mood, t)
                surf.blit(spr, (ix - pad, iy - pad))
                if faces:
                    replay_faces(surf, faces, ix, iy, self.look, t)
                gear_done = self.gear in SPRITE_GEARS and not ROBOT_MODE
            else:
                self.draw_regular(surf, ix, iy, r, color, outline, ow, mood, t)

        if self.gear and not self.is_boss and not ROBOT_MODE and not gear_done:
            draw_gear(surf, self.gear, ix, iy, r, self.face, t, self)
        if self.ethereal_t > 0:
            for k in range(14):
                a = k * math.tau / 14 + t * 2
                pygame.draw.circle(surf, (210, 235, 255), (int(ix + math.cos(a) * (r + 6)), int(iy + math.sin(a) * (r + 6))), 2)
        if self.is_boss and not self.preview and self.shield > 0 and self.shield_max > 0:
            bw_ = max(60, r * 2)
            pygame.draw.rect(surf, (30, 35, 50), (ix - bw_ / 2, iy + r + 8, bw_, 5))
            pygame.draw.rect(surf, (120, 200, 255), (ix - bw_ / 2, iy + r + 8, bw_ * self.shield / self.shield_max, 5))
        if self.crystal_buff:
            cc = {"strong": (255, 80, 70), "fast": (255, 230, 90), "both": (200, 100, 255)}[self.crystal_buff]
            pygame.draw.circle(surf, cc, (ix, iy), r + 8 + int(2 * math.sin(t * 8)), 2)
        if self.tell and self.is_boss:
            flash = int(t * 8) % 2 == 0
            tc = (255, 70, 60) if flash else (255, 220, 90)
            rr = r + 14 + int(5 * math.sin(t * 12))
            pygame.draw.circle(surf, tc, (ix, iy), rr, 5)
            for kk in range(8):
                a = kk * math.tau / 8 + t * 3
                pygame.draw.line(surf, tc, (ix + math.cos(a) * (rr + 4), iy + math.sin(a) * (rr + 4)), (ix + math.cos(a) * (rr + 16), iy + math.sin(a) * (rr + 16)), 4)
            txt = font_med.render("AWAS: " + self.tell, True, tc)
            bw = txt.get_width() + 22
            ty0 = max(8, iy - r - 62)
            pygame.draw.rect(surf, (12, 8, 18), (ix - bw / 2, ty0, bw, 36), border_radius=8)
            pygame.draw.rect(surf, tc, (ix - bw / 2, ty0, bw, 36), 3, border_radius=8)
            surf.blit(txt, (ix - txt.get_width() / 2, ty0 + 6))
        if self.haste > 0:
            pygame.draw.circle(surf, (255, 225, 120), (ix, iy), r + 6, width=1)
        if not self.preview:
            if self.poison_t > 0:
                draw_poison_fx(surf, ix, iy, r, t, self.phase_t)
            if self.burn_t > 0:
                draw_burn_fx(surf, ix, iy, r, t, self.phase_t)
            if self.steam_t > 0:
                draw_steam_fx(surf, ix, iy, r, self.steam_t)

        if not self.is_boss and not self.preview:
            w = r * 2
            bar_y = sy - r - 10
            if self.shield_max > 0 and self.shield > 0:
                pygame.draw.rect(surf, (40, 40, 50), (sx - w / 2, bar_y - 5, w, 4))
                pygame.draw.rect(surf, (90, 170, 255), (sx - w / 2, bar_y - 5, w * self.shield / self.shield_max, 4))
            if self.armor_max > 0 and self.armor > 0:
                ratio = max(self.armor / self.armor_max, 0)
                pygame.draw.rect(surf, (40, 40, 50), (sx - w / 2, bar_y, w, 4))
                pygame.draw.rect(surf, ARMOR_GRAY, (sx - w / 2, bar_y, w * ratio, 4))
            elif self.hp < self.max_hp or self.shield > 0:
                ratio = max(self.hp / self.max_hp, 0)
                pygame.draw.rect(surf, HP_RED, (sx - w / 2, bar_y, w, 4))
                pygame.draw.rect(surf, HP_GREEN, (sx - w / 2, bar_y, w * ratio, 4))
            if (r >= 9 or self.elite) and not self.preview and (SETTINGS["lvlabel"] > 0 or ROBOT_MODE) and (PERF["lod"] == 0 or self.elite or ROBOT_MODE):
                lt = _bot_label(self.kind["name"]) if ROBOT_MODE else _lv_label(self.elv, self.elite)
                surf.blit(lt, (sx - lt.get_width() / 2, bar_y - 12))


class EnemyProjectile:
    def __init__(self, x, y, tx, ty, speed, damage, color=ENEMY_PROJ_COLOR, radius=6, life=12.0, style=None):
        self.style = style
        self.x, self.y = x, y
        dx, dy = tx - x, ty - y
        dist = math.hypot(dx, dy) or 1
        self.vx, self.vy = dx / dist * speed, dy / dist * speed
        self.damage = damage
        self.radius = radius
        self.color = color
        self.life = life
        self.alive = True
        self.home = 0.0
        self.home_target = None

    def update(self, dt):
        if self.home and self.home_target:
            sp = math.hypot(self.vx, self.vy) or 1.0
            cur = math.atan2(self.vy, self.vx)
            want = math.atan2(self.home_target[1] - self.y, self.home_target[0] - self.x)
            diff = (want - cur + math.pi) % math.tau - math.pi
            cur += max(-self.home, min(self.home, diff)) * dt * 60
            self.vx, self.vy = math.cos(cur) * sp, math.sin(cur) * sp
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        self.life -= dt
        if self.life <= 0:
            self.alive = False

    def draw(self, surf, cam_x, cam_y):
        sx, sy = self.x - cam_x, self.y - cam_y
        if -30 <= sx <= WIDTH + 30 and -30 <= sy <= HEIGHT + 30:
            if self.style:
                draw_proj_shape(surf, self.style, sx, sy, math.atan2(self.vy, self.vx), self.radius, self.color,
                                pygame.time.get_ticks() / 1000.0)
                return
            pygame.draw.circle(surf, self.color, (int(sx), int(sy)), self.radius)
            pygame.draw.circle(surf, WHITE if self.radius > 6 else BLACK, (int(sx), int(sy)), self.radius, width=1)


# Tampilan peluru skill EVOLUSI: warna + lambang berbeda dari bentuk dasar (bukan sekadar jumlah lebih banyak)
EVO_LOOK = {
    "OrbWeapon": ((110, 255, 225), "diamond"), "MultiArrowWeapon": ((255, 175, 60), "star"),
    "FireballWeapon": ((90, 170, 255), "flame"), "IceSpikeWeapon": ((200, 150, 255), "diamond"),
    "KnifeWeapon": ((255, 90, 120), "star"), "HomingSpiritWeapon": ((130, 255, 190), "ring"),
    "BounceOrbWeapon": ((255, 235, 90), "ring"), "MeteorWeapon": ((255, 70, 40), "flame"),
    "SpearWeapon": ((255, 250, 190), "star"), "FireBirdWeapon": ((255, 60, 120), "flame"),
}


class Projectile:
    def __init__(self, x, y, tx, ty, speed, damage, color=ORB_COLOR,
                 splash_radius=0, splash_damage=0, freeze_on_hit=False, freeze_duration=0,
                 radius=7, pierce=0, life=None, homing=False, bounce=0, style=None):
        self.style = style
        self.x, self.y = x, y
        dx, dy = tx - x, ty - y
        dist = math.hypot(dx, dy) or 1
        self.speed = speed
        self.vx, self.vy = dx / dist * speed, dy / dist * speed
        self.damage = damage
        self.radius = radius
        self.color = color
        self.alive = True
        self.splash_radius = splash_radius
        self.splash_damage = splash_damage
        self.freeze_on_hit = freeze_on_hit
        self.freeze_duration = freeze_duration
        self.pierce = pierce
        self.life = life
        self.homing = homing
        self.bounce = bounce
        self.hit_ids = set()
        self.evo_look = None

    def update(self, dt, game=None):
        if self.life is not None:
            self.life -= dt
            if self.life <= 0:
                self.alive = False
                return
        if self.homing and game is not None:
            best, best_d = None, 1e12
            for e in game.enemies:
                if e.dead or id(e) in self.hit_ids:
                    continue
                d = dist_sq(e.x, e.y, self.x, self.y)
                if d < best_d:
                    best, best_d = e, d
            if best is not None:
                want = math.atan2(best.y - self.y, best.x - self.x)
                cur = math.atan2(self.vy, self.vx)
                diff = (want - cur + math.pi) % math.tau - math.pi
                step = 0.14 * dt * 60
                cur += max(-step, min(step, diff))
                self.vx, self.vy = math.cos(cur) * self.speed, math.sin(cur) * self.speed
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60

    def draw(self, surf, cam_x, cam_y):
        sx, sy = self.x - cam_x, self.y - cam_y
        if -40 <= sx <= WIDTH + 40 and -40 <= sy <= HEIGHT + 40:
            t = pygame.time.get_ticks() / 1000.0
            ang = math.atan2(self.vy, self.vx)
            if self.evo_look is not None:
                col, glyph = self.evo_look
                r = self.radius
                for j in range(1, 5):
                    P_ = pygame.draw
                    P_.circle(surf, tuple(int(c * (1 - j * 0.2)) for c in col), (int(sx - math.cos(ang) * j * r * 0.9), int(sy - math.sin(ang) * j * r * 0.9)), max(2, int(r * (1 - j * 0.17))))
                if glyph == "diamond":
                    for k in range(4):
                        a = t * 5 + k * math.pi / 2
                        px, py = sx + math.cos(a) * (r + 7), sy + math.sin(a) * (r + 7)
                        pygame.draw.polygon(surf, col, [(px, py - 4), (px + 3, py), (px, py + 4), (px - 3, py)])
                elif glyph == "star":
                    pts = []
                    for k in range(10):
                        a = t * 4 + k * math.pi / 5
                        rr = r + 9 if k % 2 == 0 else r + 3
                        pts.append((sx + math.cos(a) * rr, sy + math.sin(a) * rr))
                    pygame.draw.polygon(surf, col, pts, 2)
                elif glyph == "flame":
                    for k in range(5):
                        a = ang + math.pi + (k - 2) * 0.45
                        L = r + 8 + 5 * math.sin(t * 15 + k)
                        pygame.draw.line(surf, col, (sx, sy), (sx + math.cos(a) * L, sy + math.sin(a) * L), 3)
                else:
                    pygame.draw.circle(surf, col, (int(sx), int(sy)), r + 6, 2)
                    pygame.draw.circle(surf, (255, 255, 255), (int(sx), int(sy)), r + 11, 1)
                draw_proj_shape(surf, self.style, sx, sy, ang, r + 2, tuple(min(255, c + 60) for c in col), t)
                return
            draw_proj_shape(surf, self.style, sx, sy, ang, self.radius, self.color, t)


class PoisonZone:
    def __init__(self, x, y, radius, dmg_per_tick, tick_interval, duration, color=None):
        self.x, self.y = x, y
        self.radius = radius
        self.dmg_per_tick = dmg_per_tick
        self.tick_interval = tick_interval
        self.tick_timer = 0.0
        self.duration = duration
        self.color = color or POISON_COLOR

    def update(self, dt, game):
        self.duration -= dt
        self.tick_timer -= dt
        if self.tick_timer <= 0:
            self.tick_timer = self.tick_interval
            r2 = self.radius ** 2
            for e in game.enemies:
                if e.dead:
                    continue
                if dist_sq(e.x, e.y, self.x, self.y) <= r2:
                    game.damage_enemy(e, self.dmg_per_tick, show_text=self.dmg_per_tick >= 8)
                    if not e.dead:
                        if self.color == FIRE_COLOR or _is_fire_col(self.color):
                            game.ignite_enemy(e, max(2.0, self.dmg_per_tick * 2.0), 2.5)
                        else:
                            game.poison_enemy(e, max(2.0, self.dmg_per_tick * 2.0), 3.0)

    def draw(self, surf, cam_x, cam_y):
        sx, sy = self.x - cam_x, self.y - cam_y
        if not (-100 <= sx <= WIDTH + 100 and -100 <= sy <= HEIGHT + 100):
            return
        t = pygame.time.get_ticks() / 1000.0
        ix, iy, r = int(sx), int(sy), int(self.radius)
        if self.color == FIRE_COLOR:
            for i in range(5):
                a = i * 1.256 + self.x * 0.01
                fx = ix + math.cos(a) * r * 0.55
                fy = iy + math.sin(a) * r * 0.35
                h = r * (0.75 + 0.25 * math.sin(t * 9 + i * 2))
                pygame.draw.polygon(surf, (230, 70, 25), [(fx - r * 0.2, fy), (fx + r * 0.2, fy), (fx, fy - h)])
                pygame.draw.polygon(surf, (255, 200, 80), [(fx - r * 0.1, fy), (fx + r * 0.1, fy), (fx, fy - h * 0.6)])
            pygame.draw.circle(surf, (230, 70, 25), (ix, iy), r, width=2)
            return
        fill, edge = _dk(self.color, 0.45), _lt(self.color, 0.25)
        pygame.draw.circle(surf, edge, (ix, iy), r, width=2)
        for i in range(7):
            a = t * 0.6 + i * 0.897
            pr = int(r * (0.30 + 0.05 * math.sin(t * 2 + i)))
            px, py = int(ix + math.cos(a) * r * 0.55), int(iy + math.sin(a) * r * 0.55)
            pygame.draw.circle(surf, fill, (px, py), pr)
            pygame.draw.circle(surf, edge, (px, py), pr, 2)
        pygame.draw.circle(surf, fill, (ix, iy), int(r * 0.38))
        pygame.draw.circle(surf, edge, (ix, iy), int(r * 0.38), 2)


ARENA_HW, ARENA_HH = 680, 380


def rot_pts(pts, cx, cy, ang):
    c, s = math.cos(ang), math.sin(ang)
    return [(cx + px * c - py * s, cy + px * s + py * c) for (px, py) in pts]


class Hazard:
    """Bentuk berbahaya: tahap PERINGATAN (garis tipis) lalu AKTIF (melukai).
    kind: beam (sinar), ring (gelombang cincin), blast (lingkaran), rect (balok)."""

    def __init__(self, kind, x, y, warn, active, damage, color=(255, 60, 120), **kw):
        self.kind = kind
        self.x, self.y = x, y
        self.warn = max(0.05, warn)
        self.active_dur = max(0.05, active)
        self.t = self.warn
        self.phase = "warn"
        self.damage = damage
        self.color = color
        self.angle = kw.get("angle", 0.0)
        self.length = kw.get("length", 1600)
        self.width = kw.get("width", 30)
        self.spin = kw.get("spin", 0.0)
        self.max_radius = kw.get("max_radius", 600)
        self.thickness = kw.get("thickness", 24)
        self.radius = kw.get("radius", 80)
        self.w = kw.get("w", 100)
        self.h = kw.get("h", 100)
        self.cur_r = 0.0
        self.sky = kw.get("sky", False)
        self.slow = kw.get("slow", False)
        self.follow = kw.get("follow")
        self.aura = bool(kw.get("aura", False))
        self.alive = True

    def hits(self, px, py, pr):
        if self.kind == "beam":
            x2 = self.x + math.cos(self.angle) * self.length
            y2 = self.y + math.sin(self.angle) * self.length
            return seg_dist_sq(px, py, self.x, self.y, x2, y2) <= (self.width / 2 + pr) ** 2
        if self.kind == "ring":
            d = math.hypot(px - self.x, py - self.y)
            return abs(d - self.cur_r) <= self.thickness / 2 + pr
        if self.kind in ("blast", "gas"):
            return dist_sq(px, py, self.x, self.y) <= (self.radius + pr) ** 2
        return abs(px - self.x) <= self.w / 2 + pr and abs(py - self.y) <= self.h / 2 + pr

    def update(self, dt, game):
        self.t -= dt
        if self.follow is not None:
            if self.follow.dead or self.follow.hp <= 0:
                self.alive = False
                return
            self.x, self.y = self.follow.x, self.follow.y
        if self.spin:
            self.angle += self.spin * dt
        if self.phase == "warn":
            if self.t <= 0:
                self.phase = "active"
                self.t = self.active_dur
        else:
            if self.kind == "ring":
                self.cur_r = self.max_radius * (1 - max(self.t, 0.0) / self.active_dur)
            b = game.badang
            if self.hits(b.x, b.y, b.size * 0.55) and not in_merchant_shield(b.x, b.y):
                if self.slow:
                    b.slow_t = max(b.slow_t, 1.8)
                if self.damage > 0:
                    b.take_damage(self.damage)
                if self.kind in ("gas", "blast") and self.damage > 0:
                    if _is_poison_col(self.color):
                        b.set_poison(max(2.0, self.damage * 0.4), 3.5)
                    elif _is_fire_col(self.color):
                        b.set_burn(max(2.0, self.damage * 0.4), 2.5)
            if self.t <= 0:
                self.alive = False

    def draw(self, surf, cam_x, cam_y):
        sx, sy = self.x - cam_x, self.y - cam_y
        warn = self.phase == "warn"
        col = self.color
        if self.sky and not warn:
            draw_bolt(surf, sx + 12, sy - 560, sx, sy, col, 7, 9, 22)
        if self.kind == "beam":
            ex = sx + math.cos(self.angle) * self.length
            ey = sy + math.sin(self.angle) * self.length
            if warn:
                blink = (int(self.t * 10) % 2 == 0)
                pygame.draw.line(surf, WHITE if blink else col, (sx, sy), (ex, ey), 2)
            else:
                w = max(4, int(self.width * min(1.0, 0.4 + self.t / self.active_dur)))
                pygame.draw.line(surf, col, (sx, sy), (ex, ey), w)
                pygame.draw.line(surf, WHITE, (sx, sy), (ex, ey), max(2, w // 3))
        elif self.kind == "ring":
            if warn:
                pygame.draw.circle(surf, col, (int(sx), int(sy)), 26, 2)
            else:
                r = max(2, int(self.cur_r))
                pygame.draw.circle(surf, col, (int(sx), int(sy)), r, max(4, int(self.thickness)))
                pygame.draw.circle(surf, WHITE, (int(sx), int(sy)), r, 2)
        elif self.kind == "gas":
            if not (-300 <= sx <= WIDTH + 300 and -300 <= sy <= HEIGHT + 300):
                return
            r = int(self.radius)
            tt = pygame.time.get_ticks() / 1000.0
            if self.aura:
                # AURA: menempel pada pemiliknya, cincin penuh 360 derajat dengan titik-titik yang berputar mengelilinginya
                pygame.draw.circle(surf, _dk(col, 0.35), (int(sx), int(sy)), r, 3)
                pygame.draw.circle(surf, col, (int(sx), int(sy)), max(2, r - 5), 2)
                n_o = 6 if HAZ_LOD else 12
                for i in range(n_o):
                    a = tt * 1.8 + i * math.tau / n_o
                    pygame.draw.circle(surf, col, (int(sx + math.cos(a) * (r - 3)), int(sy + math.sin(a) * (r - 3))), 4)
                    pygame.draw.circle(surf, WHITE, (int(sx + math.cos(a) * (r - 3)), int(sy + math.sin(a) * (r - 3))), 4, 1)
                for i in range(4):
                    a = -tt * 1.1 + i * math.tau / 4
                    pygame.draw.circle(surf, _dk(col, 0.6), (int(sx + math.cos(a) * r * 0.55), int(sy + math.sin(a) * r * 0.55)), max(3, int(r * 0.12)))
                return
            if warn:
                pygame.draw.circle(surf, col, (int(sx), int(sy)), r, 2)
            else:
                fade = min(1.0, self.t / 1.5)
                dark = (int(40 + 40 * fade), int(90 + 50 * fade), int(30 + 20 * fade))
                pygame.draw.circle(surf, col, (int(sx), int(sy)), r, 2)
                for i in range(0, 10, 2 if HAZ_LOD else 1):
                    a = tt * 0.7 + i * 0.628
                    rr = r * (0.45 + 0.35 * ((i * 37) % 10) / 10.0)
                    pr = int(r * (0.2 + 0.06 * math.sin(tt * 2 + i)))
                    p = (int(sx + math.cos(a) * rr * 0.8), int(sy + math.sin(a) * rr * 0.8))
                    pygame.draw.circle(surf, dark, p, pr)
                    pygame.draw.circle(surf, col, p, pr, 2)
        elif self.kind == "blast":
            if not (-300 <= sx <= WIDTH + 300 and -300 <= sy <= HEIGHT + 300):
                return
            r = int(self.radius)
            if warn:
                prog = 1 - max(self.t, 0.0) / self.warn
                pygame.draw.circle(surf, col, (int(sx), int(sy)), r, 2)
                pygame.draw.circle(surf, col, (int(sx), int(sy)), max(2, int(r * prog)), 1)
            else:
                pygame.draw.circle(surf, col, (int(sx), int(sy)), r)
                pygame.draw.circle(surf, WHITE, (int(sx), int(sy)), max(2, r // 2), 2)
        else:
            rect = pygame.Rect(int(sx - self.w / 2), int(sy - self.h / 2), int(self.w), int(self.h))
            if not rect.colliderect(pygame.Rect(-50, -50, WIDTH + 100, HEIGHT + 100)):
                return
            if warn:
                pygame.draw.rect(surf, col, rect, 2)
                if int(self.t * 10) % 2 == 0:
                    pygame.draw.rect(surf, WHITE, rect, 1)
            else:
                pygame.draw.rect(surf, col, rect)
                pygame.draw.rect(surf, WHITE, rect, 3)


PATTERN_LABELS = {
    "boxring": "CINCIN KOTAK", "cubedrop": "KUBUS JATUH", "frame": "BINGKAI (DI TENGAH!)", "core": "INTI (MENEPI!)", "nest": "GELOMBANG BERSARANG",
    "rotor": "LASER BERPUTAR", "prism": "PRISMA LASER", "sweep": "LASER MENYAPU", "laserwall": "DINDING LASER", "snare": "JERAT SILANG",
    "shards": "SERPIHAN SEGITIGA", "zigzag": "ALIRAN ZIGZAG", "stormfront": "HUJAN PELURU", "tornado": "PUSARAN", "homing": "SERPIHAN PEMBURU",
    "minions": "PANGGIL PASUKAN",
    "gaze": "TATAPAN", "iris": "IRIS BERLUBANG", "tears": "AIR MATA", "hypno": "SPIRAL HIPNOTIS", "blink": "KEDIPAN KEJUT",
    "notes": "NOTE JATUH", "equalizer": "EQUALIZER", "bass": "BASS DROP", "clap": "TEPUKAN", "drumroll": "GENDANG",
    "pixelrain": "HUJAN PIKSEL", "scanline": "GARIS PINDAI", "bitburst": "LEDAKAN BIT", "corrupt": "PETAK RUSAK (CARI AMAN!)", "mirror": "BAYANGAN CERMIN",
    "glitch": "GLITCH"}

BOSS_DEFS = [
    {"name": "KUBUS PENGAWAL", "title": "Pengawal Tingkat I", "shape": "square", "color": (255, 40, 140), "accent": (255, 200, 230),
     "radius": 52, "bpm": 120, "hp": 6500, "dmg": 22, "move": (260, 50, 0.5),
     "phases": [
        [("boxring", {"n": 8}), None, ("cubedrop", {"n": 4}), None, ("frame", {}), None, ("boxring", {"n": 8}), None],
        [("boxring", {"n": 10}), ("cubedrop", {"n": 6}), ("core", {}), ("frame", {}), ("boxring", {"n": 10}), None, ("nest", {}), ("cubedrop", {"n": 7})],
        [("boxring", {"n": 12}), ("frame", {}), ("core", {}), ("nest", {}), ("cubedrop", {"n": 9}), ("boxring", {"n": 12}), ("frame", {}), ("core", {})],
    ]},
    {"name": "PEMINTAL LASER", "title": "Pengawal Tingkat II", "shape": "cross", "color": (0, 225, 255), "accent": (210, 255, 255),
     "radius": 48, "bpm": 130, "hp": 9000, "dmg": 24, "move": (300, 40, 0.6),
     "phases": [
        [("rotor", {"n": 2}), None, None, ("snare", {}), None, ("prism", {"n": 4}), None, ("laserwall", {})],
        [("rotor", {"n": 3, "spin": 1.0}), None, ("sweep", {}), None, ("laserwall", {}), ("snare", {}), ("prism", {"n": 6}), None],
        [("rotor", {"n": 4, "spin": 1.2}), ("sweep", {}), ("snare", {}), ("laserwall", {"cols": 7}), ("prism", {"n": 6}), ("sweep", {}), ("rotor", {"n": 3, "spin": -1.2}), ("snare", {})],
    ]},
    {"name": "SEGITIGA BADAI", "title": "Pengawal Tingkat III", "shape": "triangle", "color": (255, 220, 40), "accent": (255, 250, 190),
     "radius": 50, "bpm": 138, "hp": 12000, "dmg": 26, "move": (320, 80, 0.75),
     "phases": [
        [("shards", {}), None, ("zigzag", {}), None, ("stormfront", {}), None, ("minions", {"n": 3, "kind": "bat"}), None],
        [("shards", {}), ("tornado", {}), ("zigzag", {}), ("stormfront", {}), ("homing", {"n": 3}), ("minions", {"n": 3, "kind": "dasher"}), ("stormfront", {}), None],
        [("tornado", {}), ("shards", {"n": 7}), ("homing", {"n": 5}), ("stormfront", {"n": 24}), ("zigzag", {"n": 14}), ("tornado", {}), ("shards", {"n": 7}), ("homing", {"n": 5})],
    ]},
    {"name": "MATA PENGINTAI", "title": "Pengawal Tingkat IV", "shape": "eye", "color": (170, 90, 255), "accent": (235, 210, 255),
     "radius": 54, "bpm": 144, "hp": 16000, "dmg": 28, "move": (240, 100, 0.5),
     "phases": [
        [("gaze", {"n": 3}), None, ("iris", {}), None, ("tears", {}), None, ("hypno", {}), None],
        [("gaze", {"n": 4}), ("blink", {}), ("iris", {}), ("tears", {}), ("hypno", {}), ("gaze", {"n": 4}), ("blink", {}), ("iris", {})],
        [("gaze", {"n": 5}), ("iris", {"gap": 3}), ("blink", {}), ("hypno", {}), ("tears", {"n": 8}), ("gaze", {"n": 5}), ("hypno", {}), ("blink", {})],
    ]},
    {"name": "PENABUH RITME", "title": "Pengawal Tingkat V", "shape": "star", "color": (255, 90, 200), "accent": (255, 255, 255),
     "radius": 56, "bpm": 150, "hp": 21000, "dmg": 30, "move": (340, 70, 0.8),
     "phases": [
        [("notes", {}), None, ("equalizer", {}), None, ("bass", {}), ("clap", {}), None, ("drumroll", {})],
        [("notes", {}), ("equalizer", {}), ("bass", {}), ("clap", {}), ("drumroll", {}), ("notes", {"lanes": 6}), ("equalizer", {}), ("bass", {})],
        [("notes", {"lanes": 7}), ("equalizer", {"bars": 12}), ("clap", {}), ("drumroll", {"n": 12}), ("bass", {}), ("notes", {"lanes": 7}), ("equalizer", {"bars": 12}), ("clap", {})],
    ]},
    {"name": "PRAJURIT PIKSEL", "title": "Pengawal Tingkat VI", "shape": "pixel", "color": (255, 50, 50), "accent": (255, 255, 255),
     "radius": 60, "bpm": 160, "hp": 28000, "dmg": 34, "move": (380, 90, 0.9),
     "phases": [
        [("pixelrain", {}), ("scanline", {}), ("bitburst", {}), None, ("corrupt", {}), None, ("mirror", {}), ("glitch", {})],
        [("pixelrain", {"n": 14}), ("scanline", {}), ("glitch", {}), ("corrupt", {}), ("bitburst", {}), ("scanline", {"vertical": True}), ("mirror", {}), ("pixelrain", {"n": 14})],
        [("pixelrain", {"n": 18}), ("scanline", {}), ("corrupt", {}), ("glitch", {}), ("bitburst", {"n": 4}), ("scanline", {"vertical": True}), ("mirror", {}), ("corrupt", {})],
    ]},
]


MUSIC_STYLES.update({
    "lvb_0": {"bpm": BOSS_DEFS[0]["bpm"], "lead": "arp1", "drums": "boss", "prog": [(50, (0, 4, 7)), (48, (0, 4, 7)), (53, (0, 4, 7)), (52, (0, 3, 7))]},
    "lvb_1": {"bpm": BOSS_DEFS[1]["bpm"], "lead": "arp2", "drums": "drive", "prog": [(52, (0, 3, 7)), (49, (0, 4, 7)), (47, (0, 3, 7)), (51, (0, 3, 6))]},
    "lvb_2": {"bpm": BOSS_DEFS[2]["bpm"], "lead": "arp1", "drums": "boss", "prog": [(46, (0, 3, 6)), (44, (0, 3, 7)), (49, (0, 4, 7)), (47, (0, 3, 7))]},
    "lvb_3": {"bpm": BOSS_DEFS[3]["bpm"], "lead": "arp2", "drums": "soft", "prog": [(45, (0, 3, 7)), (43, (0, 3, 7)), (41, (0, 3, 6)), (44, (0, 4, 7))]},
    "lvb_4": {"bpm": BOSS_DEFS[4]["bpm"], "lead": "arp1", "drums": "drive", "prog": [(55, (0, 4, 7)), (53, (0, 4, 7)), (50, (0, 3, 7)), (52, (0, 4, 7))]},
    "lvb_5": {"bpm": BOSS_DEFS[5]["bpm"], "lead": "arp2", "drums": "boss", "prog": [(47, (0, 3, 7)), (45, (0, 3, 6)), (42, (0, 3, 7)), (40, (0, 3, 6))]},
})
PRERENDER_TRACKS += ["menu", "shop", "battle", "boss"] + ["lvb_%d" % _i for _i in range(len(BOSS_DEFS))]
MUSIC_STYLES.update({
    "tut":      {"bpm": 112, "lead": "arp2", "drums": "soft", "prog": [(60, (0, 4, 7)), (57, (0, 3, 7)), (55, (0, 4, 7)), (59, (0, 4, 7))]},
    "tut_boss": {"bpm": 138, "lead": "arp1", "drums": "drive", "prog": [(52, (0, 3, 7)), (55, (0, 4, 7)), (50, (0, 3, 7)), (53, (0, 4, 7))]},
})
BG_TRACK_ORDER = ["shop", "tut", "tut_boss", "event", "boss_old", "boss_heal", "boss_necro", "boss_brute", "boss_guard", "boss_gun",
                  "boss_exec", "boss_fire", "boss_skel", "boss_final", "boss"] + ["lvb_%d" % _i for _i in range(len(BOSS_DEFS))]


# ---- Raja Inflasi: semua kemampuan musuh, boss, dan boss geometri ----
GEO_LIST = []
_seen_geo = set()
for _bi, _bd in enumerate(BOSS_DEFS):
    for _ph in _bd["phases"]:
        for _st in _ph:
            if _st:
                _key = (_st[0], repr(sorted(_st[1].items())))
                if _key not in _seen_geo:
                    _seen_geo.add(_key)
                    GEO_LIST.append((_bi, _st[0], _st[1]))
_PUP_SKIP_FLAGS = ("teleporter", "buffer", "mother", "ethereal", "protector")
_PUP_FLAGS = ("laser", "ninja", "bomber", "sniper", "toxic", "slam", "thunder", "warden", "mimic", "hammer", "slash",
              "crystal_mage", "shotgun", "chief", "minigunner", "reaper")
ENEMY_PUP_KINDS = {}
for _k in ALL_SPAWN_TYPES:
    if _k["name"] in ENEMY_PUP_KINDS or any(_k.get(f) for f in _PUP_SKIP_FLAGS):
        continue
    if _k.get("abil") or any(_k.get(f) for f in _PUP_FLAGS):
        ENEMY_PUP_KINDS[_k["name"]] = _k
BOSS_PUP_KINDS = ["normal", "necro", "brute", "guardian", "minigun", "exec", "fire", "skel"]
FINAL_GEO_KEYS = ["g:%d" % _i for _i in range(len(GEO_LIST))]
FINAL_ENEMY_KEYS = ["e:" + _n for _n in ENEMY_PUP_KINDS]
FINAL_BOSS_KEYS = ["b:" + _k for _k in BOSS_PUP_KINDS]
FINAL_EXTRA_SET = set(FINAL_GEO_KEYS + FINAL_ENEMY_KEYS + FINAL_BOSS_KEYS)
for _i, (_bi, _nm, _kw) in enumerate(GEO_LIST):
    FINAL_LABELS["g:%d" % _i] = PATTERN_LABELS.get(_nm, _nm.upper())
for _n in ENEMY_PUP_KINDS:
    FINAL_LABELS["e:" + _n] = "JURUS " + _n.upper()
for _k in BOSS_PUP_KINDS:
    FINAL_LABELS["b:" + _k] = "JURUS " + BOSS_TYPES_BY_KIND[_k]["name"].upper()


def final_pick():
    r = random.random()
    if r < 0.34:
        return random.choice(FINAL_ATTACKS)
    if r < 0.60:
        return random.choice(FINAL_GEO_KEYS)
    if r < 0.88:
        return random.choice(FINAL_ENEMY_KEYS)
    return random.choice(FINAL_BOSS_KEYS)


class LevelBoss(Enemy):
    """Boss level bentuk geometri: melayang di arena, menyerang mengikuti ketukan musik."""

    def __init__(self, kdef, cycle, x, y, mode_config):
        mc = mode_config or MODE_CONFIGS["normal"]
        kind = {"name": kdef["name"], "color": kdef["color"], "radius": kdef["radius"], "speed": 0.0,
                "hp": 1, "xp": 450, "dmg": kdef["dmg"], "gold": 300, "pickup_chance": 1.0}
        super().__init__(kind, 0, x, y, is_boss=True, boss_scale=0, spawn_at=(x, y), mode_config=mc)
        lv = DIFFICULTY["lv"]
        self.kdef = kdef
        self.cycle = cycle
        self.boss_kind = "jsab"
        self.max_hp = int(kdef["hp"] * (1 + 0.45 * cycle) * (1 + 0.02 * max(0, lv - 10)) * mc["hp_mult"])
        self.hp = self.max_hp
        self.shield_max = int(self.max_hp * 0.2)
        self.shield = self.shield_max
        self.kind["shield_style"] = {"square": "plates", "cross": "runic", "triangle": "flame"}.get(kdef["shape"], "bubble")
        self.bpm = min(kdef["bpm"] + 4 * cycle, 188)
        self.beat_len = 60.0 / self.bpm
        self.beat_timer = self.beat_len * 2
        dscale = boss_dmg_scale(mc)
        self.bdmg = kdef["dmg"] * 0.55 * dscale
        self.hdmg = kdef["dmg"] * dscale
        self.t = 0.0
        self.beat = 0
        self.intro = 4
        self.phase = 0
        self.pulse = 0.0
        self.spin = random.uniform(0, math.tau)
        self.spin2 = random.uniform(0, math.tau)
        self.look = 0.0
        self.tell = None
        self.hypno_dir = 1
        self.pace = 1.0
        self.atk_n = 0

    def skip_nth(self, n):
        """Level pemain kecil: sebagian SERANGAN dilewati (musik tetap jalan). pace<0.65 -> setengahnya, pace<0.9 -> sepertiganya."""
        p = self.pace
        if p >= 0.9:
            return False
        if p >= 0.65:
            return n % 3 == 0
        return n % 2 == 0

    def tick(self, dt, game):
        self.t += dt
        self.pace = game.boss_pace()
        self.pulse = max(0.0, self.pulse - dt * 3.5)
        self.frozen_timer = 0.0
        self.kb_timer = 0.0
        a = game.arena
        if a:
            ax, ay, sp = self.kdef["move"]
            self.x = a["cx"] + ax * math.sin(self.t * sp)
            self.y = a["cy"] - 170 + ay * math.sin(self.t * sp * 1.3)
        self.look = math.atan2(game.badang.y - self.y, game.badang.x - self.x)
        self.beat_timer -= dt
        while self.beat_timer <= 0:
            self.beat_timer += self.beat_len
            self.on_beat(game)
        ratio = self.hp / self.max_hp
        new_phase = 0 if ratio > 0.66 else 1 if ratio > 0.33 else 2
        if new_phase != self.phase:
            self.phase = new_phase
            self.beat = 0
            game.show_toast("FASE %d!" % (new_phase + 1))
            sfx("boss_spawn")
            game.hazards.append(Hazard("ring", self.x, self.y, 0.2, 1.3, self.hdmg * 0.7, self.kdef["color"],
                                       max_radius=800, thickness=26))

    def on_beat(self, game):
        self.pulse = 1.0
        self.beat += 1
        if self.intro > 0:
            self.intro -= 1
            if self.intro == 0:
                game.show_toast("MULAI!")
            return
        steps = self.kdef["phases"][self.phase]
        step = steps[self.beat % len(steps)]
        if step:
            self.atk_n += 1
            if not self.skip_nth(self.atk_n):
                name, kw = step
                getattr(self, "p_" + name)(game, **kw)
        self.tell = None
        m = 0
        for k in (1, 2):
            nx = steps[(self.beat + k) % len(steps)]
            if nx:
                m += 1
                if not self.skip_nth(self.atk_n + m):
                    self.tell = PATTERN_LABELS.get(nx[0], nx[0].upper())
                    break

    def bullet(self, g, ang, speed, x=None, y=None, radius=7):
        if len(g.enemy_projectiles) >= 420:
            return
        x = self.x if x is None else x
        y = self.y if y is None else y
        g.enemy_projectiles.append(EnemyProjectile(x, y, x + math.cos(ang) * 100, y + math.sin(ang) * 100,
                                                   speed * (0.7 + 0.3 * self.pace), self.bdmg, self.kdef["color"], radius, 10.0))

    def haz(self, g, kind, x, y, warn_beats, active, **kw):
        if len(g.hazards) >= 90:
            return
        g.hazards.append(Hazard(kind, x, y, warn_beats * self.beat_len, active, self.hdmg,
                                self.kdef["color"], **kw))

    def aim(self, g):
        return math.atan2(g.badang.y - self.y, g.badang.x - self.x)

    def p_ring(self, g, n=12, speed=3.2, turn=0.0):
        self.spin += turn
        for i in range(n):
            self.bullet(g, self.spin + i * math.tau / n, speed)
        sfx("shoot", 0.1)

    def p_fan(self, g, n=5, spread=13, speed=4.2):
        for ang in fan_angles(self.aim(g), n, spread):
            self.bullet(g, ang, speed, radius=8)
        sfx("shoot", 0.1)

    def p_spiral(self, g, arms=3, speed=3.4, turn=0.42):
        self.spin += turn
        for i in range(arms):
            self.bullet(g, self.spin + i * math.tau / arms, speed)
        sfx("shoot", 0.1)

    def p_beams(self, g, n=4, turn=0.3, width=34, warn=2.0):
        self.spin2 += turn
        for i in range(n):
            self.haz(g, "beam", self.x, self.y, warn, 0.5, angle=self.spin2 + i * math.tau / n,
                     length=1700, width=width)
        sfx("charge", 0.3)

    def p_aimbeam(self, g, n=1, spread=0.22, width=30, warn=2.0):
        base = self.aim(g)
        for i in range(n):
            self.haz(g, "beam", self.x, self.y, warn, 0.45, angle=base + (i - (n - 1) / 2.0) * spread,
                     length=1700, width=width)
        sfx("charge", 0.3)

    def p_wave(self, g, radius=780):
        self.haz(g, "ring", self.x, self.y, 0.3, 1.5, max_radius=radius, thickness=26)
        sfx("boom", 0.2)

    def p_rain(self, g, n=5, radius=80, spread=320, warn=2.0):
        a = g.arena
        for _ in range(n):
            px = g.badang.x + random.uniform(-spread, spread)
            py = g.badang.y + random.uniform(-spread * 0.6, spread * 0.6)
            if a:
                px = max(a["cx"] - a["hw"], min(a["cx"] + a["hw"], px))
                py = max(a["cy"] - a["hh"], min(a["cy"] + a["hh"], py))
            self.haz(g, "blast", px, py, warn, 0.3, radius=radius)
        sfx("warn", 0.2)

    def p_snipe(self, g, n=1, radius=95, warn=1.5):
        for i in range(n):
            ox = 0 if i == 0 else random.uniform(-160, 160)
            oy = 0 if i == 0 else random.uniform(-160, 160)
            self.haz(g, "blast", g.badang.x + ox, g.badang.y + oy, warn + i * 0.3, 0.3, radius=radius)
        sfx("warn", 0.2)

    def p_hbars(self, g, rows=5, warn=3.0):
        a = g.arena
        if not a:
            return
        h = 2 * a["hh"] / rows
        safe = random.randrange(rows)
        for r in range(rows):
            if r != safe:
                self.haz(g, "rect", a["cx"], a["cy"] - a["hh"] + h * (r + 0.5), warn, 0.45, w=2 * a["hw"], h=h - 8)
        sfx("warn", 0.2)

    def p_vbars(self, g, cols=8, safe=2, warn=3.0):
        a = g.arena
        if not a:
            return
        w = 2 * a["hw"] / cols
        s = random.randrange(cols - safe + 1)
        for c in range(cols):
            if not (s <= c < s + safe):
                self.haz(g, "rect", a["cx"] - a["hw"] + w * (c + 0.5), a["cy"], warn, 0.45, w=w - 8, h=2 * a["hh"])
        sfx("warn", 0.2)

    def p_pillars(self, g, n=5, width=90, warn=2.0):
        a = g.arena
        if not a:
            return
        xs = [g.badang.x] + [random.uniform(a["cx"] - a["hw"], a["cx"] + a["hw"]) for _ in range(n - 1)]
        for px in xs:
            self.haz(g, "rect", px, a["cy"], warn, 0.4, w=width, h=2 * a["hh"])
        sfx("warn", 0.2)

    def p_cross(self, g, width=110, warn=2.0):
        a = g.arena
        if not a:
            return
        self.haz(g, "rect", a["cx"], g.badang.y, warn, 0.4, w=2 * a["hw"], h=width)
        self.haz(g, "rect", g.badang.x, a["cy"], warn, 0.4, w=width, h=2 * a["hh"])
        sfx("warn", 0.2)

    def p_checker(self, g, cols=6, rows=4, warn=3.0):
        a = g.arena
        if not a:
            return
        cw, ch = 2 * a["hw"] / cols, 2 * a["hh"] / rows
        parity = self.beat % 2
        for i in range(cols):
            for j in range(rows):
                if (i + j) % 2 == parity:
                    self.haz(g, "rect", a["cx"] - a["hw"] + cw * (i + 0.5), a["cy"] - a["hh"] + ch * (j + 0.5),
                             warn, 0.4, w=cw - 6, h=ch - 6)
        sfx("warn", 0.2)

    def p_rotor(self, g, n=2, spin=0.9, dur=3.2, width=36, warn=2.0):
        base = random.uniform(0, math.tau)
        for i in range(n):
            self.haz(g, "beam", self.x, self.y, warn, dur, angle=base + i * math.tau / n,
                     length=1800, width=width, spin=spin)
        sfx("charge", 0.3)

    def p_minions(self, g, n=3, kind="bat"):
        g.spawn_minions(self.x, self.y, n, kind)
        sfx("summon", 0.3)

    def arena_or_none(self, g):
        return g.arena

    def p_boxring(self, g, n=8, speed=3.0):
        half = 60
        for side in range(4):
            nx, ny = ((0, -1), (1, 0), (0, 1), (-1, 0))[side]
            tx, ty = -ny, nx
            for k in range(n):
                f = (k + 0.5) / n * 2 - 1
                px, py = self.x + nx * half + tx * f * half, self.y + ny * half + ty * f * half
                self.bullet(g, math.atan2(ny + ty * f * 0.35, nx + tx * f * 0.35), speed, px, py, 7)
        sfx("shoot", 0.1)

    def p_cubedrop(self, g, n=4, size=118, warn=2.0):
        a = g.arena
        if not a:
            return
        self.haz(g, "rect", g.badang.x, g.badang.y, warn, 0.4, w=size, h=size)
        for _ in range(n - 1):
            px = max(a["cx"] - a["hw"], min(a["cx"] + a["hw"], g.badang.x + random.uniform(-330, 330)))
            py = max(a["cy"] - a["hh"], min(a["cy"] + a["hh"], g.badang.y + random.uniform(-220, 220)))
            self.haz(g, "rect", px, py, warn + random.uniform(0, 0.6), 0.4, w=size, h=size)
        sfx("warn", 0.2)

    def p_frame(self, g, warn=2.5):
        """Bingkai bahaya di tepi: aman di KOTAK TENGAH."""
        a = g.arena
        if not a:
            return
        t = 0.30
        W, H = 2 * a["hw"], 2 * a["hh"]
        self.haz(g, "rect", a["cx"], a["cy"] - a["hh"] + H * t / 2, warn, 0.5, w=W, h=H * t)
        self.haz(g, "rect", a["cx"], a["cy"] + a["hh"] - H * t / 2, warn, 0.5, w=W, h=H * t)
        self.haz(g, "rect", a["cx"] - a["hw"] + W * t / 2, a["cy"], warn, 0.5, w=W * t, h=H)
        self.haz(g, "rect", a["cx"] + a["hw"] - W * t / 2, a["cy"], warn, 0.5, w=W * t, h=H)
        sfx("warn", 0.2)

    def p_core(self, g, warn=2.5):
        """Kotak bahaya di TENGAH: aman di tepi arena."""
        a = g.arena
        if not a:
            return
        self.haz(g, "rect", a["cx"], a["cy"], warn, 0.5, w=a["hw"] * 1.0, h=a["hh"] * 1.0)
        sfx("warn", 0.2)

    def p_nest(self, g):
        for k in range(3):
            g.after(k * self.beat_len * 0.5, lambda k=k: (not self.dead) and g.hazards.append(
                Hazard("ring", self.x, self.y, 0.25, 1.4, self.hdmg * 0.7, self.kdef["color"], max_radius=520 + k * 140, thickness=24)))
        sfx("boom", 0.2)

    def p_prism(self, g, n=4, warn=2.0):
        self.spin2 += 0.5236
        for i in range(n):
            self.haz(g, "beam", self.x, self.y, warn, 1.2, angle=self.spin2 + i * math.tau / n, length=1700, width=30, spin=0.45)
        sfx("charge", 0.3)

    def p_sweep(self, g, warn=1.8):
        base = self.aim(g) - 1.2
        self.haz(g, "beam", self.x, self.y, warn, 2.6, angle=base, length=1800, width=44, spin=0.95)
        sfx("charge", 0.3)

    def p_laserwall(self, g, cols=5):
        a = g.arena
        if not a:
            return
        w = 2 * a["hw"] / cols
        order = list(range(cols))
        if random.random() < 0.5:
            order.reverse()
        for k, c in enumerate(order):
            if abs(a["cx"] - a["hw"] + w * (c + 0.5) - g.badang.x) < w * 0.5 and k == 0:
                pass
            self.haz(g, "rect", a["cx"] - a["hw"] + w * (c + 0.5), a["cy"], 1.8 + k * 0.55, 0.35, w=w * 0.45, h=2 * a["hh"])
        sfx("warn", 0.2)

    def p_snare(self, g, warn=2.0):
        px, py = g.badang.x, g.badang.y
        self.haz(g, "beam", px - 520, py - 520, warn, 0.5, angle=math.pi / 4, length=1500, width=36)
        self.haz(g, "beam", px + 520, py - 520, warn, 0.5, angle=3 * math.pi / 4, length=1500, width=36)
        sfx("charge", 0.3)

    def p_shards(self, g, n=5, speed=4.0):
        self.spin += 0.37
        for k in range(3):
            base = self.spin + k * math.tau / 3
            for a in fan_angles(base, n, 9):
                self.bullet(g, a, speed, radius=7)
        sfx("shoot", 0.1)

    def p_zigzag(self, g, n=10):
        for i in range(n):
            g.after(i * 0.08, lambda i=i: (not self.dead) and self.bullet(g, self.aim(g) + math.sin(i * 0.9) * 0.55, 4.4, radius=7))
        sfx("shoot", 0.1)

    def p_stormfront(self, g, n=16):
        a = g.arena
        if not a:
            return
        for _ in range(n):
            x = random.uniform(a["cx"] - a["hw"], a["cx"] + a["hw"])
            self.bullet(g, math.pi / 2, random.uniform(3.4, 5.2), x, a["cy"] - a["hh"], 8)
        sfx("shoot", 0.1)

    def p_tornado(self, g):
        for k in range(4):
            g.after(k * 0.22, lambda k=k: (not self.dead) and [self.bullet(g, self.spin + k * 0.19 * (1 if k % 2 == 0 else -1) + i * math.tau / 14, 3.3) for i in range(14)])
        self.spin += 0.5
        sfx("shoot", 0.1)

    def p_homing(self, g, n=3):
        for i in range(n):
            a = self.aim(g) + (i - (n - 1) / 2.0) * 0.5
            if len(g.enemy_projectiles) < 420:
                ep = EnemyProjectile(self.x, self.y, self.x + math.cos(a) * 100, self.y + math.sin(a) * 100, 3.4, self.bdmg,
                                     self.kdef["color"], 9, 6.0, style="shuriken")
                ep.home = 0.032
                g.enemy_projectiles.append(ep)
        sfx("shoot", 0.1)

    def p_gaze(self, g, n=3):
        for i in range(n):
            g.after(i * self.beat_len * 0.5, lambda: (not self.dead) and self.haz(g, "beam", self.x, self.y, 1.1, 0.3, angle=self.aim(g), length=1700, width=26))
        sfx("charge", 0.3)

    def p_iris(self, g, n=26, gap=4, speed=3.0):
        start = random.randrange(n)
        for i in range(n):
            if (i - start) % n < gap:
                continue
            self.bullet(g, i * math.tau / n, speed)
        sfx("shoot", 0.1)

    def p_tears(self, g, n=6):
        px, py = g.badang.x, g.badang.y
        for i in range(n):
            f = (i + 1) / float(n)
            self.haz(g, "blast", self.x + (px - self.x) * f + random.uniform(-40, 40), self.y + (py - self.y) * f + random.uniform(-40, 40),
                     1.6 + i * 0.28, 0.3, radius=78)
        sfx("warn", 0.2)

    def p_hypno(self, g, arms=3, speed=3.3):
        self.hypno_dir = -getattr(self, "hypno_dir", 1)
        for k in range(10):
            g.after(k * 0.1, lambda k=k: (not self.dead) and [self.bullet(g, self.spin + self.hypno_dir * (k * 0.34) + i * math.tau / arms, speed) for i in range(arms)])
        self.spin += 1.1
        sfx("shoot", 0.1)

    def p_blink(self, g):
        g.hazards.append(Hazard("ring", self.x, self.y, 0.2, 1.0, self.hdmg * 0.6, self.kdef["color"], max_radius=420, thickness=22))
        self.t += random.uniform(1.6, 3.2)
        g.after(0.3, lambda: (not self.dead) and g.hazards.append(Hazard("ring", self.x, self.y, 0.25, 1.0, self.hdmg * 0.6, self.kdef["color"], max_radius=520, thickness=22)))
        sfx("warn", 0.2)

    def p_notes(self, g, lanes=5):
        a = g.arena
        if not a:
            return
        w = 2 * a["hw"] / lanes
        order = random.sample(range(lanes), lanes - 1)
        for k, c in enumerate(order):
            self.haz(g, "rect", a["cx"] - a["hw"] + w * (c + 0.5), a["cy"], 1.5 + k * 0.5, 0.3, w=w - 10, h=2 * a["hh"])
        sfx("warn", 0.2)

    def p_equalizer(self, g, bars=10):
        a = g.arena
        if not a:
            return
        w = 2 * a["hw"] / bars
        for c in range(bars):
            h = random.uniform(0.25, 0.9) * a["hh"] * 2
            self.haz(g, "rect", a["cx"] - a["hw"] + w * (c + 0.5), a["cy"] + a["hh"] - h / 2, 2.0 + (c % 3) * 0.25, 0.4, w=w - 8, h=h)
        sfx("warn", 0.2)

    def p_bass(self, g):
        for k in range(3):
            g.after(k * self.beat_len, lambda k=k: (not self.dead) and (g.hazards.append(
                Hazard("ring", self.x, self.y, 0.25, 1.2, self.hdmg * 0.8, self.kdef["color"], max_radius=700 + k * 120, thickness=32)), sfx("boom", 0.1)))

    def p_clap(self, g, warn=2.2):
        a = g.arena
        if not a:
            return
        W, H = 2 * a["hw"], 2 * a["hh"]
        self.haz(g, "rect", a["cx"] - a["hw"] + W * 0.2, a["cy"], warn, 0.5, w=W * 0.4, h=H)
        self.haz(g, "rect", a["cx"] + a["hw"] - W * 0.2, a["cy"], warn, 0.5, w=W * 0.4, h=H)
        sfx("warn", 0.2)

    def p_drumroll(self, g, n=8):
        for k in range(n):
            g.after(k * 0.12, lambda k=k: (not self.dead) and [self.bullet(g, k * 0.17 + i * math.tau / 6, 3.8, radius=6) for i in range(6)])
        sfx("shoot", 0.1)

    def p_pixelrain(self, g, n=10):
        a = g.arena
        if not a:
            return
        for k in range(n):
            px = random.uniform(a["cx"] - a["hw"], a["cx"] + a["hw"])
            py = random.uniform(a["cy"] - a["hh"], a["cy"] + a["hh"])
            if k == 0:
                px, py = g.badang.x, g.badang.y
            self.haz(g, "rect", px, py, 1.6 + k * 0.12, 0.3, w=72, h=72)
        sfx("warn", 0.2)

    def p_scanline(self, g, vertical=False, steps=9):
        a = g.arena
        if not a:
            return
        for k in range(steps):
            f = (k + 0.5) / steps
            if vertical:
                self.haz(g, "rect", a["cx"] - a["hw"] + 2 * a["hw"] * f, a["cy"], 1.5 + k * 0.28, 0.35, w=2 * a["hw"] / steps * 1.1, h=2 * a["hh"])
            else:
                self.haz(g, "rect", a["cx"], a["cy"] - a["hh"] + 2 * a["hh"] * f, 1.5 + k * 0.28, 0.35, w=2 * a["hw"], h=2 * a["hh"] / steps * 1.15)
        sfx("charge", 0.3)

    def p_bitburst(self, g, n=3):
        for k in range(n):
            g.after(k * 0.25, lambda k=k: (not self.dead) and [self.bullet(g, i * math.pi / 4 + (0.0 if k % 2 == 0 else math.pi / 8), 3.6 + k * 0.3, radius=7) for i in range(8)])
        sfx("shoot", 0.1)

    def p_corrupt(self, g, cols=8, rows=5, warn=3.0):
        a = g.arena
        if not a:
            return
        cw, ch = 2 * a["hw"] / cols, 2 * a["hh"] / rows
        pc = int(max(0, min(cols - 1, (g.badang.x - (a["cx"] - a["hw"])) / cw)))
        pr = int(max(0, min(rows - 1, (g.badang.y - (a["cy"] - a["hh"])) / ch)))
        safe = {(pc, pr)}
        while len(safe) < 3:
            safe.add((random.randrange(cols), random.randrange(rows)))
        for i in range(cols):
            for j in range(rows):
                if (i, j) not in safe:
                    self.haz(g, "rect", a["cx"] - a["hw"] + cw * (i + 0.5), a["cy"] - a["hh"] + ch * (j + 0.5), warn, 0.4, w=cw - 4, h=ch - 4)
        sfx("warn", 0.2)

    def p_mirror(self, g, n=5):
        base = self.aim(g)
        for a in fan_angles(base, n, 12):
            self.bullet(g, a, 4.2, radius=8)
            self.bullet(g, math.pi - a, 4.2, radius=8)
        sfx("shoot", 0.1)

    def p_glitch(self, g):
        for _ in range(3):
            ox, oy = random.uniform(-260, 260), random.uniform(-120, 120)
            for i in range(8):
                self.bullet(g, i * math.pi / 4, 3.8, self.x + ox, self.y + oy, 7)
        self.t += random.uniform(1.0, 2.4)
        sfx("warn", 0.2)

    def draw(self, surf, cam_x, cam_y):
        sx, sy = self.x - cam_x, self.y - cam_y
        if not (-250 <= sx <= WIDTH + 250 and -250 <= sy <= HEIGHT + 250):
            return
        p = self.pulse
        r = self.radius * (1 + 0.16 * p)
        col = self.kdef["color"]
        acc = (255, 255, 255)
        shape = self.kdef["shape"]
        ang = self.t * 0.6
        if shape == "square":
            pts = rot_pts([(-r, -r), (r, -r), (r, r), (-r, r)], sx, sy, ang)
            pygame.draw.polygon(surf, col, pts)
            pygame.draw.polygon(surf, acc, pts, 5)
            pygame.draw.polygon(surf, BLACK, rot_pts([(-r * .5, -r * .5), (r * .5, -r * .5), (r * .5, r * .5),
                                                      (-r * .5, r * .5)], sx, sy, -ang))
        elif shape == "cross":
            a1 = rot_pts([(-r * 1.3, -r * .35), (r * 1.3, -r * .35), (r * 1.3, r * .35), (-r * 1.3, r * .35)], sx, sy, ang)
            a2 = rot_pts([(-r * .35, -r * 1.3), (r * .35, -r * 1.3), (r * .35, r * 1.3), (-r * .35, r * 1.3)], sx, sy, ang)
            pygame.draw.polygon(surf, col, a1)
            pygame.draw.polygon(surf, col, a2)
            pygame.draw.polygon(surf, acc, a1, 4)
            pygame.draw.polygon(surf, acc, a2, 4)
        elif shape == "triangle":
            pts = rot_pts([(0, -r * 1.25), (r * 1.1, r * .85), (-r * 1.1, r * .85)], sx, sy, ang)
            pygame.draw.polygon(surf, col, pts)
            pygame.draw.polygon(surf, acc, pts, 5)
        elif shape == "eye":
            pygame.draw.circle(surf, col, (int(sx), int(sy)), int(r))
            pygame.draw.ellipse(surf, WHITE, pygame.Rect(int(sx - r * .85), int(sy - r * .5), int(r * 1.7), int(r)))
            px, py = sx + math.cos(self.look) * r * .3, sy + math.sin(self.look) * r * .25
            pygame.draw.circle(surf, BLACK, (int(px), int(py)), int(r * .3 * (1 + .3 * p)))
            pygame.draw.circle(surf, acc, (int(sx), int(sy)), int(r), 4)
        elif shape == "star":
            pts = []
            for i in range(16):
                rr = r * (1.3 if i % 2 == 0 else .65)
                a = ang + i * math.pi / 8
                pts.append((sx + math.cos(a) * rr, sy + math.sin(a) * rr))
            pygame.draw.polygon(surf, col, pts)
            pygame.draw.polygon(surf, acc, pts, 4)
        else:
            cell = r * 0.62
            for gx in (-1, 0, 1):
                for gy in (-1, 0, 1):
                    off = math.sin(self.t * 4 + gx * 2 + gy) * 5 * (1 + p)
                    cx_, cy_ = sx + gx * cell * 1.15, sy + gy * cell * 1.15 + off
                    rect = pygame.Rect(int(cx_ - cell / 2), int(cy_ - cell / 2), int(cell), int(cell))
                    pygame.draw.rect(surf, col if (gx + gy) % 2 == 0 else acc, rect)
                    pygame.draw.rect(surf, BLACK, rect, 2)
        fr = r * 0.62 if shape in ("star", "pixel") else r * 0.78
        if shape != "eye":
            draw_face(surf, sx, sy, fr, self.look, "angry", 0.6 + 0.2 * self.phase, self.t)
        if self.tell and self.intro <= 0:
            flash = int(self.t * 8) % 2 == 0
            tc = (255, 70, 60) if flash else (255, 220, 90)
            rr = int(r + 14 + 5 * math.sin(self.t * 12))
            pygame.draw.circle(surf, tc, (int(sx), int(sy)), rr, 5)
            txt = font_med.render("AWAS: " + self.tell, True, tc)
            bw = txt.get_width() + 22
            ty0 = max(8, int(sy - r - 70))
            pygame.draw.rect(surf, (12, 8, 18), (sx - bw / 2, ty0, bw, 36), border_radius=8)
            pygame.draw.rect(surf, tc, (sx - bw / 2, ty0, bw, 36), 3, border_radius=8)
            surf.blit(txt, (sx - txt.get_width() / 2, ty0 + 6))
        for i in range(3):
            c = acc if i <= self.phase else GRAY
            pygame.draw.circle(surf, c, (int(sx - 14 + i * 14), int(sy + r + 22)), 4)


_GEM_SPR = {}


class XPGem:
    """Orb XP: belah ketupat kuning yang berdenyut (musuh selalu bulat)."""
    eaten = False

    def __init__(self, x, y, amount):
        self.x, self.y = x, y
        self.amount = max(1, amount)
        self.radius = 6
        self.phase = random.uniform(0, 6.28)
        self.pulled = False
        self.pspeed = 9.0

    def draw(self, surf, cam_x, cam_y):
        sx, sy = self.x - cam_x, self.y - cam_y
        if -20 <= sx <= WIDTH + 20 and -20 <= sy <= HEIGHT + 20:
            t = pygame.time.get_ticks() / 1000.0
            big = self.amount >= 10
            spr = _GEM_SPR.get(big)
            if spr is None:
                s_ = 11 if big else 8
                w_ = int(s_ * 0.7)
                spr = pygame.Surface((2 * w_ + 6, 2 * s_ + 6), pygame.SRCALPHA)
                pts = [(w_ + 3, 3), (2 * w_ + 3, s_ + 3), (w_ + 3, 2 * s_ + 3), (3, s_ + 3)]
                pygame.draw.polygon(spr, XP_GEM_COLOR, pts)
                pygame.draw.polygon(spr, XP_GEM_EDGE, pts, width=2)
                _GEM_SPR[big] = spr
            surf.blit(spr, (int(sx) - spr.get_width() // 2, int(sy + math.sin(t * 4 + self.phase) * 2) - spr.get_height() // 2))


PICKUP_COLORS = {
    "magnet": MAGNET_COLOR, "health": HEALTH_PICKUP_COLOR, "freeze": FREEZE_COLOR,
    "nuke": NUKE_COLOR, "chest": CHEST_COLOR, "hporb": HEAL_COLOR,
}


class Pickup:
    def __init__(self, kind, x, y):
        self.kind = kind
        self.x, self.y = x, y
        if kind == "chest":
            self.radius = 14
        elif kind == "hporb":
            self.radius = 12
        else:
            self.radius = 10
        self.phase = random.uniform(0, 6.28)
        self.age = 0.0

    def draw(self, surf, cam_x, cam_y):
        sx, sy = self.x - cam_x, self.y - cam_y
        if not (-30 <= sx <= WIDTH + 30 and -30 <= sy <= HEIGHT + 30):
            return
        t = pygame.time.get_ticks() / 1000.0
        cx = int(sx)
        cy = int(sy + math.sin(t * 3 + self.phase) * 3)

        if self.kind == "hporb":
            pulse = 4 + int(2 * (1 + math.sin(t * 5 + self.phase)))
            g = self.radius + pulse
            pygame.draw.rect(surf, HEAL_GLOW, (cx - g, cy - g, g * 2, g * 2), width=2, border_radius=8)
            arm, th = self.radius, 5
            pygame.draw.rect(surf, HEAL_EDGE, (cx - arm - 2, cy - th - 2, arm * 2 + 4, th * 2 + 4), border_radius=3)
            pygame.draw.rect(surf, HEAL_EDGE, (cx - th - 2, cy - arm - 2, th * 2 + 4, arm * 2 + 4), border_radius=3)
            pygame.draw.rect(surf, HEAL_COLOR, (cx - arm, cy - th, arm * 2, th * 2))
            pygame.draw.rect(surf, HEAL_COLOR, (cx - th, cy - arm, th * 2, arm * 2))
            return

        self.draw_rune(surf, cx, cy, t)


    def draw_rune(self, surf, cx, cy, t):
        """Tiap rune punya bentuk & efek sendiri: batu bersinar dengan lambang di tengah."""
        P = pygame.draw
        k = self.kind
        color = PICKUP_COLORS[k]
        ph = self.phase
        R = self.radius + 4
        pulse = 1 + int(2 * math.sin(t * 4 + ph))

        def poly(n, r, rot=0.0):
            return [(cx + math.cos(rot + i * math.tau / n) * r, cy + math.sin(rot + i * math.tau / n) * r) for i in range(n)]

        # lingkar cahaya
        P.circle(surf, tuple(c // 3 for c in color), (cx, cy), R + 6 + pulse, 2)
        if k == "magnet":
            body = poly(6, R + 2, t * 0.5)
            P.polygon(surf, (40, 30, 70), body)
            P.polygon(surf, color, body, 3)
            # tapal kuda
            P.arc(surf, (230, 60, 70), (cx - 8, cy - 8, 16, 16), 0, math.pi, 4)
            P.line(surf, (230, 60, 70), (cx - 8, cy), (cx - 8, cy + 6), 4)
            P.line(surf, (230, 60, 70), (cx + 8, cy), (cx + 8, cy + 6), 4)
            P.line(surf, (240, 240, 250), (cx - 8, cy + 6), (cx - 8, cy + 8), 4)
            P.line(surf, (240, 240, 250), (cx + 8, cy + 6), (cx + 8, cy + 8), 4)
            for i in range(3):
                a = t * 3 + i * 2.09
                P.circle(surf, (170, 255, 190), (int(cx + math.cos(a) * (R + 7)), int(cy + math.sin(a) * (R + 7))), 2)
        elif k == "freeze":
            body = poly(4, R + 4, math.pi / 4)
            P.polygon(surf, (30, 70, 110), body)
            P.polygon(surf, (190, 240, 255), body, 3)
            for i in range(3):
                a = i * math.pi / 3 + t * 0.6
                P.line(surf, (235, 250, 255), (cx + math.cos(a) * 9, cy + math.sin(a) * 9), (cx - math.cos(a) * 9, cy - math.sin(a) * 9), 2)
            for sg in range(6):
                a = sg * math.pi / 3 + t * 0.6
                P.circle(surf, WHITE, (int(cx + math.cos(a) * 9), int(cy + math.sin(a) * 9)), 2)
        elif k == "nuke":
            pts = []
            for i in range(16):
                r_ = R + 5 if i % 2 == 0 else R - 3
                a = i * math.tau / 16 + t * 1.2
                pts.append((cx + math.cos(a) * r_, cy + math.sin(a) * r_))
            P.polygon(surf, (90, 25, 10), pts)
            P.polygon(surf, (255, 150, 50), pts, 3)
            P.circle(surf, (255, 90, 30), (cx, cy), 7 + pulse // 2)
            P.circle(surf, (255, 235, 150), (cx, cy), 3)
        elif k == "health":
            P.circle(surf, (20, 70, 40), (cx, cy), R)
            P.circle(surf, (120, 255, 150), (cx, cy), R, 3)
            P.rect(surf, (150, 255, 170), (cx - 3, cy - 8, 6, 16))
            P.rect(surf, (150, 255, 170), (cx - 8, cy - 3, 16, 6))
        elif k == "chest":
            w, h = 26, 20
            P.rect(surf, (120, 75, 30), (cx - w // 2, cy - h // 2 + 2, w, h), border_radius=3)
            P.rect(surf, (160, 105, 45), (cx - w // 2, cy - h // 2 - 4, w, 10), border_radius=5)
            P.rect(surf, GOLD_COLOR, (cx - w // 2, cy - h // 2 - 4, w, h + 6), 2, border_radius=4)
            P.line(surf, GOLD_COLOR, (cx - w // 2, cy - 1), (cx + w // 2, cy - 1), 2)
            P.rect(surf, (255, 240, 130), (cx - 3, cy - 4, 6, 7))
            for i in range(3):
                a = t * 2.5 + i * 2.09 + ph
                P.circle(surf, (255, 235, 120), (int(cx + math.cos(a) * 24), int(cy - 4 + math.sin(a) * 18)), 2)
        else:
            P.circle(surf, color, (cx, cy), R)


def add_max_hp(badang, amount):
    """Tambah HP maksimum lalu pulihkan HP sampai penuh."""
    badang.max_hp += amount
    badang.hp = badang.max_hp


def build_artifact_pool(badang):
    return [
        {"name": "Jantung Raksasa", "desc": "+40 HP maksimum & pulih penuh",
         "apply": lambda: add_max_hp(badang, 40)},
        {"name": "Sepatu Angin", "desc": "+0.8 kecepatan gerak",
         "apply": lambda: setattr(badang, "speed", badang.speed + 0.8)},
        {"name": "Batu Magnet", "desc": "+35 jangkauan tarik gem XP",
         "apply": lambda: setattr(badang, "pickup_radius", badang.pickup_radius + 35)},
        {"name": "Cincin Regenerasi", "desc": "+2 HP pulih per detik",
         "apply": lambda: setattr(badang, "regen", badang.regen + 2)},
        {"name": "Berkah Legendaris", "desc": "Semua senjata naik 1 level",
         "apply": lambda: [w.level_up() for w in badang.weapons]},
    ]



def draw_avatar_skill_icon(surf, key, cx, cy, sc=1.0, t=0.0):
    """Ikon skill khusus avatar (bukan gambar avatar): tiap skill punya bentuk sendiri."""
    S = lambda v: max(1, int(v * sc))
    P = pygame.draw
    pt = lambda r, a: (int(cx + math.cos(a) * S(r)), int(cy + math.sin(a) * S(r)))
    if key == "fast_light":
        for i in range(3):
            P.line(surf, (150, 200, 255), (cx - S(32), cy - S(16) + i * S(16)), (cx - S(10), cy - S(16) + i * S(16)), S(3))
        pts = [(cx + S(8), cy - S(32)), (cx - S(10), cy + S(2)), (cx + S(2), cy + S(2)), (cx - S(8), cy + S(32)), (cx + S(18), cy - S(6)), (cx + S(7), cy - S(6))]
        P.polygon(surf, (255, 255, 255), pts)
        P.polygon(surf, (110, 175, 255), pts, 2)
    elif key == "yomatoda":
        P.rect(surf, (45, 20, 70), (cx - S(22), cy - S(16), S(44), S(42)))
        P.ellipse(surf, (150, 60, 200), (cx - S(15), cy - S(12), S(30), S(38)))
        P.ellipse(surf, (15, 4, 30), (cx - S(10), cy - S(6), S(20), S(28)))
        P.rect(surf, (120, 70, 150), (cx - S(30), cy - S(28), S(10), S(56)))
        P.rect(surf, (120, 70, 150), (cx + S(20), cy - S(28), S(10), S(56)))
        P.rect(surf, (165, 100, 200), (cx - S(34), cy - S(32), S(68), S(9)))
        for i in range(3):
            a = t * 2 + i * 2.1
            P.circle(surf, (210, 150, 255), (int(cx + math.cos(a) * S(5)), int(cy + S(8) + math.sin(a) * S(10))), S(2))
    elif key == "sruken":
        a0 = t * 5
        for off, r in ((0.0, 28), (0.0, 12)):
            pts = []
            for i in range(8):
                rr = S(r) if i % 2 == 0 else S(r * 0.28)
                a = a0 + i * math.pi / 4
                pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
            P.polygon(surf, (190, 200, 222) if r > 20 else (90, 100, 125), pts)
            P.polygon(surf, (35, 42, 62), pts, 2)
        P.circle(surf, (35, 42, 62), (cx, cy), S(5))
        P.circle(surf, (190, 200, 222), (cx, cy), S(2))
    elif key == "muscle_skrim":
        P.polygon(surf, (130, 90, 55), [(cx - S(34), cy + S(24)), (cx - S(6), cy - S(26)), (cx + S(10), cy - S(8)), (cx + S(34), cy + S(24))])
        P.polygon(surf, (235, 235, 240), [(cx - S(12), cy - S(14)), (cx - S(6), cy - S(26)), (cx + S(2), cy - S(15)), (cx - S(4), cy - S(10))])
        P.polygon(surf, (80, 50, 28), [(cx - S(34), cy + S(24)), (cx - S(6), cy - S(26)), (cx + S(10), cy - S(8)), (cx + S(34), cy + S(24))], 2)
        P.lines(surf, (255, 190, 80), False, [(cx - S(26), cy + S(30)), (cx - S(12), cy + S(24)), (cx - S(4), cy + S(32)), (cx + S(10), cy + S(25)), (cx + S(26), cy + S(31))], max(2, S(3)))
    elif key == "brudal_mongskter":
        for i in range(3):
            ox = (i - 1) * S(15)
            pts = [(cx + ox - S(10), cy - S(30)), (cx + ox - S(4), cy - S(30)), (cx + ox + S(12), cy + S(30)), (cx + ox + S(5), cy + S(26))]
            P.polygon(surf, (95, 200, 80), pts)
            P.polygon(surf, (25, 70, 20), pts, 2)
        P.circle(surf, (255, 70, 60), (cx - S(24), cy + S(24)), S(3))
        P.circle(surf, (255, 70, 60), (cx + S(24), cy - S(24)), S(3))
    elif key == "badang":
        for i in range(3):
            P.line(surf, (150, 190, 255), (cx - S(34), cy - S(12) + i * S(12)), (cx - S(16), cy - S(12) + i * S(12)), S(3))
        draw_fist(surf, cx + S(8), cy, 0, S(20))
    elif key == "rez":
        P.arc(surf, (255, 225, 90), (cx - S(30), cy - S(30), S(60), S(60)), 0.6, 2.9, max(3, S(7)))
        P.arc(surf, (255, 255, 230), (cx - S(30), cy - S(30), S(60), S(60)), 0.8, 2.7, max(2, S(3)))
        bolt = [(cx + S(14), cy - S(22)), (cx + S(2), cy - S(2)), (cx + S(10), cy - S(2)), (cx - S(2), cy + S(24))]
        P.lines(surf, (255, 245, 120), False, bolt, max(2, S(4)))
    elif key == "black_hole":
        for i in range(4):
            P.circle(surf, (90 + i * 25, 40 + i * 10, 150 + i * 20), (cx, cy), S(32 - i * 6), max(1, S(2)))
        P.circle(surf, (4, 2, 10), (cx, cy), S(12))
        for i in range(6):
            a = -t * 3 + i * math.tau / 6
            P.circle(surf, (225, 190, 255), pt(24 - (i % 3) * 4, a), S(2))
    elif key == "dead_strong":
        flame = [(cx, cy - S(34)), (cx + S(10), cy - S(14)), (cx + S(26), cy - S(18)), (cx + S(18), cy + S(6)), (cx + S(24), cy + S(26)),
                 (cx, cy + S(16)), (cx - S(24), cy + S(26)), (cx - S(18), cy + S(6)), (cx - S(26), cy - S(18)), (cx - S(10), cy - S(14))]
        P.polygon(surf, (215, 45, 45), flame)
        P.polygon(surf, (255, 150, 60), [(cx, cy - S(14)), (cx + S(10), cy + S(2)), (cx + S(6), cy + S(18)), (cx - S(6), cy + S(18)), (cx - S(10), cy + S(2))])
        P.polygon(surf, (110, 15, 20), flame, 2)
    elif key == "string_move":
        for i in range(8):
            a = i * math.pi / 4
            P.line(surf, (110, 235, 175), (cx, cy), pt(32, a), max(1, S(2)))
        for r in (10, 19, 28):
            P.polygon(surf, (200, 255, 225), [pt(r, i * math.pi / 4) for i in range(8)], max(1, S(2)))
        P.circle(surf, (255, 255, 255), (cx, cy), S(3))
    elif key == "aurelia":
        tail = [(cx - S(34), cy - S(30)), (cx - S(4), cy - S(14)), (cx - S(14), cy - S(4))]
        P.polygon(surf, (255, 190, 60), tail)
        P.line(surf, (255, 120, 40), (cx - S(34), cy - S(30)), (cx + S(2), cy + S(2)), S(8))
        P.circle(surf, (120, 50, 20), (cx + S(8), cy + S(8)), S(20))
        P.circle(surf, (255, 130, 50), (cx + S(8), cy + S(8)), S(17))
        P.circle(surf, (255, 220, 120), (cx + S(3), cy + S(3)), S(7))
    elif key == "sera":
        for i, ox in enumerate((-S(20), 0, S(20))):
            top = cy - S(30) + abs(i - 1) * S(8)
            P.line(surf, (230, 235, 250), (cx + ox, top + S(10)), (cx + ox, cy + S(30)), max(2, S(4)))
            P.polygon(surf, (255, 240, 170), [(cx + ox, top - S(4)), (cx + ox - S(7), top + S(12)), (cx + ox + S(7), top + S(12))])
        P.line(surf, (255, 240, 170), (cx - S(26), cy + S(14)), (cx + S(26), cy + S(14)), max(2, S(3)))
    elif key == "nox":
        P.ellipse(surf, (170, 110, 235), (cx - S(34), cy - S(10), S(68), S(20)), max(2, S(4)))
        P.circle(surf, (12, 4, 24), (cx, cy), S(18))
        P.circle(surf, (120, 70, 190), (cx, cy), S(18), max(1, S(2)))
        P.arc(surf, (230, 190, 255), (cx - S(34), cy - S(10), S(68), S(20)), math.pi, math.tau, max(2, S(3)))
        for i in range(3):
            a = t * 2 + i * 2.1
            P.circle(surf, (235, 200, 255), (int(cx + math.cos(a) * S(30)), int(cy + math.sin(a) * S(8))), S(2))
    elif key == "lyra":
        P.circle(surf, (35, 60, 105), (cx, cy), S(30))
        P.circle(surf, (150, 205, 255), (cx, cy), S(30), max(2, S(3)))
        for i in range(12):
            a = i * math.tau / 12
            P.line(surf, (215, 235, 255), pt(24, a), pt(28 if i % 3 else 22, a), max(1, S(2)))
        P.line(surf, (255, 215, 90), (cx, cy), pt(20, t * 1.5 - 1.57), max(2, S(3)))
        P.line(surf, (255, 255, 255), (cx, cy), pt(13, t * 0.3 - 1.57), max(2, S(4)))
        P.circle(surf, (255, 215, 90), (cx, cy), S(3))
    elif key == "ignis":
        wl = [(cx - S(4), cy + S(2)), (cx - S(18), cy - S(14)), (cx - S(34), cy - S(8)), (cx - S(24), cy + S(6)), (cx - S(30), cy + S(18)), (cx - S(10), cy + S(14))]
        P.polygon(surf, (255, 120, 45), wl)
        P.polygon(surf, (255, 120, 45), [(2 * cx - x, y) for x, y in wl])
        P.polygon(surf, (255, 205, 80), [(cx, cy - S(22)), (cx + S(10), cy + S(4)), (cx + S(6), cy + S(28)), (cx, cy + S(20)), (cx - S(6), cy + S(28)), (cx - S(10), cy + S(4))])
        P.circle(surf, (255, 245, 190), (cx, cy - S(8)), S(4))
    elif key == "ryu":
        cone = [(cx - S(4), cy - S(6)), (cx + S(34), cy - S(26)), (cx + S(34), cy + S(26)), (cx - S(4), cy + S(6))]
        P.polygon(surf, (255, 130, 40), cone)
        P.polygon(surf, (255, 215, 90), [(cx + S(2), cy - S(3)), (cx + S(28), cy - S(14)), (cx + S(28), cy + S(14)), (cx + S(2), cy + S(3))])
        P.circle(surf, (50, 150, 95), (cx - S(14), cy), S(16))
        P.polygon(surf, (255, 210, 80), [(cx - S(20), cy - S(12)), (cx - S(26), cy - S(30)), (cx - S(12), cy - S(14))])
        P.polygon(surf, (255, 210, 80), [(cx - S(20), cy + S(12)), (cx - S(26), cy + S(30)), (cx - S(12), cy + S(14))])
        P.circle(surf, (255, 235, 90), (cx - S(10), cy - S(4)), S(3))
    elif key == "glacia":
        for i in range(6):
            a = i * math.tau / 6 + t
            P.line(surf, (200, 240, 255), (cx, cy), pt(30, a), S(3))
            P.circle(surf, (235, 250, 255), pt(30, a), S(4))
        P.circle(surf, (140, 200, 245), (cx, cy), S(9))
    elif key == "zephyr":
        pts = [(cx + S(10), cy - S(32)), (cx - S(8), cy), (cx + S(4), cy), (cx - S(10), cy + S(32)), (cx + S(18), cy - S(4)), (cx + S(6), cy - S(4))]
        P.polygon(surf, (255, 240, 120), pts)
        P.polygon(surf, (200, 170, 40), pts, 2)
    elif key == "venna":
        P.circle(surf, (110, 210, 100), (cx - S(10), cy + S(4)), S(16))
        P.circle(surf, (140, 230, 120), (cx + S(10), cy - S(6)), S(14))
        P.circle(surf, (80, 170, 80), (cx + S(6), cy + S(12)), S(11))
        P.circle(surf, (230, 255, 190), (cx, cy), S(4))
    elif key == "terra":
        P.polygon(surf, (190, 150, 95), [(cx - S(24), cy - S(22)), (cx + S(24), cy - S(22)), (cx + S(20), cy + S(10)), (cx, cy + S(32)), (cx - S(20), cy + S(10))])
        P.polygon(surf, (110, 80, 45), [(cx - S(24), cy - S(22)), (cx + S(24), cy - S(22)), (cx + S(20), cy + S(10)), (cx, cy + S(32)), (cx - S(20), cy + S(10))], 3)
    elif key == "kage":
        for i in range(3):
            P.line(surf, (210, 170, 255), (cx - S(28), cy - S(20) + i * S(16)), (cx + S(28), cy + S(4) + i * S(16) - S(24)), S(4))
        P.circle(surf, (60, 50, 90), (cx, cy), S(6))
    elif key == "lumi":
        P.circle(surf, (255, 250, 200), (cx, cy), S(14))
        for i in range(8):
            a = i * math.tau / 8
            P.line(surf, (255, 225, 110), pt(18, a), pt(32, a), S(3))
    elif key == "pyra":
        P.circle(surf, (60, 40, 40), (cx, cy + S(6)), S(18))
        P.line(surf, (255, 200, 80), (cx + S(8), cy - S(10)), (cx + S(16), cy - S(26)), S(3))
        P.circle(surf, (255, 150, 40), (cx + S(17), cy - S(28)), S(6))
    elif key == "morta":
        P.circle(surf, (190, 255, 205), (cx, cy - S(4)), S(18))
        P.rect(surf, (190, 255, 205), (cx - S(9), cy + S(8), S(18), S(12)))
        P.circle(surf, (30, 60, 45), (cx - S(7), cy - S(4)), S(4))
        P.circle(surf, (30, 60, 45), (cx + S(7), cy - S(4)), S(4))
    else:
        P.circle(surf, GOLD_COLOR, (cx, cy), S(16))


def _class_by_name(nm):
    for c in WEAPON_CLASSES:
        if c.__name__ == nm:
            return c
    return None


def _draw_pair_icon(surf, classes, col, cx, cy, sc, t, variant, fusion=False):
    """Ikon kombo/fusi: medali berwarna khas dengan KEDUA ikon sihir penyusunnya (tiap kombo tampil berbeda)."""
    S = lambda v: int(v * sc)
    dk = tuple(int(c * 0.35) for c in col)
    pygame.draw.circle(surf, dk, (cx, cy), S(31))
    pygame.draw.circle(surf, col, (cx, cy), S(31), max(2, S(3)))
    n_dots = 3 + variant % 6
    for i in range(n_dots):
        a = t * (1.2 if variant % 2 == 0 else -1.2) + i * math.tau / n_dots
        pygame.draw.circle(surf, col, (int(cx + math.cos(a) * S(37)), int(cy + math.sin(a) * S(37))), max(2, S(3 if not fusion else 4)))
    if fusion:
        pygame.draw.circle(surf, WHITE, (cx, cy), S(31), 1)
    for c, ox, oy in zip(classes, (-S(11), S(11)), (S(4), -S(4))):
        if c is not None:
            draw_skill_icon_ent(surf, {"icls": c}, cx + ox, cy + oy, sc * 0.5)



def draw_evo_icon(surf, cls, cx, cy, sc=1.0, t=0.0):
    """Ikon SKILL EVOLUSI: tiap evolusi punya gambar sendiri (bukan bintang, bukan ikon dasar)."""
    S = lambda v: max(1, int(v * sc))
    P = pygame.draw
    n = cls.__name__
    pt = lambda r, a: (int(cx + math.cos(a) * S(r)), int(cy + math.sin(a) * S(r)))
    if n == "PunchWeapon":
        for ox, oy, k in ((-14, 10, 12), (14, 10, 12), (0, -8, 16)):
            draw_fist(surf, cx + S(ox), cy + S(oy), -1.57 if ox == 0 else 0, S(k))
        for i in range(4):
            a = -2.4 + i * 0.55
            P.line(surf, (255, 220, 120), pt(26, a), pt(34, a), max(2, S(3)))
    elif n == "OrbWeapon":
        for i in range(3):
            a = -1.57 + i * math.tau / 3 + t
            draw_proj_shape(surf, "orb", cx + int(math.cos(a) * S(16)), cy + int(math.sin(a) * S(16)), 0, S(9), ORB_COLOR, t)
        P.circle(surf, (255, 255, 200), (cx, cy), S(4))
    elif n == "AuraWeapon":
        for r, col in ((30, (140, 20, 40)), (22, (230, 60, 50))):
            for i in range(14):
                a = i * math.tau / 14 + (t if r > 25 else -t)
                P.polygon(surf, col, [pt(r + 6, a), pt(r - 4, a + 0.17), pt(r - 4, a - 0.17)])
        P.circle(surf, (255, 150, 60), (cx, cy), S(10))
        P.circle(surf, (255, 235, 150), (cx, cy), S(5))
    elif n == "ShockwaveWeapon":
        for i, r in enumerate((10, 19, 28, 36)):
            P.circle(surf, (255, 140 + i * 25, 60), (cx, cy), S(r), max(2, S(5 - i)))
        for i in range(8):
            a = i * math.pi / 4 + 0.3
            P.rect(surf, (150, 110, 80), (pt(36, a)[0] - S(2), pt(36, a)[1] - S(2), S(5), S(5)))
    elif n == "ChainLightningWeapon":
        main = [(cx - S(6), cy - S(34)), (cx + S(8), cy - S(10)), (cx - S(2), cy - S(8)), (cx + S(10), cy + S(34))]
        P.lines(surf, (255, 235, 110), False, main, max(3, S(6)))
        P.lines(surf, (255, 255, 255), False, main, max(1, S(2)))
        for bx, by, ex, ey in ((8, -10, 30, -22), (4, 6, -28, 2), (8, 20, 28, 24)):
            P.lines(surf, (255, 235, 110), False, [(cx + S(bx), cy + S(by)), (cx + S((bx + ex) / 2), cy + S(by + 6)), (cx + S(ex), cy + S(ey))], max(2, S(3)))
            P.circle(surf, (170, 225, 255), (cx + S(ex), cy + S(ey)), S(3))
    elif n == "MultiArrowWeapon":
        for i in range(5):
            draw_proj_shape(surf, "arrow", cx + S(-26 + i * 13), cy + S(-10 + (i % 2) * 14), 1.1, S(8), ARROW_COLOR, t)
    elif n == "FireballWeapon":
        P.circle(surf, (120, 40, 20), (cx, cy), S(26), max(2, S(3)))
        for i in range(4):
            a = t * 2 + i * math.pi / 2
            draw_proj_shape(surf, "fire", cx + int(math.cos(a) * S(26)), cy + int(math.sin(a) * S(26)), a + 1.57, S(7), FIRE_COLOR, t)
        P.circle(surf, (255, 200, 80), (cx, cy), S(6))
    elif n == "IceSpikeWeapon":
        for ang, k in ((-0.75, 12), (-0.25, 16), (0.25, 12)):
            draw_proj_shape(surf, "ice", cx - S(6) + int(math.cos(ang) * S(8)), cy + int(math.sin(ang * 3) * S(22)), ang * 2.2 - 0.3, S(k), (170, 225, 255), t)
        for i in range(5):
            P.circle(surf, (235, 248, 255), (cx + S(-26 + i * 13), cy + S(26) - (i % 2) * S(6)), S(2))
    elif n == "BoomerangWeapon":
        draw_boomerang_shape(surf, cx - S(8), cy - S(6), t * 5, S(18))
        draw_boomerang_shape(surf, cx + S(10), cy + S(8), -t * 5 + 1, S(18))
        P.circle(surf, (255, 235, 150), (cx, cy), S(32), 1)
    elif n == "PoisonCloudWeapon":
        for ox, oy, r in ((-14, 6, 15), (14, 4, 15), (0, -10, 14), (0, 14, 12)):
            P.circle(surf, (35, 70, 40), (cx + S(ox), cy + S(oy)), S(r))
            P.circle(surf, (120, 205, 85), (cx + S(ox), cy + S(oy)), S(r), max(2, S(3)))
        for i in range(4):
            P.circle(surf, (190, 255, 130), (cx + S(-18 + i * 12), cy + S(-4 + (i % 2) * 10)), S(2))
    elif n == "LaserWeapon":
        for a, w in ((-0.55, 7), (0.0, 11), (0.55, 7)):
            e = pt(36, a)
            P.line(surf, (150, 20, 60), (cx - S(8), cy), e, max(3, S(w)))
            P.line(surf, (255, 70, 110), (cx - S(8), cy), e, max(2, S(w * 0.55)))
            P.line(surf, WHITE, (cx - S(8), cy), e, 1)
        P.circle(surf, WHITE, (cx - S(8), cy), S(7))
        P.circle(surf, (255, 70, 110), (cx - S(8), cy), S(7), 2)
    elif n == "MeteorWeapon":
        for ox, oy, r in ((-14, -14, 9), (8, -2, 12), (-4, 18, 8)):
            P.line(surf, (255, 150, 50), (cx + S(ox) - S(r * 2), cy + S(oy) - S(r * 2)), (cx + S(ox), cy + S(oy)), S(r))
            P.circle(surf, (110, 45, 20), (cx + S(ox), cy + S(oy)), S(r))
            P.circle(surf, (255, 140, 50), (cx + S(ox), cy + S(oy)), S(r * 0.8))
    elif n == "KnifeWeapon":
        for i in range(5):
            draw_proj_shape(surf, "knife", cx + S(-24 + i * 12), cy + S(-12 + abs(i - 2) * 8), 1.57 + (i - 2) * 0.22, S(8), (230, 232, 245), t)
    elif n == "TornadoWeapon":
        for ox, sx_ in ((-14, 1.0), (14, 0.75)):
            for i in range(5):
                w = S((34 - i * 6) * sx_)
                y0 = cy - S(26 * sx_) + i * S(10 * sx_)
                P.ellipse(surf, (95, 120, 150), (cx + S(ox) - w // 2, y0, w, S(8)))
                P.ellipse(surf, (210, 235, 255), (cx + S(ox) - w // 2, y0, w, S(8)), 2)
    elif n == "FireTrailWeapon":
        for i in range(6):
            x = cx - S(30) + i * S(12)
            h = S(14 + (i % 3) * 8)
            P.polygon(surf, (90, 12, 12), [(x - S(7), cy + S(22)), (x + S(7), cy + S(22)), (x, cy + S(22) - h - S(6))])
            P.polygon(surf, (235, 60, 25), [(x - S(5), cy + S(22)), (x + S(5), cy + S(22)), (x, cy + S(22) - h)])
            P.polygon(surf, (255, 210, 80), [(x - S(2), cy + S(22)), (x + S(2), cy + S(22)), (x, cy + S(22) - h * 0.55)])
    elif n == "ShieldWeapon":
        draw_shield_shape(surf, cx, cy + S(2), 0, S(22))
        draw_shield_shape(surf, cx - S(26), cy + S(8), 0, S(11))
        draw_shield_shape(surf, cx + S(26), cy + S(8), 0, S(11))
        P.arc(surf, (255, 245, 180), (cx - S(34), cy - S(36), S(68), S(60)), 0.5, 2.64, max(2, S(3)))
    elif n == "GroundSpikeWeapon":
        for i in range(4):
            x = cx - S(30) + i * S(20)
            P.polygon(surf, (150, 120, 85), [(x - S(7), cy + S(26)), (x + S(7), cy + S(26)), (x, cy - S(14) - (i % 2) * S(6))])
        P.arc(surf, (210, 175, 110), (cx - S(34), cy - S(34), S(68), S(60)), 0.0, math.pi, max(3, S(5)))
        P.polygon(surf, (210, 175, 110), [(cx - S(36), cy - S(4)), (cx - S(28), cy - S(4)), (cx - S(28), cy + S(28)), (cx - S(36), cy + S(28))])
        P.polygon(surf, (210, 175, 110), [(cx + S(36), cy - S(4)), (cx + S(28), cy - S(4)), (cx + S(28), cy + S(28)), (cx + S(36), cy + S(28))])
    elif n == "HomingSpiritWeapon":
        for i in range(4):
            x = cx - S(26) + i * S(17)
            y = cy + int(math.sin(t * 3 + i) * S(4)) + (i % 2) * S(8) - S(6)
            draw_proj_shape(surf, "spirit", x, y, 0, S(8), (205, 175, 255), t)
    elif n == "BounceOrbWeapon":
        cols = [(255, 90, 90), (255, 170, 60), (255, 235, 90), (110, 230, 110), (90, 170, 255), (190, 110, 255)]
        P.arc(surf, (255, 255, 255), (cx - S(34), cy - S(26), S(68), S(64)), 0.2, 2.9, max(1, S(2)))
        for i, c in enumerate(cols):
            a = t * 2 + i * math.tau / 6
            P.circle(surf, c, (int(cx + math.cos(a) * S(22)), int(cy + math.sin(a) * S(16))), S(7))
            P.circle(surf, WHITE, (int(cx + math.cos(a) * S(22)), int(cy + math.sin(a) * S(16))), S(7), 1)
    elif n == "SkyLightningWeapon":
        for ox, oy, r in ((-16, -26, 11), (0, -30, 13), (16, -26, 11)):
            P.circle(surf, (70, 75, 100), (cx + S(ox), cy + S(oy)), S(r))
        for ox in (-18, -6, 6, 18):
            P.lines(surf, (255, 245, 150), False, [(cx + S(ox), cy - S(18)), (cx + S(ox) + S(5), cy - S(2)), (cx + S(ox) - S(3), cy - S(2)), (cx + S(ox) + S(3), cy + S(26))], max(2, S(3)))
    elif n == "MineWeapon":
        for ox, oy in ((-18, 8), (0, -10), (18, 8)):
            P.circle(surf, (60, 40, 30), (cx + S(ox), cy + S(oy)), S(11))
            P.circle(surf, (255, 190, 60), (cx + S(ox), cy + S(oy)), S(11), 2)
            for k in range(8):
                a = k * math.pi / 4 + t
                P.line(surf, (255, 120, 40), (cx + S(ox) + math.cos(a) * S(11), cy + S(oy) + math.sin(a) * S(11)), (cx + S(ox) + math.cos(a) * S(18), cy + S(oy) + math.sin(a) * S(18)), max(2, S(2)))
    elif n == "SpearWeapon":
        for dy in (-14, 0, 14):
            P.line(surf, (255, 240, 170), (cx - S(34), cy + S(dy) + S(8)), (cx + S(20), cy + S(dy) - S(6)), max(2, S(3)))
            P.polygon(surf, (255, 255, 235), [(cx + S(32), cy + S(dy) - S(10)), (cx + S(18), cy + S(dy) - S(14)), (cx + S(18), cy + S(dy) - S(2))])
        P.circle(surf, (255, 240, 170), (cx, cy), S(38), 1)
    elif n == "ScytheWeapon":
        for i in range(3):
            P.arc(surf, (220, 170, 255), (cx - S(34 - i * 6), cy - S(34 - i * 6), S(68 - i * 12), S(68 - i * 12)), 0.3 + t + i, 2.4 + t + i, max(3, S(5 - i)))
        P.line(surf, (110, 80, 60), (cx - S(6), cy + S(30)), (cx + S(6), cy - S(10)), max(3, S(4)))
    elif n == "FireBirdWeapon":
        P.polygon(surf, (255, 150, 40), [(cx + S(30), cy - S(2)), (cx - S(8), cy - S(14)), (cx - S(26), cy + S(2)), (cx - S(8), cy + S(14))])
        P.polygon(surf, (255, 90, 30), [(cx - S(2), cy - S(8)), (cx - S(18), cy - S(30)), (cx - S(24), cy - S(6))])
        P.polygon(surf, (255, 90, 30), [(cx - S(2), cy + S(8)), (cx - S(18), cy + S(30)), (cx - S(24), cy + S(6))])
        P.circle(surf, (255, 240, 160), (cx + S(14), cy - S(3)), S(3))
    else:
        draw_skill_icon_ent(surf, {"icls": cls}, cx, cy, sc)
        return
    P.circle(surf, (255, 215, 90), (cx, cy), S(38), max(1, S(1)))


def draw_skill_icon_ent(surf, ent, cx, cy, sc=1.0):
    t = pygame.time.get_ticks() / 1000.0
    S = lambda v: int(v * sc)
    cls = ent.get("cls") or ent.get("icls")
    n = cls.__name__ if cls else ""
    if "av" in ent:
        draw_avatar_skill_icon(surf, ent["av"]["key"], cx, cy, sc, t)
        return
    if "evo_of" in ent:
        draw_evo_icon(surf, ent["evo_of"], cx, cy, sc, t)
        return
    if "combo" in ent:
        key = ent["combo"]
        _draw_pair_icon(surf, COMBO_CLASSES[key], COMBO_COLORS.get(key, COMBO_COLOR), cx, cy, sc, t, COMBO_RING.get(key, 0))
        return
    if "fus" in ent:
        _draw_pair_icon(surf, [_class_by_name(x) for x in ent["fus"]], ent["col"], cx, cy, sc, t, 3 + len(ent["name"]) % 6, fusion=True)
        return
    style = {"OrbWeapon": "orb", "MultiArrowWeapon": "arrow", "FireballWeapon": "fire", "IceSpikeWeapon": "ice",
             "KnifeWeapon": "knife", "HomingSpiritWeapon": "spirit", "BounceOrbWeapon": "orb", "MeteorWeapon": "fire"}.get(n)
    if style:
        col = {"orb": ORB_COLOR, "arrow": ARROW_COLOR, "fire": FIRE_COLOR, "ice": (170, 225, 255), "knife": (230, 232, 245),
               "spirit": (205, 175, 255)}[style]
        draw_proj_shape(surf, style, cx, cy, -0.6 if style in ("arrow", "knife", "ice") else 0, S(13), col, t)
    elif n == "PunchWeapon":
        draw_fist(surf, cx, cy, 0, S(22))
    elif n == "BoomerangWeapon":
        draw_boomerang_shape(surf, cx, cy, t * 6, S(12))
    elif n == "ShieldWeapon":
        draw_shield_shape(surf, cx, cy, 0, S(20))
    elif n in ("ChainLightningWeapon", "SkyLightningWeapon"):
        pygame.draw.lines(surf, LIGHTNING_COLOR, False, [(cx - S(8), cy - S(28)), (cx + S(6), cy - S(6)), (cx - S(4), cy - S(4)), (cx + S(10), cy + S(26))], max(3, S(5)))
    elif n == "LaserWeapon":
        pygame.draw.line(surf, (150, 20, 60), (cx - S(30), cy + S(14)), (cx + S(30), cy - S(14)), S(12))
        pygame.draw.line(surf, (255, 60, 100), (cx - S(30), cy + S(14)), (cx + S(30), cy - S(14)), S(7))
        pygame.draw.line(surf, WHITE, (cx - S(30), cy + S(14)), (cx + S(30), cy - S(14)), S(2))
    elif n == "AuraWeapon":
        pygame.draw.circle(surf, AURA_COLOR, (cx, cy), S(22), 2)
        for i in range(10):
            a = i * math.tau / 10
            pygame.draw.polygon(surf, AURA_COLOR, [(cx + math.cos(a) * S(30), cy + math.sin(a) * S(30)), (cx + math.cos(a + .15) * S(20), cy + math.sin(a + .15) * S(20)), (cx + math.cos(a - .15) * S(20), cy + math.sin(a - .15) * S(20))])
    elif n == "ShockwaveWeapon":
        for i in range(3):
            pygame.draw.circle(surf, SHOCK_COLOR, (cx, cy), S(10 + i * 9), 3)
    elif n == "PoisonCloudWeapon":
        for i in range(5):
            a = i * 1.256
            pygame.draw.circle(surf, (70, 140, 60), (cx + int(math.cos(a) * S(12)), cy + int(math.sin(a) * S(12))), S(11))
            pygame.draw.circle(surf, (150, 230, 110), (cx + int(math.cos(a) * S(12)), cy + int(math.sin(a) * S(12))), S(11), 2)
    elif n == "TornadoWeapon":
        for i in range(5):
            w = S(46 - i * 8)
            pygame.draw.ellipse(surf, (95, 120, 150), (cx - w // 2, cy - S(26) + i * S(11), w, S(10)))
            pygame.draw.ellipse(surf, (210, 235, 255), (cx - w // 2, cy - S(26) + i * S(11), w, S(10)), 2)
    elif n == "FireTrailWeapon":
        for i in range(3):
            pygame.draw.polygon(surf, (230, 70, 25), [(cx - S(22) + i * S(18), cy + S(18)), (cx - S(10) + i * S(18), cy + S(18)), (cx - S(16) + i * S(18), cy - S(14) - i * S(4))])
    elif n == "GroundSpikeWeapon":
        for i in range(3):
            pygame.draw.polygon(surf, (150, 120, 85), [(cx - S(20) + i * S(16), cy + S(20)), (cx - S(8) + i * S(16), cy + S(20)), (cx - S(14) + i * S(16), cy - S(20) + i * S(5))])
    elif n == "MineWeapon":
        pygame.draw.circle(surf, (60, 40, 30), (cx, cy), S(15))
        pygame.draw.circle(surf, (255, 190, 60), (cx, cy), S(15), 3)
        for k in range(6):
            a = k * math.pi / 3
            pygame.draw.line(surf, (255, 120, 40), (cx + math.cos(a) * S(15), cy + math.sin(a) * S(15)), (cx + math.cos(a) * S(23), cy + math.sin(a) * S(23)), max(2, S(3)))
    elif n == "SpearWeapon":
        pygame.draw.line(surf, (230, 235, 245), (cx - S(30), cy + S(14)), (cx + S(16), cy - S(8)), max(3, S(4)))
        pygame.draw.polygon(surf, (255, 255, 235), [(cx + S(30), cy - S(14)), (cx + S(14), cy - S(18)), (cx + S(14), cy - S(2))])
    elif n == "ScytheWeapon":
        pygame.draw.arc(surf, (200, 150, 255), (cx - S(28), cy - S(28), S(56), S(56)), 0.4, 2.6, max(3, S(5)))
        pygame.draw.line(surf, (110, 80, 60), (cx - S(4), cy + S(28)), (cx + S(6), cy - S(8)), max(3, S(4)))
    elif n == "FireBirdWeapon":
        pygame.draw.polygon(surf, (255, 150, 40), [(cx + S(26), cy), (cx - S(8), cy - S(12)), (cx - S(22), cy), (cx - S(8), cy + S(12))])
        pygame.draw.polygon(surf, (255, 90, 30), [(cx - S(2), cy - S(6)), (cx - S(14), cy - S(24)), (cx - S(20), cy - S(4))])
        pygame.draw.circle(surf, (255, 240, 160), (cx + S(12), cy - S(2)), S(3))
    else:
        pygame.draw.circle(surf, GOLD_COLOR, (cx, cy), S(16))



def _icon_heart(surf, cx, cy, s, col):
    r = int(s * 0.27)
    pygame.draw.circle(surf, col, (int(cx - s * 0.25), int(cy - s * 0.12)), r)
    pygame.draw.circle(surf, col, (int(cx + s * 0.25), int(cy - s * 0.12)), r)
    pygame.draw.polygon(surf, col, [(int(cx - s * 0.50), int(cy - s * 0.04)), (int(cx + s * 0.50), int(cy - s * 0.04)),
                                    (int(cx), int(cy + s * 0.48))])


def draw_heart_icon(surf, cx, cy, s, col=(235, 70, 95), edge=WHITE):
    _icon_heart(surf, cx, cy, s + 6, edge)
    _icon_heart(surf, cx, cy, s, col)
    pygame.draw.circle(surf, (255, 195, 205), (int(cx - s * 0.30), int(cy - s * 0.20)), max(2, int(s * 0.08)))


def _icon_plus(surf, x, y, a, th, col):
    pygame.draw.rect(surf, col, (x - a, y - th, a * 2, th * 2))
    pygame.draw.rect(surf, col, (x - th, y - a, th * 2, a * 2))


def _icon_star(surf, x, y, ro, ri, col, edge=None, n=5, rot=-math.pi / 2):
    pts = []
    for i in range(n * 2):
        r = ro if i % 2 == 0 else ri
        a = rot + i * math.pi / n
        pts.append((int(x + math.cos(a) * r), int(y + math.sin(a) * r)))
    pygame.draw.polygon(surf, col, pts)
    if edge is not None:
        pygame.draw.polygon(surf, edge, pts, 2)


def _icon_flask(surf, x, y, S, liquid):
    glass = (205, 228, 245)
    pygame.draw.rect(surf, glass, (x - S(7), y - S(26), S(14), S(15)))
    pygame.draw.circle(surf, glass, (x, y + S(6)), S(19))
    pygame.draw.circle(surf, liquid, (x, y + S(9)), S(15))
    pygame.draw.rect(surf, (150, 105, 60), (x - S(9), y - S(32), S(18), S(7)), border_radius=2)
    pygame.draw.circle(surf, WHITE, (x - S(9), y + S(1)), max(2, S(3)))


def _icon_snow(surf, x, y, R, col, w=3):
    for i in range(6):
        a = i * math.pi / 3
        ex, ey = x + math.cos(a) * R, y + math.sin(a) * R
        pygame.draw.line(surf, col, (x, y), (int(ex), int(ey)), w)
        for fr in (0.55, 0.8):
            bx, by = x + math.cos(a) * R * fr, y + math.sin(a) * R * fr
            for da in (-0.7, 0.7):
                pygame.draw.line(surf, col, (int(bx), int(by)),
                                 (int(bx + math.cos(a + da) * R * 0.22), int(by + math.sin(a + da) * R * 0.22)), max(1, w - 1))


def draw_item_icon(surf, key, cx, cy, sc=1.0):
    """Ikon item toko pedagang / kartu statistik. Kotak ikon ~ 56px pada sc=1."""
    t = pygame.time.get_ticks() / 1000.0
    S = lambda v: int(v * sc)
    x, y = int(cx), int(cy)
    if key in ("maxhp", "stat_hp", "vit"):
        gold = key == "vit"
        draw_heart_icon(surf, x, y, S(36), (255, 160, 50) if gold else (235, 70, 95))
        if gold:
            for i in (-1, 0, 1):
                pygame.draw.polygon(surf, (255, 225, 120), [(x + i * S(11) - S(4), y - S(14)), (x + i * S(11) + S(4), y - S(14)), (x + i * S(11), y - S(23))])
        _icon_plus(surf, x, y - S(2), S(8), S(3), WHITE)
    elif key in ("heal", "xpgain", "lvlup"):
        liquid = {"heal": (235, 60, 80), "xpgain": (80, 230, 150), "lvlup": (255, 205, 60)}[key]
        _icon_flask(surf, x, y + S(2), S, liquid)
        if key == "xpgain":
            _icon_star(surf, x + S(20), y - S(18), S(8), S(3), GOLD_COLOR, BLACK)
        elif key == "lvlup":
            tt = font_small.render("+1", True, BLACK)
            surf.blit(tt, (x - tt.get_width() // 2, y + S(10) - tt.get_height() // 2))
        else:
            _icon_plus(surf, x, y + S(10), S(6), S(2), WHITE)
    elif key in ("speed", "stat_speed"):
        pts = [(x - S(10), y - S(22)), (x + S(6), y - S(22)), (x + S(6), y + S(2)), (x + S(22), y + S(10)), (x + S(22), y + S(22)), (x - S(10), y + S(22))]
        pygame.draw.polygon(surf, (80, 150, 255), pts)
        pygame.draw.polygon(surf, WHITE, pts, 2)
        pygame.draw.rect(surf, (40, 50, 90), (x - S(10), y + S(17), S(32), S(6)))
        pygame.draw.rect(surf, (230, 235, 255), (x - S(10), y - S(22), S(16), S(6)))
        for i in range(3):
            pygame.draw.line(surf, (200, 230, 255), (x - S(16) - i * S(4), y - S(6) + i * S(8)), (x - S(26) - i * S(4), y - S(6) + i * S(8)), 2)
    elif key == "wind":
        for i in range(3):
            pts = [(x - S(24) + k * S(4), y - S(14) + i * S(14) + int(math.sin(k * 0.9 + t * 4 + i) * S(4))) for k in range(13)]
            pygame.draw.lines(surf, (190, 235, 255), False, pts, 3)
        pygame.draw.circle(surf, (190, 235, 255), (x + S(26), y - S(14)), S(4), 2)
    elif key in ("magnet", "stat_magnet"):
        R, w = S(15), S(9)
        cyy = y - S(4)
        pygame.draw.arc(surf, (70, 120, 235), pygame.Rect(x - R, cyy - R, 2 * R, 2 * R), 0, math.pi / 2, w)
        pygame.draw.arc(surf, (225, 60, 60), pygame.Rect(x - R, cyy - R, 2 * R, 2 * R), math.pi / 2, math.pi, w)
        pygame.draw.rect(surf, (225, 60, 60), (x - R, cyy, w, S(16)))
        pygame.draw.rect(surf, (70, 120, 235), (x + R - w, cyy, w, S(16)))
        pygame.draw.rect(surf, (235, 235, 240), (x - R, cyy + S(16), w, S(8)))
        pygame.draw.rect(surf, (235, 235, 240), (x + R - w, cyy + S(16), w, S(8)))
    elif key == "pull":
        pygame.draw.polygon(surf, (70, 225, 150), [(x, y - S(9)), (x + S(8), y), (x, y + S(9)), (x - S(8), y)])
        pygame.draw.polygon(surf, WHITE, [(x, y - S(9)), (x + S(8), y), (x, y + S(9)), (x - S(8), y)], 2)
        for a in range(4):
            ang = a * math.pi / 2 + math.pi / 4
            c, sn = math.cos(ang), math.sin(ang)
            p0 = (x + c * S(26), y + sn * S(26))
            p1 = (x + c * S(14), y + sn * S(14))
            pygame.draw.line(surf, (190, 235, 255), p0, p1, 3)
            pygame.draw.polygon(surf, (190, 235, 255), [(int(p1[0]), int(p1[1])), (int(p1[0] + c * S(6) - sn * S(5)), int(p1[1] + sn * S(6) + c * S(5))),
                                                        (int(p1[0] + c * S(6) + sn * S(5)), int(p1[1] + sn * S(6) - c * S(5)))])
    elif key in ("regen", "stat_regen"):
        pygame.draw.arc(surf, (90, 225, 130), pygame.Rect(x - S(22), y - S(22), S(44), S(44)), 0.5, 5.4, 4)
        ex, ey = x + math.cos(5.4) * S(22), y - math.sin(5.4) * S(22)
        pygame.draw.polygon(surf, (90, 225, 130), [(int(ex) - S(7), int(ey) - S(3)), (int(ex) + S(5), int(ey) - S(7)), (int(ex) + S(3), int(ey) + S(6))])
        _icon_plus(surf, x, y, S(10), S(4), (90, 225, 130))
        pygame.draw.rect(surf, WHITE, (x - S(10), y - S(4), S(20), S(8)), 1)
    elif key == "power":
        _icon_star(surf, x, y, S(27), S(12), (255, 150, 40), WHITE)
        pygame.draw.circle(surf, (255, 235, 150), (x, y), S(7))
    elif key == "scroll":
        pygame.draw.rect(surf, (242, 228, 188), (x - S(18), y - S(20), S(36), S(40)))
        pygame.draw.rect(surf, (150, 110, 60), (x - S(18), y - S(20), S(36), S(40)), 2)
        for yy in (-24, 16):
            pygame.draw.ellipse(surf, (200, 160, 100), (x - S(21), y + S(yy), S(42), S(9)))
            pygame.draw.ellipse(surf, (120, 85, 45), (x - S(21), y + S(yy), S(42), S(9)), 2)
        pygame.draw.polygon(surf, (80, 220, 120), [(x, y - S(12)), (x - S(10), y), (x - S(4), y), (x - S(4), y + S(13)), (x + S(4), y + S(13)), (x + S(4), y), (x + S(10), y)])
    elif key == "revive":
        for sd in (-1, 1):
            wing = [(x + sd * S(8), y - S(2)), (x + sd * S(27), y - S(16)), (x + sd * S(31), y - S(5)), (x + sd * S(25), y + S(1)), (x + sd * S(29), y + S(9)), (x + sd * S(8), y + S(9))]
            pygame.draw.polygon(surf, (245, 248, 255), wing)
            pygame.draw.polygon(surf, (150, 165, 200), wing, 2)
        draw_heart_icon(surf, x, y + S(3), S(24))
        pygame.draw.ellipse(surf, GOLD_COLOR, (x - S(10), y - S(25), S(20), S(8)), 3)
    elif key == "bomb":
        pygame.draw.circle(surf, (35, 35, 45), (x, y + S(6)), S(18))
        pygame.draw.circle(surf, (110, 110, 130), (x, y + S(6)), S(18), 2)
        pygame.draw.circle(surf, (170, 170, 190), (x - S(7), y), S(4))
        pygame.draw.line(surf, (160, 120, 70), (x + S(9), y - S(10)), (x + S(16), y - S(19)), 3)
        _icon_star(surf, x + S(18), y - S(22), S(7 + int(2 * math.sin(t * 12))), S(3), (255, 210, 70), (255, 120, 40))
        _icon_plus(surf, x, y + S(6), S(8), S(2), GOLD_COLOR)
    elif key == "armor":
        draw_shield_shape(surf, x - S(3), y, 0, S(20), (120, 105, 225), WHITE)
    elif key == "shieldt":
        draw_shield_shape(surf, x - S(5), y + S(2), 0, S(19), (90, 200, 255), WHITE)
        pygame.draw.circle(surf, (20, 30, 55), (x + S(16), y + S(14)), S(11))
        pygame.draw.circle(surf, WHITE, (x + S(16), y + S(14)), S(11), 2)
        pygame.draw.line(surf, WHITE, (x + S(16), y + S(14)), (x + S(16), y + S(7)), 2)
        pygame.draw.line(surf, WHITE, (x + S(16), y + S(14)), (x + S(21), y + S(14)), 2)
    elif key == "goldgain":
        pygame.draw.circle(surf, (225, 170, 30), (x, y), S(21))
        pygame.draw.circle(surf, (255, 215, 70), (x, y), S(18))
        pygame.draw.circle(surf, (190, 130, 20), (x, y), S(14), 2)
        _icon_star(surf, x, y, S(10), S(4), (190, 130, 20))
        _icon_star(surf, x + S(19), y - S(19), S(7), S(2), WHITE, n=4)
    elif key == "freeze":
        pygame.draw.circle(surf, (40, 85, 140), (x, y), S(25))
        pygame.draw.circle(surf, (150, 215, 255), (x, y), S(25), 2)
        _icon_snow(surf, x, y, S(20), (225, 245, 255), 3)
    elif key == "chestbuy":
        pygame.draw.rect(surf, (150, 100, 50), (x - S(21), y - S(2), S(42), S(22)), border_radius=3)
        pygame.draw.rect(surf, (190, 135, 65), (x - S(21), y - S(18), S(42), S(18)), border_radius=7)
        pygame.draw.rect(surf, (80, 50, 20), (x - S(21), y - S(18), S(42), S(38)), 2, border_radius=5)
        pygame.draw.rect(surf, GOLD_COLOR, (x - S(21), y - S(4), S(42), S(5)))
        pygame.draw.rect(surf, GOLD_COLOR, (x - S(5), y - S(6), S(10), S(12)), border_radius=2)
        pygame.draw.rect(surf, BLACK, (x - S(2), y - S(1), S(4), S(5)))
        _icon_star(surf, x + S(19), y - S(22), S(8), S(3), WHITE, n=4)
    elif key == "roti":
        pygame.draw.ellipse(surf, (222, 160, 80), (x - S(23), y - S(8), S(46), S(28)))
        pygame.draw.ellipse(surf, (150, 95, 40), (x - S(23), y - S(8), S(46), S(28)), 2)
        for i in range(3):
            pygame.draw.line(surf, (250, 225, 170), (x - S(12) + i * S(11), y - S(3)), (x - S(7) + i * S(11), y + S(8)), 3)
        for i in (-1, 1):
            pts = [(x + i * S(8) + int(math.sin(k * 1.2 + t * 3 + i) * S(3)), y - S(14) - k * S(4)) for k in range(5)]
            pygame.draw.lines(surf, (235, 240, 245), False, pts, 2)
    elif key == "cancel":
        pygame.draw.line(surf, (235, 80, 80), (x - S(16), y - S(16)), (x + S(16), y + S(16)), 6)
        pygame.draw.line(surf, (235, 80, 80), (x - S(16), y + S(16)), (x + S(16), y - S(16)), 6)
    elif key == "book":
        pygame.draw.rect(surf, (120, 60, 150), (x - S(18), y - S(22), S(36), S(44)), border_radius=3)
        pygame.draw.rect(surf, (230, 200, 255), (x - S(18), y - S(22), S(36), S(44)), 2, border_radius=3)
        pygame.draw.rect(surf, (90, 40, 120), (x - S(18), y - S(22), S(7), S(44)))
        _icon_star(surf, x + S(3), y - S(2), S(9), S(4), GOLD_COLOR, BLACK)
        pygame.draw.line(surf, (230, 200, 255), (x - S(4), y + S(13)), (x + S(11), y + S(13)), 2)
    else:
        pygame.draw.circle(surf, GOLD_COLOR, (x, y), S(18))
        pygame.draw.circle(surf, BLACK, (x, y), S(18), 2)


def draw_fusion_icon(surf, cx, cy, sc=1.0, col=(200, 90, 255), tpl="merge"):
    """Ikon senjata fusi: pola berbeda per template. 'merge' = dua sihir melebur jadi satu."""
    t = pygame.time.get_ticks() / 1000.0
    S = lambda v: int(v * sc)
    x, y = int(cx), int(cy)
    lite = tuple(min(255, c + 80) for c in col)
    dark = tuple(max(0, c - 90) for c in col)
    if tpl == "merge":
        pygame.draw.circle(surf, dark, (x, y), S(25))
        for sd, c2 in ((-1, (255, 120, 60)), (1, (110, 190, 255))):
            ox = x + sd * S(17)
            pygame.draw.circle(surf, c2, (ox, y + S(8) * 0 - S(6)), S(9))
            pygame.draw.circle(surf, WHITE, (ox, y - S(6)), S(9), 2)
            pygame.draw.line(surf, lite, (ox - sd * S(8), y - S(2)), (x + sd * S(4), y + S(8)), 3)
        _icon_star(surf, x, y + S(8), S(14), S(6), col, WHITE)
        _icon_plus(surf, x, y - S(16), S(5), S(2), WHITE)
        return
    pygame.draw.circle(surf, dark, (x, y), S(25))
    pygame.draw.circle(surf, lite, (x, y), S(25), 2)
    if tpl == "nova":
        for i, r in enumerate((6, 13, 20)):
            pygame.draw.circle(surf, lite if i % 2 == 0 else col, (x, y), S(r), 3)
        pygame.draw.circle(surf, WHITE, (x, y), S(3))
    elif tpl == "blades":
        for a in (-0.8, 0.8):
            c, sn = math.cos(a), math.sin(a)
            pts = [(x + c * S(22), y + sn * S(22)), (x - sn * S(4), y + c * S(4)), (x - c * S(14), y - sn * S(14)), (x + sn * S(4), y - c * S(4))]
            pygame.draw.polygon(surf, (235, 238, 250), [(int(px), int(py)) for px, py in pts])
            pygame.draw.polygon(surf, col, [(int(px), int(py)) for px, py in pts], 2)
    elif tpl == "beam":
        pygame.draw.line(surf, col, (x - S(22), y + S(10)), (x + S(22), y - S(10)), S(9))
        pygame.draw.line(surf, lite, (x - S(22), y + S(10)), (x + S(22), y - S(10)), S(5))
        pygame.draw.line(surf, WHITE, (x - S(22), y + S(10)), (x + S(22), y - S(10)), 2)
        pygame.draw.circle(surf, WHITE, (x - S(22), y + S(10)), S(5))
    elif tpl == "barrage":
        for i in range(5):
            a = -0.9 + i * 0.45
            c, sn = math.cos(a), math.sin(a)
            pygame.draw.line(surf, lite, (x - S(18), y + S(8)), (x - S(18) + c * S(38), y + S(8) + sn * S(38)), 2)
            pygame.draw.circle(surf, WHITE, (int(x - S(18) + c * S(38)), int(y + S(8) + sn * S(38))), S(4))
            pygame.draw.circle(surf, col, (int(x - S(18) + c * S(38)), int(y + S(8) + sn * S(38))), S(4), 2)
    elif tpl == "storm":
        for k in range(3):
            pygame.draw.arc(surf, lite if k % 2 == 0 else col, pygame.Rect(x - S(8 + k * 6), y - S(8 + k * 6), S(16 + k * 12), S(16 + k * 12)), k * 1.4, k * 1.4 + 4.3, 3)
        pygame.draw.circle(surf, WHITE, (x, y), S(3))
    elif tpl == "chain":
        pts = [(x - S(18), y + S(10)), (x - S(6), y - S(8)), (x + S(4), y + S(6)), (x + S(18), y - S(12))]
        pygame.draw.lines(surf, lite, False, pts, 3)
        for p in pts:
            pygame.draw.circle(surf, WHITE, p, S(4))
            pygame.draw.circle(surf, col, p, S(4), 2)
    else:
        _icon_star(surf, x, y, S(16), S(7), lite, WHITE)


def weapon_icon_ent(w):
    """Entri ikon yang SAMA dengan Almanak: dasar / evolusi / fusi (kombo memakai kunci 'combo')."""
    if hasattr(w, "a") and hasattr(w, "b") and hasattr(w, "tpl"):
        return {"fus": sorted((w.a, w.b)), "col": w.col, "name": w.display_name}
    if getattr(w, "evo_form", False):
        return {"evo_of": w.evo_base}
    return {"cls": type(w)}


def card_icon_kind(choice):
    """Tentukan ikon kartu: ('cls', cls) | ('item', key) | ('fusion', col, tpl) | ('evo', cls)."""
    k = choice.get("kind")
    if k == "fusion":
        return ("fusion", (200, 90, 255), "merge")
    if k == "fcancel":
        return ("item", "cancel")
    if "item" in choice:
        return ("item", choice["item"])
    if "fusent" in choice:
        return ("fuspair", choice["fusent"])
    if "fx" in choice:
        return ("fusion", choice["fx"][0], choice["fx"][1])
    w = choice.get("w")
    if w is not None and hasattr(w, "a") and hasattr(w, "b") and hasattr(w, "tpl"):
        return ("fuspair", w)
    cls = choice.get("cls") or (type(w) if w is not None else None)
    if cls is not None:
        if getattr(cls, "evo_form", False):
            return ("evo", cls.evo_base)
        if k == "learn" and evo_enabled():
            return ("evo", cls)
        return ("evo" if k == "evo" else "cls", cls)
    return ("item", "?")


def draw_card_icon(surf, choice, box, rc):
    """Gambar kotak ikon di sisi kiri kartu."""
    pygame.draw.rect(surf, (18, 16, 30), box, border_radius=8)
    pygame.draw.rect(surf, rc, box, 2, border_radius=8)
    sc = box.w / 68.0
    kind = card_icon_kind(choice)
    cx, cy = box.centerx, box.centery
    old = surf.get_clip()
    surf.set_clip(box.inflate(-4, -4))
    try:
        if kind[0] in ("cls", "evo"):
            if kind[0] == "evo":
                draw_evo_icon(surf, kind[1], cx, cy, sc * 1.1, pygame.time.get_ticks() / 1000.0)
            else:
                draw_skill_icon_ent(surf, {"cls": kind[1]}, cx, cy, sc * 1.15)
        elif kind[0] == "fuspair":
            draw_skill_icon_ent(surf, kind[1] if isinstance(kind[1], dict) else weapon_icon_ent(kind[1]), cx, cy, sc * 1.15)
        elif kind[0] == "item":
            draw_item_icon(surf, kind[1], cx, cy, sc)
        else:
            draw_fusion_icon(surf, cx, cy, sc, kind[1], kind[2])
    finally:
        surf.set_clip(old)


def skill_tags_text(cls):
    return "/".join(WEAPON_TAGS.get(cls.__name__, ["Umum"]))


def build_upgrade_pool(badang):
    pool = []
    for w in badang.weapons:
        if w.level >= MAX_WEAPON_LEVEL:
            continue
        nxt = w.level + 1
        if isinstance(w, FusionWeapon):
            pool.append({"kind": "lv", "name": f"{w.display_name} Lv.{nxt}", "desc": f"Perkuat senjata fusi (+16% damage, maks Lv.{MAX_WEAPON_LEVEL})  [{'/'.join(w.tags)}]",
                         "apply": (lambda w=w: w.level_up()), "rarity": w.rarity, "w": w})
            continue
        tg = skill_tags_text(type(w))
        if w.evolved:
            pool.append({"kind": "lv", "name": f"{w.evolved_name} Lv.{nxt}",
                         "desc": f"Upgrade evolusi: {w.evolved_desc} (+18% damage, maks Lv.{MAX_WEAPON_LEVEL})  [{tg}]",
                         "apply": (lambda w=w: w.level_up()), "rarity": w.rarity, "cls": type(w)})
        else:
            pool.append({"kind": "lv", "name": f"{w.display_name} Lv.{nxt}",
                         "desc": "Naikkan level senjata ini" + (" (Lv.4: damage +30%)" if nxt == 4 else "") + "  (Evolusi butuh Buku Evolusi)" + f"  [{tg}]",
                         "apply": (lambda w=w: w.level_up()), "rarity": w.rarity, "cls": type(w)})
    owned = RUN_RULES["owned"]
    if len(badang.weapons) < RUN_RULES["slots"]:
        for cls in WEAPON_CLASSES:
            if badang.has_weapon(cls):
                continue
            if owned is not None and cls.__name__ not in owned:
                continue
            _evo = evo_enabled()
            pool.append({"kind": "learn", "name": f"Pelajari: {cls.evolved_name if _evo else cls.display_name}",
                         "desc": (f"Langsung EVOLUSI: {cls.evolved_desc}" if _evo else cls.base_desc) + f"  [{skill_tags_text(cls)}]",
                         "apply": (lambda cls=cls: badang.weapons.append(cls(level=1))),
                         "rarity": WEAPON_RARITY.get(cls.__name__, 0), "cls": cls})
    if badang.can_fuse():
        pool.append({"kind": "fusion", "name": "FUSI SIHIR",
                     "desc": f"Lebur 2 sihir jadi 1 SENJATA FUSI baru. Keduanya hilang, slot terbuka  ({badang.fusions}/{MAX_FUSIONS})", "apply": lambda: None})
    stat_upgrades = [
        {"name": "Vitalitas", "desc": "+25 HP maksimum & pulih penuh", "item": "stat_hp",
         "apply": lambda: add_max_hp(badang, 25)},
        {"name": "Kaki Ringan", "desc": "+0.5 kecepatan gerak", "item": "stat_speed",
         "apply": lambda: setattr(badang, "speed", badang.speed + 0.5)},
        {"name": "Magnet Kuat", "desc": "+25 jangkauan tarik gem XP", "item": "stat_magnet",
         "apply": lambda: setattr(badang, "pickup_radius", badang.pickup_radius + 25)},
        {"name": "Regenerasi", "desc": "+1 HP pulih per detik", "item": "stat_regen",
         "apply": lambda: setattr(badang, "regen", badang.regen + 1)},
    ]
    pool.extend(stat_upgrades)
    return pool


class UpgradeMenu:
    def __init__(self, badang, forced=None):
        self.badang = badang
        self.title = "LEVEL UP!"
        self.fuse_main = None
        self.fused = None
        pool = build_upgrade_pool(badang)
        if forced is not None:
            self.main_choices = forced
        else:
            ups = [c for c in pool if c.get("kind") in ("evo", "lv")]
            learns = [c for c in pool if c.get("kind") == "learn"]
            fus = [c for c in pool if c.get("kind") == "fusion"]
            others = [c for c in pool if c.get("kind") not in ("evo", "lv", "learn", "fusion")] + learns
            choices = random.sample(ups, min(2, len(ups)))
            extra = others + [c for c in ups if c not in choices]
            random.shuffle(extra)
            choices = choices + extra[:3 - len(choices)]
            if fus and (random.random() < 0.55 or len(choices) < 3):
                if len(choices) >= 3:
                    choices[-1] = fus[0]
                else:
                    choices.append(fus[0])
            self.main_choices = choices
        self.choices = list(self.main_choices)
        self.layout()

    def layout(self):
        n = len(self.choices)
        card_w, card_h = 640, (100 if n <= 3 else 64)
        gap = 20 if n <= 3 else 10
        total_h = card_h * n + gap * (n - 1)
        start_y = HEIGHT / 2 - total_h / 2 + 24
        self.rects = [pygame.Rect((WIDTH - card_w) / 2, start_y + i * (card_h + gap), card_w, card_h) for i in range(n)]
        self.card_h = card_h

    @staticmethod
    def recipe_known():
        """Resep fusi terlihat bila Buku Fusi dimiliki (atau di tutorial)."""
        b = RUN_RULES.get("books")
        return b is None or "fusion" in b

    def begin_fuse_main(self):
        self.title = "FUSI: PILIH SIHIR PERTAMA"
        ch = [{"kind": "fpick", "w": w, "name": f"{w.display_name} Lv.{w.level}",
               "desc": "Sihir ini akan HILANG dan melebur jadi senjata fusi", "rarity": w.rarity}
              for w in self.badang.fusable()]
        ch.append({"kind": "fcancel", "name": "BATAL", "desc": "Kembali ke pilihan level up"})
        self.choices = ch
        self.layout()

    def begin_fuse_sac(self):
        self.title = "FUSI: PILIH SIHIR KEDUA (keduanya hilang)"
        known = self.recipe_known()
        ch = []
        for w in self.badang.fusable():
            if w is self.fuse_main:
                continue
            a, b = type(self.fuse_main).__name__, type(w).__name__
            if known:
                rec = fusion_recipe(a, b)
                ch.append({"kind": "fdo", "w": w, "name": f"{w.display_name} Lv.{w.level}  =  {rec['name']}", "desc": rec["desc"],
                           "rarity": fusion_recipe_rarity(a, b), "fx": (rec["col"], rec["tpl"]),
                           "fusent": {"fus": sorted((a, b)), "col": rec["col"], "name": rec["name"]}})
            else:
                ch.append({"kind": "fdo", "w": w, "name": f"{w.display_name} Lv.{w.level}",
                           "desc": "Hasil fusi: ??? (beli Buku Fusi di Toko untuk melihat resep)",
                           "rarity": w.rarity, "fx": ((200, 90, 255), "merge")})
        ch.append({"kind": "fcancel", "name": "BATAL", "desc": "Kembali ke pilihan level up"})
        self.choices = ch
        self.layout()

    def reset_main(self):
        self.title = "LEVEL UP!"
        self.fuse_main = None
        self.choices = list(self.main_choices)
        self.layout()

    def handle_click(self, pos):
        for r, choice in zip(self.rects, self.choices):
            if r.collidepoint(pos):
                k = choice.get("kind")
                if k == "fusion":
                    self.begin_fuse_main()
                    return False
                if k == "fpick":
                    self.fuse_main = choice["w"]
                    self.begin_fuse_sac()
                    return False
                if k == "fcancel":
                    self.reset_main()
                    return False
                if k == "fdo":
                    self.fused = self.badang.fuse(self.fuse_main, choice["w"])
                    sfx("summon")
                    return True
                choice["apply"]()
                return True
        return False

    KIND_TAG = {"evo": ("EVOLUSI", (255, 215, 90)), "learn": ("BARU", (110, 235, 140)), "lv": ("NAIK LEVEL", (130, 200, 255)),
                "fusion": ("FUSI", (215, 130, 255)), "fpick": ("PERTAMA", (255, 215, 90)), "fdo": ("KEDUA", (255, 120, 120))}

    def draw(self, surf):
        overlay = veil_surface((0, 0, 0, 185))
        surf.blit(overlay, (0, 0))
        title = font_big.render(self.title, True, GOLD_COLOR)
        surf.blit(title, (WIDTH / 2 - title.get_width() / 2, self.rects[0].y - 74))
        tall = self.card_h > 80
        for r, choice in zip(self.rects, self.choices):
            rc = RARITY_COLORS[choice["rarity"]] if "rarity" in choice else GOLD_COLOR
            pygame.draw.rect(surf, PANEL_COLOR, r, border_radius=10)
            pygame.draw.rect(surf, rc, r, width=2, border_radius=10)
            if choice.get("kind") == "fusion":
                pygame.draw.rect(surf, (200, 90, 255), r, width=4, border_radius=10)
            box = pygame.Rect(r.x + 8, r.y + 8, r.h - 16, r.h - 16)
            draw_card_icon(surf, choice, box, rc)
            tx = box.right + 16
            tw = r.right - tx - 16
            if tall:
                name = font_med.render(self.fit_desc_font(font_med, choice["name"], tw - 110), True, WHITE)
                surf.blit(name, (tx, r.y + 12))
                for i, ln in enumerate(wrap_text(choice["desc"], font_small, tw)[:2]):
                    surf.blit(font_small.render(ln, True, GRAY), (tx, r.y + 48 + i * 20))
            else:
                name = font_med.render(self.fit_desc_font(font_med, choice["name"], tw - 100), True, WHITE)
                surf.blit(name, (tx, r.y + 6))
                surf.blit(font_small.render(self.fit_desc(choice["desc"], tw), True, GRAY), (tx, r.y + 34))
            if "rarity" in choice:
                tg = font_small.render(RARITIES[choice["rarity"]], True, rc)
                surf.blit(tg, (r.right - tg.get_width() - 14, r.y + 10))
            kt = self.KIND_TAG.get(choice.get("kind"))
            if kt and tall:
                kk = font_small.render(kt[0], True, kt[1])
                surf.blit(kk, (r.right - kk.get_width() - 14, r.y + 32))

    @staticmethod
    def fit_desc_font(font, text, max_w):
        while font.size(text)[0] > max_w and len(text) > 8:
            text = text[:-2]
        return text

    @staticmethod
    def fit_desc(text, max_w):
        while font_small.size(text)[0] > max_w and len(text) > 8:
            text = text[:-2]
        return text


SHOP_CATALOG = [
    ("heal", "Ramuan Penuh", "Pulihkan HP sampai penuh", 40),
    ("maxhp", "Jantung Kuat", "+40 HP maksimum & pulih", 90),
    ("speed", "Sepatu Kilat", "+0.6 kecepatan gerak", 80),
    ("magnet", "Batu Magnet", "+45 jangkauan tarik gem", 60),
    ("regen", "Cincin Regenerasi", "+1.5 HP pulih per detik", 110),
    ("power", "Kekuatan Sihir", "+10% damage semua skill (permanen)", 160),
    ("scroll", "Gulungan Naik Level", "Satu skill acak naik 1 level", 170),
    ("revive", "Nyawa Kedua", "Bangkit sekali dengan 50% HP", 260),
    ("bomb", "Bom Suci", "Musnahkan semua musuh biasa", 70),
    ("armor", "Zirah Sihir", "-6% damage yang diterima (permanen)", 140),
    ("xpgain", "Ramuan Kebijaksanaan", "+25% XP dari orb (permanen)", 190),
    ("goldgain", "Koin Keberuntungan", "+25% Gold dari musuh (permanen)", 120),
    ("vit", "Darah Naga", "+80 HP maksimum & pulih", 150),
    ("shieldt", "Perisai Sementara", "Kebal damage selama 8 detik", 90),
    ("freeze", "Bom Es", "Bekukan semua musuh biasa 5 detik", 100),
    ("pull", "Jala Magnet", "Tarik semua gem di dunia ke arahmu", 50),
    ("chestbuy", "Peti Misteri", "Munculkan 1 Peti Harta di dekatmu", 700),
    ("lvlup", "Elixir Level", "Langsung naik 1 level", 300),
    ("roti", "Roti Hangat", "Pulihkan 40% HP", 25),
    ("wind", "Jubah Angin", "+0.3 kecepatan gerak", 70),
]


def shop_price(base, level):
    return int(base * 1.25 * (1 + 0.07 * (level - 1)))


MERCHANT_LINES = {
    "intro": [("PEDAGANG", "Selamat datang, penyihir muda. Aku Pedagang Keliling. Dulu aku penjaga menara di Lembah Abu, sebelum Retakan terbuka dan monster membanjiri negeri."),
              ("PEDAGANG", "Kabarnya Raja Inflasi akan bangkit lagi dan menelan seluruh emas dunia. Hanya penyihir terlatih yang bisa menghentikannya, jadi aku akan melatihmu."),
              ("PAHLAWAN", "Aku siap, Pak Pedagang. Apa yang harus kulakukan pertama kali?"),
              ("PEDAGANG", "BERGERAK dulu! Di HP: sentuh layar lalu geser jarimu ke arah tujuan, joystick muncul di bawah jarimu. Di komputer: tombol W (atas), A (kiri), S (bawah), D (kanan), atau tombol panah. Berjalanlah sekitar 280 langkah!")],
    "attack": [("PEDAGANG", "Bagus! Sekarang robot latihan buatanku datang. Kubuat dari sisa zirah prajurit yang gugur di Lembah Abu."),
               ("PEDAGANG", "Kamu TIDAK perlu menekan tombol serang. Sihirmu menembak musuh TERDEKAT secara otomatis. Tugasmu: terus bergerak, jaga jarak, dan biarkan sihirmu bekerja."),
               ("PEDAGANG", "Panah KUNING di layar menunjuk robot terdekat. Kalahkan 10 robot!")],
    "orb": [("PEDAGANG", "Tiap monster yang jatuh meninggalkan ORB XP. Berjalanlah ke orb (ikuti panah HIJAU), dan orb terisap otomatis saat kamu dekat. Tidak perlu menekan apa pun."),
            ("PEDAGANG", "Bila bar XP di atas layar penuh, kamu NAIK LEVEL. Para penyihir agung dulu pun memulai dari satu orb kecil. Ambil orb besar itu!")],
    "upgrade": [("PEDAGANG", "Setiap naik level, permainan berhenti dan 3 kartu muncul. SENTUH (di komputer: klik) kartu pilihanmu: sihir baru atau penguat."),
                ("PEDAGANG", "Kamu bisa membawa maksimal 6 sihir aktif (5 di Mode Inflasi), tiap sihir maksimal Lv.7. Pilihlah sesuai gayamu, itulah yang membedakan penyihir hebat dari yang biasa.")],
    "hp": [("PEDAGANG", "Lihat bar MERAH di kiri atas: itu HP-mu. Sentuhan musuh dan peluru mengurangi HP, dan kalau habis kamu kalah. Di latihan ini kupulihkan, di dunia nyata tidak!"),
           ("PEDAGANG", "Robo-Tank dan Robo-Penerjang datang. Jangan berhenti di tempat: geser terus menjauh dari mereka. Aku kehilangan menaraku karena terlalu lama berdiam diri.")],
    "warn": [("PEDAGANG", "AWAS! Lingkaran atau garis MERAH di tanah adalah serangan yang akan datang. Geser keluar dari area merah sebelum menyala, dan dengarkan bunyi peringatannya."),
             ("PEDAGANG", "Kali ini serangannya sungguhan dan akan mengurangi HP-mu. Di Lembah Abu, satu kelengahan saja bisa menghabiskan satu pasukan.")],
    "shop": [("PEDAGANG", "Nah, kamu menemukanku! Semua robot dan boss robot di arena ini BUATANKU, khusus untuk latihan. Tenang, tidak ada musuh yang asli."),
             ("PEDAGANG", "Lihat kubah cahaya ini? Musuh dan boss TIDAK bisa melewati perisaiku. Masuklah kapan pun kau terdesak."),
             ("PEDAGANG", "Aku berkeliling dunia menjual ramuan dan sihir. Di permainan sungguhan, kamu akan menemuiku tiap kelipatan 5 level. Sentuh barang yang ingin dibeli dengan Gold dari musuh, lalu tutup toko."),
             ("PEDAGANG", "Stokku selalu acak, jenis dan jumlahnya berubah tiap aku datang, jadi cek setiap kali. Waktuku terbatas, setelah habis aku pergi tapi pasti kembali. Silakan belanja!")],
    "evo": [("PEDAGANG", "Sekarang pelajaran EVOLUSI. Guruku dulu berkata: sihir yang dilatih sungguh-sungguh akan berubah wujud."),
            ("PEDAGANG", "Tiap sihir naik sampai Lv.5 lalu BEREVOLUSI: sihir lama LENYAP dan diganti sihir evolusi bernama baru, damage 2x lipat dan efek baru. Lv.6 dan Lv.7 menguatkannya lagi."),
            ("PEDAGANG", "Kuberi Bola Api dan Duri Es di Lv.4. SENTUH kartu EVOLUSI di layar berikutnya!")],
    "combo": [("PEDAGANG", "Bagus sekali! Sekarang KOMBO. Penyihir hebat tidak bertarung sendirian, sihir mereka saling melengkapi."),
              ("PEDAGANG", "Bila dua sihir yang cocok sama-sama berevolusi, keduanya menyatu jadi KOMBO dengan bonus damage +40%."),
              ("PEDAGANG", "Bola Api + Duri Es menjadi Uap Beku. SENTUH kartu untuk mengevolusikan sihir yang satunya lagi!")],
    "fusion": [("PEDAGANG", "Terakhir untuk sihir: FUSI. Ini rahasia yang kusimpan sejak menara jatuh."),
               ("PEDAGANG", "Satu run punya 6 slot sihir aktif (5 di Mode Inflasi). Fusi melebur DUA sihir menjadi satu SENJATA FUSI baru, dengan nama, bentuk serangan, dan efek sendiri. Maksimal 3 fusi per run."),
               ("PEDAGANG", "Kedua sihir asal HILANG dan satu slot terbuka lagi. Resep lengkap kombo, evolusi, dan fusi ada di tiga BUKU. Beli di TOKO dengan Kristal, lalu baca di bagian bawah Almanak Skill."),
               ("PEDAGANG", "Sekarang SENTUH kartu FUSI SIHIR, lalu pilih sihir pertama dan kedua!")],
    "avatar": [("PEDAGANG", "Setiap penyihir punya SKILL AVATAR sendiri. Avatar yang kamu pakai adalah warisan penyihir pendahulu, dan skillnya aktif OTOMATIS."),
               ("PEDAGANG", "Lihat nama skill dan hitungan isi ulangnya di kiri layar. Avatar baru bisa dibeli di TOKO lobi dengan Kristal. Sekarang kalahkan 12 robot: Drone, Penembak, dan Perisai!")],
    "event": [("PEDAGANG", "Tanda MERAH berkedip di tepi layar artinya INSIDEN besar akan datang dari sisi itu dalam sekitar 2,5 detik. Segera geser ke ruang kosong atau sisi seberang!"),
              ("PEDAGANG", "Akan ada 3 gelombang: kepungan dari segala arah, tembok dari satu sisi, lalu kawanan drone. Gelombang seperti inilah yang memusnahkan desaku di Lembah Abu. Habisi semuanya!")],
    "miniboss": [("PEDAGANG", "Lihat, MINI BOSS buatanku: Kapten Baut RX-7! Kubuat mirip kapten pasukanku yang gugur, dan dia jauh lebih tangguh dari robot biasa."),
                 ("PEDAGANG", "Perhatikan tulisan AWAS dan dengarkan peringatannya sebelum tiap serangan. Hindari dulu, lalu balas. Panah MERAH menunjuk posisinya.")],
    "wave1": [("PEDAGANG", "Mulai sekarang aku tidak banyak membimbingmu lagi. Kamu sudah tahu dasarnya, dan latihan sejati adalah pertempuran. Bertahanlah dan habiskan semua gelombang!")],
    "wave2": [("PEDAGANG", "Gelombang berat. Robot-robot tua dari gudang rahasiaku: Zirah, Laser, Golem, dan lainnya. Mereka sisa pasukan menaraku. Jangan lengah!")],
    "mini2": [("PEDAGANG", "Satu mini boss lagi: Jenderal Gerigi MX-9, tangan kananku di menara dulu. Dia memulihkan robot lain, jadi jangan biarkan pertempuran berlarut-larut.")],
    "orb15": [("PEDAGANG", "Hampir selesai. Untuk membangunkan lawan terakhir, kamu harus cukup kuat: kumpulkan ORB sampai mencapai LEVEL 15!"),
              ("PEDAGANG", "Ikuti panah HIJAU ke orb besar, ambil satu per satu, dan pilih kartu upgrade tiap naik level. Aku akan menunggu di sini.")],
    "finalstart": [("PEDAGANG", "Level 15. Kamu sudah siap. Inilah GOLIATH-X, ciptaan terakhirku, wujud Raja Inflasi seperti yang pernah kulihat sendiri."),
                   ("PAHLAWAN", "Aku siap. Akan kutunjukkan semua yang kupelajari!")],
    "ending": [("PEDAGANG", "...Kamu berhasil. GOLIATH-X tumbang. Kupikir butuh bertahun-tahun untuk melihat penyihir sehebat ini."),
               ("PAHLAWAN", "Itu hanya robot, tapi aku belajar banyak. Terima kasih, Pak Pedagang."),
               ("PEDAGANG", "Ada yang belum kuceritakan. Aku membuat GOLIATH-X mirip Raja Inflasi, makhluk yang menelan menaraku dan seluruh emasku. Bertahun-tahun aku mencari penyihir yang sanggup mengalahkannya."),
               ("PAHLAWAN", "Jadi semua latihan ini... untuk menghadapi dia?"),
               ("PEDAGANG", "Benar. Aku akan terus berkeliling dan menunggumu tiap kelipatan 5 level, membawa ramuan, sihir, dan kabar terbaru. Setiap emas yang kau bawa kepadaku akan menjadi senjata."),
               ("PEDAGANG", "Terimalah Lencana ini sebagai tanda kelulusan. Pergilah, Penyihir Pemburu Monster. Sampai jumpa di medan perang sungguhan!"),
               ("PAHLAWAN", "Sampai jumpa, Guru. Aku akan menghentikan Raja Inflasi!")],
}
MENU_PAGES = ("title", "playmenu", "storymenu", "settings", "almanac", "almanac_detail", "badges", "toko", "quests")
_onoff = lambda v: "Hidup" if v > 0 else "Mati"
SETTING_ROWS = [
    ("sfx", "Volume Suara", [0.0, 0.35, 0.7, 1.0], lambda v: "%d%%" % int(v * 100)),
    ("music", "Volume Musik", [0.0, 0.25, 0.5, 0.8], lambda v: "%d%%" % int(v * 100)),
    ("shake", "Guncangan Layar", [0.0, 0.5, 1.0], lambda v: "Mati" if v <= 0 else "Setengah" if v < 1 else "Penuh"),
    ("dmgtext", "Angka Damage", [0.0, 1.0], _onoff),
    ("minimap", "Minimap", [0.0, 1.0], _onoff),
    ("lvlabel", "Label Level Musuh", [0.0, 1.0], _onoff),
    ("joystick", "Tampilan Joystick", [0.0, 1.0], _onoff),
    ("fps", "Batas FPS", [30.0, 45.0, 60.0], lambda v: "%d" % int(v)),
]
def _robot(name, base, color=None, **kw):
    d = dict(base)
    d.update(name=name, min_lv=0, robot=True, base_name=base.get("name", ""))
    if color:
        d["color"] = color
    d.update(kw)
    return d


ROBOTS = {
    "bolt": _robot("Robo-Bolt", ENEMY_TYPES[0], (230, 70, 70)),
    "pelari": _robot("Robo-Pelari", ENEMY_TYPES[2], (170, 90, 220)),
    "tank": _robot("Robo-Tank", ENEMY_TYPES[1], (80, 200, 120)),
    "gerinda": _robot("Robo-Gerinda", ENEMY_TYPES[3], (240, 150, 60)),
    "kilat": _robot("Robo-Kilat", ENEMY_TYPES[4], (90, 210, 220)),
    "hitam": _robot("Robo-Beton", ENEMY_TYPES[5], (60, 60, 70)),
    "drone": _robot("Robo-Drone", BAT_TYPE, (150, 100, 190)),
    "penerjang": _robot("Robo-Penerjang", DASHER_TYPE),
    "perisai": _robot("Robo-Perisai", SHIELD_TYPE),
    "penembak": _robot("Robo-Penembak", SHOOTER_TYPE),
    "laser": _robot("Robo-Laser", LASER_TYPE),
    "bom": _robot("Robo-Bom", BOMBER_TYPE),
    "granat": _robot("Robo-Granat", EXPLODER_TYPE),
    "jitu": _robot("Robo-Jitu", SNIPER_TYPE),
    "zirah": _robot("Robo-Zirah", ARMORED_TYPE),
    "pecah": _robot("Robo-Pecah", SPLIT_TYPE),
    "petir": _robot("Robo-Petir", THUNDER_TYPE),
    "racun": _robot("Robo-Racun", TOXIC_TYPE),
    "kedip": _robot("Robo-Kedip", TELEPORT_TYPE),
    "montir": _robot("Robo-Montir", ENEMY_TYPES[1], (120, 255, 170), healer=True, hp=60, xp=10, gold=6),
    "golem": _robot("Robo-Golem", GOLEM_TYPE),
    "raksasa": _robot("Robo-Raksasa", GIANT_TYPE),
}
ROBOT_STYLE_DEFAULT = {"body": "box", "legs": "legs", "eyes": "visor", "arms": "arms"}
ROBOT_STYLE = {
    "Robo-Bolt": {"body": "round", "legs": "wheel", "eyes": "cyclops", "arms": "none", "extra": "spring"},
    "Robo-Pelari": {"body": "tall", "legs": "legs", "eyes": "slit", "arms": "none"},
    "Robo-Tank": {"body": "wide", "legs": "tread", "eyes": "visor", "arms": "none", "extra": "tank"},
    "Robo-Gerinda": {"body": "round", "legs": "stomp", "eyes": "triple", "arms": "none", "extra": "saw"},
    "Robo-Kilat": {"body": "dome", "legs": "hover", "eyes": "cyclops", "arms": "none", "extra": "bolt"},
    "Robo-Beton": {"body": "box", "legs": "stomp", "eyes": "slit", "arms": "arms", "extra": "plates"},
    "Robo-Drone": {"body": "dome", "legs": "hover", "eyes": "cyclops", "arms": "none"},
    "Robo-Penerjang": {"body": "tri", "legs": "legs", "eyes": "slit", "arms": "none", "extra": "spikes"},
    "Robo-Perisai": {"body": "box", "legs": "legs", "eyes": "visor", "arms": "shieldarm"},
    "Robo-Penembak": {"body": "box", "legs": "legs", "eyes": "visor", "arms": "cannon"},
    "Robo-Laser": {"body": "tall", "legs": "hover", "eyes": "cyclops", "arms": "none", "extra": "dish", "led": (255, 60, 110)},
    "Robo-Bom": {"body": "round", "legs": "wheel", "eyes": "triple", "arms": "none", "extra": "bomb"},
    "Robo-Granat": {"body": "round", "legs": "legs", "eyes": "cyclops", "arms": "none", "extra": "fuse", "led": (255, 150, 60)},
    "Robo-Jitu": {"body": "tall", "legs": "legs", "eyes": "slit", "arms": "cannon", "led": (120, 255, 140)},
    "Robo-Zirah": {"body": "box", "legs": "legs", "eyes": "visor", "arms": "arms", "extra": "plates"},
    "Robo-Pecah": {"body": "dome", "legs": "spider", "eyes": "triple", "arms": "none", "led": (255, 150, 210)},
    "Robo-Petir": {"body": "tall", "legs": "hover", "eyes": "triple", "arms": "none", "extra": "bolt", "led": (255, 240, 110)},
    "Robo-Racun": {"body": "round", "legs": "wheel", "eyes": "visor", "arms": "none", "extra": "gas", "led": (150, 255, 80)},
    "Robo-Kedip": {"body": "dome", "legs": "hover", "eyes": "cyclops", "arms": "none", "led": (200, 255, 255)},
    "Robo-Montir": {"body": "box", "legs": "legs", "eyes": "visor", "arms": "arms", "extra": "cross", "led": (120, 255, 170)},
    "Robo-Golem": {"body": "wide", "legs": "stomp", "eyes": "slit", "arms": "claw", "extra": "plates"},
    "Robo-Raksasa": {"body": "wide", "legs": "stomp", "eyes": "visor", "arms": "claw"},
    "Kapten Baut RX-7": {"body": "box", "legs": "stomp", "eyes": "visor", "arms": "cannon", "extra": "plates"},
    "Jenderal Gerigi MX-9": {"body": "dome", "legs": "tread", "eyes": "triple", "arms": "claw", "extra": "gears", "led": (110, 255, 230)},
    "GOLIATH-X": {"body": "tall", "legs": "stomp", "eyes": "cyclops", "arms": "claw", "extra": "pods"},
}
MINI_BOSS_ROBOT = _robot("Kapten Baut RX-7", BOSS_TYPE, (200, 120, 40), radius=36, hp=1700, xp=60, gold=40,
                         robot_mini=True, robot_boss=True)
FINAL_BOSS_ROBOT = _robot("GOLIATH-X", BRUTE_BOSS_TYPE, (150, 60, 200), radius=54, hp=5200, xp=200, gold=150,
                          robot_final=True, robot_boss=True)
MINI_BOSS_ROBOT2 = _robot("Jenderal Gerigi MX-9", HEALER_BOSS_TYPE, (60, 190, 170), radius=42, hp=2600, xp=90, gold=70,
                          robot_mini=True, robot_boss=True)
ROBOT_LIST = list(ROBOTS.values()) + [MINI_BOSS_ROBOT, MINI_BOSS_ROBOT2, FINAL_BOSS_ROBOT]
_ROBOT_LORE = {
    "bolt": "Robot latihan paling dasar buatan Pedagang. Cepat dan rapuh.",
    "pelari": "Robot kurus yang berlari sangat kencang. Sulit dikejar, mudah dihancurkan.",
    "tank": "Robot bertubuh sedang, lambat tapi lumayan tebal.",
    "gerinda": "Robot besar berputar yang menggerinda lawan di jalurnya.",
    "kilat": "Robot mungil secepat kilat. Biasanya datang berkelompok.",
    "hitam": "Robot beton berat. Sering menjatuhkan bonus saat hancur.",
    "drone": "Drone terbang berbaling-baling. Menyerbu dalam kawanan.",
    "penerjang": "Robot yang membidik lalu menerjang lurus. Perhatikan garis merahnya!",
    "perisai": "Robot berperisai baja. Menahan sebagian besar damage dari depan.",
    "penembak": "Robot penembak jarak jauh. Hindari pelurunya sambil mendekat.",
    "laser": "Robot dengan meriam laser. Berhenti di kejauhan lalu menembak.",
    "bom": "Robot pelempar bom. Bom mendarat di tempatmu berdiri, jadi terus bergerak.",
    "granat": "Robot kamikaze: meledak saat dekat. Hancurkan dari jauh.",
    "jitu": "Robot penembak jitu. Peluru cepat dari jarak sangat jauh.",
    "zirah": "Robot berlapis zirah. Hancurkan lapisan baja dulu baru badannya.",
    "pecah": "Robot yang terpecah menjadi robot kecil saat hancur.",
    "petir": "Robot penyambar yang melepaskan petir ke sekitar.",
    "racun": "Robot pembocor gas beracun. Jangan berdiri di awannya.",
    "kedip": "Robot yang berpindah tempat sekejap. Muncul tiba-tiba di dekatmu.",
    "montir": "Robot montir. Memulihkan HP robot lain, jadi hancurkan lebih dulu.",
    "golem": "Robot golem baja raksasa. Menghentak tanah dengan keras.",
    "raksasa": "Robot raksasa bertenaga besar. Lambat, tapi sekali pukul sangat sakit.",
}
for _rk, _rv in ROBOTS.items():
    LORE[_rv["name"]] = _ROBOT_LORE[_rk] + " (Robot Simulasi - hanya ada di Tutorial)"
LORE[MINI_BOSS_ROBOT["name"]] = "Mini boss robot buatan Pedagang di LV7 Tutorial. Menerjang dan menyerang setelah tulisan AWAS. (Boss Simulasi)"
LORE[MINI_BOSS_ROBOT2["name"]] = "Mini boss robot kedua di LV14 Tutorial. Memulihkan robot lain dan menyerang dengan pola yang lebih rumit. (Boss Simulasi)"
LORE[FINAL_BOSS_ROBOT["name"]] = "Boss robot terakhir, ujian akhir Tutorial. Menghentak, melompat, dan meninju. Tangguh dan tidak cepat tumbang. (Boss Simulasi)"
BOSS_RANK_ROBOT = {MINI_BOSS_ROBOT["name"]: "Mini Boss Simulasi", MINI_BOSS_ROBOT2["name"]: "Mini Boss Simulasi II", FINAL_BOSS_ROBOT["name"]: "Boss Ujian Akhir"}

TUT_STEPS = [
    ("Bergerak", "Tujuan: berjalan sekitar 280 langkah. HP: sentuh layar lalu geser jari ke arah tujuan. Komputer: W atas, A kiri, S bawah, D kanan, atau tombol panah."),
    ("Serangan Otomatis", "Tujuan: kalahkan 10 robot (Robo-Bolt dan Robo-Kilat). Tidak perlu menekan tombol serang, sihir menembak otomatis. Ikuti panah KUNING ke robot."),
    ("Orb XP & Level", "Tujuan: ambil orb besar hingga naik level. Berjalanlah ke orb, ikuti panah HIJAU. Orb terisap otomatis saat dekat."),
    ("Pilih Upgrade", "Tujuan: pilih satu kartu upgrade dengan menyentuhnya (komputer: klik). Lalu bertahanlah dari robot."),
    ("HP & Bahaya", "Tujuan: bertahan sambil terus bergerak menjauhi Robo-Tank dan Robo-Penerjang. Pantau bar HP merah di kiri atas."),
    ("Peringatan Merah", "Tujuan: hindari lingkaran dan garis MERAH sebelum menyala. Geser ke luar area merah, damagenya nyata."),
    ("Pedagang & Perisai", "Tujuan: temui pedagang, ikuti panah EMAS ke tanda $, masuk kubah cahayanya, sentuh barang untuk membeli, lalu tutup toko."),
    ("Evolusi Skill", "Tujuan: sentuh salah satu kartu EVOLUSI. Sihir lama diganti sihir evolusi."),
    ("Kombo Skill", "Tujuan: sentuh kartu untuk mengevolusikan sihir yang satunya agar terbentuk KOMBO (+40% damage)."),
    ("Fusi Skill", "Tujuan: sentuh kartu FUSI SIHIR, lalu pilih dua sihir untuk dilebur jadi satu senjata fusi."),
    ("Skill Avatar", "Tujuan: kalahkan 12 robot (Drone, Penembak, Perisai). Skill avatar aktif otomatis, lihat hitungannya di kiri layar."),
    ("Insiden", "Tujuan: bertahan dari 3 gelombang insiden dan habisi semua robot. Peringatan MERAH di tepi layar menunjukkan arah serangan."),
    ("Mini Boss", "Tujuan: kalahkan Kapten Baut RX-7. Hindari serangan saat tulisan AWAS muncul. Ikuti panah MERAH."),
    ("Gelombang Robot", "Tujuan: bertahan dan kalahkan semua robot."),
    ("Gelombang Berat", "Tujuan: bertahan dan kalahkan semua robot."),
    ("Mini Boss II", "Tujuan: kalahkan Jenderal Gerigi MX-9."),
    ("Kumpulkan Orb", "Tujuan: kumpulkan orb sampai LEVEL 15. Ikuti panah HIJAU, pilih kartu upgrade tiap naik level."),
    ("Ujian Akhir", "Kalahkan boss robot terakhir."),
]


class Merchant:
    """Pedagang keliling: muncul tiap kelipatan 5 level. Punya PERISAI yang tidak bisa dilewati
    musuh/boss/peluru musuh. Setelah waktu habis dia PERGI, lalu bisa KEMBALI beberapa kali."""
    SHIELD_R = 150
    STAY_TIME = 55.0
    AWAY_TIME = (28.0, 36.0)
    MAX_VISITS = 3
    _shield_surf = None

    def __init__(self, x, y, level):
        self.x, self.y = x, y
        self.radius = max(12, int(26 * PLAYER_SCALE))
        self.cooldown = 0.0
        self.alive = True
        self.present = True
        self.visits = 1
        self.stay_left = self.STAY_TIME
        self.away_left = 0.0
        self.shield_anim = 0.0
        self.event = None
        self.skin = random.randrange(len(MERCHANT_SKINS))
        n_items = random.choices([4, 5, 6, 7, 8, 9, 10], weights=[1, 2, 3, 3, 3, 2, 1])[0]
        picks = random.sample(SHOP_CATALOG, n_items)
        self.stock = [{"key": k, "name": n, "desc": d, "price": shop_price(p, level), "sold": False}
                      for (k, n, d, p) in picks]

    @property
    def shield_active(self):
        return self.present and self.alive

    def update(self, dt, game=None):
        if not self.alive:
            return
        if self.cooldown > 0:
            self.cooldown -= dt
        if self.present:
            self.shield_anim = min(1.0, self.shield_anim + dt * 2.0)
            self.stay_left -= dt
            if self.stay_left <= 0:
                self.present = False
                self.shield_anim = 0.0
                if self.visits >= self.MAX_VISITS:
                    self.alive = False
                    self.event = "gone"
                else:
                    self.away_left = random.uniform(*self.AWAY_TIME)
                    self.event = "left"
        else:
            self.away_left -= dt
            if self.away_left <= 0 and game is not None:
                ang = random.uniform(0, math.tau)
                d = random.uniform(240, 330)
                self.x = game.badang.x + math.cos(ang) * d
                self.y = game.badang.y + math.sin(ang) * d
                self.present = True
                self.visits += 1
                self.stay_left = self.STAY_TIME
                self.shield_anim = 0.0
                self.event = "returned"

    @classmethod
    def shield_surface(cls):
        if cls._shield_surf is None:
            R = cls.SHIELD_R
            sf = pygame.Surface((R * 2 + 8, R * 2 + 8), pygame.SRCALPHA)
            pygame.draw.circle(sf, (110, 210, 255, 38), (R + 4, R + 4), R)
            pygame.draw.circle(sf, (170, 235, 255, 150), (R + 4, R + 4), R, 4)
            cls._shield_surf = sf
        return cls._shield_surf

    def draw(self, surf, cam_x, cam_y):
        if not self.present:
            return
        sx, sy = self.x - cam_x, self.y - cam_y
        R = self.SHIELD_R
        if not (-R - 80 <= sx <= WIDTH + R + 80 and -R - 120 <= sy <= HEIGHT + R + 80):
            return
        t = pygame.time.get_ticks() / 1000.0
        ix, iy = int(sx), int(sy)
        k = self.shield_anim
        if k >= 1.0:
            ss = self.shield_surface()
            surf.blit(ss, (ix - R - 4, iy - R - 4))
        else:
            pygame.draw.circle(surf, (170, 235, 255), (ix, iy), max(4, int(R * k)), 3)
        for i in range(12):
            a = t * 0.8 + i * math.tau / 12
            pygame.draw.circle(surf, (210, 245, 255), (int(sx + math.cos(a) * R), int(sy + math.sin(a) * R)), 3)
        frac = min(1.0, max(0.0, self.stay_left / self.STAY_TIME))
        arc_r = pygame.Rect(ix - R + 10, iy - R + 10, 2 * (R - 10), 2 * (R - 10))
        pygame.draw.arc(surf, GOLD_COLOR if frac > 0.25 else HP_RED, arc_r, math.pi / 2,
                        math.pi / 2 + math.tau * frac, 4)
        pygame.draw.circle(surf, GOLD_COLOR, (ix, iy), int(52 * PLAYER_SCALE) + int(2 * math.sin(t * 3)), 2)
        draw_merchant_char(surf, ix, iy, self.skin, t)
        coin_y = iy - int(64 * PLAYER_SCALE) + int(math.sin(t * 4) * 3)
        pygame.draw.circle(surf, GOLD_COLOR, (ix, coin_y), 8)
        pygame.draw.circle(surf, BLACK, (ix, coin_y), 8, 2)
        lab = font_small.render("Pedagang  N/A" if self.stay_left > 1e6 else "Pedagang  %ds" % max(0, int(self.stay_left)), True, GOLD_COLOR)
        surf.blit(lab, (ix - lab.get_width() / 2, iy + int(34 * PLAYER_SCALE)))

    def push_out(self, e):
        """Dorong musuh keluar dari perisai (musuh & boss tidak bisa lewat)."""
        dx, dy = e.x - self.x, e.y - self.y
        d2 = dx * dx + dy * dy
        lim = self.SHIELD_R + e.radius * 0.5
        if d2 < lim * lim:
            d = math.sqrt(d2) or 0.001
            if d2 == 0:
                dx, dy, d = 1.0, 0.0, 1.0
            e.x = self.x + dx / d * lim
            e.y = self.y + dy / d * lim
            return True
        return False


class ShopMenu:
    def __init__(self, game, merchant):
        self.game = game
        self.merchant = merchant
        self.rects = []
        x0 = WIDTH / 2 - 450
        n = len(merchant.stock)
        y0 = 138 + (5 - (n + 1) // 2) * 40
        for i in range(n):
            col, row = i % 2, i // 2
            x = WIDTH / 2 - 220 if (n % 2 == 1 and i == n - 1) else x0 + col * 460
            self.rects.append(pygame.Rect(x, y0 + row * 80, 440, 72))
        self.close_rect = pygame.Rect(WIDTH / 2 - 130, 566, 260, 52)

    def handle_click(self, pos):
        """True bila toko ditutup."""
        if self.close_rect.collidepoint(pos):
            sfx("click")
            return True
        g = self.game
        for r, item in zip(self.rects, self.merchant.stock):
            if r.collidepoint(pos):
                if item["sold"]:
                    return False
                if g.gold < item["price"]:
                    sfx("deny")
                    g.show_toast("Gold tidak cukup!")
                    return False
                if g.apply_shop_item(item["key"]):
                    g.gold -= item["price"]
                    item["sold"] = True
                    sfx("buy")
                else:
                    sfx("deny")
                return False
        return False

    _frame = None
    _fkey = None

    def _key(self):
        return (self.game.gold, tuple(it["sold"] for it in self.merchant.stock))

    def ready(self):
        return self._frame is not None and self._fkey == self._key()

    def draw(self, surf):
        key = self._key()
        if self._frame is not None and self._fkey == key:
            surf.blit(self._frame, (0, 0))
            return
        self._draw_now(surf)
        if self._frame is None:
            self._frame = surf.copy()
        else:
            self._frame.blit(surf, (0, 0))
        self._fkey = key

    def _draw_now(self, surf):
        overlay = veil_surface((0, 0, 0, 200))
        surf.blit(overlay, (0, 0))
        title = font_big.render("PEDAGANG KELILING", True, GOLD_COLOR)
        surf.blit(title, (WIDTH / 2 - title.get_width() / 2, 24))
        gold = font_med.render("Gold: %d" % self.game.gold, True, GOLD_COLOR)
        surf.blit(gold, (WIDTH / 2 - gold.get_width() / 2, 84))
        for r, item in zip(self.rects, self.merchant.stock):
            afford = self.game.gold >= item["price"]
            pygame.draw.rect(surf, PANEL_COLOR, r, border_radius=10)
            edge = GRAY if item["sold"] else (HP_GREEN if afford else HP_RED)
            pygame.draw.rect(surf, edge, r, width=2, border_radius=10)
            box = pygame.Rect(r.x + 8, r.y + 8, r.h - 16, r.h - 16)
            pygame.draw.rect(surf, (18, 16, 30), box, border_radius=8)
            pygame.draw.rect(surf, GRAY if item["sold"] else edge, box, 2, border_radius=8)
            old_clip = surf.get_clip()
            surf.set_clip(box.inflate(-4, -4))
            draw_item_icon(surf, item["key"], box.centerx, box.centery, box.w / 62.0)
            surf.set_clip(old_clip)
            if item["sold"]:
                pygame.draw.line(surf, HP_RED, box.inflate(-12, -12).topleft, box.inflate(-12, -12).bottomright, 4)
                pygame.draw.line(surf, HP_RED, box.inflate(-12, -12).bottomleft, box.inflate(-12, -12).topright, 4)
            name = font_med.render(item["name"], True, GRAY if item["sold"] else WHITE)
            desc = font_small.render(UpgradeMenu.fit_desc(item["desc"], r.width - 90 - 16), True, GRAY)
            surf.blit(name, (r.x + 76, r.y + 8))
            surf.blit(desc, (r.x + 76, r.y + 44))
            tag = "TERJUAL" if item["sold"] else "%d G" % item["price"]
            tt = font_med.render(tag, True, GRAY if item["sold"] else GOLD_COLOR)
            surf.blit(tt, (r.right - tt.get_width() - 16, r.y + 8))
        pygame.draw.rect(surf, PANEL_COLOR, self.close_rect, border_radius=10)
        pygame.draw.rect(surf, WHITE, self.close_rect, width=2, border_radius=10)
        ct = font_med.render("TUTUP", True, WHITE)
        surf.blit(ct, (self.close_rect.centerx - ct.get_width() / 2, self.close_rect.centery - ct.get_height() / 2))


def _resolve_save_path():
    try:
        base = os.path.dirname(os.path.abspath(__file__))
    except Exception:
        base = os.getcwd()
    return os.path.join(base, "witch_survivor_save.json")


SAVE_PATH = _resolve_save_path()


class SaveData:
    """Penyimpanan permanen (JSON): top skor, statistik, pengaturan suara,
    avatar terakhir dipilih, dan progres permainan (untuk Lanjutkan)."""

    def __init__(self):
        self.data = {
            "version": 10,
            "crystals": STARTER_CRYSTALS,
            "owned_avatars": ["badang"],
            "selected_avatar": "badang",
            "settings": dict(SETTINGS),
            "top_scores": [],
            "stats": {"runs": 0, "kills": 0, "bosses": 0, "best_level": 1, "best_time": 0},
            "last_level_times": {},
            "almanac": {"kills": {}, "skills": []},
            "owned_skills": list(STARTER_SKILLS),
            "books": [],
            "badges": [],
            "badge_pending": [],
            "quests": {},
            "chests": {},
            "gacha_bad": 0,
            "run": None,
        }
        self.load()

    def load(self):
        try:
            with open(SAVE_PATH, "r", encoding="utf-8") as f:
                raw = json.load(f)
            if isinstance(raw, dict):
                for k, v in raw.items():
                    if k in self.data:
                        if isinstance(self.data[k], dict) and isinstance(v, dict):
                            self.data[k].update(v)
                        else:
                            self.data[k] = v
        except Exception:
            pass
        kills_ = self.data.get("almanac", {}).get("kills", {})
        for old_, new_ in (("Kubus Denyut", "Kubus Pengawal"), ("Sang Pemintal Laser", "Pemintal Laser"), ("Mata Nirwana", "Mata Pengintai"),
                           ("Raja Ritme", "Penabuh Ritme"), ("Kiamat Piksel", "Prajurit Piksel")):
            if old_ in kills_:
                kills_[new_] = kills_.get(new_, 0) + kills_.pop(old_)
        os_ = self.data.get("owned_skills")
        if not isinstance(os_, list):
            self.data["owned_skills"] = list(STARTER_SKILLS)
        bk_ = self.data.get("books")
        if not isinstance(self.data.get("badge_pending"), list):
            self.data["badge_pending"] = []
        self.data["books"] = [k for k in bk_ if k in ("combo", "evo", "fusion")] if isinstance(bk_, list) else []
        owned = self.data.get("owned_avatars")
        if not isinstance(owned, list) or "badang" not in owned:
            self.data["owned_avatars"] = ["badang"] + [k for k in (owned if isinstance(owned, list) else []) if k != "badang"]
        if not isinstance(self.data.get("crystals"), int):
            self.data["crystals"] = STARTER_CRYSTALS

    def save(self):
        try:
            tmp = SAVE_PATH + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.data, f)
            os.replace(tmp, SAVE_PATH)
        except Exception:
            pass

    def add_score(self, entry):
        scores = self.data["top_scores"]
        scores.append(entry)
        scores.sort(key=lambda s: s.get("score", 0), reverse=True)
        del scores[10:]
        for i, s in enumerate(scores):
            if s is entry:
                return i + 1
        return None

    @property
    def best_score(self):
        s = self.data["top_scores"]
        return s[0]["score"] if s else 0


# ---------------- QUEST HARIAN & MINGGUAN ----------------
# stat "sum" = dijumlahkan dari semua run; stat "max" = nilai terbaik dalam SATU run.
QUEST_STAT_KIND = {"kills": "sum", "bosses": "sum", "runs": "sum", "infl_runs": "sum", "wins": "sum",
                   "level": "max", "minutes": "max", "infl_level": "max"}
QUEST_DAILY_POOL = [
    ("d_kills1", "Kalahkan 250 musuh", "kills", 250, 80), ("d_kills2", "Kalahkan 500 musuh", "kills", 500, 150),
    ("d_boss", "Kalahkan 3 boss", "bosses", 3, 110), ("d_runs", "Mainkan 2 permainan", "runs", 2, 70),
    ("d_level", "Capai Level 20 dalam satu permainan", "level", 20, 90), ("d_time", "Bertahan 10 menit dalam satu permainan", "minutes", 10, 100),
    ("d_infl", "Mainkan Mode Inflasi 1 kali", "infl_runs", 1, 110), ("d_level2", "Capai Level 35 dalam satu permainan", "level", 35, 160),
]
QUEST_WEEKLY_POOL = [
    ("w_kills", "Kalahkan 3000 musuh", "kills", 3000, 650), ("w_boss", "Kalahkan 20 boss", "bosses", 20, 550),
    ("w_runs", "Mainkan 12 permainan", "runs", 12, 450), ("w_infl", "Mainkan Mode Inflasi 6 kali", "infl_runs", 6, 600),
    ("w_win", "Kalahkan Raja Inflasi 1 kali", "wins", 1, 1000), ("w_level", "Capai Level 50 di Mode Inflasi", "infl_level", 50, 750),
    ("w_time", "Bertahan 25 menit dalam satu permainan", "minutes", 25, 550),
]
QUEST_BY_ID = {q[0]: q for q in QUEST_DAILY_POOL + QUEST_WEEKLY_POOL}


QUEST_CHEST_CHANCE = (0.10, 0.03, 0.008)   # peluang peti Kayu / Perak / Emas per quest


def quest_chest_tier(rw):
    """Hadiah peti skill menurut tingkat kesulitan (besar hadiah Kristal): Kayu < Perak < Emas."""
    return 0 if rw < 140 else (1 if rw < 500 else 2)


def _quest_keys():
    import datetime
    d = datetime.date.today()
    y, w, _ = d.isocalendar()
    return d.isoformat(), "%d-W%02d" % (y, w)


def _quest_pick(pool, seed, n):
    rnd = random.Random(seed)
    order = list(pool)
    rnd.shuffle(order)
    out, used = [], set()
    for q in order:
        if q[2] in used:
            continue
        used.add(q[2])
        out.append({"id": q[0], "p": 0, "claimed": False})
        if len(out) >= n:
            break
    return out


def quest_refresh(data):
    """Buat/segarkan quest bila hari atau minggu sudah berganti."""
    day, week = _quest_keys()
    q = data.get("quests")
    if not isinstance(q, dict):
        q = data["quests"] = {}
    if q.get("day") != day or not isinstance(q.get("daily"), list):
        q["day"] = day
        q["daily"] = _quest_pick(QUEST_DAILY_POOL, "daily-" + day, 3)
    if q.get("week") != week or not isinstance(q.get("weekly"), list):
        q["week"] = week
        q["weekly"] = _quest_pick(QUEST_WEEKLY_POOL, "weekly-" + week, 3)
    q["daily"] = [e for e in q["daily"] if e.get("id") in QUEST_BY_ID]
    q["weekly"] = [e for e in q["weekly"] if e.get("id") in QUEST_BY_ID]
    return q


def quest_add_run(data, stats):
    q = quest_refresh(data)
    for e in q["daily"] + q["weekly"]:
        _id, _txt, stat, target, _rw = QUEST_BY_ID[e["id"]]
        v = stats.get(stat, 0)
        if QUEST_STAT_KIND[stat] == "sum":
            e["p"] = min(target, e["p"] + v)
        else:
            e["p"] = min(target, max(e["p"], v))


def quest_claimable(data):
    q = quest_refresh(data)
    return sum(1 for e in q["daily"] + q["weekly"] if not e["claimed"] and e["p"] >= QUEST_BY_ID[e["id"]][3])


BOOKS = [
    ("combo", "Buku Kombo", 1200, (110, 190, 255), "Daftar semua KOMBO: dua sihir yang sama-sama berevolusi menyatu dan menambah +40% damage."),
    ("evo", "Buku Evolusi", 2100, (255, 200, 90), "Membuka EVOLUSI skill: semua skill langsung berbentuk evolusi sejak Lv.1 dan upgrade Lv.1-7 menjadi upgrade evolusi. Tanpa buku skill tidak bisa berevolusi."),
    ("fusion", "Buku Fusi", 3000, (215, 130, 255), "Daftar resep FUSI: dua sihir dilebur jadi satu senjata fusi baru. Juga menampilkan hasil fusi di kartu level up."),
]


def book_count(key):
    return {"combo": len(COMBO_DEFS), "evo": len(WEAPON_CLASSES), "fusion": len(_FR)}.get(key, 0)


def draw_book_icon(surf, cx, cy, sc, col, key="combo"):
    S = lambda v: int(v * sc)
    x, y = int(cx), int(cy)
    pygame.draw.rect(surf, _dk(col, 0.45), (x - S(32), y - S(40), S(64), S(80)), border_radius=S(6))
    pygame.draw.rect(surf, col, (x - S(27), y - S(36), S(56), S(72)), border_radius=S(5))
    pygame.draw.rect(surf, _dk(col, 0.6), (x - S(32), y - S(40), S(12), S(80)), border_radius=S(5))
    pygame.draw.rect(surf, (245, 240, 225), (x + S(26), y - S(33), S(6), S(66)))
    pygame.draw.rect(surf, _dk(col, 0.45), (x - S(32), y - S(40), S(64), S(80)), 2, border_radius=S(6))
    ex, ey = x + S(4), y - S(6)
    if key == "fusion":
        draw_fusion_icon(surf, ex, ey, sc * 0.62, (225, 150, 255), "merge")
    elif key == "evo":
        pygame.draw.polygon(surf, GOLD_COLOR, [(ex, ey - S(20)), (ex + S(15), ey), (ex + S(6), ey), (ex + S(6), ey + S(16)), (ex - S(6), ey + S(16)), (ex - S(6), ey), (ex - S(15), ey)])
        pygame.draw.polygon(surf, BLACK, [(ex, ey - S(20)), (ex + S(15), ey), (ex + S(6), ey), (ex + S(6), ey + S(16)), (ex - S(6), ey + S(16)), (ex - S(6), ey), (ex - S(15), ey)], 2)
    else:
        pygame.draw.circle(surf, WHITE, (ex - S(8), ey), S(11), 3)
        pygame.draw.circle(surf, GOLD_COLOR, (ex + S(8), ey), S(11), 3)
    for k in range(3):
        pygame.draw.line(surf, _lt(col, 0.5), (x - S(10), y + S(20) + k * S(5)), (x + S(18), y + S(20) + k * S(5)), 2)


def draw_arrow(surf, x1, y, x2, col=(210, 210, 225)):
    pygame.draw.line(surf, col, (x1, y), (x2 - 5, y), 3)
    pygame.draw.polygon(surf, col, [(x2, y), (x2 - 9, y - 6), (x2 - 9, y + 6)])


_END_CACHE = {}


def end_vignette(col, strength=170):
    """Vinyet tepi layar: dibuat SEKALI per warna (hemat lag)."""
    k = (tuple(col), strength)
    sf = _END_CACHE.get(k)
    if sf is None:
        sf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        steps = 30
        for i in range(steps):
            a = int(strength * (1 - i / steps) ** 2)
            pygame.draw.rect(sf, (col[0], col[1], col[2], a), (i * 6, i * 6, WIDTH - i * 12, HEIGHT - i * 12), 6)
        _END_CACHE[k] = sf
    return sf


def draw_end_frame(surf, main, light, dark, t):
    """Bingkai layar penuh: pita gelap + pita warna + siku sudut + paku. Garis dalam berdenyut."""
    W, H = WIDTH, HEIGHT
    pulse = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(t * 2.4))
    glow = tuple(int(dark[i] + (light[i] - dark[i]) * pulse) for i in range(3))
    pygame.draw.rect(surf, dark, (0, 0, W, H), 12)
    pygame.draw.rect(surf, main, (12, 12, W - 24, H - 24), 6)
    for (cx, cy, sx, sy) in ((0, 0, 1, 1), (W, 0, -1, 1), (0, H, 1, -1), (W, H, -1, -1)):
        x, y = cx + sx * 34, cy + sy * 34
        pygame.draw.line(surf, glow, (x, y), (x + sx * 280, y), 4)
        pygame.draw.line(surf, glow, (x, y), (x, y + sy * 200), 4)
        pts = [(x, y - 20), (x + 20, y), (x, y + 20), (x - 20, y)]
        pygame.draw.polygon(surf, light, pts)
        pygame.draw.polygon(surf, dark, pts, 3)
        pygame.draw.circle(surf, WHITE, (x, y), 4)
    for x in range(130, W - 110, 90):
        for yy in (15, H - 15):
            if yy > H / 2 and 440 < x < 860:
                continue
            pygame.draw.polygon(surf, light, [(x, yy - 6), (x + 6, yy), (x, yy + 6), (x - 6, yy)])
    for y in range(130, H - 110, 90):
        for xx in (15, W - 15):
            pygame.draw.polygon(surf, light, [(xx, y - 6), (xx + 6, y), (xx, y + 6), (xx - 6, y)])


def draw_end_panel(surf, rect, fill, main, light):
    pygame.draw.rect(surf, (0, 0, 0), rect.move(6, 8), border_radius=18)
    pygame.draw.rect(surf, fill, rect, border_radius=18)
    pygame.draw.rect(surf, main, rect, 5, border_radius=18)
    pygame.draw.rect(surf, light, rect.inflate(-20, -20), 2, border_radius=14)


def end_shadow_text(surf, font, text, col, cx, y, sh=(0, 0, 0), off=3):
    a = font.render(text, True, sh)
    b = font.render(text, True, col)
    surf.blit(a, (cx - a.get_width() / 2 + off, y + off))
    surf.blit(b, (cx - b.get_width() / 2, y))


def draw_fallen_hat(surf, cx, cy):
    """Topi penyihir patah (layar kalah)."""
    pygame.draw.ellipse(surf, (50, 28, 80), (cx - 46, cy + 12, 92, 20))
    pygame.draw.polygon(surf, (88, 52, 135), [(cx - 30, cy + 20), (cx + 30, cy + 20), (cx + 10, cy - 20), (cx - 10, cy - 20)])
    pygame.draw.polygon(surf, (88, 52, 135), [(cx - 10, cy - 20), (cx + 10, cy - 20), (cx + 42, cy - 12)])
    pygame.draw.polygon(surf, (28, 14, 48), [(cx - 30, cy + 20), (cx + 30, cy + 20), (cx + 10, cy - 20), (cx - 10, cy - 20)], 3)
    pygame.draw.rect(surf, (200, 40, 55), (cx - 28, cy + 6, 56, 9))
    pygame.draw.lines(surf, (255, 235, 235), False, [(cx - 4, cy - 18), (cx + 2, cy - 6), (cx - 5, cy + 2), (cx + 3, cy + 14)], 3)
    _icon_star(surf, cx + 56, cy + 22, 11, 5, (255, 200, 80), (120, 70, 10))


def draw_leaf(surf, x, y, ang, L, Wd, col, edge):
    tx, ty = math.cos(ang), math.sin(ang)
    nx, ny = -ty, tx
    pts = [(x - tx * L / 2, y - ty * L / 2), (x + nx * Wd / 2, y + ny * Wd / 2), (x + tx * L / 2, y + ty * L / 2), (x - nx * Wd / 2, y - ny * Wd / 2)]
    pygame.draw.polygon(surf, col, pts)
    pygame.draw.polygon(surf, edge, pts, 1)


def draw_laurel_medal(surf, cx, cy, t):
    """Medali bintang emas dikelilingi karangan daun (layar menang)."""
    for side in (-1, 1):
        for i in range(9):
            phi = math.radians(22 + i * 17)
            for rr, col in ((62, (60, 175, 90)), (50, (36, 130, 66))):
                if rr == 50 and i % 2:
                    continue
                x, y = cx + side * math.sin(phi) * rr, cy - math.cos(phi) * rr
                draw_leaf(surf, x, y, math.atan2(math.sin(phi), side * math.cos(phi)), 20, 9, col, (20, 80, 40))
    pygame.draw.circle(surf, (150, 100, 10), (cx, cy), 36)
    pygame.draw.circle(surf, GOLD_COLOR, (cx, cy), 33)
    _icon_star(surf, cx, cy, 28, 12, (255, 245, 170), (150, 100, 10))
    k = 0.5 + 0.5 * math.sin(t * 3)
    pygame.draw.circle(surf, WHITE, (cx - 14, cy - 16), int(3 + 2 * k))


FREEZE_STATES = ("paused", "levelup", "shop", "gameover", "victory")


# ================= ALMANAK: cerita & detail lengkap =================
ENEMY_STORY = {
"Merah": "Merah adalah korban pertama Retakan di Lembah Abu. Dulu mereka para petani yang menggarap ladang di kaki menara, sampai kabut merah menyelimuti desa dan mengubah semua orang menjadi prajurit tanpa pikiran. Karena jumlahnya tak terhitung, para penyihir tua menamai mereka Pasukan Angka: satu mati, seratus lagi datang.",
"Hijau": "Hijau dulunya penjaga ladang gandum yang paling dihormati desa. Ketika kabut sihir turun, kulitnya berubah hijau lumut dan ia lupa siapa yang dulu dilindunginya. Kadang ia berhenti sejenak di tengah serbuan, seolah mencari ladang yang sudah lama hilang.",
"Ungu": "Ungu lahir dari tetesan ramuan gagal di laboratorium menara. Ramuan itu seharusnya membuat penyihir cepat berlari, tapi hasilnya hanya makhluk kecil yang tak bisa diam. Ia menyerbu karena hanya itu satu-satunya hal yang ia tahu cara melakukannya.",
"Oranye": "Oranye adalah prajurit garis depan pertama yang dikirim Raja Inflasi ke Lembah Abu. Tubuhnya digembungkan sihir angka sampai kebal pukulan ringan, tetapi pikirannya ikut menyempit hingga hanya mengenal satu perintah: maju. Para penjaga menara menjulukinya Si Tembok Berjalan.",
"Cyan": "Cyan dikatakan berasal dari embun beku di dasar Retakan. Ia nyaris tak bersuara, sehingga banyak penyihir baru baru menyadarinya setelah terlambat. Para tabib menyarankan satu hal: jangan pernah berdiri membelakangi bayangan yang bergerak.",
"Hitam": "Hitam adalah prajurit yang tertimbun terlalu lama di bawah abu Lembah. Abu itu memadat menjadi lapisan hitam yang membuat badannya berat dan lamban. Setiap langkahnya meninggalkan getaran yang terasa sampai ke menara.",
"Pecah": "Pecah dibuat dari kristal sihir retak yang tidak mau hancur seluruhnya. Tiap kali dipukul, pecahannya hidup sendiri dan terus menyerang. Penyihir kuno menyebutnya bukti bahwa sihir yang terpotong tidak pernah benar-benar padam.",
"Zirah": "Zirah adalah sisa ksatria kerajaan yang gugur mempertahankan gerbang Lembah. Baju besinya masih melekat dan masih berjalan, meski penghuninya sudah lama lenyap. Ia tidak membenci pemain; ia hanya menjalankan sumpah penjagaan terakhir yang tak pernah dicabut.",
"Necromancer": "Necromancer kecil ini murid yang menyalahgunakan buku sihir tulang milik gurunya. Ia mengira bisa mengendalikan arwah, tapi arwah itulah yang kini mengendalikannya. Setiap tengkorak yang ia bangkitkan adalah teman yang ia cari di tengah kesendirian.",
"Penembak": "Penembak dulu pemburu hutan yang ahli membidik rusa. Sihir Retakan menajamkan matanya tapi menumpulkan hatinya, sehingga ia menembak apa pun yang bergerak di kejauhan. Pelurunya lambat, namun ia punya kesabaran yang tak ada habisnya.",
"Peledak": "Peledak adalah prajurit yang dijejali bubuk sihir sampai tubuhnya tak sanggup lagi menampung. Ia dikirim tanpa rencana pulang, karena Raja Inflasi menghitung satu nyawa sebagai satu ledakan. Dalam ledakan terakhirnya konon terdengar tawa kecil yang aneh.",
"Raksasa": "Raksasa lahir dari prajurit biasa yang digelembungkan oleh sihir inflasi hingga berkali-kali lipat. Semakin besar tubuhnya, semakin kecil ingatannya tentang siapa dirinya dulu. Warga desa mengenal kedatangannya dari getaran gelas di meja.",
"Kelelawar": "Kelelawar bersarang di gua di bawah menara dan terbang keluar saat Retakan pertama kali terbuka. Sayapnya setajam pisau cukur dan mereka selalu bergerak berkelompok agar tak sempat dikejar satu per satu. Pedagang Keliling pernah berkata, kalau kau mendengar kepakan, sudah ada lusinan di sekelilingmu.",
"Penerjang": "Penerjang dulunya pelari pesan kerajaan yang tak pernah terlambat. Retakan mengubah semangat itu menjadi dorongan menabrak apa saja dengan kecepatan penuh. Garis merah di depannya adalah satu-satunya kebaikan yang tersisa: ia selalu memberi peringatan.",
"Prajurit Perisai": "Prajurit Perisai adalah penjaga barisan depan yang bersumpah tak akan mundur selangkah. Perisainya ditempa dari pintu gerbang menara yang runtuh, dan ia menolak melepasnya meski sudah tak punya apa-apa lagi untuk dilindungi. Serang ia dari belakang, kata para pendahulumu, dan jangan merasa bersalah.",
"Hantu Kedip": "Hantu Kedip adalah roh penyihir yang mati saat berlatih sihir teleportasi. Mantranya tak pernah selesai, jadi ia terus berpindah tempat tanpa tujuan. Tak ada yang tahu apakah ia sedang menyerang atau hanya mencari jalan pulang.",
"Penembak Laser": "Penembak Laser adalah mesin sihir dari bengkel menara yang tak sengaja ikut terbangun saat Retakan terbuka. Lensa di dadanya butuh waktu mengisi, dan keheningan sesaat sebelum tembakan adalah satu-satunya tanda. Para pengrajin dulu menggunakannya untuk memotong batu; sekarang ia memotong yang lain.",
"Ninja Bayangan": "Ninja Bayangan dulu anggota perkumpulan mata-mata yang mengabdi pada kerajaan lama. Ketika kerajaan jatuh, mereka tidak bubar; mereka hanya berganti majikan menjadi siapa pun yang membayar dengan angka. Shuriken mereka senyap, tapi aroma tinta di kain hitamnya sering membongkar persembunyian.",
"Pelempar Bom": "Pelempar Bom adalah ahli peledak tambang yang kehilangan akal. Ia mengisi kantongnya dengan bom hitam dan melemparnya dengan kegembiraan seorang anak bermain bola. Lingkaran merah di tanah adalah sisa kebiasaan lamanya menandai area aman.",
"Penembak Jitu": "Penembak Jitu menunggu berjam-jam di atas menara untuk satu tembakan sempurna. Ia tak peduli pada pertempuran, hanya pada satu bidikan yang tepat. Konon ia pernah menunggu seminggu demi sebutir kelereng.",
"Dukun Semangat": "Dukun Semangat adalah tabib desa yang dulu menyalakan harapan warga lewat tabuhan dan nyanyian. Sihir Retakan memelintir lagunya menjadi seruan perang. Kini setiap pukulan genderangnya membuat kawan-kawannya berlari lebih cepat.",
"Racun Berjalan": "Racun Berjalan adalah pengolah ramuan yang tercebur ke kolam bisa di dasar menara. Tubuhnya sekarang terlalu beracun untuk ditinggali orang lain, bahkan oleh bayangannya sendiri. Jejak hijau di belakangnya adalah satu-satunya tempat yang tidak ingin kau pijak.",
"Golem Baja": "Golem Baja dipahat penyihir tua untuk menjaga gudang emas kerajaan. Ketika Raja Inflasi menelan emas dunia, golem ini ikut terbangun dengan amarah karena tugasnya gagal. Ia tidak bisa tidur lagi sampai ada yang menggantikan penjagaannya, atau menghancurkannya.",
"Raksasa Cepat": "Raksasa Cepat adalah raksasa yang menolak tubuh lambatnya dan memaksa sihir inflasi mengubah otot kakinya. Hasilnya lari yang mengguncang tanah seperti derap kuda perang. Para pengungsi menyebutnya Badai Tanpa Awan.",
"Penyambar Petir": "Penyambar Petir adalah penyihir cuaca yang terlalu dekat dengan badai pertama setelah Retakan terbuka. Petir menyambarnya berulang kali tanpa membunuhnya, lalu belajar mematuhinya. Sekarang ia memanggil petir untuk mempercepat kawan, bukan lagi untuk dirinya.",
"Raksasa Super": "Raksasa Super adalah hasil percobaan penyihir kerajaan yang ingin mengetahui seberapa besar tubuh bisa digelembungkan sebelum pecah. Jawabannya: lebih besar dari yang dikira siapa pun. Ia tidak pecah, hanya melupakan namanya sendiri.",
"Tengkorak Raksasa Cepat": "Tengkorak Raksasa Cepat adalah rangka raksasa yang kehilangan dagingnya tapi tidak kehilangan dendamnya. Tanpa otot yang membuatnya berat, ia bisa berlari tanpa lelah dan tanpa rasa sakit. Hanya bunyi tulang beradu yang mendahului kedatangannya.",
"Raksasa Pecah": "Raksasa Pecah dulunya raksasa biasa yang kena kutukan Kristal Pecah. Ketika ia mati, kristal itu membelah tubuhnya menjadi raksasa sedang, lalu menjadi pecahan kecil. Penyihir kuno bilang ini bukti kutukan angka: pembagian yang tak pernah habis.",
"Tanker Raksasa": "Tanker Raksasa adalah raksasa yang ditanam kantong gas beracun ke dalam zirahnya oleh pasukan Raja Inflasi. Ia dirancang untuk menjadi benteng bergerak, lalu menjadi bom saat tumbang. Ledakan terakhirnya adalah lelucon pahit dari majikannya.",
"Tank Raksasa Cepat": "Tank Raksasa Cepat dirakit dari zirah yang seharusnya dipakai raksasa lamban. Tukang besi Raja Inflasi menambahkan roda sihir di telapak kakinya agar zirah tebal itu bisa melaju. Ia melintasi medan seperti pintu benteng yang lepas dari engselnya.",
"Warden": "Warden adalah penjaga makam terdalam yang matanya dibutakan sendiri agar tak tergoda harta. Ia mendengar detak jantung dan langkah kaki dari jauh, lalu menjawabnya dengan dentuman sonik. Berdiri diam bukan perlindungan; ia mendengar napasmu.",
"Peniru Sihir": "Peniru Sihir adalah ilusi yang diciptakan penyihir iseng untuk menggoda murid. Ia tak punya jurus sendiri dan hanya meminjam apa yang dilihatnya dari pemain. Karena itu, makin kuat sihirmu, makin berbahaya cerminnya.",
"Tank Besi": "Tank Besi adalah kendaraan perang ringan yang dirakit para tukang besi menara saat Retakan baru terbuka. Tak ada awak di dalamnya, hanya sihir yang menggerakkan rodanya. Ia lambat, tetapi besinya menyimpan dendam dari setiap pengrajin yang gugur.",
"Raksasa Hantu": "Raksasa Hantu adalah arwah raksasa yang menolak pergi setelah tubuhnya dihancurkan. Ia menembus dinding dan senjata sesukanya, menjadi nyata hanya ketika ingin memukul. Kadang ia terlihat menangis di tengah medan, tanpa suara.",
"Algojo Raksasa": "Algojo Raksasa adalah penegak hukuman kerajaan yang tak pernah salah memilih sasaran. Palunya diwarisi dari tujuh generasi algojo, dan setiap hantaman meninggalkan lingkaran peringatan kematian. Ia tak pernah menanyakan alasan, hanya menjatuhkan hukuman.",
"Raksasa Perisai": "Raksasa Perisai bersumpah melindungi pasukan di belakangnya dengan perisai selebar pintu. Selama perisainya utuh ia tak akan roboh, dan selama ia berdiri kawan di sekitarnya merasa aman. Itulah sebabnya para penyihir selalu memecahkan perisainya lebih dulu.",
"Ksatria Raksasa": "Ksatria Raksasa dulu pemimpin pasukan kerajaan yang tubuhnya dibesarkan sihir demi memukul mundur Retakan. Sihir itu memang berhasil, tapi ia tak pernah kembali menjadi manusia. Pedang lebarnya masih diasah tiap fajar oleh tangan yang tak lagi mengingat alasannya.",
"Golem Es": "Golem Es dibentuk dari es abadi di gletser utara untuk menjaga sebuah kuil yang kini tak ada lagi. Dinginnya tak pernah mencair karena ia tak punya hati yang bisa dihangatkan. Penyihir api sering gagal menghancurkannya karena tidak sadar ia kebal pembekuan.",
"Raksasa Induk": "Raksasa Induk adalah raksasa betina yang dulu dikenal sebagai pelindung para yatim di Lembah Abu. Sihir Retakan mengubah naluri itu menjadi kemampuan melahirkan pasukan baru tiap kali ia terluka. Anak-anaknya selalu datang bertiga, dan selalu tak mau berpisah darinya.",
"Penyihir Kristal": "Penyihir Kristal menggunakan batu permata sihir untuk menguatkan sekutunya. Ia percaya sedang menolong, padahal tiap buff yang ia lemparkan memperpanjang penderitaan mereka. Kristal di tongkatnya adalah serpihan pertama Retakan yang pernah ditemukan.",
"Tanker Kepala Dua": "Tanker Kepala Dua adalah eksperimen yang menyatukan dua prajurit tank dalam satu tubuh. Keduanya tak pernah sepakat, tapi sama-sama keras kepala untuk tidak mati. Saat satu kepala jatuh, kepala lain mengamuk karena kehilangan lawan berdebat.",
"Raksasa Shotgun": "Raksasa Shotgun dulu pemburu beruang yang tubuhnya dibesarkan hingga senapan lamanya terlihat seperti mainan. Ia menggantinya dengan senapan hasil pesanan khusus yang menyemburkan sembilan peluru sekaligus. Jangan berdiri di depan laras; berdirilah di sisinya.",
"Ketua Raksasa": "Ketua Raksasa adalah mandor pasukan raksasa yang suaranya mampu menggoyang atap. Satu teriakannya cukup membuat prajurit lemah ikut berlari dengan tenaga baru. Ia tidak pernah ikut bertarung dulu; ia mengomando sampai yang lain kelelahan.",
"Raksasa Minigun": "Raksasa Minigun ditugaskan menghentikan pelarian penduduk dari Lembah Abu. Senjata putarnya dirancang untuk ditembakkan sepuluh orang sekaligus, tapi tangannya cukup besar untuk memegangnya sendiri. Bunyi putaran laras yang mulai memanas adalah tanda untuk segera lari.",
"Raksasa Reaper": "Raksasa Reaper adalah penjemput arwah yang tersesat dari alam baka. Sabitnya tak melukai tubuh melainkan memanggil kendaraan perang dari sisi lain. Banyak yang mengira ia pemimpin, padahal ia hanya kurir yang membawa kiriman tank.",
}

ENEMY_STORY.update({
"Serigala Es": "Serigala Es turun dari gletser utara mengikuti hawa dingin yang bocor dari Retakan. Mereka berburu berkelompok dan meninggalkan jejak beku yang memperlambat siapa pun yang mengejar. Penduduk percaya satu lolongan mereka cukup untuk membekukan embun di jendela.",
"Penyihir Es": "Penyihir Es adalah murid akademi utara yang terjebak badai salju saat Retakan membuka. Es meresap ke tubuhnya sampai ia kebal dingin dan lupa rasa hangat. Duri es yang ia lontarkan adalah mantra pertama yang ia pelajari dulu.",
"Pembeku": "Pembeku dulu penjaga sumur yang bertugas memastikan air desa tidak membeku di musim dingin. Ketika sihir dingin menguasainya, tugasnya terbalik: kini ia membekukan apa pun yang mendekat. Gelombang dingin darinya terasa seperti napas terakhir musim dingin.",
"Raksasa Salju": "Raksasa Salju tertidur ratusan tahun di bawah longsoran salju sebelum Retakan membangunkannya. Ia melempar bola salju sebesar rumah dan menebar kabut dingin tiap kali melangkah. Para pendaki menganggapnya legenda, sampai mereka bertemu.",
"Imp Api": "Imp Api adalah iblis kecil yang lolos dari dapur neraka saat Retakan terbuka. Ia suka berlari sambil meninggalkan jejak api, bukan karena jahat, tetapi karena menurutnya itu permainan. Pedagang Keliling bersumpah ia pernah melihat satu imp menertawakan lilin yang padam.",
"Penyembur Api": "Penyembur Api dulu juru masak istana yang terlalu dekat dengan tungku sihir. Sihir kompor itu kini ada di tenggorokannya dan menyembur dalam kipas pendek yang berbahaya. Ia masih sering terlihat mengaduk udara kosong, seperti sedang memasak sup.",
"Kelelawar Api": "Kelelawar Api adalah kelelawar biasa yang sarangnya jatuh ke aliran lava di bawah menara. Sayapnya sekarang membara dan ia meludahkan bola api kecil sebagai peringatan. Mereka kehilangan arah terbang, tetapi tidak kehilangan lapar.",
"Golem Magma": "Golem Magma dipahat dari batu yang masih panas dari dasar gunung. Ia berjalan lambat dan membakar tanah di sekelilingnya. Saat hancur, ia meledak dan meninggalkan genangan api, seakan menolak berhenti panas.",
"Raksasa Lava": "Raksasa Lava lahir dari satu tetes terbesar lava yang pernah menetes dari Retakan. Ia melempar meteor cair ke arah penyihir dan meninggalkan kawah di tiap langkah. Para pengungsi menamai jalur yang ia lewati Jalan Merah.",
"Kodok Racun": "Kodok Racun adalah kodok rawa yang meminum air dari kolam bekas ramuan penyihir. Ia melompat riang tanpa tahu ia meninggalkan genangan beracun. Orang desa memelihara satu untuk meracuni tikus, sampai kodok itu tumbuh sebesar kerbau.",
"Penyembur Racun": "Penyembur Racun dulu ahli pembasmi hama yang mengolah gas dari tanaman beracun. Setelah terpapar sihir Retakan, gas itu mengalir dari mulutnya tanpa bisa dihentikan. Ia memuntahkan awan hijau tepat di tempat musuhnya berdiri.",
"Ular Beracun": "Ular Beracun bersembunyi di bawah akar pohon tua di tepi Lembah. Ia menyemburkan tiga peluru bisa sekaligus, seolah tahu bahwa satu peluru tak akan pernah cukup. Tabib desa memburu bisanya untuk obat, dan sekarang bisa itu memburu mereka.",
"Jamur Beracun": "Jamur Beracun tumbuh dari tubuh prajurit yang gugur dan tak pernah dikuburkan. Ia menyebar spora ke segala arah dan meledak menjadi kabut racun saat diganggu. Para penjelajah mengajarkan satu aturan: jangan menyentuh jamur yang tumbuh di tempat pertempuran.",
"Raksasa Racun": "Raksasa Racun dulu raksasa pengangkut tong bahan kimia untuk pabrik ramuan. Tongnya bocor, tubuhnya menyerap gas, dan sejak itu ia mengepulkan racun tanpa henti. Burung enggan terbang di atasnya.",
"Bola Petir": "Bola Petir adalah sisa badai pertama yang terperangkap di dalam bola kaca percobaan penyihir. Ia lepas dan menyambar ke mana pun ada logam. Di tempat ia lewat, rambut berdiri dan lonceng berbunyi sendiri.",
"Elang Petir": "Elang Petir terbang terlalu tinggi saat badai Retakan dan tersambar tepat di jantungnya. Ia kini menembakkan garis petir lurus dari paruhnya, selalu menuju mangsa yang paling terang. Para pemburu menandainya sebagai tanda untuk berlindung di bawah tanah.",
"Penyetrum": "Penyetrum adalah juru las menara yang kejatuhan sihir listrik. Ia memanggil tiga sambaran petir sekaligus di sekitar target, seolah sedang menyalakan lampu pesta. Pasukannya berani maju karena tahu ia selalu menyambar lebih dulu.",
"Raksasa Badai": "Raksasa Badai membawa awan hitam kecil yang mengikutinya ke mana pun. Dari awan itu turun hujan petir dan gelombang listrik. Penduduk mengira badai sedang berjalan, sampai melihat kakinya.",
"Pelempar Batu": "Pelempar Batu dulu atlet desa yang jago melempar batu ke sasaran. Retakan mengisinya dengan kekuatan sehingga batu yang ia lempar sebesar kepala kambing. Ia tak membidik pemain, hanya sasaran terbesar di depan matanya.",
"Armadillo Batu": "Armadillo Batu adalah hewan tambang yang kulitnya mengeras jadi batu setelah kena debu Retakan. Ia menggulung diri dan melesat jauh lebih cepat dari yang tampak. Penambang menjulukinya Kelereng Maut.",
"Golem Batu": "Golem Batu dibentuk dari tumpukan batu pagar yang runtuh saat Retakan terbuka. Ia melempar potongan tubuhnya sendiri lalu menumbuhkannya lagi. Meski tampak bodoh, ia sangat sabar menunggu mangsa lewat.",
"Raksasa Batu": "Raksasa Batu tertidur di dasar tebing dan baru bangun saat tanah berguncang. Ia menghentak bumi sampai batu berjatuhan dari langit. Pedagang Keliling mencatat: kalau tanah bergetar dan kau tak melihat apa-apa, itu mungkin dia.",
"Pembantai Baja": "Pembantai Baja adalah raksasa terbaik hasil tempaan bengkel Raja Inflasi. Gelombang kejutnya menyapu medan, lalu tubuhnya menggulung menabrak sisanya. Ia dibuat bukan untuk menang, melainkan untuk menyisakan sedikit saja yang bisa dihitung.",
"Kapten Bayangan": "Kapten Bayangan memimpin kelompok mata-mata yang dulu membelot dari kerajaan. Ia menghilang, muncul di dekat sasaran, lalu menghujani shuriken dan pisau. Konon ia tak pernah terlihat berkedip, karena matanya sendiri sudah tertutup bayangan.",
"Pendeta Gelap": "Pendeta Gelap dulunya penyembuh kuil terang yang mengabaikan nasihat gurunya. Ia memanggil petir sambil menyembuhkan semua kawan yang masih hidup. Doa-doanya sekarang adalah bisikan yang membuat dingin siapa pun yang mendengar.",
"Naga Kecil": "Naga Kecil menetas dari telur yang dicuri penyihir dari puncak gunung. Meski masih anak-anak, ia menyemburkan kipas api dan melontarkan bola api yang cukup untuk membakar padang. Para penyihir dilarang menyentuh sisiknya karena ibunya masih mencarinya.",
"Ratu Laba-laba": "Ratu Laba-laba bersarang di ruang bawah tanah menara dan merajut jaring dari benang sihir. Ia memanggil anak-anaknya dan menyemburkan awan racun saat sarangnya terancam. Para penyihir sepakat, satu-satunya jalan keluar dari sarangnya adalah dengan membakarnya.",
"Golem Kristal": "Golem Kristal tumbuh dari rangkaian kristal sihir yang membesar di bawah Retakan. Tubuhnya tembus cahaya namun nyaris tak tertembus senjata. Cincin pecahan es yang ia tembakkan adalah serpihan tubuhnya sendiri.",
"Pemburu Malam": "Pemburu Malam adalah pemburu tak bernama yang masuk ke Lembah setelah matahari terbenam dan tak pernah keluar. Ia berkedip, menghilang, lalu menerjang tanpa suara. Orang desa menyalakan obor sepanjang malam karena takut padanya.",
"Kolosus": "Kolosus adalah patung raksasa penjaga gerbang kerajaan yang dibangunkan Retakan. Hentakannya mengguncang tanah, hujan batu mengikuti, dan ia memanggil tengkorak cepat sebagai pengawal. Para pemahat patung itu pernah berkata: jangan pernah mengagumi karyamu terlalu lama.",
"Penguasa Bayangan": "Penguasa Bayangan memerintah makhluk-makhluk gelap yang muncul tiap malam di Lembah. Ia memanggil hantu dan menebar cincin roh, seolah memimpin upacara pemakaman. Tak ada yang pernah melihat wajahnya; hanya tudung dan dua titik cahaya.",
"Titan Perang": "Titan Perang adalah panglima raksasa Raja Inflasi yang ikut menaklukkan tujuh desa dalam semalam. Zirahnya setebal tembok kota, hujan lemparannya meratakan kebun, dan terjangannya menumbangkan menara. Ia tak pernah mundur, karena tak ada satu pun perintah mundur dalam kamusnya.",
"Archon Cahaya": "Archon Cahaya adalah utusan cahaya yang turun ke Lembah untuk menolong, tetapi terjebak dalam angka Raja Inflasi. Ia memanah dengan sinar dan menyambar dengan petir suci. Para tetua menyesalkan, bahkan cahaya pun bisa dibeli.",
"Malaikat Maut": "Malaikat Maut adalah entitas yang bertugas menghitung kematian di Lembah dan kini kelelahan menghitung. Ia memanggil tank dari alam baka dan menyembuhkan sekutunya. Ia tidak membenci siapa pun; ia hanya tidak bisa berhenti bekerja.",
"Penguasa Es": "Penguasa Es adalah penguasa gletser yang menolak mencair meski musim berganti. Gelombang dinginnya memperlambat siapa pun dan kebal pembekuan. Di singgasananya konon ada seribu patung es yang adalah penantang sebelumnya.",
"Phoenix Muda": "Phoenix Muda belum sempat belajar bangkit dari abu sendiri. Ia berkedip, menembakkan lima bola api sekaligus, dan bingung kenapa semua orang lari. Para penyihir yakin ia akan menjadi legenda jika dibiarkan tumbuh, sayangnya ia tumbuh di pihak yang salah.",
"Raja Racun": "Raja Racun adalah penguasa rawa yang berkuasa lewat aura beracun dan semburan gas tebal. Ia memanggil kodok-kodok racun sebagai prajurit pribadi. Tak ada yang tahu apakah ia manusia, katak, atau sihir yang kebetulan berpikir.",
"Dewa Petir": "Dewa Petir adalah roh badai yang dulu disembah desa di kaki gunung. Ia menjatuhkan delapan sambaran sekaligus lalu melepas gelombang listrik, seolah menagih persembahan yang lama terlupakan. Penduduk yang masih mengingat doanya selalu selamat.",
"Raja Batu": "Raja Batu memerintah pegunungan dari tahta karang. Ia menjatuhkan hujan bongkahan dan menggulung tubuhnya menabrak lawan. Tahta itu terbuat dari batu nisan raja-raja terdahulu yang menolak mati.",
"Ratu Salju": "Ratu Salju adalah hantu putri yang membeku di tengah pelarian dari Retakan. Ia menembakkan duri pelambat dan memanggil serigala salju sebagai pengiring. Mahkotanya tak pernah mencair, bahkan di perapian terpanas.",
"Iblis Magma": "Iblis Magma adalah iblis tingkat tinggi yang diundang ke dunia lewat sihir pemanggilan yang salah. Ia melontarkan lima semburan api dan hujan lava, lalu meninggalkan genangan api saat tumbang. Para pemanggil sudah lama hangus, tapi ia belum diperintah pulang.",
"Hantu Wabah": "Hantu Wabah adalah arwah tabib desa yang gagal menahan penyakit dan kini menyebarkannya. Ia mengepung dengan racun dan memanggil jamur peledak. Setiap malam ia terdengar menghitung korban yang tak sempat disembuhkan.",
"Elemental Badai": "Elemental Badai adalah badai yang menolak reda dan akhirnya mengambil bentuk. Ia menjatuhkan sepuluh petir sekaligus dan menembakkan sinar listrik panjang. Para ahli cuaca bersumpah ia tak punya hati, tapi punya suasana hati yang sangat buruk.",
"Gargoyle Granit": "Gargoyle Granit adalah patung penjaga katedral yang dibangunkan sihir Retakan. Ia nyaris tak bisa digores, melempar batu, dan menggulung dengan kecepatan mengerikan. Pada malam hari ia kembali ke atap, seolah tidak ada yang terjadi.",
"Kaisar Es Abadi": "Kaisar Es Abadi memerintah dunia beku yang menunggu setelah musim terakhir. Ia melepas gelombang beku raksasa, hujan es, dan tembakan pelambat. Konon ia ingin seluruh Lembah membeku agar tak ada lagi yang bisa memakan angka.",
"Raja Neraka": "Raja Neraka adalah penguasa api yang lebih tua dari menara itu sendiri. Kipas api, hujan lava, cincin api, dan imp panggilan adalah pasukan setianya. Ia tidak mengenal ampun karena tak ada yang pernah memintanya.",
"Maha Racun": "Maha Racun adalah pusat wabah yang menyebar dari bawah Lembah. Aura gas raksasa dan jamur peledak adalah dua senjata utamanya. Ia tak bergerak cepat; ia hanya menunggu semua yang lain berhenti bernapas.",
"Murka Langit": "Murka Langit adalah amarah badai purba yang hanya muncul menjelang akhir Inflasi. Dua belas petir, sinar, dan teleportasi adalah caranya mengumumkan diri. Para penyihir tua menyebutnya pertanda bahwa Raja Inflasi sudah dekat.",
"Penjaga Inflasi": "Penjaga Inflasi adalah penjaga terakhir yang ditugaskan sebelum singgasana Raja Inflasi. Cincin emas, teleportasi, dan golem panggilan adalah pertahanan terakhir sang raja. Ia bukan musuh yang ingin kau hadapi dengan sisa tenaga.",
"Laba-laba Kecil": "Laba-laba Kecil adalah anak Ratu Laba-laba yang menetas serempak dalam kepompong sihir. Mereka cepat, rapuh, dan meninggalkan jejak racun sebagai tanda belajar berburu. Bila satu muncul, biasanya induknya sudah dekat.",
"Tengkorak": "Tengkorak adalah tulang prajurit yang dibangkitkan Necromancer dari tanah pertempuran. Rapuh namun tak kenal lelah, mereka datang bergerombol tanpa pikiran sendiri. Para penyihir menganggapnya pertanda bahwa pertempuran yang dulu belum benar-benar selesai.",
"Pecahan": "Pecahan adalah serpihan terkecil dari musuh Pecah yang masih hidup. Mereka tak punya ingatan, hanya naluri untuk menempel pada pemain. Satu pecahan hampir tak berbahaya, tapi mereka tidak pernah datang satu.",
"Raksasa Sedang": "Raksasa Sedang adalah tahap tengah dari kutukan Raksasa Pecah. Ia lebih kecil dari ayahnya dan lebih besar dari anaknya, terjebak di antara keduanya. Saat jatuh, ia pecah sekali lagi menjadi musuh biasa.",
"Tengkorak Raksasa": "Tengkorak Raksasa adalah kerangka raksasa yang dibangkitkan Necromancer untuk menjadi pengawal pribadi. Tulangnya sebesar tiang rumah, dan ia tak pernah bicara karena tak punya lidah. Ia berdiri di sisi tuannya seperti tembok yang bisa berjalan.",
"Raksasa Induk Mini": "Raksasa Induk Mini adalah anak yang dilahirkan Raksasa Induk saat ia terluka. Mereka kecil, gesit, dan selalu datang bertiga untuk membela induknya. Bila kau melihat satu sendirian, mungkin dua lainnya sedang berada di belakangmu.",
})

BOSS_STORY = {
"Bos Biasa": "Bos Biasa adalah jenderal pasukan kecil yang pertama kali menembus gerbang Lembah Abu. Ia bukan yang terkuat, tetapi ia yang paling dulu memahami cara Raja Inflasi memerintah: tak ada belas kasihan untuk prajurit yang gagal. Tiap bos yang datang setelahnya hanyalah variasi dari pola yang ia mulai, dan para penyihir memakainya sebagai ujian awal untuk mengukur kesiapan murid.",
"Bos Penyembuh": "Bos Penyembuh dulu kepala tabib kerajaan yang mengabdikan hidupnya merawat korban perang. Ketika Retakan terbuka, ia menolak meninggalkan pasien dan sihir inflasi menjadikannya penyembuh tak terkalahkan bagi pihak yang salah. Ia menyembuhkan siapa pun, bahkan musuh sesama bos, karena tak lagi bisa membedakan siapa yang pantas.",
"Bos Necromancer": "Bos Necromancer adalah guru dari para necromancer kecil yang kini berkeliaran. Ia mempelajari sihir tulang untuk bertemu kembali dengan keluarganya yang gugur, tapi malah membangkitkan pasukan yang tak pernah mengenalnya. Tiga Tengkorak Raksasa miliknya adalah wajah-wajah yang ia coba kenali setiap hari.",
"Brute Berkepala Dua": "Brute Berkepala Dua dulunya sepasang kembar yang tak bisa dipisahkan, penjaga tambang batu di pegunungan. Mereka bersatu secara paksa oleh sihir Retakan dan sekarang berbagi satu tubuh, satu amarah, dan dua pendapat. Satu kepala menghentak dan melempar batu, kepala lainnya melompat dan meninju, selalu bergantian.",
"Penjaga Gerbang": "Penjaga Gerbang adalah penjaga terakhir gerbang utama kerajaan yang menolak membukanya meski Retakan mengepung. Zirah tebalnya hasil tempaan tujuh pandai besi, tombak sucinya diberkati kuil. Setelah sumpahnya dibengkokkan angka, ia memanggil meteor, petir, dan pasukan acak untuk mempertahankan gerbang yang sudah tidak ada.",
"Komandan Minigun": "Komandan Minigun memimpin resimen penembak terbaik kerajaan dan membawa senjata berputar kebanggaannya sendiri. Ia tak pernah kalah di medan terbuka karena tak pernah berhenti menembak. Zirah dan darahnya tebal karena ia percaya prajurit sejati tidak boleh jatuh sebelum pelurunya habis.",
"Executioner": "Executioner adalah algojo bertopeng yang kapaknya diwariskan dari generasi ke generasi. Ia melempar kapak itu lalu menariknya kembali tanpa pernah meleset, seperti sumpah yang selalu kembali ke pemiliknya. Ia tidak pernah membuka topengnya, sehingga tak ada yang tahu apakah di baliknya masih ada manusia.",
"Raja Api": "Raja Api adalah penguasa kerajaan bara yang dulu dikenal bijak dan adil. Api oranye di tubuhnya menandai kemarahan yang terkendali. Saat terdesak, nyalanya berubah menjadi api biru yang lebih panas dan lebih sedih, seakan ia akhirnya menyadari apa yang ia bakar.",
"Tengkorak Penembak": "Tengkorak Penembak dulu koboi pengelana yang tersesat di Lembah Abu dan tak pernah pulang. Revolvernya selalu terisi dan tas di punggungnya menyimpan minigun rahasia. Ia masih memakai topi miring dan menyapa penantang dengan anggukan sopan sebelum menembak.",
"Raja Inflasi": "Raja Inflasi adalah penguasa angka yang membuat semua hal membengkak: harga, tubuh, ambisi, dan hutang. Ia menelan emas dunia bukan karena rakus, melainkan karena percaya semakin besar jumlahnya, semakin dekat ia pada keabadian. Kedua tangan terbangnya menjatuhkan seluruh kemampuan musuh yang pernah kau kalahkan, karena ia menyimpan satu dari setiap korban sebagai koleksi. Mengalahkannya berarti menghentikan angka yang tak pernah berhenti bertambah.",
"Kubus Pengawal": "Kubus Pengawal adalah penjaga tingkat pertama arena geometri, dibentuk dari balok sihir pertama yang diciptakan Raja Inflasi. Ia melayang tanpa suara dan hanya bergerak mengikuti ketukan musik arena. Setiap serangannya berirama: cincin kotak, kubus jatuh, bingkai, lalu ulang. Penantang yang bisa menghitung ketukan akan selalu selamat.",
"Pemintal Laser": "Pemintal Laser adalah penjaga tingkat kedua yang dulu mesin penerangan menara, dibangunkan dan diberi tugas menjaga arena. Ia memutar sinar yang menyapu lantai seperti jarum jam yang marah. Laser-lasernya berubah warna tiap fase, dan penantang cerdas tahu bahwa pola putaran tidak pernah acak.",
"Segitiga Badai": "Segitiga Badai adalah penjaga ketiga yang terbentuk dari sudut-sudut badai yang tak sempat reda. Pecahan segitiga tajam ditembakkan ke segala arah, dan pusaran mengintai di tengah arena. Menurut penyihir arena, ia marah karena sudutnya tak pernah bisa tumpul.",
"Mata Pengintai": "Mata Pengintai adalah penjaga keempat yang selalu menatap penantang tanpa berkedip. Dari tatapannya lahir sinar, air mata peluru, dan iris berlubang yang harus dicari celah amannya. Konon ia menangis karena pernah melihat terlalu banyak kekalahan.",
"Penabuh Ritme": "Penabuh Ritme adalah penjaga kelima yang memimpin arena seperti konduktor orkestra maut. Not jatuh, equalizer, dan gendang membentuk simfoni yang harus dihindari mengikuti irama. Ia berhenti hanya ketika penantangnya menang, atau ketika lagunya selesai.",
"Prajurit Piksel": "Prajurit Piksel adalah penjaga keenam dan terakhir arena geometri, berwujud kumpulan titik cahaya yang rusak. Hujan piksel, garis pindai, dan petak rusak adalah serangan khasnya, dan ia sesekali menggandakan bayangannya sendiri. Ia disebut Kiamat Piksel karena setiap penantang yang jatuh berubah menjadi satu titik baru di tubuhnya.",
}
BOSS_MOVES = {
"Bos Biasa": "Cincin peluru ke segala arah; menerjang pemain; mengamuk (lebih cepat) saat HP di bawah 50%.",
"Bos Penyembuh": "Menyembuhkan diri dan semua musuh di sekitar (termasuk boss lain); menembakkan sihir hijau. Habisi ia lebih dulu.",
"Bos Necromancer": "Memanggil 3 Tengkorak Raksasa; menghujani sihir gelap dari jauh.",
"Brute Berkepala Dua": "Hentakan tanah, lemparan batu, lompatan, dan tinju yang melempar pemain.",
"Penjaga Gerbang": "Memanggil meteor, petir, dan pasukan acak; tombak suci menusuk lurus.",
"Komandan Minigun": "Menyapu medan dengan minigun; bertahan dengan darah dan zirah tebal.",
"Executioner": "Melempar kapak yang kembali ke tangannya; berzirah penuh sehingga lambat tetapi kuat.",
"Raja Api": "Semburan dan bola api; berubah menjadi api biru yang lebih ganas saat terdesak.",
"Tengkorak Penembak": "Revolver tembakan cepat; mengeluarkan minigun dari tas.",
"Raja Inflasi": "Memakai SEMUA kemampuan: serangan tangan, meteor, petir, minigun, sonic boom, jurus semua musuh, jurus semua boss, dan seluruh pola boss geometri. 3 fase, makin cepat dan beruntun di fase akhir.",
}

SKILL_STORY = {
"Ranjau Sihir": "Ranjau Sihir diciptakan penjaga menara untuk menjebak penyusup di lorong sempit. Jebakan kecil itu tampak seperti batu biasa sampai seseorang menginjaknya. Penjaga tua berkata, kesabaran adalah mantra yang paling jarang dipelajari.",
"Ranjau Berantai": "Ranjau Berantai lahir dari kebiasaan seorang penjaga yang tak sabar menunggu satu ledakan. Ia menanam lebih banyak dan lebih besar, hingga seluruh lorong bergetar berurutan. Musuh yang selamat dari satu ledakan jarang selamat dari yang berikutnya.",
"Tombak Cahaya": "Tombak Cahaya ditempa dari sinar fajar oleh para penjaga gerbang. Ia tidak berhenti pada musuh pertama dan terus melesat sampai cahayanya habis. Murid-murid belajar bahwa serangan lurus yang jujur sering lebih ampuh daripada yang rumit.",
"Tombak Langit": "Tombak Langit adalah tiga tombak cahaya yang dilempar bersamaan, seolah langit sendiri membidik. Tak ada barisan yang cukup rapat untuk menahannya. Para penjaga gerbang menyebutnya doa yang dilempar.",
"Sabit Hantu": "Sabit Hantu dulu milik penuai arwah yang tak pernah beristirahat. Ia menebas dalam lingkaran, mengambil apa pun yang terlalu dekat. Penyihir yang memakainya belajar tidak menoleh ke belakang.",
"Sabit Maut": "Sabit Maut adalah wujud sabit hantu yang sudah kenyang jiwa. Delapan tebasan melingkar jatuh hampir bersamaan dan melempar musuh hingga pingsan. Konon penuai tua itu tersenyum setiap kali melihatnya dipakai.",
"Burung Api": "Burung Api lahir dari bara menara yang tak pernah padam. Ia terbang mengejar musuh lalu meledak jadi kobaran. Anak-anak akademi diajari memanggilnya dengan sopan, karena ia mudah tersinggung.",
"Phoenix Api": "Phoenix Api adalah burung api yang sudah beberapa kali terbakar dan bangkit kembali. Dua phoenix terbang bersama dan meledak lebih luas. Katanya, abu yang ditinggalkannya selalu hangat sampai pagi.",
# ---- Senjata ----
"Tinju": "Tinju adalah pelajaran pertama di akademi menara: sebelum belajar memanggil api atau petir, murid diminta mengepalkan tangan dan mengalirkan sihir ke buku jarinya. Para guru percaya penyihir yang tak bisa memukul tak akan bisa melindungi. Tak ada mantra yang lebih jujur dari tinju yang bersinar.",
"Bola Energi": "Bola Energi adalah sihir murni tanpa unsur, ditembakkan dari telapak tangan. Ia dipakai murid untuk berlatih membidik karena selalu mencari musuh terdekat. Penyihir tua berkata, jika kau bisa mengendalikan bola ini, kau bisa mengendalikan semua mantra lain.",
"Aura Duri": "Aura Duri diciptakan penjaga menara untuk melindungi diri saat tertidur di pos jaga. Lingkaran duri tak kasat mata muncul di sekeliling tubuh dan melukai siapa pun yang berani mendekat. Banyak pencuri belajar dari pengalaman bahwa menara itu tidak pernah benar-benar kosong.",
"Gelombang Kejut": "Gelombang Kejut dahulu digunakan untuk meruntuhkan tembok kota musuh. Penyihir yang menguasainya dapat mengirim getaran lewat tanah hingga menggoyahkan segala sesuatu di sekitar. Kini sihir yang sama dipakai untuk memukul mundur kerumunan Pasukan Angka.",
"Petir Rantai": "Petir Rantai ditemukan penyihir yang bereksperimen dengan badai di dalam botol. Satu sambaran melompat dari musuh ke musuh seperti kabar yang menyebar di pasar. Tak ada yang bisa memastikan seberapa jauh ia akan menyambar, bahkan penciptanya.",
"Panah Berganda": "Panah Berganda adalah teknik pemanah elf yang diadaptasi menjadi sihir: satu busur, banyak panah. Anak panah itu terbuat dari cahaya dan tak pernah habis. Pemanah tua mengingatkan muridnya untuk tidak bangga, karena yang menembak bukan jarimu melainkan sihirnya.",
"Bola Api": "Bola Api adalah mantra yang paling dicari oleh murid baru karena terlihat paling megah. Bola-bola itu mengorbit tubuh pemanggil seperti planet kecil yang haus. Guru tua selalu memperingatkan: api tidak pernah ingat siapa yang memanggilnya.",
"Duri Es": "Duri Es dipelajari penyihir utara dari pembekuan embun pagi di ujung daun. Satu duri cukup untuk membekukan musuh di tempat. Mereka mengajarkan satu pelajaran penting: dingin yang sabar lebih berbahaya daripada api yang tergesa.",
"Bumerang": "Bumerang adalah senjata para pengelana yang diberi sihir agar selalu kembali ke pelemparnya. Ia menebas di jalan pergi dan menebas lagi di jalan pulang. Konon bumerang pertama dibuat oleh seorang pengembara yang selalu takut kehilangan sesuatu.",
"Awan Racun": "Awan Racun diramu para tabib untuk membasmi hama di ladang, sebelum seseorang menyadari ia juga cocok untuk musuh. Awan hijau itu melayang pelan dan menggerus siapa pun yang berdiri di dalamnya. Pedagang Keliling menjualnya dengan peringatan: jangan hirup, jangan tiup, jangan tanya.",
"Laser Sihir": "Laser Sihir adalah hasil kerja insinyur menara yang berhasil memadatkan cahaya sihir menjadi satu sinar. Sinar itu menembus barisan musuh tanpa pandang bulu. Prototipenya meledak tiga kali sebelum akhirnya stabil.",
"Meteor": "Meteor adalah sihir langit yang memanggil batu angkasa jatuh ke titik tertentu. Penyihir yang memanggilnya harus yakin pada hitungannya, karena meteor tidak mengenal kata maaf. Konon meteor pertama yang dipanggil di Lembah menciptakan danau yang masih ada sampai sekarang.",
"Pisau Terbang": "Pisau Terbang adalah mainan murid iseng yang diubah menjadi senjata mematikan. Pisau sihir ini menembus musuh lurus ke arah bidikan dan terus melaju. Para guru melarangnya dipakai di dalam kelas setelah insiden di aula besar.",
"Angin Puyuh": "Angin Puyuh adalah puting beliung kecil yang dipanggil dari udara kosong. Ia menyedot musuh ke tengah dan melukai mereka berulang kali. Penyihir angin mengatakan ia tak diciptakan, melainkan dilepaskan dari sangkarnya.",
"Jejak Api": "Jejak Api adalah mantra para pelari yang membakar tanah di belakangnya agar tak dikejar. Setiap langkah meninggalkan api yang menyala beberapa detik. Para pengejar tahu satu hal: mundur adalah satu-satunya jalan yang aman.",
"Perisai Cahaya": "Perisai Cahaya diwariskan para kesatria suci yang mengelilingi sang penyihir dengan lingkaran cahaya berputar. Ia memblokir peluru sekaligus melukai musuh yang menyentuhnya. Perisai itu hanya bertahan selama pemakainya percaya ia layak dilindungi.",
"Duri Bumi": "Duri Bumi muncul dari dalam tanah tepat di bawah kaki musuh. Pencipta mantra ini adalah penambang yang muak dengan monster yang merangkak di terowongannya. Tanah selalu mengingat siapa yang menginjaknya.",
"Roh Pemburu": "Roh Pemburu adalah arwah penyihir lama yang rela mengabdi sebagai pelayan sihir. Mereka mengejar musuh sendiri tanpa perlu dibimbing. Mereka tak menuntut apa pun, kecuali kesempatan untuk merasa berguna sekali lagi.",
"Bola Pantul": "Bola Pantul awalnya mainan anak-anak di akademi yang ditingkatkan menjadi senjata. Ia memantul dari musuh ke musuh tanpa kehilangan semangat. Anak yang menciptakannya kini dewasa, tapi masih tertawa tiap kali bola itu memantul.",
"Kilat Langit": "Kilat Langit memanggil petir dari awan yang tidak ada. Sambaran jatuh di tempat musuh yang tak terduga, seakan langit memilih sendiri sasarannya. Penyihir yang memakainya sering melihat ke atas dan berbisik terima kasih.",
# ---- Evolusi ----
"Tinju Badai": "Tinju Badai lahir ketika seorang murid terus melatih tinju hingga buku jarinya mengeluarkan angin. Satu pukulan menyebar ke semua musuh di jangkauan, seolah badai kecil melompat dari kepalan. Guru tua mengakui, ia belum pernah melihat ketekunan yang menyerupai kemarahan.",
"Bola Energi Ganda": "Bola Energi Ganda terjadi saat sihir murni terpecah menjadi tiga bola kembar. Tiap bola mencari sasaran sendiri tapi berasal dari satu hati. Penyihir yang mencapai tahap ini biasanya mulai bicara pada bola-bolanya.",
"Aura Neraka": "Aura Neraka adalah aura duri yang meluas dan menyala seperti bara. Lingkaran itu kini membakar siapa saja yang bahkan sekadar berpikir mendekat. Para penjaga menara menyebutnya api tak terlihat yang menjaga mimpi mereka.",
"Gelombang Dahsyat": "Gelombang Dahsyat adalah gelombang kejut yang kini mampu menerbangkan prajurit dan merobohkan benteng. Getarannya terasa sampai di dasar Retakan. Penyihir kuno yang menciptakannya kehilangan pendengaran karena ledakan pertamanya.",
"Petir Dewa": "Petir Dewa adalah petir rantai yang naik derajat menjadi hukuman langit. Ia melompat lebih jauh, lebih ganas, dan jarang meleset. Penyihir yang menguasainya biasanya tak berani menyebut namanya terlalu keras.",
"Hujan Panah": "Hujan Panah adalah panah berganda yang sudah tak terhitung lagi jumlahnya. Satu tembakan menyebar menjadi hujan yang menutupi langit. Pemanah yang melihatnya biasanya menyimpan busurnya dalam diam.",
"Lingkaran Api": "Lingkaran Api adalah bola api yang bertambah dan mengorbit membentuk cincin pelindung. Cincin itu membakar apa pun yang mencoba menembusnya. Penyihir api percaya inilah kemarahan yang akhirnya belajar berdisiplin.",
"Badai Es": "Badai Es adalah duri es yang menjelma badai kecil. Tiga duri kini membekukan lebih lama dan lebih luas dari sebelumnya. Penyihir utara menyebutnya bisikan musim dingin yang tidak mau pulang.",
"Bumerang Kembar": "Bumerang Kembar adalah tiga bumerang besar yang dilempar bersamaan. Mereka menari di udara dan menebas setiap musuh dua kali. Orang bilang pembuatnya tak pernah kehilangan apa pun lagi setelahnya.",
"Kabut Pekat": "Kabut Pekat adalah dua awan racun yang jauh lebih besar dan lama. Ia menyelimuti medan sampai penglihatan menyempit. Para tabib mengingatkan: yang menyembuhkan dan yang meracuni hanya dibedakan oleh takaran.",
"Laser Nova": "Laser Nova adalah laser sihir yang berkembang menjadi tiga sinar lebar. Tiap sinar menembus semua musuh di jalurnya. Insinyur menara berkata ia terlalu terang untuk dipandang langsung.",
"Hujan Meteor": "Hujan Meteor memanggil empat meteor raksasa tiap jatuhan. Langit tampak retak dan satu per satu batu menghantam bumi. Konon penyihir pertama yang memakainya menangis karena keindahannya.",
"Hujan Pisau": "Hujan Pisau melepaskan pisau-pisau tambahan yang menembus semua musuh di jalurnya. Satu lemparan menjadi ratusan kilatan cahaya. Penyihir yang memakainya berbisik: ini bukan lagi lemparan, ini cuaca.",
"Topan Raksasa": "Topan Raksasa adalah dua puting beliung yang lebih besar dan melempar musuh jauh. Ia menggulung segala sesuatu tanpa pandang bulu. Warga yang melihatnya dari jauh mengira itu adalah dewa yang sedang menari.",
"Jalur Neraka": "Jalur Neraka adalah jejak api yang melebar dan bertahan jauh lebih lama. Seluruh jalan yang kau lalui menjadi kuburan bagi pengejar. Sebagian orang menolak menapakinya lagi bahkan setelah apinya padam.",
"Benteng Cahaya": "Benteng Cahaya menambah dua perisai dan memberi kekebalan sebagian. Peluru musuh hancur sebelum sempat menyentuh pemilik perisai. Konon cahaya itu berasal dari doa para penjaga terdahulu.",
"Gerbang Duri": "Gerbang Duri memunculkan duri bumi yang lebih besar dan melumpuhkan lama. Musuh yang terperangkap tak bisa bergerak sampai gerbang menutup. Penambang tua menyebutnya pintu terakhir yang pernah mereka gali.",
"Legiun Roh": "Legiun Roh memanggil lebih banyak roh yang menembus beberapa musuh sekaligus. Mereka tidak lagi pelayan, melainkan pasukan. Para arwah itu akhirnya mendapat alasan untuk bangga pada kematian.",
"Bola Pelangi": "Bola Pelangi adalah dua bola pantul yang memantul jauh lebih banyak dengan warna yang berganti tiap benturan. Ia menari di antara musuh seperti kegembiraan yang tak bisa dihentikan. Anak-anak yang melihatnya selalu tersenyum, bahkan di tengah perang.",
"Murka Langit": "Murka Langit adalah kilat langit yang menyambar dengan empat sambaran tambahan dan membuat musuh pingsan. Langit seperti kehilangan kesabaran pada dunia di bawahnya. Penyihir yang memakainya sering lupa menyebutkan bahwa nama itu juga milik seorang musuh.",
}

SKILL_STORY.update({
# ---- Combo ----
"Combo: Uap Beku": "Para penyihir api dan es dulu bermusuhan, hingga seorang murid mencoba menggabungkan keduanya dalam satu ruangan. Uap yang tercipta membekukan di tengah panas, dan cara itu kini dikenal sebagai Uap Beku. Kisah ini selalu diceritakan untuk mengingatkan bahwa musuh lama bisa menjadi sekutu paling licik.",
"Combo: Badai Petir": "Badai Petir lahir ketika Kejut menyentuh Petir Rantai di satu medan perang. Sambaran yang saling menyalakan itu tidak bisa dihentikan oleh siapa pun yang berada di bawahnya. Penyihir tua menyebutnya reaksi berantai yang menolak berhenti.",
"Combo: Hujan Bintang": "Hujan Bintang diciptakan penyihir yang ingin menenangkan anak yatim dengan memperlihatkan bintang jatuh. Bola energi ganda menembak lebih banyak, seolah langit malam ikut bergerak. Anak-anak itu kini besar dan sebagian menjadi penjaga menara.",
"Combo: Kabut Maut": "Kabut Maut terjadi saat Aura Duri dan racun bertemu di satu lingkaran. Kabut hijau meluas lebih lama dari yang diperkirakan siapa pun. Pembuatnya selalu memakai penutup wajah saat mengajarkannya.",
"Combo: Tinju Bumerang": "Tinju Bumerang terjadi ketika Tinju Badai dan Bumerang Kembar bergabung. Satu lemparan tambahan menjadi tanda bahwa tangan dan senjata saling mengenali. Murid yang menciptakannya bersumpah bumerang itu sempat menepuk bahunya.",
"Combo: Neraka Api": "Neraka Api muncul ketika Bola Api dan Aura menyala bersama. Dunia di sekitar pemanggil berubah menjadi tungku yang nyaris tak bisa ditahan. Kebakaran yang dihasilkan pertama kali konon terlihat dari seberang laut.",
"Combo: Gempa Es": "Gempa Es terjadi saat duri es dan getaran gelombang kejut saling memperkuat. Tanah membeku sebelum pecah, dan pecahannya menghantam semua yang ada. Para penjelajah utara menganggapnya pertanda bahwa gunung es mulai bergerak.",
"Combo: Petir Beracun": "Petir Beracun menyatukan racun dan petir dalam satu sambaran. Racun menempel di setiap lompatan listrik, menyisakan jejak hijau di langit. Tak ada obat yang diketahui, hanya tabib yang sabar menunggu.",
"Combo: Laser Badai": "Laser Badai terjadi saat sinar laser memicu sambaran petir di sepanjang jalurnya. Cahaya dan petir saling berlomba menuju sasaran. Insinyur menara menyebutnya kecelakaan terbaik yang pernah terjadi di laboratorium.",
"Combo: Meteor Api": "Meteor Api adalah meteor yang meninggalkan api membara di tempat jatuhnya. Medan pertempuran terbakar jauh setelah ledakan pertama selesai. Para penyihir langit mengingatkan, api yang jatuh dari langit hampir selalu membawa serta kemarahan.",
"Combo: Puting Api": "Puting Api adalah topan raksasa yang disulut api dan tumbuh 30% lebih besar. Puting beliung itu menyala seperti obor raksasa yang berputar. Kata penyihir angin, ia menunjukkan bahwa api tak pernah ingin diam.",
"Combo: Roh Racun": "Roh Racun menambahkan dua roh pemburu yang membawa bisa dari kuburan bekas wabah. Mereka melayang tanpa suara dan meninggalkan jejak hijau. Para pemburu arwah tahu: yang beracun bukan arwahnya, melainkan kenangan di dalamnya.",
"Combo: Pisau Kejut": "Pisau Kejut adalah hujan pisau yang dialiri listrik, menambah tiga pisau sekaligus. Tiap pisau menyengat sebelum menusuk. Pembuatnya selalu menyarungkan pisaunya dengan sarung karet.",
"Combo: Benteng Bumi": "Benteng Bumi lahir dari perisai cahaya yang bersatu dengan duri bumi. Perisai menjadi lebih kebal dan dua duri tambahan muncul di tanah. Ia dipakai para penjaga untuk menahan serbuan di jalur sempit.",
"Combo: Bola Listrik": "Bola Listrik adalah bola pantul yang dialiri petir rantai sehingga memantul empat kali lebih banyak. Setiap pantulan menyisakan percikan di udara. Anak-anak akademi menjulukinya bola terlarang karena tidak ada yang berhasil memegangnya.",
"Combo: Laser Beku": "Laser Beku adalah laser yang mampu membekukan musuh yang ditembusnya. Sinar dingin itu meninggalkan jalur berkilau di udara. Para pembuatnya menyebutnya bukti bahwa cahaya pun bisa merasa kedinginan.",
# ---- Fusi ----
"Prisma Uap": "Prisma Uap dilahirkan dari peleburan Bola Api dan Duri Es menjadi satu kristal bening. Di dalam kristal itu panas dan dingin bergulat dan melepaskan ledakan uap yang membekukan sekaligus membakar. Penyihir yang membuatnya mengaku tak pernah memahami bagaimana dua hal berlawanan bisa memiliki satu jiwa.",
"Guntur Gempa": "Guntur Gempa memadukan Petir Rantai dengan Gelombang Kejut. Gelombang guntur melumpuhkan semua musuh dekat, sebelum mereka sempat menyadari apa yang terjadi. Dentumannya konon terdengar dua hari setelah dilepaskan.",
"Meriam Bintang": "Meriam Bintang menggabungkan Panah Berganda dan Bola Energi menjadi meriam kecil di tangan penyihir. Peluru bintangnya mengejar musuh dan meledak di sasaran. Pembuatnya menamainya dari kenangan masa kecil melihat meteor.",
"Wabah Senyap": "Wabah Senyap adalah leburan Aura Duri dan Awan Racun yang membentuk cincin wabah. Ia tak menimbulkan suara, hanya kehampaan di sekelilingnya. Para tabib menyebutnya satu-satunya sihir yang membuat sunyi menjadi senjata.",
"Palu Elang": "Palu Elang lahir dari Bumerang dan Tinju yang menyatu menjadi palu berputar yang menembus barisan musuh. Bilahnya berkelebat seperti elang yang mengitari mangsa. Para prajurit tua menyukainya karena mengingatkan pada kampung halaman yang jauh.",
"Matahari Mini": "Matahari Mini adalah leburan Aura Duri dan Bola Api yang meledakkan matahari kecil di sekitar penyihir. Panasnya membakar semua musuh dekat tanpa melukai pemanggilnya. Konon pembuatnya pernah membuat siang di tengah malam.",
"Gempa Salju": "Gempa Salju memadukan Duri Es dan Gelombang Kejut menjadi gelombang salju yang membekukan semua musuh dekat. Ia menyapu medan seperti longsor yang bergerak mendatar. Warga utara menamainya napas gunung.",
"Petir Bisa": "Petir Bisa adalah leburan Petir Rantai dan Awan Racun, menciptakan rantai petir beracun yang melompat antar musuh. Setiap sambaran meninggalkan bisa di tubuh yang tersentuh. Para ahli ramuan menyebutnya obat paling mematikan yang pernah dirancang tanpa sengaja.",
"Sinar Langit": "Sinar Langit menggabungkan Laser Sihir dengan Kilat Langit menjadi sinar petir lebar yang melumpuhkan siapa pun yang tertembus. Ia terlihat seperti tiang yang menghubungkan bumi dan awan. Orang desa menganggapnya tanda kebaikan dewa, sampai melihat apa yang ditinggalkannya.",
"Hujan Magma": "Hujan Magma adalah leburan Jejak Api dan Meteor yang menjatuhkan meteor magma dan meninggalkan lahar membara. Tanah yang terkena menjadi kawah kecil. Penyihir yang membuatnya menamai kawah-kawah itu dengan nama musuh yang pernah dikalahkannya.",
"Pusaran Api": "Pusaran Api memadukan Bola Api dan Angin Puyuh sehingga pusaran api menyeret musuh ke arah penyihir lalu membakarnya. Ia menari seperti kobaran yang kehilangan arah. Penyihir yang membuatnya ternyata tak pernah merasa kepanasan.",
"Arwah Bisa": "Arwah Bisa adalah leburan Roh Pemburu dan Awan Racun, menghasilkan arwah beracun yang memburu musuh dan meledakkan racun. Ia tak meninggalkan jejak, hanya kabut hijau samar. Konon arwah itu adalah korban wabah yang dendamnya akhirnya menemukan jalan keluar.",
"Badai Belati": "Badai Belati menggabungkan Pisau Terbang dengan Gelombang Kejut hingga membentuk lingkaran belati yang menembus dan melumpuhkan musuh. Ia berputar seperti kincir yang haus. Pengrajin belati tua menolak membuatnya lagi setelah melihat hasilnya.",
"Benteng Duri": "Benteng Duri memadukan Duri Bumi dan Perisai Cahaya sehingga duri bumi menghantam dan melumpuhkan musuh di sekitar sasaran. Ia berdiri sebagai benteng dan senjata sekaligus. Para penjaga gerbang menyebutnya sumpah yang berubah menjadi tanah.",
"Listrik Pantul": "Listrik Pantul adalah leburan Bola Pantul dan Petir Rantai, menghasilkan rantai listrik yang memantul tanpa henti antar musuh. Ia tak pernah kehabisan tenaga selama ada target. Para penyihir menjulukinya bola yang tidak tahu cara berhenti.",
"Sinar Kristal": "Sinar Kristal memadukan Duri Es dan Laser Sihir menjadi sinar kristal yang membekukan semua yang tertembus. Cahaya dingin itu membentuk kristal di sepanjang jalurnya. Para pemburu mengaku pernah melihat jalur itu bertahan sampai pagi.",
"Komet Beku": "Komet Beku adalah leburan Duri Es dan Meteor, menjatuhkan komet es yang membekukan musuh di sekitar sasaran. Ia membawa dingin angkasa ke tanah. Astronom kuno mencatatnya sebagai tanda keberuntungan yang nyaris tidak pernah dipercaya.",
"Badai Sempurna": "Badai Sempurna menggabungkan Kilat Langit dan Angin Puyuh: kilat jatuh bersama angin yang menarik musuh mendekat. Ia disebut sempurna karena tidak ada celah untuk lolos. Penyihir yang menciptakannya tak pernah melepaskannya lagi karena takut pada akibatnya.",
"Bilah Pulang": "Bilah Pulang adalah leburan Bumerang dan Pisau Terbang menjadi bilah berputar ke segala arah, cepat dan menembus. Bilahnya selalu kembali ke tangan pemiliknya meski dunia berubah. Pembuatnya menyebutnya satu-satunya janji yang ia tepati.",
"Planet Pantul": "Planet Pantul menggabungkan Bola Pantul dan Bola Energi menjadi peluru planet yang mengejar dan meledak di sasaran. Ia mengorbit sebentar sebelum menyerang. Anak-anak akademi suka menyebutnya mainan para dewa.",
"Arwah Api": "Arwah Api memadukan Bola Api dan Roh Pemburu, menciptakan arwah api yang memburu musuh dan membakarnya. Mereka berpijar seperti lilin dan lenyap seperti harapan. Penyihir yang memanggilnya biasa menutup mata saat mereka pergi.",
"Tinju Gempa": "Tinju Gempa adalah leburan Tinju dan Gelombang Kejut: satu hantaman mengguncang semua musuh di dekat penyihir. Tanah di sekitarnya retak membentuk bintang. Guru bela diri menganggapnya bukti bahwa kekuatan terbesar sering berasal dari hal paling sederhana.",
# ---- Skill Avatar ----
"Tinju Lurus": "Tinju Lurus adalah jurus khas Badang, pahlawan yang dulu hanyalah penjaga biasa di kaki menara. Ia mengepalkan tangan, menyalurkan seluruh sihirnya, lalu menghantam lurus jauh ke depan. Rumornya, tinjunya bisa menembus tembok, tapi ia lebih bangga karena tinju itu tidak pernah mengkhianati temannya.",
"Tebasan Kilat": "Tebasan Kilat adalah jurus Rez, pengembara yang meninggalkan kampungnya karena tak ingin diam. Ia melesat menebas musuh lalu kebal sesaat, seolah waktu melambat di sekelilingnya. Ia berjanji tak akan berhenti sampai menemukan alasan untuk berhenti.",
"Lubang Hitam": "Lubang Hitam adalah jurus Black Hole, penyihir kosmik yang pernah melihat akhir sebuah bintang. Ia menyedot dan menggerus musuh selama 4,5 detik, seolah mengundang kehampaan untuk bertamu. Konon ia tak pernah menjawab pertanyaan tentang apa yang ada di dalamnya.",
"Amukan Kuat": "Amukan Kuat adalah jurus Dead Strong, prajurit yang hidupnya sudah ditentukan sebagai pengorbanan. Ia mengamuk selama 5 detik dengan damage semua skill 1,7 kali lipat dan gerakan lebih cepat. Ia tak mengamuk karena marah, melainkan karena ingin segera selesai.",
"Jaring Benang": "Jaring Benang adalah jurus String Move, penari boneka yang kehilangan dalangnya. Delapan benang menyambar, melukai, dan mengikat musuh seperti panggung dalang yang hidup. Ia menari karena itu satu-satunya cara ia bisa merasa dikendalikan.",
"Kilat Cahaya": "Kilat Cahaya adalah jurus Fast Light, kurir yang dulu mengantar pesan lebih cepat dari fajar. Ia berlari 4,5 detik dengan jejak cahaya yang melukai siapa pun yang dilewatinya. Pesan terakhirnya belum pernah sampai, dan ia masih berlari.",
"Gerbang Yomi": "Gerbang Yomi adalah jurus Yomatoda, pendeta dari negeri jauh yang menjaga pintu antara hidup dan mati. Ia menguras musuh, memulihkan HP, dan melepas roh untuk menemani. Ia mengaku tak pernah takut mati, hanya takut dilupakan.",
"Badai Shuriken": "Badai Shuriken adalah jurus Sruken, ninja yang bersumpah tak akan melukai orang tak bersalah. Ia melempar 20 shuriken ke segala arah dalam satu tarikan napas. Ia selalu meminta maaf pada setiap musuh sebelum pertarungan, dan selalu serius.",
"Hantaman Gunung": "Hantaman Gunung adalah jurus Muscle Skrim, pegulat yang tubuhnya sekeras batu karang. Ia menghantam tanah hingga musuh pingsan, sementara tubuhnya kebal 40%. Ia menolak disebut kuat, katanya, ia hanya terlalu keras kepala untuk roboh.",
"Amarah Monster": "Amarah Monster adalah jurus Brudal Mongskter, makhluk yang dulu dikurung kerajaan karena dianggap berbahaya. Ia membesar selama 6 detik dengan damage 1,5 kali, pulih cepat, dan beraura. Ia sebenarnya lebih takut pada kemarahannya sendiri daripada musuhnya.",
"Hujan Meteor Agung": "Hujan Meteor Agung adalah jurus Archmage Aurelia, penyihir agung yang memimpin akademi menara sebelum Retakan. Meteor besar jatuh ke 10 musuh sekaligus atas perintahnya. Ia mengaku tak pernah membuat meteor, hanya membangunkannya dari tidur.",
"Tombak Langit": "Tombak Langit adalah jurus Valkyrie Sera, pejuang dari langit yang turun karena mendengar tangisan. Tujuh tombak cahaya menembus musuh dalam satu kedipan mata. Ia tidak pernah menyebut asal tombaknya, hanya bahwa tombak itu selalu terasa hangat.",
"Singularitas": "Singularitas adalah jurus Void Emperor Nox, penguasa kehampaan yang kini ikut bertarung demi alasan yang tak ia ungkap. Lubang hitam raksasa muncul selama 5 detik dan menelan segalanya. Para tetua percaya ia hanya ingin satu hal: tempat yang tidak sepi.",
"Henti Waktu": "Henti Waktu adalah jurus Chrono Lyra, penjaga waktu yang terlalu sering melihat akhir cerita. Ia membekukan semua musuh selama 4 detik, memberi dunia satu napas tambahan. Ia mengaku empat detik itu adalah satu-satunya hal yang bisa ia berikan.",
"Kelahiran Kembali": "Kelahiran Kembali adalah jurus Phoenix Ignis, burung api yang selalu bangkit dari abunya. Ledakan api memulihkan 35% HP dan membuatnya kebal 2,5 detik. Ia percaya kematian hanya jeda singkat antara dua pertarungan.",
"Napas Naga": "Napas Naga adalah jurus Dewa Naga Ryu, naga yang menjelma manusia untuk melindungi pegunungan. Semburan apinya berlangsung 1,6 detik dan membakar segalanya di depan. Ia hanya berpesan: jangan pernah meremehkan makhluk yang diam.",
})



_ABIL_LONG = {"trail": "meninggalkan jejak di tanah", "aura": "aura yang mengikuti tubuhnya", "spit": "menyemburkan genangan ke posisimu",
              "shoot": "menembakkan peluru", "nova": "melepas gelombang melingkar", "bolt": "memanggil petir ke posisimu",
              "lob": "melontarkan bola jatuh dari langit", "cone": "menyemburkan kipas serangan", "beam": "menembakkan sinar lurus",
              "roll": "menggulung dan melaju cepat", "ring": "melepas cincin peluru", "blink": "berteleportasi ke dekatmu",
              "summon": "memanggil bantuan", "healaoe": "menyembuhkan semua di sekitarnya"}
_FLAG_TIPS = [("ice_immune", "Jangan andalkan sihir es; kebal pembekuan."), ("mother", "Jangan biarkan terlalu lama; tiap luka melahirkan mini. Habisi dengan damage besar sekaligus."),
              ("ethereal", "Serang saat ia berwujud nyata, bukan saat menembus."), ("protector", "Pecahkan perisainya dulu sebelum zirah dan darah."),
              ("splits", "Siapkan serangan area; ia pecah jadi musuh lebih kecil."), ("explodes", "Jangan menghabisinya saat dekat; ia meledak ketika mati."),
              ("shotgun", "Berdiri di samping, bukan di depan laras."), ("minigunner", "Menyingkir saat larasnya berputar."),
              ("laser", "Geser keluar dari garis sebelum sinar ditembak."), ("sniper", "Terus bergerak; tembakannya lurus."),
              ("bomber", "Jangan diam di lingkaran merah."), ("warden", "Jangan berdiri lurus di garis sonic boom."),
              ("hammer", "Menjauh dari lingkaran hantaman palu."), ("slash", "Mundur saat tebasan diisi."),
              ("thunder", "Habisi lebih dulu agar kawannya tak makin cepat."), ("buffer", "Habisi lebih dulu; ia menguatkan kawan."),
              ("chief", "Habisi lebih dulu agar perintah cepatnya berhenti."), ("crystal_mage", "Prioritaskan sebelum kawannya dikuatkan."),
              ("toxic", "Jangan berdiri di genangan racun."), ("teleporter", "Waspadai sisi belakang setelah ia berpindah."),
              ("dasher", "Hindari garis merah sebelum ia menerjang."), ("necro", "Habisi pemanggilnya agar tengkorak berhenti muncul.")]


def abil_text(a):
    t = a.get("t")
    s_ = _ABIL_LONG.get(t, t)
    bits = []
    if a.get("n", 1) > 1:
        bits.append("%d sekaligus" % a["n"])
    if a.get("range"):
        bits.append("jangkauan %d" % a["range"])
    if a.get("slow"):
        bits.append("memperlambat")
    cd = a.get("cd")
    if cd:
        bits.append("tiap %.1f-%.1f dtk" % (cd[0], cd[1]))
    return s_ + (" (" + ", ".join(bits) + ")" if bits else "")


def enemy_tip(k):
    for f, tip in _FLAG_TIPS:
        if k.get(f):
            return tip
    if k.get("armor", 0) >= 100 or k.get("shield"):
        return "Zirahnya tebal; fokuskan damage besar atau tembusan."
    if k.get("hp", 0) >= 400:
        return "Darah banyak; jaga jarak dan serang terus sambil bergerak."
    if k.get("speed", 0) >= 2.0:
        return "Sangat cepat; jangan sampai terkepung."
    return "Musuh biasa; habisi cepat sebelum jumlahnya menumpuk."


def enemy_detail_rows(k):
    rows = [("HP dasar", fmt_num(k["hp"])), ("Ukuran", "radius %d" % k["radius"])]
    if k.get("elem"):
        rows.append(("Elemen", EL_NAME.get(k["elem"], k["elem"])))
    for a in k.get("abil") or []:
        rows.append(("Jurus", abil_text(a)))
    if k.get("mode") == "inflation":
        rows.append(("Mode", "Hanya muncul di Mode Inflasi"))
    if k.get("pickup_chance") is not None:
        rows.append(("Peluang drop", "%d%%" % round(k["pickup_chance"] * 100)))
    rows.append(("Saran", enemy_tip(k)))
    return rows


ROBOT_STORY = " Robot ini hanya ada di Tutorial: dirakit Pedagang Keliling agar murid baru bisa berlatih tanpa risiko. Ia meniru perilaku musuh asli, tetapi tidak membawa dendam apa pun."


AVATAR_TIERS = [("PEMULA", 1500, (120, 230, 140)), ("MENENGAH", 4800, (130, 200, 255)),
                ("MAHIR", 8400, (255, 200, 90)), ("LEGENDARIS", 10 ** 9, (255, 120, 200))]


class Game:
    _freeze = None
    _freeze_st = None
    def __init__(self):
        self.save = SaveData()
        for k, v in self.save.data["settings"].items():
            if k in SETTINGS and isinstance(v, (int, float)):
                SETTINGS[k] = float(v)
        key = self.save.data.get("selected_avatar")
        self.selected_avatar = next((i for i, a in enumerate(AVATARS) if a["key"] == key), 0)
        if not self.owned(self.selected_avatar):
            self.selected_avatar = 0
        self.music_key = None
        self.music_prio = 0
        self.music_lock_until = 0.0
        self.menu_msg = ""
        self.menu_msg_t = 0.0
        self.title_t = 0.0
        self.last_crystals = 0
        self.event_over = False
        self.av_scroll = 0.0
        self.tk_scroll = 0.0
        self.av_press = None
        self.tk_press = None
        self.fx_anims = []
        self.shieldt_t = 0.0
        self._shieldt_surf = None
        self.al_tab = "enemy"
        self.toko_from = "playmenu"
        self.toko_tab = "avatar"
        self.toko_sel = 1
        self.gacha = None
        self.al_scroll = 0.0
        self.al_press = None
        self.det_scroll = 0.0
        self.det_max = 0.0
        self.det_press = None
        self.al_sel = None
        self._al_cache = None
        self._rec_cache = None
        self._prev_cache = {}
        self.settings_from = "title"
        self.badge_queue = []
        self.badge_show = None
        _titles = {k: t for (k, t, _d, _i) in all_badges()}
        for _k in self.save.data.get("badge_pending", []):
            if _k in _titles and _k in self.save.data.get("badges", []):
                self.badge_queue.append((_k, _titles[_k]))
        self.reset(None)
        self.state = "title"
        if "welcome" not in self.save.data.get("badges", []):
            self.save.data.setdefault("badges", []).append("welcome")
            self.save.data.setdefault("badge_pending", []).append("welcome")
            self.save.save()
            self.badge_queue.append(("welcome", "Selamat Datang"))

    def reset(self, mode):
        self.mode = mode
        self.mode_config = MODE_CONFIGS[mode] if mode else MODE_CONFIGS["normal"]
        global ROBOT_MODE
        ROBOT_MODE = (mode == "tutorial")
        RUN_RULES["slots"] = 5 if mode == "inflation" else 6
        RUN_RULES["owned"] = None if mode == "tutorial" else set(self.save.data.get("owned_skills", STARTER_SKILLS))
        RUN_RULES["books"] = None if mode == "tutorial" else set(self.save.data.get("books", []))
        RUN_RULES["avatar_dmg"] = AVATARS[self.selected_avatar].get("dmg", 1.0)

        self.badang = Badang(AVATARS[self.selected_avatar])
        PLAYER_BUFFS["dmg"] = 1.0
        PLAYER_BUFFS["perm"] = 1.0
        DIFFICULTY["lv"] = 1
        self.enemies = []
        self.gems = []
        self.pickups = []
        self.projectiles = []
        self.enemy_projectiles = []
        self.boomerangs = []
        self.poison_zones = []
        self.strikes = []
        self.tornados = []
        self.hazards = []
        self.merchants = []
        self.effects = []
        self.damage_texts = []
        self.nearest_enemy = None

        self.arena = None
        self.level_boss = None
        self.next_boss_level = 10
        self.next_merchant_level = 5
        self.jsab_kills = 0
        self.revives = 0
        self.autosave_timer = 15.0
        self.shop_menu = None
        self.new_rank = None
        self.last_score = 0
        self.run_finished = False

        self.time_survived = 0.0
        self.spawn_timer = 0.0
        self.spawn_interval = 2.6
        self.hporb_timer = 4.0
        self.rune_timer = 12.0
        self.evo_seen = set()
        ACTIVE_COMBOS.clear()
        self.boss_timer = 30.0 if mode == "inflation" else 45.0
        self.boss_active = False
        self.kills = 0
        self.gold = 0
        self.gold_frac = 0.0
        self.fx_anims = []
        self.shieldt_t = 0.0
        SHIELD_ZONES[:] = []
        self.boss_kill_count = 0
        self.protectors = []
        self.victory_kind = None
        self.pending_mode = "normal"
        self.gold_gain_mult = 1.0
        self.pending_levelups = 0
        self.skill_rec_t = 0.0
        self.elem_phase = None
        self.elem_timer = 60.0
        self.elem_idx = 0
        self.tut = None
        self.final_boss = None
        self.victory_bonus = 0
        self.dialog = None
        self.light = None
        self.victory = None
        self.final_spawned = False
        self.last_event = None
        self.sched = []
        self.advanced_unlocked = True

        self.budget = 3.0
        self.spawn_acc = 0.0
        self.spawn_target = None
        self.spawn_wait = 0.0
        self.pulse_timer = PULSE_DENSE_TIME
        self.pulse_relief = False
        self.mercy_t = 0.0
        self.mercy_cd = 0.0
        self.formation_timer = random.uniform(*FORMATION_INTERVAL) * 0.8
        self.formation_warn = None
        self.formation_music_t = 0.0
        self.recycle_timer = 0.5
        self.boss_spawn_count = 0
        self.last_old_boss = None
        self.jsab_index = 0
        self.last_jsab_time = 0.0
        self.level_times = {}
        self.last_level_seen = 1
        self.dmg_acc = 0.0
        self.dps_buckets = []
        self.dps_clock = 0.0
        self.boss_intro = None
        self.shake = 0.0
        self.flash_t = 0.0
        self.flash_col = (255, 255, 255)
        self.shake_off = (0.0, 0.0)

        self.toast_text = None
        self.toast_timer = 0.0

        self.upgrade_menu = None

        self.joystick_finger_id = None
        self.joystick_center = JOY_DEFAULT_CENTER
        self.joystick_knob = JOY_DEFAULT_CENTER
        self.move_vector = (0.0, 0.0)

        self.state = "playing" if mode else "menu"

    def start_run(self, mode, resume=None):
        if not self.owned(self.selected_avatar):
            self.selected_avatar = self.first_owned()
        self.reset(mode)
        if mode == "tutorial":
            bg_enqueue(["tut", "shop", "tut_boss", "event"], front=True)
            self.tut = {"i": 0, "t": 0.0, "entered": False, "shop": False, "met": False, "moved": 0.0, "px": self.badang.x, "py": self.badang.y, "kills0": 0, "lvl0": 1, "haz": 0.0}
        if mode in ("normal", "inflation"):
            bg_enqueue(["shop", "event", "boss_old", "lvb_0", "lvb_1"], front=True)
        if resume:
            self.restore_run(resume)
        self.save.data["selected_avatar"] = AVATARS[self.selected_avatar]["key"]
        self.save.save()
        sfx("click")

    def reset_to_menu(self):
        self.reset(None)

    def get_camera(self):
        return self.badang.x - WIDTH / 2 + self.shake_off[0], self.badang.y - HEIGHT / 2 + self.shake_off[1]

    def owned(self, idx):
        return AVATARS[idx]["key"] in self.save.data["owned_avatars"]

    def first_owned(self):
        return next((i for i in range(len(AVATARS)) if self.owned(i)), 0)

    def cycle_owned(self, step):
        n = len(AVATARS)
        i = self.selected_avatar
        for _ in range(n):
            i = (i + step) % n
            if self.owned(i):
                self.selected_avatar = i
                return

    def buy_avatar(self, idx):
        av = AVATARS[idx]
        if self.owned(idx):
            return True
        have = self.save.data["crystals"]
        if have < av["price"]:
            sfx("deny")
            self.menu_msg, self.menu_msg_t = "Kristal kurang %d" % (av["price"] - have), 2.0
            return False
        self.save.data["crystals"] = have - av["price"]
        self.save.data["owned_avatars"].append(av["key"])
        self.save.save()
        sfx("buy")
        self.menu_msg, self.menu_msg_t = "%s dibeli!" % av["name"], 2.0
        return True

    def leave_avatars(self):
        if not self.owned(self.selected_avatar):
            key = self.save.data.get("selected_avatar")
            idx = next((i for i, a in enumerate(AVATARS) if a["key"] == key), 0)
            self.selected_avatar = idx if self.owned(idx) else self.first_owned()
        self.save.data["selected_avatar"] = AVATARS[self.selected_avatar]["key"]
        self.save.save()
        sfx("click")
        self.state = "menu"

    def avatar_confirm(self):
        if self.owned(self.selected_avatar):
            self.leave_avatars()
        else:
            self.buy_avatar(self.selected_avatar)

    def compute_crystals(self):
        b = self.badang
        base = int(self.kills * 0.35 + b.level * 4 + self.time_survived / 15.0 + self.jsab_kills * 40
                   + self.boss_kill_count * 10)
        return int(base * self.mode_config.get("crystal_mult", 1.0))

    def enemies_in_range(self, x, y, r):
        r2 = r * r
        return [e for e in self.enemies if not e.dead and dist_sq(e.x, e.y, x, y) <= r2]

    def find_nearest_enemy(self):
        if self.nearest_enemy is not None and not self.nearest_enemy.dead:
            return self.nearest_enemy
        bx, by = self.badang.x, self.badang.y
        best = None
        best_d = None
        for e in self.enemies:
            if e.dead:
                continue
            d = (e.x - bx) ** 2 + (e.y - by) ** 2
            if best_d is None or d < best_d:
                best_d = d
                best = e
        self.nearest_enemy = best
        return best


    def wave_multiplier(self):
        return self.time_survived / 15.0



    def enemy_cap(self):
        return MAX_ENEMIES + min(30, self.badang.level) + (INFL_CAP_BONUS if self.mode == "inflation" else 0)

    def player_power(self):
        b = self.badang
        bonus = max((w.combo_bonus for w in b.weapons), default=1.0)
        return b.level * 0.04 + (bonus - 1.0) * 0.8 + len(ACTIVE_COMBOS) * 0.15

    def spawn_pool(self):
        lv = self.badang.level
        wm = self.wave_multiplier()
        out = []
        for k in ALL_SPAWN_TYPES:
            if wm < k["min_wave"] or lv < k.get("min_lv", 0):
                continue
            if k.get("mode") and k["mode"] != self.mode:
                continue
            base = 1.0
            if k["min_wave"] > 0:
                base = min(1.6, (wm - k["min_wave"]) * 0.5 + 0.3)
            if k.get("min_lv"):
                base = min(base, 0.35 + (lv - k["min_lv"]) * 0.08)
            if k.get("elem"):
                base *= 1.9
                if k["elem"] == self.elem_phase:
                    base *= 2.4
            out.append((k, max(0.05, base)))
        return out

    def pick_spawn_kind(self, max_cost=None):
        """Pilih jenis musuh. Build pemain makin kuat -> pilihan makin condong ke musuh BERAT."""
        expo = -0.4 + min(1.4, self.player_power() * 0.3)
        cands, weights = [], []
        for k, base in self.spawn_pool():
            c = enemy_cost(k)
            if max_cost is not None and c > max_cost:
                continue
            cands.append(k)
            weights.append(base * (c ** expo))
        if not cands:
            return None
        return random.choices(cands, weights=weights)[0]

    def add_enemy(self, kind, elite=False, spawn_at=None):
        e = Enemy(kind, self.wave_multiplier(), self.badang.x, self.badang.y,
                  mode_config=self.mode_config, elite=elite, spawn_at=spawn_at)
        self.enemies.append(e)
        return e

    def update_spawning(self, dt):
        b = self.badang
        lv = b.level
        wm = self.wave_multiplier()
        self.pulse_timer -= dt
        if self.pulse_timer <= 0:
            if self.pulse_relief:
                self.pulse_relief = False
                self.pulse_timer = PULSE_DENSE_TIME
            else:
                self.pulse_relief = True
                self.pulse_timer = random.uniform(*(INFL_RELIEF_TIME if self.mode == "inflation" else PULSE_RELIEF_TIME))
        if self.mode == "inflation":
            self.elem_timer -= dt
            if self.elem_timer <= 0:
                order = ["fire", "ice", "toxic", "thunder", "rock"]
                self.elem_phase = order[self.elem_idx % len(order)]
                self.elem_idx += 1
                self.elem_timer = INFL_ELEM_PHASE
                self.show_toast("FASE %s! Musuh %s merajalela" % (EL_NAME[self.elem_phase].upper(), EL_NAME[self.elem_phase].lower()))
                self.effects.append({"x": self.badang.x, "y": self.badang.y, "radius": 500, "timer": 0.6, "max_timer": 0.6, "color": EL_COL[self.elem_phase]})
        income = SPAWN_BASE_INCOME + SPAWN_WAVE_INCOME * (wm ** 0.9) + SPAWN_LEVEL_INCOME * (lv - 1)
        income *= self.mode_config["spawn_mult"]
        if self.mode == "normal" and lv > LATE_SCALE_LEVEL:
            income *= min(8.0, 1.09 ** (lv - LATE_SCALE_LEVEL))
        if self.pulse_relief:
            income *= INFL_RELIEF_MULT if self.mode == "inflation" else PULSE_RELIEF_MULT
        if self.boss_active:
            income *= BOSS_SPAWN_MULT
        ratio = b.hp / max(1.0, b.max_hp)
        if ratio < 0.3 and self.mercy_cd <= 0:
            self.mercy_t, self.mercy_cd = 8.0, 25.0
        if self.mercy_t > 0:
            income *= HP_LOW_MULT
        elif ratio > 0.8:
            income *= HP_HIGH_MULT
        self.budget = min(SPAWN_BANK_CAP, self.budget + income * dt)
        self.recycle_timer -= dt
        if self.recycle_timer <= 0:
            self.recycle_timer = 0.5
            self.recycle_far_enemies(6)
        self.spawn_acc += dt
        if self.spawn_acc < SPAWN_TICK:
            return
        self.spawn_acc = 0.0
        if len(self.enemies) >= self.enemy_cap():
            self.recycle_far_enemies(10)
            return
        for _ in range(2 if self.budget > 30 else 1):
            if self.spawn_target is None:
                self.spawn_target = self.pick_spawn_kind()
                self.spawn_wait = 0.0
            k = self.spawn_target
            if k is None:
                return
            cost = enemy_cost(k)
            if cost <= self.budget:
                elite = random.random() < elite_chance(lv) * (INFL_ELITE_MULT if self.mode == "inflation" else 1.0)
                if elite and self.budget < cost * 2:
                    elite = False
                self.budget -= cost * (2 if elite else 1)
                self.spawn_target = None
                self.add_enemy(k, elite=elite)
            else:
                self.spawn_wait += SPAWN_TICK
                if self.spawn_wait > 6.0:
                    self.spawn_target = self.pick_spawn_kind(max_cost=max(1, int(self.budget)))
                    self.spawn_wait = 0.0
                return

    def recycle_far_enemies(self, limit=6):
        b = self.badang
        far2 = RECYCLE_DIST ** 2
        mx, my = self.move_vector
        moving = math.hypot(mx, my) > 0.2
        moved = 0
        for e in self.enemies:
            if moved >= limit:
                break
            if e.dead or e.is_boss or e.no_recycle or e.fixed_dir is not None or e.busy:
                continue
            if dist_sq(e.x, e.y, b.x, b.y) > far2:
                a = (math.atan2(my, mx) + random.uniform(-1.0, 1.0)) if moving else random.uniform(0, math.tau)
                d = random.uniform(760, 840)
                e.x, e.y = b.x + math.cos(a) * d, b.y + math.sin(a) * d
                e.kb_timer = 0.0
                moved += 1
        return moved

    def update_formation(self, dt):
        if self.formation_warn is None:
            self.formation_timer -= dt
            if self.formation_timer <= 0:
                self.start_formation()
            return
        w = self.formation_warn
        w["t"] -= dt
        if w["t"] <= 0:
            self.fire_formation(w)
            self.formation_warn = None
            self.formation_timer = random.uniform(*FORMATION_INTERVAL) * (INFL_EVENT_MULT if self.mode == "inflation" else 1.0)

    def start_formation(self):
        lv = self.badang.level
        kinds = ["ring", "wall", "bats"]
        if self.mode == "inflation" and lv >= 6:
            kinds += ["rockfall", "blizzard", "rockfall", "blizzard"]
        for nm, need in (("spiral", 4), ("pincer", 5), ("skeleton_horde", 6), ("bomb_run", 7), ("meteor_shower", 8),
                         ("frenzy", 8), ("gas_field", 9), ("storm", 10), ("elite_squad", 12), ("giant_charge", 14)):
            if lv >= need:
                kinds += [nm, nm]
        kind = random.choice(kinds)
        if kind == self.last_event and len(kinds) > 4:
            kind = random.choice(kinds)
        self.last_event = kind
        side = random.choice(["top", "bottom", "left", "right"])
        self.formation_warn = {"kind": kind, "side": side, "t": FORMATION_WARN}
        self.formation_music_t = FORMATION_WARN + 12.0
        sfx("warn")

    def fire_formation(self, w):
        if w["kind"] in EVENT2_KINDS:
            self.fire_event2(w)
        else:
            self.fire_formation_basic(w)

    def event_enemy(self, lo=1, hi=4):
        """Musuh acak untuk event: dipilih dari kolam spawn yang sedang terbuka (menurut level & mode) menurut rentang biaya."""
        c = [k for k, _w in self.spawn_pool() if lo <= enemy_cost(k) <= hi and not k.get("stationary")]
        return random.choice(c) if c else ENEMY_TYPES[0]

    def fire_event2(self, w):
        b = self.badang
        lv = b.level
        kind, side = w["kind"], w["side"]
        if self.level_boss is not None:
            return
        wm = self.wave_multiplier()
        room = MAX_ENEMIES + 30 - len(self.enemies)
        dirs = {"top": (0, 1), "bottom": (0, -1), "left": (1, 0), "right": (-1, 0)}
        opp = {"top": "bottom", "bottom": "top", "left": "right", "right": "left"}
        hw, hh = WIDTH / 2 + 90, HEIGHT / 2 + 90

        def mk(k, x, y, elite=False):
            e = Enemy(k, wm, 0, 0, spawn_at=(x, y), mode_config=self.mode_config, elite=elite)
            e.from_event = True
            self.enemies.append(e)
            return e

        def edge_point(sd, along):
            if sd == "top":
                return b.x + along, b.y - hh
            if sd == "bottom":
                return b.x + along, b.y + hh
            if sd == "left":
                return b.x - hw, b.y + along
            return b.x + hw, b.y + along

        if kind == "pincer":
            for sd in (side, opp[side]):
                dx, dy = dirs[sd]
                vertical = sd in ("top", "bottom")
                span = hw if vertical else hh
                slots = int(2 * span / 90)
                gap = random.randrange(max(1, slots - 3))
                for i in range(slots):
                    if gap <= i < gap + 3 or room <= 0:
                        continue
                    x, y = edge_point(sd, -span + i * 90 + 45)
                    e = mk(self.event_enemy(1, 2 + lv // 10), x, y)
                    e.fixed_dir, e.life, e.no_recycle = (dx, dy), 14.0, True
                    room -= 1
            self.show_toast("TANG! DUA TEMBOK!")
        elif kind == "spiral":
            n = min(room, 32)
            for i in range(n):
                a = i * 0.55
                rr = 820 - i * 8
                e = mk(self.event_enemy(1, 2 + lv // 10), b.x + math.cos(a) * rr, b.y + math.sin(a) * rr)
                e.no_recycle = True
            self.show_toast("PUSARAN MUSUH!")
        elif kind == "skeleton_horde":
            names = ["Tengkorak"] * min(room, 22 + min(10, lv // 3))
            if lv >= 10:
                names += ["Necromancer"] * 2
            if lv >= 14:
                names += ["Tengkorak Raksasa Cepat"] * 3
            if lv >= 20:
                names += ["Tengkorak Raksasa"] * 2
            for nm in names[:max(0, room)]:
                a = random.uniform(0, math.tau)
                mk(KIND_BY_NAME[nm], b.x + math.cos(a) * 800, b.y + math.sin(a) * 800).no_recycle = True
            self.show_toast("PASUKAN TENGKORAK!")
        elif kind == "bomb_run":
            names = ["Peledak"] * (10 + min(6, lv // 4))
            if lv >= 9:
                names += ["Pelempar Bom"] * 3
            if lv >= 14:
                names += ["Tanker Raksasa"]
            for nm in names[:max(0, room)]:
                a = random.uniform(0, math.tau)
                e = mk(KIND_BY_NAME[nm], b.x + math.cos(a) * 780, b.y + math.sin(a) * 780)
                e.no_recycle = True
                e.haste, e.haste_mult = 8.0, 1.3
            self.show_toast("SERBUAN PELEDAK! JAGA JARAK!")
        elif kind == "meteor_shower":
            for i in range(20):
                self.after(i * 0.22, lambda: self.meteor_at(b.x + random.uniform(-560, 560), b.y + random.uniform(-330, 330), 1.0, 30, 85))
            self.show_toast("HUJAN METEOR!")
        elif kind == "rockfall":
            for i in range(26):
                self.after(i * 0.2, lambda: self.meteor_at(b.x + random.uniform(-580, 580), b.y + random.uniform(-340, 340), 1.1, 32, 95, (150, 138, 120)))
            names = ["Pelempar Batu", "Armadillo Batu"] * 3 + (["Golem Batu"] if lv >= 12 else [])
            for i, nm in enumerate(names[:max(0, room)]):
                a = i * math.tau / len(names)
                mk(KIND_BY_NAME[nm], b.x + math.cos(a) * 800, b.y + math.sin(a) * 800).no_recycle = True
            self.show_toast("HUJAN BATU!")
        elif kind == "blizzard":
            for i in range(5):
                a = random.uniform(0, math.tau)
                d0 = random.uniform(120, 380)
                self.add_hazard(Hazard("ring", b.x + math.cos(a) * d0, b.y + math.sin(a) * d0, 0.8 + i * 0.4, 1.2, 20,
                                       (170, 225, 255), max_radius=330, thickness=24, slow=True))
            for i in range(3):
                a = i * 2.1 + random.uniform(0, 1)
                self.add_hazard(Hazard("gas", b.x + math.cos(a) * 260, b.y + math.sin(a) * 260, 0.8, 6.0, 9, (190, 230, 255), radius=115, slow=True))
            ice = [k for k in ELEM_TYPES if k.get("elem") == "ice" and k["radius"] < 20]
            for i in range(min(room, 14)):
                a = i * math.tau / 14
                mk(random.choice(ice), b.x + math.cos(a) * 800, b.y + math.sin(a) * 800).no_recycle = True
            if lv >= 12 and room > 14:
                mk(KIND_BY_NAME["Golem Es"], b.x + 800, b.y).no_recycle = True
            self.show_toast("BADAI SALJU! GERAKMU MELAMBAT")
        elif kind == "storm":
            for i in range(26):
                self.after(i * 0.17, lambda: self.sky_bolt(b.x + random.uniform(-520, 520), b.y + random.uniform(-310, 310), 0.8, 26))
            names = (["Bola Petir", "Elang Petir", "Penyetrum"] * 2) if self.mode == "inflation" else ["Penyambar Petir"] * (4 + min(4, lv // 10))
            for i, nm in enumerate(names[:max(0, room)]):
                a = i * math.tau / len(names) + random.uniform(-0.2, 0.2)
                mk(KIND_BY_NAME[nm], b.x + math.cos(a) * 800, b.y + math.sin(a) * 800).no_recycle = True
            self.show_toast("BADAI PETIR!")
        elif kind == "gas_field":
            for i in range(6):
                a = i * math.tau / 6 + random.uniform(-0.3, 0.3)
                d = random.uniform(180, 380)
                self.add_hazard(Hazard("gas", b.x + math.cos(a) * d, b.y + math.sin(a) * d, 0.8, 7.0, 10, (110, 205, 60), radius=120))
            names = (["Kodok Racun", "Ular Beracun", "Jamur Beracun"] * 2) if self.mode == "inflation" else ["Racun Berjalan"] * (5 + min(4, lv // 8))
            for i, nm in enumerate(names[:max(0, room)]):
                a = i * math.tau / len(names) + random.uniform(-0.2, 0.2)
                mk(KIND_BY_NAME[nm], b.x + math.cos(a) * 800, b.y + math.sin(a) * 800).no_recycle = True
            sfx("gas", 0.2)
            self.show_toast("KABUT BERACUN!")
        elif kind == "frenzy":
            for o in self.enemies:
                if not o.dead and not o.is_boss:
                    o.haste, o.haste_mult = 9.0, 1.6
            self.effects.append({"x": b.x, "y": b.y, "radius": 600, "timer": 0.6, "max_timer": 0.6, "color": (255, 90, 60)})
            self.show_toast("AMUK MASSAL! MUSUH JADI CEPAT!")
        elif kind == "elite_squad":
            pool = [k for k, _w in self.spawn_pool() if 4 <= enemy_cost(k) <= 12] or [ARMORED_TYPE]
            for i in range(5):
                x, y = edge_point(side, (i - 2) * 120)
                mk(random.choice(pool), x, y, elite=True).no_recycle = True
            self.show_toast("PASUKAN ELIT!")
        elif kind == "giant_charge":
            big = [k for k, _w in self.spawn_pool() if k.get("shape") in ("giant", "skull", "ghost") and k["radius"] >= 26
                   and 6 <= enemy_cost(k) <= 12 + lv // 5 and not k.get("stationary")] or [KIND_BY_NAME["Raksasa"]]
            cnt = min(7, 4 + lv // 10)
            for i in range(cnt):
                x, y = edge_point(side, (i - (cnt - 1) / 2) * 150)
                e = mk(random.choice(big), x, y)
                e.no_recycle = True
                e.haste, e.haste_mult = 6.0, 1.35
            self.show_toast("SERBUAN RAKSASA!")
        sfx("summon")

    def fire_formation_basic(self, w):
        b = self.badang
        lv = b.level
        kind, side = w["kind"], w["side"]
        wm = self.wave_multiplier()
        room = MAX_ENEMIES + 30 - len(self.enemies)
        if room <= 0 or self.level_boss is not None:
            return
        weak = [ENEMY_TYPES[0], ENEMY_TYPES[4], ENEMY_TYPES[2]]
        mid = [ENEMY_TYPES[0], ENEMY_TYPES[1], ENEMY_TYPES[2]]
        hw, hh = WIDTH / 2 + 90, HEIGHT / 2 + 90
        dirs = {"top": (0, 1), "bottom": (0, -1), "left": (1, 0), "right": (-1, 0)}
        vertical = side in ("top", "bottom")

        def mk(k, x, y):
            e = Enemy(k, wm, 0, 0, spawn_at=(x, y), mode_config=self.mode_config)
            e.from_event = True
            self.enemies.append(e)
            return e

        if kind == "ring":
            n = min(room, 25 + min(10, lv // 4))
            for i in range(n):
                a = i * math.tau / n
                e = mk(self.event_enemy(1, 2 + lv // 9), b.x + math.cos(a) * 790, b.y + math.sin(a) * 790)
                e.no_recycle = True
            self.show_toast("KEPUNGAN!")
        elif kind == "wall":
            dx, dy = dirs[side]
            span = hw if vertical else hh
            step = 82
            slots = int(2 * span / step)
            gap = random.randrange(max(1, slots - 3))
            for i in range(slots):
                if gap <= i < gap + 3 or room <= 0:
                    continue
                along = -span + i * step + step / 2
                if vertical:
                    x, y = b.x + along, b.y + (-hh if side == "top" else hh)
                else:
                    x, y = b.x + (-hw if side == "left" else hw), b.y + along
                kd = self.event_enemy(2, 4 + lv // 8)
                e = mk(kd, x, y)
                e.fixed_dir, e.life, e.no_recycle = (dx, dy), 14.0, True
                room -= 1
            self.show_toast("TEMBOK MUSUH!")
        else:
            dx, dy = dirs[side]
            n = min(room, 12 + min(12, lv // 3))
            for i in range(n):
                off = random.uniform(-260, 260)
                back = random.uniform(0, 160)
                if vertical:
                    x, y = b.x + off, b.y + (-hh - back if side == "top" else hh + back)
                else:
                    x, y = b.x + (-hw - back if side == "left" else hw + back), b.y + off
                e = mk(KIND_BY_NAME["Kelelawar Api"] if (self.mode == "inflation" and random.random() < 0.3) else BAT_TYPE, x, y)
                e.fixed_dir, e.life, e.no_recycle = (dx, dy), 12.0, True
            self.show_toast("KAWANAN KELELAWAR!")
        sfx("summon")

    def draw_formation_warning(self, surf):
        w = self.formation_warn
        if not w:
            return
        t = pygame.time.get_ticks() / 1000.0
        col = (255, 40, 40) if int(t * 8) % 2 == 0 else (160, 20, 20)
        kind = w["kind"]
        opp = {"top": "bottom", "bottom": "top", "left": "right", "right": "left"}
        if kind in EVENT_ALL_SIDES:
            sides = ("top", "bottom", "left", "right")
        elif kind == "pincer":
            sides = (w["side"], opp[w["side"]])
        else:
            sides = (w["side"],)
        th = 12
        for sd in sides:
            if sd == "top":
                pygame.draw.rect(surf, col, (0, 0, WIDTH, th))
                for x in range(60, WIDTH, 120):
                    pygame.draw.polygon(surf, col, [(x - 16, th + 4), (x + 16, th + 4), (x, th + 30)])
            elif sd == "bottom":
                pygame.draw.rect(surf, col, (0, HEIGHT - th, WIDTH, th))
                for x in range(60, WIDTH, 120):
                    pygame.draw.polygon(surf, col, [(x - 16, HEIGHT - th - 4), (x + 16, HEIGHT - th - 4),
                                                    (x, HEIGHT - th - 30)])
            elif sd == "left":
                pygame.draw.rect(surf, col, (0, 0, th, HEIGHT))
                for y in range(60, HEIGHT, 110):
                    pygame.draw.polygon(surf, col, [(th + 4, y - 16), (th + 4, y + 16), (th + 30, y)])
            else:
                pygame.draw.rect(surf, col, (WIDTH - th, 0, th, HEIGHT))
                for y in range(60, HEIGHT, 110):
                    pygame.draw.polygon(surf, col, [(WIDTH - th - 4, y - 16), (WIDTH - th - 4, y + 16),
                                                    (WIDTH - th - 30, y)])
        label = EVENT_LABELS.get(kind, "PERINGATAN!")
        txt = font_med.render("%s  %.1f" % (label, max(0.0, w["t"])), True, (255, 120, 120))
        surf.blit(txt, (WIDTH / 2 - txt.get_width() / 2, HEIGHT - 90))
        hint = EVENT_HINTS.get(kind)
        if hint:
            ht = font_small.render(hint, True, (255, 200, 200))
            surf.blit(ht, (WIDTH / 2 - ht.get_width() / 2, HEIGHT - 60))

    def draw_boss_intro(self, surf):
        bi = self.boss_intro
        if not bi:
            return
        band = pygame.Rect(0, 96, WIDTH, 112)
        pygame.draw.rect(surf, (12, 6, 14), band)
        pygame.draw.rect(surf, (200, 30, 40), (0, band.y, WIDTH, 4))
        pygame.draw.rect(surf, (200, 30, 40), (0, band.bottom - 4, WIDTH, 4))
        title = font_big.render(bi["text"], True, (255, 90, 90))
        surf.blit(title, (WIDTH / 2 - title.get_width() / 2, band.y + 18))
        sub = font_med.render(bi["sub"], True, GOLD_COLOR)
        surf.blit(sub, (WIDTH / 2 - sub.get_width() / 2, band.y + 72))
    def spawn_minions(self, x, y, n, kind_name):
        kinds = {"bat": BAT_TYPE, "dasher": DASHER_TYPE, "ninja": NINJA_TYPE}
        kind = kinds.get(kind_name, BAT_TYPE)
        wm = self.wave_multiplier()
        for _ in range(n):
            if len(self.enemies) >= MAX_ENEMIES + 30:
                break
            off = (random.uniform(-60, 60), random.uniform(-60, 60))
            self.enemies.append(Enemy(kind, wm, 0, 0, spawn_at=(x + off[0], y + off[1]),
                                      mode_config=self.mode_config))

    def after(self, delay, fn):
        """Jadwalkan aksi beberapa detik lagi (dipakai serangan berurutan)."""
        self.sched.append([delay, fn])

    def run_sched(self, dt):
        if not self.sched:
            return
        due = []
        for it in self.sched:
            it[0] -= dt
            if it[0] <= 0:
                due.append(it)
        if due:
            self.sched = [it for it in self.sched if it[0] > 0]
            for it in due:
                try:
                    it[1]()
                except Exception:
                    pass

    def meteor_at(self, x, y, warn, dmg, radius=80, color=(255, 140, 40)):
        """Meteor jatuh: lingkaran peringatan, lalu batu berapi menghantam."""
        self.add_hazard(Hazard("blast", x, y, warn, 0.3, dmg, color, radius=radius))
        fall = 0.55
        self.after(max(0.0, warn - fall), lambda: self.effects.append(
            {"x": x, "y": y, "radius": 0, "timer": fall, "max_timer": fall, "color": color, "fall": True}))
        self.after(warn, lambda: (sfx("boom", 0.1), setattr(self, "shake", max(self.shake, 0.25))))

    def sky_bolt(self, x, y, warn, dmg, radius=52):
        self.add_hazard(Hazard("blast", x, y, warn, 0.25, dmg, LIGHTNING_COLOR, radius=radius, sky=True))
        self.after(warn, lambda: sfx("thunder", 0.05))

    def spawn_random_horde(self, n, cx, cy, max_cost=8):
        wm = self.wave_multiplier()
        for _ in range(n):
            if len(self.enemies) >= MAX_ENEMIES + 30:
                break
            k = self.pick_spawn_kind(max_cost=max_cost) or ENEMY_TYPES[0]
            a = random.uniform(0, math.tau)
            d = random.uniform(40, 160)
            self.enemies.append(Enemy(k, wm, 0, 0, spawn_at=(cx + math.cos(a) * d, cy + math.sin(a) * d), mode_config=self.mode_config))

    def start_final_boss(self):
        b = self.badang
        self.final_spawned = True
        self.enemies = self.settle_enemies_for_boss()
        self.enemy_projectiles, self.hazards, self.strikes = [], [], []
        self.formation_warn = None
        wm = self.wave_multiplier()
        e = Enemy(FINAL_BOSS_TYPE, wm, b.x, b.y, is_boss=True, boss_scale=0, mode_config=self.mode_config,
                  spawn_at=(b.x, b.y - 1100))
        e.boss_kind = "final"
        e.radius = 320
        e.max_hp = 75000000
        e.hp = e.max_hp
        e.dmg = 24 * boss_dmg_scale(self.mode_config)
        e.stop_range = 430
        e.intro_t = 999.0
        e.dmg_in_mult = 1.0  # tanpa pengali damage: HP 75 juta dikalahkan murni oleh damage pemain
        e.hands = [{"x": e.x - 330, "y": e.y + 120, "tx": 0.0, "ty": 0.0, "mode": "idle", "t": 0.0, "side": -1},
                   {"x": e.x + 330, "y": e.y + 120, "tx": 0.0, "ty": 0.0, "mode": "idle", "t": 0.0, "side": 1}]
        self.enemies.append(e)
        self.final_boss = e
        self.boss_active = True
        sfx("intro")
        sfx("boss_spawn")
        lines = [("BOS", "Akhirnya kau tiba, penantang kecil."),
                 ("BOS", "%d tingkat sudah kau daki. Semua itu hanya angka yang menggelembung." % FINAL_BOSS_LEVEL),
                 ("PAHLAWAN", "Aku tidak akan berhenti sebelum kau jatuh!"),
                 ("BOS", "Kalau begitu rasakan semua kekuatan musuh yang pernah kau kalahkan!")]

        def go():
            e.intro_t = 0.0
            e.atk_timer = 2.0
            self.boss_intro = {"text": "RAJA INFLASI", "sub": "Pertarungan terakhir", "t": 2.5}
            sfx("boss_spawn")
            self.shake = 1.0
        self.start_dialog(lines, "talk_final", go)

    def final_extra(self, e, atk, bx, by, base, d):
        """Raja Inflasi memakai semua kemampuan: pola boss geometri (g:), musuh biasa (e:), dan boss lama (b:)."""
        grp, _, nm = atk.partition(":")
        try:
            if grp == "g":
                bi, name, kw = GEO_LIST[int(nm)]
                p = LevelBoss(BOSS_DEFS[bi], 0, e.x, e.y, self.mode_config)
                p.hdmg, p.bdmg, p.pace = e.dmg, e.dmg * 0.5, 1.0
                p.intro = 0
                self.arena = {"cx": bx, "cy": by, "hw": ARENA_HW, "hh": ARENA_HH}
                try:
                    getattr(p, "p_" + name)(self, **kw)
                finally:
                    self.arena = None
                return
            wm = self.wave_multiplier()
            if not hasattr(e, "pup"):
                e.pup, e.pup_act = {}, []
            if atk not in e.pup:
                if grp == "e":
                    p = Enemy(ENEMY_PUP_KINDS[nm], wm, 0, 0, spawn_at=(e.x, e.y), mode_config=self.mode_config)
                else:
                    p = Enemy(BOSS_TYPES_BY_KIND[nm], wm, 0, 0, is_boss=True, boss_scale=0, spawn_at=(e.x, e.y), mode_config=self.mode_config)
                    p.boss_kind = nm
                p.intro_t, p.frozen_timer = 0.0, 0.0
                e.pup[atk] = p
            p = e.pup[atk]
            p.dmg = e.dmg * (1.0 if grp == "b" else 0.9)
            p.hp = p.max_hp * (0.4 if grp == "b" and e.hp < e.max_hp * 0.5 else 1.0)
            p.ability_timer, p.atk_timer, p.bstate, p.busy, p.abil_t = 0.0, 0.0, None, False, None
            p.dead = False
            if grp == "e":
                a = random.uniform(0, math.tau)
                p.x, p.y = bx + math.cos(a) * 300, by + math.sin(a) * 300
                self.effects.append({"x": p.x, "y": p.y, "radius": 90, "timer": 0.5, "max_timer": 0.5, "color": (255, 120, 120)})
            else:
                p.x, p.y = e.x, e.y
            e.pup_act = [x for x in e.pup_act if x[0] is not p]
            e.pup_act.append([p, 3.5 if grp == "e" else 7.0, grp])
        except Exception:
            self.arena = None

    def final_puppets_tick(self, e, dt, bx, by):
        act = getattr(e, "pup_act", None)
        if not act:
            return
        for it in list(act):
            p, t, grp = it
            it[1] -= dt
            if it[1] <= 0:
                act.remove(it)
                continue
            if grp == "b":
                p.x, p.y = e.x, e.y
            p.intro_t, p.frozen_timer, p.dead = 0.0, 0.0, False
            dsq = dist_sq(p.x, p.y, bx, by)
            try:
                if grp == "b":
                    self.run_old_boss(p, dt, dsq, bx, by)
                else:
                    self.run_enemy_abilities(p, dt, dsq, bx, by)
            except Exception:
                act.remove(it)

    def final_tick_intro(self, dt):
        fb = getattr(self, "final_boss", None)
        if fb and fb.intro_t > 0 and not fb.dead:
            ty = self.badang.y - 360
            fb.y += (ty - fb.y) * min(1.0, dt * 1.6)
            fb.x += (self.badang.x - fb.x) * min(1.0, dt * 1.6)
            self.hands_idle(fb, dt)

    def hands_idle(self, e, dt):
        t = pygame.time.get_ticks() / 1000.0
        for h in e.hands:
            if h["mode"] == "idle":
                tx = e.x + h["side"] * (e.radius * 1.05)
                ty = e.y + 150 + math.sin(t * 2 + h["side"]) * 22
                h["x"] += (tx - h["x"]) * min(1.0, dt * 4)
                h["y"] += (ty - h["y"]) * min(1.0, dt * 4)
            elif h["mode"] == "move":
                h["x"] += (h["tx"] - h["x"]) * min(1.0, dt * 5)
                h["y"] += (h["ty"] - h["y"]) * min(1.0, dt * 5)

    def run_final_boss(self, e, dt, dsq, bx, by):
        if e.dying:
            return
        self.hands_idle(e, dt)
        self.final_puppets_tick(e, dt, bx, by)
        ratio = e.hp / e.max_hp
        phase = 1 if ratio > 0.66 else 2 if ratio > 0.33 else 3
        if phase != getattr(e, "phase_seen", 1):
            e.phase_seen = phase
            self.show_toast("FASE %d!" % phase)
            self.shake = max(self.shake, 0.8)
            self.effects.append({"x": e.x, "y": e.y, "radius": 700, "timer": 0.7, "max_timer": 0.7, "color": (255, 80, 90)})
            sfx("boss_spawn")
            if phase == 3:
                self.start_dialog([("BOS", "Cukup! Akan kuperlihatkan wujud inflasi sejati!")], "talk_final")
        e.atk_timer -= dt * self.boss_pace()
        if not getattr(e, "queue", None):
            e.queue = [final_pick() for _ in range(2)]
        e.next_label = FINAL_LABELS.get(e.queue[0], "SERANGAN")
        if e.atk_timer > 0:
            return
        e.atk_timer = {1: 2.6, 2: 2.0, 3: 1.5}[phase]
        n = 2 if phase == 3 else 1
        d = e.dmg
        base = math.atan2(by - e.y, bx - e.x)
        for _ in range(n):
            atk = e.queue.pop(0) if e.queue else final_pick()
            e.queue.append(final_pick())
            if atk in FINAL_EXTRA_SET:
                self.final_extra(e, atk, bx, by, base, d)
            elif atk == "hand_slam":
                for h in e.hands:
                    tx, ty = bx + random.uniform(-90, 90) * (1 if h["side"] else 0), by + random.uniform(-90, 90)
                    h["mode"], h["tx"], h["ty"] = "move", tx, ty - 120
                    self.add_hazard(Hazard("blast", tx, ty, 1.1, 0.35, d * 1.4, (255, 90, 90), radius=140))
                    self.after(1.1, lambda h=h: (h.__setitem__("mode", "idle"), setattr(self, "shake", max(self.shake, 0.5)), sfx("stomp")))
                    self.after(0.9, lambda h=h, ty=ty: (h.__setitem__("ty", ty), h.__setitem__("y", h["y"])))
            elif atk == "hand_laser":
                for h in e.hands:
                    a = math.atan2(by - h["y"], bx - h["x"])
                    for k in (-1, 0, 1):
                        self.add_hazard(Hazard("beam", h["x"], h["y"], 1.2, 0.5, d * 0.9, (255, 70, 110), angle=a + k * 0.28, length=1100, width=40, spin=0.5 * k))
                sfx("warn", 0.2)
            elif atk == "meteors":
                for _i in range(14):
                    self.meteor_at(bx + random.uniform(-460, 460), by + random.uniform(-280, 280), 1.0 + random.uniform(0, 0.9), d * 0.9, 85)
                self.meteor_at(bx, by, 1.1, d * 0.9, 85)
            elif atk == "lightning":
                for _i in range(18):
                    self.sky_bolt(bx + random.uniform(-520, 520), by + random.uniform(-320, 320), 0.8 + random.uniform(0, 0.9), d * 0.8)
                self.sky_bolt(bx, by, 0.8, d * 0.8)
            elif atk == "minigun":
                for i in range(50):
                    h = e.hands[i % 2]
                    self.after(i * 0.06, lambda h=h: (not e.dead) and self.fire_minigun(
                        type("P", (), {"x": h["x"], "y": h["y"], "radius": 20})(), self.badang.x, self.badang.y, d * 0.25, 7.5, 0.08))
                sfx("warn", 0.2)
            elif atk == "sonic":
                self.add_hazard(Hazard("beam", e.x, e.y, 1.4, 0.5, d * 1.5, (70, 235, 230), angle=base, length=1500, width=130))
                sfx("warn", 0.2)
            elif atk == "rocks":
                for k in range(18):
                    a = k * math.tau / 18 + random.uniform(0, 0.3)
                    if len(self.enemy_projectiles) < 320:
                        self.enemy_projectiles.append(EnemyProjectile(e.x, e.y, e.x + math.cos(a) * 100, e.y + math.sin(a) * 100,
                                                                      4.4, d * 0.6, (135, 128, 118), 16, life=6.0, style="rock"))
                sfx("rock")
            elif atk == "rings":
                for k in range(3):
                    self.after(k * 0.7, lambda: self.add_hazard(Hazard("ring", e.x, e.y, 0.6, 1.2, d * 0.9, (255, 120, 110), max_radius=900, thickness=30)))
            elif atk == "summon":
                self.spawn_random_horde(14, e.x, e.y + 200, 10)
                wm = self.wave_multiplier()
                for _i in range(2):
                    self.enemies.append(Enemy(random.choice(TANK_POOL), wm, 0, 0, spawn_at=(e.x + random.uniform(-250, 250), e.y + 330), mode_config=self.mode_config))
                sfx("summon", 0.2)
            elif atk == "mimic":
                for k in range(3):
                    self.after(k * 0.5, lambda: (not e.dead) and self.mimic_cast(e, self.badang.x, self.badang.y))
            elif atk == "frenzy":
                for o in self.enemies:
                    if not o.dead and not o.is_boss:
                        o.haste, o.haste_mult = 8.0, 1.6
                for _i in range(6):
                    self.sky_bolt(bx + random.uniform(-300, 300), by + random.uniform(-200, 200), 0.8, d * 0.8)
                self.add_damage_text(e.x, e.y - 100, "SERANG!", (255, 190, 90), True)
            elif atk == "fire_spiral":
                for k in range(40):
                    a = k * 0.5
                    self.after(k * 0.05, lambda a=a: (not e.dead) and len(self.enemy_projectiles) < 320 and self.enemy_projectiles.append(
                        EnemyProjectile(e.x, e.y, e.x + math.cos(a) * 100, e.y + math.sin(a) * 100, 4.4, d * 0.45, (255, 130, 40), 10, life=6.0, style="fire")))
            elif atk == "gas":
                for _i in range(5):
                    self.add_hazard(Hazard("gas", bx + random.uniform(-350, 350), by + random.uniform(-220, 220), 0.7, 6.0, max(5.0, d * 0.2), (110, 205, 60), radius=125))
            else:
                for _i in range(5):
                    a = base + random.uniform(-0.5, 0.5)
                    if len(self.enemy_projectiles) < 320:
                        self.enemy_projectiles.append(EnemyProjectile(e.x, e.y, e.x + math.cos(a) * 100, e.y + math.sin(a) * 100,
                                                                      7.5, d * 0.7, (230, 235, 245), 16, life=3.0, style="spear"))
        sfx("shoot", 0.1)

    def begin_final_defeat(self, e):
        """Boss terakhir kalah: berdialog, mengeluarkan cahaya dari kedua tangan, lalu layar Victory."""
        e.dying = True
        e.hp = 1
        e.armor = 0
        self.record_kill(e)
        self.enemy_projectiles, self.hazards, self.strikes = [], [], []
        for o in self.enemies:
            if o is not e:
                o.dead = True
        self.sched = []
        sfx("boss_die")
        lines = [("BOS", "Mustahil... angka-angkaku... habis?"),
                 ("BOS", "Inflasi tak pernah berhenti, tapi kau... benar-benar kuat."),
                 ("BOS", "Terimalah... cahaya terakhirku!")]

        def after_dialog():
            hands = [(h["x"], h["y"]) for h in e.hands]
            cam_x, cam_y = self.get_camera()
            src = [(hx - cam_x, hy - cam_y) for hx, hy in hands] + [(e.x - cam_x, e.y - cam_y)]
            self.start_light(src, self.show_victory)
        self.start_dialog(lines, "talk_final", after_dialog)

    def show_victory(self):
        self.light = None
        e = getattr(self, "final_boss", None)
        if e:
            e.dead = True
        self.enemies = []
        self.victory_bonus = 3000
        self.finish_run(victory=True)
        self.unlock_badge("final")
        self.state = "victory"
        sfx("victory")

    def start_dialog(self, lines, voice="talk_boss", on_done=None, back_state="playing"):
        """lines = [(pembicara, teks), ...]. Teks diketik huruf demi huruf dengan suara tiap pembicara."""
        self.dialog = {"lines": lines, "i": 0, "chars": 0.0, "voice": voice, "on_done": on_done, "back": back_state,
                       "blip": 0, "hold": 0.0}
        self.state = "dialog"
        self.joystick_finger_id = None
        self.move_vector = (0.0, 0.0)

    def dialog_voice(self, who):
        return {"BOS": "talk_final", "API": "talk_fire", "TENGKORAK": "talk_skel", "PAHLAWAN": "talk_hero", "PEDAGANG": "talk_merchant"}.get(who, "talk_boss")

    def update_dialog(self, dt):
        d = self.dialog
        if not d:
            self.state = "playing"
            return
        who, text = d["lines"][d["i"]]
        if d["chars"] < len(text):
            d["chars"] = min(len(text), d["chars"] + dt * 34)
            n = int(d["chars"])
            if n // 2 > d["blip"] and text[max(0, n - 1)] != " ":
                d["blip"] = n // 2
                sfx(self.dialog_voice(who), 0.0)
        else:
            d["hold"] += dt

    def advance_dialog(self):
        d = self.dialog
        if not d:
            return
        text = d["lines"][d["i"]][1]
        if d["chars"] < len(text):
            d["chars"] = len(text)
            return
        d["i"] += 1
        d["chars"], d["blip"], d["hold"] = 0.0, 0, 0.0
        if d["i"] >= len(d["lines"]):
            cb, back = d["on_done"], d["back"]
            self.dialog = None
            self.state = back
            if cb:
                cb()

    def draw_dialog(self, surf):
        d = self.dialog
        if not d:
            return
        who, text = d["lines"][d["i"]]
        box = pygame.Rect(60, HEIGHT - 190, WIDTH - 120, 160)
        pygame.draw.rect(surf, (10, 8, 18), box, border_radius=14)
        pygame.draw.rect(surf, {"PAHLAWAN": (110, 200, 255), "PEDAGANG": GOLD_COLOR}.get(who, (230, 70, 80)), box, 4, border_radius=14)
        nm = font_med.render({"BOS": "RAJA INFLASI", "API": "RAJA API", "TENGKORAK": "TENGKORAK PENEMBAK", "PEDAGANG": "PEDAGANG KELILING"}.get(who, who), True, GOLD_COLOR)
        surf.blit(nm, (box.x + 24, box.y + 14))
        n = int(d["chars"])
        y = box.y + 54
        used = 0
        for line in wrap_text(text, font_med, box.width - 60)[:3]:
            if used >= n:
                break
            surf.blit(font_med.render(line[:n - used], True, WHITE), (box.x + 24, y))
            used += len(line) + 1
            y += 32
        if d["chars"] >= len(text) and int(d["hold"] * 3) % 2 == 0:
            tip = font_small.render("sentuh untuk lanjut >", True, GRAY)
            surf.blit(tip, (box.right - tip.get_width() - 20, box.bottom - 28))

    def start_light(self, sources, then):
        """Cahaya memancar dari 'sources' (posisi layar) membesar sampai MENUTUP SELURUH LAYAR, lalu 'then'."""
        self.light = {"t": 0.0, "dur": 3.4, "src": sources, "then": then}
        self.state = "light"
        sfx("light")

    def update_light(self, dt):
        L = self.light
        if not L:
            self.state = "playing"
            return
        L["t"] += dt
        if L["t"] >= L["dur"]:
            then = L["then"]
            self.light = None
            then()

    def draw_light(self, surf):
        L = self.light
        if not L:
            return
        k = min(1.0, L["t"] / (L["dur"] * 0.75))
        far = math.hypot(WIDTH, HEIGHT)
        for (sx, sy) in L["src"]:
            r = int(40 + (far + 200) * k * k)
            for j in range(4):
                rr = int(r * (1 - j * 0.18))
                col = (255, 255 - j * 12, 220 - j * 25)
                pygame.draw.circle(surf, col, (int(sx), int(sy)), max(2, rr))
            for a in range(16):
                ang = a * math.tau / 16 + L["t"] * 0.7
                pygame.draw.line(surf, (255, 255, 255), (sx, sy), (sx + math.cos(ang) * r * 1.3, sy + math.sin(ang) * r * 1.3), 6)
        if k >= 1.0:
            surf.fill((255, 255, 255))

    def avg_dps(self):
        return sum(self.dps_buckets) / len(self.dps_buckets) if self.dps_buckets else 0.0

    def dps_boss_hp(self):
        """HP boss mengikuti DPS rata-rata 10 detik terakhir, target bertarung ~25-40 dtk."""
        return int(self.avg_dps() * BOSS_DPS_UPTIME * BOSS_TARGET_FIGHT)

    def spawn_boss(self):
        """Bos lama: Bos Biasa, Penyembuh, Necromancer, Brute. Jenis dipilih menurut level pemain."""
        wm = self.wave_multiplier()
        lv = self.badang.level
        pool = [("normal", BOSS_TYPE, 1.0)]
        if lv >= 6:
            pool.append(("healer", HEALER_BOSS_TYPE, 0.9))
        if lv >= 12:
            pool.append(("necro", NECRO_BOSS_TYPE, 0.9))
        if lv >= 16:
            pool.append(("brute", BRUTE_BOSS_TYPE, 0.9))
        if lv >= 14:
            pool.append(("guardian", GUARDIAN_BOSS_TYPE, 0.9))
        if lv >= 17:
            pool.append(("minigun", MINIGUN_BOSS_TYPE, 0.9))
        if lv >= 20:
            pool.append(("exec", EXEC_BOSS_TYPE, 0.9))
        if self.mode == "inflation":
            if lv >= 10:
                pool.append(("fire", FIRE_BOSS_TYPE, 1.3))
            if lv >= 14:
                pool.append(("skel", SKEL_BOSS_TYPE, 1.3))
        cands = [p for p in pool if p[0] != self.last_old_boss] or pool
        boss_kind, kind, _w = random.choices(cands, weights=[p[2] for p in cands])[0]
        self.last_old_boss = boss_kind
        self.boss_spawn_count += 1
        e = Enemy(kind, wm, self.badang.x, self.badang.y, is_boss=True,
                  boss_scale=self.boss_kill_count, mode_config=self.mode_config)
        e.boss_kind = boss_kind
        scaled = self.dps_boss_hp()
        total = e.max_hp + e.armor_max
        if scaled > total:
            total = int(min(scaled, total * 8))
        if e.armor_max > 0:
            e.armor_max = int(total * 0.4)
            e.armor = e.armor_max
            e.max_hp = int(total * 0.6)
        else:
            e.max_hp = max(e.max_hp, total)
        e.hp = e.max_hp
        e.intro_t = 2.0
        e.atk_timer = 3.0
        if boss_kind == "minigun":
            e.stop_range = 360
        if boss_kind == "skel":
            e.stop_range = 300
        if boss_kind == "necro":
            e.stop_range = 300
        if boss_kind == "normal":
            e.is_dasher = True
            e.dash_cd = (5.0, 7.0)
            e.ability_timer = 5.0
        self.enemies.append(e)
        self.boss_active = True
        self.boss_intro = {"text": kind["name"].upper(), "sub": "Level %d" % lv, "t": 2.0}
        self.show_toast("%s muncul!" % kind["name"])
        sfx("intro")
        sfx("boss_spawn")
    def settle_enemies_for_boss(self):
        """Saat boss datang: musuh biasa jadi gem, TAPI musuh dari event tidak dihapus - mereka jadi musuh normal yang menyerang."""
        keep = []
        for e in self.enemies:
            if e.is_boss:
                keep.append(e)
            elif e.from_event and not e.dead:
                e.fixed_dir, e.life, e.no_recycle = None, None, False
                keep.append(e)
            else:
                self.add_gem(e.x, e.y, e.xp)
        return keep

    def spawn_level_boss(self, by_time=False):
        """Boss level: muncul tiap kelipatan 10 level ATAU paling lambat tiap 6 menit."""
        n = self.jsab_index
        kdef = BOSS_DEFS[n % len(BOSS_DEFS)]
        cycle = n // len(BOSS_DEFS)
        self.jsab_index += 1
        self.enemies = self.settle_enemies_for_boss()
        self.enemy_projectiles = []
        self.hazards = []
        self.strikes = []
        self.formation_warn = None
        cx, cy = self.badang.x, self.badang.y
        self.arena = {"cx": cx, "cy": cy, "hw": ARENA_HW, "hh": ARENA_HH}
        boss = LevelBoss(kdef, cycle, cx, cy - 170, self.mode_config)
        boss.by_time = by_time
        scaled = self.dps_boss_hp()
        if scaled > boss.max_hp:
            boss.max_hp = int(min(scaled, boss.max_hp * 6))
            boss.hp = boss.max_hp
        self.enemies.append(boss)
        self.level_boss = boss
        self.boss_active = True
        self.show_toast("%s: %s  (LV %d)%s" % (LEVEL_BOSS_NAME.upper(), kdef["name"], self.badang.level, "  - batas waktu" if by_time else ""))
        print("[LOG] %s #%d (%s) muncul: LV %d, waktu %s, %s" % (
            LEVEL_BOSS_NAME, self.jsab_index, kdef["name"], self.badang.level, fmt_time(int(self.time_survived)),
            "karena batas waktu" if by_time else "karena level"))
        sfx("intro")
        sfx("boss_spawn")
    def end_level_boss(self, boss):
        self.boss_active = False
        self.level_boss = None
        self.arena = None
        self.hazards = []
        self.enemy_projectiles = []
        self.jsab_kills += 1
        lvl = self.badang.level
        by_time = getattr(boss, "by_time", False)
        self.next_boss_level = max(self.next_boss_level if by_time else 0, (lvl // 10) * 10 + 10)
        self.last_jsab_time = self.time_survived
        idx = self.jsab_index - 1
        n_chest = min(8, 3 + idx // 2 + boss.cycle)
        for i in range(n_chest):
            self.add_pickup(Pickup("chest", boss.x + (i - (n_chest - 1) / 2.0) * 46, boss.y + 20))
        for _ in range(24 + min(36, idx * 4)):
            self.add_gem(boss.x + random.uniform(-90, 90), boss.y + random.uniform(-90, 90), max(1, boss.xp // 12))
        self.show_toast("%s TUMBANG!  +%d peti" % (boss.kdef["name"], n_chest))
        sfx("boss_die")
        self.save_run()
    def spawn_merchant(self):
        if self.merchants:
            return
        ang = random.uniform(0, math.tau)
        d = random.uniform(240, 330)
        self.merchants.append(Merchant(self.badang.x + math.cos(ang) * d, self.badang.y + math.sin(ang) * d,
                                       self.badang.level))
        self.show_toast("Pedagang muncul! Cari tanda $")
        sfx("merchant")

    def show_toast(self, text):
        self.toast_text = text
        self.toast_timer = 2.5

    def add_damage_text(self, x, y, text, color, big=False):
        if SETTINGS["dmgtext"] <= 0:
            return
        lim = MAX_DAMAGE_TEXTS if PERF["lod"] == 0 else (30 if PERF["lod"] == 1 else 14)
        while len(self.damage_texts) >= lim:
            del self.damage_texts[0]
        font = font_dmg_big if big else font_dmg
        surf = get_outlined_text(text, color, font)
        self.damage_texts.append([x + random.uniform(-10, 10), y, 0.7, surf])


    def damage_enemy(self, enemy, dmg, show_text=True, track=True, pierce=True):
        if enemy.dead:
            return
        if enemy.shield > 0 and not pierce:
            # Perisai musuh/boss: kebal terhadap serangan tunggal, hanya AOE/tembus yang mempan
            if len(self.effects) < 70:
                self.effects.append({"x": enemy.x, "y": enemy.y, "radius": enemy.radius + 8, "timer": 0.14, "max_timer": 0.14,
                                     "color": (150, 200, 255)})
            if time.time() - getattr(enemy, "shield_msg_at", 0.0) > 0.6:
                enemy.shield_msg_at = time.time()
                self.add_damage_text(enemy.x, enemy.y - enemy.radius - 6, "PERISAI!", (150, 200, 255), True)
                sfx("shield_up", 0.05)
            return
        if enemy.reduction > 0:
            dmg *= (1.0 - enemy.reduction)
        if enemy.dmg_in_mult != 1.0:
            dmg *= enemy.dmg_in_mult
        if self.mode == "tutorial":
            dmg *= TUT_DAMAGE_MULT
        cap = getattr(enemy, "tut_cap", 0)
        if cap:
            ad = self.avg_dps()
            if ad > cap * 1.2:
                dmg *= cap * 1.2 / ad
        if enemy.dying:
            return
        if enemy.ethereal_t > 0:
            dmg *= 0.25
        if enemy.crystal_buff in ("strong", "both"):
            dmg *= 0.85
        if self.protectors and not enemy.is_protector:
            px, py = self.badang.x, self.badang.y
            for pr in self.protectors:
                if pr is enemy or pr.dead or pr.shield <= 0:
                    continue
                ax, ay = pr.x - px, pr.y - py
                bx2, by2 = enemy.x - pr.x, enemy.y - pr.y
                dl, db = math.hypot(ax, ay), math.hypot(bx2, by2)
                if 0 < db < 200 and dl > 0 and (ax * bx2 + ay * by2) / (dl * db) > 0.6:
                    absorbed = min(pr.shield, dmg)
                    pr.shield -= absorbed
                    dmg -= absorbed
                    if len(self.effects) < 70:
                        self.effects.append({"x": enemy.x, "y": enemy.y, "radius": 14, "timer": 0.15, "max_timer": 0.15,
                                             "color": (120, 180, 255)})
                    if dmg <= 0:
                        sfx("hit", 0.07)
                        return
                    break
        if track:
            self.dmg_acc += min(dmg, enemy.hp + enemy.armor + enemy.shield)
        if show_text:
            if dmg >= 50:
                color, big = DMG_COLOR_BIG, True
            elif dmg >= 20:
                color, big = DMG_COLOR_MID, False
            else:
                color, big = DMG_COLOR_SMALL, False
            self.add_damage_text(enemy.x, enemy.y - enemy.radius - 6,
                                 str(max(1, int(round(dmg)))), color, big)
            sfx("hit", 0.07)
        had_armor = enemy.armor > 0
        if enemy.shield > 0:
            absorbed = min(enemy.shield, dmg)
            enemy.shield -= absorbed
            dmg -= absorbed
            if enemy.shield <= 0:
                self.add_damage_text(enemy.x, enemy.y - enemy.radius - 14, "PERISAI HANCUR!", (255, 220, 120), True)
                if len(self.effects) < 70:
                    self.effects.append({"x": enemy.x, "y": enemy.y, "radius": enemy.radius + 40, "timer": 0.35, "max_timer": 0.35,
                                         "color": (255, 230, 150)})
            if dmg <= 0:
                return
        if enemy.armor > 0:
            absorbed = min(enemy.armor, dmg)
            enemy.armor -= absorbed
            remaining = dmg - absorbed
            if remaining > 0:
                enemy.hp -= remaining
        else:
            enemy.hp -= dmg
        if had_armor and enemy.armor <= 0 and enemy.armor_max > 0 and not enemy.is_boss:
            self.add_damage_text(enemy.x, enemy.y - enemy.radius - 12, "ARMOR PECAH!", (200, 205, 225), True)
        if enemy.is_mother and enemy.hp > 0 and enemy.mother_cd <= 0 and not enemy.dead:
            self.mother_birth(enemy)
        if enemy.hp <= 0:
            self.kill_enemy(enemy)

    def kill_enemy(self, enemy):
        if enemy.boss_kind == "final":
            if not enemy.dying:
                self.begin_final_defeat(enemy)
            return
        if enemy.heads > 1 and not enemy.dying:
            enemy.heads = 1
            enemy.hp = enemy.max_hp * 0.55
            enemy.armor = enemy.armor_max * 0.4
            enemy.speed *= 1.3
            enemy.dmg *= 1.5
            enemy.enraged = True
            self.add_gem(enemy.x, enemy.y, max(1, enemy.xp // 3))
            self.effects.append({"x": enemy.x, "y": enemy.y, "radius": 110, "timer": 0.4, "max_timer": 0.4, "color": (255, 70, 50)})
            self.add_damage_text(enemy.x, enemy.y - enemy.radius - 24, "KEPALA PUTUS! MENGAMUK!", (255, 90, 70), True)
            sfx("boom", 0.2)
            return
        self.record_kill(enemy)
        enemy.dead = True
        sfx("die", 0.05)
        self.add_gem(enemy.x, enemy.y, enemy.xp)
        self.gold_frac = getattr(self, "gold_frac", 0.0) + enemy.gold * self.gold_gain_mult
        _g = int(self.gold_frac)
        self.gold += _g
        self.gold_frac -= _g
        self.kills += 1
        wm = self.wave_multiplier()

        child, n_child = enemy.kind.get("split_child"), enemy.kind.get("split_n", 2)
        if enemy.kind.get("splits"):
            child, n_child = SPLIT_CHILD_TYPE, 2
        if child is not None:
            for _ in range(n_child):
                if len(self.enemies) >= MAX_ENEMIES + 30:
                    break
                off = (random.uniform(-22, 22), random.uniform(-22, 22))
                self.enemies.append(Enemy(child, wm, 0, 0, spawn_at=(enemy.x + off[0], enemy.y + off[1]),
                                          mode_config=self.mode_config))

        if enemy.kind.get("explodes"):
            er = enemy.kind.get("explode_radius", 90)
            self.effects.append({"x": enemy.x, "y": enemy.y, "radius": er,
                                 "timer": 0.3, "max_timer": 0.3, "color": FIRE_COLOR})
            sfx("boom", 0.1)
            if dist_sq(enemy.x, enemy.y, self.badang.x, self.badang.y) <= er ** 2:
                self.badang.take_damage(enemy.kind.get("explode_damage", 18))
            gas = enemy.kind.get("gas")
            if gas:
                self.add_hazard(Hazard("gas", enemy.x, enemy.y, 0.25, gas[1], max(4.0, enemy.dmg * 0.3),
                                       enemy.kind.get("gas_col", (110, 205, 60)), radius=gas[0]))
                sfx("gas", 0.2)

        if random.random() < min(1.0, enemy.pickup_chance * 1.8):
            kind = random.choice(PICKUP_DROP_KINDS)
            self.add_pickup(Pickup(kind, enemy.x, enemy.y))

        if enemy.is_boss:
            if enemy.boss_kind == "jsab":
                try:
                    self.unlock_badge("lvb_%d" % BOSS_DEFS.index(enemy.kdef))
                except ValueError:
                    pass
                self.end_level_boss(enemy)
                return
            self.boss_active = False
            self.boss_intro = None
            self.boss_kill_count += 1
            if self.mode == "tutorial":
                if enemy.kind.get("robot_final"):
                    for o in self.enemies:
                        if o is not enemy:
                            o.dead = True
                    self.enemy_projectiles, self.hazards = [], []
                    sfx("boss_die")
                    self.start_dialog(MERCHANT_LINES["ending"], "talk_merchant", self.tutorial_victory)
                else:
                    self.tut["mini_dead"] = True
                    for _i in range(8):
                        self.add_gem(enemy.x + random.uniform(-35, 35), enemy.y + random.uniform(-35, 35), max(1, enemy.xp // 4))
                    sfx("boss_die")
                return
            self.unlock_badge(enemy.boss_kind)
            n = min(6, 1 + enemy.reward + self.boss_kill_count // 3)
            for i in range(n):
                self.add_pickup(Pickup("chest", enemy.x + (i - (n - 1) / 2.0) * 40, enemy.y))
            sfx("boss_die")
            for _ in range(6 + 2 * n):
                gx = enemy.x + random.uniform(-35, 35)
                gy = enemy.y + random.uniform(-35, 35)
                self.add_gem(gx, gy, max(1, enemy.xp // 4))
            if enemy.boss_kind == "necro":
                for o in self.enemies:
                    if o.kind is GSKEL_TYPE and not o.dead:
                        o.dead = True
            self.show_toast("%s tumbang!  +%d peti" % (enemy.kind["name"], n))
    # ---------- Status BAKAR / RACUN / UAP ----------
    def ignite_enemy(self, e, dps, dur=3.0):
        """Bakar musuh. Kalau musuh sedang beku, es meleleh jadi UAP: tidak terbakar, tapi kena damage."""
        if e.dead or e.dying:
            return
        if e.frozen_timer > 0 and not e.ice_immune:
            e.frozen_timer = 0.0
            e.steam_dmg = max(e.steam_dmg, 8.0, dps * 4.0)
            e.steam_t = 0.7
            return
        e.burn_t = max(e.burn_t, dur)
        e.burn_dps = max(e.burn_dps, dps)

    def poison_enemy(self, e, dps, dur=4.0):
        if e.dead or e.dying:
            return
        e.poison_t = max(e.poison_t, dur)
        e.poison_dps = max(e.poison_dps, dps)

    def update_statuses(self, dt):
        """Tick damage bakar/racun musuh + damage uap (api bertemu es) + status pemain."""
        for e in self.enemies:
            if e.dead:
                continue
            if e.steam_dmg > 0:
                d, e.steam_dmg = e.steam_dmg, 0.0
                self.damage_enemy(e, d, show_text=True)
                if len(self.effects) < 70:
                    self.effects.append({"x": e.x, "y": e.y, "radius": e.radius + 14, "timer": 0.3, "max_timer": 0.3,
                                         "color": (225, 235, 245)})
                if e.dead:
                    continue
            if e.steam_t > 0:
                e.steam_t -= dt
            if e.burn_t > 0:
                e.burn_t -= dt
                e.burn_tick -= dt
                if e.burn_tick <= 0:
                    e.burn_tick = 0.5
                    self.damage_enemy(e, max(1.0, e.burn_dps * 0.5), show_text=e.burn_dps * 0.5 >= 4, pierce=True)
                    if e.burn_t <= 0:
                        e.burn_dps = 0.0
                if e.dead:
                    continue
            if e.poison_t > 0:
                e.poison_t -= dt
                e.poison_tick -= dt
                if e.poison_tick <= 0:
                    e.poison_tick = 0.5
                    self.damage_enemy(e, max(1.0, e.poison_dps * 0.5), show_text=e.poison_dps * 0.5 >= 4, pierce=True)
                    if e.poison_t <= 0:
                        e.poison_dps = 0.0
        b = self.badang
        b.update_statuses(dt, self)

    def add_gem(self, x, y, amount):
        """Tambah orb XP. Orb yang berdekatan digabung dan jumlah orb dibatasi (XP tidak hilang): dulu orb yang tak diambil
        menumpuk tanpa batas selama permainan = penyebab lag yang makin parah."""
        gems = self.gems
        amount = max(1, int(amount))
        best, bd = None, GEM_MERGE_R2
        for g in gems[-48:]:
            if not g.pulled:
                d = dist_sq(g.x, g.y, x, y)
                if d < bd:
                    best, bd = g, d
        if best is not None:
            best.amount += amount
            return
        gems.append(XPGem(x, y, amount))
        if len(gems) > MAX_GEMS:
            bx, by = self.badang.x, self.badang.y
            far, fd = None, -1.0
            for g in gems[:-1]:
                d = dist_sq(g.x, g.y, bx, by)
                if d > fd:
                    far, fd = g, d
            if far is not None:
                gems.remove(far)
                gems[-1].amount += far.amount

    def add_pickup(self, pk):
        pks = self.pickups
        pks.append(pk)
        if len(pks) > MAX_PICKUPS:
            for i, o in enumerate(pks[:-1]):
                if o.kind not in ("chest", "hporb"):
                    del pks[i]
                    return
            for i, o in enumerate(pks[:-1]):
                if o.kind != "hporb":
                    del pks[i]
                    return

    def add_hazard(self, hz):
        if len(self.hazards) < 90:
            self.hazards.append(hz)

    def boss_tell_label(self, e):
        """Nama serangan boss berikutnya / yang sedang disiapkan (untuk pertanda di layar)."""
        k, st = e.boss_kind, e.bstate
        by_state = {"punch_wind": "TINJU!", "stomp_wind": "HENTAKAN!", "throw": "LEMPAR!", "leap_wind": "LOMPAT!", "mg_spin": "MINIGUN!",
                    "bag_open": "TAS MINIGUN!", "rev": "REVOLVER!", "cleave": "TEBASAN!", "thrust": "TOMBAK!", "raise": "METEOR!",
                    "charge": "SONIC BOOM!", "smash": "HANTAMAN!", "slam_wind": "PALU!", "slash_wind": "TEBASAN!", "aim": "TEMBAKAN!"}
        if st in by_state:
            return by_state[st]
        i = e.atk_index
        tbl = {"guardian": ["TOMBAK LURUS", "HUJAN METEOR", "PETIR LANGIT", "PANGGIL PASUKAN", "LEMPAR TOMBAK", "HENTAKAN"],
               "minigun": ["MINIGUN", "MINIGUN", "GRANAT", "MINIGUN", "MINIGUN", "GRANAT"],
               "exec": ["LEMPAR KAPAK", "TEBASAN LEBAR", "HUKUMAN", "LEMPAR KAPAK", "HENTAKAN"],
               "fire": ["KIPAS API", "TIANG API", "CINCIN API", "KOLAM API"] + (["SINAR API", "SPIRAL API"] if e.form == "blue" else []),
               "skel": ["REVOLVER", "TAS MINIGUN", "DINAMIT", "REVOLVER", "PANGGIL TENGKORAK", "TAS MINIGUN"],
               "healer": ["TEMBAKAN", "PANGGIL KELELAWAR", "HUJAN RACUN", "CINCIN PELURU"],
               "necro": ["PELURU SIHIR", "HUJAN SIHIR", "PANGGIL KERANGKA", "KUTUKAN SINAR"],
               "normal": ["CINCIN PELURU", "KIPAS PELURU"] + (["GELOMBANG", "CINCIN PELURU"] if (self.boss_kill_count >= 1 or e.enraged) else [])}
        if k == "final":
            return getattr(e, "next_label", None)
        lst = tbl.get(k)
        return lst[i % len(lst)] if lst else None

    def boss_pace(self):
        """Boss yang muncul saat level pemain masih kecil menyerang lebih pelan & jarang (menyesuaikan kondisi pemain).
        LV<=5 -> 0.55, naik linear sampai 1.0 di LV 30. HP pemain di bawah 35% -> sedikit lebih pelan lagi."""
        b = self.badang
        p = 0.55 + 0.45 * min(1.0, max(0.0, (b.level - 5) / 25.0))
        if b.hp < 0.35 * b.max_hp:
            p *= 0.85
        return max(0.45, min(1.0, p))

    def update_boss_tells(self):
        for e in self.enemies:
            if not e.is_boss or e.boss_kind in ("jsab",) or e.dead:
                continue
            if e.intro_t > 0 or e.dying:
                e.tell = None
                continue
            lab = self.boss_tell_label(e)
            soon = e.atk_timer <= 1.0 or e.bstate is not None
            new = lab if (lab and soon) else None
            if new and new != e.tell:
                sfx("warn", 0.25)
            e.tell = new

    def mother_birth(self, e):
        """Raksasa Induk: TIAP KALI TERLUKA melahirkan 3 Raksasa Induk Mini dan memulihkan diri."""
        e.mother_cd = 0.9
        wm = self.wave_multiplier()
        cap = self.enemy_cap() + 25
        e.mother_n = min(6, e.mother_n + 1)
        e.hp = min(e.max_hp, e.hp + e.max_hp * 0.09)
        for _ in range(3):
            if len(self.enemies) < cap:
                a = random.uniform(0, math.tau)
                self.enemies.append(Enemy(MOTHER_MINI_TYPE, wm, 0, 0, spawn_at=(e.x + math.cos(a) * e.radius, e.y + math.sin(a) * e.radius), mode_config=self.mode_config))
        if len(self.effects) < 70:
            self.effects.append({"x": e.x, "y": e.y, "radius": 110, "timer": 0.4, "max_timer": 0.4, "color": (255, 130, 170)})
        self.add_damage_text(e.x, e.y - e.radius - 18, "MELAHIRKAN!", (255, 150, 190), True)
        sfx("summon", 0.2)

    def healer_pulse(self, e):
        """Bos Penyembuh menyembuhkan DIRINYA dan semua musuh di sekitarnya (termasuk boss lain)."""
        hr2 = e.heal_radius ** 2
        texts = 0
        amt = max(e.heal_amount, e.max_hp * 0.03)
        before = e.hp
        e.hp = min(e.max_hp, e.hp + amt)
        if e.hp > before:
            self.add_damage_text(e.x, e.y - e.radius - 16, "+%d" % int(e.hp - before), DMG_COLOR_HEAL, True)
        for o in self.enemies:
            if o is e or o.dead or o.boss_kind == "jsab":
                continue
            if dist_sq(o.x, o.y, e.x, e.y) <= hr2:
                before = o.hp
                o.hp = min(o.max_hp, o.hp + max(e.heal_amount * 0.5, o.max_hp * 0.10))
                if o.hp > before:
                    if texts < 6:
                        texts += 1
                        self.add_damage_text(o.x, o.y - o.radius - 10, "+%d" % int(o.hp - before), DMG_COLOR_HEAL)
                    if len(self.effects) < 70:
                        self.effects.append({"x": e.x, "y": e.y, "radius": 0, "timer": 0.35, "max_timer": 0.35,
                                             "color": (110, 255, 160), "bolt": (e.x, e.y, o.x, o.y)})
        self.effects.append({"x": e.x, "y": e.y, "radius": e.heal_radius, "timer": 0.6, "max_timer": 0.6,
                             "color": (80, 220, 120)})
        sfx("heal_big", 0.3)

    def fire_minigun(self, e, bx, by, dmg, speed=7.0, spread=0.09, color=(255, 210, 90), r=4):
        if len(self.enemy_projectiles) >= 320:
            return
        a = math.atan2(by - e.y, bx - e.x) + random.uniform(-spread, spread)
        ex, ey = e.x + math.cos(a) * e.radius, e.y + math.sin(a) * e.radius
        self.enemy_projectiles.append(EnemyProjectile(ex, ey, ex + math.cos(a) * 100, ey + math.sin(a) * 100,
                                                      speed, dmg, color, r, life=1.5))

    def mimic_cast(self, e, bx, by):
        """Peniru Sihir menirukan SKILL PEMAIN secara acak."""
        d = e.dmg
        base = math.atan2(by - e.y, bx - e.x)
        pick = random.choice(["Bola Energi", "Panah", "Duri Es", "Pisau Terbang", "Bola Api", "Gelombang Kejut", "Laser",
                              "Meteor", "Awan Racun", "Petir Langit", "Angin Puyuh", "Roh Pemburu", "Bumerang", "Aura Maut",
                              "Petir Rantai"])

        def shot(ang, spd, dm, col, rad, style, life=6.0):
            if len(self.enemy_projectiles) < 320:
                self.enemy_projectiles.append(EnemyProjectile(e.x, e.y, e.x + math.cos(ang) * 100, e.y + math.sin(ang) * 100,
                                                              spd, dm, col, rad, life=life, style=style))
        if pick == "Bola Energi":
            shot(base, 4.6, d * 0.6, ORB_COLOR, 9, "orb")
        elif pick == "Panah":
            for a in fan_angles(base, 3, 9):
                shot(a, 6.0, d * 0.45, ARROW_COLOR, 6, "arrow")
        elif pick == "Duri Es":
            shot(base, 5.2, d * 0.6, (170, 225, 255), 8, "ice")
        elif pick == "Pisau Terbang":
            for k in range(5):
                shot(base + (k - 2) * 0.07, 7.5, d * 0.35, (230, 232, 245), 6, "knife", 1.4)
        elif pick == "Bola Api":
            for a in fan_angles(base, 2, 10):
                shot(a, 4.4, d * 0.7, FIRE_COLOR, 11, "fire")
        elif pick == "Gelombang Kejut":
            self.add_hazard(Hazard("ring", e.x, e.y, 0.5, 0.9, d * 0.8, SHOCK_COLOR, max_radius=330, thickness=22))
        elif pick == "Laser":
            self.add_hazard(Hazard("beam", e.x, e.y, 0.8, 0.3, d * 0.9, (255, 60, 100), angle=base, length=900, width=26))
        elif pick == "Meteor":
            self.add_hazard(Hazard("blast", bx, by, 1.2, 0.3, d * 1.2, (255, 140, 40), radius=85))
        elif pick == "Awan Racun":
            self.add_hazard(Hazard("gas", bx, by, 0.4, 3.5, max(3.0, d * 0.25), (110, 205, 60), radius=95))
        elif pick == "Petir Langit":
            for _ in range(3):
                self.add_hazard(Hazard("blast", bx + random.uniform(-130, 130), by + random.uniform(-100, 100), 0.9, 0.2,
                                       d * 0.9, LIGHTNING_COLOR, radius=48))
        elif pick == "Angin Puyuh":
            for k in range(3):
                shot(base + (k - 1) * 0.5, 3.4, d * 0.5, (190, 215, 235), 12, "shuriken", 4.0)
        elif pick == "Roh Pemburu":
            for k in range(2):
                if len(self.enemy_projectiles) < 320:
                    ep = EnemyProjectile(e.x, e.y, e.x + math.cos(base + (k - .5)) * 100, e.y + math.sin(base + (k - .5)) * 100,
                                         3.6, d * 0.55, (205, 175, 255), 9, life=5.0, style="spirit")
                    ep.home = 0.05
                    self.enemy_projectiles.append(ep)
        elif pick == "Bumerang":
            if len(self.enemy_projectiles) < 320:
                ax = ReturnAxe(e, bx, by, 6.0, d * 0.7, 0.7, 16)
                ax.style = "boom"
                self.enemy_projectiles.append(ax)
        elif pick == "Aura Maut":
            self.add_hazard(Hazard("blast", e.x, e.y, 0.4, 1.2, d * 0.5, AURA_COLOR, radius=110))
        else:
            for k in range(2):
                self.add_hazard(Hazard("beam", e.x, e.y, 0.6, 0.2, d * 0.7, LIGHTNING_COLOR, angle=base + (k - .5) * 0.5,
                                       length=520, width=18))
        self.add_damage_text(e.x, e.y - e.radius - 22, pick, (230, 200, 255), True)
        sfx("magic", 0.1)

    def run_new_ability(self, e, dt, dsq, bx, by):
        if e.frozen_timer > 0 or e.intro_t > 0:
            return
        dist = math.sqrt(dsq)
        base = math.atan2(by - e.y, bx - e.x)
        wm = self.wave_multiplier()
        if e.is_ethereal:
            e.ability_timer -= dt
            if e.ability_timer <= 0 and e.ethereal_t <= 0:
                e.ethereal_t = 2.5
                e.ability_timer = 6.0
                self.add_damage_text(e.x, e.y - e.radius - 14, "MENEMBUS!", (200, 230, 255))
            return
        if e.is_mother:
            if e.mother_cd > 0:
                e.mother_cd -= dt
            return
        if e.bstate is not None:
            e.bstate_t -= dt
            st = e.bstate
            if st == "charge":
                if e.bstate_t <= 0:
                    sfx("boom", 0.2)
                    e.bstate, e.busy, e.ability_timer = None, False, 4.5
            elif st == "smash":
                if e.bstate_t <= 0:
                    sfx("stomp")
                    self.shake = max(self.shake, 0.35)
                    e.bstate, e.busy, e.ability_timer = None, False, 2.6
            elif st in ("slam_wind", "slash_wind", "bash"):
                if e.bstate_t <= 0:
                    if st == "slam_wind":
                        e.bstate, e.bstate_t = "slam", 0.35
                        self.shake = max(self.shake, 0.3)
                        sfx("stomp")
                    elif st == "bash":
                        if dist <= e.radius + 120 and self.badang.take_damage(e.dmg):
                            self.badang.apply_knockback(math.cos(e.bdata["ang"]), math.sin(e.bdata["ang"]), 20)
                        e.bstate, e.busy, e.ability_timer = None, False, 4.0
                        sfx("punch")
                    else:
                        e.bstate, e.busy, e.ability_timer = None, False, 2.6
                        sfx("punch")
            elif st == "slam":
                if e.bstate_t <= 0:
                    e.bstate, e.busy, e.ability_timer = None, False, 3.2
            elif st == "aim":
                if e.bstate_t <= 0:
                    a0 = math.atan2(by - e.y, bx - e.x)
                    for a in fan_angles(a0, 9, 6):
                        if len(self.enemy_projectiles) < 320:
                            self.enemy_projectiles.append(EnemyProjectile(
                                e.x + math.cos(a0) * e.radius, e.y + math.sin(a0) * e.radius,
                                e.x + math.cos(a) * 100, e.y + math.sin(a) * 100, 7.5, e.dmg * 0.4, (255, 220, 120), 5, life=0.9))
                    sfx("boom", 0.1)
                    e.bstate, e.busy, e.ability_timer = None, False, 2.8
            elif st == "command":
                if e.bstate_t <= 0:
                    n = 0
                    for o in self.enemies:
                        if not o.dead and dist_sq(o.x, o.y, e.x, e.y) <= 380 ** 2:
                            o.haste, o.haste_mult = 5.0, 1.55
                            n += 1
                    self.effects.append({"x": e.x, "y": e.y, "radius": 380, "timer": 0.5, "max_timer": 0.5, "color": (255, 170, 70)})
                    self.add_damage_text(e.x, e.y - e.radius - 20, "SERANG!", (255, 190, 90), True)
                    sfx("summon", 0.2)
                    e.bstate, e.busy, e.ability_timer = None, False, 5.5
            elif st == "spin":
                if e.bstate_t <= 0:
                    e.bstate, e.bstate_t, e.bdata = "fire", 1.8, {"cd": 0.0}
            elif st == "fire":
                e.bdata["cd"] -= dt
                while e.bdata["cd"] <= 0:
                    e.bdata["cd"] += 0.07
                    self.fire_minigun(e, bx, by, e.dmg * 0.35)
                if e.bstate_t <= 0:
                    e.bstate, e.ability_timer = None, 3.2
            elif st == "reap":
                if e.bstate_t <= 0:
                    alive = sum(1 for o in self.enemies if o.kind in TANK_POOL and not o.dead)
                    for _ in range(random.choice((1, 2))):
                        if alive < 8 and len(self.enemies) < MAX_ENEMIES + 30:
                            a = random.uniform(0, math.tau)
                            self.enemies.append(Enemy(random.choice(TANK_POOL), wm, 0, 0,
                                                      spawn_at=(e.x + math.cos(a) * 80, e.y + math.sin(a) * 80),
                                                      mode_config=self.mode_config))
                            alive += 1
                    self.effects.append({"x": e.x, "y": e.y, "radius": 120, "timer": 0.5, "max_timer": 0.5, "color": (150, 110, 220)})
                    sfx("summon", 0.2)
                    e.bstate, e.busy, e.ability_timer = None, False, 8.0
            return
        e.ability_timer -= dt
        if e.ability_timer > 0:
            return
        if e.is_warden:
            if dist <= 150:
                e.bstate, e.bstate_t, e.busy = "smash", 0.5, True
                self.add_hazard(Hazard("blast", e.x, e.y, 0.5, 0.25, e.dmg * 1.2, (60, 220, 215), radius=135))
            elif dist <= 700:
                e.bstate, e.bstate_t, e.busy = "charge", 1.1, True
                self.add_hazard(Hazard("beam", e.x, e.y, 1.1, 0.4, e.dmg, (70, 235, 230), angle=base, length=850, width=58))
                sfx("warn", 0.2)
            else:
                e.ability_timer = 1.0
        elif e.is_mimic:
            e.ability_timer = random.uniform(2.6, 3.4)
            self.mimic_cast(e, bx, by)
        elif e.is_hammer:
            if dist <= 280:
                e.bstate, e.bstate_t, e.busy = "slam_wind", 0.7, True
                e.bdata = {"ang": base}
                self.add_hazard(Hazard("blast", e.x + math.cos(base) * 100, e.y + math.sin(base) * 100, 0.7, 0.25,
                                       e.dmg * 1.2, (255, 130, 70), radius=115))
                sfx("warn", 0.2)
            elif dist <= 520:
                e.ability_timer = 4.5
                self.add_hazard(Hazard("ring", e.x, e.y, 0.8, 1.0, e.dmg * 0.8, (255, 130, 70), max_radius=330, thickness=22))
                sfx("stomp", 0.2)
            else:
                e.ability_timer = 1.0
        elif e.is_slash:
            if dist <= 260:
                e.bstate, e.bstate_t, e.busy = "slash_wind", 0.55, True
                self.add_hazard(Hazard("beam", e.x, e.y, 0.55, 0.18, e.dmg * 1.1, (235, 240, 255), angle=base, length=240, width=115))
                sfx("warn", 0.2)
            else:
                e.ability_timer = 0.8
        elif e.is_protector:
            if dist <= e.radius + 110:
                e.bstate, e.bstate_t, e.busy, e.bdata = "bash", 0.5, True, {"ang": base}
                self.add_hazard(Hazard("blast", e.x + math.cos(base) * 60, e.y + math.sin(base) * 60, 0.5, 0.15, 0,
                                       (150, 190, 255), radius=100))
            else:
                e.ability_timer = 0.8
        elif e.is_crystal:
            e.ability_timer = random.uniform(5.0, 6.5)
            cands = [o for o in self.enemies if o is not e and not o.dead and not o.is_boss and not o.crystal_buff
                     and not o.is_crystal and dist_sq(o.x, o.y, bx, by) <= 750 ** 2]
            if cands:
                t = random.choice(cands)
                buff = random.choice(["strong", "fast", "both"])
                t.crystal_buff = buff
                if buff in ("strong", "both"):
                    t.dmg *= 1.6
                    t.max_hp = int(t.max_hp * 1.3)
                    t.hp = min(t.max_hp, t.hp + t.max_hp * 0.3)
                if buff in ("fast", "both"):
                    t.speed *= 1.55
                label = {"strong": "KUAT!", "fast": "CEPAT!", "both": "KUAT + CEPAT!"}[buff]
                col = {"strong": (255, 90, 80), "fast": (255, 230, 90), "both": (210, 110, 255)}[buff]
                self.add_damage_text(t.x, t.y - t.radius - 18, label, col, True)
                if len(self.effects) < 70:
                    self.effects.append({"x": e.x, "y": e.y, "radius": 0, "timer": 0.4, "max_timer": 0.4, "color": col, "bolt": (e.x, e.y, t.x, t.y)})
                sfx("magic", 0.1)
        elif e.is_shotgun:
            if 100 < dist <= 520:
                e.bstate, e.bstate_t, e.busy = "aim", 0.6, True
                sfx("warn", 0.2)
            else:
                e.ability_timer = 0.8
        elif e.is_chief:
            e.bstate, e.bstate_t = "command", 0.5
            sfx("warn", 0.2)
        elif e.is_minigunner:
            if dist <= 720:
                e.bstate, e.bstate_t = "spin", 0.9
                sfx("warn", 0.2)
            else:
                e.ability_timer = 1.0
        elif e.is_reaper:
            e.bstate, e.bstate_t, e.busy = "reap", 0.7, True
            self.effects.append({"x": e.x, "y": e.y, "radius": 90, "timer": 0.7, "max_timer": 0.7, "color": (120, 90, 200)})

    def run_elem_ability(self, e, dt, dsq, bx, by):
        if e.frozen_timer > 0 or e.intro_t > 0:
            return
        ab = e.kind["abil"]
        if e.abil_t is None:
            e.abil_t = [random.uniform(0.4, a["cd"][1]) for a in ab]
        dist = math.sqrt(dsq)
        base = math.atan2(by - e.y, bx - e.x)
        for i, a in enumerate(ab):
            e.abil_t[i] -= dt
            if e.abil_t[i] > 0:
                continue
            e.abil_t[i] = random.uniform(*a["cd"])
            if a.get("range") and dist > a["range"]:
                e.abil_t[i] = 0.5
                continue
            t, col, d, slow = a["t"], a.get("col", EL_COL.get(e.kind.get("elem"), WHITE)), e.dmg * a.get("dm", 0.6), a.get("slow", False)
            if t == "trail":
                if sum(1 for h_ in self.hazards if h_.kind == "gas") > 26:
                    continue
                self.add_hazard(Hazard("gas", e.x, e.y, 0.05, a.get("dur", 3.0), max(2.0, d), col, radius=a.get("r", 40), slow=slow))
            elif t == "aura":
                cur = getattr(e, "aura_h", None)
                if cur is not None and cur.alive and cur in self.hazards:
                    if cur.phase == "active":
                        cur.t = max(cur.t, a.get("dur", 2.0))   # aura yang sama diperpanjang, tidak ditumpuk
                else:
                    hz = Hazard("gas", e.x, e.y, 0.1, a.get("dur", 2.0), max(2.0, d), col, radius=a["r"], slow=slow, follow=e, aura=True)
                    e.aura_h = hz
                    self.add_hazard(hz)
            elif t == "spit":
                self.add_hazard(Hazard("gas", bx, by, 0.5, a.get("dur", 3.0), max(2.0, d), col, radius=a["r"], slow=slow))
                sfx("gas", 0.2)
            elif t == "shoot":
                for ang in fan_angles(base, a.get("n", 1), a.get("sp", 10)):
                    if len(self.enemy_projectiles) < 320:
                        ep = EnemyProjectile(e.x, e.y, e.x + math.cos(ang) * 100, e.y + math.sin(ang) * 100, a.get("spd", 4.5),
                                             e.dmg * 0.5, col, a.get("r", 8), life=6.0, style=a.get("style"))
                        ep.slow = slow
                        self.enemy_projectiles.append(ep)
                sfx("shoot", 0.1)
            elif t == "nova":
                self.add_hazard(Hazard("ring", e.x, e.y, 0.5, 1.0, d, col, max_radius=a["r"], thickness=24, slow=slow))
                sfx("warn", 0.2)
            elif t == "bolt":
                for k in range(a.get("n", 1)):
                    sp = a.get("spread", 0)
                    self.sky_bolt(bx + (random.uniform(-sp, sp) if k else 0), by + (random.uniform(-sp, sp) if k else 0), a.get("warn", 0.85), d)
            elif t == "lob":
                for k in range(a.get("n", 1)):
                    sp = a.get("spread", 0)
                    self.meteor_at(bx + (random.uniform(-sp, sp) if k else 0), by + (random.uniform(-sp, sp) if k else 0),
                                   a.get("warn", 1.2) + random.uniform(0, 0.4), d, a.get("r", 80), col)
            elif t == "cone":
                n = a.get("n", 3)
                for k in range(n):
                    self.add_hazard(Hazard("beam", e.x, e.y, 0.6, 0.4, d, col, angle=base + (k - (n - 1) / 2.0) * 0.38,
                                           length=a.get("length", 260), width=a.get("width", 60)))
                sfx("warn", 0.2)
            elif t == "beam":
                self.add_hazard(Hazard("beam", e.x, e.y, a.get("warn", 0.7), 0.3, d, col, angle=base, length=a.get("length", 480), width=a.get("width", 24)))
                sfx("warn", 0.2)
            elif t == "roll":
                e.haste, e.haste_mult = 1.8, 3.2
                self.add_damage_text(e.x, e.y - e.radius - 14, "MENGGULUNG!", (200, 190, 160))
            elif t == "ring":
                n = a.get("n", 12)
                off = random.uniform(0, 1)
                for k in range(n):
                    ang = off + k * math.tau / n
                    if len(self.enemy_projectiles) < 320:
                        ep = EnemyProjectile(e.x, e.y, e.x + math.cos(ang) * 100, e.y + math.sin(ang) * 100, a.get("spd", 4.0), e.dmg * 0.4,
                                             col, a.get("r", 8), life=6.0, style=a.get("style"))
                        self.enemy_projectiles.append(ep)
                sfx("shoot", 0.1)
            elif t == "blink":
                ang = random.uniform(0, math.tau)
                dd = a.get("d", 280)
                if len(self.effects) < 70:
                    self.effects.append({"x": e.x, "y": e.y, "radius": 60, "timer": 0.3, "max_timer": 0.3, "color": (170, 120, 230)})
                e.x, e.y = bx + math.cos(ang) * dd, by + math.sin(ang) * dd
                if len(self.effects) < 70:
                    self.effects.append({"x": e.x, "y": e.y, "radius": 70, "timer": 0.35, "max_timer": 0.35, "color": (200, 160, 255)})
                sfx("warn", 0.2)
            elif t == "summon":
                kind = KIND_BY_NAME.get(a.get("kind"))
                if kind is not None:
                    alive = sum(1 for o in self.enemies if o.kind is kind and not o.dead)
                    for k in range(a.get("n", 2)):
                        if alive < 8 and len(self.enemies) < self.enemy_cap() + 20:
                            ang = random.uniform(0, math.tau)
                            self.enemies.append(Enemy(kind, self.wave_multiplier(), 0, 0, spawn_at=(e.x + math.cos(ang) * (e.radius + 30), e.y + math.sin(ang) * (e.radius + 30)),
                                                      mode_config=self.mode_config))
                            alive += 1
                    self.effects.append({"x": e.x, "y": e.y, "radius": 110, "timer": 0.4, "max_timer": 0.4, "color": col})
                    sfx("summon", 0.2)
            elif t == "healaoe":
                hr2 = a.get("r", 300) ** 2
                for o in self.enemies:
                    if not o.dead and o.boss_kind != "jsab" and dist_sq(o.x, o.y, e.x, e.y) <= hr2:
                        o.hp = min(o.max_hp, o.hp + o.max_hp * a.get("pct", 0.1))
                self.effects.append({"x": e.x, "y": e.y, "radius": a.get("r", 300), "timer": 0.5, "max_timer": 0.5, "color": (110, 255, 160)})
                sfx("heal_big", 0.3)

    def run_enemy_abilities(self, e, dt, dsq, bx, by):
        if e.has_elem:
            self.run_elem_ability(e, dt, dsq, bx, by)
            return
        if e.has_new:
            self.run_new_ability(e, dt, dsq, bx, by)
            return
        if not (e.is_teleporter or e.is_laser or e.is_ninja or e.is_bomber or e.is_sniper
                or e.is_buffer or e.is_toxic or e.is_slam or e.is_thunder):
            return
        if e.frozen_timer > 0:
            return
        e.ability_timer -= dt
        if e.ability_timer > 0:
            return
        if e.is_teleporter:
            e.ability_timer = random.uniform(3.5, 5.5)
            a, d = random.uniform(0, math.tau), random.uniform(170, 260)
            self.effects.append({"x": e.x, "y": e.y, "radius": 40, "timer": 0.25, "max_timer": 0.25,
                                 "color": (170, 245, 245)})
            e.x, e.y = bx + math.cos(a) * d, by + math.sin(a) * d
            sfx("teleport", 0.1)
        elif e.is_laser:
            if dsq < 640 ** 2:
                e.ability_timer = 5.0
                ang = math.atan2(by - e.y, bx - e.x)
                self.add_hazard(Hazard("beam", e.x, e.y, 0.9, 0.25, e.dmg * 1.3, (255, 60, 110),
                                       angle=ang, length=900, width=20))
                sfx("charge", 0.3)
            else:
                e.ability_timer = 0.5
        elif e.is_ninja:
            if dsq < 560 ** 2 and len(self.enemy_projectiles) < MAX_ENEMY_PROJECTILES:
                e.ability_timer = 3.2
                base = math.atan2(by - e.y, bx - e.x)
                for ang in fan_angles(base, 3, 14):
                    self.enemy_projectiles.append(EnemyProjectile(
                        e.x, e.y, e.x + math.cos(ang) * 100, e.y + math.sin(ang) * 100, 4.5, e.dmg * 0.6,
                        (205, 205, 225), 5))
            else:
                e.ability_timer = 0.5
        elif e.is_bomber:
            if dsq < 660 ** 2:
                e.ability_timer = 4.5
                self.add_hazard(Hazard("blast", bx, by, 1.1, 0.25, e.dmg * 1.6, (255, 170, 60), radius=85))
                sfx("warn", 0.2)
            else:
                e.ability_timer = 0.5
        elif e.is_sniper:
            if dsq < 820 ** 2 and len(self.enemy_projectiles) < MAX_ENEMY_PROJECTILES:
                e.ability_timer = 5.5
                self.enemy_projectiles.append(EnemyProjectile(e.x, e.y, bx, by, 9.0, e.dmg * 1.6,
                                                              (120, 255, 120), 8))
                sfx("shoot", 0.1)
            else:
                e.ability_timer = 0.5
        elif e.is_thunder:
            e.ability_timer = random.uniform(3.5, 5.0)
            r2 = 230 ** 2
            group = [e] + [o for o in self.enemies if o is not e and not o.dead and not o.is_boss
                           and dist_sq(o.x, o.y, e.x, e.y) <= r2][:13]
            for o in group:
                o.haste = 4.5
                o.haste_mult = 1.75
                if len(self.effects) < 70:
                    self.effects.append({"x": o.x, "y": o.y, "radius": 0, "timer": 0.3, "max_timer": 0.3,
                                         "color": LIGHTNING_COLOR, "bolt": (o.x + random.uniform(-14, 14), o.y - 260, o.x, o.y)})
                    if o is not e:
                        self.effects.append({"x": o.x, "y": o.y, "radius": 0, "timer": 0.25, "max_timer": 0.25,
                                             "color": (255, 240, 110), "bolt": (e.x, e.y, o.x, o.y)})
            self.effects.append({"x": e.x, "y": e.y, "radius": 230, "timer": 0.35, "max_timer": 0.35,
                                 "color": (255, 240, 110)})
            sfx("thunder", 0.1)
        elif e.is_buffer:
            e.ability_timer = 1.0
            r2 = 220 ** 2
            for o in self.enemies:
                if o is not e and not o.dead and not o.is_boss and dist_sq(o.x, o.y, e.x, e.y) <= r2:
                    o.haste = 1.5
                    o.hp = min(o.max_hp, o.hp + o.max_hp * 0.03)
        elif e.is_toxic:
            e.ability_timer = 1.6
            self.add_hazard(Hazard("blast", e.x, e.y, 0.35, 3.0, e.dmg * 0.5, (130, 225, 60), radius=45))
        elif e.is_slam:
            if dsq < 380 ** 2:
                e.ability_timer = 6.0
                self.add_hazard(Hazard("ring", e.x, e.y, 0.8, 0.6, e.dmg * 1.2, (170, 170, 200),
                                       max_radius=300, thickness=28))
                sfx("warn", 0.2)
            else:
                e.ability_timer = 0.5

    def run_old_boss(self, e, dt, dsq, bx, by):
        """Pola serangan Bos Biasa, Penyembuh, Necromancer, dan Brute Berkepala Dua."""
        kind = e.boss_kind
        if kind == "final":
            if e.intro_t <= 0:
                self.run_final_boss(e, dt, dsq, bx, by)
            return
        if kind not in ("normal", "healer", "necro", "brute", "guardian", "minigun", "exec", "fire", "skel") or e.intro_t > 0:
            return
        enraged = e.hp < e.max_hp * 0.5
        if enraged and not e.enraged:
            e.enraged = True
            e.speed *= 1.3
            self.show_toast("BOS MENGAMUK!")
            sfx("boss_spawn")
            self.shake = max(self.shake, 0.5)
        if kind == "brute":
            self.run_brute(e, dt, dsq, bx, by, enraged)
            return
        if kind in ("guardian", "minigun", "exec", "fire", "skel"):
            self.run_boss2(e, dt, dsq, bx, by, enraged)
            return
        e.atk_timer -= dt * self.boss_pace()
        if e.atk_timer > 0 or e.frozen_timer > 0:
            return
        e.atk_timer = 2.0 if enraged else 3.0
        i = e.atk_index
        e.atk_index += 1
        bdmg = e.dmg * 0.45
        base = math.atan2(by - e.y, bx - e.x)

        def radial(n, speed, off=0.0):
            for k in range(n):
                if len(self.enemy_projectiles) >= 300:
                    return
                a = off + k * math.tau / n
                self.enemy_projectiles.append(EnemyProjectile(
                    e.x, e.y, e.x + math.cos(a) * 100, e.y + math.sin(a) * 100, speed, bdmg,
                    ENEMY_PROJ_COLOR, 7))

        def fan(n, spread, speed, color=ENEMY_PROJ_COLOR, style=None, rad=7):
            for a in fan_angles(base, n, spread):
                if len(self.enemy_projectiles) >= 300:
                    return
                self.enemy_projectiles.append(EnemyProjectile(
                    e.x, e.y, e.x + math.cos(a) * 100, e.y + math.sin(a) * 100, speed, bdmg,
                    color, rad, style=style))

        if kind == "normal":
            veteran = self.boss_kill_count >= 1
            pats = ["ring", "fan"] + (["wave", "ring"] if (veteran or enraged) else []) + \
                   (["beams"] if (veteran and enraged) else [])
            p = pats[i % len(pats)]
            if p == "ring":
                radial(16 if enraged else 12, 3.4, random.uniform(0, 1))
            elif p == "fan":
                fan(7 if enraged else 5, 12, 4.4)
            elif p == "wave":
                self.add_hazard(Hazard("ring", e.x, e.y, 0.7, 1.2, e.dmg * 0.9, (255, 120, 90),
                                       max_radius=420, thickness=24))
            else:
                for k in range(4):
                    self.add_hazard(Hazard("beam", e.x, e.y, 1.2, 0.4, e.dmg * 1.0, (255, 120, 90),
                                           angle=base + k * math.tau / 4, length=900, width=30))
        elif kind == "healer":
            pats = ["fan", "minions", "rain", "ring"]
            p = pats[i % len(pats)]
            if p == "fan":
                fan(5 if enraged else 3, 14, 4.0)
            elif p == "minions":
                self.spawn_minions(e.x, e.y, 4 if enraged else 3, "bat")
            elif p == "rain":
                for _ in range(6 if enraged else 4):
                    self.add_hazard(Hazard("blast", bx + random.uniform(-200, 200), by + random.uniform(-150, 150),
                                           1.2, 0.3, e.dmg * 1.0, (80, 220, 120), radius=75))
            else:
                radial(12 if enraged else 8, 3.0)
        else:
            pats = ["bolts", "rain", "summon", "curse"]
            p = pats[i % len(pats)]
            magic = (175, 85, 245)
            if p == "bolts":
                fan(7 if enraged else 5, 11, 4.2, magic, "spirit", 9)
                sfx("magic", 0.1)
            elif p == "rain":
                for _ in range(7 if enraged else 5):
                    self.add_hazard(Hazard("blast", bx + random.uniform(-230, 230), by + random.uniform(-170, 170),
                                           1.2, 0.3, e.dmg * 1.0, magic, radius=72))
                sfx("magic", 0.1)
            elif p == "summon":
                alive = sum(1 for o in self.enemies if o.kind is GSKEL_TYPE and not o.dead)
                n = min(3, max(0, 7 - alive))
                wm = self.wave_multiplier()
                for k in range(n):
                    a = k * math.tau / 3 + random.uniform(0, 1)
                    self.enemies.append(Enemy(GSKEL_TYPE, wm, 0, 0,
                                              spawn_at=(e.x + math.cos(a) * 90, e.y + math.sin(a) * 90),
                                              mode_config=self.mode_config))
                self.effects.append({"x": e.x, "y": e.y, "radius": 140, "timer": 0.5, "max_timer": 0.5, "color": magic})
                sfx("summon", 0.2)
            else:
                self.add_hazard(Hazard("ring", e.x, e.y, 0.8, 1.3, e.dmg * 0.9, magic, max_radius=480, thickness=26))
                for sgn in (-1, 1):
                    self.add_hazard(Hazard("beam", e.x, e.y, 1.2, 0.4, e.dmg, magic, angle=base + sgn * 0.3,
                                           length=950, width=28))
                sfx("magic", 0.1)
        sfx("shoot", 0.1)

    def run_boss2(self, e, dt, dsq, bx, by, enraged):
        """Penjaga (tombak), Komandan Minigun, Executioner (kapak kembali), Raja Api, Tengkorak Penembak."""
        k = e.boss_kind
        dist = math.sqrt(dsq)
        base = math.atan2(by - e.y, bx - e.x)
        d = e.dmg
        if k == "fire" and e.form == "orange" and e.hp < e.max_hp * 0.5:
            e.form = "blue"
            e.speed *= 1.35
            e.dmg *= 1.3
            self.show_toast("API BIRU MENGGANAS!")
            self.effects.append({"x": e.x, "y": e.y, "radius": 400, "timer": 0.6, "max_timer": 0.6, "color": (90, 170, 255)})
            self.shake = max(self.shake, 0.6)
            sfx("boss_spawn")
        if e.bstate is not None:
            e.bstate_t -= dt
            st = e.bstate
            if st in ("mg_fire", "mg_sweep", "bag_fire"):
                e.bdata["cd"] -= dt
                while e.bdata["cd"] <= 0:
                    e.bdata["cd"] += 0.055
                    if st == "mg_sweep":
                        prog = 1.0 - max(0.0, e.bstate_t) / e.bdata["dur"]
                        a = e.bdata["a0"] + (prog - 0.5) * 1.5 * e.bdata["dir"]
                        ex, ey = e.x + math.cos(a) * e.radius, e.y + math.sin(a) * e.radius
                        if len(self.enemy_projectiles) < 320:
                            self.enemy_projectiles.append(EnemyProjectile(ex, ey, ex + math.cos(a) * 100, ey + math.sin(a) * 100,
                                                                          7.0, d * 0.22, (255, 210, 90), 4, life=1.6, style="bullet"))
                    else:
                        self.fire_minigun(e, bx, by, d * 0.22, 7.5, 0.07 if k == "minigun" else 0.1)
                if e.bstate_t <= 0:
                    e.bstate, e.bdata = None, None
                    e.atk_timer = 1.6 if enraged else 2.4
                return
            if e.bstate_t > 0:
                return
            if st == "mg_spin":
                sweep = e.atk_index % 2 == 0
                dur = 2.0 if sweep else 2.4
                e.bstate, e.bstate_t = ("mg_sweep" if sweep else "mg_fire"), dur
                e.bdata = {"cd": 0.0, "dur": dur, "a0": math.atan2(by - e.y, bx - e.x), "dir": random.choice((-1, 1))}
            elif st == "rev":
                for n in range(6):
                    self.after(n * 0.22, lambda: e.dead or self.fire_minigun(e, self.badang.x, self.badang.y, d * 0.5, 8.5, 0.03, (255, 235, 150), 5))
                e.bstate, e.bstate_t = "rev_rest", 1.5
            elif st == "bag_open":
                e.bstate, e.bstate_t = "bag_fire", 3.0
                e.bdata = {"cd": 0.0}
            elif st == "throw":
                ax = ReturnAxe(e, self.badang.x, self.badang.y, 8.0, d * 1.1, 0.85, 26)
                self.enemy_projectiles.append(ax)
                e.axe = ax
                if enraged:
                    ax2 = ReturnAxe(e, self.badang.x + math.cos(base + 1.57) * 160, self.badang.y + math.sin(base + 1.57) * 160, 8.0, d * 1.1, 0.85, 26)
                    self.enemy_projectiles.append(ax2)
                sfx("whoosh", 0.1)
                e.bstate, e.bstate_t = "rest", 0.5
            elif st == "cleave":
                sfx("punch")
                self.shake = max(self.shake, 0.3)
                e.bstate, e.bstate_t = "rest", 0.4
            elif st == "thrust":
                sfx("punch")
                e.bstate, e.bstate_t = "rest", 0.4
            elif st == "raise":
                n = 8 if enraged else 5
                for _ in range(n):
                    self.meteor_at(bx + random.uniform(-190, 190), by + random.uniform(-150, 150), 1.1 + random.uniform(0, 0.7), d * 1.1, 80)
                self.meteor_at(bx, by, 1.1, d * 1.1, 80)
                sfx("magic", 0.1)
                e.bstate, e.bstate_t = "rest", 1.2
            else:
                e.bstate, e.bdata, e.busy = None, None, False
            return
        e.atk_timer -= dt * self.boss_pace()
        if e.atk_timer > 0 or e.frozen_timer > 0:
            return
        e.atk_timer = 1.5 if enraged else 2.3
        i = e.atk_index
        e.atk_index += 1
        if k == "guardian":
            pats = ["thrust", "raise", "lightning", "summon", "throw", "slam"]
            p = pats[i % len(pats)]
            if p == "thrust":
                e.bstate, e.bstate_t = "thrust", 0.8
                self.add_hazard(Hazard("beam", e.x, e.y, 0.8, 0.3, d * 1.1, (255, 230, 150), angle=base, length=460, width=80))
                sfx("warn", 0.2)
            elif p == "raise":
                e.bstate, e.bstate_t = "raise", 1.0
                sfx("warn", 0.2)
            elif p == "lightning":
                for _ in range(10 if enraged else 7):
                    self.sky_bolt(bx + random.uniform(-260, 260), by + random.uniform(-190, 190), 0.9 + random.uniform(0, 0.8), d * 0.9)
                self.sky_bolt(bx, by, 0.9, d * 0.9)
            elif p == "summon":
                self.spawn_random_horde(10 if enraged else 7, e.x, e.y, 7)
                self.effects.append({"x": e.x, "y": e.y, "radius": 200, "timer": 0.5, "max_timer": 0.5, "color": (255, 220, 130)})
                sfx("summon", 0.2)
            elif p == "throw":
                for a in fan_angles(base, 3 if enraged else 1, 14):
                    if len(self.enemy_projectiles) < 320:
                        self.enemy_projectiles.append(EnemyProjectile(e.x, e.y, e.x + math.cos(a) * 100, e.y + math.sin(a) * 100,
                                                                      7.2, d * 0.8, (230, 235, 245), 14, life=3.0, style="spear"))
                sfx("whoosh", 0.1)
            else:
                self.add_hazard(Hazard("ring", e.x, e.y, 0.7, 1.2, d * 0.9, (255, 220, 130), max_radius=440, thickness=26))
        elif k == "minigun":
            if i % 3 == 2:
                for _ in range(5):
                    self.meteor_at(bx + random.uniform(-170, 170), by + random.uniform(-130, 130), 1.0 + random.uniform(0, 0.5), d * 0.9, 70, (255, 200, 80))
            else:
                e.bstate, e.bstate_t = "mg_spin", 0.9
                sfx("warn", 0.2)
        elif k == "exec":
            alive_axe = e.axe is not None and e.axe.alive
            pats = ["throw", "cleave", "execute", "throw", "slam"]
            p = pats[i % len(pats)]
            if p == "throw" and alive_axe:
                p = "cleave"
            if p == "throw":
                e.bstate, e.bstate_t = "throw", 0.5
                sfx("warn", 0.2)
            elif p == "cleave":
                if dist < 300:
                    e.bstate, e.bstate_t = "cleave", 0.6
                    self.add_hazard(Hazard("beam", e.x, e.y, 0.6, 0.2, d * 1.2, (230, 90, 90), angle=base, length=280, width=170))
                    sfx("warn", 0.2)
                else:
                    e.atk_timer = 0.6
            elif p == "execute":
                self.add_hazard(Hazard("blast", bx, by, 1.2, 0.3, d * 1.6, (200, 40, 40), radius=75))
                self.after(0.5, lambda: self.add_hazard(Hazard("blast", self.badang.x, self.badang.y, 0.9, 0.3, d * 1.6, (200, 40, 40), radius=75)))
            else:
                self.add_hazard(Hazard("ring", e.x, e.y, 0.7, 1.0, d * 0.9, (200, 200, 220), max_radius=380, thickness=24))
        elif k == "fire":
            blue = e.form == "blue"
            col = (80, 160, 255) if blue else (255, 130, 40)
            pats = ["fan", "pillars", "ring", "pools"] + (["beams", "spiral"] if blue else [])
            p = pats[i % len(pats)]
            if p == "fan":
                for a in fan_angles(base, 9 if blue else 5, 10):
                    if len(self.enemy_projectiles) < 320:
                        ep = EnemyProjectile(e.x, e.y, e.x + math.cos(a) * 100, e.y + math.sin(a) * 100, 4.8, d * 0.5, col, 10, life=6.0, style="fire")
                        if blue:
                            ep.home = 0.012
                        self.enemy_projectiles.append(ep)
            elif p == "pillars":
                for _ in range(7 if blue else 5):
                    self.add_hazard(Hazard("blast", bx + random.uniform(-230, 230), by + random.uniform(-170, 170), 1.0, 0.8, d * 0.9, col, radius=62))
                self.add_hazard(Hazard("blast", bx, by, 1.0, 0.8, d * 0.9, col, radius=62))
            elif p == "ring":
                self.add_hazard(Hazard("ring", e.x, e.y, 0.7, 1.4, d, col, max_radius=520 if blue else 430, thickness=30))
            elif p == "pools":
                for _ in range(3):
                    self.add_hazard(Hazard("gas", bx + random.uniform(-200, 200), by + random.uniform(-150, 150), 0.6, 5.0, max(4.0, d * 0.28), col, radius=105))
            elif p == "beams":
                for n in range(4):
                    self.add_hazard(Hazard("beam", e.x, e.y, 1.1, 0.8, d, col, angle=base + n * math.tau / 4, length=950, width=34, spin=0.9))
            else:
                for n in range(24):
                    a = n * math.tau / 24
                    self.after(n * 0.06, lambda a=a: e.dead or (len(self.enemy_projectiles) < 320 and self.enemy_projectiles.append(
                        EnemyProjectile(e.x, e.y, e.x + math.cos(a) * 100, e.y + math.sin(a) * 100, 4.2, d * 0.4, col, 8, life=6.0, style="fire"))))
            sfx("shoot", 0.1)
        elif k == "skel":
            pats = ["rev", "bag", "dynamite", "rev", "summon", "bag"]
            p = pats[i % len(pats)]
            if p == "rev":
                e.bstate, e.bstate_t = "rev", 0.7
                sfx("warn", 0.2)
            elif p == "bag":
                e.bstate, e.bstate_t = "bag_open", 1.0
                sfx("warn", 0.2)
            elif p == "dynamite":
                for _ in range(6 if enraged else 4):
                    self.meteor_at(bx + random.uniform(-200, 200), by + random.uniform(-150, 150), 1.0 + random.uniform(0, 0.6), d * 1.0, 78, (255, 200, 80))
            else:
                wm = self.wave_multiplier()
                alive = sum(1 for o in self.enemies if o.kind is GSKEL_TYPE and not o.dead)
                for n in range(min(3, 6 - alive)):
                    a = n * math.tau / 3
                    self.enemies.append(Enemy(GSKEL_TYPE, wm, 0, 0, spawn_at=(e.x + math.cos(a) * 90, e.y + math.sin(a) * 90), mode_config=self.mode_config))
                sfx("summon", 0.2)

    def run_brute(self, e, dt, dsq, bx, by, enraged):
        """Brute Berkepala Dua: hentak, lempar batu, melompat, meninju (player terpental)."""
        dist = math.sqrt(dsq)
        if e.bstate is None:
            e.atk_timer -= dt * self.boss_pace()
            if e.atk_timer > 0 or e.frozen_timer > 0:
                return
            e.atk_timer = 1.5 if enraged else 2.4
            i = e.atk_index
            e.atk_index += 1
            base = math.atan2(by - e.y, bx - e.x)
            if dist < 200:
                choice = "punch" if (i % 2 == 0 or random.random() < 0.55) else "stomp"
            else:
                choice = ("throw", "leap", "stomp", "throw", "leap")[i % 5]
            e.busy = True
            if choice == "punch":
                e.bstate, e.bstate_t, e.bdata = "punch_wind", 0.55, {"ang": base}
                self.add_hazard(Hazard("beam", e.x, e.y, 0.55, 0.15, 0, (255, 150, 70), angle=base,
                                       length=e.radius + 160, width=70))
                sfx("warn", 0.2)
            elif choice == "stomp":
                e.bstate, e.bstate_t, e.bdata = "stomp_wind", 0.6, {}
                self.add_hazard(Hazard("ring", e.x, e.y, 0.6, 1.0, e.dmg * 0.9, (255, 150, 80),
                                       max_radius=520 if enraged else 430, thickness=28))
                sfx("warn", 0.2)
            elif choice == "throw":
                e.bstate, e.bstate_t, e.bdata = "throw", 0.5, {}
                sfx("warn", 0.2)
            else:
                e.bstate, e.bstate_t, e.bdata = "leap_wind", 0.7, {"tx": bx, "ty": by}
                self.add_hazard(Hazard("blast", bx, by, 1.5, 0.25, e.dmg * 1.2, (255, 100, 60), radius=125))
                sfx("warn", 0.2)
            return
        e.bstate_t -= dt
        st = e.bstate
        if st == "punch_wind":
            if e.bstate_t <= 0:
                a = e.bdata["ang"]
                reach = e.radius + 160
                if seg_dist_sq(bx, by, e.x, e.y, e.x + math.cos(a) * reach, e.y + math.sin(a) * reach) \
                        <= (38 + self.badang.size * 0.8) ** 2:
                    if self.badang.take_damage(e.dmg * 1.1):
                        self.badang.apply_knockback(math.cos(a), math.sin(a), 26)
                sfx("punch")
                self.shake = max(self.shake, 0.3)
                e.bstate, e.bstate_t = "punch", 0.3
        elif st == "stomp_wind":
            if e.bstate_t <= 0:
                sfx("stomp")
                self.shake = max(self.shake, 0.55)
                e.bstate, e.bstate_t = "stomp_rec", 0.4
        elif st == "throw":
            if e.bstate_t <= 0:
                n = 3 if enraged else 2
                for k in range(n):
                    lead = (k - (n - 1) / 2.0) * 0.28
                    a = math.atan2(by - e.y, bx - e.x) + lead
                    if len(self.enemy_projectiles) < 300:
                        self.enemy_projectiles.append(EnemyProjectile(
                            e.x, e.y - 10, e.x + math.cos(a) * 100, e.y + math.sin(a) * 100, 5.6, e.dmg * 0.8,
                            (135, 128, 118), 15, life=6.0, style="rock"))
                sfx("rock")
                e.bstate, e.bstate_t = "throw_rec", 0.4
        elif st == "leap_wind":
            if e.bstate_t <= 0:
                e.bdata["sx"], e.bdata["sy"] = e.x, e.y
                e.bstate, e.bstate_t = "leap_air", 0.8
                sfx("jump")
        elif st == "leap_air":
            k = 1.0 - max(0.0, e.bstate_t) / 0.8
            e.x = e.bdata["sx"] + (e.bdata["tx"] - e.bdata["sx"]) * k
            e.y = e.bdata["sy"] + (e.bdata["ty"] - e.bdata["sy"]) * k
            e.air_h = math.sin(k * math.pi) * 180
            if e.bstate_t <= 0:
                e.air_h = 0.0
                self.add_hazard(Hazard("ring", e.x, e.y, 0.05, 0.7, e.dmg * 0.8, (255, 150, 80),
                                       max_radius=320, thickness=24))
                sfx("stomp")
                self.shake = max(self.shake, 0.7)
                e.bstate, e.bstate_t = "leap_rec", 0.5
        elif e.bstate_t <= 0:
            e.bstate, e.busy, e.bdata = None, False, None
    def update_combos(self):
        self.badang.refresh_evolutions()
        weapons = self.badang.all_weapons()
        n_evo = sum(1 for w in weapons if w.evolved)
        base = 1.0 + 0.25 * max(0, n_evo - 1)

        active = set()
        for key, classes, _title, _desc in COMBO_DEFS:
            if all(any(isinstance(w, c) and w.evolved for w in weapons) for c in classes):
                active.add(key)

        for w in weapons:
            if not w.evolved:
                w.combo_bonus = 1.0
                continue
            n_combo = sum(1 for key, classes, _t, _d in COMBO_DEFS
                          if key in active and isinstance(w, classes))
            w.combo_bonus = base * (1.0 + COMBO_DAMAGE_BONUS * n_combo)

        new_combos = active - ACTIVE_COMBOS
        new_evos = [w for w in weapons if w.evolved and w.display_name not in self.evo_seen]
        ACTIVE_COMBOS.clear()
        ACTIVE_COMBOS.update(active)
        for w in new_evos:
            self.evo_seen.add(w.display_name)
        if new_combos:
            key = sorted(new_combos)[0]
            self.show_toast(f"COMBO {COMBO_TITLES[key]}: {COMBO_DESCS[key]}")
            sfx("combo")
        elif new_evos:
            self.show_toast(f"EVOLUSI: {new_evos[0].evolved_name}!")



    def spawn_heal_orbs(self):
        bx, by = self.badang.x, self.badang.y
        far2 = 1500 ** 2
        self.pickups = [p for p in self.pickups
                        if not (p.kind == "hporb" and dist_sq(p.x, p.y, bx, by) > far2)]
        count = sum(1 for p in self.pickups if p.kind == "hporb")
        for _ in range(2):
            if count >= MAX_HEAL_ORBS:
                break
            ang = random.uniform(0, math.tau)
            dist = random.uniform(220, 520)
            self.pickups.append(Pickup("hporb", bx + math.cos(ang) * dist, by + math.sin(ang) * dist))
            count += 1



    def apply_shop_item(self, key):
        b = self.badang
        if key == "heal":
            b.hp = b.max_hp
        elif key == "maxhp":
            add_max_hp(b, 40)
        elif key == "speed":
            b.speed += 0.6
        elif key == "magnet":
            b.pickup_radius += 45
        elif key == "armor":
            b.dr_shop = min(0.3, b.dr_shop + 0.06)
        elif key == "xpgain":
            b.xp_gain_mult += 0.25
        elif key == "goldgain":
            self.gold_gain_mult += 0.25
        elif key == "vit":
            add_max_hp(b, 80)
        elif key == "shieldt":
            b.invuln_timer = max(b.invuln_timer, 8.0)
            self.shieldt_t = 8.0
            sfx("shield_up")
        elif key == "freeze":
            self.start_holy_bomb(ice=True)
        elif key == "pull":
            self.pull_all_gems()
        elif key == "chestbuy":
            self.pickups.append(Pickup("chest", b.x + 60, b.y))
        elif key == "lvlup":
            if b.gain_xp((b.xp_needed - b.xp + 1) / XP_GAIN_MULT):
                self.pending_levelups += 1
            else:
                self.show_toast("Level sudah maksimum")
                return False
        elif key == "roti":
            b.hp = min(b.max_hp, b.hp + b.max_hp * 0.4)
        elif key == "wind":
            b.speed += 0.3
        elif key == "regen":
            b.regen += 1.5
        elif key == "power":
            PLAYER_BUFFS["perm"] = round(PLAYER_BUFFS["perm"] + 0.10, 2)
        elif key == "scroll":
            cand = [w for w in b.weapons if w.level < MAX_WEAPON_LEVEL]
            if not cand:
                self.show_toast("Semua skill sudah evolusi!")
                return False
            random.choice(cand).level_up()
        elif key == "revive":
            if self.revives >= 1:
                self.show_toast("Sudah punya Nyawa Kedua")
                return False
            self.revives += 1
        elif key == "bomb":
            self.start_holy_bomb()
        return True

    def compute_score(self):
        return (self.kills * 10 + self.badang.level * 150 + int(self.time_survived) * 2
                + self.jsab_kills * 2000 + self.boss_kill_count * 300)

    def snapshot(self):
        b = self.badang
        return {
            "avatar": b.avatar["key"], "mode": self.mode, "time": self.time_survived,
            "level": b.level, "xp": b.xp, "xp_needed": b.xp_needed, "hp": b.hp, "max_hp": b.max_hp,
            "speed": b.speed, "pickup": b.pickup_radius, "regen": b.regen,
            "weapons": [(["FusionWeapon", w.level, [], {"a": w.a, "b": w.b}] if isinstance(w, FusionWeapon) else [type(w).__name__, w.level, []]) for w in b.weapons], "fusions": b.fusions,
            "gold": self.gold, "kills": self.kills, "boss_kill_count": self.boss_kill_count,
            "advanced": self.advanced_unlocked, "next_boss_level": self.next_boss_level,
            "next_merchant_level": self.next_merchant_level, "perm": PLAYER_BUFFS["perm"],
            "revives": self.revives, "jsab_kills": self.jsab_kills, "evo_seen": sorted(self.evo_seen),
            "jsab_index": self.jsab_index, "last_jsab_time": self.last_jsab_time,
            "boss_spawn_count": self.boss_spawn_count,
            "dr_shop": b.dr_shop, "xp_gain_mult": b.xp_gain_mult, "gold_gain_mult": self.gold_gain_mult,
        }

    def restore_run(self, s):
        try:
            b = self.badang
            b.level, b.xp, b.xp_needed = int(s["level"]), s["xp"], s["xp_needed"]
            b.max_hp = s["max_hp"]
            b.hp = max(1.0, min(b.max_hp, s["hp"]))
            b.speed, b.pickup_radius, b.regen = s["speed"], s["pickup"], s["regen"]
            by_name = {c.__name__: c for c in WEAPON_CLASSES}
            ws = []
            for item in s["weapons"]:
                if item[0] == "FusionWeapon" and len(item) > 3 and isinstance(item[3], dict):
                    fa, fb = item[3].get("a"), item[3].get("b")
                    if fa in by_name and fb in by_name:
                        ws.append(FusionWeapon(level=int(item[1]), a=fa, b=fb))
                    continue
                if item[0] not in by_name:
                    continue
                ws.append(by_name[item[0]](level=int(item[1])))
            if ws:
                b.weapons = ws
                b.refresh_evolutions()
            b.fusions = int(s.get("fusions", 0))
            self.time_survived = s["time"]
            self.gold, self.kills = s["gold"], s["kills"]
            self.boss_kill_count = s["boss_kill_count"]
            self.advanced_unlocked = s["advanced"]
            self.next_boss_level = s["next_boss_level"]
            self.next_merchant_level = s["next_merchant_level"]
            PLAYER_BUFFS["perm"] = s.get("perm", 1.0)
            self.revives = s.get("revives", 0)
            b.dr_shop = float(s.get("dr_shop", 0.0))
            b.xp_gain_mult = float(s.get("xp_gain_mult", 1.0))
            self.gold_gain_mult = float(s.get("gold_gain_mult", 1.0))
            self.jsab_kills = s.get("jsab_kills", 0)
            self.evo_seen = set(s.get("evo_seen", []))
            DIFFICULTY["lv"] = b.level
            self.jsab_index = s.get("jsab_index", max(0, int(s["next_boss_level"]) // 10 - 1))
            self.last_jsab_time = s.get("last_jsab_time", self.time_survived)
            self.boss_spawn_count = s.get("boss_spawn_count", 0)
            self.last_level_seen = b.level
            self.boss_timer = 25.0
            b.invuln_timer = 2.0
            self.show_toast("Permainan dilanjutkan")
        except Exception:
            pass

    def save_run(self):
        if self.mode is None or self.mode == "tutorial" or self.state in ("gameover", "menu", "avatars", "scores", "title", "victory"):
            return
        self.save.data["run"] = self.snapshot()
        self.save.save()

    def finish_run(self, victory=False):
        if self.run_finished:
            return
        self.run_finished = True
        b = self.badang
        self.last_score = self.compute_score()
        entry = {"score": self.last_score, "avatar": b.avatar["name"], "mode": self.mode,
                 "level": b.level, "time": int(self.time_survived), "kills": self.kills,
                 "bosses": self.jsab_kills}
        self.new_rank = self.save.add_score(entry)
        self.last_crystals = self.compute_crystals() + (getattr(self, "victory_bonus", 0) if victory else 0)
        self.save.data["crystals"] = int(self.save.data.get("crystals", 0)) + self.last_crystals
        self.save.data["last_level_times"] = {str(k): v for k, v in self.level_times.items() if k % 5 == 0}
        st = self.save.data["stats"]
        st["runs"] += 1
        st["kills"] += self.kills
        st["bosses"] += self.jsab_kills
        st["best_level"] = max(st["best_level"], b.level)
        st["best_time"] = max(st["best_time"], int(self.time_survived))
        infl = self.mode == "inflation"
        try:
            if self.mode != "tutorial":
                quest_add_run(self.save.data, {"kills": self.kills, "bosses": self.jsab_kills + self.boss_kill_count, "runs": 1,
                                                 "infl_runs": 1 if infl else 0, "wins": 1 if (victory and infl) else 0,
                                                 "level": b.level, "minutes": int(self.time_survived // 60),
                                                 "infl_level": b.level if infl else 0})
        except Exception:
            pass
        self.save.data["run"] = None
        self.save.save()
        if not victory:
            sfx("gameover")

    def on_quit(self):
        if self.state in ("playing", "paused", "levelup", "shop"):
            self.save_run()
        else:
            self.save.save()

    def update_music(self):
        st = self.state
        now = time.time()
        bpm = None
        if st in ("menu", "avatars", "scores", "title", "playmenu", "storymenu", "settings", "almanac", "almanac_detail", "badges", "confirm_new", "toko", "quests"):
            want, prio = "menu", 1
        elif st == "shop":
            want, prio = "shop", 1
        elif st == "gameover":
            want, prio = None, 0
        elif st == "victory":
            want, prio = "menu", 1
        elif st in ("title", "playmenu", "storymenu", "settings", "almanac", "almanac_detail", "badges"):
            want, prio = "menu", 1
        else:
            ob = next((e for e in self.enemies if e.is_boss and e.boss_kind != "jsab" and not e.dead), None)
            if st == "light":
                want, prio = None, 9
            elif self.level_boss is not None:
                try:
                    bi = BOSS_DEFS.index(self.level_boss.kdef)
                    want, prio = "lvb_%d" % bi, 4
                    bpm = None if self.level_boss.bpm == BOSS_DEFS[bi]["bpm"] else self.level_boss.bpm
                except ValueError:
                    want, prio, bpm = "boss", 4, self.level_boss.bpm
            elif ob is not None:
                want, prio = {"normal": "boss_old", "healer": "boss_heal", "necro": "boss_necro", "brute": "boss_brute",
                              "guardian": "boss_guard", "minigun": "boss_gun", "exec": "boss_exec", "fire": "boss_fire",
                              "skel": "boss_skel", "final": "boss_final"}.get(ob.boss_kind, "boss_old"), (5 if ob.boss_kind == "final" else 3)
                if self.mode == "tutorial":
                    want = "tut_boss"
            elif self.formation_warn is not None or self.formation_music_t > 0:
                want, prio = "event", 2
            elif self.mode == "tutorial":
                want, prio = "tut", 1
            else:
                want, prio = "battle", 1
        key = (want, bpm)
        if key != self.music_key:
            if self.music_key is None or prio > self.music_prio or now >= self.music_lock_until or want is None:
                if set_music(want, bpm) is not False:
                    self.music_key, self.music_prio = key, prio
                    self.music_lock_until = now + (9.0 if prio == 2 else 4.0)
        music_poll()
        pause_music(st == "paused")
    def update(self, dt):
        if self.toast_timer > 0:
            self.toast_timer -= dt
        if self.menu_msg_t > 0:
            self.menu_msg_t -= dt
        self.title_t += dt
        self.check_event_alarm()
        self.update_badge_banner(dt)
        self.update_music()

        if self.state == "dialog":
            self.update_dialog(dt)
            self.final_tick_intro(dt)
            return
        if self.state == "light":
            self.update_light(dt)
            return
        if self.state != "playing":
            return

        self.nearest_enemy = None
        SHIELD_ZONES[:] = [(m.x, m.y, m.SHIELD_R) for m in self.merchants if m.shield_active]
        self.update_fx_anims(dt)

        self.time_survived += dt
        b = self.badang
        lv = b.level
        DIFFICULTY["lv"] = lv
        self.update_combos()
        self.run_sched(dt)
        if self.pending_levelups > 0 and self.state == "playing":
            self.pending_levelups -= 1
            self.state = "levelup"
            self.upgrade_menu = UpgradeMenu(self.badang)
            sfx("levelup")
        self.skill_rec_t -= dt
        if self.skill_rec_t <= 0:
            self.skill_rec_t = 1.0
            self.record_skills()

        self.dps_clock += dt
        if self.dps_clock >= 1.0:
            self.dps_clock -= 1.0
            self.dps_buckets.append(self.dmg_acc)
            self.dmg_acc = 0.0
            del self.dps_buckets[:-10]
        if lv > self.last_level_seen:
            for L in range(self.last_level_seen + 1, lv + 1):
                self.level_times[L] = int(self.time_survived)
                if L % 5 == 0:
                    print("[LOG] Level %d tercapai pada %s" % (L, fmt_time(int(self.time_survived))))
            self.last_level_seen = lv
        if self.shake > 0:
            self.shake = max(0.0, self.shake - dt)
            mag = self.shake * 14 * SETTINGS["shake"]
            self.shake_off = (random.uniform(-mag, mag), random.uniform(-mag, mag))
        else:
            self.shake_off = (0.0, 0.0)
        if self.mercy_t > 0:
            self.mercy_t -= dt
        if self.mercy_cd > 0:
            self.mercy_cd -= dt
        if self.formation_music_t > 0:
            self.formation_music_t -= dt
        if self.boss_intro:
            self.boss_intro["t"] -= dt
            if self.boss_intro["t"] <= 0:
                self.boss_intro = None

        for t in self.damage_texts:
            t[1] -= 45 * dt
            t[2] -= dt
        self.damage_texts = [t for t in self.damage_texts if t[2] > 0]

        self.hporb_timer -= dt
        if self.hporb_timer <= 0:
            self.hporb_timer = random.uniform(8.0, 13.0) if self.mode == "inflation" else random.uniform(5.0, 8.0)
            self.spawn_heal_orbs()
        self.rune_timer -= dt
        if self.rune_timer <= 0:
            self.rune_timer = random.uniform(14.0, 24.0)
            if self.mode != "tutorial" and not self.final_spawned:
                ang, dist = random.uniform(0, math.tau), random.uniform(200, 460)
                self.add_pickup(Pickup(random.choice(["magnet", "freeze", "nuke"]), b.x + math.cos(ang) * dist, b.y + math.sin(ang) * dist))
                self.show_toast("Rune acak muncul di dekatmu!")

        b.update(dt)
        b.move(self.move_vector, dt)
        a = self.arena
        if a:
            b.x = max(a["cx"] - a["hw"] + 24, min(a["cx"] + a["hw"] - 24, b.x))
            b.y = max(a["cy"] - a["hh"] + 24, min(a["cy"] + a["hh"] - 24, b.y))
        prev_sp = b.special.timer
        b.special.update(dt, self)
        if b.special.timer > prev_sp + 0.5:
            sfx("skill", 0.2)

        self.autosave_timer -= dt
        if self.autosave_timer <= 0:
            self.autosave_timer = 15.0
            if self.level_boss is None:
                self.save_run()

        if (self.mode == "inflation" and lv >= FINAL_BOSS_LEVEL and not self.final_spawned and not self.boss_active
                and self.level_boss is None):
            self.start_final_boss()
            return
        due_level = lv >= self.next_boss_level and not (self.mode == "inflation" and lv >= FINAL_BOSS_LEVEL)
        due_time = (self.mode != "inflation" or lv < FINAL_BOSS_LEVEL) and (self.time_survived - self.last_jsab_time) >= JSAB_MAX_INTERVAL
        if not self.boss_active and self.level_boss is None and (due_level or due_time) and self.mode != "tutorial":
            self.spawn_level_boss(by_time=not due_level)
        mlv = self.next_merchant_level
        if lv >= mlv and self.level_boss is None and self.mode != "tutorial" and (mlv % 10 != 0 or self.next_boss_level > mlv):
            self.spawn_merchant()
            self.next_merchant_level += 5

        mc = self.mode_config
        if self.mode == "tutorial":
            self.tutorial_update(dt)
        if self.level_boss is None and self.mode != "tutorial":
            self.update_spawning(dt)
            if self.boss_active:
                self.formation_warn = None
            else:
                self.update_formation(dt)

        if not self.boss_active and self.mode != "tutorial" and not (self.mode == "inflation" and lv >= FINAL_BOSS_LEVEL - 4):
            self.boss_timer -= dt
            if self.boss_timer <= 0:
                self.spawn_boss()
                self.boss_timer = INFL_BOSS_TIMER if self.mode == "inflation" else 55.0

        wm = self.wave_multiplier()
        bx, by = b.x, b.y
        for e in self.enemies:
            if e.dead:
                continue
            if e.boss_kind == "jsab":
                e.tick(dt, self)
                if dist_sq(e.x, e.y, bx, by) < (e.radius + b.size * 0.8) ** 2:
                    b.take_damage(e.dmg * 0.4)
                continue
            e.update((bx, by), dt)
            dsq = dist_sq(e.x, e.y, bx, by)
            if e.intro_t <= 0 and e.air_h <= 0 and dsq < (e.radius + b.size * 0.8) ** 2:
                b.take_damage(e.dmg * 0.6 if e.is_boss else e.dmg)

            if e.is_summoner and len(self.enemies) < MAX_ENEMIES:
                e.summon_timer -= dt
                if e.summon_timer <= 0:
                    e.summon_timer = e.summon_interval
                    for _ in range(3):
                        if len(self.enemies) >= MAX_ENEMIES:
                            break
                        off = (random.uniform(-30, 30), random.uniform(-30, 30))
                        self.enemies.append(Enemy(SKELETON_TYPE, wm, 0, 0,
                                                  spawn_at=(e.x + off[0], e.y + off[1]),
                                                  mode_config=self.mode_config))

            if e.is_shooter:
                e.shoot_timer -= dt
                if e.shoot_timer <= 0:
                    e.shoot_timer = e.shoot_interval
                    if dsq < 650 * 650 and len(self.enemy_projectiles) < MAX_ENEMY_PROJECTILES:
                        self.enemy_projectiles.append(
                            EnemyProjectile(e.x, e.y, bx, by, e.shoot_speed, e.shoot_damage)
                        )

            if e.is_healer and e.intro_t <= 0:
                e.heal_timer -= dt
                if e.heal_timer <= 0:
                    e.heal_timer = e.heal_interval
                    self.healer_pulse(e)

            self.run_enemy_abilities(e, dt, dsq, bx, by)
            if e.is_boss:
                self.run_old_boss(e, dt, dsq, bx, by)

        self.protectors = [e for e in self.enemies if e.is_protector and not e.dead and e.shield > 0]
        self.update_statuses(dt)
        self.update_boss_tells()
        shields = [m for m in self.merchants if m.shield_active]
        if shields:
            for e in self.enemies:
                if e.dead or e.boss_kind == "jsab":
                    continue
                for m in shields:
                    m.push_out(e)
            for p in self.enemy_projectiles:
                if not p.alive:
                    continue
                for m in shields:
                    if dist_sq(p.x, p.y, m.x, m.y) <= (m.SHIELD_R + p.radius) ** 2:
                        p.alive = False
                        if len(self.effects) < 70:
                            self.effects.append({"x": p.x, "y": p.y, "radius": 16, "timer": 0.18, "max_timer": 0.18,
                                                 "color": (170, 235, 255)})
                        break

        self.enemies = [e for e in self.enemies if not e.dead]

        for w in b.all_weapons():
            prev = getattr(w, "timer", None)
            _n0 = len(self.projectiles)
            w.update(dt, self)
            if w.evolved and len(self.projectiles) > _n0:
                _look = EVO_LOOK.get(getattr(type(w), "evo_base", type(w)).__name__, ((255, 225, 120), "star"))
                for _p in self.projectiles[_n0:]:
                    _p.evo_look = _look
            if prev is not None and w.timer > prev + 0.05 and (w.timer >= 0.45 or isinstance(w, PunchWeapon)):
                if self.nearest_enemy is not None:
                    sfx(w.sfx_name, 0.08)

        for p in self.projectiles:
            p.update(dt, self)
        for p in self.projectiles:
            if not p.alive:
                continue
            for e in self.enemies:
                if e.dead or id(e) in p.hit_ids:
                    continue
                r2 = (p.radius + e.radius) ** 2
                if dist_sq(p.x, p.y, e.x, e.y) <= r2:
                    self.damage_enemy(e, p.damage * (0.35 if (e.ice_immune and p.freeze_on_hit) else 1.0), pierce=(p.pierce > 0 or p.splash_radius > 0))
                    _fire = (p.style in ("fire", "flame", "meteor")) or _is_fire_col(p.color)
                    if _fire and not e.dead:
                        self.ignite_enemy(e, max(2.0, p.damage * 0.2), 3.0)
                    if p.freeze_on_hit and not e.is_boss and not e.ice_immune:
                        e.frozen_timer = max(e.frozen_timer, p.freeze_duration)
                    if p.splash_radius > 0:
                        sr2 = p.splash_radius ** 2
                        for other in self.enemies:
                            if other is e or other.dead:
                                continue
                            if dist_sq(other.x, other.y, e.x, e.y) <= sr2:
                                self.damage_enemy(other, p.splash_damage)
                                if _fire and not other.dead:
                                    self.ignite_enemy(other, max(2.0, p.splash_damage * 0.2), 3.0)
                        self.effects.append({"x": e.x, "y": e.y, "radius": p.splash_radius,
                                             "timer": 0.25, "max_timer": 0.25, "color": FIRE_COLOR})
                    p.hit_ids.add(id(e))
                    if p.bounce > 0:
                        p.bounce -= 1
                        best, best_d = None, 420 ** 2
                        for o in self.enemies:
                            if o.dead or id(o) in p.hit_ids:
                                continue
                            d = dist_sq(o.x, o.y, e.x, e.y)
                            if d < best_d:
                                best, best_d = o, d
                        if best is not None:
                            m = math.hypot(best.x - p.x, best.y - p.y) or 1
                            p.vx, p.vy = (best.x - p.x) / m * p.speed, (best.y - p.y) / m * p.speed
                        else:
                            p.alive = False
                    elif p.pierce > 0:
                        p.pierce -= 1
                    else:
                        p.alive = False
                    break

        for p in self.enemy_projectiles:
            if p.home:
                p.home_target = (bx, by)
            p.update(dt)
        for p in self.enemy_projectiles:
            if not p.alive:
                continue
            r2 = (p.radius + b.size * 0.8) ** 2
            if dist_sq(p.x, p.y, bx, by) <= r2:
                b.take_damage(p.damage)
                if _is_fire_col(p.color) or p.style in ("fire", "flame"):
                    b.set_burn(max(2.0, p.damage * 0.3), 2.5)
                elif _is_poison_col(p.color):
                    b.set_poison(max(2.0, p.damage * 0.3), 3.5)
                if getattr(p, "slow", False) and not in_merchant_shield(bx, by):
                    b.slow_t = max(b.slow_t, 2.0)
                if not getattr(p, "pierce_player", False):
                    p.alive = False

        for bm in self.boomerangs:
            bm.update(dt, b)
            for e in self.enemies:
                if e.dead or id(e) in bm.hit_ids:
                    continue
                r2 = (bm.radius + e.radius) ** 2
                if dist_sq(bm.x, bm.y, e.x, e.y) <= r2:
                    self.damage_enemy(e, bm.damage)
                    bm.hit_ids.add(id(e))
        self.boomerangs = [x for x in self.boomerangs if x.alive]

        for z in self.poison_zones:
            z.update(dt, self)
        self.poison_zones = [z for z in self.poison_zones if z.duration > 0]

        for s in self.strikes:
            s.update(dt, self)
        self.strikes = [s for s in self.strikes if s.alive]
        for t in self.tornados:
            t.update(dt, self)
        self.tornados = [t for t in self.tornados if t.alive]
        for h in self.hazards:
            h.update(dt, self)
        self.hazards = [h for h in self.hazards if h.alive]

        cam_x, cam_y = self.get_camera()
        m = 800 if self.arena else 100
        self.projectiles = [
            p for p in self.projectiles
            if p.alive and -100 <= p.x - cam_x <= WIDTH + 100 and -100 <= p.y - cam_y <= HEIGHT + 100
        ]
        self.enemy_projectiles = [
            p for p in self.enemy_projectiles
            if p.alive and -m <= p.x - cam_x <= WIDTH + m and -m <= p.y - cam_y <= HEIGHT + m
        ]

        for eff in self.effects:
            eff["timer"] -= dt
        self.update_rune_shocks()
        self.effects = [x for x in self.effects if x["timer"] > 0]
        if self.flash_t > 0:
            self.flash_t = max(0.0, self.flash_t - dt)

        pr2 = b.pickup_radius ** 2
        sz2 = b.size ** 2
        gem_sfx = 0
        ate = False
        for g in self.gems:
            dsq = dist_sq(g.x, g.y, bx, by)
            if g.pulled:
                dx, dy = bx - g.x, by - g.y
                d = math.hypot(dx, dy) or 1
                g.pspeed = min(46.0, g.pspeed + 55.0 * dt)
                step = g.pspeed * dt * 60
                if d <= step + b.size:
                    dsq = 0.0
                else:
                    g.x += dx / d * step
                    g.y += dy / d * step
                    continue
            elif dsq < pr2:
                dx, dy = bx - g.x, by - g.y
                d = math.hypot(dx, dy) or 1
                g.x += dx / d * 7
                g.y += dy / d * 7
            if dsq < sz2:
                gem_sfx += 1
                if gem_sfx <= 3:
                    sfx("gem", 0.05)
                if b.gain_xp(g.amount):
                    self.add_damage_text(bx, by - 50, f"+{HP_PER_LEVEL} HP max", DMG_COLOR_HEAL)
                    if self.state == "levelup":
                        self.pending_levelups += 1
                    else:
                        self.state = "levelup"
                        self.upgrade_menu = UpgradeMenu(b)
                        sfx("levelup")
                g.eaten = True
                ate = True
        if ate:
            self.gems = [g for g in self.gems if not g.eaten]

        if self.pickups:
            keep_pk = []
            for pk in self.pickups:
                r2 = (b.size + pk.radius) ** 2
                if dist_sq(pk.x, pk.y, bx, by) < r2:
                    self.apply_pickup(pk)
                    sfx("heal" if pk.kind in ("hporb", "health") else "pickup", 0.05)
                    continue
                pk.age += dt
                if pk.age > PICKUP_LIFE and pk.kind not in ("chest", "hporb"):
                    continue
                keep_pk.append(pk)
            self.pickups = keep_pk

        for mer in self.merchants:
            mer.update(dt, self)
            if mer.event:
                ev, mer.event = mer.event, None
                if ev == "left":
                    self.show_toast("Pedagang pergi... dia akan kembali!")
                    sfx("merchant")
                elif ev == "returned":
                    self.show_toast("Pedagang kembali! Masuk perisainya.")
                    sfx("shield_up")
                else:
                    self.show_toast("Pedagang pergi untuk selamanya")
        self.merchants = [mm for mm in self.merchants if mm.alive]
        if self.state == "playing":
            for mer in self.merchants:
                if mer.present and mer.cooldown <= 0 and dist_sq(mer.x, mer.y, bx, by) < 75 ** 2 and not (self.mode == "tutorial" and self.tut["i"] != 6):
                    if self.mode == "tutorial" and not self.tut.get("met"):
                        self.tut["met"] = True
                        self.start_dialog(MERCHANT_LINES["shop"], "talk_merchant", (lambda m=mer: self.open_shop(m)))
                        break
                    self.open_shop(mer)
                    self.move_vector = (0.0, 0.0)
                    self.joystick_finger_id = None
                    sfx("merchant")
                    self.save_run()
                    break

        if b.hit_events:
            for amt in b.hit_events:
                self.add_damage_text(bx, by - 42, f"-{max(1, int(round(amt)))}", DMG_COLOR_HURT, big=True)
            b.hit_events.clear()
            sfx("hurt", 0.15)
        if b.dot_events:
            for amt, kind in b.dot_events:
                self.add_damage_text(bx, by - 30, f"-{max(1, int(round(amt)))}",
                                     (120, 230, 100) if kind == "poison" else (255, 150, 60), big=False)
            b.dot_events.clear()

        if b.hp <= 0 and self.mode == "tutorial":
            b.hp = b.max_hp
            b.invuln_timer = 2.0
        elif b.hp <= 0:
            if self.revives > 0:
                self.revives -= 1
                b.hp = b.max_hp * 0.5
                b.invuln_timer = 3.0
                b.clear_statuses()
                self.enemy_projectiles = []
                self.hazards = []
                self.show_toast("Nyawa Kedua terpakai!")
                self.start_revive_anim()
                sfx("revive")
            else:
                self.state = "gameover"
                self.finish_run()

    def pull_all_gems(self):
        """Rune magnet: SEMUA orb di dunia terbang ke pemain (bukan langsung hilang)."""
        for g in self.gems:
            g.pulled = True
            g.pspeed = 9.0

    def start_holy_bomb(self, ice=False):
        """Animasi pemain melempar Bom Suci (atau Bom Es); meledak di titik jatuh."""
        b = self.badang
        t = self.find_nearest_enemy()
        if t is not None:
            tx, ty = t.x, t.y
        else:
            tx, ty = b.x + 260, b.y - 60
        self.fx_anims.append({"kind": "bomb", "t": 0.0, "dur": 0.85, "x0": b.x, "y0": b.y, "tx": tx, "ty": ty, "ice": ice})
        sfx("whoosh", 0.05)

    def start_revive_anim(self):
        self.fx_anims.append({"kind": "revive", "t": 0.0, "dur": 2.4})
        self.flash_t = 0.3
        self.flash_col = (255, 240, 180)

    def update_fx_anims(self, dt):
        if self.shieldt_t > 0:
            self.shieldt_t -= dt
        keep = []
        for a in self.fx_anims:
            a["t"] += dt
            if a["kind"] == "bomb" and not a.get("boom") and a["t"] >= a["dur"]:
                a["boom"] = True
                if a.get("ice"):
                    self.trigger_rune_shock("freeze", 5.0, cx=a["tx"], cy=a["ty"])
                    self.show_toast("BOM ES!")
                else:
                    self.trigger_rune_shock("nuke", cx=a["tx"], cy=a["ty"])
                    self.show_toast("BOM SUCI!")
            if a["t"] < a["dur"] + (0.0 if a["kind"] != "bomb" else 0.05):
                keep.append(a)
        self.fx_anims = keep

    def draw_evo_emblems(self, surf, cam_x, cam_y):
        """Skill evolusi tampil beda: lambang evolusi (gambar yang sama dengan Almanak) mengorbit pemain."""
        if PERF["lod"] > 0:
            return
        b = self.badang
        evs = [w for w in b.weapons if w.evolved and getattr(w, "evo_form", False)]
        if not evs:
            return
        t = pygame.time.get_ticks() / 1000.0
        px, py = int(b.x - cam_x), int(b.y - cam_y)
        n = len(evs)
        for i, w in enumerate(evs):
            a = t * 0.9 + i * math.tau / n
            ex, ey = px + int(math.cos(a) * 58), py + int(math.sin(a) * 40) - 6
            pygame.draw.circle(surf, (30, 26, 50), (ex, ey), 15)
            pygame.draw.circle(surf, (255, 215, 90), (ex, ey), 15, 2)
            old = surf.get_clip()
            surf.set_clip(pygame.Rect(ex - 14, ey - 14, 28, 28))
            draw_evo_icon(surf, w.evo_base, ex, ey, 0.3, t)
            surf.set_clip(old)

    def draw_fx_anims(self, surf, cam_x, cam_y):
        P = pygame.draw
        b = self.badang
        tm = pygame.time.get_ticks() / 1000.0
        self.draw_evo_emblems(surf, cam_x, cam_y)
        # Cincin perisai sementara (seperti perisai pedagang)
        if self.shieldt_t > 0 and not (self.shieldt_t < 2.0 and int(self.shieldt_t * 6) % 2 == 0):
            R = 66
            sx, sy = int(b.x - cam_x), int(b.y - cam_y)
            if self._shieldt_surf is None:
                sf = pygame.Surface((R * 2 + 8, R * 2 + 8), pygame.SRCALPHA)
                P.circle(sf, (110, 210, 255, 42), (R + 4, R + 4), R)
                P.circle(sf, (170, 235, 255, 170), (R + 4, R + 4), R, 4)
                self._shieldt_surf = sf
            surf.blit(self._shieldt_surf, (sx - R - 4, sy - R - 4))
            for i in range(8):
                a = tm * 1.6 + i * math.tau / 8
                P.circle(surf, (215, 247, 255), (int(sx + math.cos(a) * R), int(sy + math.sin(a) * R)), 3)
        for an in self.fx_anims:
            k = min(1.0, an["t"] / an["dur"])
            if an["kind"] == "bomb":
                if an.get("ice"):
                    trail_c, core_c, edge_c, spark_c = (150, 215, 255), (225, 247, 255), (110, 190, 255), (255, 255, 255)
                else:
                    trail_c, core_c, edge_c, spark_c = (255, 225, 120), (255, 250, 200), GOLD_COLOR, (255, 150, 40)
                x = an["x0"] + (an["tx"] - an["x0"]) * k - cam_x
                y = an["y0"] + (an["ty"] - an["y0"]) * k - cam_y - math.sin(math.pi * k) * 150
                for j in range(5):
                    kk = max(0.0, k - j * 0.04)
                    tx_ = an["x0"] + (an["tx"] - an["x0"]) * kk - cam_x
                    ty_ = an["y0"] + (an["ty"] - an["y0"]) * kk - cam_y - math.sin(math.pi * kk) * 150
                    P.circle(surf, trail_c, (int(tx_), int(ty_)), max(2, 11 - j * 2))
                P.circle(surf, core_c, (int(x), int(y)), 15)
                P.circle(surf, edge_c, (int(x), int(y)), 15, 3)
                a = tm * 14
                for q in range(3 if an.get("ice") else 2):
                    aq = a + q * (math.pi / 3 if an.get("ice") else 1.57)
                    P.line(surf, spark_c, (x + math.cos(aq) * 10, y + math.sin(aq) * 10), (x - math.cos(aq) * 10, y - math.sin(aq) * 10), 3)
                if an["t"] < 0.3:   # pose melempar: lengan menyapu
                    px, py = b.x - cam_x, b.y - cam_y
                    ang = math.atan2(an["ty"] - an["y0"], an["tx"] - an["x0"]) + (1 - an["t"] / 0.3) * 1.6 - 0.8
                    P.line(surf, trail_c, (px, py), (px + math.cos(ang) * 46, py + math.sin(ang) * 46), 6)
                    P.circle(surf, core_c, (int(px + math.cos(ang) * 46), int(py + math.sin(ang) * 46)), 8)
            elif an["kind"] == "revive":
                px, py = int(b.x - cam_x), int(b.y - cam_y)
                fade = 1 - k
                # pilar cahaya turun dari atas
                w = int(70 * (1 - abs(2 * k - 1) * 0.6))
                P.rect(surf, (255, 245, 190), (px - w // 2, 0, w, py))
                P.rect(surf, (255, 255, 235), (px - w // 4, 0, max(2, w // 2), py))
                # sayap cahaya
                spread = min(1.0, k * 2.5)
                for sg in (-1, 1):
                    for f in range(5):
                        ang = -0.5 + f * 0.3
                        L = (50 + f * 14) * spread * 1.4
                        P.line(surf, (255, 225, 120), (px + sg * 12, py - 8), (px + sg * (12 + math.cos(ang) * L), py - 8 + math.sin(ang) * L - 20), 6)
                # cincin bangkit
                for j in range(3):
                    rr = int((k * 2.0 - j * 0.25) * 200)
                    if rr > 6:
                        P.circle(surf, (255, 235, 150), (px, py), rr, max(2, int(6 * fade) + 1))
                # bulu naik
                for i in range(14):
                    ph = (i * 0.37 + k * 1.5) % 1.0
                    P.circle(surf, (255, 240, 190), (int(px + math.sin(i * 2.3) * 70), int(py + 30 - ph * 160)), 3)
                txt = font_big.render("NYAWA KEDUA!", True, (255, 235, 140))
                a_ = max(0, min(255, int(255 * min(1.0, (1 - k) * 3))))
                txt.set_alpha(a_)
                surf.blit(txt, (px - txt.get_width() / 2, py - 140 - k * 40))

    def trigger_rune_shock(self, kind, freeze_time=3.0, cx=None, cy=None):
        """Gelombang kejut besar dari pemain; mengenai semua musuh begitu cincinnya melewati mereka.
        'freeze' = membekukan, 'nuke' = memusnahkan (musuh biasa)."""
        b = self.badang
        col = (170, 225, 255) if kind == "freeze" else (255, 130, 60)
        dur = 1.0
        self.effects.append({"x": b.x if cx is None else cx, "y": b.y if cy is None else cy, "radius": 1300, "timer": dur, "max_timer": dur, "color": col,
                             "shock": kind, "hit": set(), "rmax": 1300, "ftime": freeze_time})
        self.shake = max(self.shake, 1.0)
        self.flash_t = 0.3
        self.flash_col = (225, 245, 255) if kind == "freeze" else (255, 235, 200)
        sfx("boom")

    def update_rune_shocks(self):
        for eff in self.effects:
            if "shock" not in eff:
                continue
            prog = 1 - eff["timer"] / eff["max_timer"]
            r = eff["rmax"] * (1 - (1 - prog) ** 2)
            r2 = r * r
            hit = eff["hit"]
            ex, ey = eff["x"], eff["y"]
            for e in list(self.enemies):
                if e.dead or e.is_boss or id(e) in hit:
                    continue
                dx, dy = e.x - ex, e.y - ey
                if dx * dx + dy * dy > r2:
                    continue
                hit.add(id(e))
                if eff["shock"] == "freeze":
                    if not e.ice_immune:
                        e.frozen_timer = max(e.frozen_timer, eff["ftime"])
                    d = math.hypot(dx, dy) or 1.0
                    e.kb_vx, e.kb_vy, e.kb_timer = dx / d * 9.0, dy / d * 9.0, 0.3
                else:
                    self.damage_enemy(e, e.hp + e.armor + getattr(e, "shield", 0) + 9999, show_text=False, track=False)

    def apply_pickup(self, pk):
        if pk.kind == "magnet":
            self.pull_all_gems()
            self.show_toast("Magnet! Semua orb tertarik ke arahmu")
        elif pk.kind == "hporb":
            self.badang.hp = min(self.badang.max_hp, self.badang.hp + HEAL_ORB_AMOUNT)
            self.add_damage_text(self.badang.x, self.badang.y - 42, f"+{HEAL_ORB_AMOUNT}", DMG_COLOR_HEAL, big=True)
        elif pk.kind == "health":
            self.badang.hp = min(self.badang.max_hp, self.badang.hp + 30)
            self.add_damage_text(self.badang.x, self.badang.y - 42, "+30", DMG_COLOR_HEAL, big=True)
            self.show_toast("+30 HP")
        elif pk.kind == "freeze":
            self.trigger_rune_shock("freeze")
            self.show_toast("Rune Beku! Gelombang kejut membekukan musuh")
        elif pk.kind == "nuke":
            self.trigger_rune_shock("nuke")
            self.show_toast("Rune Hancur! Gelombang kejut memusnahkan musuh biasa")
        elif pk.kind == "chest":
            artifact = random.choice(build_artifact_pool(self.badang))
            artifact["apply"]()
            self.show_toast(f"Peti Harta: {artifact['name']}!")



    def lobby_rects(self):
        return {
            "avatar": pygame.Rect(60, 500, 400, 54),
            "toko": pygame.Rect(60, 566, 400, 54),
            "scores": pygame.Rect(500, 380, 360, 54),
            "back": pygame.Rect(880, 380, 360, 54),
            "normal": pygame.Rect(500, 450, 360, 100),
            "inflation": pygame.Rect(880, 450, 360, 100),
            "continue": pygame.Rect(500, 566, 740, 62),
        }

    def owned_list(self):
        return [i for i in range(len(AVATARS)) if self.owned(i)]

    AV_VIEW = pygame.Rect(0, 62, WIDTH, 540)
    TK_VIEW = pygame.Rect(0, 112, WIDTH, 392)

    def avatar_grid(self, idxs, cols, w, h, gap):
        """Susun avatar berurutan menurut gelar (Pemula, Menengah, Mahir, Legendaris) dengan judul pemisah.
        Koordinat konten (belum digulir). Mengembalikan (judul, kartu, tinggi total)."""
        order = sorted(idxs, key=lambda i: (AVATARS[i]["price"], i))
        x0 = (WIDTH - (cols * w + (cols - 1) * gap)) / 2
        y, cur, c = 4, -1, 0
        heads, items = [], []
        for i in order:
            pr = AVATARS[i]["price"]
            t = next(k for k, (_n, lim, _c) in enumerate(AVATAR_TIERS) if pr <= lim)
            if t != cur:
                if c:
                    y += h + gap
                    c = 0
                heads.append((AVATAR_TIERS[t][0], AVATAR_TIERS[t][2], y))
                y += 34
                cur = t
            items.append((i, pygame.Rect(x0 + c * (w + gap), y, w, h)))
            c += 1
            if c == cols:
                c = 0
                y += h + gap
        if c:
            y += h + gap
        return heads, items, y

    def avatar_cards(self):
        return self.avatar_grid(self.owned_list(), 5, 232, 268, 16)

    def toko_cards(self):
        return self.avatar_grid(list(range(len(AVATARS))), 8, 150, 176, 10)

    def clamp_scroll(self, v, total, view_h):
        return max(0.0, min(float(max(0, total - view_h)), v))

    def back_rect(self):
        return pygame.Rect(WIDTH / 2 - 170, 634, 340, 50)

    def buy_rect(self):
        return pygame.Rect(WIDTH / 2 - 350, 634, 340, 50)

    def back_rect2(self):
        return pygame.Rect(WIDTH / 2 + 10, 634, 340, 50)

    def pause_button_center(self):
        return (WIDTH - 62, 50)

    def pause_hit(self, pos, norm=None):
        """Tombol pause: area persegi besar di pojok kanan atas, ATAU pojok layar fisik (koordinat ternormalisasi),
        supaya tetap bisa ditekan walau layar di-skala/letterbox atau ada poni/lengkung layar."""
        if pos is not None and pos[0] >= WIDTH - 150 and pos[1] <= 104:
            return True
        if norm is not None and norm[0] >= 0.90 and norm[1] <= 0.15:
            return True
        return False

    def pause_rects(self):
        return {"resume": pygame.Rect(WIDTH / 2 - 190, HEIGHT / 2 + 10, 380, 56),
                "menu": pygame.Rect(WIDTH / 2 - 190, HEIGHT / 2 + 80, 380, 56)}

    def toggle_pause(self):
        """Jeda/lanjut. Kunci waktu mencegah dobel-toggle (sentuhan + klik mouse tiruan)."""
        now = time.time()
        if now < getattr(self, "pause_lock", 0.0):
            return
        self.pause_lock = now + 0.3
        if self.state == "playing":
            self.state = "paused"
            self.joystick_finger_id = None
            self.move_vector = (0.0, 0.0)
            self.save_run()
            sfx("click")
        elif self.state == "paused":
            self.state = "playing"
            sfx("click")

    def auto_pause(self):
        if self.state == "playing":
            self.pause_lock = 0.0
            self.toggle_pause()

    def pause_click(self, pos):
        r = self.pause_rects()
        if r["resume"].collidepoint(pos):
            self.toggle_pause()
        elif r["menu"].collidepoint(pos):
            self.save_run()
            self.reset(None)
            self.state = "title"
            self.title_t = 0.0
            sfx("click")


    def cycle_setting(self, key, steps):
        cur = SETTINGS[key]
        idx = min(range(len(steps)), key=lambda i: abs(steps[i] - cur))
        SETTINGS[key] = steps[(idx + 1) % len(steps)]
        apply_volumes()
        self.save.data["settings"] = dict(SETTINGS)
        self.save.save()
        sfx("click")

    def continue_run(self):
        run = self.save.data.get("run")
        if not run:
            return
        idx = next((i for i, a in enumerate(AVATARS) if a["key"] == run.get("avatar")), self.selected_avatar)
        self.selected_avatar = idx
        self.start_run(run.get("mode") or "normal", run)

    def lobby_click(self, pos):
        r = self.lobby_rects()
        if r["avatar"].collidepoint(pos):
            sfx("click")
            self.state = "avatars"
        elif r["toko"].collidepoint(pos):
            sfx("click")
            self.toko_from = "menu"
            self.state = "toko"
        elif r["scores"].collidepoint(pos):
            sfx("click")
            self.state = "scores"
        elif r["back"].collidepoint(pos):
            self.go_back()
        elif r["normal"].collidepoint(pos):
            self.request_new_run("normal")
        elif r["inflation"].collidepoint(pos):
            self.request_new_run("inflation")
        elif self.save.data.get("run") and r["continue"].collidepoint(pos):
            self.continue_run()

    def request_new_run(self, mode):
        """Bila ada game tersimpan, minta konfirmasi dulu supaya tidak hilang karena salah tekan."""
        if self.save.data.get("run"):
            self.pending_mode = mode
            self.state = "confirm_new"
            sfx("click")
        else:
            self.start_run(mode)

    def confirm_rects(self):
        return {"yes": pygame.Rect(WIDTH / 2 - 320, 400, 300, 64), "no": pygame.Rect(WIDTH / 2 + 20, 400, 300, 64)}

    def confirm_click(self, pos):
        r = self.confirm_rects()
        if r["yes"].collidepoint(pos):
            self.save.data["run"] = None
            self.save.save()
            self.start_run(self.pending_mode)
        elif r["no"].collidepoint(pos):
            sfx("click")
            self.state = "menu"

    def draw_confirm(self, surf):
        surf.fill(BG_COLOR)
        self.draw_lobby(surf)
        veil = veil_surface((0, 0, 0, 190))
        surf.blit(veil, (0, 0))
        box = pygame.Rect(WIDTH / 2 - 380, 190, 760, 300)
        pygame.draw.rect(surf, (16, 14, 32), box, border_radius=16)
        pygame.draw.rect(surf, HP_RED, box, 4, border_radius=16)
        t1 = font_big.render("Anda yakin ingin ulang dari awal?", True, WHITE)
        surf.blit(t1, (box.centerx - t1.get_width() / 2, box.y + 28))
        for i, ln in enumerate(("Game yang sedang berjalan akan HILANG", "dan diganti dengan permainan baru.")):
            t2 = font_med.render(ln, True, GOLD_COLOR)
            surf.blit(t2, (box.centerx - t2.get_width() / 2, box.y + 108 + i * 34))
        r = self.confirm_rects()
        self.draw_button(surf, r["yes"], "YA, ULANG", HP_RED)
        self.draw_button(surf, r["no"], "BATAL (simpan)", HP_GREEN)

    def avatars_click(self, pos):
        if self.buy_rect().collidepoint(pos):
            sfx("click")
            self.toko_from = "avatars"
            self.state = "toko"
        elif self.back_rect2().collidepoint(pos):
            self.leave_avatars()
        elif self.AV_VIEW.collidepoint(pos):
            self.av_press = [pos, self.av_scroll, False]

    def avatar_pick_at(self, pos):
        _h, items, _t = self.avatar_cards()
        for idx, rc in items:
            if rc.move(0, self.AV_VIEW.y - self.av_scroll).collidepoint(pos):
                self.selected_avatar = idx
                sfx("click")
                return

    def unlock_badge(self, key):
        lst = self.save.data.setdefault("badges", [])
        if key in lst or (self.mode == "tutorial" and key != "tutorial"):
            return
        lst.append(key)
        pend = self.save.data.setdefault("badge_pending", [])
        if key not in pend:
            pend.append(key)
        self.save.save()
        title = next((t for (k, t, _d, _i) in all_badges() if k == key), key)
        self.badge_queue.append((key, title))
        sfx("victory", 0.5)

    def record_kill(self, enemy):
        if self.mode == "tutorial" and not enemy.kind.get("robot"):
            return
        nm = enemy.kind["name"]
        if enemy.boss_kind == "jsab":
            nm = nm.title()
        kills = self.save.data.setdefault("almanac", {"kills": {}, "skills": []}).setdefault("kills", {})
        kills[nm] = kills.get(nm, 0) + 1

    def record_skills(self):
        al = self.save.data.setdefault("almanac", {"kills": {}, "skills": []})
        sk = al.setdefault("skills", [])
        b = self.badang
        names = []
        for w in b.all_weapons():
            names.append(w.display_name)
            if w.evo_base is not None:
                names.append(w.evo_base.display_name)
        names += [b.avatar["skill_name"]] + ["Combo: " + COMBO_TITLES[k] for k in ACTIVE_COMBOS]
        if self.mode == "tutorial":
            return
        for n in names:
            if n not in sk:
                sk.append(n)

    def badge_banner_ok(self):
        """Notifikasi lencana muncul di semua halaman dan saat bermain."""
        return True

    def update_badge_banner(self, dt):
        if not self.badge_banner_ok():
            return
        if self.badge_show is None and self.badge_queue:
            self.badge_show = [self.badge_queue.pop(0), 4.5]
            pend = self.save.data.get("badge_pending", [])
            if self.badge_show[0][0] in pend:
                pend.remove(self.badge_show[0][0])
                self.save.save()
        if self.badge_show is not None:
            self.badge_show[1] -= dt
            if self.badge_show[1] <= 0:
                self.badge_show = None

    def draw_badge_banner(self, surf):
        if self.badge_show is None or not self.badge_banner_ok():
            return
        (key, title), left = self.badge_show
        k = min(1.0, (4.5 - left) / 0.35, left / 0.35)
        w, h = 430, 78
        x = WIDTH / 2 - w / 2
        y = -h + (h + 150) * max(0.0, k)
        box = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surf, (24, 18, 44), box, border_radius=14)
        pygame.draw.rect(surf, GOLD_COLOR, box, 4, border_radius=14)
        cx, cy = int(box.x + 44), int(box.centery)
        self.draw_medal_frame(surf, cx, cy, 33, self.badge_color(key), True)
        icon = next((b[3] for b in all_badges() if b[0] == key), None)
        self.draw_badge_icon(surf, cx, cy, 33, icon, self.build_almanac()["enemy"])
        surf.blit(font_small.render("LENCANA BARU!", True, GOLD_COLOR), (box.x + 86, box.y + 12))
        surf.blit(font_med.render(self.fit_text(font_med, title, w - 110), True, WHITE), (box.x + 86, box.y + 36))

    def toko_tab_rects(self):
        return {k: pygame.Rect(165 + i * 245, 64, 235, 46) for i, k in enumerate(("avatar", "peti", "koleksi", "buku"))}

    def book_rect(self, i):
        return pygame.Rect(90 + i * 400, 128, 380, 420)

    def book_buy_rect(self, i):
        r = self.book_rect(i)
        return pygame.Rect(r.x + 40, r.bottom - 74, r.width - 80, 56)

    def buy_book(self, i):
        key, name, price, _col, _desc = BOOKS[i]
        books = self.save.data.setdefault("books", [])
        if key in books:
            return
        have = self.save.data["crystals"]
        if have < price:
            sfx("deny")
            self.menu_msg, self.menu_msg_t = "Kristal kurang %d" % (price - have), 2.0
            return
        self.save.data["crystals"] = have - price
        books.append(key)
        self.save.save()
        self._rec_cache = None
        sfx("buy")
        self.menu_msg, self.menu_msg_t = "%s dibeli! Baca di ALMANAK > SKILL (bagian bawah)" % name, 4.0

    def toko_buy_rect(self):
        return pygame.Rect(WIDTH - 360, 520, 320, 64)

    def chest_rect(self, i):
        return pygame.Rect(90 + i * 400, 128, 380, 380)

    def chest_open_rect(self, i):
        r = self.chest_rect(i)
        return pygame.Rect(r.x + 40, r.bottom - 74, r.width - 80, 56)

    def chest_inv(self):
        d = self.save.data.get("chests")
        if not isinstance(d, dict):
            d = self.save.data["chests"] = {}
        return d

    def roll_chest(self, i):
        name, price, weights, col = CHESTS[i]
        inv = self.chest_inv()
        if inv.get(str(i), 0) > 0:
            inv[str(i)] -= 1
            self.open_chest_roll(i)
            return
        have = self.save.data["crystals"]
        if have < price:
            sfx("deny")
            self.menu_msg, self.menu_msg_t = "Kristal kurang %d" % (price - have), 2.0
            return
        self.save.data["crystals"] = have - price
        self.open_chest_roll(i)

    def open_chest_roll(self, i, quiet=False):
        name, price, weights, col = CHESTS[i]
        rar = random.choices(range(len(RARITIES)), weights=weights)[0]
        cands = [c for c in WEAPON_CLASSES if WEAPON_RARITY.get(c.__name__, 0) == rar] or list(WEAPON_CLASSES)
        cls = random.choice(cands)
        owned = self.save.data["owned_skills"]
        dup = cls.__name__ in owned
        refund = 0
        if dup:
            streak = int(self.save.data.get("gacha_bad", 0)) + 1
            self.save.data["gacha_bad"] = streak
            refund = int(RARITY_REFUND[WEAPON_RARITY.get(cls.__name__, 0)] * (1.0 + min(1.5, GACHA_BAD_LUCK_STEP * (streak - 1))))
            self.save.data["crystals"] += refund
        else:
            self.save.data["gacha_bad"] = 0
            owned.append(cls.__name__)
        self.save.save()
        if quiet:
            return cls, dup, refund
        self.gacha = {"cls": cls, "rar": WEAPON_RARITY.get(cls.__name__, 0), "dup": dup, "refund": refund, "t0": self.title_t, "chest": i}
        sfx("levelup" if not dup else "pickup")

    def toko_click(self, pos):
        if self.gacha:
            if self.title_t - self.gacha["t0"] > 0.7:
                self.gacha = None
            return
        if self.back_rect().collidepoint(pos):
            self.go_back()
            return
        for k, rc in self.toko_tab_rects().items():
            if rc.collidepoint(pos):
                self.toko_tab = k
                sfx("click")
                return
        if self.toko_tab == "avatar":
            if self.TK_VIEW.collidepoint(pos):
                self.tk_press = [pos, self.tk_scroll, False]
                return
            if self.toko_buy_rect().collidepoint(pos) and not self.owned(self.toko_sel):
                self.buy_avatar(self.toko_sel)
        elif self.toko_tab == "peti":
            for i in range(len(CHESTS)):
                if self.chest_open_rect(i).collidepoint(pos):
                    self.roll_chest(i)
                    return
        elif self.toko_tab == "buku":
            for i in range(len(BOOKS)):
                if self.book_buy_rect(i).collidepoint(pos):
                    self.buy_book(i)
                    return

    def draw_chest_icon(self, surf, cx, cy, sc, col, t):
        S = lambda v: int(v * sc)
        body = pygame.Rect(cx - S(50), cy - S(8), S(100), S(60))
        pygame.draw.rect(surf, _dk(col, 0.55), body, border_radius=S(6))
        pygame.draw.rect(surf, col, body.inflate(-S(8), -S(8)), border_radius=S(5))
        pygame.draw.arc(surf, _dk(col, 0.55), pygame.Rect(cx - S(50), cy - S(44), S(100), S(80)), 0, math.pi, S(8))
        pygame.draw.arc(surf, col, pygame.Rect(cx - S(46), cy - S(40), S(92), S(72)), 0, math.pi, S(5))
        pygame.draw.rect(surf, (60, 40, 20), (cx - S(50), cy + S(10), S(100), S(5)))
        pygame.draw.rect(surf, GOLD_COLOR, (cx - S(9), cy - S(2), S(18), S(24)), border_radius=S(3))
        pygame.draw.circle(surf, BLACK, (cx, cy + S(10)), max(2, S(3)))
        for k in range(3):
            a = t * 2 + k * 2.1
            pygame.draw.circle(surf, WHITE, (int(cx + math.cos(a) * S(58)), int(cy - S(10) + math.sin(a) * S(30))), max(2, S(3)))

    def draw_toko(self, surf):
        self.draw_page_header(surf, "TOKO")
        self.draw_crystals(surf, WIDTH - 24, 14)
        if self.menu_msg_t > 0:
            mt = font_med.render(self.menu_msg, True, XP_COLOR)
            surf.blit(mt, (24, 22))
        labels = {"avatar": "AVATAR", "peti": "PETI SKILL (GACHA)", "koleksi": "KOLEKSI SKILL", "buku": "BUKU RESEP"}
        for k, rc in self.toko_tab_rects().items():
            on = self.toko_tab == k
            self.draw_button(surf, rc, labels[k], GOLD_COLOR if on else GRAY, font_small, fill=(40, 34, 60) if on else None)
        t = pygame.time.get_ticks() / 1000.0
        if self.toko_tab == "avatar":
            heads, items, total = self.toko_cards()
            view = self.TK_VIEW
            self.tk_scroll = self.clamp_scroll(self.tk_scroll, total, view.h)
            off = view.y - self.tk_scroll
            old_clip = surf.get_clip()
            surf.set_clip(view)
            for nm_, col_, hy in heads:
                ty = hy + off
                pygame.draw.line(surf, col_, (40, ty + 14), (WIDTH - 40, ty + 14), 1)
                lab = font_med.render(nm_, True, col_)
                pygame.draw.rect(surf, BG_COLOR, (WIDTH / 2 - lab.get_width() / 2 - 14, ty, lab.get_width() + 28, 30))
                surf.blit(lab, (WIDTH / 2 - lab.get_width() / 2, ty))
            for i, rc0 in items:
                rc = rc0.move(0, off)
                if rc.bottom < view.y or rc.y > view.bottom:
                    continue
                av, own = AVATARS[i], self.owned(i)
                sel = i == self.toko_sel
                pygame.draw.rect(surf, PANEL_COLOR, rc, border_radius=10)
                pygame.draw.rect(surf, GOLD_COLOR if sel else (GRAY if own else (70, 70, 90)), rc, 4 if sel else 2, border_radius=10)
                cmp_ = rc.height < 160
                draw_wizard_cached(surf, rc.centerx, rc.y + (58 if cmp_ else 72), av, 0.75 if cmp_ else 0.95)
                nm = font_small.render(self.fit_text(font_small, av["name"], rc.width - 8), True, av["color"] if own else (130, 130, 150))
                surf.blit(nm, (rc.centerx - nm.get_width() / 2, rc.y + (100 if cmp_ else 116)))
                if cmp_:
                    if own:
                        tag = font_small.render("DIMILIKI", True, HP_GREEN)
                    else:
                        afford = self.save.data["crystals"] >= av["price"]
                        tag = font_small.render(str(av["price"]), True, (150, 230, 255) if afford else HP_RED)
                    surf.blit(tag, (rc.centerx - tag.get_width() / 2, rc.y + 124))
                    continue
                if own:
                    tag = font_small.render("DIMILIKI", True, HP_GREEN)
                    surf.blit(tag, (rc.centerx - tag.get_width() / 2, rc.y + 144))
                else:
                    afford = self.save.data["crystals"] >= av["price"]
                    col = (150, 230, 255) if afford else HP_RED
                    tag = font_small.render(str(av["price"]), True, col)
                    dx = rc.centerx - (tag.get_width() + 22) / 2
                    pts = [(dx + 7, rc.y + 146), (dx + 14, rc.y + 154), (dx + 7, rc.y + 162), (dx, rc.y + 154)]
                    pygame.draw.polygon(surf, (120, 215, 255), pts)
                    surf.blit(tag, (dx + 22, rc.y + 144))
                    pygame.draw.line(surf, (60, 60, 80), (rc.x + 6, rc.y + 6), (rc.x + 22, rc.y + 6), 3)
            surf.set_clip(old_clip)
            if total > view.h:
                bar_h = max(30, int(view.h * view.h / float(total)))
                by = view.y + int((view.h - bar_h) * (self.tk_scroll / float(total - view.h)))
                pygame.draw.rect(surf, (90, 90, 120), (WIDTH - 10, by, 5, bar_h), border_radius=3)
            av = AVATARS[self.toko_sel]
            panel = pygame.Rect(40, 512, WIDTH - 420, 108)
            pygame.draw.rect(surf, PANEL_COLOR, panel, border_radius=10)
            pygame.draw.rect(surf, GOLD_COLOR, panel, 2, border_radius=10)
            surf.blit(font_med.render(av["name"], True, av["color"]), (panel.x + 16, panel.y + 8))
            surf.blit(font_small.render("HP %d | Kecepatan x%.2f | Damage x%.2f" % (av["hp"], av["speed"], av.get("dmg", 1.0)), True, GRAY), (panel.x + 16, panel.y + 40))
            surf.blit(font_small.render("Skill: %s - %s" % (av["skill_name"], av["skill_desc"]), True, WHITE), (panel.x + 16, panel.y + 62))
            surf.blit(font_small.render(av["role"], True, GRAY), (panel.x + 16, panel.y + 84))
            br = self.toko_buy_rect()
            if self.owned(self.toko_sel):
                self.draw_button(surf, br, "SUDAH DIMILIKI", HP_GREEN)
            else:
                afford = self.save.data["crystals"] >= av["price"]
                self.draw_button(surf, br, "BELI  %d KRISTAL" % av["price"], XP_COLOR if afford else HP_RED)
        elif self.toko_tab == "peti":
            for i, (name, price, weights, col) in enumerate(CHESTS):
                r = self.chest_rect(i)
                pygame.draw.rect(surf, PANEL_COLOR, r, border_radius=14)
                pygame.draw.rect(surf, col, r, 3, border_radius=14)
                self.draw_chest_icon(surf, r.centerx, r.y + 80, 1.1, col, t)
                nm = font_med.render(name, True, col)
                surf.blit(nm, (r.centerx - nm.get_width() / 2, r.y + 142))
                y = r.y + 178
                for rar, wgt in enumerate(weights):
                    if wgt <= 0:
                        continue
                    tx = font_small.render("%s  %s%%" % (RARITIES[rar], ("%g" % wgt)), True, RARITY_COLORS[rar])
                    surf.blit(tx, (r.centerx - tx.get_width() / 2, y))
                    y += 22
                afford = self.save.data["crystals"] >= price
                stock = int(self.chest_inv().get(str(i), 0))
                if stock > 0:
                    self.draw_button(surf, self.chest_open_rect(i), "BUKA GRATIS  (simpanan x%d)" % stock, HP_GREEN, font_small)
                else:
                    self.draw_button(surf, self.chest_open_rect(i), "BUKA  %d KRISTAL" % price, XP_COLOR if afford else HP_RED, font_small)
            owned = len(self.save.data["owned_skills"])
            info = font_small.render("Koleksi: %d / %d skill. Skill langka lebih kuat. Duplikat dikembalikan sebagian jadi Kristal." % (owned, len(WEAPON_CLASSES)), True, GRAY)
            surf.blit(info, (WIDTH / 2 - info.get_width() / 2, 540))
            info2 = font_small.render("Hanya skill yang kamu miliki yang bisa muncul saat naik level.", True, GRAY)
            surf.blit(info2, (WIDTH / 2 - info2.get_width() / 2, 564))
        elif self.toko_tab == "buku":
            have_books = set(self.save.data.get("books", []))
            for i, (key, name, price, col, desc) in enumerate(BOOKS):
                r = self.book_rect(i)
                own = key in have_books
                pygame.draw.rect(surf, PANEL_COLOR, r, border_radius=14)
                pygame.draw.rect(surf, col if own else _dk(col, 0.7), r, 3, border_radius=14)
                draw_book_icon(surf, r.centerx, r.y + 88, 1.5, col, key)
                nm = font_med.render(name, True, col)
                surf.blit(nm, (r.centerx - nm.get_width() / 2, r.y + 156))
                for j, ln in enumerate(wrap_text(desc, font_small, r.width - 44)[:5]):
                    surf.blit(font_small.render(ln, True, WHITE), (r.x + 22, r.y + 190 + j * 21))
                cnt = font_small.render("Isi: %d resep" % book_count(key), True, GRAY)
                surf.blit(cnt, (r.centerx - cnt.get_width() / 2, r.bottom - 102))
                if own:
                    self.draw_button(surf, self.book_buy_rect(i), "SUDAH DIMILIKI", HP_GREEN, font_small)
                else:
                    afford = self.save.data["crystals"] >= price
                    self.draw_button(surf, self.book_buy_rect(i), "BELI  %d KRISTAL" % price, XP_COLOR if afford else HP_RED, font_small)
            i1 = font_small.render("Buku dibaca di ALMANAK > SKILL (gulir ke bagian bawah).", True, GRAY)
            surf.blit(i1, (WIDTH / 2 - i1.get_width() / 2, 566))
            i2 = font_small.render("Fusi tetap bisa dilakukan tanpa buku, tetapi hasil fusi baru terlihat di kartu bila memiliki Buku Fusi.", True, GRAY)
            surf.blit(i2, (WIDTH / 2 - i2.get_width() / 2, 590))
        else:
            owned = set(self.save.data["owned_skills"])
            y = 124
            for rar in range(len(RARITIES)):
                cl = [c for c in WEAPON_CLASSES if WEAPON_RARITY.get(c.__name__, 0) == rar]
                surf.blit(font_small.render("%s  (x%.2f damage)" % (RARITIES[rar], RARITY_MULT[rar]), True, RARITY_COLORS[rar]), (40, y + 2))
                for j, c in enumerate(cl):
                    rc = pygame.Rect(40 + j * 150, y + 22, 142, 58)
                    own = c.__name__ in owned
                    pygame.draw.rect(surf, PANEL_COLOR if own else (22, 22, 32), rc, border_radius=8)
                    pygame.draw.rect(surf, RARITY_COLORS[rar] if own else (50, 50, 64), rc, 2, border_radius=8)
                    if own:
                        self.draw_skill_icon(surf, {"cls": c}, rc.x + 26, rc.centery, 0.5)
                        surf.blit(font_tiny.render(self.fit_text(font_tiny, c.display_name, 92), True, WHITE), (rc.x + 50, rc.y + 12))
                        surf.blit(font_tiny.render(skill_tags_text(c)[:16], True, GRAY), (rc.x + 50, rc.y + 32))
                    else:
                        q = font_med.render("?", True, (80, 80, 100))
                        surf.blit(q, (rc.centerx - q.get_width() / 2, rc.centery - q.get_height() / 2))
                y += 86
        self.draw_button(surf, self.back_rect(), "KEMBALI", GRAY)
        if self.gacha:
            self.draw_gacha(surf)

    def draw_gacha(self, surf):
        g = self.gacha
        k = min(1.0, (self.title_t - g["t0"]) / 0.8)
        veil = veil_surface((0, 0, 0, 215))
        surf.blit(veil, (0, 0))
        col = RARITY_COLORS[g["rar"]]
        cx, cy = WIDTH // 2, 300
        t = pygame.time.get_ticks() / 1000.0
        for i in range(16):
            a = i * math.tau / 16 + t * 0.6
            pygame.draw.line(surf, _dk(col, 0.6), (cx, cy), (cx + math.cos(a) * 520 * k, cy + math.sin(a) * 520 * k), 14)
        pygame.draw.circle(surf, _dk(col, 0.5), (cx, cy), int(130 * k) + 2)
        pygame.draw.circle(surf, col, (cx, cy), int(120 * k) + 2, 6)
        if k >= 0.6:
            self.draw_skill_icon(surf, {"cls": g["cls"]}, cx, cy, 3.2)
            rt = font_big.render(RARITIES[g["rar"]].upper(), True, col)
            surf.blit(rt, (cx - rt.get_width() / 2, 440))
            nm = font_big.render(g["cls"].display_name, True, WHITE)
            surf.blit(nm, (cx - nm.get_width() / 2, 484))
            tg = font_med.render("Jenis: " + skill_tags_text(g["cls"]), True, GRAY)
            surf.blit(tg, (cx - tg.get_width() / 2, 530))
            msg = ("DUPLIKAT! +%d Kristal dikembalikan" % g["refund"]) if g["dup"] else "SKILL BARU! Masuk koleksi"
            ms = font_med.render(msg, True, GOLD_COLOR if not g["dup"] else (150, 230, 255))
            surf.blit(ms, (cx - ms.get_width() / 2, 566))
            tip = font_small.render("sentuh untuk lanjut", True, GRAY)
            surf.blit(tip, (cx - tip.get_width() / 2, 612))

    def go_back(self):
        """ESC / tombol kembali. Mengembalikan False bila sudah di halaman judul (keluar game)."""
        st = self.state
        if st == "title":
            return False
        if st == "avatars":
            self.leave_avatars()
            return True
        nxt = {"playmenu": "title", "storymenu": "playmenu", "menu": "storymenu", "settings": self.settings_from, "toko": self.toko_from,
               "almanac": "playmenu", "almanac_detail": "almanac", "badges": "playmenu", "quests": "playmenu", "scores": "menu",
               "victory": "menu"}.get(st)
        if nxt:
            if nxt == "title":
                self.title_t = max(self.title_t, 3.0)
            self.state = nxt
            sfx("click")
        return True

    def center_rect(self, y, w=400, h=66):
        return pygame.Rect(WIDTH / 2 - w / 2, y, w, h)

    def menu_rects(self, st):
        if st == "title":
            return {"play": self.center_rect(300), "settings": self.center_rect(386), "tutorial": self.center_rect(472)}
        if st == "playmenu":
            return {"story": self.center_rect(104, 460, 76), "almanac": self.center_rect(188, 460, 76),
                    "badges": self.center_rect(272, 460, 76), "quests": self.center_rect(356, 460, 76),
                    "toko": self.center_rect(440, 460, 76), "back": self.back_rect()}
        if st == "storymenu":
            return {"classic": self.center_rect(230, 560, 100), "event": self.center_rect(350, 560, 100), "back": self.back_rect()}
        return {}

    def settings_rows(self):
        return [pygame.Rect(240, 118 + i * 62, 820, 54) for i in range(len(SETTING_ROWS))]

    @staticmethod
    def menu_bg_surface():
        bg = getattr(Game, "_menu_bg", None)
        if bg is None:
            bg = pygame.Surface((WIDTH, HEIGHT))
            bg.fill((10, 8, 24))
            for i in range(70):
                x, y = (i * 173) % WIDTH, (i * 97) % 440
                c = 150 if i % 3 else 215
                bg.fill((c, c, min(255, c + 25)), (x, y, 2 if i % 5 else 3, 2 if i % 5 else 3))
            pygame.draw.circle(bg, (235, 230, 200), (1080, 120), 60)
            pygame.draw.circle(bg, (10, 8, 24), (1058, 104), 54)
            pygame.draw.polygon(bg, (20, 15, 42), [(0, HEIGHT), (0, 570), (260, 505), (530, 565), (810, 495), (1100, 555), (WIDTH, 505), (WIDTH, HEIGHT)])
            Game._menu_bg = bg
        return bg

    def draw_menu_bg(self, surf, t, parade=False):
        surf.blit(Game.menu_bg_surface(), (0, 0))
        for i in range(0, 70, 5):
            x, y = (i * 173) % WIDTH, (i * 97) % 440
            c = int(120 + 130 * (0.5 + 0.5 * math.sin(t * 2 + i)))
            surf.fill((c, c, min(255, c + 25)), (x, y, 3, 3))
        for i in range(10):
            x = (i * 211 + t * 22 * (1 + i % 3)) % WIDTH
            y = HEIGHT - ((t * 34 * (1 + i % 4) + i * 53) % HEIGHT)
            pygame.draw.circle(surf, (255, 150 + (i * 7) % 90, 60), (int(x), int(y)), 1 + i % 3)
        if parade:
            n = len(AVATARS)
            span = WIDTH + 320
            gap = span / n
            lo, hi = 60, WIDTH - 160
            old_clip = surf.get_clip()
            surf.set_clip(pygame.Rect(0, 0, WIDTH, HEIGHT))
            for j, av in enumerate(AVATARS):
                x = (t * 55 + j * gap) % span - 160
                if lo <= x <= hi:
                    bob = abs(math.sin(t * 6 + j)) * 7
                    draw_wizard_cached(surf, int(x), int(672 - bob * 0.6), av, 0.7)
            surf.set_clip(old_clip)

    def draw_title(self, surf):
        self._draw_title_base(surf)

    def _draw_title_base(self, surf):
        t = self.title_t
        self.draw_menu_bg(surf, t, parade=True)
        word = "WITCH SURVIVOR"
        step = 66
        x0 = WIDTH / 2 - (len(word) - 1) * step / 2
        for i, ch in enumerate(word):
            if ch == " ":
                continue
            p = max(0.0, min(1.0, (t - 0.15 - i * 0.07) / 0.75))
            c1, c3 = 1.70158, 2.70158
            f = 1 + c3 * (p - 1) ** 3 + c1 * (p - 1) ** 2
            y = -140 + (96 + 140) * f
            pulse = round((0.5 + 0.5 * math.sin(t * 3 - i * 0.45)) * 5) / 5.0
            col = (255, int(200 + 55 * pulse), int(60 + 150 * pulse))
            sh = font_huge.render(ch, True, (120, 60, 10))
            gl = font_huge.render(ch, True, col)
            surf.blit(sh, (x0 + i * step - sh.get_width() / 2 + 5, y + 6))
            surf.blit(gl, (x0 + i * step - gl.get_width() / 2, y))
        if t > 1.7:
            k = round(min(1.0, (t - 1.7) / 0.8) * 8) / 8.0
            c = (int(10 + 160 * k), int(8 + 150 * k), int(24 + 190 * k))
            sub = font_med.render("Penyihir Pemburu Monster", True, c)
            surf.blit(sub, (WIDTH / 2 - sub.get_width() / 2, 222 + 4 * math.sin(t * 2)))
        r = self.menu_rects("title")
        labels = (("play", "BERMAIN", HP_GREEN), ("settings", "PENGATURAN", WHITE), ("tutorial", "TUTORIAL", GOLD_COLOR))
        for i, (key, lab, col) in enumerate(labels):
            p = max(0.0, min(1.0, (t - 1.2 - i * 0.18) / 0.6))
            f = 1 - (1 - p) ** 3
            rect = r[key].move(int((1 - f) * -70), 0)
            if p > 0:
                self.draw_button(surf, rect, lab, col)
        ver = font_small.render(GAME_VERSION, True, GRAY)
        surf.blit(ver, (WIDTH - ver.get_width() - 16, HEIGHT - ver.get_height() - 10))
        if self.menu_msg_t > 0:
            mt = font_small.render(self.menu_msg, True, XP_COLOR)
            surf.blit(mt, (16, HEIGHT - 28))

    def check_event_alarm(self):
        if not getattr(self, "event_over", False) and event_remaining() <= 0:
            self.event_over = True
            try:
                self.show_toast(EVENT_EXPIRED_MSG)
                self.toast_timer = 8.0
            except Exception:
                pass

    def draw_page_header(self, surf, text):
        title = font_big.render(text, True, GOLD_COLOR)
        surf.blit(title, (WIDTH / 2 - title.get_width() / 2, 24))

    def draw_menu_page(self, surf):
        st = self.state
        if st == "title":
            self.draw_title(surf)
            return
        self.draw_menu_bg(surf, self.title_t)
        if st == "playmenu":
            self.draw_page_header(surf, "BERMAIN")
            r = self.menu_rects(st)
            self.draw_button(surf, r["story"], "STORY", HP_GREEN)
            self.draw_button(surf, r["almanac"], "ALMANAK", (120, 200, 255))
            self.draw_button(surf, r["badges"], "LENCANA", GOLD_COLOR)
            self.draw_button(surf, r["quests"], "QUEST", (150, 230, 160))
            n_cl = quest_claimable(self.save.data)
            if n_cl:
                pygame.draw.circle(surf, (230, 60, 60), (r["quests"].right - 22, r["quests"].y + 22), 14)
                nt = font_small.render(str(n_cl), True, WHITE)
                surf.blit(nt, (r["quests"].right - 22 - nt.get_width() / 2, r["quests"].y + 22 - nt.get_height() / 2))
            self.draw_button(surf, r["toko"], "TOKO", (255, 170, 60))
            self.draw_button(surf, r["back"], "KEMBALI", GRAY)
        elif st == "storymenu":
            self.draw_page_header(surf, "STORY")
            r = self.menu_rects(st)
            self.draw_button(surf, r["classic"], "CLASSIC", HP_GREEN)
            t1 = font_small.render("Lobi, pilih avatar, Mode Normal & Inflasi", True, GRAY)
            surf.blit(t1, (r["classic"].centerx - t1.get_width() / 2, r["classic"].bottom - 30))
            cd_ = fmt_countdown()
            if cd_ is None:
                self.draw_button(surf, r["event"], "EVENT", (255, 90, 90), fill=(40, 20, 24))
                t2 = font_small.render("Segera update file-nya!", True, (255, 210, 120))
            else:
                self.draw_button(surf, r["event"], "EVENT", (255, 215, 90), fill=(34, 30, 20))
                t2 = font_small.render(cd_, True, (255, 225, 140))
            surf.blit(t2, (r["event"].centerx - t2.get_width() / 2, r["event"].bottom - 30))
            self.draw_button(surf, r["back"], "KEMBALI", GRAY)
        elif st == "settings":
            self.draw_settings(surf)
        elif st == "almanac":
            self.draw_almanac(surf)
        elif st == "almanac_detail":
            self.draw_almanac_detail(surf)
        elif st == "badges":
            self.draw_badges(surf)
        elif st == "quests":
            self.draw_quests(surf)
        elif st == "toko":
            self.draw_toko(surf)

    def menu_page_click(self, pos, finger_id):
        st = self.state
        if st == "title":
            if self.title_t < 1.8:
                self.title_t = 3.0
                return
            r = self.menu_rects(st)
            if r["play"].collidepoint(pos):
                sfx("click")
                self.state = "playmenu"
            elif r["settings"].collidepoint(pos):
                sfx("click")
                self.settings_from = "title"
                self.state = "settings"
            elif r["tutorial"].collidepoint(pos):
                self.start_run("tutorial")
            return
        if st in ("playmenu", "storymenu"):
            r = self.menu_rects(st)
            if r["back"].collidepoint(pos):
                self.go_back()
            elif st == "playmenu":
                if r["story"].collidepoint(pos):
                    sfx("click")
                    self.state = "storymenu"
                elif r["almanac"].collidepoint(pos):
                    sfx("click")
                    self.al_scroll = 0.0
                    self.state = "almanac"
                elif r["badges"].collidepoint(pos):
                    sfx("click")
                    self.state = "badges"
                elif r["quests"].collidepoint(pos):
                    sfx("click")
                    quest_refresh(self.save.data)
                    self.state = "quests"
                elif r["toko"].collidepoint(pos):
                    sfx("click")
                    self.toko_from = "playmenu"
                    self.state = "toko"
            else:
                if r["classic"].collidepoint(pos):
                    sfx("click")
                    self.state = "menu"
                elif r["event"].collidepoint(pos):
                    sfx("deny")
                    self.menu_msg = "Segera update file-nya!" if event_remaining() <= 0 else "Event belum dimulai"
                    self.menu_msg_t = 2.5
            return
        if st == "settings":
            if self.back_rect().collidepoint(pos):
                self.go_back()
                return
            for rect, (key, _lab, steps, _fmt) in zip(self.settings_rows(), SETTING_ROWS):
                if rect.collidepoint(pos):
                    self.cycle_setting(key, steps)
            return
        if st == "almanac":
            t1, t2 = self.al_tab_rects()
            if self.back_rect().collidepoint(pos):
                self.go_back()
            elif t1.collidepoint(pos):
                self.al_tab, self.al_scroll = "skill", 0.0
                sfx("click")
            elif t2.collidepoint(pos):
                self.al_tab, self.al_scroll = "enemy", 0.0
                sfx("click")
            else:
                self.al_press = [pos, self.al_scroll, False]
            return
        if st == "almanac_detail":
            if self.back_rect().collidepoint(pos):
                self.go_back()
            else:
                self.det_press = [pos, self.det_scroll, False]
            return
        if st == "badges":
            if self.back_rect().collidepoint(pos):
                self.go_back()
            return
        if st == "quests":
            if self.back_rect().collidepoint(pos):
                self.go_back()
            else:
                self.quests_click(pos)
            return
        if st == "toko":
            self.toko_click(pos)
            return

    def wheel(self, dy):
        if self.state == "almanac_detail":
            self.det_scroll = max(0.0, min(self.det_max, self.det_scroll - dy * 60))
        elif self.state == "almanac":
            self.al_scroll = max(0.0, min(self.al_max_scroll(), self.al_scroll - dy * 70))
        elif self.state == "avatars":
            self.av_scroll -= dy * 70
        elif self.state == "toko" and self.toko_tab == "avatar":
            self.tk_scroll -= dy * 70

    def draw_settings(self, surf):
        self.draw_page_header(surf, "PENGATURAN")
        for rect, (key, lab, steps, fmt) in zip(self.settings_rows(), SETTING_ROWS):
            pygame.draw.rect(surf, PANEL_COLOR, rect, border_radius=10)
            pygame.draw.rect(surf, GRAY, rect, 2, border_radius=10)
            surf.blit(font_med.render(lab, True, WHITE), (rect.x + 20, rect.centery - 12))
            val = font_med.render(fmt(SETTINGS[key]), True, GOLD_COLOR)
            vb = pygame.Rect(rect.right - 210, rect.y + 7, 190, 40)
            pygame.draw.rect(surf, (12, 14, 24), vb, border_radius=8)
            pygame.draw.rect(surf, GOLD_COLOR, vb, 2, border_radius=8)
            surf.blit(val, (vb.centerx - val.get_width() / 2, vb.centery - val.get_height() / 2))
        hint = font_small.render("Sentuh baris untuk mengubah nilai. Pengaturan tersimpan otomatis.", True, GRAY)
        surf.blit(hint, (WIDTH / 2 - hint.get_width() / 2, 118 + len(SETTING_ROWS) * 62 + 4))
        self.draw_button(surf, self.back_rect(), "KEMBALI", GOLD_COLOR)

    def build_almanac(self):
        if self._al_cache:
            return self._al_cache
        en, seen = [], set()
        for k in ALL_SPAWN_TYPES + [SKELETON_TYPE, SPLIT_CHILD_TYPE, SPLIT_MID_TYPE, GSKEL_TYPE, MOTHER_MINI_TYPE]:
            if k["name"] in seen:
                continue
            seen.add(k["name"])
            en.append({"name": k["name"], "kind": k, "boss": False})
        for i, d in enumerate(BOSS_DEFS):
            en.append({"name": d["name"].title(), "kdef": d, "boss": True, "lvb": i})
        for bk in BOSS_ORDER:
            k = BOSS_TYPES_BY_KIND[bk]
            en.append({"name": k["name"], "kind": k, "boss": True, "bk": bk})
        for k in ROBOT_LIST:
            en.append({"name": k["name"], "kind": k, "boss": bool(k.get("robot_boss")), "robot": True,
                       "bk": "normal"})
        sk = []
        for c in WEAPON_CLASSES:
            sk.append({"name": c.display_name, "cls": c, "type": "Senjata"})
        for c in WEAPON_CLASSES:
            if c.evolved_name and c.evolved_name not in ("Evolusi", c.display_name):
                sk.append({"name": c.evolved_name, "icls": c, "type": "Evolusi", "desc": c.evolved_desc or c.base_desc, "evo_of": c})
        for (key, _c, title, desc) in COMBO_DEFS:
            sk.append({"name": "Combo: " + title, "type": "Combo", "desc": desc, "combo": key})
        for fkey, (fname, ftpl, fcol, ffx, fdesc) in _FR.items():
            sk.append({"name": fname, "type": "Fusi", "desc": fdesc, "fus": fkey, "col": fcol, "tpl": ftpl})
        for av in AVATARS:
            sk.append({"name": av["skill_name"], "type": "Skill Avatar (%s)" % av["name"], "desc": av["skill_desc"], "av": av})
        self._al_cache = {"enemy": en, "skill": sk}
        return self._al_cache

    def al_unlocked(self, tab, ent):
        al = self.save.data.get("almanac", {})
        if tab == "enemy":
            return al.get("kills", {}).get(ent["name"], 0) > 0
        return ent["name"] in al.get("skills", [])

    def al_tab_rects(self):
        return pygame.Rect(WIDTH / 2 - 300, 78, 290, 50), pygame.Rect(WIDTH / 2 + 10, 78, 290, 50)

    AL_COLS, AL_W, AL_H, AL_GAP, AL_Y0 = 8, 140, 104, 8, 140
    AL_VIEW = (0, 138, WIDTH, 468)

    def al_tile_rect(self, i):
        x0 = (WIDTH - (self.AL_COLS * self.AL_W + (self.AL_COLS - 1) * self.AL_GAP)) / 2
        r, c = divmod(i, self.AL_COLS)
        return pygame.Rect(x0 + c * (self.AL_W + self.AL_GAP), self.AL_Y0 + r * (self.AL_H + self.AL_GAP) - self.al_scroll, self.AL_W, self.AL_H)

    def al_max_scroll(self):
        n = len(self.build_almanac()[self.al_tab])
        rows = (n + self.AL_COLS - 1) // self.AL_COLS
        extra = (16 + self.recipe_layout()[1]) if self.al_tab == "skill" else 0
        return max(0.0, rows * (self.AL_H + self.AL_GAP) + extra - self.AL_VIEW[3] + 6)

    def recipe_layout(self):
        """Tata letak bagian RESEP (di bawah Almanak Skill): daftar baris + tinggi total. Di-cache per kepemilikan buku."""
        books = tuple(sorted(self.save.data.get("books", [])))
        c = self._rec_cache
        if c is not None and c[0] == books:
            return c[1], c[2]
        rows = []
        y = [0]

        def add(kind, h, data=None):
            rows.append((y[0], h, kind, data))
            y[0] += h
        add("title", 54)
        for (key, name, price, col, _desc) in BOOKS:
            own = key in books
            add("head", 40, (key, name, col, own, price))
            if not own:
                add("locked", 40, (name, price))
            elif key == "combo":
                for ent in COMBO_DEFS:
                    add("combo", 50, ent)
            elif key == "evo":
                for cls in WEAPON_CLASSES:
                    add("evo", 50, cls)
            else:
                for k in _FR:
                    add("fusion", 50, k)
                add("note", 56)
            y[0] += 14
        self._rec_cache = (books, rows, y[0])
        return rows, y[0]

    def draw_recipes(self, surf, y0, vy, vh):
        rows, _total = self.recipe_layout()
        x0, w = 60, WIDTH - 120
        by_name = {c.__name__: c for c in WEAPON_CLASSES}
        for (ry, h, kind, data) in rows:
            top = y0 + ry
            if top + h < vy or top > vy + vh:
                continue
            cy = top + (h - 6) // 2
            if kind == "title":
                tt = font_big.render("RESEP SIHIR", True, GOLD_COLOR)
                surf.blit(tt, (WIDTH / 2 - tt.get_width() / 2, top + 6))
                continue
            if kind == "head":
                key, name, col, own, price = data
                rc = pygame.Rect(x0, top, w, h - 4)
                pygame.draw.rect(surf, _dk(col, 0.35), rc, border_radius=8)
                pygame.draw.rect(surf, col, rc, 2, border_radius=8)
                draw_book_icon(surf, rc.x + 26, rc.centery, 0.38, col, key)
                surf.blit(font_med.render(name, True, col), (rc.x + 56, rc.y + 8))
                st = font_small.render("%d resep" % book_count(key) if own else "belum dibeli", True, WHITE if own else GRAY)
                surf.blit(st, (rc.right - st.get_width() - 16, rc.y + 12))
                continue
            if kind == "locked":
                nm, price = data
                msg = font_small.render("%s belum dibeli. Beli di TOKO > BUKU RESEP (%d Kristal)." % (nm, price), True, GRAY)
                surf.blit(msg, (x0 + 16, top + 8))
                continue
            if kind == "note":
                lines = wrap_text("Pasangan sihir lain tetap bisa difusikan. Hasilnya senjata fusi tetap dengan nama, bentuk serangan, dan efek menurut kedua sihir (terlihat di kartu fusi saat Buku Fusi dimiliki).", font_small, w - 32)
                for j, ln in enumerate(lines[:2]):
                    surf.blit(font_small.render(ln, True, GRAY), (x0 + 16, top + 4 + j * 20))
                continue
            rc = pygame.Rect(x0, top, w, h - 6)
            pygame.draw.rect(surf, PANEL_COLOR, rc, border_radius=8)
            pygame.draw.rect(surf, (70, 70, 92), rc, 1, border_radius=8)
            if kind == "combo":
                key, (ca, cb), title, desc = data
                draw_skill_icon_ent(surf, {"cls": ca}, rc.x + 34, cy, 0.42)
                surf.blit(font_med.render("+", True, WHITE), (rc.x + 60, cy - 9))
                draw_skill_icon_ent(surf, {"cls": cb}, rc.x + 100, cy, 0.42)
                draw_arrow(surf, rc.x + 128, cy, rc.x + 158)
                draw_skill_icon_ent(surf, {"combo": key}, rc.x + 184, cy, 0.4)
                surf.blit(font_small.render(title, True, COMBO_COLOR), (rc.x + 220, rc.y + 6))
                line = "%s + %s (keduanya harus evolusi): %s (+40%% damage)" % (ca.display_name, cb.display_name, desc)
                surf.blit(font_tiny.render(self.fit_text(font_tiny, line, rc.width - 240), True, GRAY), (rc.x + 220, rc.y + 28))
            elif kind == "evo":
                cls = data
                draw_skill_icon_ent(surf, {"cls": cls}, rc.x + 34, cy, 0.42)
                draw_arrow(surf, rc.x + 62, cy, rc.x + 92)
                draw_evo_icon(surf, cls, rc.x + 118, cy, 0.42, pygame.time.get_ticks() / 1000.0)
                surf.blit(font_small.render("%s  >  %s" % (cls.display_name, cls.evolved_name), True, GOLD_COLOR), (rc.x + 150, rc.y + 6))
                line = "Lv.5: %s (damage x2). Sihir lama dihapus, diganti sihir evolusi." % cls.evolved_desc
                surf.blit(font_tiny.render(self.fit_text(font_tiny, line, rc.width - 170), True, GRAY), (rc.x + 150, rc.y + 28))
            elif kind == "fusion":
                rec = fusion_recipe(*data)
                ca, cb = by_name.get(data[0]), by_name.get(data[1])
                if ca is None or cb is None:
                    continue
                draw_skill_icon_ent(surf, {"cls": ca}, rc.x + 34, cy, 0.42)
                surf.blit(font_med.render("+", True, WHITE), (rc.x + 60, cy - 9))
                draw_skill_icon_ent(surf, {"cls": cb}, rc.x + 100, cy, 0.42)
                draw_arrow(surf, rc.x + 128, cy, rc.x + 158)
                draw_fusion_icon(surf, rc.x + 184, cy, 0.5, rec["col"], rec["tpl"])
                surf.blit(font_small.render(rec["name"], True, _lt(rec["col"], 0.35)), (rc.x + 220, rc.y + 6))
                line = "%s + %s: %s" % (ca.display_name, cb.display_name, rec["desc"])
                surf.blit(font_tiny.render(self.fit_text(font_tiny, line, rc.width - 240), True, GRAY), (rc.x + 220, rc.y + 28))

    def fit_text(self, font, text, max_w):
        while font.size(text)[0] > max_w and len(text) > 3:
            text = text[:-2]
        return text

    def preview_obj(self, ent, max_r):
        key = (ent["name"], max_r)
        obj = self._prev_cache.get(key)
        if obj is None:
            if "kdef" in ent:
                obj = LevelBoss(ent["kdef"], 0, 0, 0, MODE_CONFIGS["normal"])
            else:
                obj = Enemy(ent["kind"], 0, 0, 0, is_boss=ent["boss"], boss_scale=0, spawn_at=(0, 0))
                if ent["boss"]:
                    obj.boss_kind = ent.get("bk", "normal")
                    obj.hands = [{"x": -330, "y": 120, "mode": "idle", "side": -1}, {"x": 330, "y": 120, "mode": "idle", "side": 1}] if obj.boss_kind == "final" else None
                obj.face = 0.5
                obj.preview = True
            obj.radius = min(obj.radius, max_r)
            self._prev_cache[key] = obj
        return obj

    def draw_enemy_preview(self, surf, ent, cx, cy, max_r):
        global ROBOT_MODE
        saved_rm = ROBOT_MODE
        ROBOT_MODE = bool(ent.get("robot"))
        try:
            self._draw_enemy_preview(surf, ent, cx, cy, max_r)
        finally:
            ROBOT_MODE = saved_rm

    def _draw_enemy_preview(self, surf, ent, cx, cy, max_r):
        obj = self.preview_obj(ent, max_r)
        obj.x, obj.y = 0.0, 0.0
        saved = SETTINGS["lvlabel"]
        SETTINGS["lvlabel"] = 0.0
        try:
            if isinstance(obj, LevelBoss):
                obj.draw(surf, -cx, -cy)
            else:
                if obj.boss_kind == "final":
                    for h, sd in zip(obj.hands, (-1, 1)):
                        h["x"], h["y"] = sd * obj.radius * 1.05, 0.0 + obj.radius * 0.5
                obj.draw(surf, -cx, -cy)
        finally:
            SETTINGS["lvlabel"] = saved

    def al_enemy_medal(self, ent, R):
        """Medali bulat untuk kotak Almanak: sprite musuh/boss digambar utuh, dipas ke dalam lingkaran (tidak terpotong,
        tidak menimpa nama), lalu di-cache."""
        key = ("almedal", ent["name"], R)
        spr = self._prev_cache.get(key)
        if spr is not None:
            return spr
        D = 2 * R + 6
        spr = pygame.Surface((D, D), pygame.SRCALPHA)
        c0 = D // 2
        boss = bool(ent.get("boss"))
        pygame.draw.circle(spr, (20, 18, 34), (c0, c0), R)
        try:
            size = 400
            tmp = pygame.Surface((size, size), pygame.SRCALPHA)
            cap = 36 if ent.get("bk") == "final" else 44
            self.draw_enemy_preview(tmp, ent, size // 2, size // 2, cap)
            br = tmp.get_bounding_rect(40)
            if br.w >= 2 and br.h >= 2:
                crop = tmp.subsurface(br).copy()
                diag = math.hypot(br.w, br.h)
                k = min((2 * R - 12) / diag, 3.0)
                nw, nh = max(2, int(br.w * k)), max(2, int(br.h * k))
                crop = pygame.transform.smoothscale(crop, (nw, nh))
                spr.blit(crop, (c0 - nw // 2, c0 - nh // 2))
        except Exception:
            pass
        pygame.draw.circle(spr, GOLD_COLOR if boss else GRAY, (c0, c0), R, 3)
        self._prev_cache[key] = spr
        return spr

    def draw_skill_icon(self, surf, ent, cx, cy, sc=1.0):
        draw_skill_icon_ent(surf, ent, cx, cy, sc)

    def draw_almanac(self, surf):
        self.draw_page_header(surf, "ALMANAK")
        ent = self.build_almanac()
        t1, t2 = self.al_tab_rects()
        c_sk = sum(1 for e in ent["skill"] if self.al_unlocked("skill", e))
        c_en = sum(1 for e in ent["enemy"] if self.al_unlocked("enemy", e))
        self.draw_button(surf, t1, "SKILL  %d/%d" % (c_sk, len(ent["skill"])), GOLD_COLOR if self.al_tab == "skill" else GRAY,
                         fill=(40, 34, 60) if self.al_tab == "skill" else None)
        self.draw_button(surf, t2, "ENEMY  %d/%d" % (c_en, len(ent["enemy"])), GOLD_COLOR if self.al_tab == "enemy" else GRAY,
                         fill=(40, 34, 60) if self.al_tab == "enemy" else None)
        vx, vy, vw, vh = self.AL_VIEW
        surf.set_clip(pygame.Rect(vx, vy, vw, vh))
        for i, e in enumerate(ent[self.al_tab]):
            r = self.al_tile_rect(i)
            if r.bottom < vy or r.top > vy + vh:
                continue
            unl = self.al_unlocked(self.al_tab, e)
            pygame.draw.rect(surf, PANEL_COLOR if unl else (22, 22, 32), r, border_radius=10)
            pygame.draw.rect(surf, (GOLD_COLOR if e.get("boss") else GRAY) if unl else (50, 50, 64), r, 2, border_radius=10)
            cx, cy = r.centerx, r.y + 44
            if unl:
                if self.al_tab == "enemy":
                    sp = self.al_enemy_medal(e, 38)
                    surf.blit(sp, (cx - sp.get_width() // 2, cy - sp.get_height() // 2))
                else:
                    self.draw_skill_icon(surf, e, cx, cy, 0.9)
            else:
                if self.al_tab == "enemy":
                    pygame.draw.circle(surf, (16, 16, 26), (cx, cy), 38)
                    pygame.draw.circle(surf, (50, 50, 64), (cx, cy), 38, 2)
                q = font_big.render("?", True, (70, 70, 90))
                surf.blit(q, (cx - q.get_width() / 2, cy - q.get_height() / 2))
            nm = self.fit_text(font_small, e["name"] if unl else "???", r.width - 10)
            tx = font_small.render(nm, True, WHITE if unl else (90, 90, 110))
            surf.blit(tx, (r.centerx - tx.get_width() / 2, r.bottom - 22))
        if self.al_tab == "skill":
            n_rows = (len(ent["skill"]) + self.AL_COLS - 1) // self.AL_COLS
            self.draw_recipes(surf, self.AL_Y0 + n_rows * (self.AL_H + self.AL_GAP) + 16 - self.al_scroll, vy, vh)
        surf.set_clip(None)
        hint = font_small.render("Geser untuk menggulir. Sentuh gambar untuk detail. Musuh terbuka setelah dikalahkan, skill setelah dimiliki.", True, GRAY)
        surf.blit(hint, (WIDTH / 2 - hint.get_width() / 2, 612))
        self.draw_button(surf, self.back_rect(), "KEMBALI", GOLD_COLOR)

    def al_open_detail(self, pos):
        ent = self.build_almanac()[self.al_tab]
        for i, e in enumerate(ent):
            r = self.al_tile_rect(i)
            if r.collidepoint(pos) and self.AL_VIEW[1] <= pos[1] <= self.AL_VIEW[1] + self.AL_VIEW[3]:
                if self.al_unlocked(self.al_tab, e):
                    self.al_sel = (self.al_tab, i)
                    self.det_scroll = 0.0
                    self.state = "almanac_detail"
                    sfx("click")
                else:
                    sfx("deny")
                return

    def draw_almanac_detail(self, surf):
        tab, i = self.al_sel
        e = self.build_almanac()[tab][i]
        left = pygame.Rect(50, 70, 430, 540)
        pygame.draw.rect(surf, PANEL_COLOR, left, border_radius=14)
        pygame.draw.rect(surf, GOLD_COLOR, left, 3, border_radius=14)
        right = pygame.Rect(500, 70, 750, 540)
        pygame.draw.rect(surf, PANEL_COLOR, right, border_radius=14)
        pygame.draw.rect(surf, GRAY, right, 2, border_radius=14)
        rows = []
        if tab == "enemy":
            self.draw_enemy_preview(surf, e, left.centerx, left.centery + (30 if e.get("bk") == "final" else 0), 130 if e.get("boss") else 90)
            if e.get("bk") == "final":
                pass
            kills = self.save.data.get("almanac", {}).get("kills", {}).get(e["name"], 0)
            if "kdef" in e:
                d = e["kdef"]
                rows = [("Tipe", "Enemy (Boss - %s)" % LEVEL_BOSS_NAME), ("Gelar", d.get("title", "Pengawal Arena")), ("Kecepatan", "melayang di arena"),
                        ("HP dasar", fmt_num(d["hp"])), ("Ukuran", "radius %d" % d["radius"]),
                        ("Damage", str(d["dmg"])), ("Tempo", "%d BPM" % d["bpm"]), ("Fase", "3 fase"), ("Muncul", "tiap kelipatan 10 level")]
                for pi, ph in enumerate(d["phases"]):
                    labs = []
                    for st_ in ph:
                        if st_:
                            lb = PATTERN_LABELS.get(st_[0], st_[0].upper())
                            if lb not in labs:
                                labs.append(lb)
                    rows.append(("Pola Fase %d" % (pi + 1), ", ".join(labs).title()))
                rows.append(("Dikalahkan", "%d kali" % kills))
                story = BOSS_STORY.get(e["name"], "Pengawal arena bertempo %d BPM. Serangannya mengikuti ketukan musik dan berubah di tiap fase." % d["bpm"])
            else:
                k = e["kind"]
                rows = [("Tipe", "Enemy (Boss)" if e["boss"] else "Enemy (Musuh biasa)"), ("Kelas", "Boss" if e["boss"] else enemy_class(k)),
                        ("Kecepatan", "%.2f" % k["speed"]), ("Damage", str(k["dmg"]))]
                if e["boss"]:
                    rows.insert(2, ("Gelar", BOSS_RANK_ROBOT.get(e["name"]) or BOSS_RANK.get(e.get("bk"), "Boss")))
                if e.get("robot"):
                    rows[0] = ("Tipe", "Robot Simulasi (Boss)" if e["boss"] else "Robot Simulasi")
                if k.get("armor"):
                    rows.append(("Armor", fmt_num(k["armor"])))
                if k.get("shield"):
                    rows.append(("Perisai", fmt_num(k["shield"])))
                rows += [("XP / Gold", "%s / %s" % (k["xp"], k["gold"]))]
                if e["boss"] and not e.get("robot"):
                    rows += [("HP dasar", fmt_num(k["hp"])), ("Ukuran", "radius %d" % k["radius"])]
                    if BOSS_MOVES.get(e["name"]):
                        rows.append(("Jurus", BOSS_MOVES[e["name"]]))
                elif e["boss"] and e.get("robot"):
                    rows += [("HP dasar", fmt_num(k["hp"])), ("Ukuran", "radius %d" % k["radius"]), ("Meniru", k.get("base_name") or "-")]
                    if BOSS_MOVES.get(k.get("base_name")):
                        rows.append(("Jurus", BOSS_MOVES[k["base_name"]]))
                    rows.append(("Muncul", "Hanya di Tutorial (tidak mati cepat)"))
                elif not e["boss"]:
                    rows += enemy_detail_rows(k)
                if not e["boss"] and e.get("robot"):
                    rows.append(("Meniru", k.get("base_name") or "-"))
                    rows.append(("Muncul", "Hanya di Tutorial"))
                if not e["boss"]:
                    rows.append(("Biaya spawn", str(enemy_cost(k))))
                    if k.get("min_lv"):
                        rows.append(("Muncul mulai", "LV %d" % k["min_lv"] if k["min_lv"] < 90 else "dipanggil boss"))
                fl = enemy_flags_text(k)
                if fl:
                    rows.append(("Kemampuan", ", ".join(fl)))
                rows.append(("Dikalahkan", "%d kali" % kills))
                if not e.get("robot") and not e["boss"] and LORE.get(e["name"]):
                    rows.append(("Ringkasan", LORE[e["name"]]))
                if e["boss"] and not e.get("robot"):
                    story = BOSS_STORY.get(e["name"]) or LORE.get(e["name"], "Makhluk misterius dari dunia sihir.")
                elif e.get("robot"):
                    story = LORE.get(e["name"], "Robot simulasi.") + ROBOT_STORY
                else:
                    story = ENEMY_STORY.get(e["name"]) or LORE.get(e["name"], "Makhluk misterius dari dunia sihir.")
        else:
            self.draw_skill_icon(surf, e, left.centerx, left.centery, 3.2)
            cls = e.get("cls")
            if "evo_of" in e:
                tags = (WEAPON_TAGS.get(e["evo_of"].__name__) or ["Umum"]) + ["Evolusi"]
            elif "fus" in e:
                tags = FUSION_TPL_TAGS.get(e["tpl"], ["Fusi"])
            else:
                tags = WEAPON_TAGS.get(cls.__name__) if cls else (AVATAR_SKILL_TAGS.get(e["av"]["key"]) if "av" in e else ["Combo", "Buff"])
            rows = [("Tipe", "Skill (%s)" % e["type"]), ("Jenis", " | ".join(tags or ["Umum"]))]
            if cls:
                _rar = WEAPON_RARITY.get(cls.__name__, 0)
                rows.append(("Kelangkaan", "%s (damage x%.2f)" % (RARITIES[_rar], RARITY_MULT[_rar])))
                rows.append(("Deskripsi", cls.base_desc))
                if cls.evolved_desc:
                    rows.append(("Evolusi Lv.5", "%s - %s" % (cls.evolved_name, cls.evolved_desc)))
                story = SKILL_STORY.get(e["name"]) or SKILL_LORE.get(cls.__name__, "Sihir kuno yang diwariskan para penyihir.")
            elif "evo_of" in e:
                rows.append(("Asal", "%s (butuh Buku Evolusi)" % e["evo_of"].display_name))
                rows.append(("Efek", e["desc"]))
                story = SKILL_STORY.get(e["name"]) or "Bentuk evolusi dari %s. Sihir lama hilang dan diganti sihir ini." % e["evo_of"].display_name
            elif "fus" in e:
                a_, b_ = (_class_by_name(x) for x in e["fus"])
                rows.append(("Resep", "%s + %s" % (a_.display_name, b_.display_name)))
                rows.append(("Efek", e["desc"]))
                rows.append(("Catatan", "Kedua sihir asal hilang setelah fusi."))
                story = SKILL_STORY.get(e["name"]) or "Senjata fusi: dua sihir dilebur jadi satu senjata baru. Kedua sihir asal hilang."
            elif "combo" in e:
                _cd = next((c_ for c_ in COMBO_DEFS if c_[0] == e["combo"]), None)
                if _cd:
                    rows.append(("Syarat", "%s + %s (keduanya sudah berevolusi)" % (_cd[1][0].display_name, _cd[1][1].display_name)))
                rows.append(("Efek", e["desc"] + " (+40% damage)"))
                story = SKILL_STORY.get(e["name"]) or "Bila dua skill sama-sama berevolusi, kekuatan keduanya menyatu menjadi combo yang menambah damage."
            else:
                rows.append(("Efek", e["desc"]))
                _av = e.get("av")
                if _av:
                    rows.append(("Pemilik", "%s - %s" % (_av["name"], _av.get("role", ""))))
                    rows.append(("Status", "HP %s, kecepatan x%.2f, senjata awal %s" % (_av["hp"], _av["speed"], _av["start"].display_name)))
                    rows.append(("Harga", "gratis" if not _av.get("price") else "%d Kristal" % _av["price"]))
                story = SKILL_STORY.get(e["name"]) or "Skill khusus %s. Aktif otomatis saat musuh mendekat." % e["type"].split("(")[-1].rstrip(")")
        nm = font_big.render(e["name"], True, GOLD_COLOR)
        surf.blit(nm, (right.x + 24, right.y + 14))
        area = pygame.Rect(right.x + 6, right.y + 66, right.width - 12, right.height - 74)
        prev_clip = surf.get_clip()
        surf.set_clip(area)
        y0 = area.y + 6 - self.det_scroll
        y = y0
        for lab, val in rows:
            lines = wrap_text(str(val), font_small, right.width - 220)[:8]
            if area.y - 40 < y < area.bottom:
                surf.blit(font_small.render(lab + ":", True, GRAY), (right.x + 24, y + 3))
            for ln in lines:
                if area.y - 24 < y < area.bottom:
                    surf.blit(font_small.render(ln, True, WHITE), (right.x + 190, y + 3))
                y += 20
            y += 8
        y += 6
        if area.y - 4 < y < area.bottom:
            pygame.draw.line(surf, GRAY, (right.x + 24, y), (right.right - 24, y), 1)
        y += 12
        if area.y - 24 < y < area.bottom:
            surf.blit(font_small.render("CERITA", True, GOLD_COLOR), (right.x + 24, y))
        y += 24
        for ln in wrap_text(story, font_small, right.width - 50):
            if area.y - 24 < y < area.bottom:
                surf.blit(font_small.render(ln, True, WHITE), (right.x + 24, y))
            y += 20
        content_h = y - y0 + 12
        surf.set_clip(prev_clip)
        self.det_max = max(0.0, content_h - area.height)
        self.det_scroll = max(0.0, min(self.det_max, self.det_scroll))
        if self.det_max > 0:
            bar_h = max(30, int(area.height * area.height / (area.height + self.det_max)))
            bar_y = area.y + int((area.height - bar_h) * (self.det_scroll / self.det_max))
            pygame.draw.rect(surf, (90, 90, 110), (right.right - 12, bar_y, 6, bar_h), border_radius=3)
            hint = font_small.render("geser / scroll untuk membaca", True, GRAY)
            surf.blit(hint, (right.right - hint.get_width() - 24, right.y + 22))
        self.draw_button(surf, self.back_rect(), "KEMBALI", GOLD_COLOR)

    def draw_medal_frame(self, surf, cx, cy, R, bc, got, t=0.0):
        """Medali: bingkai lingkaran logam bergerigi + cincin + latar berwarna bersinar. Ikon digambar oleh pemanggil."""
        if not got:
            pygame.draw.circle(surf, (58, 58, 74), (cx, cy), R)
            pygame.draw.circle(surf, (36, 36, 48), (cx, cy), int(R * 0.82))
            pygame.draw.circle(surf, (70, 70, 88), (cx, cy), int(R * 0.82), 2)
            for i in range(24):
                a = i * math.tau / 24
                pygame.draw.circle(surf, (80, 80, 98), (int(cx + math.cos(a) * R * 0.91), int(cy + math.sin(a) * R * 0.91)), max(1, int(R * 0.035)))
            return
        gold, gold_d = (240, 200, 90), (150, 105, 25)
        pygame.draw.circle(surf, gold_d, (cx, cy), R)
        pygame.draw.circle(surf, gold, (cx, cy), R - 2)
        for i in range(24):
            a = i * math.tau / 24 + 0.1
            pygame.draw.circle(surf, gold_d, (int(cx + math.cos(a) * R * 0.91), int(cy + math.sin(a) * R * 0.91)), max(2, int(R * 0.05)))
        pygame.draw.circle(surf, gold_d, (cx, cy), int(R * 0.80))
        pygame.draw.circle(surf, _dk(bc, 0.5), (cx, cy), int(R * 0.77))
        pygame.draw.circle(surf, bc, (cx, cy), int(R * 0.70))
        pygame.draw.circle(surf, _lt(bc, 0.30), (cx, cy), int(R * 0.52))
        for i in range(12):
            a = i * math.tau / 12 + t * 0.2
            pygame.draw.line(surf, _lt(bc, 0.45), (cx + math.cos(a) * R * 0.30, cy + math.sin(a) * R * 0.30),
                             (cx + math.cos(a) * R * 0.68, cy + math.sin(a) * R * 0.68), 1)
        pygame.draw.arc(surf, WHITE, pygame.Rect(cx - R * 0.64, cy - R * 0.64, R * 1.28, R * 1.28), 2.0, 2.9, max(2, int(R * 0.06)))
        pygame.draw.circle(surf, WHITE, (int(cx - R * 0.42), int(cy - R * 0.5)), max(2, int(R * 0.06)))

    def badge_color(self, key):
        bc = BADGE_COLORS.get(key)
        if bc is None and key.startswith("lvb_"):
            bc = BOSS_DEFS[int(key.split("_")[1])]["color"]
        return bc or GOLD_COLOR

    def draw_badge_icon(self, surf, cx, cy, R, icon, al):
        sc = R / 50.0
        S = lambda v: int(v * sc)
        if icon == "final":
            R = int(R * 0.78)
        if icon == "tutorial":
            pygame.draw.rect(surf, (150, 165, 185), (cx - S(21), cy - S(14), S(42), S(34)), border_radius=S(7))
            pygame.draw.rect(surf, (50, 60, 80), (cx - S(21), cy - S(14), S(42), S(34)), max(1, S(3)), border_radius=S(7))
            pygame.draw.line(surf, (50, 60, 80), (cx, cy - S(14)), (cx, cy - S(26)), max(1, S(3)))
            pygame.draw.circle(surf, (255, 90, 80), (cx, cy - S(28)), max(2, S(4)))
            for sg in (-1, 1):
                pygame.draw.rect(surf, (90, 230, 255), (cx + sg * S(9) - S(6), cy - S(5), S(12), S(10)), border_radius=max(1, S(3)))
        elif icon is None:
            pygame.draw.polygon(surf, (235, 240, 255), [(cx - S(20), cy + S(12)), (cx + S(20), cy + S(12)), (cx + S(7), cy - S(26))])
            pygame.draw.ellipse(surf, (235, 240, 255), (cx - S(30), cy + S(4), S(60), S(15)))
            pygame.draw.line(surf, GOLD_COLOR, (cx - S(18), cy + S(4)), (cx + S(18), cy + S(4)), max(2, S(4)))
        else:
            ent = next((e for e in al if (e.get("bk") == icon) or (("lvb_%d" % e["lvb"]) == icon if "lvb" in e else False)), None)
            if ent:
                self.draw_enemy_preview(surf, ent, cx, cy + S(3 if icon != "final" else 12), max(8, int(R * (0.52 if icon != "final" else 0.4))))

    def quest_row_rect(self, col, i):
        return pygame.Rect(60 + col * 600, 196 + i * 138, 580, 124)

    def quest_claim_rect(self, col, i):
        r = self.quest_row_rect(col, i)
        return pygame.Rect(r.right - 150, r.bottom - 54, 130, 40)

    def quests_click(self, pos):
        q = quest_refresh(self.save.data)
        for col, key in enumerate(("daily", "weekly")):
            for i, e in enumerate(q[key]):
                if self.quest_claim_rect(col, i).collidepoint(pos):
                    _id, _txt, _stat, target, rw = QUEST_BY_ID[e["id"]]
                    if e["claimed"] or e["p"] < target:
                        sfx("deny")
                        return
                    e["claimed"] = True
                    self.save.data["crystals"] = int(self.save.data.get("crystals", 0)) + rw
                    ti = quest_chest_tier(rw)
                    sfx("buy")
                    if random.random() < QUEST_CHEST_CHANCE[ti]:
                        inv = self.chest_inv()
                        inv[str(ti)] = inv.get(str(ti), 0) + 1
                        self.menu_msg = "+%d Kristal & %s! Disimpan di TOKO > Peti" % (rw, CHESTS[ti][0])
                    else:
                        self.menu_msg = "+%d Kristal dari quest!" % rw
                    self.save.save()
                    self.menu_msg_t = 4.0
                    return

    def draw_quests(self, surf):
        import datetime
        self.draw_page_header(surf, "QUEST")
        self.draw_crystals(surf, WIDTH - 24, 14)
        q = quest_refresh(self.save.data)
        now = datetime.datetime.now()
        tomorrow = datetime.datetime.combine(now.date() + datetime.timedelta(days=1), datetime.time())
        left_d = tomorrow - now
        left_w = (7 - now.weekday()) * 86400 - (now - datetime.datetime.combine(now.date(), datetime.time())).total_seconds()
        heads = (("QUEST HARIAN", "reset %02d:%02d" % (left_d.seconds // 3600, (left_d.seconds % 3600) // 60), (255, 215, 90)),
                 ("QUEST MINGGUAN", "reset %d hari %d jam" % (left_w // 86400, (left_w % 86400) // 3600), (150, 200, 255)))
        for col, key in enumerate(("daily", "weekly")):
            title, sub, color = heads[col]
            x0 = 60 + col * 600
            surf.blit(font_med.render(title, True, color), (x0, 138))
            st_ = font_small.render(sub, True, GRAY)
            surf.blit(st_, (x0 + 580 - st_.get_width(), 148))
            for i, e in enumerate(q[key]):
                _id, text, stat, target, rw = QUEST_BY_ID[e["id"]]
                r = self.quest_row_rect(col, i)
                done = e["p"] >= target
                pygame.draw.rect(surf, PANEL_COLOR, r, border_radius=12)
                pygame.draw.rect(surf, HP_GREEN if e["claimed"] else (color if done else GRAY), r, 3, border_radius=12)
                surf.blit(font_med.render(self.fit_text(font_med, text, r.width - 40), True, WHITE), (r.x + 20, r.y + 14))
                bar = pygame.Rect(r.x + 20, r.y + 56, r.width - 40, 16)
                pygame.draw.rect(surf, (30, 30, 44), bar, border_radius=8)
                fw = int(bar.width * min(1.0, e["p"] / float(target)))
                if fw > 0:
                    pygame.draw.rect(surf, HP_GREEN if done else color, (bar.x, bar.y, fw, bar.height), border_radius=8)
                pt_ = font_small.render("%s / %s" % (fmt_num(e["p"]), fmt_num(target)), True, WHITE)
                surf.blit(pt_, (bar.centerx - pt_.get_width() / 2, bar.y - 1))
                ti_ = quest_chest_tier(rw)
                gx, gy = r.x + 34, r.bottom - 36
                pygame.draw.polygon(surf, (120, 215, 255), [(gx, gy - 14), (gx + 11, gy), (gx, gy + 14), (gx - 11, gy)])
                pygame.draw.polygon(surf, WHITE, [(gx, gy - 14), (gx + 11, gy), (gx, gy + 14), (gx - 11, gy)], 2)
                surf.blit(font_small.render("x%s" % fmt_num(rw), True, (150, 230, 255)), (gx + 18, gy - 8))
                cx_ = gx + 150
                old_c = surf.get_clip()
                surf.set_clip(pygame.Rect(cx_ - 22, gy - 22, 44, 44))
                self.draw_chest_icon(surf, cx_, gy, 0.42, CHESTS[ti_][3], pygame.time.get_ticks() / 1000.0)
                surf.set_clip(old_c)
                pc_ = QUEST_CHEST_CHANCE[ti_] * 100
                surf.blit(font_small.render("x1  (%s%%)" % (("%g" % pc_)), True, CHESTS[ti_][3]), (cx_ + 26, gy - 8))
                cr = self.quest_claim_rect(col, i)
                if e["claimed"]:
                    self.draw_button(surf, cr, "DIAMBIL", GRAY, font_small, fill=(26, 26, 36))
                elif done:
                    self.draw_button(surf, cr, "AMBIL", HP_GREEN, font_small)
                else:
                    self.draw_button(surf, cr, "BELUM", (90, 90, 110), font_small, fill=(26, 26, 36))
        hint = font_small.render("Progres dihitung saat satu permainan selesai (kalah atau menang), bukan saat Tutorial.", True, GRAY)
        surf.blit(hint, (WIDTH / 2 - hint.get_width() / 2, 606))
        if self.menu_msg_t > 0:
            mt = font_small.render(self.menu_msg, True, XP_COLOR)
            surf.blit(mt, (WIDTH / 2 - mt.get_width() / 2, 112))
        self.draw_button(surf, self.back_rect(), "KEMBALI", GOLD_COLOR)

    def draw_badges(self, surf):
        self.draw_page_header(surf, "LENCANA")
        owned = set(self.save.data.get("badges", []))
        bl = all_badges()
        surf.blit(font_small.render("%d / %d lencana" % (sum(1 for b in bl if b[0] in owned), len(bl)), True, GRAY), (24, 40))
        cols, w, h = 6, 200, 178
        x0 = (WIDTH - cols * w) / 2
        al = self.build_almanac()["enemy"]
        t = pygame.time.get_ticks() / 1000.0
        R = 54
        for i, (key, title, desc, icon) in enumerate(bl):
            r, c = divmod(i, cols)
            rect = pygame.Rect(x0 + c * w, 74 + r * h, w, h)
            got = key in owned
            cx, cy = rect.centerx, rect.y + R + 4
            mk = ("medal", key, got)
            spr = self._prev_cache.get(mk)
            if spr is None:
                spr = pygame.Surface((2 * R + 12, 2 * R + 12), pygame.SRCALPHA)
                c0 = R + 6
                self.draw_medal_frame(spr, c0, c0, R, self.badge_color(key), got, 0.0)
                if got:
                    self.draw_badge_icon(spr, c0, c0, R, icon, al)
                else:
                    lk = font_big.render("?", True, (96, 96, 118))
                    spr.blit(lk, (c0 - lk.get_width() / 2, c0 - lk.get_height() / 2))
                self._prev_cache[mk] = spr
            surf.blit(spr, (cx - R - 6, cy - R - 6))
            tt = font_small.render(self.fit_text(font_small, title if got else "???", w - 12), True, GOLD_COLOR if got else (96, 96, 118))
            surf.blit(tt, (rect.centerx - tt.get_width() / 2, rect.y + 2 * R + 14))
            for j, ln in enumerate(wrap_text(desc if got else "Belum didapat.", font_tiny, w - 16)[:2]):
                dt_ = font_tiny.render(ln, True, WHITE if got else (84, 84, 104))
                surf.blit(dt_, (rect.centerx - dt_.get_width() / 2, rect.y + 2 * R + 36 + j * 13))
        self.draw_button(surf, self.back_rect(), "KEMBALI", GOLD_COLOR)
    def open_shop(self, mer):
        self.shop_menu = ShopMenu(self, mer)
        self.state = "shop"
        if self.mode == "tutorial":
            self.tut["shop"] = True

    def evo_card(self, w):
        return {"kind": "evo", "name": f"EVOLUSI! {w.evolved_name}", "desc": f"{w.display_name} Lv.{EVOLVE_LEVEL}: {w.evolved_desc} (damage x2). Sihir lama diganti",
                "apply": (lambda w=w: w.level_up()), "rarity": w.rarity, "cls": type(w)}

    def tut_menu(self, title, cards):
        self.upgrade_menu = UpgradeMenu(self.badang, forced=cards)
        self.upgrade_menu.title = title
        self.state = "levelup"
        sfx("levelup")

    def tutorial_victory(self):
        self.save.save()
        self.victory_kind = "tutorial"
        self.unlock_badge("tutorial")
        self.state = "victory"
        sfx("victory")

    def tutorial_rects(self):
        panel = pygame.Rect(50, HEIGHT - 150, WIDTH - 100, 128)
        return panel, pygame.Rect(panel.right - 190, panel.y + 12, 170, 44), pygame.Rect(panel.right - 190, panel.y + 70, 170, 44)

    def tutorial_can_skip(self):
        """Tombol LEWATI/KELUAR hanya ada setelah Tutorial pernah diselesaikan dan lencananya didapat."""
        return "tutorial" in self.save.data.get("badges", [])

    def tutorial_exit(self):
        self.save.save()
        self.reset(None)
        self.state = "title"
        self.title_t = 0.0
        sfx("click")

    def tutorial_click(self, pos):
        panel, skip, leave = self.tutorial_rects()
        if not panel.collidepoint(pos):
            return False
        if not self.tutorial_can_skip():
            return True
        if leave.collidepoint(pos):
            self.tutorial_exit()
        elif skip.collidepoint(pos):
            if self.tut["i"] >= len(TUT_STEPS) - 1:
                self.tutorial_exit()
            else:
                self.tut["i"] += 1
                self.tut["entered"] = False
                sfx("click")
        return True

    def tutorial_update(self, dt):
        T, b = self.tut, self.badang
        T["t"] += dt
        i = T["i"]
        wm = 0.0
        def bots(k, a, d):
            e_ = Enemy(k, wm, 0, 0, spawn_at=(b.x + math.cos(a) * d, b.y + math.sin(a) * d), mode_config=self.mode_config)
            self.tut_toughen(e_)
            self.enemies.append(e_)

        def squad(spec, d=440):
            n = sum(c for _k, c in spec)
            a0, j = random.uniform(0, math.tau), 0
            for key, c in spec:
                for _ in range(c):
                    bots(ROBOTS[key], a0 + j * math.tau / n, d + random.uniform(-40, 40))
                    j += 1

        def orbs_and_squad():
            for k in range(8):
                a = k * 0.785
                self.gems.append(XPGem(b.x + math.cos(a) * 140, b.y + math.sin(a) * 140, 2))
            self.gems.append(XPGem(b.x + 90, b.y - 90, int(b.xp_needed / XP_GAIN_MULT) + 5))
            squad([("pelari", 3)], 480)

        def hazard_start():
            T["haz"] = 0.5
            squad([("penembak", 2)], 520)

        def event_start():
            self.formation_music_t = 60.0

        if not T["entered"]:
            T["entered"], T["t"] = True, 0.0
            T["kills0"], T["lvl0"] = self.kills, b.level
            T["px"], T["py"], T["moved"] = b.x, b.y, 0.0
            if i == 0:
                self.merchant_dialog("intro")
            elif i == 1:
                self.merchant_dialog("attack", lambda: squad([("bolt", 5), ("kilat", 5)], 420))
            elif i == 2:
                self.merchant_dialog("orb", orbs_and_squad)
            elif i == 3:
                self.merchant_dialog("upgrade", lambda: squad([("bolt", 2), ("tank", 2)], 460))
            elif i == 4:
                self.merchant_dialog("hp", lambda: squad([("tank", 2), ("penerjang", 2)], 500))
            elif i == 5:
                T["haz"] = 99.0
                self.merchant_dialog("warn", hazard_start)
            elif i == 6:
                self.gold = max(self.gold, 400)
                self.spawn_merchant()
                for m in self.merchants:
                    m.stay_left = 1e9
                T["met"] = False
                T["shop"] = False
            elif i == 7:
                self.merchant_dialog("evo", self.tut_give_evolution)
            elif i == 8:
                self.merchant_dialog("combo", self.tut_second_evolution)
            elif i == 9:
                self.merchant_dialog("fusion", self.tut_fusion_menu)
            elif i == 10:
                self.merchant_dialog("avatar", lambda: squad([("drone", 5), ("penembak", 4), ("perisai", 3)], 420))
            elif i == 11:
                T["ev"], T["evcd"] = 0, 1.0
                self.merchant_dialog("event", event_start)
            elif i == 12:
                T["mini_dead"] = False
                self.merchant_dialog("miniboss", lambda: self.tut_spawn_boss(MINI_BOSS_ROBOT, 1700, "normal", "Mini Boss"))
            elif i in (13, 14):
                T["wave"], T["wcd"] = 0, 0.5
                self.merchant_dialog("wave1" if i == 13 else "wave2")
            elif i == 15:
                T["mini_dead"] = False
                T["esc"] = 12.0
                b.hp = b.max_hp
                self.merchant_dialog("mini2", lambda: self.tut_spawn_boss(MINI_BOSS_ROBOT2, 2600, "healer", "Mini Boss II"))
            elif i == 16:
                T["orb"], T["hcd"] = None, 6.0
                self.merchant_dialog("orb15")
            elif i == 17:
                b.hp = b.max_hp
                T["esc"] = 10.0
                self.merchant_dialog("finalstart", lambda: self.tut_spawn_boss(FINAL_BOSS_ROBOT, 5200, "brute", "UJIAN AKHIR"))
        if i == 0:
            T["moved"] = math.hypot(b.x - T["px"], b.y - T["py"])
            done = T["moved"] > 280
        elif i == 1:
            done = self.kills - T["kills0"] >= 10
        elif i == 2:
            done = b.level > T["lvl0"]
        elif i == 3:
            done = T["t"] > 20.0
        elif i == 4:
            done = T["t"] > 22.0
        elif i == 5:
            T["haz"] -= dt
            if T["haz"] <= 0:
                T["haz"] = 3.2
                self.add_hazard(Hazard("blast", b.x + random.uniform(-200, 200), b.y + random.uniform(-150, 150), 2.2, 0.4, 12, (255, 80, 80), radius=95))
                self.add_hazard(Hazard("beam", b.x - 300, b.y + random.uniform(-100, 100), 2.2, 0.4, 12, (255, 80, 80), angle=0.0, length=700, width=36))
                sfx("warn")
                self.after(1.1, lambda: sfx("warn"))
            done = T["t"] > 26.0
        elif i == 6:
            done = T["shop"] and self.state == "playing" and T["t"] > 3.0
        elif i == 7:
            done = any(w.evolved for w in b.all_weapons()) and self.state == "playing"
        elif i == 8:
            done = "steam" in ACTIVE_COMBOS and self.state == "playing"
        elif i == 9:
            done = b.fusions >= 1 and self.state == "playing"
        elif i == 10:
            done = (self.kills - T["kills0"] >= 12 and T["t"] > 18.0) or T["t"] > 80.0
        elif i == 11:
            w = self.formation_warn
            if w is not None:
                w["t"] -= dt
                if w["t"] <= 0:
                    self.fire_tut_event(w)
                    self.formation_warn = None
                    T["ev"] += 1
                    T["evcd"] = 16.0
            elif T["ev"] < 3:
                T["evcd"] -= dt
                if T["evcd"] <= 0:
                    self.start_tut_event()
            alive = sum(1 for e in self.enemies if not e.dead)
            done = (T["ev"] >= 3 and alive == 0 and T["t"] > 40.0) or T["t"] > 180.0
        elif i in (12, 15):
            done = bool(T.get("mini_dead"))
            if i == 15:
                T["esc"] = T.get("esc", 12.0) - dt
                if T["esc"] <= 0 and any(e.is_boss and not e.dead for e in self.enemies):
                    T["esc"] = 11.0
                    if sum(1 for e in self.enemies if not e.is_boss and not e.dead) < 6:
                        squad([("bolt", 2), ("tank", 1), ("drone", 2)], 460)
        elif i in (13, 14):
            waves = ([[("bolt", 3), ("kilat", 3), ("pelari", 2)], [("tank", 2), ("penerjang", 2), ("penembak", 2)], [("drone", 5), ("perisai", 2), ("zirah", 2)]] if i == 13 else
                     [[("zirah", 3), ("laser", 2), ("bom", 2), ("montir", 1), ("golem", 1)], [("granat", 3), ("kedip", 3), ("jitu", 2), ("pecah", 2)], [("raksasa", 1), ("petir", 2), ("racun", 2), ("hitam", 3), ("drone", 4)]])
            T["wcd"] -= dt
            alive = sum(1 for e in self.enemies if not e.dead)
            if T["wave"] < 3 and (T["wcd"] <= 0 or alive == 0):
                squad(waves[T["wave"]], 460)
                T["wave"] += 1
                T["wcd"] = 24.0
                sfx("warn")
            done = T["wave"] >= 3 and alive == 0
        elif i == 16:
            if b.level < 15 and (T.get("orb") is None or T["orb"] not in self.gems):
                a = random.uniform(0, math.tau)
                d = random.uniform(170, 240)
                T["orb"] = XPGem(b.x + math.cos(a) * d, b.y + math.sin(a) * d, int(b.xp_needed / XP_GAIN_MULT) + 5)
                self.gems.append(T["orb"])
            T["hcd"] -= dt
            if T["hcd"] <= 0:
                T["hcd"] = 14.0
                if sum(1 for e in self.enemies if not e.dead) < 6:
                    squad([("bolt", 2), ("kilat", 2)], 460)
            done = b.level >= 15 and self.state == "playing"
        else:
            done = False
            T["esc"] = T.get("esc", 10.0) - dt
            if T["esc"] <= 0 and any(e.is_boss and not e.dead for e in self.enemies):
                T["esc"] = 10.0
                if sum(1 for e in self.enemies if not e.is_boss and not e.dead) < 8:
                    squad(random.choice([[("bolt", 2), ("kilat", 2)], [("drone", 3), ("penembak", 1)], [("zirah", 2), ("perisai", 1)],
                                         [("montir", 1), ("tank", 2)], [("granat", 2), ("pelari", 2)]]), 460)
        if done and i < len(TUT_STEPS) - 1:
            T["i"] += 1
            T["entered"] = False
            sfx("pickup")
            if i == 9:
                for m in self.merchants:
                    m.stay_left = 5.0
            if i in (12, 14):
                b.hp = b.max_hp

    def tut_target(self):
        T, b = self.tut, self.badang
        i = T["i"]

        def nearest(lst):
            best, bd = None, 1e18
            for o in lst:
                if getattr(o, "dead", False):
                    continue
                d = dist_sq(o.x, o.y, b.x, b.y)
                if d < bd:
                    best, bd = o, d
            return best
        if i in (1, 4, 5, 10, 11, 13, 14):
            o = nearest(self.enemies)
            return (o.x, o.y, "ROBOT", (255, 220, 70)) if o else None
        if i in (2, 16):
            o = nearest(self.gems)
            return (o.x, o.y, "ORB", (90, 240, 130)) if o else None
        if i == 6 and self.merchants and not T.get("shop"):
            m = self.merchants[0]
            return (m.x, m.y, "PEDAGANG", GOLD_COLOR)
        if i in (12, 15, 17):
            o = nearest([e for e in self.enemies if e.is_boss])
            return (o.x, o.y, "BOSS", (255, 80, 80)) if o else None
        return None

    def draw_tut_guide(self, surf):
        T, b = self.tut, self.badang
        t = pygame.time.get_ticks() / 1000.0
        cx, cy = CENTER
        if T["i"] == 0 and T.get("moved", 0) < 280:
            for lab, dx, dy in (("W", 0, -1), ("S", 0, 1), ("A", -1, 0), ("D", 1, 0)):
                k = 84 + 6 * math.sin(t * 5)
                px, py = cx + dx * k, cy + dy * k
                tip = (px + dx * 22, py + dy * 22)
                base1 = (px - dy * 16, py + dx * 16)
                base2 = (px + dy * 16, py - dx * 16)
                pygame.draw.polygon(surf, (255, 220, 70), [tip, base1, base2])
                pygame.draw.polygon(surf, BLACK, [tip, base1, base2], 2)
                tx = font_med.render(lab, True, WHITE)
                surf.blit(tx, (px - dx * 26 - tx.get_width() / 2, py - dy * 26 - tx.get_height() / 2))
            return
        tg = self.tut_target()
        if tg is None:
            return
        tx, ty, label, col = tg
        sx, sy = cx + (tx - b.x), cy + (ty - b.y)
        ang = math.atan2(sy - cy, sx - cx)
        on = 40 <= sx <= WIDTH - 40 and 40 <= sy <= HEIGHT - 170
        if on:
            ax, ay = sx, sy - 52 - 6 * math.sin(t * 6)
            pygame.draw.polygon(surf, col, [(ax, ay + 18), (ax - 14, ay - 8), (ax + 14, ay - 8)])
            pygame.draw.polygon(surf, BLACK, [(ax, ay + 18), (ax - 14, ay - 8), (ax + 14, ay - 8)], 2)
            lt = font_small.render(label, True, col)
            surf.blit(lt, (ax - lt.get_width() / 2, ay - 28))
        else:
            r = 120 + 6 * math.sin(t * 6)
            px, py = cx + math.cos(ang) * r, cy + math.sin(ang) * r
            c, sn = math.cos(ang), math.sin(ang)
            pts = [(px + c * 24, py + sn * 24), (px - c * 12 - sn * 16, py - sn * 12 + c * 16), (px - c * 12 + sn * 16, py - sn * 12 - c * 16)]
            pygame.draw.polygon(surf, col, pts)
            pygame.draw.polygon(surf, BLACK, pts, 2)
            lt = font_small.render(label, True, col)
            surf.blit(lt, (px - c * 40 - lt.get_width() / 2, py - sn * 40 - lt.get_height() / 2))

    def tut_toughen(self, e):
        """Tutorial: robot biasa ikut menebal sesuai DPS pemain supaya tidak mati seketika walau skill sudah kuat."""
        d = self.avg_dps()
        e.max_hp = e.hp = int(max(e.max_hp * 1.5, min(d * 4.5, e.max_hp * 40)))

    def tut_spawn_boss(self, kind, hp, boss_kind, sub):
        b = self.badang
        self.last_old_boss = None
        e = Enemy(kind, 0.0, b.x, b.y, is_boss=True, boss_scale=0, mode_config=self.mode_config)
        e.boss_kind = boss_kind
        fight = TUT_BOSS_FIGHT.get(boss_kind, 60.0)
        by_dps = int(self.avg_dps() * BOSS_DPS_UPTIME * fight * 1.6)
        hp = int(max(hp * 3.0, min(by_dps, hp * 60)))
        e.max_hp = e.hp = hp
        e.tut_cap = hp / fight
        e.armor = e.armor_max = 0
        e.intro_t = 2.0
        e.atk_timer = 3.0
        if boss_kind == "normal":
            e.is_dasher = True
            e.dash_cd = (6.0, 8.0)
            e.ability_timer = 6.0
        self.enemies.append(e)
        self.boss_active = True
        self.boss_intro = {"text": kind["name"].upper(), "sub": sub, "t": 2.5}
        self.show_toast("%s muncul!" % kind["name"])
        sfx("intro")
        sfx("boss_spawn")

    def start_tut_event(self):
        kinds = ["ring", "wall", "bats"]
        self.formation_warn = {"kind": kinds[min(2, self.tut["ev"])], "side": random.choice(["top", "bottom", "left", "right"]),
                               "t": FORMATION_WARN + 1.0}
        self.formation_music_t = 40.0
        sfx("warn")

    def fire_tut_event(self, w):
        """Event Tutorial: BANYAK robot sekaligus (kepungan / tembok / kawanan drone)."""
        b = self.badang
        hw, hh = WIDTH / 2 + 90, HEIGHT / 2 + 90
        sd = w["side"]

        def mk(key, x, y):
            e = Enemy(ROBOTS[key], 0.0, 0, 0, spawn_at=(x, y), mode_config=self.mode_config)
            self.tut_toughen(e)
            e.from_event = True
            self.enemies.append(e)

        if w["kind"] == "ring":
            mix = ["bolt", "kilat", "pelari", "tank", "zirah", "penerjang", "granat", "kedip"]
            n = 22
            for k in range(n):
                a = k * math.tau / n
                mk(mix[k % len(mix)], b.x + math.cos(a) * 430, b.y + math.sin(a) * 340)
        elif w["kind"] == "wall":
            mix = ["tank", "perisai", "hitam", "penembak", "gerinda", "laser", "montir"]
            n = 18
            for k in range(n):
                al = (k - (n - 1) / 2.0) * 80
                if sd == "top":
                    x, y = b.x + al, b.y - hh
                elif sd == "bottom":
                    x, y = b.x + al, b.y + hh
                elif sd == "left":
                    x, y = b.x - hw, b.y + al * 0.6
                else:
                    x, y = b.x + hw, b.y + al * 0.6
                mk(mix[k % len(mix)], x, y)
        else:
            for k in range(18):
                al = random.uniform(-hw, hw)
                mk("drone", b.x + al, b.y - hh - random.uniform(0, 160))
            for k in range(5):
                mk(["penembak", "petir", "laser", "jitu", "racun"][k], b.x + random.uniform(-hw, hw), b.y - hh - 120)
        self.show_toast("Gelombang robot datang!")
        sfx("warn")

    def merchant_dialog(self, topic, then=None):
        self.start_dialog(MERCHANT_LINES[topic], "talk_merchant", then)

    def tut_give_evolution(self):
        b = self.badang
        b.weapons = [FireballWeapon(level=4), IceSpikeWeapon(level=4), OrbWeapon(level=2)]
        b.fusions = 0
        self.tut_menu("TUTORIAL: PILIH KARTU EVOLUSI", [self.evo_card(w) for w in b.weapons[:2]])

    def tut_second_evolution(self):
        b = self.badang
        if not b.weapons or not any(isinstance(w, (FireballWeapon, IceSpikeWeapon)) for w in b.weapons):
            b.weapons = [FireballWeapon(level=4), IceSpikeWeapon(level=4), OrbWeapon(level=2)]
        todo = [w for w in b.weapons if isinstance(w, (FireballWeapon, IceSpikeWeapon)) and not w.evolved]
        if todo:
            self.tut_menu("TUTORIAL: EVOLUSIKAN YANG SATUNYA", [self.evo_card(todo[0])])

    def tut_fusion_menu(self):
        b = self.badang
        while len(b.weapons) < 3:
            b.weapons.append(OrbWeapon(level=2) if not b.has_weapon(OrbWeapon) else MultiArrowWeapon(level=2))
        card = {"kind": "fusion", "name": "FUSI SIHIR", "desc": "Lebur 2 sihir jadi 1 SENJATA FUSI baru. Keduanya hilang", "apply": lambda: None}
        self.tut_menu("TUTORIAL: FUSI SIHIR", [card])

    def draw_tutorial(self, surf):
        T = self.tut
        self.draw_tut_guide(surf)
        panel, skip, leave = self.tutorial_rects()
        pygame.draw.rect(surf, (10, 8, 22), panel, border_radius=12)
        pygame.draw.rect(surf, (110, 200, 255), panel, 3, border_radius=12)
        title, text = TUT_STEPS[T["i"]]
        surf.blit(font_med.render("Step %d/%d  %s" % (T["i"] + 1, len(TUT_STEPS), title), True, GOLD_COLOR), (panel.x + 20, panel.y + 12))
        y = panel.y + 50
        for ln in wrap_text(text, font_small, panel.width - 240)[:4]:
            surf.blit(font_small.render(ln, True, WHITE), (panel.x + 20, y))
            y += 20
        if T["i"] == 16:
            lv = font_med.render("Level %d / 15" % min(15, self.badang.level), True, XP_COLOR)
            surf.blit(lv, (panel.centerx - lv.get_width() / 2 - 100, panel.y - 36))
        if self.tutorial_can_skip():
            last = T["i"] >= len(TUT_STEPS) - 1
            self.draw_button(surf, skip, "KELUAR" if last else "LEWATI", HP_GREEN, font_small)
            self.draw_button(surf, leave, "KELUAR", GRAY, font_small)

    def handle_touch_down(self, pos, finger_id, norm=None):
        st = self.state
        if st in MENU_PAGES:
            self.menu_page_click(pos, finger_id)
            return
        if self.mode == "tutorial" and st == "playing" and self.tutorial_click(pos):
            return
        if st == "menu":
            self.lobby_click(pos)
            return
        if st == "avatars":
            self.avatars_click(pos)
            return
        if st == "scores":
            if self.back_rect().collidepoint(pos):
                sfx("click")
                self.state = "menu"
            return
        if st == "paused":
            if self.pause_hit(pos, norm):
                self.toggle_pause()
            else:
                self.pause_click(pos)
            return
        if st == "playing" and self.pause_hit(pos, norm):
            self.toggle_pause()
            return
        if st == "shop":
            if self.shop_menu.handle_click(pos):
                self.shop_menu.merchant.cooldown = 4.0
                self.state = "playing"
            return
        if st == "levelup":
            if self.upgrade_menu.handle_click(pos):
                sfx("click")
                fz = getattr(self.upgrade_menu, "fused", None)
                if fz is not None:
                    self.show_toast("FUSI: %s! %s" % (fz.display_name, fz.evolved_desc))
                self.badang.refresh_evolutions()
                self.state = "playing"
            return
        if st == "confirm_new":
            self.confirm_click(pos)
            return
        if st == "dialog":
            self.advance_dialog()
            return
        if st == "light":
            return
        if st == "victory":
            if self.back_rect().collidepoint(pos):
                sfx("click")
                tut = self.mode == "tutorial"
                self.reset_to_menu()
                self.state = "title" if tut else "menu"
                if tut:
                    self.title_t = 3.0
            return
        if st == "gameover":
            self.reset_to_menu()
            return
        if st == "playing":
            self.joystick_finger_id = finger_id
            self.joystick_center = pos
            self.joystick_knob = pos
            self.move_vector = (0.0, 0.0)

    def handle_touch_motion(self, pos, finger_id):
        if self.state == "avatars" and self.av_press:
            p0, sc0, _m = self.av_press
            if abs(pos[1] - p0[1]) > 10:
                self.av_press[2] = True
            self.av_scroll = sc0 - (pos[1] - p0[1])
            return
        if self.state == "toko" and self.tk_press:
            p0, sc0, _m = self.tk_press
            if abs(pos[1] - p0[1]) > 10:
                self.tk_press[2] = True
            self.tk_scroll = sc0 - (pos[1] - p0[1])
            return
        if self.state == "almanac_detail" and self.det_press:
            self.det_scroll = max(0.0, min(self.det_max, self.det_press[1] - (pos[1] - self.det_press[0][1])))
            return
        if self.state == "almanac" and self.al_press:
            p0, sc0, _m = self.al_press
            dy = pos[1] - p0[1]
            if abs(dy) > 10:
                self.al_press[2] = True
            self.al_scroll = max(0.0, min(self.al_max_scroll(), sc0 - dy))
            return
        if self.state == "playing" and finger_id == self.joystick_finger_id:
            dx = pos[0] - self.joystick_center[0]
            dy = pos[1] - self.joystick_center[1]
            dist = math.hypot(dx, dy)
            if dist > JOY_MAX_RADIUS:
                dx, dy = dx / dist * JOY_MAX_RADIUS, dy / dist * JOY_MAX_RADIUS
            self.joystick_knob = (self.joystick_center[0] + dx, self.joystick_center[1] + dy)
            self.move_vector = (dx / JOY_MAX_RADIUS, dy / JOY_MAX_RADIUS)

    def handle_touch_up(self, finger_id):
        if self.av_press:
            p0, _sc, moved = self.av_press
            self.av_press = None
            if not moved:
                self.avatar_pick_at(p0)
            return
        if self.tk_press:
            p0, _sc, moved = self.tk_press
            self.tk_press = None
            if not moved:
                _h, items, _t = self.toko_cards()
                for i, rc in items:
                    if rc.move(0, self.TK_VIEW.y - self.tk_scroll).collidepoint(p0) and self.TK_VIEW.collidepoint(p0):
                        self.toko_sel = i
                        sfx("click")
                        break
            return
        if self.det_press:
            self.det_press = None
            return
        if self.state == "almanac" and self.al_press:
            p0, _sc, moved = self.al_press
            self.al_press = None
            if not moved:
                self.al_open_detail(p0)
            return
        if finger_id == self.joystick_finger_id:
            self.joystick_finger_id = None
            self.joystick_knob = self.joystick_center
            self.move_vector = (0.0, 0.0)



    def draw(self, surf):
        global FACE_DETAIL, HAZ_LOD
        HAZ_LOD = len(self.hazards) > 24 or PERF["lod"] >= 1
        st = self.state
        if st == "confirm_new":
            self.draw_confirm(surf)
            self.draw_badge_banner(surf)
            return
        if st in MENU_PAGES:
            self.draw_menu_page(surf)
            self.draw_badge_banner(surf)
            return
        if st == "menu":
            surf.fill(BG_COLOR)
            self.draw_lobby(surf)
            self.draw_badge_banner(surf)
            return
        if st == "avatars":
            surf.fill(BG_COLOR)
            self.draw_avatars(surf)
            self.draw_badge_banner(surf)
            return
        if st == "scores":
            surf.fill(BG_COLOR)
            self.draw_scores(surf)
            self.draw_badge_banner(surf)
            return

        if st in FREEZE_STATES:
            fb = self._freeze
            if fb is not None and self._freeze_st == st:
                if not (st == "shop" and self.shop_menu is not None and self.shop_menu.ready()):
                    surf.blit(fb, (0, 0))
            else:
                self.draw_world(surf, st)
                if fb is None:
                    self._freeze = surf.copy()
                else:
                    fb.blit(surf, (0, 0))
                self._freeze_st = st
        else:
            self._freeze_st = None
            self.draw_world(surf, st)

        if st == "dialog":
            self.draw_dialog(surf)
        elif st == "light":
            self.draw_light(surf)
        elif st == "victory":
            self.draw_victory(surf)
        elif st == "paused":
            self.draw_paused(surf)
        elif st == "levelup":
            self.upgrade_menu.draw(surf)
        elif st == "shop":
            self.shop_menu.draw(surf)
        elif st == "gameover":
            self.draw_gameover(surf)
        self.draw_badge_banner(surf)
        self.draw_toast(surf, 650 if st in FREEZE_STATES else 84)

    def draw_world(self, surf, st):
        cam_x, cam_y = self.get_camera()
        lb = self.level_boss
        p = lb.pulse if lb else 0.0
        surf.fill((BG_COLOR[0] + int(26 * p), BG_COLOR[1] + int(6 * p), BG_COLOR[2] + int(22 * p)))
        self.draw_grid(surf, cam_x, cam_y)
        if self.arena:
            self.draw_arena(surf, cam_x, cam_y)

        for z in self.poison_zones:
            z.draw(surf, cam_x, cam_y)
        for g in self.gems:
            g.draw(surf, cam_x, cam_y)
        for pk in self.pickups:
            pk.draw(surf, cam_x, cam_y)
        for m in self.merchants:
            m.draw(surf, cam_x, cam_y)
        for eff in self.effects:
            if "shock" not in eff:
                self.draw_effect(surf, cam_x, cam_y, eff)
        for s in self.strikes:
            s.draw(surf, cam_x, cam_y)
        for t in self.tornados:
            t.draw(surf, cam_x, cam_y)
        for e in self.enemies:
            e.draw(surf, cam_x, cam_y)
        for h in self.hazards:
            h.draw(surf, cam_x, cam_y)
        for pr in self.projectiles:
            pr.draw(surf, cam_x, cam_y)
        for pr in self.enemy_projectiles:
            pr.draw(surf, cam_x, cam_y)
        for bm in self.boomerangs:
            bm.draw(surf, cam_x, cam_y)
        self.badang.draw(surf, self)
        self.draw_fx_anims(surf, cam_x, cam_y)
        for eff in self.effects:
            if "shock" in eff:
                self.draw_effect(surf, cam_x, cam_y, eff)
        if self.flash_t > 0:
            lv_ = int(self.flash_t / 0.3 * 3.0 + 0.99)
            fc = self.flash_col
            surf.blit(veil_surface((fc[0], fc[1], fc[2], 45 * lv_)), (0, 0))
        if self.badang.slow_t > 0:
            pygame.draw.circle(surf, (170, 225, 255), CENTER, 36, 3)
            pygame.draw.circle(surf, WHITE, CENTER, 40, 1)

        for tx, ty, _life, tsurf in self.damage_texts:
            sx, sy = tx - cam_x, ty - cam_y
            if -60 <= sx <= WIDTH + 60 and -30 <= sy <= HEIGHT + 30:
                surf.blit(tsurf, (sx - tsurf.get_width() / 2, sy - tsurf.get_height() / 2))

        self.draw_hud(surf)
        self.draw_formation_warning(surf)
        self.draw_boss_intro(surf)
        if SETTINGS.get("joystick", 1.0) > 0:
            self.draw_joystick(surf)
        if self.mode == "tutorial" and st == "playing":
            self.draw_tutorial(surf)

    def draw_arena(self, surf, cam_x, cam_y):
        a = self.arena
        l, t = a["cx"] - a["hw"] - cam_x, a["cy"] - a["hh"] - cam_y
        w, h = 2 * a["hw"], 2 * a["hh"]
        dark = (5, 5, 10)
        if t > 0:
            pygame.draw.rect(surf, dark, (0, 0, WIDTH, t))
        if t + h < HEIGHT:
            pygame.draw.rect(surf, dark, (0, t + h, WIDTH, HEIGHT - t - h))
        if l > 0:
            pygame.draw.rect(surf, dark, (0, 0, l, HEIGHT))
        if l + w < WIDTH:
            pygame.draw.rect(surf, dark, (l + w, 0, WIDTH - l - w, HEIGHT))
        lb = self.level_boss
        col = lb.kdef["color"] if lb else WHITE
        pulse = lb.pulse if lb else 0.0
        pygame.draw.rect(surf, col, (l, t, w, h), width=4 + int(5 * pulse))
        pygame.draw.rect(surf, WHITE, (l, t, w, h), width=1)

    def draw_grid(self, surf, cam_x, cam_y):
        cell = 90
        off_x = int(cam_x) % cell
        off_y = int(cam_y) % cell
        for gx in range(-off_x, WIDTH + cell, cell):
            pygame.draw.line(surf, GRID_COLOR, (gx, 0), (gx, HEIGHT), 1)
        for gy in range(-off_y, HEIGHT + cell, cell):
            pygame.draw.line(surf, GRID_COLOR, (0, gy), (WIDTH, gy), 1)

    def draw_effect(self, surf, cam_x, cam_y, eff):
        if "fall" in eff:
            prog = 1 - eff["timer"] / eff["max_timer"]
            sx, sy = eff["x"] - cam_x, eff["y"] - cam_y
            mx, my = sx + (1 - prog) * 170, sy - (1 - prog) * 520
            pygame.draw.polygon(surf, (255, 140, 40), [(mx - 12, my - 6), (mx + 60, my - 140), (mx + 10, my + 8)])
            pygame.draw.polygon(surf, (255, 225, 120), [(mx - 6, my - 4), (mx + 32, my - 85), (mx + 5, my + 4)])
            rock = [(mx + math.cos(i * 0.785 + 0.3) * (16 if i % 2 == 0 else 12), my + math.sin(i * 0.785 + 0.3) * (16 if i % 2 == 0 else 12)) for i in range(8)]
            pygame.draw.polygon(surf, (95, 65, 50), rock)
            pygame.draw.polygon(surf, (40, 25, 20), rock, 2)
            return
        if "shock" in eff:
            prog = 1 - eff["timer"] / eff["max_timer"]
            r = int(eff["rmax"] * (1 - (1 - prog) ** 2))
            sx, sy = int(eff["x"] - cam_x), int(eff["y"] - cam_y)
            fade = 1 - prog
            col = eff["color"]
            lite = (min(255, col[0] + 60), min(255, col[1] + 60), min(255, col[2] + 60))
            for j in range(3):
                rr = r - j * 38
                if rr > 6:
                    pygame.draw.circle(surf, col if j != 1 else lite, (sx, sy), rr, max(2, int((16 - j * 4) * fade) + 2))
            if prog < 0.3:
                pygame.draw.circle(surf, WHITE, (sx, sy), max(2, int(90 * (1 - prog / 0.3))))
            if r > 60:
                for i in range(20):
                    a = i * math.tau / 20 + prog * 0.6
                    pygame.draw.line(surf, lite, (sx + math.cos(a) * (r - 8), sy + math.sin(a) * (r - 8)),
                                     (sx + math.cos(a) * (r + 26 * fade), sy + math.sin(a) * (r + 26 * fade)), 3)
            return
        if "bolt" in eff:
            x1, y1, x2, y2 = eff["bolt"]
            draw_bolt(surf, x1 - cam_x, y1 - cam_y, x2 - cam_x, y2 - cam_y, eff["color"], 5, 6, 12)
            return
        progress = 1 - eff["timer"] / eff["max_timer"]
        r = max(1, int(eff["radius"] * progress))
        sx, sy = eff["x"] - cam_x, eff["y"] - cam_y
        pygame.draw.circle(surf, eff["color"], (int(sx), int(sy)), r, width=4)

    def draw_joystick(self, surf):
        active = self.joystick_finger_id is not None
        outer_color = (210, 210, 220) if active else (80, 80, 92)
        pygame.draw.circle(surf, outer_color, (int(self.joystick_center[0]), int(self.joystick_center[1])),
                            JOY_MAX_RADIUS, width=4)
        knob_color = BADANG_COLOR if active else (70, 70, 82)
        pygame.draw.circle(surf, knob_color, (int(self.joystick_knob[0]), int(self.joystick_knob[1])), 28)

    def draw_paused(self, surf):
        overlay = veil_surface((0, 0, 0, 170))
        surf.blit(overlay, (0, 0))
        title = font_big.render("JEDA", True, WHITE)
        surf.blit(title, (WIDTH / 2 - title.get_width() / 2, HEIGHT / 2 - 80))
        r = self.pause_rects()
        self.draw_button(surf, r["resume"], "LANJUTKAN", XP_COLOR)
        self.draw_button(surf, r["menu"], "KE MENU UTAMA", GRAY)
        hint = font_small.render("P / ESC / tombol pause = lanjut", True, GRAY)
        surf.blit(hint, (WIDTH / 2 - hint.get_width() / 2, HEIGHT / 2 + 150))


    def draw_button(self, surf, rect, text, border, font=None, fill=None):
        font = font or font_med
        pygame.draw.rect(surf, fill or PANEL_COLOR, rect, border_radius=12)
        pygame.draw.rect(surf, border, rect, width=3, border_radius=12)
        t = font.render(text, True, WHITE)
        surf.blit(t, (rect.centerx - t.get_width() / 2, rect.centery - t.get_height() / 2))

    def draw_crystals(self, surf, right, y):
        txt = font_med.render(fmt_num(self.save.data["crystals"]), True, (150, 230, 255))
        x = right - txt.get_width()
        surf.blit(txt, (x, y))
        cx, cy = x - 18, y + txt.get_height() // 2
        pts = [(cx, cy - 11), (cx + 9, cy), (cx, cy + 11), (cx - 9, cy)]
        pygame.draw.polygon(surf, (120, 215, 255), pts)
        pygame.draw.polygon(surf, WHITE, pts, 2)
        lab = font_small.render("KRISTAL", True, GRAY)
        surf.blit(lab, (right - lab.get_width(), y + txt.get_height()))

    def draw_lobby(self, surf):
        title = font_big.render("WITCH SURVIVOR", True, GOLD_COLOR)
        surf.blit(title, (WIDTH / 2 - title.get_width() / 2, 22))
        self.draw_crystals(surf, WIDTH - 24, 14)
        sub = font_med.render("LOBI", True, WHITE)
        surf.blit(sub, (WIDTH / 2 - sub.get_width() / 2, 72))
        av = AVATARS[self.selected_avatar]

        panel = pygame.Rect(60, 100, 400, 390)
        pygame.draw.rect(surf, PANEL_COLOR, panel, border_radius=14)
        pygame.draw.rect(surf, GOLD_COLOR, panel, width=3, border_radius=14)
        draw_wizard_cached(surf, panel.centerx, panel.y + 190, av, scale=3.0)
        nm = font_big.render(av["name"], True, av["color"])
        surf.blit(nm, (panel.centerx - nm.get_width() / 2, panel.y + 262))
        st = font_small.render("HP %d   Kecepatan x%.2f" % (av["hp"], av["speed"]), True, GRAY)
        surf.blit(st, (panel.centerx - st.get_width() / 2, panel.y + 312))
        sk = font_small.render("Skill: " + av["skill_name"], True, GOLD_COLOR)
        surf.blit(sk, (panel.centerx - sk.get_width() / 2, panel.y + 338))
        y = panel.y + 360
        for line in wrap_text(av["skill_desc"], font_small, panel.width - 30)[:2]:
            t = font_small.render(line, True, WHITE)
            surf.blit(t, (panel.centerx - t.get_width() / 2, y))
            y += 18

        r = self.lobby_rects()
        self.draw_button(surf, r["avatar"], "PILIH AVATAR", GOLD_COLOR)
        self.draw_button(surf, r["toko"], "TOKO (AVATAR & PETI SKILL)", (255, 170, 60), font_small)
        stats = self.save.data["stats"]
        lines = ["Total main: %d" % stats["runs"], "Level tertinggi: %d" % stats["best_level"],
                 "Boss ditumbangkan: %d" % stats["bosses"]]
        for i, ln in enumerate(lines):
            t = font_small.render(ln, True, GRAY)
            surf.blit(t, (panel.x + 6, 568 + i * 22))

        board = pygame.Rect(500, 100, 740, 262)
        pygame.draw.rect(surf, PANEL_COLOR, board, border_radius=14)
        pygame.draw.rect(surf, GRAY, board, width=2, border_radius=14)
        bt = font_med.render("TOP SKOR", True, GOLD_COLOR)
        surf.blit(bt, (board.x + 20, board.y + 12))
        scores = self.save.data["top_scores"][:5]
        if not scores:
            t = font_small.render("Belum ada skor. Ayo bermain!", True, GRAY)
            surf.blit(t, (board.x + 20, board.y + 60))
        for i, s in enumerate(scores):
            row = "#%d  %s  -  %s  (LV %d, %s)" % (i + 1, fmt_num(s["score"]), s["avatar"], s["level"],
                                                  fmt_time(s["time"]))
            t = font_small.render(row, True, GOLD_COLOR if i == 0 else WHITE)
            surf.blit(t, (board.x + 20, board.y + 52 + i * 38))

        self.draw_button(surf, r["scores"], "LIHAT SEMUA SKOR", WHITE, font_small)
        self.draw_button(surf, r["back"], "KEMBALI", GRAY, font_small)

        nr, ir = r["normal"], r["inflation"]
        self.draw_button(surf, nr, "MODE NORMAL", HP_GREEN)
        self.draw_button(surf, ir, "MODE INFLASI", HP_RED)
        t = font_small.render("Musuh naik bertahap", True, GRAY)
        surf.blit(t, (nr.centerx - t.get_width() / 2, nr.bottom - 26))
        t = font_small.render("Lebih ganas, hadiah lebih besar", True, GRAY)
        surf.blit(t, (ir.centerx - t.get_width() / 2, ir.bottom - 26))
        run = self.save.data.get("run")
        if run:
            self.draw_button(surf, r["continue"],
                             "LANJUTKAN  (LV %d, %s, %s)" % (run["level"], fmt_time(run["time"]),
                                                             "Inflasi" if run["mode"] == "inflation" else "Normal"),
                             GOLD_COLOR)
        if self.menu_msg_t > 0:
            mt = font_med.render(self.menu_msg, True, XP_COLOR)
            surf.blit(mt, (24, 22))
        hint = font_small.render("PC: panah kiri/kanan ganti avatar, 1 Normal, 2 Inflasi, C lanjut, V avatar (toko), T skor",
                                 True, GRAY)
        surf.blit(hint, (WIDTH / 2 - hint.get_width() / 2, 668))

    _lock_surf = None


    def draw_avatars(self, surf):
        title = font_big.render("PILIH AVATAR", True, GOLD_COLOR)
        surf.blit(title, (WIDTH / 2 - title.get_width() / 2, 12))
        self.draw_crystals(surf, WIDTH - 24, 12)
        if self.menu_msg_t > 0:
            mt = font_med.render(self.menu_msg, True, XP_COLOR)
            surf.blit(mt, (24, 20))
        heads, items, total = self.avatar_cards()
        view = self.AV_VIEW
        self.av_scroll = self.clamp_scroll(self.av_scroll, total, view.h)
        off = view.y - self.av_scroll
        old = surf.get_clip()
        surf.set_clip(view)
        for nm_, col_, hy in heads:
            ty = hy + off
            if -30 < ty < HEIGHT:
                pygame.draw.line(surf, col_, (60, ty + 14), (WIDTH - 60, ty + 14), 1)
                lab = font_med.render(nm_, True, col_)
                pygame.draw.rect(surf, BG_COLOR, (WIDTH / 2 - lab.get_width() / 2 - 14, ty, lab.get_width() + 28, 30))
                surf.blit(lab, (WIDTH / 2 - lab.get_width() / 2, ty))
        for idx, r0 in items:
            r = r0.move(0, off)
            if r.bottom < view.y or r.y > view.bottom:
                continue
            av = AVATARS[idx]
            selected = idx == self.selected_avatar
            pygame.draw.rect(surf, PANEL_COLOR, r, border_radius=12)
            pygame.draw.rect(surf, GOLD_COLOR if selected else GRAY, r, width=4 if selected else 2, border_radius=12)
            cx = int(r.x + r.width / 2)
            draw_wizard_cached(surf, cx, int(r.y + 82), av, scale=1.25)
            name = font_med.render(self.fit_text(font_med, av["name"], r.width - 8), True, av["color"])
            surf.blit(name, (cx - name.get_width() / 2, r.y + 124))
            stt = font_small.render("HP %d  Kec. x%.2f" % (av["hp"], av["speed"]), True, GRAY)
            surf.blit(stt, (cx - stt.get_width() / 2, r.y + 150))
            y = r.y + 172
            for line in wrap_text(av["role"], font_small, r.width - 16)[:2]:
                t = font_small.render(line, True, WHITE)
                surf.blit(t, (cx - t.get_width() / 2, y))
                y += 17
            sk = font_small.render(self.fit_text(font_small, av["skill_name"], r.width - 8), True, GOLD_COLOR)
            surf.blit(sk, (cx - sk.get_width() / 2, r.y + 210))
            y = r.y + 229
            for line in wrap_text(av["skill_desc"], font_small, r.width - 16)[:2]:
                t = font_small.render(line, True, GRAY)
                surf.blit(t, (cx - t.get_width() / 2, y))
                y += 17
        surf.set_clip(old)
        if total > view.h:
            frac = view.h / float(total)
            bar_h = max(30, int(view.h * frac))
            by = view.y + int((view.h - bar_h) * (self.av_scroll / float(total - view.h)))
            pygame.draw.rect(surf, (90, 90, 120), (WIDTH - 10, by, 5, bar_h), border_radius=3)
        if len(self.owned_list()) < len(AVATARS):
            hint = font_small.render("Avatar lain dibeli di TOKO dengan Kristal.", True, GRAY)
            surf.blit(hint, (WIDTH / 2 - hint.get_width() / 2, 608))
        self.draw_button(surf, self.buy_rect(), "TOKO (BELI AVATAR)", (255, 170, 60))
        self.draw_button(surf, self.back_rect2(), "PILIH & KEMBALI", GOLD_COLOR)
    def draw_scores(self, surf):
        title = font_big.render("TOP SKOR", True, GOLD_COLOR)
        surf.blit(title, (WIDTH / 2 - title.get_width() / 2, 20))
        head = font_small.render("Skor = musuh x10 + level x150 + waktu x2 + boss level x2000 + bos lama x300",
                                 True, GRAY)
        surf.blit(head, (WIDTH / 2 - head.get_width() / 2, 78))
        scores = self.save.data["top_scores"]
        if not scores:
            t = font_med.render("Belum ada skor.", True, GRAY)
            surf.blit(t, (WIDTH / 2 - t.get_width() / 2, 300))
        for i, s in enumerate(scores):
            y = 110 + i * 46
            row = pygame.Rect(180, y, 940, 40)
            pygame.draw.rect(surf, PANEL_COLOR, row, border_radius=8)
            col = GOLD_COLOR if i == 0 else WHITE
            surf.blit(font_med.render("#%d" % (i + 1), True, col), (row.x + 14, row.y + 8))
            surf.blit(font_med.render(fmt_num(s["score"]), True, col), (row.x + 80, row.y + 8))
            info = "%s | %s | LV %d | %s | %d musuh | %d boss" % (
                s["avatar"], "Inflasi" if s["mode"] == "inflation" else "Normal", s["level"],
                fmt_time(s["time"]), s["kills"], s.get("bosses", 0))
            surf.blit(font_small.render(info, True, GRAY), (row.x + 280, row.y + 12))
        self.draw_button(surf, self.back_rect(), "KEMBALI", GOLD_COLOR)

    def draw_minimap(self, surf):
        """Minimap lengkap: pemain, semua musuh, elite, boss (ditempel ke tepi bila jauh), rune, peti, orb HP/XP, pedagang, arena + legenda."""
        mx, my, mw, mh = WIDTH - 156, 100, 140, 140
        rect = pygame.Rect(mx, my, mw, mh)
        pygame.draw.rect(surf, (12, 14, 24), rect)
        b = self.badang
        sc = mw / 1700.0
        cx, cy = mx + mw / 2, my + mh / 2
        surf.set_clip(rect)
        pygame.draw.circle(surf, (24, 28, 44), (int(cx), int(cy)), int(mw / 2 - 2), 1)
        if self.arena:
            a = self.arena
            ar = pygame.Rect(cx + (a["cx"] - a["hw"] - b.x) * sc, cy + (a["cy"] - a["hh"] - b.y) * sc,
                             2 * a["hw"] * sc, 2 * a["hh"] * sc)
            pygame.draw.rect(surf, (255, 90, 160), ar, 1)

        def edge(x, y, pad=5):
            return (max(mx + pad, min(mx + mw - pad, cx + (x - b.x) * sc)),
                    max(my + pad, min(my + mh - pad, cy + (y - b.y) * sc)))

        lod = PERF["lod"]
        if lod == 0:
            for g in self.gems[::2]:
                surf.fill(XP_COLOR, (int(cx + (g.x - b.x) * sc), int(cy + (g.y - b.y) * sc), 1, 1))
        for pk in self.pickups:
            col = PICKUP_COLORS.get(pk.kind, WHITE)
            if pk.kind == "hporb":
                if lod == 0:
                    surf.fill(col, (int(cx + (pk.x - b.x) * sc) - 1, int(cy + (pk.y - b.y) * sc) - 1, 3, 3))
                continue
            px, py = edge(pk.x, pk.y)
            if pk.kind == "chest":
                pygame.draw.rect(surf, col, (int(px) - 2, int(py) - 2, 5, 5))
            else:
                pygame.draw.polygon(surf, col, [(int(px), int(py) - 4), (int(px) + 4, int(py)), (int(px), int(py) + 4), (int(px) - 4, int(py))])
                pygame.draw.polygon(surf, WHITE, [(int(px), int(py) - 4), (int(px) + 4, int(py)), (int(px), int(py) + 4), (int(px) - 4, int(py))], 1)
        for i, e in enumerate(self.enemies):
            if e.dead:
                continue
            if e.is_boss:
                ex, ey = edge(e.x, e.y, 6)
                pygame.draw.circle(surf, (255, 60, 60), (int(ex), int(ey)), 6)
                pygame.draw.circle(surf, WHITE, (int(ex), int(ey)), 6, 1)
                continue
            ex, ey = cx + (e.x - b.x) * sc, cy + (e.y - b.y) * sc
            if e.elite:
                pygame.draw.circle(surf, GOLD_COLOR, (int(ex), int(ey)), 3)
            else:
                surf.fill((255, 95, 95), (int(ex) - 1, int(ey) - 1, 3, 3))
        for m in self.merchants:
            if not m.present:
                continue
            mmx, mmy = edge(m.x, m.y, 4)
            pygame.draw.rect(surf, (120, 255, 150), (int(mmx) - 3, int(mmy) - 3, 7, 7))
        pygame.draw.circle(surf, (120, 220, 255), (int(cx), int(cy)), 4)
        pygame.draw.circle(surf, WHITE, (int(cx), int(cy)), 4, 1)
        surf.set_clip(None)
        pygame.draw.rect(surf, GOLD_COLOR, rect, 2)
        # legenda
        items = (("Kamu", (120, 220, 255)), ("Musuh", (255, 95, 95)), ("Elite", GOLD_COLOR), ("Boss", (255, 60, 60)),
                 ("Rune", MAGNET_COLOR), ("Peti", CHEST_COLOR), ("Orb HP", HEAL_COLOR), ("Pedagang", (120, 255, 150)))
        ly = my + mh + 4
        for k, (lab, col) in enumerate(items):
            lx = mx + (k % 2) * 72
            yy = ly + (k // 2) * 14
            if lab == "Rune":
                pygame.draw.polygon(surf, col, [(lx + 5, yy + 2), (lx + 9, yy + 6), (lx + 5, yy + 10), (lx + 1, yy + 6)])
            elif lab == "Peti":
                pygame.draw.rect(surf, col, (lx + 2, yy + 3, 6, 6))
            else:
                pygame.draw.circle(surf, col, (lx + 5, yy + 6), 4)
            surf.blit(font_tiny.render(lab, True, (200, 200, 215)), (lx + 13, yy))

    def draw_merchant_arrows(self, surf):
        b = self.badang
        for m in self.merchants:
            if not m.present:
                continue
            dx, dy = m.x - b.x, m.y - b.y
            if abs(dx) < WIDTH / 2 - 30 and abs(dy) < HEIGHT / 2 - 30:
                continue
            ang = math.atan2(dy, dx)
            px = max(40, min(WIDTH - 40, WIDTH / 2 + dx * 0.9))
            py = max(70, min(HEIGHT - 40, HEIGHT / 2 + dy * 0.9))
            pts = [(px + math.cos(ang) * 18, py + math.sin(ang) * 18),
                   (px + math.cos(ang + 2.5) * 14, py + math.sin(ang + 2.5) * 14),
                   (px + math.cos(ang - 2.5) * 14, py + math.sin(ang - 2.5) * 14)]
            pygame.draw.polygon(surf, GOLD_COLOR, pts)
            t = font_small.render("$", True, GOLD_COLOR)
            surf.blit(t, (px - t.get_width() / 2, py - 30))

    def draw_hud(self, surf):
        b = self.badang
        bar_y, bar_h = 4, 22
        xp_ratio = b.xp / b.xp_needed
        pygame.draw.rect(surf, (15, 15, 22), (0, bar_y, WIDTH, bar_h))
        pygame.draw.rect(surf, XP_COLOR, (0, bar_y, WIDTH * xp_ratio, bar_h))
        pygame.draw.rect(surf, GOLD_COLOR, (0, bar_y + bar_h, WIDTH, 3))

        lvl_text = font_med.render(f"LEVEL {b.level}", True, WHITE)
        pill_w = lvl_text.get_width() + 20
        pill = pygame.Rect(WIDTH / 2 - pill_w / 2, bar_y - 3, pill_w, bar_h + 6)
        pygame.draw.rect(surf, (10, 10, 16), pill, border_radius=10)
        pygame.draw.rect(surf, GOLD_COLOR, pill, width=2, border_radius=10)
        surf.blit(lvl_text, (pill.x + 10, pill.y + (pill.height - lvl_text.get_height()) / 2))

        pygame.draw.rect(surf, (50, 20, 20), (16, 34, 240, 20), border_radius=4)
        ratio = max(b.hp / b.max_hp, 0)
        pygame.draw.rect(surf, HP_RED, (16, 34, 240 * ratio, 20), border_radius=4)
        hp_text = font_small.render(f"HP {max(int(b.hp), 0)}/{b.max_hp}", True, WHITE)
        surf.blit(hp_text, (22, 36))

        mode_label = "Inflasi" if self.mode == "inflation" else "Normal"
        info = f"{b.avatar['name']}  |  Gold: {self.gold}  |  {mode_label}"
        if self.revives:
            info += "  |  Nyawa+%d" % self.revives
        surf.blit(font_small.render(info, True, GOLD_COLOR), (16, 58))

        y = 82
        for w in b.weapons:
            wtext = font_small.render(w.hud_label, True, w.hud_color or (GOLD_COLOR if w.evolved else WHITE))
            box = pygame.Rect(16, y, wtext.get_width() + 40, 24)
            pygame.draw.rect(surf, PANEL_COLOR, box, border_radius=5)
            ibox = pygame.Rect(box.x + 2, box.y + 2, 20, 20)
            old_clip = surf.get_clip()
            surf.set_clip(ibox)
            draw_skill_icon_ent(surf, weapon_icon_ent(w), ibox.centerx, ibox.centery, 0.34)
            surf.set_clip(old_clip)
            surf.blit(wtext, (box.x + 28, box.y + 4))
            y += 27
        st_ = font_tiny.render("Slot %d/%d   Fusi %d/%d" % (len(b.weapons), RUN_RULES["slots"], b.fusions, MAX_FUSIONS), True, GRAY)
        surf.blit(st_, (18, y))
        y += 17
        sp = b.special
        sp_label = f"{sp.name}: Siap" if sp.ready else f"{sp.name}: {sp.timer:0.1f}s"
        sp_text = font_small.render(sp_label, True, STRAIGHT_PUNCH_COLOR)
        box2 = pygame.Rect(16, y, sp_text.get_width() + 16, 20)
        pygame.draw.rect(surf, PANEL_COLOR, box2, border_radius=5)
        surf.blit(sp_text, (box2.x + 8, box2.y + 2))

        cy_ = box2.bottom + 6
        bonus = max((w.combo_bonus for w in b.weapons), default=1.0)
        if bonus > 1.0:
            surf.blit(font_small.render(f"Bonus Evolusi/Combo maks x{bonus:.2f}", True, GOLD_COLOR), (16, cy_))
            cy_ += 20
        for key in sorted(ACTIVE_COMBOS):
            surf.blit(font_small.render(f"COMBO: {COMBO_TITLES[key]}", True, COMBO_COLOR), (16, cy_))
            cy_ += 20

        right_x = WIDTH - 170
        t = int(self.time_survived)
        timer_text = font_med.render(f"{t // 60:02d}:{t % 60:02d}", True, WHITE)
        surf.blit(timer_text, (right_x - timer_text.get_width(), 40))
        left_t = max(0, int(JSAB_MAX_INTERVAL - (self.time_survived - self.last_jsab_time)))
        lines = [f"Skor: {fmt_num(self.compute_score())}",
                 f"Musuh: {self.kills}  |  Bos: {self.boss_kill_count}",
                 f"{LEVEL_BOSS_NAME}: LV {self.next_boss_level} / maks {left_t // 60}:{left_t % 60:02d}   Pedagang: LV {self.next_merchant_level}"]
        if self.pulse_relief and self.level_boss is None:
            lines.append("Jeda spawn...")
        if self.mode == "inflation" and self.elem_phase:
            lines.append("Fase: %s" % EL_NAME[self.elem_phase])
        for i, ln in enumerate(lines):
            tt = font_small.render(ln, True, GRAY)
            surf.blit(tt, (right_x - tt.get_width(), 70 + i * 20))

        boss = next((e for e in self.enemies if e.is_boss), None)
        if boss:
            bar_w = 420
            bxp, by = WIDTH / 2 - bar_w / 2, 54
            name = font_small.render(boss.kind["name"], True, WHITE)
            surf.blit(name, (WIDTH / 2 - name.get_width() / 2, by - 20))
            pygame.draw.rect(surf, (40, 10, 15), (bxp, by, bar_w, 16), border_radius=4)
            ratio = max(boss.hp / boss.max_hp, 0)
            if boss.boss_kind == "jsab":
                bar_color = boss.kdef["color"]
            elif boss.boss_kind == "healer":
                bar_color = HEALER_BAR_COLOR
            elif boss.boss_kind == "necro":
                bar_color = (150, 70, 220)
            elif boss.boss_kind == "brute":
                bar_color = (200, 120, 60)
            elif boss.boss_kind in ("fire",):
                bar_color = (90, 170, 255) if boss.form == "blue" else (255, 140, 40)
            elif boss.boss_kind in ("guardian", "minigun", "exec", "skel", "final"):
                bar_color = {"guardian": (150, 160, 190), "minigun": (110, 150, 90), "exec": (170, 170, 190),
                             "skel": (230, 230, 210), "final": (255, 70, 110)}[boss.boss_kind]
            else:
                bar_color = BOSS_BAR_COLOR
            pygame.draw.rect(surf, bar_color, (bxp, by, bar_w * ratio, 16), border_radius=4)
            if boss.armor_max > 0 and boss.boss_kind != "jsab":
                pygame.draw.rect(surf, (35, 35, 45), (bxp, by + 18, bar_w, 6))
                pygame.draw.rect(surf, ARMOR_GRAY, (bxp, by + 18, bar_w * max(0.0, boss.armor / boss.armor_max), 6))
            if boss.boss_kind == "final":
                nums = font_small.render("%s / 75.000.000" % fmt_num(int(boss.hp)).replace(",", "."), True, WHITE)
                surf.blit(nums, (WIDTH / 2 - nums.get_width() / 2, by + 19))
            if boss.boss_kind == "jsab":
                ttl = font_tiny.render(boss.kdef.get("title", ""), True, boss.kdef["color"])
                surf.blit(ttl, (bxp + bar_w - ttl.get_width() - 4, by + 18))
                for mk in (0.33, 0.66):
                    pygame.draw.line(surf, WHITE, (bxp + bar_w * mk, by), (bxp + bar_w * mk, by + 16), 2)

        if SETTINGS["minimap"] > 0:
            self.draw_minimap(surf)
        self.draw_merchant_arrows(surf)

        pc = self.pause_button_center()
        if self.state == "paused":
            pause_rect = pygame.Rect(pc[0] - 28, pc[1] - 28, 56, 56)
            pygame.draw.rect(surf, (30, 70, 40), pause_rect, border_radius=10)
            pygame.draw.rect(surf, HP_GREEN, pause_rect, width=3, border_radius=10)
            pygame.draw.polygon(surf, WHITE, [(pc[0] - 8, pc[1] - 14), (pc[0] - 8, pc[1] + 14), (pc[0] + 14, pc[1])])
        else:
            pause_rect = pygame.Rect(pc[0] - 28, pc[1] - 28, 56, 56)
            pygame.draw.rect(surf, PANEL_COLOR, pause_rect, border_radius=10)
            pygame.draw.rect(surf, WHITE, pause_rect, width=3, border_radius=10)
            bw, bh = 8, 26
            pygame.draw.rect(surf, WHITE, (pc[0] - 13, pc[1] - bh / 2, bw, bh))
            pygame.draw.rect(surf, WHITE, (pc[0] + 5, pc[1] - bh / 2, bw, bh))

    def draw_toast(self, surf, y=84):
        if self.toast_timer > 0 and self.toast_text:
            toast = font_med.render(self.toast_text, True, WHITE)
            box_w, box_h = toast.get_width() + 24, toast.get_height() + 14
            box_rect = pygame.Rect(WIDTH / 2 - box_w / 2, y, box_w, box_h)
            pygame.draw.rect(surf, PANEL_COLOR, box_rect, border_radius=8)
            surf.blit(toast, (box_rect.x + 12, box_rect.y + 7))

    def draw_victory(self, surf):
        t = pygame.time.get_ticks() / 1000.0
        surf.fill((250, 246, 225))
        for i in range(14):
            a = i * math.tau / 14 + t * 0.25
            pygame.draw.polygon(surf, (255, 238, 165), [(WIDTH / 2, 230), (WIDTH / 2 + math.cos(a) * 1600, 230 + math.sin(a) * 1600),
                                                        (WIDTH / 2 + math.cos(a + 0.11) * 1600, 230 + math.sin(a + 0.11) * 1600)])
        surf.blit(end_vignette((60, 165, 90), 130), (0, 0))
        draw_end_frame(surf, (46, 165, 88), (150, 240, 160), (14, 72, 40), t)
        panel = pygame.Rect(WIDTH // 2 - 340, 56, 680, 566)
        draw_end_panel(surf, panel, (255, 251, 236), (46, 165, 88), (230, 190, 80))
        draw_laurel_medal(surf, WIDTH // 2, 134, t)
        tut = self.mode == "tutorial"
        if tut:
            end_shadow_text(surf, font_big, "TUTORIAL SELESAI!", (30, 130, 60), WIDTH // 2, 214, (255, 230, 150), 2)
        else:
            end_shadow_text(surf, font_huge, "VICTORY!", (30, 130, 60), WIDTH // 2, 186, (255, 230, 150), 3)
        tt = int(self.time_survived)
        if tut:
            rows = ["Boss robot buatan pedagang berhasil dikalahkan!", f"Waktu latihan: {tt // 60:02d}:{tt % 60:02d}",
                    "Kamu sudah menguasai gerak, skill, evolusi, kombo, fusi, pedagang, event, dan boss."]
        else:
            rows = [f"Raja Inflasi telah tumbang di LV {self.badang.level}", f"Waktu: {tt // 60:02d}:{tt % 60:02d}   Musuh dikalahkan: {self.kills}",
                    f"Skor: {fmt_num(self.last_score)}"]
        for i, r_ in enumerate(rows):
            for j, ln in enumerate(wrap_text(r_, font_med, panel.width - 70)[:2]):
                line = font_med.render(ln, True, (60, 40, 20))
                surf.blit(line, (WIDTH / 2 - line.get_width() / 2, 304 + i * 36 + j * 26))
        box = pygame.Rect(WIDTH // 2 - 270, 432, 540, 126)
        pygame.draw.rect(surf, (28, 54, 40), box, border_radius=16)
        pygame.draw.rect(surf, GOLD_COLOR, box, 4, border_radius=16)
        pygame.draw.rect(surf, (90, 200, 120), box.inflate(-16, -16), 1, border_radius=12)
        hd = font_med.render("HADIAH TUTORIAL" if tut else "HADIAH VICTORY", True, GOLD_COLOR)
        surf.blit(hd, (box.centerx - hd.get_width() / 2, box.y + 14))
        ry = box.y + 78
        if tut:
            draw_medal_icon(surf, box.x + 150, ry - 4, 1.2)
            rw = font_med.render("Lencana: Murid Teladan", True, (150, 230, 255))
            surf.blit(rw, (box.x + 184, ry - 12))
        else:
            draw_crystal_icon(surf, box.x + 70, ry, 1.3)
            rw = font_med.render(f"x{fmt_num(self.last_crystals)}", True, (150, 230, 255))
            surf.blit(rw, (box.x + 96, ry - 12))
            draw_medal_icon(surf, box.x + 290, ry - 4, 1.2)
            rl = font_med.render("Lencana Raja Inflasi", True, (255, 225, 140))
            surf.blit(rl, (box.x + 322, ry - 12))
        self.draw_button(surf, self.back_rect(), "KEMBALI", (46, 165, 88))

    def draw_gameover(self, surf):
        t = pygame.time.get_ticks() / 1000.0
        surf.blit(veil_surface((22, 0, 6, 208)), (0, 0))
        surf.blit(end_vignette((175, 20, 32), 200), (0, 0))
        draw_end_frame(surf, (190, 35, 48), (255, 115, 105), (78, 8, 18), t)
        panel = pygame.Rect(WIDTH // 2 - 310, 58, 620, 584)
        draw_end_panel(surf, panel, (28, 12, 22), (190, 35, 48), (255, 120, 110))
        draw_fallen_hat(surf, WIDTH // 2, 124)
        end_shadow_text(surf, font_big, "PENYIHIR GUGUR", (255, 95, 95), WIDTH // 2, 176)
        pygame.draw.line(surf, (110, 40, 55), (panel.x + 50, 236), (panel.right - 50, 236), 2)
        tm = int(self.time_survived)
        stats = [
            ("Mode", 'Inflasi' if self.mode == 'inflation' else 'Normal'),
            ("Waktu bertahan", f"{tm // 60:02d}:{tm % 60:02d}"),
            ("Musuh dikalahkan", str(self.kills)),
            ("Gold terkumpul", str(self.gold)),
            ("Level dicapai", str(self.badang.level)),
            ("Boss level ditumbangkan", str(self.jsab_kills)),
            ("Kristal didapat", f"x{self.last_crystals}  (total {self.save.data['crystals']})"),
        ]
        for i, (lab, val) in enumerate(stats):
            y = 248 + i * 32
            a = font_med.render(lab, True, (200, 170, 180))
            b = font_med.render(val, True, WHITE)
            surf.blit(a, (panel.x + 56, y))
            surf.blit(b, (panel.right - 56 - b.get_width(), y))
            if lab == "Kristal didapat":
                draw_crystal_icon(surf, panel.right - 56 - b.get_width() - 20, y + 13, 0.9)
            pygame.draw.line(surf, (60, 28, 42), (panel.x + 50, y + 28), (panel.right - 50, y + 28), 1)
        pygame.draw.line(surf, (110, 40, 55), (panel.x + 50, 482), (panel.right - 50, 482), 2)
        end_shadow_text(surf, font_big, "SKOR: " + fmt_num(self.last_score), GOLD_COLOR, WIDTH // 2, 492)
        if self.new_rank:
            msg = "PERINGKAT #%d DI TOP SKOR!" % self.new_rank
            col = GOLD_COLOR if self.new_rank == 1 else XP_COLOR
        else:
            msg = "Skor tertinggi: " + fmt_num(self.save.best_score)
            col = (190, 175, 180)
        rk = font_med.render(msg, True, col)
        surf.blit(rk, (WIDTH / 2 - rk.get_width() / 2, 552))
        if int(t * 1.6) % 2 == 0:
            retry = font_med.render("Sentuh layar untuk kembali ke lobi", True, (255, 170, 160))
            surf.blit(retry, (WIDTH / 2 - retry.get_width() / 2, 596))


def draw_crystal_icon(surf, gx, gy, sc=1.0):
    h, w = int(14 * sc), int(11 * sc)
    pts = [(gx, gy - h), (gx + w, gy), (gx, gy + h), (gx - w, gy)]
    pygame.draw.polygon(surf, (120, 215, 255), pts)
    pygame.draw.polygon(surf, WHITE, pts, 2)
    pygame.draw.line(surf, WHITE, (gx - w, gy), (gx + w, gy), 1)


def draw_medal_icon(surf, gx, gy, sc=1.0):
    r = int(14 * sc)
    pygame.draw.polygon(surf, (200, 60, 60), [(gx - r // 2, gy + r // 2), (gx - r, gy + r * 2), (gx - r // 4, gy + int(r * 1.5)), (gx + r // 8, gy + r * 2), (gx + r // 2, gy + r // 2)])
    pygame.draw.circle(surf, GOLD_COLOR, (gx, gy), r)
    pygame.draw.circle(surf, (255, 245, 170), (gx, gy), r, 2)
    _icon_star(surf, gx, gy, int(r * 0.7), int(r * 0.3), (255, 255, 255))


def title_prewarm_iter():
    """Siapkan SEMUA yang berat untuk animasi intro judul SEBELUM judul tampil (di layar loading): huruf besar 6 warna + bayangan,
    subjudul 9 warna, latar, label tombol, sprite parade avatar. Dulu semua itu dibuat sambil animasi berjalan = patah-patah."""
    word = "WITCH SURVIVOR"
    chars = sorted(set(word) - {" "})
    total = 2 + len(AVATARS) + len(chars) + 9 + 2
    n = 0
    yield 0.0
    Game.menu_bg_surface()
    n += 1
    yield n / total
    for av in AVATARS:
        _wiz_entry(av, 0.95)
        n += 1
        yield n / total
    for ch in chars:
        font_huge.render(ch, True, (120, 60, 10))
        for lv in range(6):
            pulse = lv / 5.0
            font_huge.render(ch, True, (255, int(200 + 55 * pulse), int(60 + 150 * pulse)))
        n += 1
        yield n / total
    for j in range(9):
        k = j / 8.0
        font_med.render("Penyihir Pemburu Monster", True, (int(10 + 160 * k), int(8 + 150 * k), int(24 + 190 * k)))
        n += 1
        yield n / total
    for lab in ("BERMAIN", "PENGATURAN", "TUTORIAL", "KEMBALI"):
        font_med.render(lab, True, WHITE)
    font_small.render(GAME_VERSION, True, GRAY)
    n += 2
    yield 1.0


def main():
    loading_frame(0.0)
    init_audio(lambda f: loading_frame(f * 0.88))
    gen = title_prewarm_iter()
    last = time.time()
    while True:
        try:
            p_ = next(gen)
        except StopIteration:
            break
        if time.time() - last > 0.02:
            loading_frame(0.88 + 0.12 * p_)
            last = time.time()
    loading_frame(1.0)
    game = Game()
    running = True
    slow_n = 0

    while running:
        dt = min(clock.tick(int(SETTINGS.get("fps", FPS))) / 1000.0, 0.05)
        frame_t0 = time.perf_counter()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION) and getattr(event, "touch", False):
                continue
            elif event.type == getattr(pygame, "MOUSEWHEEL", -1):
                game.wheel(event.y)
            elif event.type == pygame.MOUSEBUTTONDOWN and getattr(event, "button", 1) in (4, 5):
                continue
            elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.FINGERDOWN):
                pos = event.pos if event.type == pygame.MOUSEBUTTONDOWN else \
                    (event.x * WIDTH, event.y * HEIGHT)
                if event.type == pygame.FINGERDOWN:
                    norm = (event.x, event.y)
                else:
                    try:
                        if SCALED_OK:
                            norm = (event.pos[0] / float(WIDTH), event.pos[1] / float(HEIGHT))
                        else:
                            ww, wh = pygame.display.get_window_size()
                            norm = (event.pos[0] / float(ww), event.pos[1] / float(wh))
                    except Exception:
                        norm = None
                game.handle_touch_down(pos, event_finger_id(event), norm)

            elif event.type in (pygame.MOUSEBUTTONUP, pygame.FINGERUP):
                game.handle_touch_up(event_finger_id(event))

            elif event.type in (pygame.MOUSEMOTION, pygame.FINGERMOTION):
                pos = event.pos if event.type == pygame.MOUSEMOTION else \
                    (event.x * WIDTH, event.y * HEIGHT)
                game.handle_touch_motion(pos, event_finger_id(event))

            elif event.type in tuple(getattr(pygame, n_) for n_ in ("WINDOWFOCUSLOST", "APP_WILLENTERBACKGROUND", "APP_DIDENTERBACKGROUND")
                                     if hasattr(pygame, n_)):
                game.auto_pause()
            elif event.type == pygame.KEYDOWN:
                if event.key in (getattr(pygame, "K_AC_BACK", -1),) and game.state in ("playing", "paused"):
                    game.toggle_pause()
                elif event.key == pygame.K_F11:
                    try:
                        pygame.display.toggle_fullscreen()
                    except Exception:
                        pass
                elif event.key == pygame.K_ESCAPE:
                    if game.state == "avatars":
                        game.leave_avatars()
                    elif game.state in ("playing", "paused"):
                        game.toggle_pause()
                    else:
                        game.go_back()
                elif game.state == "menu":
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        game.cycle_owned(-1)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        game.cycle_owned(1)
                    elif event.key in (pygame.K_1, pygame.K_n):
                        game.start_run("normal")
                    elif event.key in (pygame.K_2, pygame.K_i):
                        game.start_run("inflation")
                    elif event.key == pygame.K_c:
                        game.continue_run()
                    elif event.key == pygame.K_v:
                        game.state = "avatars"
                    elif event.key == pygame.K_t:
                        game.state = "scores"
                elif game.state == "avatars":
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        game.cycle_owned(-1)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        game.cycle_owned(1)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        game.avatar_confirm()
                elif event.key == pygame.K_p and game.state in ("playing", "paused"):
                    game.toggle_pause()

        keys = pygame.key.get_pressed()
        if game.state == "playing":
            kb_dx = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
            kb_dy = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])
            if kb_dx or kb_dy:
                game.move_vector = (kb_dx, kb_dy)
            elif game.joystick_finger_id is None:
                game.move_vector = (0.0, 0.0)

        game.update(dt)
        game.draw(screen)
        pygame.display.flip()
        used = time.perf_counter() - frame_t0
        perf_note(used)
        left = 1.0 / max(20.0, float(SETTINGS.get("fps", FPS))) - used
        if left > 0.004:
            bg_tick(min(0.010, left - 0.0025))
        else:
            slow_n += 1
            if slow_n % 6 == 0:
                bg_tick(0.0012)

    game.on_quit()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()

import pygame
import sys
import random
import math

# ═══════════════════════════════════════════════════════
#   1. CONSTANTS & CONFIGURATION
# ═══════════════════════════════════════════════════════
SCREEN_WIDTH  = 400
SCREEN_HEIGHT = 600
FPS           = 60

GRAVITY        = 0.45
JUMP_STRENGTH  = -9.0
PIPE_SPEED     = 3
PIPE_GAP       = 155
PIPE_INTERVAL  = 1700

ENEMY_SPEED           = 4
ENEMY_SCORE_THRESHOLD = 50

GROUND_HEIGHT = 80
PIPE_WIDTH    = 62

# Palette
SKY_TOP      = (100, 185, 220)
SKY_BOT      = (160, 220, 255)
WHITE        = (255, 255, 255)
BLACK        = (0,   0,   0)
PIPE_GREEN   = ( 82, 188,  74)
PIPE_DARK    = ( 55, 140,  45)
PIPE_BORDER  = ( 35,  95,  25)
PIPE_SHINE   = (130, 220, 110)
GROUND_GRN   = (111, 198,  57)
GROUND_BRN   = (159, 127,  83)
SCORE_GOLD   = (255, 210,   0)
SHADOW_COL   = ( 50,  30,   0)
PANEL_BORDER = (255, 200,   0)

# Slider colours
SL_TRACK     = ( 60,  60,  90)
SL_FILL_BRT  = (255, 230, 100)
SL_FILL_VOL  = ( 80, 200, 255)
SL_KNOB      = (255, 255, 255)
SL_KNOB_SHD  = (120, 120, 160)

# States
STATE_MENU     = "menu"
STATE_PLAYING  = "playing"
STATE_GAMEOVER = "gameover"
STATE_SETTINGS = "settings"


# ═══════════════════════════════════════════════════════
#   2. ASSET MANAGER
# ═══════════════════════════════════════════════════════
class AssetManager:
    def __init__(self):
        self.bird_frames  = [self._make_bird(s) for s in ("mid", "up", "down")]
        self.enemy_frames = [self._make_enemy(s) for s in ("mid", "up", "down")]
        self.bg_surf      = self._make_background()
        self.ground_surf  = self._make_ground()
        self._volume      = 0.8
        self._init_sounds()

    def _init_sounds(self):
        self.snd_jump  = None
        self.snd_score = None
        self.snd_die   = None
        self.snd_click = None
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=256)
            self.snd_jump  = self._beep(880,  0.08, 0.28)
            self.snd_score = self._beep(1320, 0.12, 0.30)
            self.snd_die   = self._beep(220,  0.30, 0.50)
            self.snd_click = self._beep(660,  0.06, 0.18)
        except Exception:
            pass

    def _beep(self, freq, duration, vol):
        try:
            import numpy as np
            sr   = 22050
            t    = np.linspace(0, duration, int(sr * duration), False)
            env  = np.exp(-t * 6)
            wave = (np.sin(2 * np.pi * freq * t) * env * vol * 32767).astype(np.int16)
            return pygame.sndarray.make_sound(wave)
        except Exception:
            return None

    def set_volume(self, v: float):
        self._volume = max(0.0, min(1.0, v))
        for snd in (self.snd_jump, self.snd_score, self.snd_die, self.snd_click):
            if snd:
                try:
                    snd.set_volume(self._volume)
                except Exception:
                    pass

    def play(self, snd):
        if snd:
            try:
                snd.play()
            except Exception:
                pass

    # ── Bird sprite ───────────────────────────────────
    def _make_bird(self, wing):
        s = pygame.Surface((38, 28), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (255, 205,  15), (2, 4, 30, 20))
        pygame.draw.ellipse(s, (220, 160,   0), (2, 15, 30, 9))
        pygame.draw.ellipse(s, (255, 235, 100), (5,  5, 13, 9))
        wy = {"mid": 10, "up": 3, "down": 16}[wing]
        pygame.draw.ellipse(s, (230, 110,  10), (5, wy, 20, 9))
        pygame.draw.ellipse(s, (255, 160,  50), (7, wy+1, 12, 5))
        pygame.draw.polygon(s, (210, 100,  10), [(2, 9), (0, 5), (3, 15)])
        pygame.draw.circle(s, WHITE, (27,  9), 6)
        pygame.draw.circle(s, BLACK, (29,  9), 4)
        pygame.draw.circle(s, WHITE, (30,  7), 2)
        pygame.draw.polygon(s, (255, 120,  0), [(32, 10), (38, 13), (32, 16)])
        pygame.draw.polygon(s, (200,  90,  0), [(32, 13), (38, 13), (32, 16)])
        pygame.draw.ellipse(s, (180, 130,  0), (2, 4, 30, 20), 1)
        return s.convert_alpha()

    def _make_enemy(self, wing):
        s = pygame.Surface((30, 22), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (205,  55,  55), (2, 3, 22, 16))
        pygame.draw.ellipse(s, (160,  30,  30), (2, 12, 22, 7))
        pygame.draw.ellipse(s, (235, 100, 100), (4,  4, 10, 7))
        wy = {"mid": 7, "up": 2, "down": 13}[wing]
        pygame.draw.ellipse(s, (215,  75,   0), (4, wy, 14, 7))
        pygame.draw.ellipse(s, (255, 140,  50), (6, wy+1, 8, 4))
        pygame.draw.circle(s, WHITE, (7, 7), 4)
        pygame.draw.circle(s, BLACK, (5, 7), 2)
        pygame.draw.circle(s, WHITE, (4, 6), 1)
        pygame.draw.polygon(s, (200, 100,  0), [(2, 8), (0, 10), (2, 12)])
        return s.convert_alpha()

    # ── Pipe ─────────────────────────────────────────
    def make_pipe_surfs(self, gap_y, gap_size):
        cap_h, cap_x = 22, 4
        top_h = max(gap_y, 1)
        ts = pygame.Surface((PIPE_WIDTH, top_h), pygame.SRCALPHA)
        body = pygame.Rect(cap_x, 0, PIPE_WIDTH - cap_x*2, top_h - cap_h)
        pygame.draw.rect(ts, PIPE_GREEN, body)
        pygame.draw.rect(ts, PIPE_SHINE, (cap_x+3, 0, 9, top_h - cap_h))
        pygame.draw.rect(ts, PIPE_DARK,  body, 2)
        cap = pygame.Rect(0, top_h - cap_h, PIPE_WIDTH, cap_h)
        pygame.draw.rect(ts, PIPE_GREEN, cap)
        pygame.draw.rect(ts, PIPE_SHINE, (3, top_h-cap_h+3, 12, cap_h-6))
        pygame.draw.rect(ts, PIPE_BORDER, cap, 2)

        bot_y = gap_y + gap_size
        bot_h = max(SCREEN_HEIGHT - bot_y - GROUND_HEIGHT, 1)
        bs = pygame.Surface((PIPE_WIDTH, bot_h), pygame.SRCALPHA)
        cap2 = pygame.Rect(0, 0, PIPE_WIDTH, cap_h)
        pygame.draw.rect(bs, PIPE_GREEN, cap2)
        pygame.draw.rect(bs, PIPE_SHINE, (3, 3, 12, cap_h-6))
        pygame.draw.rect(bs, PIPE_BORDER, cap2, 2)
        body2 = pygame.Rect(cap_x, cap_h, PIPE_WIDTH - cap_x*2, bot_h - cap_h)
        pygame.draw.rect(bs, PIPE_GREEN, body2)
        pygame.draw.rect(bs, PIPE_SHINE, (cap_x+3, cap_h, 9, bot_h - cap_h))
        pygame.draw.rect(bs, PIPE_DARK,  body2, 2)
        return ts.convert_alpha(), bs.convert_alpha(), bot_y

    # ── Background ───────────────────────────────────
    def _make_background(self):
        s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        sky_h = SCREEN_HEIGHT - GROUND_HEIGHT
        for y in range(sky_h):
            t = y / sky_h
            r = int(SKY_TOP[0] + (SKY_BOT[0]-SKY_TOP[0]) * t)
            g = int(SKY_TOP[1] + (SKY_BOT[1]-SKY_TOP[1]) * t)
            b = int(SKY_TOP[2] + (SKY_BOT[2]-SKY_TOP[2]) * t)
            pygame.draw.line(s, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        pygame.draw.ellipse(s, (140, 195, 115), (-30, sky_h-65, 210, 100))
        pygame.draw.ellipse(s, (115, 170,  90), (160, sky_h-55, 190,  90))
        pygame.draw.ellipse(s, (140, 195, 115), (300, sky_h-70, 200, 105))
        for cx2, cy2 in [(55,75),(185,48),(310,95),(125,135),(260,58)]:
            self._draw_cloud(s, cx2, cy2)
        return s.convert()

    def _draw_cloud(self, s, x, y):
        c, sh = (238, 248, 255), (210, 225, 242)
        pygame.draw.ellipse(s, c,  (x,    y,    62, 26))
        pygame.draw.ellipse(s, c,  (x+15, y-16, 42, 32))
        pygame.draw.ellipse(s, c,  (x+36, y,    46, 22))
        pygame.draw.ellipse(s, sh, (x+5,  y+11, 57, 16))

    def _make_ground(self):
        w = SCREEN_WIDTH * 2
        s = pygame.Surface((w, GROUND_HEIGHT))
        pygame.draw.rect(s, GROUND_GRN, (0, 0, w, 22))
        pygame.draw.rect(s, GROUND_BRN, (0, 22, w, GROUND_HEIGHT-22))
        for x in range(0, w, 28):
            pygame.draw.polygon(s, (85,175,38), [(x,18),(x+4,3),(x+9,18)])
            pygame.draw.polygon(s, (85,175,38), [(x+14,18),(x+18,7),(x+23,18)])
        for y in range(32, GROUND_HEIGHT, 14):
            pygame.draw.line(s, (125, 90, 55), (0, y), (w, y), 1)
        return s.convert()


# ═══════════════════════════════════════════════════════
#   3. GAME OBJECTS
# ═══════════════════════════════════════════════════════
class Bird:
    W, H = 38, 28

    def __init__(self, assets):
        self.assets  = assets
        self.x       = 110
        self.y       = float(SCREEN_HEIGHT // 2)
        self.vel_y   = 0.0
        self.angle   = 0.0
        self.frame   = 0
        self._ftimer = 0
        self.alive   = True
        self.rect    = pygame.Rect(0, 0, self.W - 8, self.H - 4)
        self._update_rect()

    def jump(self):
        self.vel_y = JUMP_STRENGTH
        self.assets.play(self.assets.snd_jump)

    def update(self):
        self.vel_y = min(self.vel_y + GRAVITY, 14)
        self.y    += self.vel_y
        target     = max(-80.0, min(35.0, -self.vel_y * 4))
        self.angle += (target - self.angle) * 0.15
        self._ftimer += 1
        if self._ftimer >= 7:
            self._ftimer = 0
            self.frame   = (self.frame + 1) % 3
        self._update_rect()
        if self.y + self.H//2 >= SCREEN_HEIGHT - GROUND_HEIGHT:
            self.y = float(SCREEN_HEIGHT - GROUND_HEIGHT - self.H//2)
            self.alive = False
        if self.y < self.H//2:
            self.y, self.vel_y = float(self.H//2), 0.0

    def _update_rect(self):
        self.rect.center = (int(self.x), int(self.y))

    def draw(self, surf):
        img = self.assets.bird_frames[self.frame]
        rot = pygame.transform.rotate(img, self.angle)
        surf.blit(rot, rot.get_rect(center=(int(self.x), int(self.y))))


class Pipe:
    def __init__(self, assets, x):
        self.assets = assets
        self.x      = float(x)
        self.gap_y  = random.randint(110, SCREEN_HEIGHT - GROUND_HEIGHT - PIPE_GAP - 90)
        self.scored = False
        self.top_s, self.bot_s, self.bot_y = assets.make_pipe_surfs(self.gap_y, PIPE_GAP)
        xi = int(self.x)
        self.top_rect = pygame.Rect(xi, 0, PIPE_WIDTH, self.gap_y)
        self.bot_rect = pygame.Rect(xi, self.bot_y, PIPE_WIDTH,
                                    SCREEN_HEIGHT - self.bot_y - GROUND_HEIGHT)

    def update(self):
        self.x -= PIPE_SPEED
        xi = int(self.x)
        self.top_rect.x = xi
        self.bot_rect.x = xi

    def draw(self, surf):
        xi = int(self.x)
        surf.blit(self.top_s, (xi, 0))
        surf.blit(self.bot_s, (xi, self.bot_y))

    def off_screen(self):
        return self.x + PIPE_WIDTH < 0

    def hits(self, br):
        b = br.inflate(-6, -6)
        return self.top_rect.colliderect(b) or self.bot_rect.colliderect(b)


class EnemyBird:
    def __init__(self, assets):
        self.assets  = assets
        self.x       = float(SCREEN_WIDTH + 30)
        self.y       = float(random.randint(70, SCREEN_HEIGHT - GROUND_HEIGHT - 70))
        self.vel_y   = random.uniform(-1.2, 1.2)
        self.frame   = 0
        self._ftimer = 0
        self.rect    = pygame.Rect(0, 0, 22, 16)
        self.rect.center = (int(self.x), int(self.y))

    def update(self):
        self.x   -= ENEMY_SPEED
        self.y   += self.vel_y
        if self.y < 40 or self.y > SCREEN_HEIGHT - GROUND_HEIGHT - 40:
            self.vel_y *= -1
        self._ftimer += 1
        if self._ftimer >= 6:
            self._ftimer = 0
            self.frame   = (self.frame + 1) % 3
        self.rect.center = (int(self.x), int(self.y))

    def draw(self, surf):
        img = pygame.transform.flip(self.assets.enemy_frames[self.frame], True, False)
        surf.blit(img, img.get_rect(center=(int(self.x), int(self.y))))

    def off_screen(self):
        return self.x + 30 < 0

    def hits(self, br):
        return self.rect.inflate(-4, -4).colliderect(br)


# ═══════════════════════════════════════════════════════
#   4. PARTICLE SYSTEM
# ═══════════════════════════════════════════════════════
class ParticleSystem:
    def __init__(self):
        self._pool = []

    def emit(self, x, y, color=(255,210,50), n=10):
        for _ in range(n):
            self._pool.append({
                "x": float(x), "y": float(y),
                "vx": random.uniform(-3.5, 3.5),
                "vy": random.uniform(-5, -0.5),
                "life": random.randint(18, 36), "max_life": 36,
                "color": color, "r": random.randint(2, 5),
            })

    def update(self):
        alive = []
        for p in self._pool:
            p["x"] += p["vx"]; p["y"] += p["vy"]; p["vy"] += 0.25
            p["life"] -= 1
            if p["life"] > 0:
                alive.append(p)
        self._pool = alive

    def draw(self, surf):
        for p in self._pool:
            a   = int(255 * p["life"] / p["max_life"])
            tmp = pygame.Surface((p["r"]*2, p["r"]*2), pygame.SRCALPHA)
            pygame.draw.circle(tmp, (*p["color"][:3], a), (p["r"], p["r"]), p["r"])
            surf.blit(tmp, (int(p["x"])-p["r"], int(p["y"])-p["r"]))


# ═══════════════════════════════════════════════════════
#   5. UI HELPERS
# ═══════════════════════════════════════════════════════
class UI:
    def __init__(self):
        pygame.font.init()
        self.f_title  = pygame.font.SysFont("Courier", 46, bold=True)
        self.f_large  = pygame.font.SysFont("Courier", 36, bold=True)
        self.f_medium = pygame.font.SysFont("Courier", 26, bold=True)
        self.f_small  = pygame.font.SysFont("Courier", 18, bold=True)
        self.f_tiny   = pygame.font.SysFont("Courier", 14, bold=True)

    def text(self, surf, txt, font, color, cx, cy,
             shadow=True, shadow_color=SHADOW_COL):
        if shadow:
            s = font.render(txt, True, shadow_color)
            surf.blit(s, s.get_rect(center=(cx+2, cy+2)))
        t = font.render(txt, True, color)
        surf.blit(t, t.get_rect(center=(cx, cy)))

    def panel(self, surf, rect, alpha=210, border_color=PANEL_BORDER, radius=8):
        bg = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(bg, (0, 0, 30, alpha), bg.get_rect(), border_radius=radius)
        pygame.draw.rect(bg, (*border_color, 255), bg.get_rect(), 3, border_radius=radius)
        surf.blit(bg, rect.topleft)

    def hline(self, surf, y, x1=60, x2=340, color=SCORE_GOLD, thick=2):
        pygame.draw.line(surf, color, (x1, y), (x2, y), thick)

    def button(self, surf, label, font, rect,
               color_fill, color_text, border_color=WHITE, radius=10):
        bg = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(bg, (*color_fill, 220), bg.get_rect(), border_radius=radius)
        pygame.draw.rect(bg, (*border_color, 255), bg.get_rect(), 2, border_radius=radius)
        surf.blit(bg, rect.topleft)
        t = font.render(label, True, color_text)
        surf.blit(t, t.get_rect(center=rect.center))
        return rect


# ═══════════════════════════════════════════════════════
#   6. SLIDER WIDGET
# ═══════════════════════════════════════════════════════
class Slider:
    """
    Thanh trượt ngang tương tác – hỗ trợ click & drag.
    value: float [0.0, 1.0]
    """
    TRACK_H = 10
    KNOB_R  = 14

    def __init__(self, cx, cy, width, value, fill_color):
        self.cx    = cx
        self.cy    = cy
        self.width = width
        self.value = float(value)
        self.fill  = fill_color
        self._drag = False
        self._x0   = cx - width // 2
        self._x1   = cx + width // 2

    @property
    def _knob_x(self):
        return int(self._x0 + self.value * self.width)

    def handle_event(self, event):
        """Trả True nếu value đã thay đổi."""
        changed = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            kx, ky = self._knob_x, self.cy
            mx, my = event.pos
            # Click vào knob
            if (mx - kx)**2 + (my - ky)**2 <= (self.KNOB_R + 8)**2:
                self._drag = True
            # Click vào track
            elif abs(my - self.cy) <= self.TRACK_H + 10 and self._x0 <= mx <= self._x1:
                self._drag = True
                self.value = max(0.0, min(1.0, (mx - self._x0) / self.width))
                changed = True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._drag = False
        if event.type == pygame.MOUSEMOTION and self._drag:
            mx = event.pos[0]
            self.value = max(0.0, min(1.0, (mx - self._x0) / self.width))
            changed = True
        return changed

    def draw(self, surf):
        # Track
        track = pygame.Rect(self._x0, self.cy - self.TRACK_H//2,
                            self.width, self.TRACK_H)
        pygame.draw.rect(surf, SL_TRACK, track, border_radius=5)

        # Fill
        fill_w = max(1, int(self.value * self.width))
        pygame.draw.rect(surf, self.fill,
                         pygame.Rect(self._x0, self.cy - self.TRACK_H//2,
                                     fill_w, self.TRACK_H),
                         border_radius=5)

        # Tick marks mỗi 25%
        for pct in (0.25, 0.50, 0.75):
            tx = int(self._x0 + pct * self.width)
            pygame.draw.line(surf, (100, 100, 140),
                             (tx, self.cy - self.TRACK_H//2 - 3),
                             (tx, self.cy + self.TRACK_H//2 + 3), 1)

        # Knob shadow
        kx = self._knob_x
        pygame.draw.circle(surf, SL_KNOB_SHD, (kx+2, self.cy+2), self.KNOB_R)
        # Knob
        pygame.draw.circle(surf, SL_KNOB,  (kx, self.cy), self.KNOB_R)
        pygame.draw.circle(surf, self.fill, (kx, self.cy), self.KNOB_R - 5)
        pygame.draw.circle(surf, (200, 200, 220), (kx, self.cy), self.KNOB_R, 2)


# ═══════════════════════════════════════════════════════
#   7. SETTINGS SCREEN
# ═══════════════════════════════════════════════════════
class SettingsScreen:
    """
    Panel cài đặt pixel-art:
      • Slider Brightness  (0–100%)  → overlay đen
      • Slider Sound       (0–100%)  → pygame volume
      • Nút BACK (hoặc ESC)
    """
    PANEL_W = 344
    PANEL_H = 400

    def __init__(self, ui: UI, assets: AssetManager,
                 brightness: float, volume: float):
        self.ui     = ui
        self.assets = assets

        px = (SCREEN_WIDTH  - self.PANEL_W) // 2
        py = (SCREEN_HEIGHT - self.PANEL_H) // 2
        self.panel_rect = pygame.Rect(px, py, self.PANEL_W, self.PANEL_H)
        cx = SCREEN_WIDTH // 2

        sl_y1 = py + 168    # Brightness slider Y
        sl_y2 = py + 285    # Volume slider Y
        sw    = 230

        self.sl_brt = Slider(cx, sl_y1, sw, brightness, SL_FILL_BRT)
        self.sl_vol = Slider(cx, sl_y2, sw, volume,     SL_FILL_VOL)

        self.btn_back = pygame.Rect(cx - 85, py + self.PANEL_H - 62, 170, 44)

        # Pre-render icons
        self._icon_sun     = self._make_sun_icon()
        self._icon_speaker = self._make_speaker_icon()

    # ── Icons ─────────────────────────────────────────
    def _make_sun_icon(self):
        s = pygame.Surface((28, 28), pygame.SRCALPHA)
        cx, cy = 14, 14
        pygame.draw.circle(s, (255, 220, 50), (cx, cy), 7)
        for a in range(0, 360, 45):
            r = math.radians(a)
            x1 = int(cx + 9  * math.cos(r))
            y1 = int(cy + 9  * math.sin(r))
            x2 = int(cx + 13 * math.cos(r))
            y2 = int(cy + 13 * math.sin(r))
            pygame.draw.line(s, (255, 200, 30), (x1,y1), (x2,y2), 2)
        return s

    def _make_speaker_icon(self):
        s = pygame.Surface((28, 28), pygame.SRCALPHA)
        pygame.draw.polygon(s, (80, 200, 255),
                            [(5,10),(12,10),(18,5),(18,23),(12,18),(5,18)])
        for r_in, r_out in [(5,8),(9,13)]:
            for a in range(-45, 46, 6):
                rd = math.radians(a)
                x1 = int(20 + r_in  * math.cos(rd))
                y1 = int(14 + r_in  * math.sin(rd))
                x2 = int(20 + r_out * math.cos(rd))
                y2 = int(14 + r_out * math.sin(rd))
                pygame.draw.line(s, (80, 200, 255), (x1,y1), (x2,y2), 2)
        return s

    # ── Events ────────────────────────────────────────
    def handle_event(self, event):
        """
        Returns: "back" | "brightness" | "volume" | None
        """
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "back"

        ch_brt = self.sl_brt.handle_event(event)
        ch_vol = self.sl_vol.handle_event(event)

        if ch_vol:
            self.assets.set_volume(self.sl_vol.value)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_back.collidepoint(event.pos):
                self.assets.play(self.assets.snd_click)
                return "back"

        if ch_brt:
            return "brightness"
        if ch_vol:
            return "volume"
        return None

    @property
    def brightness(self):
        return self.sl_brt.value

    @property
    def volume(self):
        return self.sl_vol.value

    # ── Draw ──────────────────────────────────────────
    def draw(self, surf):
        cx = SCREEN_WIDTH // 2
        px = self.panel_rect.x
        py = self.panel_rect.y

        # Semi-transparent backdrop
        ov = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 150))
        surf.blit(ov, (0, 0))

        # Main panel
        self.ui.panel(surf, self.panel_rect, alpha=235,
                      border_color=PANEL_BORDER, radius=14)

        # ── Title ──
        self.ui.text(surf, "SETTINGS", self.ui.f_large,
                     SCORE_GOLD, cx, py + 38, shadow_color=(110, 75, 0))
        # Gear deco
        for dx in (-110, 110):
            gc = pygame.Surface((22, 22), pygame.SRCALPHA)
            _draw_gear(gc, 11, 11, 10, 6, 7, (255, 200, 0, 200))
            surf.blit(gc, (cx + dx - 11, py + 27))

        self.ui.hline(surf, py + 66, px+18, px+self.PANEL_W-18, SCORE_GOLD, 2)

        # ══ BRIGHTNESS section ══════════════════════
        # Row label
        self.ui.text(surf, "BRIGHTNESS", self.ui.f_small,
                     (220, 230, 255), cx, py + 105)

        # Left icon: moon (dark)
        _draw_moon(surf, px + 30, self.sl_brt.cy)

        # Right icon: sun (bright)
        surf.blit(self._icon_sun,
                  (px + self.PANEL_W - 42, self.sl_brt.cy - 14))

        # Slider
        self.sl_brt.draw(surf)

        # Percentage label
        brt_pct = int(self.sl_brt.value * 100)
        label   = f"{brt_pct}%"
        # Colour shifts warm→cool as brightness increases
        brt_col = _lerp_color((150, 150, 200), SL_FILL_BRT, self.sl_brt.value)
        self.ui.text(surf, label, self.ui.f_small, brt_col,
                     cx, self.sl_brt.cy + 32, shadow=False)

        # Preview circle (tiny screen brightness preview)
        _draw_brightness_preview(surf, px + self.PANEL_W - 18,
                                 self.sl_brt.cy + 30, self.sl_brt.value)

        self.ui.hline(surf, py + 228, px+18, px+self.PANEL_W-18,
                      (65, 65, 100), 1)

        # ══ SOUND VOLUME section ════════════════════
        self.ui.text(surf, "SOUND VOLUME", self.ui.f_small,
                     (220, 230, 255), cx, py + 248)

        # Left icon: mute symbol
        _draw_mute(surf, px + 30, self.sl_vol.cy)

        # Right icon: speaker
        surf.blit(self._icon_speaker,
                  (px + self.PANEL_W - 42, self.sl_vol.cy - 14))

        self.sl_vol.draw(surf)

        vol_pct = int(self.sl_vol.value * 100)
        vol_col = _lerp_color((150, 150, 200), SL_FILL_VOL, self.sl_vol.value)
        self.ui.text(surf, f"{vol_pct}%", self.ui.f_small, vol_col,
                     cx, self.sl_vol.cy + 32, shadow=False)

        if vol_pct == 0:
            self.ui.text(surf, "[ MUTED ]", self.ui.f_tiny,
                         (255, 80, 80), cx, self.sl_vol.cy + 54, shadow=False)

        self.ui.hline(surf, py + 340, px+18, px+self.PANEL_W-18,
                      (65, 65, 100), 1)

        # ══ BACK button ═════════════════════════════
        hover = self.btn_back.collidepoint(pygame.mouse.get_pos())
        fill  = (55, 85, 165) if not hover else (85, 125, 215)
        self.ui.button(surf, "  BACK", self.ui.f_small,
                       self.btn_back, fill, WHITE,
                       border_color=(170, 195, 255), radius=10)
        # Arrow deco
        arr = self.ui.f_small.render("<", True, (200, 230, 255))
        surf.blit(arr, arr.get_rect(midleft=(self.btn_back.x + 14,
                                             self.btn_back.centery)))

        # Keyboard hint
        self.ui.text(surf, "[ ESC to close ]", self.ui.f_tiny,
                     (130, 150, 190), cx, py + self.PANEL_H - 12, shadow=False)


# ═══════════════════════════════════════════════════════
#   8. SETTINGS ICON HELPERS  (module-level pure functions)
# ═══════════════════════════════════════════════════════
def _lerp_color(c1, c2, t):
    return tuple(int(c1[i] + (c2[i]-c1[i]) * t) for i in range(3))


def _draw_gear(surf, cx, cy, r_out, r_in, n_teeth, color):
    pts = []
    for i in range(n_teeth * 2):
        a = math.radians(i * 360 / (n_teeth * 2))
        r = r_out if i % 2 == 0 else r_in
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    pygame.draw.polygon(surf, color, pts)
    pygame.draw.circle(surf, (0, 0, 30, 200), (cx, cy), r_in - 2)


def _draw_moon(surf, cx, cy):
    """Crescent moon – icon cho "tối"."""
    s = pygame.Surface((28, 28), pygame.SRCALPHA)
    pygame.draw.circle(s, (200, 210, 240), (14, 14), 11)
    pygame.draw.circle(s, (0, 0, 30, 255), (19, 11), 9)
    surf.blit(s, (cx - 14, cy - 14))


def _draw_mute(surf, cx, cy):
    """Loa bị gạch chéo – icon mute."""
    s = pygame.Surface((28, 28), pygame.SRCALPHA)
    pygame.draw.polygon(s, (150, 150, 180),
                        [(4, 9),(11, 9),(17, 4),(17, 22),(11, 17),(4, 17)])
    pygame.draw.line(s, (220, 80, 80), (18, 8), (26, 20), 3)
    pygame.draw.line(s, (220, 80, 80), (26, 8), (18, 20), 3)
    surf.blit(s, (cx - 14, cy - 14))


def _draw_brightness_preview(surf, rx, ry, brightness):
    """Hình tròn nhỏ preview sáng/tối."""
    r = 8
    # Nền sáng
    pygame.draw.circle(surf, (255, 230, 150), (rx, ry), r)
    # Phủ tối
    dark_a = int((1.0 - brightness) * 220)
    if dark_a > 0:
        dim = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        pygame.draw.circle(dim, (0, 0, 0, dark_a), (r, r), r)
        surf.blit(dim, (rx - r, ry - r))
    pygame.draw.circle(surf, (200, 200, 200), (rx, ry), r, 1)


# ═══════════════════════════════════════════════════════
#   9. GEAR BUTTON (menu corner)
# ═══════════════════════════════════════════════════════
class GearButton:
    SIZE = 46

    def __init__(self):
        self.rect   = pygame.Rect(SCREEN_WIDTH - self.SIZE - 10, 10,
                                  self.SIZE, self.SIZE)
        self._angle = 0.0

    def update(self):
        self._angle = (self._angle + 0.5) % 360

    def draw(self, surf):
        hover = self.rect.collidepoint(pygame.mouse.get_pos())
        fill  = (50, 70, 130, 210) if not hover else (80, 115, 195, 240)

        bg = pygame.Surface((self.SIZE, self.SIZE), pygame.SRCALPHA)
        pygame.draw.circle(bg, fill, (self.SIZE//2, self.SIZE//2), self.SIZE//2)
        pygame.draw.circle(bg, (*SCORE_GOLD, 255), (self.SIZE//2, self.SIZE//2),
                           self.SIZE//2, 2)
        surf.blit(bg, self.rect.topleft)

        cx = self.rect.centerx
        cy = self.rect.centery
        n, ro, ri = 8, 17, 12
        pts = []
        for i in range(n * 2):
            a = math.radians(self._angle + i * 360 / (n * 2))
            r = ro if i % 2 == 0 else ri
            pts.append((cx + r*math.cos(a), cy + r*math.sin(a)))
        pygame.draw.polygon(surf, SCORE_GOLD, pts)
        pygame.draw.circle(surf, (30, 30, 65), (cx, cy), 6)

    def is_clicked(self, event):
        return (event.type == pygame.MOUSEBUTTONDOWN and
                event.button == 1 and
                self.rect.collidepoint(event.pos))


# ═══════════════════════════════════════════════════════
#   10. MAIN GAME
# ═══════════════════════════════════════════════════════
class FlappyBirdGame:
    """
    State Machine:
      MENU ──(Space/Click)──► PLAYING ──(die)──► GAMEOVER
       │                                              │
       └──(⚙ / ESC)──► SETTINGS ◄──(ESC)────────────┘
                              │
                           (BACK)
                              │
                    ◄─────────┘  (trở về state trước)
    """

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Flappy Bird – Pixel Edition")
        self.clock  = pygame.time.Clock()

        self.assets    = AssetManager()
        self.ui        = UI()
        self.particles = ParticleSystem()

        # Settings
        self._brightness = 1.0
        self._volume     = 0.8
        self.assets.set_volume(self._volume)
        self._dim_surf   = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT),
                                          pygame.SRCALPHA)
        self._settings   = SettingsScreen(self.ui, self.assets,
                                          self._brightness, self._volume)
        self._prev_state = STATE_MENU

        # Game state
        self.state      = STATE_MENU
        self.high_score = 0
        self.score      = 0

        # UI elements
        self._gear       = GearButton()
        self._hover_t    = 0.0
        self._blink_t    = 0
        self._blink_show = True
        self._ground_scroll = 0
        self._go_alpha   = 0
        self._warn_t     = 0

        # Objects
        self.bird    = None
        self.pipes   = []
        self.enemies = []
        self._next_pipe  = 0
        self._next_enemy = 0

    # ── Brightness overlay ───────────────────────────
    def _apply_brightness(self):
        """Phủ lớp đen nếu brightness < 1.0."""
        alpha = int((1.0 - self._brightness) * 210)
        if alpha > 0:
            self._dim_surf.fill((0, 0, 0, alpha))
            self.screen.blit(self._dim_surf, (0, 0))

    # ── Reset ────────────────────────────────────────
    def _reset(self):
        self.bird      = Bird(self.assets)
        self.pipes     = []
        self.enemies   = []
        self.score     = 0
        self.particles = ParticleSystem()
        now = pygame.time.get_ticks()
        self._next_pipe  = now + 1200
        self._next_enemy = now + 5000
        self._go_alpha   = 0

    # ── Events ───────────────────────────────────────
    def _handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            # Settings screen chiếm toàn bộ input
            if self.state == STATE_SETTINGS:
                result = self._settings.handle_event(e)
                if result == "back":
                    self._brightness = self._settings.brightness
                    self._volume     = self._settings.volume
                    self.state       = self._prev_state
                elif result == "brightness":
                    self._brightness = self._settings.brightness
                elif result == "volume":
                    self._volume = self._settings.volume
                continue

            # ESC → open settings (chỉ từ menu/gameover)
            if (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE
                    and self.state in (STATE_MENU, STATE_GAMEOVER)):
                self._open_settings()
                continue

            # Gear button click (menu)
            if self.state == STATE_MENU and self._gear.is_clicked(e):
                self.assets.play(self.assets.snd_click)
                self._open_settings()
                continue

            # Game actions
            is_space = (e.type == pygame.KEYDOWN and
                        e.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w))
            is_click = e.type == pygame.MOUSEBUTTONDOWN
            if is_space or is_click:
                self._on_action()

    def _open_settings(self):
        self._prev_state             = self.state
        self._settings.sl_brt.value = self._brightness
        self._settings.sl_vol.value = self._volume
        self.state                   = STATE_SETTINGS

    def _on_action(self):
        if self.state == STATE_MENU:
            self.state = STATE_PLAYING
            self._reset()
        elif self.state == STATE_PLAYING and self.bird and self.bird.alive:
            self.bird.jump()
        elif self.state == STATE_GAMEOVER:
            self.state       = STATE_MENU
            self._hover_t    = 0.0
            self._blink_t    = 0
            self._blink_show = True

    # ── Update ───────────────────────────────────────
    def _update_menu(self):
        self._hover_t      += 1
        self._blink_t      += 1
        self._ground_scroll = (self._ground_scroll + 1) % SCREEN_WIDTH
        if self._blink_t > 35:
            self._blink_t   = 0
            self._blink_show= not self._blink_show
        self._gear.update()

    def _update_playing(self):
        now = pygame.time.get_ticks()
        self._ground_scroll = (self._ground_scroll + PIPE_SPEED) % SCREEN_WIDTH
        self.bird.update()

        if now >= self._next_pipe:
            self.pipes.append(Pipe(self.assets, SCREEN_WIDTH + 10))
            self._next_pipe = now + PIPE_INTERVAL

        if self.score >= ENEMY_SCORE_THRESHOLD and now >= self._next_enemy:
            self.enemies.append(EnemyBird(self.assets))
            interval = max(1800, 4200-(self.score-ENEMY_SCORE_THRESHOLD)*25)
            self._next_enemy = now + interval

        for p in self.pipes[:]:
            p.update()
            if p.off_screen():
                self.pipes.remove(p); continue
            if not p.scored and p.x + PIPE_WIDTH < self.bird.x:
                p.scored = True
                self.score += 1
                if self.score > self.high_score:
                    self.high_score = self.score
                self.assets.play(self.assets.snd_score)
                self.particles.emit(self.bird.x, self.bird.y, SCORE_GOLD, 12)
            if p.hits(self.bird.rect):
                self._kill_bird((255, 100, 50))

        for en in self.enemies[:]:
            en.update()
            if en.off_screen():
                self.enemies.remove(en); continue
            if en.hits(self.bird.rect):
                self._kill_bird((255, 50, 80))

        self.particles.update()

        if not self.bird.alive:
            self.state       = STATE_GAMEOVER
            self._go_alpha   = 0
            self._blink_t    = 0
            self._blink_show = False

    def _kill_bird(self, color):
        if self.bird.alive:
            self.bird.alive = False
            self.assets.play(self.assets.snd_die)
            self.particles.emit(self.bird.x, self.bird.y, color, 18)

    def _update_gameover(self):
        self._go_alpha   = min(255, self._go_alpha + 7)
        self._blink_t   += 1
        if self._blink_t > 40:
            self._blink_t   = 0
            self._blink_show= not self._blink_show
        self.particles.update()

    # ── Draw helpers ─────────────────────────────────
    def _draw_bg(self):
        self.screen.blit(self.assets.bg_surf, (0, 0))

    def _draw_ground(self):
        gy = SCREEN_HEIGHT - GROUND_HEIGHT
        ox = -self._ground_scroll
        self.screen.blit(self.assets.ground_surf, (ox, gy))
        self.screen.blit(self.assets.ground_surf, (ox+SCREEN_WIDTH, gy))

    def _draw_pipes_enemies(self):
        for p  in self.pipes:   p.draw(self.screen)
        for en in self.enemies: en.draw(self.screen)

    def _draw_score_hud(self):
        self.ui.text(self.screen, str(self.score), self.ui.f_large,
                     WHITE, SCREEN_WIDTH//2, 52)

    # ── Draw MENU ────────────────────────────────────
    def _draw_menu(self):
        self._draw_bg()
        self._draw_ground()
        cx = SCREEN_WIDTH // 2

        self.ui.panel(self.screen, pygame.Rect(45, 105, 310, 60))
        self.ui.text(self.screen, "FLAPPY BIRD", self.ui.f_title,
                     SCORE_GOLD, cx, 135, shadow_color=(120,70,0))

        hover = math.sin(self._hover_t * 0.055) * 13
        by    = int(SCREEN_HEIGHT//2 - 20 + hover)
        img   = self.assets.bird_frames[1]
        big   = pygame.transform.scale(img, (57, 42))
        self.screen.blit(big, big.get_rect(center=(cx, by)))

        if self.high_score > 0:
            self.ui.text(self.screen, f"BEST  {self.high_score:>4}",
                         self.ui.f_small, SCORE_GOLD, cx, 310)

        if self._blink_show:
            self.ui.panel(self.screen, pygame.Rect(55,330,290,36),
                          alpha=130, border_color=(200,200,200))
            self.ui.text(self.screen, "PRESS  SPACE  TO  START",
                         self.ui.f_small, WHITE, cx, 348)

        self.ui.text(self.screen, "SPACE / CLICK to flap",
                     self.ui.f_small, (180,220,255), cx, 393, shadow=False)
        self.ui.text(self.screen, "Gear  or  ESC  =  Settings",
                     self.ui.f_tiny, (150,190,220), cx, 416, shadow=False)

        # Gear button (góc phải trên)
        self._gear.draw(self.screen)

    # ── Draw PLAYING ─────────────────────────────────
    def _draw_playing(self):
        self._draw_bg()
        self._draw_pipes_enemies()
        self._draw_ground()
        self.bird.draw(self.screen)
        self.particles.draw(self.screen)
        self._draw_score_hud()
        if ENEMY_SCORE_THRESHOLD-5 <= self.score < ENEMY_SCORE_THRESHOLD:
            self._warn_t = (self._warn_t+1) % 30
            if self._warn_t < 20:
                self.ui.text(self.screen, "ENEMIES INCOMING!",
                             self.ui.f_small, (255,60,60), SCREEN_WIDTH//2, 95)

    # ── Draw GAMEOVER ────────────────────────────────
    def _draw_gameover(self):
        self._draw_bg()
        self._draw_pipes_enemies()
        self._draw_ground()
        if self.bird:
            self.bird.draw(self.screen)
        self.particles.draw(self.screen)

        alpha = self._go_alpha
        pr    = pygame.Rect(35, 140, 330, 295)
        if alpha > 20:
            pan = pygame.Surface(pr.size, pygame.SRCALPHA)
            pygame.draw.rect(pan, (0,0,30,min(alpha,215)),
                             pan.get_rect(), border_radius=12)
            pygame.draw.rect(pan, (*PANEL_BORDER,255),
                             pan.get_rect(), 3, border_radius=12)
            self.screen.blit(pan, pr.topleft)

        cx = SCREEN_WIDTH // 2
        if alpha > 80:
            self.ui.text(self.screen, "GAME  OVER", self.ui.f_title,
                         (240,55,55), cx, 175, shadow_color=(100,0,0))
            self.ui.hline(self.screen, 212, 60, 340, SCORE_GOLD, 2)
            self.ui.text(self.screen, "SCORE", self.ui.f_small,
                         (195,195,195), cx, 235)
            self.ui.text(self.screen, str(self.score),
                         self.ui.f_large, WHITE, cx, 262)
            self.ui.hline(self.screen, 290, 60, 340, (90,90,130), 1)
            self.ui.text(self.screen, "BEST",  self.ui.f_small,
                         SCORE_GOLD, cx, 310)
            self.ui.text(self.screen, str(self.high_score),
                         self.ui.f_large, SCORE_GOLD, cx, 337)
            if self.score > 0 and self.score >= self.high_score:
                self.ui.text(self.screen, "NEW RECORD!",
                             self.ui.f_small, (255,240,80), cx, 368)
            if self._blink_show and alpha > 200:
                self.ui.panel(self.screen, pygame.Rect(65,395,270,34),
                              alpha=140, border_color=(200,200,200))
                self.ui.text(self.screen, "TAP TO PLAY AGAIN",
                             self.ui.f_small, WHITE, cx, 412)
            self.ui.text(self.screen, "ESC = Settings",
                         self.ui.f_tiny, (150,190,230), cx, 442, shadow=False)

    # ── Main loop ────────────────────────────────────
    def run(self):
        while True:
            # ① Events
            self._handle_events()

            # ② Logic Update
            if self.state == STATE_MENU:
                self._update_menu()
            elif self.state == STATE_PLAYING:
                self._update_playing()
            elif self.state == STATE_GAMEOVER:
                self._update_gameover()
            # STATE_SETTINGS: game logic đóng băng

            # ③ Render  (BG → Game → UI → Settings overlay → Brightness)
            if self.state == STATE_MENU:
                self._draw_menu()
            elif self.state == STATE_PLAYING:
                self._draw_playing()
            elif self.state == STATE_GAMEOVER:
                self._draw_gameover()
            elif self.state == STATE_SETTINGS:
                # Render màn hình phía sau rồi đè panel Settings
                if self._prev_state == STATE_MENU:
                    self._draw_menu()
                else:
                    self._draw_gameover()
                self._settings.draw(self.screen)

            # ④ Áp độ sáng CUỐI CÙNG – trước flip
            self._apply_brightness()

            pygame.display.flip()
            self.clock.tick(FPS)


# ═══════════════════════════════════════════════════════
#   ENTRY POINT
# ═══════════════════════════════════════════════════════
if __name__ == "__main__":
    game = FlappyBirdGame()
    game.run()

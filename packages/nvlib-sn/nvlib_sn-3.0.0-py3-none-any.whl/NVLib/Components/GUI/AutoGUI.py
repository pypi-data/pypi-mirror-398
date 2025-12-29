import sys
import os
import json
import shutil
import math
import base64
import io
import os
import warnings
import logging
from kivy.resources import resource_add_path, resource_find

# Hide pygame banner
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

# Silence Kivy completely
os.environ["KIVY_NO_CONSOLELOG"] = "1"
os.environ["KIVY_NO_FILELOG"] = "1"
os.environ["KIVY_LOG_LEVEL"] = "error"

# Silence warnings
warnings.filterwarnings("ignore")

# Silence matplotlib logs
logging.getLogger("matplotlib").setLevel(logging.ERROR)
# --- Kivy Configuration ---
from kivy.config import Config
os.environ["KIVY_NO_ARGS"] = "1"
Config.set('input', 'mouse', 'mouse,multitouch_on_demand') 
Config.set('postproc', 'double_tap_drag_distance', '0')
Config.set('postproc', 'double_tap_time', '0')
Config.set('graphics', 'multisamples', '0') 
Config.set('kivy', 'window_icon', os.path.join(os.path.abspath("."), "logo.png"))


from kivymd.app import MDApp
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.selectioncontrol import MDCheckbox, MDSwitch
from kivymd.uix.slider import MDSlider
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.card import MDCard
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivy.uix.image import Image as KivyImage
from kivy.core.image import Image as CoreImage
from kivy.utils import get_color_from_hex
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button 
from kivy.graphics import Color, RoundedRectangle

SECRET_KEY = b"NVLIB_PROTECT_2025"

def load_secured_asset(filename):
    """General purpose XOR unscrambler for any file type."""
    filepath = sync_to_cache(filename)
    if not os.path.exists(filepath):
        return None
        
    with open(filepath, "rb") as f:
        data = f.read()
    
    if data.startswith(b"NVPRT"):
        raw_payload = data[5:]
        return bytearray([raw_payload[i] ^ SECRET_KEY[i % len(SECRET_KEY)] for i in range(len(raw_payload))])
    return data

def resource_path_bundle(relative_path):
    """ Standard PyInstaller path resolver """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def resource_path(relative_path):
    """ Standard Kivy/PyInstaller path resolver """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def load_secured_json(filename):
    data = load_secured_asset(filename)
    return json.loads(data.decode("utf-8")) if data else None

def get_dynamic_app_name():
    if hasattr(sys, '_MEIPASS'):
        return os.path.splitext(os.path.basename(sys.executable))[0]
    return "NVLib_Dev"

def get_persistent_path():
    app_name = get_dynamic_app_name()
    # Windows: %LOCALAPPDATA%/AppName
    base = os.getenv('LOCALAPPDATA') or os.path.expanduser('~')
    path = os.path.join(base, app_name)
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    return path

def sync_to_cache(filename):
    """Moves assets from the slow EXE bundle to the fast AppData folder once."""
    cache_dir = get_persistent_path()
    persistent_file = os.path.join(cache_dir, filename)
    
    if hasattr(sys, '_MEIPASS'):
        bundle_file = resource_path_bundle(filename)
        # Copy to AppData if it doesn't exist yet
        if os.path.exists(bundle_file) and not os.path.exists(persistent_file):
            try:
                os.makedirs(os.path.dirname(persistent_file), exist_ok=True)
                shutil.copy2(bundle_file, persistent_file)
            except:
                return bundle_file
    
    return persistent_file if os.path.exists(persistent_file) else filename

# --- Base Wrapper (Universal Features) ---
class BaseWrapper:
    def __init__(self, widget, original_font_size=14):
        self.widget = widget
        self.is_visible = True
        self._saved_opacity = 1.0
        self.base_font_size = original_font_size
        self._hover_bound = False

    def set_visible(self, visible):
        self.is_visible = visible
        if visible:
            self.widget.opacity = self._saved_opacity
            self.widget.disabled = False
        else:
            self._saved_opacity = self.widget.opacity
            self.widget.opacity = 0
            self.widget.disabled = True

    def set_enabled(self, enabled=True):
        """Enable or disable the widget without affecting visibility"""
        if hasattr(self.widget, 'disabled'):
            self.widget.disabled = not enabled

    def bg_color(self, hex_code):
        if not hex_code: return
        color = get_color_from_hex(hex_code)
        if hasattr(self.widget, 'md_bg_color'): self.widget.md_bg_color = color
        elif hasattr(self.widget, 'background_color'): self.widget.background_color = color

    def opacity(self, value):
        self.widget.opacity = value
        self._saved_opacity = value

    def border(self, width, hex_code, visible=True):
        # Only apply borders if widget is MDCard
        if not isinstance(self.widget, MDCard): return
        if visible and hex_code and width > 0:
            color = get_color_from_hex(hex_code)
            self.widget.line_color = color
            self.widget.line_width = width
        else:
            self.widget.line_color = (0,0,0,0)


    def on_click(self, func):
        if hasattr(self.widget, 'on_release'):
            self.widget.bind(on_release=lambda x: func())
        else:
            def check_touch(instance, touch):
                if self.is_visible and instance.collide_point(*touch.pos):
                     if touch.button == 'left':
                        func()
                        return True
            self.widget.bind(on_touch_down=check_touch)

    def on_hover(self, on_enter, on_leave=None):
        if not self._hover_bound:
            Window.bind(mouse_pos=lambda w, p: self._check_hover(p, on_enter, on_leave))
            self._hover_bound = True
            self._is_hovering = False

    def _check_hover(self, pos, enter_cb, leave_cb):
        if not self.is_visible: return
        widget_pos = self.widget.to_widget(*pos, relative=True) 
        inside = self.widget.collide_point(*widget_pos)
        if inside and not self._is_hovering:
            self._is_hovering = True
            if enter_cb: enter_cb()
        elif not inside and self._is_hovering:
            self._is_hovering = False
            if leave_cb: leave_cb()

    def text(self, new_text=None):
        if new_text is None: return getattr(self.widget, 'text', "")
        else:
            if hasattr(self.widget, 'text'): self.widget.text = str(new_text)

    def text_color(self, hex_code):
        if not hex_code: return
        c = get_color_from_hex(hex_code)
        if hasattr(self.widget, 'theme_text_color'):
            self.widget.theme_text_color = "Custom"
            self.widget.text_color = c
        elif hasattr(self.widget, 'foreground_color'):
            self.widget.foreground_color = c
        elif hasattr(self.widget, 'color'):
            self.widget.color = c

    def font_size(self, size):
        self.base_font_size = size
        if hasattr(self.widget, 'font_size'): self.widget.font_size = dp(size)

    def font_family(self, font_name):
        if hasattr(self.widget, 'font_name'): self.widget.font_name = font_name
    
    def bold(self, is_bold):
        # Only applicable to widgets that support bold
        if hasattr(self.widget, 'bold'):
            self.widget.bold = is_bold
        elif hasattr(self.widget, 'font_style') and is_bold:
            self.widget.font_style = "H6"


    def update_scale(self, scale_factor):
        if hasattr(self.widget, 'font_size'):
            new_size = max(12, self.base_font_size * scale_factor)
            self.widget.font_size = dp(new_size)

# --- Specific Wrappers ---

class ButtonWrapper(BaseWrapper):
    pass

class ValueWrapper(BaseWrapper):
    def __init__(self, widget, inner_input, fs):
        super().__init__(widget, fs)
        self.inner_input = inner_input
        self.inner_input.bind(size=self._align, font_size=self._align)
    def _align(self, i, v):
        if not self.inner_input.multiline:
            py = (i.height - i.line_height) / 2
            i.padding = [10, py if py > 0 else 0]
        else:
            i.padding = [10, 10]
    def text(self, val=None):
        if val is None: return self.inner_input.text
        else: self.inner_input.text = str(val)
    def text_color(self, hex_code): self.inner_input.foreground_color = get_color_from_hex(hex_code)
    def font_size(self, size):
        self.base_font_size = size; self.inner_input.font_size = dp(size)
    def update_scale(self, sf): self.inner_input.font_size = dp(max(13, self.base_font_size * sf))

class SpinnerWrapper(BaseWrapper):
    def __init__(self, card, entry, btns, mn, mx, fs):
        super().__init__(card, fs)
        self.entry = entry; self.btns = btns; self.mn = mn; self.mx = mx
        self.entry.bind(size=self._align, font_size=self._align)
    def _align(self, i, v):
        py = (i.height - i.line_height) / 2
        i.padding = [0, py if py > 0 else 0]
    def get(self):
        try: return int(self.entry.text)
        except: return self.mn
    def set(self, val): self.entry.text = str(val)
    def update_scale(self, sf):
        self.entry.font_size = dp(max(14, self.base_font_size * sf))
        for b in self.btns: b.font_size = dp(max(18, (self.base_font_size+4)*sf))

class SelectWrapper(BaseWrapper):
    def __init__(self, w, m, fs): super().__init__(w, fs); self.menu = m
    def get(self): return self.widget.text
    def on_select(self, cmd):
        new_items = []
        for i in self.menu.items:
            t = i['text']
            cb = lambda x=t: [setattr(self.widget, 'text', x), self.menu.dismiss(), cmd(x)]
            new_items.append({"viewclass": "OneLineListItem", "text": t, "on_release": cb})
        self.menu.items = new_items

class RadioGroupWrapper(BaseWrapper):
    def __init__(self, w, rads, g, fs): super().__init__(w, fs); self.rads = rads
    def get(self):
        for cb, val in self.rads:
            if cb.active: return val
        return None
    def on_select(self, cmd):
        handler = lambda i, v, t: cmd(t) if v else None
        for cb, val in self.rads: cb.bind(active=lambda i,v,t=val: handler(i,v,t))

class CheckWrapper(BaseWrapper):
    def is_checked(self): return self.widget.active
    def on_toggle(self, cmd): self.widget.bind(active=lambda i, v: cmd())

class ToggleWrapper(BaseWrapper):
    def is_on(self): return self.widget.active
    def on_toggle(self, cmd): self.widget.bind(active=lambda i, v: cmd())

class SliderWrapper(BaseWrapper):
    def get(self): return self.widget.value
    def set(self, val): self.widget.value = val

class ProgressWrapper(BaseWrapper):
    def __init__(self, layout, pb_widget, label_widget, fs):
        super().__init__(layout, fs)
        self.pb = pb_widget
        self.label = label_widget
    def set(self, val):
        self.pb.value = val
        if self.label: self.label.text = f"{int(val)}%"
    def update_scale(self, sf):
        if self.label: self.label.font_size = dp(max(12, self.base_font_size * sf))

# --- Parser ---
class NVLibParserKivy:
    def __init__(self, root, size):
        self.root = root; self.orig_w, self.orig_h = size; self.widgets = {}

    def _hints(self, x, y, w, h):
        return {'x': x/self.orig_w, 'top': 1.0-(y/self.orig_h)}, {'w': w/self.orig_w, 'h': h/self.orig_h}

    def parse(self, comps):
        conts = [c for c in comps if c['type'] in ['Panel', 'CardView']]
        others = [c for c in comps if c['type'] not in ['Panel', 'CardView']]
        c_map = {}

        for d in conts:
            w, wrap, cid = self.create(d, self.root)
            if w:
                self.widgets[cid] = wrap
                inner = MDFloatLayout()
                w.add_widget(inner)
                c_map[cid] = {'l': inner, 'r': (d['x'], d['y'], d['width'], d['height'])}

        for d in others:
            p = self.root
            cx, cy = d['x'], d['y']
            for cid, info in c_map.items():
                r = info['r']
                if r[0] <= cx < r[0]+r[2] and r[1] <= cy < r[1]+r[3]:
                    p = info['l']; d['x'] -= r[0]; d['y'] -= r[1]; break
            w, wrap, cid = self.create(d, p)
            if w: self.widgets[cid] = wrap
        return self.widgets

    def create(self, d, parent):
        t = d['type']; p = d.get('properties', {}); cid = d.get('id')
        ph, sh = self._hints(d['x'], d['y'], d['width'], d['height'])
        fs = p.get('fontSize', 14)
        def hc(k, df=None): return get_color_from_hex(p.get(k)) if p.get(k) else df
        
        wid, wrap = None, None

        if t == 'Button':
            cr = p.get("cornerRadius", 0)
            container = MDCard(
                pos_hint=ph,
                size_hint=(sh['w'], sh['h']),
                radius=[cr],
                padding=0,
                elevation=0,
                md_bg_color=(0,0,0,0)
            )

            wid = MDRaisedButton(
            text=p.get('text',''),
            size_hint=(1,1),
            pos_hint={"center_x":0.5, "center_y":0.5}
            )
            wid.font_size = dp(fs)
            wid.ripple_duration_in_fast = 0.05

            if hc('backgroundColor'): wid.md_bg_color = hc('backgroundColor')
            if hc('textColor'): wid.text_color = hc('textColor')
            if p.get('bold'): wid.font_style = "H6"

            container.add_widget(wid)
            wrap = ButtonWrapper(wid, fs)

            parent.add_widget(container)
            return container, wrap, cid

        elif t == 'Label':
            if p.get('iconName'):
                wid = MDIcon(icon=p.get('iconName'), pos_hint=ph, font_size=dp(fs))
                wid.halign = "center"
            else:
                wid = MDLabel(text=p.get('text',''), pos_hint=ph, size_hint=(sh['w'],sh['h']), valign='top')
                wid.font_size = dp(fs)
                if p.get('bold'): wid.bold = True
            
            if hc('textColor'): wid.theme_text_color="Custom"; wid.text_color=hc('textColor')
            if hc('backgroundColor'): wid.md_bg_color = hc('backgroundColor') 
            wrap = BaseWrapper(wid, fs)

        elif t in ['TextBox', 'TextArea']:
            wid = MDCard(pos_hint=ph, size_hint=(sh['w'],sh['h']), radius=[6])
            wid.md_bg_color = hc('backgroundColor', get_color_from_hex('#ffffff'))
            is_area = (t == 'TextArea')
            ti = TextInput(text=p.get('text',''), hint_text=p.get('hintText',''),
                           multiline=is_area, background_color=(0,0,0,0),
                           foreground_color=hc('textColor', get_color_from_hex('#000000')),
                           font_size=dp(fs), hint_text_color=hc('hintColor', get_color_from_hex('#888888')),
                           padding=[10,10])
            if is_area: ti.do_wrap = True
            if p.get('bold'): ti.bold = True
            wid.add_widget(ti)
            wrap = ValueWrapper(wid, ti, fs)

        elif t == 'Spinner':
            wid = MDCard(pos_hint=ph, size_hint=(sh['w'],sh['h']), radius=[6], ripple_behavior=False)
            wid.md_bg_color = hc('backgroundColor', get_color_from_hex('#f0f0f0'))
            bx = MDBoxLayout(orientation='horizontal')
            mn, mx = int(p.get('min',0)), int(p.get('max',100))
            ti = TextInput(text=str(p.get('value', mn)), multiline=False, background_color=(0,0,0,0),
                           font_size=dp(fs), input_filter='int', halign='center', size_hint_x=0.4)
            if p.get('bold'): ti.bold = True
            if hc('textColor'): ti.foreground_color = hc('textColor')
            
            def chg(delta):
                try: v = int(ti.text)
                except: v = mn
                v = max(mn, min(mx, v + delta))
                ti.text = str(v)
            
            def mk_btn(txt, cb):
                b = Button(text=txt, background_normal='', background_color=(0,0,0,0),
                           color=hc('textColor', get_color_from_hex('#000000')),
                           size_hint_x=0.3, font_size=dp(fs+4))
                b.bind(on_release=lambda x: cb())
                return b

            b1 = mk_btn("-", lambda: chg(-1)); b2 = mk_btn("+", lambda: chg(1))
            bx.add_widget(b1); bx.add_widget(ti); bx.add_widget(b2)
            wid.add_widget(bx)
            wrap = SpinnerWrapper(wid, ti, [b1, b2], mn, mx, fs)

        elif t == 'Checkbox':
            wid = MDFloatLayout(pos_hint=ph, size_hint=(sh['w'],sh['h']))
            cb = MDCheckbox(active=p.get('checked',False), pos_hint={'x':0,'center_y':0.5}, size_hint=(None,None), size=(dp(40),dp(40)))
            if hc('checkedColor'): cb.selected_color = hc('checkedColor')
            wid.add_widget(cb)
            if p.get('text'):
                lbl = MDLabel(text=p.get('text'), pos_hint={'x':0.2,'center_y':0.5}, size_hint=(0.8,1))
                lbl.font_size = dp(fs)
                if p.get('bold'): lbl.bold = True
                if hc('textColor'): lbl.theme_text_color="Custom"; lbl.text_color=hc('textColor')
                wid.add_widget(lbl)
                wrap = CheckWrapper(cb, fs)
            else:
                wrap = CheckWrapper(cb, fs)
                wid = cb

        elif t == 'RadioGroup':
            wid = MDGridLayout(cols=1, pos_hint=ph, size_hint=(sh['w'],sh['h']))
            if p.get('label'):
                l = MDLabel(text=p.get('label'), size_hint_y=None, height=dp(30))
                l.font_size = dp(fs)
                if hc('textColor'): l.theme_text_color="Custom"; l.text_color=hc('textColor')
                if p.get('bold'): l.bold = True
                wid.add_widget(l)
            rads = []
            grp = f"g_{cid}"
            for opt in p.get('options','').split('\n'):
                r = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(30))
                cb = MDCheckbox(group=grp, size_hint=(None,None), size=(dp(30),dp(30)), active=(opt==p.get('checkedValue')))
                if hc('checkedColor'): cb.selected_color = hc('checkedColor')
                lb = MDLabel(text=opt); lb.font_size=dp(fs)
                if p.get('bold'): lb.bold = True
                if hc('textColor'): lb.theme_text_color="Custom"; lb.text_color=hc('textColor')
                lb.bind(on_touch_down=lambda i,t,c=cb: setattr(c,'active',True) if i.collide_point(*t.pos) else None)
                r.add_widget(cb); r.add_widget(lb); wid.add_widget(r); rads.append((cb, opt))
            wrap = RadioGroupWrapper(wid, rads, grp, fs)

        elif t == 'Dropdown':
            wid = MDRaisedButton(text=p.get('text',''), pos_hint=ph, size_hint=(sh['w'],sh['h']))
            wid.font_size = dp(fs)
            wid.ripple_duration_in_fast = 0.05

            if hc('backgroundColor'): wid.md_bg_color = hc('backgroundColor')
            if hc('textColor'): wid.text_color = hc('textColor')
            if p.get('bold'): wid.font_style = 'H6'

            selection_color = hc("selectionColor", [0.2, 0.4, 0.6, 0.3])
            opts = p.get('options','').split('\n')

            def make_item(o):
                return {
                    "viewclass": "OneLineListItem",
                    "text": o,
                    "bg_color": selection_color,
                    "on_release": lambda x=o: [setattr(wid, 'text', x), menu.dismiss()]
                }

            menu = MDDropdownMenu(
                caller=wid,
                items=[make_item(o) for o in opts],
                width_mult=4
            )

            wid.bind(on_release=lambda x: menu.open())
            wrap = SelectWrapper(wid, menu, fs)


        elif t == 'Slider':
            wid = MDSlider(min=p.get('min',0), max=p.get('max',100), value=p.get('value',0), pos_hint=ph, size_hint=(sh['w'],sh['h']))
            if hc('progressColor'): wid.color_active = hc('progressColor')
            if hc('buttonColor'):
                 wid.thumb_color_active = hc('buttonColor')
                 wid.thumb_color_inactive = hc('buttonColor')
            wrap = SliderWrapper(wid, fs)

        elif t == 'ProgressBar':
            wid = MDFloatLayout(pos_hint=ph, size_hint=(sh['w'],sh['h']))
            val = p.get('value',0)
            pos_t = p.get('textPosition', 'right').lower()
            bh = {'x': 0, 'center_y': 0.5}; bs = (0.8, 0.6)
            lh = {'right': 1, 'center_y': 0.5}; ls = (0.18, 1); la = 'right'
            if pos_t == 'left': bh = {'right': 1, 'center_y': 0.5}; lh = {'x': 0, 'center_y': 0.5}; la = 'left'
            elif pos_t == 'top': lh = {'top': 1, 'center_x': 0.5}; ls = (1, 0.4); bh = {'y': 0, 'center_x': 0.5}; bs = (1, 0.5); la = 'center'
            elif pos_t == 'bottom': bh = {'top': 1, 'center_x': 0.5}; bs = (1, 0.5); lh = {'y': 0, 'center_x': 0.5}; ls = (1, 0.4); la = 'center'

            # FIX: Transparent default, explicit color only if provided
            track = MDCard(pos_hint=bh, size_hint=bs, radius=[999], elevation=0)
            track.md_bg_color = [0, 0, 0, 0]  # Always transparent, ignore trackColor entirely

            
            pb = MDProgressBar(value=val, pos_hint={'center_x':0.5,'center_y':0.5}, size_hint_x=1, type="determinate")
            if hc('progressColor'): pb.color = hc('progressColor')
            track.add_widget(pb); wid.add_widget(track)
            
            lbl = MDLabel(text=f"{int(val)}%", pos_hint=lh, size_hint=ls, halign=la, valign='center')
            lbl.font_size = dp(fs)
            if hc('textColor'): lbl.theme_text_color = "Custom"; lbl.text_color = hc('textColor')
            
            wid.add_widget(lbl)
            wrap = ProgressWrapper(wid, pb, lbl, fs)
        
        elif t == 'ToggleButton':
            w = d['width']
            h = d['height']

            wid = MDSwitch(
                active=False,
                pos_hint=ph,
                size_hint=(None,None),
                width=dp(w),
                height=dp(h)
            )

            if hc('onColor'): wid.thumb_color_active = hc('onColor')
            if hc('offColor'): wid.thumb_color_inactive = hc('offColor')

            if p.get('checked'):
                Clock.schedule_once(lambda dt: setattr(wid, 'active', True), 0)

            wrap = ToggleWrapper(wid, fs)


        elif t == 'Panel':
            cr = p.get("cornerRadius", 0)
            wid = MDCard(pos_hint=ph, size_hint=(sh['w'],sh['h']), radius=[cr])
            if hc('backgroundColor'):
                wid.md_bg_color = hc('backgroundColor')
            wrap = BaseWrapper(wid, fs)


        elif t == 'CardView':
            wid = MDCard(pos_hint=ph, size_hint=(sh['w'],sh['h']), radius=[p.get('cornerRadius',8)])
            if hc('backgroundColor'): wid.md_bg_color = hc('backgroundColor')
            if p.get('elevation'): wid.elevation = p.get('elevation') / 2
            
            if p.get('text'):
                lbl = MDLabel(text=p.get('text'), halign="center", valign="center")
                if hc('textColor'): lbl.theme_text_color="Custom"; lbl.text_color=hc('textColor')
                if p.get('bold'): lbl.bold = True
                lbl.font_size = dp(fs)
                wid.add_widget(lbl)
            wrap = BaseWrapper(wid, fs)

        elif t == 'Image':
            cr = p.get('cornerRadius', 0)
            wid = MDCard(pos_hint=ph, size_hint=(sh['w'], sh['h']), radius=[cr])
            wid.md_bg_color = (0,0,0,0) 
            if hc('backgroundColor'): wid.md_bg_color = hc('backgroundColor') 
            wid.opacity = p.get('opacity', 1.0)
            
            src = p.get('src', '')
            if src.startswith('data:image'): src = src.split(',')[-1]
            try:
                img_data = base64.b64decode(src)
                cim = CoreImage(io.BytesIO(img_data), ext="png")
                fit = p.get('fit', 'cover')
                kr = True; as_ = True
                if fit == 'fill': kr = False; as_ = True
                elif fit == 'contain': kr = True; as_ = False
                elif fit == 'cover': kr = True; as_ = True
                elif fit == 'none': kr = True; as_ = False
                img = KivyImage(texture=cim.texture, allow_stretch=as_, keep_ratio=kr)
                wid.add_widget(img)
            except:
                wid.add_widget(MDLabel(text="Image Error", halign='center'))
            wrap = BaseWrapper(wid, fs)

        if wrap:
            if 'opacity' in p: wrap.opacity(p['opacity'])
            if 'visible' in p: wrap.set_visible(p['visible'])
            if 'borderColor' in p and 'borderWidth' in p:
                wrap.border(p['borderWidth'], p['borderColor'], True)

        if wid: parent.add_widget(wid)
        return wid, wrap, cid

class AutoGUI(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.widgets = {}
        self.root_layout = MDFloatLayout()
        self.title = "AutoGUI"
        self._icon_path = None
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Gray"
        self.orig_w, self.orig_h = 800, 600

    def set_icon(self, path):
        """Sets the window icon. Works locally and in build."""
        # Use sync_to_cache to ensure the icon is available in AppData
        if hasattr(self, 'sync_to_cache'):
            path = self.sync_to_cache(path)
        
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path):
            self.icon = abs_path
            # Force update the config for the current session
            Config.set('kivy', 'window_icon', abs_path)
        else:
            print(f"[AutoGUI] Icon path not found: {abs_path}")

    def build(self):
        if self._icon_path: self.icon = self._icon_path
        Window.minimum_width = self.orig_w; Window.minimum_height = self.orig_h
        Window.bind(size=self._on_resize)
        return self.root_layout

    def _on_resize(self, i, w, h):
        sf = math.sqrt((w/self.orig_w) * (h/self.orig_h))
        for k, v in self.widgets.items(): 
            if hasattr(v, 'update_scale'): v.update_scale(sf)

    def build_gui(self, fp):
        # 1. Setup Persistent Search Path for Kivy images/fonts
        persistent_dir = get_persistent_path()
        resource_add_path(persistent_dir)
        
        # 2. Also allow Kivy to look in the internal bundle if needed
        if hasattr(sys, '_MEIPASS'):
            resource_add_path(sys._MEIPASS)

        try:
            # 3. Use the Secured Loader
            # No need to call resource_path here, load_secured_json handles it
            layout = load_secured_json(fp)
            
            cvs = layout.get('canvas', {})
            self.orig_w, self.orig_h = cvs.get('width', 800), cvs.get('height', 600)
            
            from kivy.core.window import Window
            Window.size = (self.orig_w, self.orig_h)
            
            if cvs.get('title'):
                self.title = cvs.get('title')
            
            # 4. Parse
            self.widgets = NVLibParserKivy(self.root_layout, (self.orig_w, self.orig_h)).parse(layout.get('components', []))
            
        except Exception as e:
            print(f"[AutoGUI] Load Error: {e}")

    def __getattr__(self, name):
        if name in self.widgets: return self.widgets[name]
        raise AttributeError(name)
    def enable_debugging(self, enabled): pass
    def set_background(self, c): Window.clearcolor = get_color_from_hex(c)
    def set_title(self, t): self.title = t
    def set_icon(self, p):
        if os.path.exists(p): self._icon_path = p; self.icon = p
    def run(self): super().run()
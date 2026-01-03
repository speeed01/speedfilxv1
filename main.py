
# main.py - تطبيق مشاهدة الأفلام والمسلسلات كامل
import os
import sqlite3
import hashlib
import json
import requests
from datetime import datetime
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.video import Video
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import AsyncImage
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.progressbar import ProgressBar
from kivy.uix.modalview import ModalView
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ObjectProperty
from kivy.clock import Clock
from kivy.metrics import dp
from kivymd.uix.card import MDCard
from kivymd.uix.list import MDList, OneLineListItem, TwoLineListItem, ThreeLineListItem
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.tab import MDTabsBase
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.imagelist import SmartTile
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.segmentedcontrol import MDSegmentedControl, MDSegmentedControlItem
import threading

# حجم النافذة للهاتف
Window.size = (360, 640)

# ============================================================================
# قاعدة البيانات
# ============================================================================

class Database:
    def __init__(self, db_name='movie_app.db'):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # جدول المستخدمين
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول المفضلة
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                item_type TEXT NOT NULL,
                title TEXT NOT NULL,
                poster_path TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, item_id, item_type)
            )
        ''')
        
        # جدول سجل المشاهدة
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS watch_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                item_type TEXT NOT NULL,
                season_number INTEGER,
                episode_number INTEGER,
                progress REAL DEFAULT 0,
                last_watched TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # إضافة مستخدم افتراضي إذا لم يكن موجود
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            hashed_password = hashlib.sha256("123456".encode()).hexdigest()
            cursor.execute(
                "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                ("test", hashed_password, "test@example.com")
            )
        
        self.conn.commit()
    
    def authenticate_user(self, username, password):
        cursor = self.conn.cursor()
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute(
            "SELECT id FROM users WHERE username = ? AND password = ?",
            (username, hashed_password)
        )
        user = cursor.fetchone()
        return user[0] if user else None
    
    def register_user(self, username, password, email):
        cursor = self.conn.cursor()
        try:
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            cursor.execute(
                "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                (username, hashed_password, email)
            )
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
    
    def add_to_favorites(self, user_id, item_id, item_type, title, poster_path):
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO favorites (user_id, item_id, item_type, title, poster_path)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, item_id, item_type, title, poster_path))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def remove_from_favorites(self, user_id, item_id, item_type):
        cursor = self.conn.cursor()
        cursor.execute('''
            DELETE FROM favorites 
            WHERE user_id = ? AND item_id = ? AND item_type = ?
        ''', (user_id, item_id, item_type))
        self.conn.commit()
        return cursor.rowcount > 0
    
    def get_favorites(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT item_id, item_type, title, poster_path, added_at
            FROM favorites
            WHERE user_id = ?
            ORDER BY added_at DESC
        ''', (user_id,))
        return cursor.fetchall()
    
    def is_favorite(self, user_id, item_id, item_type):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id FROM favorites
            WHERE user_id = ? AND item_id = ? AND item_type = ?
        ''', (user_id, item_id, item_type))
        return cursor.fetchone() is not None

# ============================================================================
# TMDB API Client
# ============================================================================

class TMDBClient:
    def __init__(self, api_key="9c72e6d6c8f14e7b8c7c9c6d6a8f1b9a"):  # استبدل بمفتاح API الخاص بك
        self.api_key = api_key
        self.base_url = "https://api.themoviedb.org/3"
        self.image_base_url = "https://image.tmdb.org/t/p"
        
    def _make_request(self, endpoint, params=None):
        if params is None:
            params = {}
        
        params['api_key'] = self.api_key
        params['language'] = 'ar'
        
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None
    
    def get_popular_movies(self, page=1):
        return self._make_request("movie/popular", {"page": page})
    
    def get_popular_tv_shows(self, page=1):
        return self._make_request("tv/popular", {"page": page})
    
    def get_movie_details(self, movie_id):
        return self._make_request(f"movie/{movie_id}")
    
    def get_tv_details(self, tv_id):
        return self._make_request(f"tv/{tv_id}")
    
    def search_multi(self, query, page=1):
        return self._make_request("search/multi", {"query": query, "page": page})
    
    def get_image_url(self, path, size="w500"):
        if path:
            return f"{self.image_base_url}/{size}{path}"
        return None

# ============================================================================
# مكونات واجهة المستخدم
# ============================================================================

class MovieCard(MDCard):
    item_id = NumericProperty()
    item_type = StringProperty()
    title = StringProperty()
    poster_path = StringProperty()
    overview = StringProperty()
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(120), dp(200))
        self.orientation = 'vertical'
        self.elevation = 4
        self.radius = [15,]
        
        # صورة الفيلم
        img = AsyncImage(
            source=self.get_poster_url(),
            size_hint=(1, 0.7),
            allow_stretch=True
        )
        self.add_widget(img)
        
        # العنوان
        title_label = MDLabel(
            text=self.title[:20] + "..." if len(self.title) > 20 else self.title,
            size_hint=(1, 0.3),
            halign="center",
            theme_text_color="Secondary",
            font_style="Caption"
        )
        self.add_widget(title_label)
    
    def get_poster_url(self):
        if self.poster_path:
            return f"https://image.tmdb.org/t/p/w500{self.poster_path}"
        return "https://via.placeholder.com/150x225?text=No+Image"
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            app = MDApp.get_running_app()
            app.show_item_details(self.item_id, self.item_type)
            return True
        return super().on_touch_down(touch)

class VideoPlayerModal(ModalView):
    def __init__(self, video_url, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.95, 0.8)
        self.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        self.auto_dismiss = False
        
        layout = BoxLayout(orientation='vertical')
        
        # مشغل الفيديو (باستخدام AsyncImage كبديل)
        self.video_info = MDLabel(
            text=f"مشغل الفيديو\n{video_url}",
            halign="center",
            valign="middle"
        )
        layout.add_widget(self.video_info)
        
        # عناصر التحكم
        controls = BoxLayout(size_hint_y=0.2)
        controls.add_widget(Button(text="إغلاق", on_press=lambda x: self.dismiss()))
        controls.add_widget(Button(text="تشغيل", on_press=lambda x: self.play_video()))
        layout.add_widget(controls)
        
        self.add_widget(layout)
    
    def play_video(self):
        self.video_info.text = "جاري تشغيل الفيديو..."

# ============================================================================
# الشاشات
# ============================================================================

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        layout = MDBoxLayout(
            orientation='vertical',
            padding=dp(20),
            spacing=dp(20),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        
        # العنوان
        title = MDLabel(
            text="MovieFlix",
            halign="center",
            theme_text_color="Primary",
            font_style="H3"
        )
        layout.add_widget(title)
        
        # حقل اسم المستخدم
        self.username = MDTextField(
            hint_text="اسم المستخدم",
            icon_left="account",
            size_hint_x=0.8,
            pos_hint={'center_x': 0.5}
        )
        layout.add_widget(self.username)
        
        # حقل كلمة المرور
        self.password = MDTextField(
            hint_text="كلمة المرور",
            icon_left="lock",
            password=True,
            size_hint_x=0.8,
            pos_hint={'center_x': 0.5}
        )
        layout.add_widget(self.password)
        
        # زر تسجيل الدخول
        login_btn = MDRaisedButton(
            text="تسجيل الدخول",
            size_hint_x=0.8,
            pos_hint={'center_x': 0.5},
            on_press=self.login
        )
        layout.add_widget(login_btn)
        
        # رابط التسجيل
        register_btn = MDFlatButton(
            text="إنشاء حساب جديد",
            pos_hint={'center_x': 0.5},
            on_press=self.go_to_register
        )
        layout.add_widget(register_btn)
        
        self.add_widget(layout)
    
    def login(self, instance):
        app = MDApp.get_running_app()
        username = self.username.text
        password = self.password.text
        
        if username and password:
            user_id = app.db.authenticate_user(username, password)
            if user_id:
                app.current_user_id = user_id
                app.current_username = username
                app.root.current = 'home'
                app.load_home_content()
            else:
                self.show_error("اسم المستخدم أو كلمة المرور غير صحيحة")
        else:
            self.show_error("يرجى ملء جميع الحقول")
    
    def go_to_register(self, instance):
        app = MDApp.get_running_app()
        app.show_register_dialog()
    
    def show_error(self, message):
        dialog = MDDialog(
            title="خطأ",
            text=message,
            buttons=[MDFlatButton(text="حسنا", on_release=lambda x: dialog.dismiss())]
        )
        dialog.open()

class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = None
        self.build_ui()
    
    def build_ui(self):
        self.layout = MDBoxLayout(orientation='vertical')
        
        # شريط الأدوات العلوي
        self.toolbar = MDTopAppBar(
            title="MovieFlix",
            elevation=10,
            left_action_items=[["menu", lambda x: self.open_menu()]],
            right_action_items=[
                ["magnify", lambda x: self.search()],
                ["heart", lambda x: self.show_favorites()],
                ["account", lambda x: self.show_profile()]
            ]
        )
        self.layout.add_widget(self.toolbar)
        
        # تبويبات التنقل
        self.tabs = MDTabs()
        self.layout.add_widget(self.tabs)
        
        # محتوى التبويبات
        self.build_tabs_content()
        
        self.add_widget(self.layout)
    
    def build_tabs_content(self):
        # تبويب الرئيسية
        home_tab = MDFloatLayout()
        self.home_scroll = MDScrollView()
        self.home_content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(20),
            padding=dp(20),
            size_hint_y=None
        )
        self.home_content.bind(minimum_height=self.home_content.setter('height'))
        self.home_scroll.add_widget(self.home_content)
        home_tab.add_widget(self.home_scroll)
        self.tabs.add_widget(MDFloatLayout(text="الرئيسية"))
        
        # تبويب الأفلام
        movies_tab = MDFloatLayout()
        self.movies_scroll = MDScrollView()
        self.movies_grid = MDGridLayout(
            cols=3,
            spacing=dp(10),
            padding=dp(10),
            size_hint_y=None
        )
        self.movies_grid.bind(minimum_height=self.movies_grid.setter('height'))
        self.movies_scroll.add_widget(self.movies_grid)
        movies_tab.add_widget(self.movies_scroll)
        self.tabs.add_widget(MDFloatLayout(text="الأفلام"))
        
        # تبويب المسلسلات
        tv_tab = MDFloatLayout()
        self.tv_scroll = MDScrollView()
        self.tv_grid = MDGridLayout(
            cols=3,
            spacing=dp(10),
            padding=dp(10),
            size_hint_y=None
        )
        self.tv_grid.bind(minimum_height=self.tv_grid.setter('height'))
        self.tv_scroll.add_widget(self.tv_grid)
        tv_tab.add_widget(self.tv_scroll)
        self.tabs.add_widget(MDFloatLayout(text="المسلسلات"))
        
        # تبويب المفضلة
        favorites_tab = MDFloatLayout()
        self.fav_scroll = MDScrollView()
        self.fav_grid = MDGridLayout(
            cols=3,
            spacing=dp(10),
            padding=dp(10),
            size_hint_y=None
        )
        self.fav_grid.bind(minimum_height=self.fav_grid.setter('height'))
        self.fav_scroll.add_widget(self.fav_grid)
        favorites_tab.add_widget(self.fav_scroll)
        self.tabs.add_widget(MDFloatLayout(text="المفضلة"))
    
    def open_menu(self):
        print("فتح القائمة")
    
    def search(self):
        app = MDApp.get_running_app()
        app.show_search_dialog()
    
    def show_favorites(self):
        self.tabs.switch_tab("المفضلة")
        app = MDApp.get_running_app()
        app.load_favorites()
    
    def show_profile(self):
        app = MDApp.get_running_app()
        app.show_profile_dialog()

class DetailScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = MDBoxLayout(orientation='vertical')
        
        self.toolbar = MDTopAppBar(
            title="تفاصيل",
            elevation=10,
            left_action_items=[["arrow-left", lambda x: self.go_back()]]
        )
        self.layout.add_widget(self.toolbar)
        
        self.scroll = MDScrollView()
        self.content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(20),
            padding=dp(20),
            size_hint_y=None
        )
        self.content.bind(minimum_height=self.content.setter('height'))
        self.scroll.add_widget(self.content)
        self.layout.add_widget(self.scroll)
        
        self.add_widget(self.layout)
    
    def go_back(self):
        app = MDApp.get_running_app()
        app.root.current = 'home'

# ============================================================================
# التطبيق الرئيسي
# ============================================================================

class MovieApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = Database()
        self.tmdb = TMDBClient()
        self.current_user_id = None
        self.current_username = None
        self.current_item_details = None
        self.current_item_type = None
    
    def build(self):
        self.theme_cls.primary_palette = "Red"
        self.theme_cls.theme_style = "Dark"
        
        # إنشاء مدير الشاشات
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(DetailScreen(name='detail'))
        
        return sm
    
    def on_start(self):
        # تحميل المحتوى التلقائي
        Clock.schedule_once(lambda dt: self.load_home_content(), 1)
    
    def load_home_content(self):
        if self.root.current == 'home':
            home_screen = self.root.get_screen('home')
            
            # مسح المحتوى القديم
            home_screen.home_content.clear_widgets()
            home_screen.movies_grid.clear_widgets()
            home_screen.tv_grid.clear_widgets()
            
            # تحميل الأفلام الشائعة
            self.load_popular_movies()
            
            # تحميل المسلسلات الشائعة
            self.load_popular_tv()
    
    def load_popular_movies(self):
        def load_in_thread():
            movies = self.tmdb.get_popular_movies()
            if movies and 'results' in movies:
                Clock.schedule_once(lambda dt: self.display_movies(movies['results']))
        
        threading.Thread(target=load_in_thread, daemon=True).start()
    
    def display_movies(self, movies):
        home_screen = self.root.get_screen('home')
        
        # عرض في قسم الأفلام الشائعة
        section_label = MDLabel(
            text="الأفلام الشائعة",
            halign="right",
            size_hint_y=None,
            height=dp(40),
            font_style="H6"
        )
        home_screen.home_content.add_widget(section_label)
        
        movies_grid = MDGridLayout(
            cols=3,
            spacing=dp(10),
            size_hint_y=None,
            height=dp(220)
        )
        
        for movie in movies[:6]:
            card = MovieCard(
                item_id=movie['id'],
                item_type='movie',
                title=movie.get('title', movie.get('name', '')),
                poster_path=movie.get('poster_path', ''),
                overview=movie.get('overview', '')
            )
            movies_grid.add_widget(card)
        
        home_screen.home_content.add_widget(movies_grid)
        
        # عرض في تبويب الأفلام
        for movie in movies:
            card = MovieCard(
                item_id=movie['id'],
                item_type='movie',
                title=movie.get('title', movie.get('name', '')),
                poster_path=movie.get('poster_path', ''),
                overview=movie.get('overview', '')
            )
            home_screen.movies_grid.add_widget(card)
    
    def load_popular_tv(self):
        def load_in_thread():
            tv_shows = self.tmdb.get_popular_tv_shows()
            if tv_shows and 'results' in tv_shows:
                Clock.schedule_once(lambda dt: self.display_tv_shows(tv_shows['results']))
        
        threading.Thread(target=load_in_thread, daemon=True).start()
    
    def display_tv_shows(self, tv_shows):
        home_screen = self.root.get_screen('home')
        
        # عرض في قسم المسلسلات الشائعة
        section_label = MDLabel(
            text="المسلسلات الشائعة",
            halign="right",
            size_hint_y=None,
            height=dp(40),
            font_style="H6"
        )
        home_screen.home_content.add_widget(section_label)
        
        tv_grid = MDGridLayout(
            cols=3,
            spacing=dp(10),
            size_hint_y=None,
            height=dp(220)
        )
        
        for tv in tv_shows[:6]:
            card = MovieCard(
                item_id=tv['id'],
                item_type='tv',
                title=tv.get('title', tv.get('name', '')),
                poster_path=tv.get('poster_path', ''),
                overview=tv.get('overview', '')
            )
            tv_grid.add_widget(card)
        
        home_screen.home_content.add_widget(tv_grid)
        
        # عرض في تبويب المسلسلات
        for tv in tv_shows:
            card = MovieCard(
                item_id=tv['id'],
                item_type='tv',
                title=tv.get('title', tv.get('name', '')),
                poster_path=tv.get('poster_path', ''),
                overview=tv.get('overview', '')
            )
            home_screen.tv_grid.add_widget(card)
    
    def show_item_details(self, item_id, item_type):
        def load_details():
            if item_type == 'movie':
                details = self.tmdb.get_movie_details(item_id)
            else:
                details = self.tmdb.get_tv_details(item_id)
            
            if details:
                Clock.schedule_once(lambda dt: self.display_item_details(details, item_type))
        
        threading.Thread(target=load_details, daemon=True).start()
    
    def display_item_details(self, details, item_type):
        self.current_item_details = details
        self.current_item_type = item_type
        
        detail_screen = self.root.get_screen('detail')
        detail_screen.content.clear_widgets()
        
        # صورة الفيلم/المسلسل
        if 'poster_path' in details and details['poster_path']:
            img = AsyncImage(
                source=f"https://image.tmdb.org/t/p/w500{details['poster_path']}",
                size_hint=(1, None),
                height=dp(300),
                allow_stretch=True
            )
            detail_screen.content.add_widget(img)
        
        # العنوان
        title = details.get('title', details.get('name', ''))
        title_label = MDLabel(
            text=title,
            halign="center",
            theme_text_color="Primary",
            font_style="H4",
            size_hint_y=None,
            height=dp(50)
        )
        detail_screen.content.add_widget(title_label)
        
        # التقييم
        if 'vote_average' in details:
            rating_label = MDLabel(
                text=f"التقييم: {details['vote_average']}/10",
                halign="center",
                size_hint_y=None,
                height=dp(30)
            )
            detail_screen.content.add_widget(rating_label)
        
        # النوع
        if 'genres' in details:
            genres = ", ".join([g['name'] for g in details['genres'][:3]])
            genres_label = MDLabel(
                text=f"النوع: {genres}",
                halign="center",
                size_hint_y=None,
                height=dp(30)
            )
            detail_screen.content.add_widget(genres_label)
        
        # الوصف
        if 'overview' in details:
            overview_label = MDLabel(
                text=details['overview'],
                halign="right",
                size_hint_y=None,
                height=dp(100)
            )
            detail_screen.content.add_widget(overview_label)
        
        # أزرار التحكم
        buttons_layout = MDBoxLayout(
            orientation='horizontal',
            spacing=dp(10),
            size_hint_y=None,
            height=dp(50)
        )
        
        # زر المشاهدة
        watch_btn = MDRaisedButton(
            text="مشاهدة",
            on_press=lambda x: self.watch_item()
        )
        buttons_layout.add_widget(watch_btn)
        
        # زر المفضلة
        is_fav = self.db.is_favorite(self.current_user_id, details['id'], item_type)
        fav_text = "إزالة من المفضلة" if is_fav else "إضافة إلى المفضلة"
        fav_btn = MDRaisedButton(
            text=fav_text,
            on_press=lambda x: self.toggle_favorite(details, item_type)
        )
        buttons_layout.add_widget(fav_btn)
        
        detail_screen.content.add_widget(buttons_layout)
        
        # تغيير إلى شاشة التفاصيل
        self.root.current = 'detail'
    
    def watch_item(self):
        if self.current_item_details:
            # في التطبيق الحقيقي، هنا يجب إضافة رابط الفيديو الفعلي
            video_url = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
            player = VideoPlayerModal(video_url)
            player.open()
    
    def toggle_favorite(self, item, item_type):
        if not self.current_user_id:
            return
        
        item_id = item['id']
        title = item.get('title', item.get('name', ''))
        poster_path = item.get('poster_path', '')
        
        is_fav = self.db.is_favorite(self.current_user_id, item_id, item_type)
        
        if is_fav:
            self.db.remove_from_favorites(self.current_user_id, item_id, item_type)
        else:
            self.db.add_to_favorites(self.current_user_id, item_id, item_type, title, poster_path)
        
        # إعادة تحميل التفاصيل لتحديث زر المفضلة
        self.display_item_details(item, item_type)
    
    def load_favorites(self):
        if not self.current_user_id:
            return
        
        favorites = self.db.get_favorites(self.current_user_id)
        home_screen = self.root.get_screen('home')
        home_screen.fav_grid.clear_widgets()
        
        for fav in favorites:
            item_id, item_type, title, poster_path, _ = fav
            card = MovieCard(
                item_id=item_id,
                item_type=item_type,
                title=title,
                poster_path=poster_path,
                overview=""
            )
            home_screen.fav_grid.add_widget(card)
    
    def show_register_dialog(self):
        self.dialog = MDDialog(
            title="إنشاء حساب جديد",
            type="custom",
            content_cls=MDBoxLayout(
                orientation='vertical',
                spacing=dp(10),
                size_hint_y=None,
                height=dp(200)
            ),
            buttons=[
                MDFlatButton(text="إلغاء", on_release=lambda x: self.dialog.dismiss()),
                MDRaisedButton(text="تسجيل", on_release=self.register_user)
            ]
        )
        
        # حقول التسجيل
        self.reg_username = MDTextField(hint_text="اسم المستخدم")
        self.reg_email = MDTextField(hint_text="البريد الإلكتروني")
        self.reg_password = MDTextField(hint_text="كلمة المرور", password=True)
        
        self.dialog.content_cls.add_widget(self.reg_username)
        self.dialog.content_cls.add_widget(self.reg_email)
        self.dialog.content_cls.add_widget(self.reg_password)
        
        self.dialog.open()
    
    def register_user(self, instance):
        username = self.reg_username.text
        email = self.reg_email.text
        password = self.reg_password.text
        
        if username and email and password:
            user_id = self.db.register_user(username, password, email)
            if user_id:
                self.current_user_id = user_id
                self.current_username = username
                self.dialog.dismiss()
                self.root.current = 'home'
                self.load_home_content()
            else:
                self.show_error("اسم المستخدم موجود مسبقاً")
        else:
            self.show_error("يرجى ملء جميع الحقول")
    
    def show_search_dialog(self):
        self.search_dialog = MDDialog(
            title="بحث",
            type="custom",
            content_cls=MDBoxLayout(
                orientation='vertical',
                spacing=dp(10),
                size_hint_y=None,
                height=dp(100)
            ),
            buttons=[
                MDFlatButton(text="إلغاء", on_release=lambda x: self.search_dialog.dismiss()),
                MDRaisedButton(text="بحث", on_release=self.perform_search)
            ]
        )
        
        self.search_field = MDTextField(hint_text="ابحث عن أفلام أو مسلسلات...")
        self.search_dialog.content_cls.add_widget(self.search_field)
        
        self.search_dialog.open()
    
    def perform_search(self, instance):
        query = self.search_field.text
        if query:
            def search_in_thread():
                results = self.tmdb.search_multi(query)
                if results and 'results' in results:
                    Clock.schedule_once(lambda dt: self.display_search_results(results['results']))
            
            threading.Thread(target=search_in_thread, daemon=True).start()
            self.search_dialog.dismiss()
    
    def display_search_results(self, results):
        dialog = MDDialog(
            title="نتائج البحث",
            type="custom",
            content_cls=MDBoxLayout(
                orientation='vertical',
                spacing=dp(10),
                size_hint_y=None,
                height=dp(400)
            ),
            buttons=[
                MDFlatButton(text="إغلاق", on_release=lambda x: dialog.dismiss())
            ]
        )
        
        scroll = MDScrollView()
        content = MDGridLayout(
            cols=3,
            spacing=dp(10),
            size_hint_y=None
        )
        content.bind(minimum_height=content.setter('height'))
        
        for item in results[:12]:
            media_type = item.get('media_type', 'movie')
            if media_type in ['movie', 'tv']:
                card = MovieCard(
                    item_id=item['id'],
                    item_type=media_type,
                    title=item.get('title', item.get('name', '')),
                    poster_path=item.get('poster_path', ''),
                    overview=item.get('overview', '')
                )
                content.add_widget(card)
        
        scroll.add_widget(content)
        dialog.content_cls.add_widget(scroll)
        dialog.open()
    
    def show_profile_dialog(self):
        dialog = MDDialog(
            title=f"الملف الشخصي - {self.current_username}",
            text=f"اسم المستخدم: {self.current_username}\n\nتطبيق MovieFlix\n\nإصدار 1.0.0",
            buttons=[
                MDRaisedButton(text="تسجيل الخروج", on_release=lambda x: self.logout(dialog)),
                MDFlatButton(text="إغلاق", on_release=lambda x: dialog.dismiss())
            ]
        )
        dialog.open()
    
    def logout(self, dialog):
        self.current_user_id = None
        self.current_username = None
        dialog.dismiss()
        self.root.current = 'login'
    
    def show_error(self, message):
        dialog = MDDialog(
            title="خطأ",
            text=message,
            buttons=[MDFlatButton(text="حسنا", on_release=lambda x: dialog.dismiss())]
        )
        dialog.open()

# ============================================================================
# تشغيل التطبيق
# ============================================================================

if __name__ == '__main__':
    MovieApp().run()

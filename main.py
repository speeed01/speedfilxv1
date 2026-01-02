from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import AsyncImage, Image
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.modalview import ModalView
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.network.urlrequest import UrlRequest
from kivy.properties import StringProperty, NumericProperty, ListProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.animation import Animation
import json
import requests
import webbrowser
import os


TMDB_API_KEY = "9f9c93a0d3124a3119c69e921fec2979"
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI5ZjljOTNhMGQzMTI0YTMxMTljNjllOTIxZmVjMjk3OSIsIm5iZiI6MTczNTc4MjY0Ni4wMDQzMDUsInN1YiI6IjY3NzBjZTA5ZTlmNzIxOTNhYTIwN2JjNyIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.e7ct7Igs8y-7ci9WNlOfGLK6m-8ODdaeHdpbGfs4mYc"


BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

class MovieCard(ButtonBehavior, BoxLayout):
    
    title = StringProperty('')
    year = StringProperty('')
    rating = StringProperty('')
    image_url = StringProperty('')
    movie_id = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (None, None)
        self.size = (190, 300)
        self.padding = [8, 8, 8, 8]
        self.spacing = 8
        
        
        with self.canvas.before:
            Color(0.12, 0.12, 0.12, 1)
            self.bg = RoundedRectangle(
                pos=self.pos, 
                size=self.size,
                radius=[10,]
            )
            Color(1, 0, 0, 0.3)
            self.border = RoundedRectangle(
                pos=[self.pos[0]-1, self.pos[1]-1], 
                size=[self.size[0]+2, self.size[1]+2],
                radius=[12,]
            )
        
        self.bind(pos=self.update_graphics, size=self.update_graphics)
        
        
        self.img = AsyncImage(
            source=self.image_url or "https://via.placeholder.com/190x220/222/fff?text=SpeedFlix",
            size_hint=(1, 0.65),
            allow_stretch=True,
            keep_ratio=True,
            mipmap=True
        )
        self.add_widget(self.img)
        
        
        play_overlay = Button(
            text='▶',
            size_hint=(1, 0.1),
            background_color=(1, 0, 0, 0.8),
            color=(1, 1, 1, 1),
            font_size=20,
            opacity=0
        )
        self.img.add_widget(play_overlay)
        
        
        self.title_label = Label(
            text=self.title,
            size_hint=(1, 0.15),
            color=(1, 1, 1, 1),
            font_size=15,
            bold=True,
            halign='center',
            valign='middle',
            text_size=(170, None),
            shorten=True,
            shorten_from='right'
        )
        self.title_label.bind(size=self.title_label.setter('text_size'))
        self.add_widget(self.title_label)
        
        
        info_box = BoxLayout(size_hint=(1, 0.1), spacing=10)
        
        self.rating_label = Label(
            text=f"⭐ {self.rating}" if self.rating else "⭐ --",
            size_hint=(0.5, 1),
            color=(1, 0.8, 0, 1),
            font_size=13
        )
        
        self.year_label = Label(
            text=self.year if self.year else "----",
            size_hint=(0.5, 1),
            color=(0.6, 0.6, 0.6, 1),
            font_size=13
        )
        
        info_box.add_widget(self.rating_label)
        info_box.add_widget(self.year_label)
        self.add_widget(info_box)
    
    def update_graphics(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size
        self.border.pos = [self.pos[0]-1, self.pos[1]-1]
        self.border.size = [self.size[0]+2, self.size[1]+2]
    
    def on_press(self):
        
        anim = Animation(opacity=0.7, duration=0.1) + Animation(opacity=1, duration=0.1)
        anim.start(self.img)
        
        
        app = App.get_running_app()
        app.show_movie_details(self.movie_id)

class SpeedFlixApp(App):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "SpeedFlix - مشاهدة أفلام ومسلسلات"
        
        
        try:
            if os.path.exists("icon.png"):
                self.icon = "icon.png"
            else:
                self.icon = "https://img.icons8.com/color/96/000000/netflix.png"
        except:
            self.icon = "https://img.icons8.com/color/96/000000/netflix.png"
        
        
        self.cache = {}
        self.favorites = []
    
    def build(self):
        Window.clearcolor = (0.08, 0.08, 0.08, 1)
        
        
        self.root = BoxLayout(orientation='vertical')
        
        
        header = BoxLayout(size_hint=(1, 0.12), padding=[15, 0])
        
        with header.canvas.before:
            Color(0.1, 0.1, 0.1, 1)
            Rectangle(pos=header.pos, size=header.size)
        
        
        logo_box = BoxLayout(size_hint=(0.3, 1))
        logo = Label(
            text="🎬 SPEEDFLIX",
            font_size=24,
            bold=True,
            color=(1, 0, 0, 1)
        )
        logo_box.add_widget(logo)
        
        
        search_box = BoxLayout(size_hint=(0.7, 1), spacing=10)
        
        self.search_input = TextInput(
            hint_text="🔍 ابحث عن فيلم أو مسلسل...",
            hint_text_color=(0.7, 0.7, 0.7, 1),
            multiline=False,
            size_hint=(0.8, 0.7),
            background_color=(0.2, 0.2, 0.2, 1),
            foreground_color=(1, 1, 1, 1),
            padding=[15, 10],
            font_size=16,
            write_tab=False
        )
        
        search_btn = Button(
            text="بحث",
            size_hint=(0.2, 0.7),
            background_color=(1, 0, 0, 1),
            background_normal='',
            color=(1, 1, 1, 1),
            bold=True
        )
        search_btn.bind(on_press=self.do_search)
        
        search_box.add_widget(self.search_input)
        search_box.add_widget(search_btn)
        
        header.add_widget(logo_box)
        header.add_widget(search_box)
        
        
        self.tab_container = BoxLayout(size_hint=(1, 0.08))
        
        tabs = [
            ("🎥 الأفلام", "movies"),
            ("📺 المسلسلات", "tv"),
            ("🔥 الرائجة", "trending"),
            ("⭐ المفضلة", "favorites")
        ]
        
        for tab_text, tab_id in tabs:
            tab = Button(
                text=tab_text,
                size_hint=(0.25, 1),
                background_color=(0.15, 0.15, 0.15, 1),
                background_normal='',
                color=(1, 1, 1, 1),
                font_size=14
            )
            tab.bind(on_press=lambda instance, tid=tab_id: self.switch_tab(tid))
            self.tab_container.add_widget(tab)
        
        
        self.content_area = ScrollView()
        self.content_grid = GridLayout(
            cols=2,
            spacing=20,
            padding=20,
            size_hint_y=None
        )
        self.content_grid.bind(minimum_height=self.content_grid.setter('height'))
        self.content_area.add_widget(self.content_grid)
        
        
        self.root.add_widget(header)
        self.root.add_widget(self.tab_container)
        self.root.add_widget(self.content_area)
        
        
        Clock.schedule_once(lambda dt: self.load_initial_data(), 0.5)
        
        return self.root
    
    def load_initial_data(self):
        
        self.load_trending_movies()
    
    def load_trending_movies(self):
        
        url = f"{BASE_URL}/trending/movie/week"
        
        headers = {
            'Authorization': f'Bearer {ACCESS_TOKEN}',
            'Content-Type': 'application/json;charset=utf-8'
        }
        
        params = {
            'language': 'ar-SA',
            'page': 1
        }
        
        def on_success(req, result):
            movies = result.get('results', [])[:12]
            self.display_movies(movies)
        
        def on_failure(req, error):
            
            params_with_key = {
                'api_key': TMDB_API_KEY,
                'language': 'ar-SA',
                'page': 1
            }
            UrlRequest(
                url, 
                req_params=params_with_key, 
                on_success=on_success,
                on_failure=lambda req, error: self.show_error("فشل تحميل البيانات")
            )
        
        UrlRequest(url, req_headers=headers, req_params=params, on_success=on_success, on_failure=on_failure)
    
    def display_movies(self, movies):
        
        self.content_grid.clear_widgets()
        
        if not movies:
            empty_label = Label(
                text="😞 لا توجد أفلام متاحة",
                font_size=20,
                color=(0.7, 0.7, 0.7, 1)
            )
            self.content_grid.add_widget(empty_label)
            return
        
        for movie in movies:
            card = MovieCard(
                title=movie.get('title', 'غير معروف'),
                year=movie.get('release_date', '')[:4] if movie.get('release_date') else 'N/A',
                rating=str(round(movie.get('vote_average', 0), 1)),
                image_url=f"https://image.tmdb.org/t/p/w300{movie.get('poster_path', '')}" if movie.get('poster_path') else "",
                movie_id=movie.get('id', 0)
            )
            self.content_grid.add_widget(card)
        
        
        rows = (len(movies) + 1) // 2
        self.content_grid.height = rows * 320
    
    def do_search(self, instance):
        
        query = self.search_input.text.strip()
        if len(query) < 2:
            return
        
        url = f"{BASE_URL}/search/movie"
        
        headers = {
            'Authorization': f'Bearer {ACCESS_TOKEN}',
            'Content-Type': 'application/json;charset=utf-8'
        }
        
        params = {
            'language': 'ar-SA',
            'query': query,
            'page': 1
        }
        
        def on_success(req, result):
            movies = result.get('results', [])
            self.display_movies(movies)
        
        def on_failure(req, error):
            
            params_with_key = {
                'api_key': TMDB_API_KEY,
                'language': 'ar-SA',
                'query': query,
                'page': 1
            }
            UrlRequest(
                url, 
                req_params=params_with_key, 
                on_success=on_success,
                on_failure=lambda req, error: self.show_error("فشل البحث")
            )
        
        UrlRequest(url, req_headers=headers, req_params=params, on_success=on_success, on_failure=on_failure)
    
    def switch_tab(self, tab_id):
        
        for btn in self.tab_container.children:
            if tab_id in btn.text.lower():
                btn.background_color = (1, 0, 0, 1)
            else:
                btn.background_color = (0.15, 0.15, 0.15, 1)
        
       
        if tab_id == "movies":
            self.load_trending_movies()
        elif tab_id == "favorites":
            self.show_favorites()
    
    def show_movie_details(self, movie_id):
        
        url = f"{BASE_URL}/movie/{movie_id}"
        
        headers = {
            'Authorization': f'Bearer {ACCESS_TOKEN}',
            'Content-Type': 'application/json;charset=utf-8'
        }
        
        params = {'language': 'ar-SA'}
        
        def on_success(req, result):
            
            popup = ModalView(size_hint=(0.9, 0.8), background_color=(0, 0, 0, 0.7))
            
            content = BoxLayout(orientation='vertical', padding=20, spacing=15)
            
            
            title = Label(
                text=result.get('title', ''),
                font_size=22,
                bold=True,
                color=(1, 1, 1, 1),
                size_hint=(1, 0.1)
            )
            
            
            play_btn = Button(
                text="▶️ مشاهدة الآن",
                size_hint=(1, 0.15),
                background_color=(1, 0, 0, 1),
                font_size=18,
                bold=True
            )
            play_btn.bind(on_press=lambda x: self.play_movie(movie_id))
            
            # زر الإغلاق
            close_btn = Button(
                text="إغلاق",
                size_hint=(1, 0.1),
                background_color=(0.3, 0.3, 0.3, 1)
            )
            close_btn.bind(on_press=lambda x: popup.dismiss())
            
            content.add_widget(title)
            content.add_widget(play_btn)
            content.add_widget(close_btn)
            
            popup.add_widget(content)
            popup.open()
        
        def on_failure(req, error):
            
            params_with_key = {'api_key': TMDB_API_KEY, 'language': 'ar-SA'}
            UrlRequest(
                url, 
                req_params=params_with_key, 
                on_success=on_success,
                on_failure=lambda req, error: self.show_error("فشل تحميل التفاصيل")
            )
        
        UrlRequest(url, req_headers=headers, req_params=params, on_success=on_success, on_failure=on_failure)
    
    def play_movie(self, movie_id):
        
        sources = [
            f"https://vidsrc.me/embed/movie?tmdb={movie_id}",
            f"https://2embed.org/embed/movie?tmdb={movie_id}",
            f"https://autoembed.co/movie/tmdb/{movie_id}"
        ]
        
        webbrowser.open(sources[0])  
    
    def show_favorites(self):
        
        self.content_grid.clear_widgets()
        
        if not self.favorites:
            empty_label = Label(
                text="⭐ قائمة المفضلة فارغة\nاضغط على أي فيلم لإضافته للمفضلة",
                font_size=18,
                color=(0.7, 0.7, 0.7, 1),
                halign='center'
            )
            self.content_grid.add_widget(empty_label)
    
    def show_error(self, message):
        
        error_popup = ModalView(size_hint=(0.7, 0.3))
        error_content = BoxLayout(orientation='vertical', padding=20)
        error_content.add_widget(Label(text=message, color=(1, 0, 0, 1)))
        error_popup.add_widget(error_content)
        error_popup.open()

if __name__ == '__main__':
    SpeedFlixApp().run()

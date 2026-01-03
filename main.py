from kivy.app import App
from kivy.uix.label import Label

class SpeedFlix(App):
    def build(self):
        return Label(text="SpeedFlix OK")

SpeedFlix().run()

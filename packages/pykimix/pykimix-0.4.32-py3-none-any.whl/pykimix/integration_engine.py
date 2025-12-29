# integration_engine.py
import threading
import pygame
from kivy.app import App
from kivy.clock import Clock

class IntegrationEngine:
    """
    Minimal PyKimix Integration Engine
    Mixes Pygame window and Kivy App
    """

    def __init__(self, app_class: type(App), fps: int = 60):
        if not issubclass(app_class, App):
            raise TypeError("app_class must be a subclass of kivy.app.App")
        self.app_class = app_class
        self.fps = fps
        self.kivy_app = None
        self.running = False

    def _run_kivy(self):
        self.kivy_app = self.app_class()
        self.kivy_app.run()

    def _pygame_loop(self):
        clock = pygame.time.Clock()
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.stop()
            # You can update Pygame logic here
            pygame.display.flip()
            clock.tick(self.fps)

    def run(self):
        pygame.init()
        self.running = True

        # Start Kivy in a separate thread
        kivy_thread = threading.Thread(target=self._run_kivy)
        kivy_thread.start()

        # Start Pygame loop in main thread
        self._pygame_loop()

    def stop(self):
        self.running = False
        # Stop Kivy App safely
        if self.kivy_app:
            App.get_running_app().stop()
        pygame.quit()
from manim import *
class MyScene(Scene):
    def construct(self):
        m0 = Text('Hello Manim', color='WHITE', font='Cambria Math')
        m0.move_to([0.0, 0.0, 0])
        m0.scale(3.012)

        self.play(Write(m0), run_time=1.0)
        self.wait(1)

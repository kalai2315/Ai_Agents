from manim import *

class PythagoreanTheoremScene(Scene):
    def construct(self):
        # Title
        title = Text("Pythagorean Theorem", font_size=36).to_edge(UP)
        self.add(title)

        # Define triangle sides
        a = 3
        b = 4
        c = 5

        # Create a right-angled triangle
        triangle = Polygon(
            [0, 0, 0],
            [a, 0, 0],
            [a, b, 0],
            stroke_width=2,
            stroke_color=BLUE
        )

        # Create squares on triangle sides
        square_a = Square(side_length=a).next_to(triangle, LEFT, buff=0.2)
        square_b = Square(side_length=b).next_to(triangle, UP, buff=0.2)
        square_c = Square(side_length=c).next_to(triangle, RIGHT, buff=0.2).rotate(PI/2)


        # Labels for squares
        label_a = MathTex("a^2").move_to(square_a.get_center())
        label_b = MathTex("b^2").move_to(square_b.get_center())
        label_c = MathTex("c^2").move_to(square_c.get_center())


        #Add squares and labels
        self.add(square_a, label_a, square_b, label_b, square_c, label_c, triangle)

        # Pythagorean theorem formula
        formula = MathTex("a^2 + b^2 = c^2").to_edge(DOWN)
        self.add(formula)

        # Example values for a, b, and c
        example = MathTex("3^2 + 4^2 = 5^2").next_to(formula, DOWN)
        self.add(example)

        self.wait(2)
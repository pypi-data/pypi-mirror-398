import random

import aggdraw
from PIL import Image
from lambdawaker.draw.grid.concentric_polygins import draw_concentric_polygons


def create_type_a_card_background(width=800, height=800, primary_color=(100, 100, 0, 255)):
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = aggdraw.Draw(img)

    sides = random.randint(3, 12)
    rotation_step = random.uniform(0, 15)
    spacing = random.randint(10, 50)
    color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255), random.randint(100, 255))
    thickness = random.uniform(1, 5)
    fill_opacity = random.randint(0, 100)

    draw_concentric_polygons(
        draw=draw,
        canvas_size=(width, height),
        sides=sides,
        rotation_step=rotation_step,
        spacing=spacing,
        color=color,
        thickness=thickness,
        fill_opacity=fill_opacity,
    )

    return img


if __name__ == "__main__":
    # Demo usage when executed directly
    create_type_a_card_background().show()

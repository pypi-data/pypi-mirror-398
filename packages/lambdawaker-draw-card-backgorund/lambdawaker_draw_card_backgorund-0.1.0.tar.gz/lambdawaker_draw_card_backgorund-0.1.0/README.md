lambdawaker.draw.card_backgorund

Utilities to generate card backgrounds (Type A) using concentric polygons. Built on top of Pillow and aggdraw.

Installation:
- pip install lambdawaker.draw.card_backgorund

Usage:
- from lambdawaker.draw.card_background import create_type_a_card_background
- img = create_type_a_card_background(width=800, height=800)
- img.save("card_bg.png")

Notes:
- This package imports draw_concentric_polygons from lambdawaker.draw.grid.concentric_polygins. Ensure that module is available in your environment.

License: MIT

Changelog:
- 0.1.0 — Initial release

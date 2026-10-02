from lowpoly import *

NAME = "Wooden Crate"
CATEGORY = "prop"
DESCRIPTION = "Sample asset: 1 m crate with dark frame boards and iron corner caps."


def build():
    wood = mat("Wood", "#c08a4e")
    frame = mat("WoodDark", "#7a4f2a")
    iron = mat("Iron", "#4a4d52", roughness=0.5, metallic=0.6)

    s = 1.0  # crate size
    t = 0.08  # frame board thickness
    box("Body", (s - 0.02, s - 0.02, s - 0.02), loc=(0, 0, s / 2), material=wood)

    # Frame boards along the 12 edges, slightly proud of the body.
    h = s / 2 - t / 2 + 0.01
    for x in (-h, h):
        for y in (-h, h):
            box("PostV", (t, t, s), loc=(x, y, s / 2), material=frame)
    for z in (t / 2, s - t / 2):
        for y in (-h, h):
            box("RailX", (s - 2 * t, t, t), loc=(0, y, z), material=frame)
        for x in (-h, h):
            box("RailY", (t, s - 2 * t, t), loc=(x, 0, z), material=frame)

    # Diagonal brace on the front and back faces.
    diag = (2 ** 0.5) * (s - 2 * t)
    for y in (-h, h):
        box("Brace", (diag - 0.1, t * 0.8, t), loc=(0, y, s / 2), rot=(0, 45, 0), material=frame)

    # Iron caps on the 8 corners.
    c = s / 2 - 0.04 + 0.02
    for x in (-c, c):
        for y in (-c, c):
            for z in (0.04 - 0.01, s - 0.04 + 0.01):
                box("Cap", (0.12, 0.12, 0.1), loc=(x, y, z), material=iron)

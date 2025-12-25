from enum import Enum
from typing import Tuple, List, Self, Iterable
import random as rnd
from cooptools.geometry_utils import vector_utils as vec
from cooptools import common as com

def random_rgb(r_range: Tuple[int, int] = None,
               g_range: Tuple[int, int] = None,
               b_range: Tuple[int, int] = None):
    if r_range is None:
        r_range = (0, 255)

    if g_range is None:
        g_range = (0, 255)

    if b_range is None:
        b_range = (0, 255)

    r = rnd.randint(*r_range)
    g = rnd.randint(*g_range)
    b = rnd.randint(*b_range)

    return (r, g, b)

def rgb_as_hex(rgb):
    return '#%02x%02x%02x' % rgb

class Color(Enum):
    # https: // www.colorschemer.com / rgb - color - codes /

    # LEGACY
    LIGHT_RED = 255, 204, 204
    BRIGHT_BLUE = 0, 100, 255

    # Black and White
    BLACK = 0, 0, 0
    ROSY_GRANITE = 162, 159, 159
    CHARCOAL = 75, 75, 75
    GRAY = 128, 128, 128
    GREY = 128, 128, 128
    DIM_GRAY = 105, 105, 105
    DIM_GREY = 105, 105, 105
    FLORAL_WHITE = 255, 250, 240
    SNOW = 255, 250, 250
    BRIGHT_SNOW = 247, 247, 247
    IVORY = 255, 255, 240
    WHITE = 255, 255, 255
    SLATE_GRAY = 112, 128, 144
    LIGHT_SLATE_GRAY = 119, 136, 153


    # Browns
    CHAMPAGNE_MIST = 243, 223, 196
    CAMEL = 193, 163, 129

    # Reds
    PINK_ORCHID = 235, 193, 235
    ORANGE_RED = 255, 69, 0
    TOMATO = 255, 99, 71
    LIGHT_PINK = 255, 182, 193
    PINK = 255, 192, 203
    DEEP_PINK = 255, 20, 147

    # Oranges
    CORAL = 255, 127, 80
    DARK_ORANGE = 255, 140, 0
    LIGHT_SALMON = 255, 160, 122
    ORANGE = 255, 165, 0

    LAWN_GREEN = 124, 252, 0
    CHART_REUSE = 127, 255, 0
    AQUA_MARINE = 127, 255, 212
    OLIVE = 128, 128, 0
    BLUE_VIOLET = 138, 43, 226
    DARK_RED = 139, 0, 0
    DARK_MAGENTA = 139, 0, 139
    SADDLE_BROWN = 139, 69, 19
    DARK_SEA_GREEN = 143, 188, 143
    LIGHT_GREEN = 144, 238, 144
    MEDIUM_PURPLE = 147, 112, 219
    DARK_VIOLET = 148, 0, 211
    PALE_GREEN = 152, 251, 152
    DARK_ORCHID = 153, 50, 204
    YELLOW_GREEN = 154, 205, 50
    SIENNA = 160, 82, 45
    BROWN = 165, 42, 42
    DARK_GRAY = 49, 49, 49
    DARK_GREY = 49, 49, 49
    LIGHT_BLUE = 173, 216, 230
    GREEN_YELLOW = 173, 255, 47
    PALE_TURQUOISE = 175, 238, 238
    LIGHT_STEEL_BLUE = 176, 196, 222
    POWDER_BLUE = 176, 224, 230
    FIREBRICK = 178, 34, 34
    DARK_GOLDEN_ROD = 184, 134, 11
    MEDIUM_ORCHID = 186, 85, 211
    ROSY_BROWN = 188, 143, 143
    DARK_KHAKI = 189, 183, 107
    SILVER = 192, 192, 192
    MEDIUM_VIOLET_RED = 199, 21, 133
    PERU = 205, 133, 63
    INDIAN_RED = 205, 92, 92
    CHOCOLATE = 210, 105, 30
    TAN = 210, 180, 140
    LIGHT_GRAY = 211, 211, 211
    LIGHT_GREY = 211, 211, 211
    THISTLE = 216, 191, 216
    ORCHID = 218, 112, 214
    GOLDEN_ROD = 218, 165, 32
    PALE_VIOLET_RED = 219, 112, 147
    CRIMSON = 220, 20, 60
    GAINSBORO = 220, 220, 220
    PLUM = 221, 160, 221
    BURLY_WOOD = 222, 184, 135
    LIGHT_CYAN = 224, 255, 255
    LAVENDER = 230, 230, 250
    DARK_SALMON = 233, 150, 122
    VIOLET = 238, 130, 238
    PALE_GOLDEN_ROD = 238, 232, 170
    LIGHT_CORAL = 240, 128, 128
    KHAKI = 240, 230, 140
    ALICE_BLUE = 240, 248, 255
    HONEYDEW = 240, 255, 240
    AZURE = 240, 255, 255
    SANDY_BROWN = 244, 164, 96
    WHEAT = 245, 222, 179
    BEIGE = 245, 245, 220
    WHITE_SMOKE = 245, 245, 245
    MINT_CREAM = 245, 255, 250
    GHOST_WHITE = 248, 248, 255
    MIDNIGHT_BLUE = 25, 25, 112
    SALMON = 250, 128, 114
    ANTIQUE_WHITE = 250, 235, 215
    LINEN = 250, 240, 230
    LIGHT_GOLDEN_ROD_YELLOW = 250, 250, 210
    OLD_LACE = 253, 245, 230
    RED = 255, 0, 0
    FUCHSIA = 255, 0, 255
    MAGENTA = 255, 0, 255
    HOT_PINK = 255, 105, 180

    GOLD = 255, 215, 0
    PEACH_PUFF = 255, 218, 185
    NAVAJO_WHITE = 255, 222, 173
    MOCCASIN = 255, 228, 181
    BISQUE = 255, 228, 196
    MISTY_ROSE = 255, 228, 225
    BLANCHED_ALMOND = 255, 235, 205
    PAPAYA_WHIP = 255, 239, 213
    LAVENDER_BLUSH = 255, 240, 245
    SEA_SHELL = 255, 245, 238


    # Yellows
    YELLOW = 255, 255, 0
    LIGHT_YELLOW = 255, 255, 224
    CORN_SILK = 255, 248, 220
    LEMON_CHIFFON = 255, 250, 205


    # Greens
    LIGHT_SEA_GREEN = 32, 178, 170
    FOREST_GREEN = 34, 139, 34
    SEA_GREEN = 46, 139, 87
    DARK_SLATE_GRAY = 47, 79, 79
    LIME_GREEN = 50, 205, 50
    MEDIUM_SEA_GREEN = 60, 179, 113
    DARK_OLIVE_GREEN = 85, 107, 47
    DARK_GREEN = 0, 100, 0
    GREEN = 0, 128, 0
    MEDIUM_SPRING_GREEN = 0, 250, 154
    LIME = 0, 255, 0
    SPRING_GREEN = 0, 255, 127
    BLACK_FOREST = 29, 63, 14
    EMERALD = 95, 190, 127
    OLIVE_DRAB = 107, 142, 35

    # Blues
    BLUE = 0, 0, 255
    ROYAL_BLUE = 65, 105, 225
    STEEL_BLUE = 70, 130, 180
    MEDIUM_TURQUOISE = 72, 209, 204
    DARK_SLATE_BLUE = 72, 61, 139
    INDIGO = 75, 0, 130
    TURQUOISE = 64, 224, 208
    CADET_BLUE = 95, 158, 160
    DODGER_BLUE = 30, 144, 255
    NAVY = 0, 0, 128
    DARK_BLUE = 0, 0, 139
    MEDIUM_BLUE = 0, 0, 205
    TEAL = 0, 128, 128
    DARK_CYAN = 0, 139, 139
    DEEP_SKY_BLUE = 0, 191, 255
    DARK_TURQUOISE = 0, 206, 209
    AQUA = 0, 255, 255
    CYAN = 0, 255, 255
    CORN_FLOWER_BLUE = 100, 149, 237
    MEDIUM_AQUA_MARINE = 102, 205, 170
    SLATE_BLUE = 106, 90, 205
    FRESH_SKY = 69, 168, 234
    REGAL_NAVY = 33, 61, 119
    MEDIUM_SLATE_BLUE = 123, 104, 238
    SKY_BLUE = 135, 206, 235
    LIGHT_SKY_BLUE = 135, 206, 250

    # Purples
    PALE_PURPLE = 182, 153, 203
    MAROON = 128, 0, 0
    PURPLE = 128, 0, 128


    @classmethod
    def closest_color_to_rgb(cls, rgb: Tuple):
        best_mse = None
        best_color = None
        for color in Color:
            dr = rgb[0] - color.value[0]
            dg = rgb[1] - color.value[1]
            db = rgb[2] - color.value[2]
            mse = dr * dr + dg * dg + db * db

            if mse == 0:
                return color
            elif best_mse is None or mse < best_mse:
                best_mse = mse
                best_color = color

        return best_color

    def closest_color(self):
        #TODO: Will always return itself... not ideal
        return Color.closest_color_to_rgb(self.value)

    def normalized(self):
        return tuple((1/256) * x for x in self.value)

    @classmethod
    def furthest_color(self):
        worst_mse = None
        worst_color = None
        for color in Color:
            if color == self:
                continue
            dr = self.value[0] - color.value[0]
            dg = self.value[1] - color.value[1]
            db = self.value[2] - color.value[2]
            mse = dr * dr + dg * dg + db * db

            if worst_mse is None or mse > worst_mse:
                worst_mse = mse
                worst_color = color

        return worst_color

    @classmethod
    def random(cls):
        rnd_rgb = random_rgb()
        return cls.closest_color_to_rgb(rnd_rgb)

    @classmethod
    def choice(cls,
               excluded: List = None,
               vibrancy_range: Tuple[int, int] = None):
        return rnd.choice([color for color in Color if color not in (set(excluded) if excluded is not None else set())  # Color not in one of the background used colors
                    and ((vibrancy_range[0] <= sum(color.value) <= vibrancy_range[1]) if vibrancy_range is not None else True)])  # Force towards vibrant colors

    def as_hex(self):
        return '#%02x%02x%02x' % self.value

    @classmethod
    def from_hex(cls, hex, exact: bool = False):
        value = hex.lstrip('#')
        lv = len(value)
        rgb = tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))

        closest = Color.closest_color(rgb)
        if exact and closest.value == rgb:
            return closest
        elif exact:
            return None
        else:
            return closest


    def interpolate(self, color: Self | vec.FloatVec, amt: float) -> vec.FloatVec:
        com.verify_val(val=amt,
                       gte=0,
                       lte=1.0,
                       error_msg=f"Interpolate amount must be between 0 and 1")

        tup = Color.resolve(color)
        interp = vec.interpolate(self.value, tup, amt)
        return tuple(int(x) for x in interp)

    @staticmethod
    def resolve(color: Self | vec.FloatVec):
        if type(color) == Color:
            tup = color.value
        elif issubclass(type(color), Iterable):
            tup = color
        else:
            print(type(color))
            raise NotImplementedError()

        return tup

if __name__ == "__main__":
    def test_closest():
        close = Color.closest_color((45, 45, 45))

        print(f"Color: {close}: {close.value}")


    def test_ashex():
        hex = Color.as_hex(Color.BLUE.value)
        print(hex)

    def test_fromhex():
        color = Color.from_hex(hex)
        print(color, color.value)

    def test_interp():
        print(Color.BLACK.interpolate(Color.PINK, .5))

    test_interp()
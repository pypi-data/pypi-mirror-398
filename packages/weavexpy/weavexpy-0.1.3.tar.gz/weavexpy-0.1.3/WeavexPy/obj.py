dashed = 'dashed'
dotted = 'dotted'
none = 'none'
cover = 'cover'
contain = 'contain'
no_repeat = 'no-repeat'
repeat = 'repeat'
repeat_x = 'repeat-x'
repeat_y = 'repeat-y'
relative = 'relative'
absolute = 'absolute'
fixed = 'fixed'
sticky = 'sticky'
static = 'static'
flex = 'flex'
inline = 'inline'
block_ = 'block'
inline_block = 'inline-block'
grid = 'grid'
inline_flex = 'inline-flex'
navy = 'navy'
black = 'black'
white = 'white'
red = 'red'
blue = 'blue'
green = 'green'
yellow = 'yellow'
gray = 'gray'
transparent = 'transparent'
flex_start = 'flex-start'
flex_end = 'flex-end'
space_between = 'space-between'
space_around = 'space-around'
space_evenly = 'space-evenly'
visible = 'visible'
hidden = 'hidden'
scroll = 'scroll'
auto = 'auto'
pointer = 'pointer'
no_drop = 'no-drop'
default = 'default'
move = 'move'
text_ = 'text'
inherit = 'inherit'
initial = 'initial'
unset = 'unset'
line_through = 'line-through'
overline = 'overline'
underline = 'underline'
none = 'none'
double = 'double'
solid = 'solid'
inherit = 'inherit'
initial = 'initial'
unset = 'unset'
start = 'start'
end = 'end'
top = 'top'
low = 'low'
right = 'right'
left = 'left'
center = 'center'
justify = 'justify'
collapse = 'collapse'
important = '!important'
infinite = 'infinite'
linear = 'linear'

bullet = '&#8226;'        # •
circle_small = '&#9702;'  # ◦
circle_black = '&#9679;'  # ●
circle_white = '&#9675;'  # ○
square_small = '&#9642;'  # ▪
square_black = '&#9632;'  # ■

arrow_right = '&#8594;'     # →
arrow_left = '&#8592;'      # ←
arrow_up = '&#8593;'        # ↑
arrow_down = '&#8595;'      # ↓
arrow_horiz = '&#8596;'     # ↔
arrow_vert = '&#8597;'      # ↕

arrow_double_right = '&#8658;' # ⇒
arrow_double_left = '&#8656;'  # ⇐
arrow_double_up = '&#8657;'    # ⇑
arrow_double_down = '&#8659;'  # ⇓

arrow_curve_right = '&#8614;'  # ↦
arrow_curve_left = '&#8612;'   # ↤

plus_minus = '&#177;'     # ±
divide = '&#247;'         # ÷
multiply = '&#215;'       # ×
infinity = '&#8734;'      # ∞
square_root = '&#8730;'   # √
approx = '&#8776;'        # ≈
not_equal = '&#8800;'     # ≠
less_equal = '&#8804;'    # ≤
greater_equal = '&#8805;' # ≥

dollar = '&#36;'     # $
euro = '&#8364;'     # €
pound = '&#163;'     # £
yen = '&#165;'       # ¥
cent = '&#162;'      # ¢

ampersand = '&amp;'    # &
less_than = '&lt;'     # <
greater_than = '&gt;'  # >
copyright = '&#169;'   # ©
registered = '&#174;'  # ®
trademark = '&#8482;'  # ™
Section = '&#167;'     # §
paragraph_ = '&#182;'   # ¶

menu_ico = '&#9776' # ☰

OL_1 = '1'
OL_I = 'I'
OL_i = 'i'
OL_A = 'A'
OL_a = 'a'

_blank = '_blank'
_self = '_self'
_parent = '_parent'
_top = '_top'

br = '<br>'
hr = '<hr>'

def href(link):
    link = 'index.html' if link in ['home', '/'] else link
    if link[0] == '>':
        link = f'{link.replace('>', '')}.html'
    return f'window.location.href={f"'{link}'"};'
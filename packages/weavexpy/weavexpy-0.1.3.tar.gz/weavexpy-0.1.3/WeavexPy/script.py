import inspect
from .style import style
import re

class __select__:
    def __init__(self, element):
        self.style = style().obj_sty
        self.attrs = {}
        self.id = None
        self.className = None
        self.innerText = None
        self.textContent = None
        self.innerHTML = None
        self.value = None
        self.title = None
        self.lang = None
        self.dir = None
        self.hidden = None
        self.tabIndex = None
        self.accessKey = None
        self.draggable = None
        self.contentEditable = None
        self.inputMode = None
        self.placeholder = None
        self.defaultValue = None
        self.name = None
        self.type = None
        self.href = None
        self.src = None
        self.alt = None
        self.width = None
        self.height = None
        self.maxLength = None
        self.minLength = None
        self.readOnly = None
        self.required = None
        self.checked = None
        self.selected = None
        self.disabled = None
        
    def remove(self) : pass
    class getBoundingClientRect:
        def __init__(self):
            self.rigth  = None
            self.left   = None
            self.bottom = None
            self.top    = None
        
class html:
    class Element:
        def __init__(self, tag_name): pass
        def set_attribute(self, name, value): pass
        def get_attribute(self, name): pass
        def append_child(self, child): pass
        def remove_child(self, child): pass
        def add_class(self, class_name): pass
        def remove_class(self, class_name): pass
        def toggle_class(self, class_name): pass
        def set_text(self, text): pass
        def bind_event(self, event_name, callback): pass

    # Elementos estruturais
    @staticmethod
    def HTML(**kwargs): pass
    @staticmethod
    def HEAD(**kwargs): pass
    @staticmethod
    def BODY(**kwargs): return __select__('')
    @staticmethod
    def HEADER(**kwargs): return __select__('')
    @staticmethod
    def FOOTER(**kwargs): return __select__('')
    @staticmethod
    def MAIN(**kwargs): return __select__('')
    @staticmethod
    def NAV(**kwargs): return __select__('')
    @staticmethod
    def SECTION(**kwargs): return __select__('')
    @staticmethod
    def ARTICLE(**kwargs): return __select__('')
    @staticmethod
    def ASIDE(**kwargs): return __select__('')
    @staticmethod
    def FIGURE(**kwargs): return __select__('')
    @staticmethod
    def FIGCAPTION(**kwargs): return __select__('')
    @staticmethod
    def DIV(**kwargs): return __select__('')
    @staticmethod
    def SPAN(**kwargs): return __select__('')

    # Texto e cabeçalhos
    @staticmethod
    def H1(**kwargs): return __select__('')
    @staticmethod
    def H2(**kwargs): return __select__('')
    @staticmethod
    def H3(**kwargs): return __select__('')
    @staticmethod
    def H4(**kwargs): return __select__('')
    @staticmethod
    def H5(**kwargs): return __select__('')
    @staticmethod
    def H6(**kwargs): return __select__('')
    @staticmethod
    def P(**kwargs): return __select__('')
    @staticmethod
    def BLOCKQUOTE(**kwargs): return __select__('')
    @staticmethod
    def PRE(**kwargs): return __select__('')
    @staticmethod
    def BR(**kwargs): return __select__('')
    @staticmethod
    def HR(**kwargs): return __select__('')

    # Links e mídia
    @staticmethod
    def A(**kwargs): return __select__('')
    @staticmethod
    def IMG(**kwargs): return __select__('')
    @staticmethod
    def VIDEO(**kwargs): return __select__('')
    @staticmethod
    def AUDIO(**kwargs): return __select__('')
    @staticmethod
    def IFRAME(**kwargs): return __select__('')
    @staticmethod
    def CANVAS(**kwargs): return __select__('')
    @staticmethod
    def SVG(**kwargs): return __select__('')

    # Formulários
    @staticmethod
    def FORM(**kwargs): return __select__('')
    @staticmethod
    def INPUT(**kwargs): return __select__('')
    @staticmethod
    def TEXTAREA(**kwargs): return __select__('')
    @staticmethod
    def SELECT(**kwargs): return __select__('')
    @staticmethod
    def OPTION(**kwargs): return __select__('')
    @staticmethod
    def BUTTON(**kwargs): return __select__('')
    @staticmethod
    def FIELDSET(**kwargs): return __select__('')
    @staticmethod
    def LEGEND(**kwargs): return __select__('')
    @staticmethod
    def LABEL(**kwargs): return __select__('')
    @staticmethod
    def DATALIST(**kwargs): return __select__('')
    @staticmethod
    def OUTPUT(**kwargs): return __select__('')
    @staticmethod
    def PROGRESS(**kwargs): return __select__('')
    @staticmethod
    def METER(**kwargs): return __select__('')

    # Tabelas
    @staticmethod
    def TABLE(**kwargs): return __select__('')
    @staticmethod
    def TR(**kwargs): return __select__('')
    @staticmethod
    def TD(**kwargs): return __select__('')
    @staticmethod
    def TH(**kwargs): return __select__('')
    @staticmethod
    def THEAD(**kwargs): return __select__('')
    @staticmethod
    def TBODY(**kwargs): return __select__('')
    @staticmethod
    def TFOOT(**kwargs): return __select__('')
    @staticmethod
    def CAPTION(**kwargs): return __select__('')
    @staticmethod
    def COL(**kwargs): return __select__('')
    @staticmethod
    def COLGROUP(**kwargs): return __select__('')

    # Scripts, estilos e metadados
    @staticmethod
    def SCRIPT(**kwargs): return __select__('')
    @staticmethod
    def LINK(**kwargs): return __select__('')
    @staticmethod
    def STYLE(**kwargs): return __select__('')
    @staticmethod
    def META(**kwargs): return __select__('')
    @staticmethod
    def TITLE(**kwargs): return __select__('')
    @staticmethod
    def BASE(**kwargs): return __select__('')

    # Listas
    @staticmethod
    def UL(**kwargs): return __select__('')
    @staticmethod
    def OL(**kwargs): return __select__('')
    @staticmethod
    def LI(**kwargs): return __select__('')
    @staticmethod
    def DL(**kwargs): return __select__('')
    @staticmethod
    def DT(**kwargs): return __select__('')
    @staticmethod
    def DD(**kwargs): return __select__('')

    # Elementos semânticos adicionais
    @staticmethod
    def DETAILS(**kwargs): return __select__('')
    @staticmethod
    def SUMMARY(**kwargs): return __select__('')
    @staticmethod
    def MARK(**kwargs): return __select__('')
    @staticmethod
    def TIME(**kwargs): return __select__('')
    @staticmethod
    def ABBR(**kwargs): return __select__('')
    @staticmethod
    def ADDRESS(**kwargs): return __select__('')
    @staticmethod
    def CITE(**kwargs): return __select__('')
    @staticmethod
    def CODE(**kwargs): return __select__('')
    @staticmethod
    def VAR(**kwargs): return __select__('')
    @staticmethod
    def SAMP(**kwargs): return __select__('')
    @staticmethod
    def KBD(**kwargs): return __select__('')
    @staticmethod
    def SUB(**kwargs): return __select__('')
    @staticmethod
    def SUP(**kwargs): return __select__('')
    @staticmethod
    def SMALL(**kwargs): return __select__('')
    @staticmethod
    def STRONG(**kwargs): return __select__('')
    @staticmethod
    def EM(**kwargs): return __select__('')
    @staticmethod
    def B(**kwargs): return __select__('')
    @staticmethod
    def I(**kwargs): return __select__('')
    @staticmethod
    def U(**kwargs): return __select__('')
    @staticmethod
    def S(**kwargs): return __select__('')
    @staticmethod
    def Q(**kwargs): return __select__('')
    @staticmethod
    def WBR(**kwargs): return __select__('')



class __document__:
    def __init__(self):
        self.select = __select__
        self.querySelectorAll = __select__
        self.querySelector = __select__
        self.getElementsByTagName = __select__
        self.getElementById = __select__
        self.getElementsByClassName = __select__
        self.getElementsByName = __select__
        self.getElementsByTagNameNS = __select__

class __window__:
    def __init__(self):
        self.document = __document__()
        self.history = self.__history__()
        self.location = self.__location__()
        self.fetch = self.__fetch__
        self.JSON = self.__json__
        
    class __json__:
        @staticmethod
        def stringify(dict) -> str : pass
        @staticmethod
        def parse(str) -> dict : pass
    class __fetch__:
        def __init__(self, url):
            pass
        def json(self) : return {}
        def txt(self) : return ''
        def html(self) : return ''
    
    class __history__:
        def back(self) : pass
        def forward(self) : pass
        
    class __location__:
        def reolad(self) : pass
        def href(): pass
        
    class pywebview:
        def api(): pass
    def open(self, url, target="_blank"): pass
    def set_timeout(self, func, ms, *args): pass
    def setTimeout(self, func, ms, *args): pass
    def clear_timeout(self, timer_id): pass
    def set_interval(self, func, ms, *args): pass
    def setInterval(self, func, ms, *args): pass
    def clear_interval(self, interval_id): pass
    def scroll_to(self, x, y): pass
        
window = __window__()
document = __document__()

def bind(element, event): pass



# class window:
#     @staticmethod
#     class location:
#         @staticmethod
#         def href(): pass
#     @staticmethod
#     def open(url, target='_blank'): pass
#     @staticmethod
#     def set_timeout(func, ms, *args): pass
#     @staticmethod
#     def clear_timeout(timer_id): pass
#     @staticmethod
#     def set_interval(func, ms, *args): pass
#     @staticmethod
#     def clear_interval(interval_id): pass
#     @staticmethod
#     def location(): pass
#     @staticmethod
#     def scroll_to(x, y): pass
#     @staticmethod
#     def load(seg, limt=50, func=lambda: None, cond=0, Class='', element='█'): pass

# # (. + string) obeter elementos com class ex: document.select('.class')
# # (# + string ou string) obeter elemento pelo id ex: document.select('#my_id') or document['my_id'] -> sem o '#' sem o select tmb
# # (str(form)) lista de elementos <form> ex: document.select('form')
# # (obj.class) obeter elemento de um objeto especifico e de uma class especifica ex: document.select('H1.my_title')
# # (obj[atri]) obeter elementos com um atributo ex: document.select('H1['text']')
# # # os elementos TD dentro do elemento com id #tid ex: document.delect('#tid td')


# # Name	Type	Description	R = read only
# # R/W = read + write
# # abs_left	integer	position of the element relatively to the document left border (1)	R
# # abs_top	integer	position of the element relatively to the document top border (1)	R
# # bind	method	event binding, see the section events	-
# # children	list	the element's children of type element (not text)	R
# # child_nodes	list	the element's children of any type	R
# # class_name	string	the name of the element's class (tag attribute class)	R/W
# # clear	method	elt.clear() removes all the descendants of the element	-
# # closest	method	elt.closest(tag_name) returns the first parent element of elt with the specified tag name. Raises KeyError if no element is found.	-
# # get	method	selects elements (cf access to elements)	-
# # height	integer	element height in pixels (2)	R/W
# # html	string	the HTML code inside the element	R/W
# # index	method	elt.index([selector]) returns the index (an integer) of the element among its parent's children. If selector is specified, only the elements matching the CSS selector are taken into account ; in this case, if no element matches, the method returns -1.	-
# # inside	method	elt.inside(other) tests if elt is contained inside element other	-
# # left	integer	the position of the element relatively to the left border of the first positioned parent (3)	R/W
# # parent	DOMNode instance	the element's parent (None for doc)	R
# # scrolled_left	integer	position of the element relatively to the left border of the visible part of the document (1)	L
# # scrolled_top	entier	position of the element relatively to the top border of the visible part of the document (1)	L
# # select	method	elt.select(css_selector) returns the elements matching the specified CSS selector	-
# # select_one	method	elt.select_one(css_selector) returns the elements matching the specified CSS selector, otherwise None	-
# # text	string	the text inside the element	R/W
# # top	integer	the position of the element relatively to the upper border of the first positioned parent (3)	R/W
# # width	integer	element width in pixels (2)	R/W

# # Mouse events
# # The mouse-related events (movement, pressing a button) are
# # mouseenter	A pointing device is moved onto the element that has the listener attached
# # mouseleave	a pointing device is moved off the element that has the listener attached
# # mouseover	a pointing device is moved onto the element that has the listener attached or onto one of its children
# # mouseout	a pointing device is moved off the element that has the listener attached or off one of its children
# # mousemove	a pointing device is moved over an element
# # mousedown	a pointing device button (usually a mouse) is pressed on an element
# # mouseup	a pointing device button is released over an element
# # click	a pointing device button has been pressed and released on an element
# # dblclick	a pointing device button is clicked twice on an element

# # button	indicates which button was pressed on the mouse to trigger the event
# # buttons	indicates which buttons were pressed on the mouse to trigger the event.
# # Each button that can be pressed is represented by a given number (1 : Left button, 2 : Right button, 4 : Wheel button). If more than one button is pressed, the value of the buttons is combined to produce a new number. For example, if the right button (2) and the wheel button (4) are pressed, the value is equal to 2|4, which is 6
# # x	position of the mouse relatively to the left border of the window (in pixels)
# # y	position of the mouse relatively to the upper border of the window (in pixels)
# # clientX	the X coordinate of the mouse pointer in local (DOM content) coordinates
# # clientY	the Y coordinate of the mouse pointer in local (DOM content) coordinates
# # screenX	the X coordinate of the mouse pointer in global (screen) coordinates
# # screenY	the Y coordinate of the mouse pointer in global (screen) coordinates

class element:
    def __init__(self):
        pass
    class attrs:
        def __init__(self):
            pass
        def get(self) : pass
        def keys(self) : pass
        def values(self) : pass
        def items(self) : pass


class svg:
    class element:
        def __init__(self, tag_name): pass
        def set_attribute(self, name, value): pass
        def get_attribute(self, name): pass
        def append_child(self, child): pass
        def remove_child(self, child): pass
        def bind_event(self, event_name, callback): pass

    @staticmethod
    def svg(): pass
    @staticmethod
    def circle(): pass
    @staticmethod
    def rect(): pass
    @staticmethod
    def line(): pass
    @staticmethod
    def polyline(): pass
    @staticmethod
    def polygon(): pass
    @staticmethod
    def ellipse(): pass
    @staticmethod
    def path(): pass
    @staticmethod
    def text(): pass
    @staticmethod
    def g(): pass
    @staticmethod
    def defs(): pass
    @staticmethod
    def symbol(): pass
    @staticmethod
    def use(): pass
    @staticmethod
    def image(): pass
    @staticmethod
    def clip_path(): pass
    @staticmethod
    def mask(): pass
    @staticmethod
    def linear_gradient(): pass
    @staticmethod
    def radial_gradient(): pass
    @staticmethod
    def stop(): pass
    @staticmethod
    def pattern(): pass

class EVENTS:
    def __init__(self):
        self.ctrlKey  = None   
        self.altKey   = None
        self.code     = None
        self.shiftKey = None
        self.metKey   = None
        self.clientX  = None
        self.clientY  = None
        self.x        = None
        self.y        = None
        self.pageX    = None
        self.pageY    = None
        self.screenX  = None
        self.screenY  = None
        self.button   = None
        self.buttons  = None
    class key:
        @staticmethod
        def lower() : pass
        
    def preventDefault(self) : pass
        
# def EVENTS():
#     return __e()


# # =========================================================
# # HTML elements placeholder
# # =========================================================


# # =========================================================
# # Document placeholder
# # =========================================================

# class DOCUMENT:
#     def __init__(self):
        # self.id = None
        # self.className = None
        # self.innerText = None
        # self.textContent = None
        # self.innerHTML = None
        # self.value = None
        # self.title = None
        # self.lang = None
        # self.dir = None
        # self.hidden = None
        # self.tabIndex = None
        # self.accessKey = None
        # self.draggable = None
        # self.contentEditable = None
        # self.inputMode = None
        # self.placeholder = None
        # self.defaultValue = None
        # self.name = None
        # self.type = None
        # self.href = None
        # self.src = None
        # self.alt = None
        # self.width = None
        # self.height = None
        # self.maxLength = None
        # self.minLength = None
        # self.readOnly = None
        # self.required = None
        # self.checked = None
        # self.selected = None
        # self.disabled = None

#         self.style = None               # objeto CSSStyleDeclaration
#         self.classList = None           # DOMTokenList
#         self.children = None            # HTMLCollection
#         self.childNodes = None          # NodeList
#         self.dataset = None             # DOMStringMap
#         self.attributes = None          # NamedNodeMap
#         self.parentElement = None
#         self.parentNode = None
#         self.nextSibling = None
#         self.previousSibling = None
#         self.firstChild = None
#         self.lastChild = None
#         self.shadowRoot = None
#         self.ownerDocument = None

#         # eventos e funções
#         self.onclick = None
#         self.onchange = None
#         self.oninput = None



#     def innerHTML(self) : pass
    
#     def get(self, id_): pass
    
#     def set(self, id_, value): pass
    
#     def bind(self, event, func): pass
    
#     def unbind(self, event, func): pass
    
#     def create_element(self, tag): pass
    
#     def query_selector(self, selector): pass
    
#     def query_selector_all(self, selector): pass
    
#     def append(self, element): pass
    
#     def select(self, element) : pass
    
#     def select_one(self, element) : pass
# document = DOCUMENT()
# # =========================================================
# # Bind helper
# # =========================================================
# def bind(element, event): pass


# # =========================================================
# # Browser placeholder
# # =========================================================
class browser:
    def __init__(self):
        self.document = __document__()
        self.window = __window__()
    
    # Console
    class console:
        @staticmethod
        def log(message): pass
        @staticmethod
        def warn(message): pass
        @staticmethod
        def error(message): pass
        @staticmethod
        def info(message): pass

    # Alertas e prompts

    def alert(self, message): pass

    def confirm(self, message): pass

    def prompt(self, message, default=""): pass

    class aio:
        @staticmethod
        def run(func_load) : pass
        @staticmethod
        async def sleep(seconds): pass
        @staticmethod
        async def fetch(url, method="GET", headers=None, body=None): pass

    # Timers
    class timer:
        @staticmethod
        def set_timeout(func, ms, *args): pass
        @staticmethod
        def clear_timeout(timer_id): pass
        @staticmethod
        def set_interval(func, ms, *args): pass
        @staticmethod
        def clear_interval(interval_id): pass

    # Local storage
    class local_storage:
        @staticmethod
        def set_item(key, value): pass
        @staticmethod
        def get_item(key): pass
        @staticmethod
        def remove_item(key): pass
        @staticmethod
        def clear(): pass

    # Session storage
    class session_storage:
        @staticmethod
        def set_item(key, value): pass
        @staticmethod
        def get_item(key): pass
        @staticmethod
        def remove_item(key): pass
        @staticmethod
        def clear(): pass

    # Worker
    class worker:
        @staticmethod
        def create(script): pass
        @staticmethod
        def post_message(worker, msg): pass
        @staticmethod
        def terminate(worker): pass

    # AJAX
    class ajax:
        class Ajax:
            def __init__(self): pass
            def open(self, method, url, async_=True): pass
            def send(self, data=None): pass
            def set_header(self, name, value): pass
            def bind(self, event, callback): pass
            @property
            def status(self): pass
            @property
            def text(self): pass
            @property
            def response(self): pass


class InfoDialog:
    def __init__(self, name, ifo, top, left, ok=None):
        pass
    
    def bind(self, event, func):
        pass

class asyncio:
    @staticmethod
    def sleep(time) : pass
    @staticmethod
    def run(func) : pass
    @staticmethod
    def create_task(func) : pass

# # =========================================================
# # BackScript placeholder
# # =========================================================

# import inspect
# import re

class FrontScript:
    def __init__(self, obj):
        self.object = ''
        if isinstance(obj, str):
            self.object = obj
        else:
            src = inspect.getsource(obj)
            linhas = src.splitlines()

    
            conteudo = linhas[1:]

    
            padrao_indent = re.match(r'(\s*)', conteudo[0]).group(1)


            linhas_formatadas = [
                linha[len(padrao_indent):] if linha.startswith(padrao_indent) else linha
                for linha in conteudo
            ]

            self.object = '\n'.join(linhas_formatadas)


        self.imports = '''
from browser import document, html, bind, alert, console
import asyncio
import browser
from browser import timer
from browser import ajax, aio
from browser import local_storage, session_storage, object_storage
from browser import websocket, worker
from browser import webcomponent, markdown, template, svg
from browser.widgets import dialog, menu
from browser.widgets.dialog import InfoDialog
from browser import window




class EVENTS:
    def __init__(self):
        self.ctrlKey  = None   
        self.altKey   = None
        self.code     = None
        self.shiftKey = None
        self.metKey   = None
        self.clientX  = None
        self.clientY  = None
        self.x        = None
        self.y        = None
        self.pageX    = None
        self.pageY    = None
        self.screenX  = None
        self.screenY  = None
        self.button   = None
        self.buttons  = None
    class key:
        @staticmethod
        def lower() : pass
        
    def preventDefault(self) : pass










'''

    def __str__(self):
        return f'''
<script type="text/python">
{self.imports}
{self.object}
</script>'''
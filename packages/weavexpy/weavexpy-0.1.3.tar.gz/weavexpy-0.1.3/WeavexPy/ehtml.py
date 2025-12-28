from .style import *

def __param__(param):
    PARAM = ''
    if not param == None:
        if isinstance(param, dict):
            param_names = list(param.keys())
            param_values = list(param.values())
            for i, n in enumerate(param_names):
                value = param_values[i] if not isinstance(param_values[i], str) else f'{param_values[i]}'
            n = f'{n} = ' if not n == '' else n
            PARAM += f' {n}{value}'
    return PARAM
        


class title :
    def __init__(self, title_type = 1, content = '', cls = None, id = None, name = None, param = None) :
        self.title_type = title_type
        self.content = content
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        
        
        self.param = __param__(param)


    def __str__(self): return f'<h{self.title_type} {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>{self.content}</h{self.title_type}>'

class paragraph :
    def __init__(self, content = '', cls = None, id = None, name = None, param = None) :
        self.content = content
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.param = __param__(param)
        self.s = style('line')
        self.style = self.s.obj_sty

    def __str__(self): return f'<p {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>{self.content}</p>'
    
class title_page :
    def __init__(self, content = '', cls = None, id = None, name = None, param = None) :
        self.content = content
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.param = __param__(param)
    


    def __str__(self): return f'<title {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>{self.content}</title>'
    
class legend :
    def __init__(self, content = '', cls = None, id = None, name = None, param = None) :
        self.content = content
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.param = __param__(param)


    def __str__(self): return f'<legend {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>{self.content}</legend>'

class anchor :
    def __init__(self, href='/', target='_self', content = '', cls = None, id = None, name = None, param = None) :
        self.content = content
        self.href = f' href="{href}"'
        self.target = f' target="{target}"'
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.param = __param__(param)


    def __str__(self): return f'<a {self.param}{self.href}{self.target}{self.cls}{self.id}{self.name} style={self.s.set()}>{self.content}</a>'
    
class base :
    def __init__(self, href='/', target='_self', content = '', cls = None, id = None, name = None, param = None) :
        self.content = content
        self.href = f' href="{href}"'
        self.target = f' target="{target}"'
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.param = __param__(param)


    def __str__(self): return f'<base {self.param}{self.href}{self.target}{self.cls}{self.id}{self.name} style={self.s.set()} />'
        
class label :
    def __init__(self, content = '', cls = None, id = None, name = None, For = None, param = None) :
        self.content = content
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.For = f' for="{For}"' if not For == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.param = __param__(param)


    def __str__(self): return f'<label {self.param}{self.For}{self.cls}{self.id}{self.name} style={self.s.set()}>{self.content}</label>'
    
class textarea :
    def __init__(self, content = '', cols=None, rows=None, placeholder = None, cls = None, id = None, name = None, disabled:bool= False, param=None) :
        self.content = content
        self.cols = f' cols={cols}' if not cols == None else ''
        self.rows = f' rows={rows}' if not rows == None else ''
        self.placeholder = f' placeholder="{placeholder}"' if not placeholder == None else ''
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.disabled = f' disabled' if disabled else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.param = __param__(param)


    def __str__(self): return f'<textarea {self.param}{self.cls}{self.id}{self.name}{self.cols}{self.rows}{self.placeholder} style={self.s.set()}>{self.content}</textarea>'

class option :
    def __init__(self, content = '', value = '', cls = None, id = None, name = None, param = None) :
        self.content = content
        self.value = f' value="{value}"'
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.param = __param__(param)
        self.s = style('line')
        self.style = self.s.obj_sty

    def __str__(self): return f'<option {self.value}{self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>{self.content}</option>'
        
class select:
    def __init__(self, cls = None, id = None, name = None, param = None):
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.content = []
        self.param = __param__(param)

        
    def add(self, element) : self.content.append(element)
    def __str__(self) : 
        Format = ''
        for e in self.content : Format += f'{e}\n'
        return f'<select {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>\n   {Format}\n</select>\n'

class div:
    def __init__(self, cls = None, id = None, name = None, param = None):
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.content = []
        self.param = __param__(param)

        
    def add(self, element) : self.content.append(element)
    def __str__(self) : 
        Format = ''
        for e in self.content : Format += f'{e}\n'
        return f'<div {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>\n   {Format}\n</div>\n'
    
class table:
    def __init__(self, cls = None, id = None, name = None, param = None):
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.content = []
        self.param = __param__(param)

        
    def add(self, element) : self.content.append(element)
    def __str__(self) : 
        Format = ''
        for e in self.content : Format += f'{e}\n'
        return f'<table {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>\n   {Format}\n</table>\n'
   
class thead:
    def __init__(self, cls = None, id = None, name = None, param = None):
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.content = []
        self.param = __param__(param)

        
    def add(self, element) : self.content.append(element)
    def __str__(self) : 
        Format = ''
        for e in self.content : Format += f'{e}\n'
        return f'<thead {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>\n   {Format}\n</thead>\n'
    
class tbody:
    def __init__(self, cls = None, id = None, name = None, param = None):
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.content = []
        self.param = __param__(param)

        
    def add(self, element) : self.content.append(element)
    def __str__(self) : 
        Format = ''
        for e in self.content : Format += f'{e}\n'
        return f'<tbody {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>\n   {Format}\n</tbody>\n'
    
class tr:
    def __init__(self, cls = None, id = None, name = None, param = None):
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.content = []
        self.param = __param__(param)

        
    def add(self, element) : self.content.append(element)
    def __str__(self) : 
        Format = ''
        for e in self.content : Format += f'{e}\n'
        return f'<tr {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>\n   {Format}\n</tr>\n'
    
class th :
    def __init__(self, content = '', cls = None, id = None, name = None, param = None) :
        self.content = content
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.param = __param__(param)
        self.s = style('line')
        self.style = self.s.obj_sty

    def __str__(self): return f'<th {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>{self.content}</th>'
    
class td :
    def __init__(self, content = '', cls = None, id = None, name = None, param = None) :
        self.content = content
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.param = __param__(param)
        self.s = style('line')
        self.style = self.s.obj_sty

    def __str__(self): return f'<td {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>{self.content}</td>'

class fieldset:
    def __init__(self, cls = None, id = None, name = None, param = None):
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.content = []
        self.param = __param__(param)

        
    def add(self, element) : self.content.append(element)
    def __str__(self) : 
        Format = ''
        for e in self.content : Format += f'{e}\n'
        return f'<fieldset {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>\n   {Format}\n</fieldset>\n'


class form:
    def __init__(self, method = None, action = None, cls = None, id = None, name = None, param=None):
        self.method = f' method="{method}"' if not method == None else ''
        self.action = f' action="/{action}"' if not action == None else ''
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.param = __param__(param)
        self.content = []
        
    def add(self, element) : self.content.append(element)
    def __str__(self) : 
        Format = ''
        for e in self.content : Format += f'{e}\n'
        return f'<form {self.param}{self.method}{self.action}{self.cls}{self.id}{self.name} style={self.s.set()}>\n   {Format}\n</form>'
    
class entry:
    def __init__(self, value = '', placeholder = None, type = 'text', cls = None, id = None, name = None, disabled:bool=False, param = None):
        self.value = f'value="{value}"'
        self.placeholder = f' placeholder="{placeholder}"' if not placeholder == None else ''
        self.type = f' type="{type}"' if not type == None else ''
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.disabled = f' disabled' if disabled else ''
        self.param = __param__(param)
        
    def __str__(self) : return f'<input {self.param}{self.value}{self.placeholder}{self.type}{self.cls}{self.id}{self.name}{self.disabled} style={self.s.set()}>'
    
class button:
    def __init__(self, content = '', type = 'submit', cls = None, id = None, name = None, onclick = None, disabled:bool=False, param = None):
        self.value = str(content)
        self.type = f' type="{type}"' if not type == None else ''
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.onclick = f' onclick="{onclick}"' if not onclick == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.disabled = f' disabled' if disabled else ''
        self.param = __param__(param)
        
    def __str__(self) : return f'<button {self.param}{self.onclick}{self.type}{self.cls}{self.id}{self.name}{self.disabled} style={self.s.set()}>{self.value}</button>'
    
class img:
    def __init__(self, src = '', alt = '', cls = None, id = None, name = None, param = None):
        
        self.src = f' src="{src}"'
        self.alt = f' alt="{alt}"'
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.param = __param__(param)
        self.content = []

    def add(self, element) : self.content.append(element)
    def __str__(self): return f'<img {self.param}{self.src}{self.alt}{self.cls}{self.id}{self.name} style={self.s.set()}>'
    
class audio:
    def __init__(self, src = '', alt = '', cls = None, id = None, name = None, param = None):
        
        self.src = f' src="{src}"'
        self.alt = f' alt="{alt}"'
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.param = __param__(param)
        self.content = []
        
    def add(self, element) : return self.content.append(element)

    def __str__(self): 
        Format = ''
        for e in self.content : Format += f'{e}\n'
        return f'<audio {self.param}{self.src}{self.alt}{self.cls}{self.id}{self.name} style={self.s.set()}>\n   {Format}\n</audio>'
    
class video:
    def __init__(self, src = '', alt = '', cls = None, id = None, name = None, param = None):
        
        self.src = f' src="{src}"'
        self.alt = f' alt="{alt}"'
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.param = __param__(param)
        self.content = []
        
    def add(self, element) : return self.content.append(element)

    def __str__(self): 
        Format = ''
        for e in self.content : Format += f'{e}\n'
        return f'<video {self.param}{self.src}{self.alt}{self.cls}{self.id}{self.name} style={self.s.set()}>\n   {Format}\n</video>'
    
    
class strong:
    def __init__(self, content = '', cls = None, id = None, name = None, param = None):
        self.content = content
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.param = __param__(param)
        
    def __str__(self): return f'<strong {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>{self.content}</strong>'
    
class italic:
    def __init__(self, content = '', cls = None, id = None, name = None, param = None):
        self.content = content
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.param = __param__(param)
        
    def __str__(self): return f'<em {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>{self.content}</em>'
    
    
class abbr:
    def __init__(self, content = '', title = '', cls = None, id = None, name = None, param = None):
        self.content = content
        self.title = f' title="{title}"'
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.param = __param__(param)
        
    def __str__(self): return f'<abbr {self.title}{self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>{self.content}</abbr>'
     
class delt:
    def __init__(self, content = '', cls = None, id = None, name = None, param = None):
        self.content = content
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.param = __param__(param)
        
    def __str__(self): return f'<del {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>{self.content}</del>'
    
     
class ins:
    def __init__(self, content = '', cls = None, id = None, name = None, param = None):
        self.content = content
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.param = __param__(param)
        
    def __str__(self): return f'<ins {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>{self.content}</ins>'
     
          
class small:
    def __init__(self, content = '', cls = None, id = None, name = None, param=None):
        self.content = content
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.param = __param__(param)
        
    def __str__(self): return f'<small {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>{self.content}</small>'
     
          
class sub:
    def __init__(self, content = '', cls = None, id = None, name = None, param = None):
        self.content = content
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.param = __param__(param)
        
    def __str__(self): return f'<sub {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>{self.content}</sub>'
     
     
class sup:
    def __init__(self, content = '', cls = None, id = None, name = None, param = None):
        self.content = content
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.param = __param__(param)
        
    def __str__(self): return f'<sup {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>{self.content}</sup>'
     
class blockquote:
    def __init__(self, cls = None, id = None, name = None, cite = None, param = None):
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.cite = f' cite="{cite}"' if not cite == None else ''
        self.s = style('line')
        self.param = __param__(param)
        self.style = self.s.obj_sty
        self.content = []
        
    def add(self, element) : self.content.append(element)
    def __str__(self) : 
        Format = ''
        for e in self.content : Format += f'{e}\n'
        return f'<blockquote {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>\n   {Format}\n</blockquote>\n'

class head:
    def __init__(self, cls = None, id = None, name = None, param = None):
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.content = []
        self.param = __param__(param)
        
    def add(self, element) : self.content.append(element)
    def __str__(self) : 
        Format = ''
        for e in self.content : Format += f'{e}\n'
        return f'<head {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>\n   {Format}\n</head>\n'
    
class body:
    def __init__(self, cls = None, id = None, name = None, param = None):
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.content = []
        self.param = __param__(param)
        
    def add(self, element) : self.content.append(element)
    def __str__(self) : 
        Format = ''
        for e in self.content : Format += f'{e}\n'
        return f'<body {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>\n   {Format}\n</body>\n'
    
class address:
    def __init__(self, cls = None, id = None, name = None, param = None):
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.content = []
        self.param = __param__(param)
        
    def add(self, element) : self.content.append(element)
    def __str__(self) : 
        Format = ''
        for e in self.content : Format += f'{e}\n'
        return f'<address {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>\n   {Format}\n</address>\n'
    
class article:
    def __init__(self, cls = None, id = None, name = None, param = None):
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.content = []
        self.param = __param__(param)
        
    def add(self, element) : self.content.append(element)
    def __str__(self) : 
        Format = ''
        for e in self.content : Format += f'{e}\n'
        return f'<article {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>\n   {Format}\n</article>\n'
    
class aside:
    def __init__(self, cls = None, id = None, name = None, param = None):
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.content = []
        self.param = __param__(param)
        
    def add(self, element) : self.content.append(element)
    def __str__(self) : 
        Format = ''
        for e in self.content : Format += f'{e}\n'
        return f'<aside {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>\n   {Format}\n</aside>\n'
    
class header:
    def __init__(self, cls = None, id = None, name = None, param = None):
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.content = []
        self.param = __param__(param)
        
    def add(self, element) : self.content.append(element)
    def __str__(self) : 
        Format = ''
        for e in self.content : Format += f'{e}\n'
        return f'<header {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>\n   {Format}\n</header>\n'
    
class meta:
    def __init__(self, cls = None, id = None, name = None, param = None):
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.param = __param__(param)
        self.content = []
        
    def add(self, element) : self.content.append(element)
    def __str__(self) : 
        Format = ''
        for e in self.content : Format += f'{e}\n'
        return f'<meta {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>\n   {Format}\n</meta>\n'
    
class style_block:
    def __init__(self, cls = None, id = None, name = None, param = None):
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.param = __param__(param)
        self.content = []
        
    def add(self, element) : self.content.append(element)
    def __str__(self) : 
        Format = ''
        for e in self.content : Format += f'{e}\n'
        return f'<style {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>\n   {Format}\n</style>\n'
    
class main:
    def __init__(self, cls = None, id = None, name = None, param = None):
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.content = []
        self.param = __param__(param)
        
    def add(self, element) : self.content.append(element)
    def __str__(self) : 
        Format = ''
        for e in self.content : Format += f'{e}\n'
        return f'<main {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>\n   {Format}\n</main>\n'
    
class nav:
    def __init__(self, cls = None, id = None, name = None, param = None):
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.content = []
        self.param = __param__(param)
        
    def add(self, element) : self.content.append(element)
    def __str__(self) : 
        Format = ''
        for e in self.content : Format += f'{e}\n'
        return f'<nav {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>\n   {Format}\n</nav>\n'
    
class select:
    def __init__(self, cls = None, id = None, name = None, param = None):
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.content = []
        self.param = __param__(param)
        
    def add(self, element) : self.content.append(element)
    def __str__(self) : 
        Format = ''
        for e in self.content : Format += f'{e}\n'
        return f'<select {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>\n   {Format}\n</select>\n'

class link :
    def __init__(self, href='/', rel='_self', content = '', cls = None, id = None, name = None, onload = None, onerror = None, param = None) :
        self.content = content
        self.href = f' href="{href}"'
        self.rel = f' rel="{rel}"'
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.onload = f' onload="{onload}"' if not onload == None else ''
        self.onerror = f' onerror="{onerror}"' if not onerror == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.param = __param__(param)
        
    def __str__(self): return f'<link {self.param}{self.href}{self.rel}{self.cls}{self.id}{self.name}{self.onload}{self.onerror} style={self.s.set()}>{self.content}</link>'

class dd :
    def __init__(self, content = '', cls = None, id = None, name = None, param = None) :
        self.content = content
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.param = __param__(param)

    def __str__(self): return f'<dd {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>{self.content}</dd>'
    
class dt :
    def __init__(self, content = '', cls = None, id = None, name = None, param = None) :
        self.content = content
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.param = __param__(param)

    def __str__(self): return f'<dt {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>{self.content}</dt>'
    
class dl :
    def __init__(self, content = '', cls = None, id = None, name = None, param = None) :
        self.content = content
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.param = __param__(param)

    def __str__(self): return f'<dl {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>{self.content}</dl>'

class figure:
    def __init__(self, cls = None, id = None, name = None, param = None):
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.content = []
        self.param = __param__(param)
        
    def add(self, element) : self.content.append(element)
    def __str__(self) : 
        Format = ''
        for e in self.content : Format += f'{e}\n'
        return f'<figure {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>\n   {Format}\n</figure>\n'
    
class figcaption :
    def __init__(self, content = '', cls = None, id = None, name = None, param = None) :
        self.content = content
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.param = __param__(param)

    def __str__(self): return f'<figcaption {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>{self.content}</figcaption>'

class menu:
    def __init__(self, cls = None, id = None, name = None, param = None):
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.content = []
        self.param = __param__(param)
        
    def add(self, element) : self.content.append(element)
    def __str__(self) : 
        Format = ''
        for e in self.content : Format += f'{e}\n'
        return f'<menu {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>\n   {Format}\n</menu>\n'
    
class li :
    def __init__(self, content = '', cls = None, id = None, name = None, param = None) :
        self.content = content
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.param = __param__(param)

    def __str__(self): return f'<li {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>{self.content}</li>'
    
class ol:
    def __init__(self, cls = None, id = None, name = None, type = None, start = None, param = None):
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.type = f' type="{type}"' if not type == None else ''
        self.start = f' start="{start}"' if not start == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.content = []
        self.param = __param__(param)
        
    def add(self, element) : self.content.append(element)
    def __str__(self) : 
        Format = ''
        for e in self.content : Format += f'{e}\n'
        return f'<ol {self.param}{self.type}{self.start}{self.cls}{self.id}{self.name} style={self.s.set()}>\n   {Format}\n</ol>\n'
    
class ul:
    def __init__(self, cls = None, id = None, name = None, param = None):
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.content = []
        self.param = __param__(param)
        
    def add(self, element) : self.content.append(element)
    def __str__(self) : 
        Format = ''
        for e in self.content : Format += f'{e}\n'
        return f'<ul {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>\n   {Format}\n</ul>\n'
    
class pre:
    def __init__(self, cls = None, id = None, name = None, param = None):
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.content = []
        self.param = __param__(param)
        
    def add(self, element) : self.content.append(element)
    def __str__(self) : 
        Format = ''
        for e in self.content : Format += f'{e}\n'
        return f'<pre {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>\n   {Format}\n</pre>\n'
    
class code:
    def __init__(self, cls = None, id = None, name = None, param = None):
        self.cls = f' class="{cls}"' if not cls == None else ''
        self.id = f' id="{id}"' if not id == None else ''
        self.name = f' name="{name}"' if not name == None else ''
        self.s = style('line')
        self.style = self.s.obj_sty
        self.content = []
        self.param = __param__(param)
        
    def add(self, element) : self.content.append(element)
    def __str__(self) : 
        Format = ''
        for e in self.content : Format += f'{e}\n'
        return f'<code {self.param}{self.cls}{self.id}{self.name} style={self.s.set()}>\n   {Format}\n</code>\n'

class CreateTagHtml:
    def __init__(self, tag, end = True, param = None, content = None):
        self.tag = f'{tag}'
        self.end = '' if not end else f'</{tag}>'
        self.content = '\n' if content == None else f'{content}\n'
        self.s = style('line')
        self.style = self.s.obj_sty
        
        self.param = __param__(param)
        
    def add(self, element):
        '''function add if not content == None'''
        self.content += f'{element}\n'
    def __str__(self) : return f'<{self.tag}{self.param} style={self.s.set()}>{self.content}{self.end}'
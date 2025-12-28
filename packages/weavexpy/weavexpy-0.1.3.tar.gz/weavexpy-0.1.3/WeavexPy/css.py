from .style import *
class CSS:
    def __init__(self, tag):
        self.s = style('{}')
        self.style = self.s.obj_sty
        self.tag = tag
        self.ani = False
        self.animation = self.__animation__(self)
        
    class __animation__:
        def __init__(self, parent):
            self.parent = parent
            
        def keyframes(self):
            def dec(func):
                ani_format = f'@keyframes {self.parent.tag} {{\n'
                ani = func()
                for a in ani:
                    ani_format += str(a) + '\n'
                    
                self.parent.ani = ani_format
            
            return dec
        
                
    def set(self) : 
        if not self.ani : return f'{self.tag} {self.s.set()}\n'
        else: return str(self.ani) + '\n}'
    
class FROM:
    def __init__(self):
        self.s = style('{}')
        self.style = self.s.obj_sty
        
    def __str__(self):
        return f'from {self.s.set()}'
        
class TO:
    def __init__(self):
        self.s = style('{}')
        self.style = self.s.obj_sty
    
    def __str__(self):
        return f'to {self.s.set()}'
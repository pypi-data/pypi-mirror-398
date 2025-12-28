from tkinter import messagebox
import webview
from threading import Thread



def ifo(title, message): messagebox.showinfo(title, message)
def erro(title, message): messagebox.showerror(title, message)
def warning(title, message): messagebox.showwarning(title, message)




class CreateMessage:
    def __init__(self, size):
        self.format = '''
<html>
<body>
<head>
    <meta charset="UTF-8">
    <title>Minha Janela</title>
</head>
'''
        self.size = size
        self.ok = False


    def EventCloseWindow(self):
        return 'CloseWindow()'
    
    def EventOk(self) :
        return 'Ok()'
    

    def add(self, element):
        self.format += str(element) + '\n'

    def set(self):
        self.format += '''
<script>
function CloseWindow() {
    window.pywebview.api.Close();
}

function Ok() {
    window.pywebview.api.Ok()
}


</script>
</body>
</html>
'''
        class API:
            def __init__(self, parent):
                self.parent = parent
            def Close(self):
                window.destroy()
            def Ok(self):
                self.parent.ok = True
                
        api = API(self)  
        window = webview.create_window(
            '',
            html=self.format,
            width=self.size[0],
            height=self.size[1],
            frameless=True,
            js_api=api
        )
        Thread(target=webview.start, daemon=True).start()
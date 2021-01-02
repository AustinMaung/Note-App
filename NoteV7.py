from tkinter import *
from tkinter import messagebox
from tkinter.filedialog import askopenfilename, asksaveasfilename, askdirectory
from tkinter.colorchooser import askcolor
from tkinter import ttk
from tkinter.ttk import Progressbar
from PIL import ImageGrab,ImageTk, Image
import pyautogui
import threading
import math
import os
import io
import shutil
import pickle
import configparser
import time
import uuid
from fpdf import FPDF
from PyPDF2 import PdfFileReader
import numpy
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
matplotlib.use('TkAgg')          

main = Tk()
screensize = main.winfo_screenwidth(),main.winfo_screenheight() 
windowWidth = int(0.65 * screensize[0])
windowHeight = int(0.6 * screensize[1])
lineThick = int(0.01 * (screensize[0]+screensize[1])/2)
DPI = main.winfo_fpixels('1i')
#print(DPI)
#home laptop: uFont = 13, uSpace = 2, mathSpace = 15
#study laptop: uFont = 12, uSpace = 4, mathSpace = 14
uFont = 13
uSpace = 2
mathSize = 13
boxColor = 'green'
canvasColor = 'white'
text_background = 'white'
text_color = 'black'
highlightColor = 'yellow'
lineColor = 'black'
invis = 1.0

main.title("Austin Notes")

#.ini file stuff
path = os.path.dirname(os.path.abspath(__file__))
print(path)
configPath = "Austin Notes.ini"
config = configparser.ConfigParser()
if os.path.exists(configPath):
    print('exsits')
    config.read(configPath)
    uFont = int(config.get('settings', 'font_size'))
    uSpacing = int(config.get('settings', 'spacing'))
    mathSize = int(config.get('settings', 'mathSize'))
    boxColor = config.get('settings', 'boxColor')
    canvasColor = config.get('settings', 'canvasColor')
    text_background = config.get('settings', 'text_background')
    text_color = config.get('settings', 'text_color')
    highlightColor = config.get('settings', 'highlightColor')
    invis = float(config.get('settings', 'invis'))
    windowWidth = int(float(config.get('settings', 'windowWidth')) * screensize[0])
    windowHeight = int(float(config.get('settings', 'windowHeight')) * screensize[1])
    lineThick = int(float(config.get('settings', 'lineThick')) * (screensize[0]+screensize[1])/2)
    lineColor = config.get('settings', 'lineColor')
    hideConfig = config.get('settings', 'hideConfig')
    if hideConfig == "True":
        hide = win32gui.GetForegroundWindow()
        win32gui.ShowWindow(hide , win32con.SW_HIDE)
else:
    print('nope')
    with open('Austin Notes.ini', 'w') as configfile:    # save
        config.add_section('settings')
        config.set('settings', 'invis', '1.0')
        config.set('settings', 'font_size', '13')
        config.set('settings', 'mathSize', '13')
        config.set('settings', 'spacing', '2')
        config.set('settings', 'windowWidth', '0.65')
        config.set('settings', 'windowHeight', '0.6')
        config.set('settings', 'lineThick', '0.01')
        config.set('settings', 'lineColor', 'black')
        config.set('settings', 'boxColor', 'green')
        config.set('settings', 'canvasColor', 'white')
        config.set('settings', 'text_background', 'white')
        config.set('settings', 'text_color', 'black')
        config.set('settings', 'highlightColor', 'yellow')
        config.set('settings', 'hideConfig', 'False')
        config.write(configfile)
main.attributes('-alpha', invis)
class Point():
    def __init__(self,x,y):
        self.x = x
        self.y = y

class PDF(FPDF):
    # Page footer
    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font('Arial', 'I', 8)
        # Page number
        self.cell(0, 10, 'Page ' + str(self.page_no()) + '/{nb}', 0, 0, 'C')

class CustomText(Text):
    '''
    text = CustomText()
    text.tag_configure("red", foreground="#ff0000")
    text.highlight_pattern("this should be red", "red")
    '''
    def __init__(self, *args, **kwargs):
        Text.__init__(self, *args, **kwargs)
        self.parent = None
    def highlight_pattern(self, pattern, tag, start="1.0", end="end",regexp=False):
        start = self.index(start)
        end = self.index(end)
        self.mark_set("matchStart", start)
        self.mark_set("matchEnd", start)
        self.mark_set("searchLimit", end)

        count = IntVar()
        while True:
            index = self.search(pattern, "matchEnd","searchLimit",
                                count=count, regexp=regexp)
            if index == "": break
            if count.get() == 0: break # degenerate pattern which matches zero-length strings
            self.mark_set("matchStart", index)
            self.mark_set("matchEnd", "%s+%sc" % (index, count.get()))
            self.tag_add(tag, "matchStart", "matchEnd")

class Custom_Scrollbar(Scrollbar):
    def __init__(self,parent,frame,side): #frame = object being scrolled,canvas
        super().__init__(parent)
        frame.configure(scrollregion=(0,0,int(screensize[0] * 0.98),int(screensize[1]) * 0.94)) #becareful when Scrollbar made
        self.side = side
        self.frame = frame
        self.mathlist = []
        self.begin = True
        if self.side == "right":
            frame.configure(yscrollcommand=self.set)
            self.config(command=frame.yview,width=2*lineThick)
            self.bind('<B1-Motion>',self.move)
            self.bind('<ButtonRelease-1>',self.reset)
        elif self.side == "bottom":
            frame.configure(xscrollcommand=self.set)
            self.config(command=frame.xview,width=2*lineThick)
            self.bind('<B1-Motion>',self.move)
            self.bind('<ButtonRelease-1>',self.reset)
    def move(self,event):
        main.update()
    def reset(self,event):
        main.update()
        for boxes in box_handler.box_list:
            if str(type(boxes)) == "<class '__main__.MathBox'>":
                boxes.fig_frame.draw()

class CustomImage():
    def __init__(self,array,fullscreen):
        self.name = uuid.uuid1()
        self.parent = None
        self.image = array
        self.fullscreen = fullscreen
    def __getstate__(self):
        print( "I'm being pickled")
        info = {
            "name" : self.name,
            "image" : self.image,
            "fullscreen" : self.fullscreen
        }
        return info
    def __setstate__(self, d):
        #print ("I'm being unpickled with these values:", d)
        self.__dict__ = d

class CustomLabel(Label):
    def __init__(self,parent,image): #frame = object being scrolled,canvas
        super().__init__(parent,image = image)
        self.parent = parent

            
class Box(Frame):
    def __init__(self,parent,bg=boxColor):
        self.color = bg
        super().__init__(parent,bg=self.color,cursor="target") 
        self.parent = parent
        self.name = uuid.uuid1()
        self.connected_to = []
        self.line_connects = {}
        self.line_id = canvas.create_line(0,0,0,0,width=10, fill=self.color)
        self.frame = None
        self.TLcorner = Point(-1,-1)
        self.w = -1
        self.h = -1
        self.cur_anchor = ''
        self.center = Point(-1,-1)
    def connectTo(self,box):
        if self.name not in box.line_connects and box.name not in self.line_connects: 
            #print('yo')
            self.connected_to.append(box)
            box.connected_to.append(self)
            x1 = self.TLcorner.x + self.w/2
            y1 = self.TLcorner.y + self.h/2
            x2 = box.TLcorner.x + box.w/2
            y2 = box.TLcorner.y + box.h/2
            l1 = canvas.create_line(x1,y1,x2,y2,width=10, fill=lineColor)
            l2 = canvas.create_line(x1,y1,x2,y2,width=10, fill=lineColor)
            self.line_connects[box.name] = l2
            box.line_connects[self.name] = l1
            #print(self.line_connects, box.line_connects)
    #def drawConnections(self):  #used for loading     
    def updateConnections(self): #used when redrawing lines
        for boxes in self.connected_to:
            if boxes.name in self.line_connects:
                l1 = self.line_connects[boxes.name]
                l2 = boxes.line_connects[self.name]
                x1 = self.TLcorner.x + self.w/2
                y1 = self.TLcorner.y + self.h/2
                x2 = boxes.TLcorner.x + boxes.w/2
                y2 = boxes.TLcorner.y + boxes.h/2
                canvas.coords(l1,x1,y1,x2,y2)
                canvas.coords(l2,x1,y1,x2,y2)
                #print(self.line_connects, boxes.line_connects)
    def unbindSelf(self):
        self.unbind("<Button-1>")
        self.unbind("<B1-Motion>")
        self.unbind("<ButtonRelease-1>")

class TextBox(Box):
    def __init__(self,parent,bg=boxColor):
        self.color = bg
        super().__init__(parent,bg=self.color) 
        self.text = ""
        self.highlighted_text = []
        
        self.TextArea = CustomText(self,wrap=WORD,font=("Courier", uFont),background=text_background,foreground=text_color,highlightcolor=highlightColor,tabs="1c",undo=True,autoseparators=True,maxundo=-1)
        self.TextArea.parent = self
        bindtags = self.TextArea.bindtags()
        self.TextArea.bindtags((bindtags[2], bindtags[0], bindtags[1], bindtags[3]))
        self.TextArea.bind('<Enter>',self.addSpacing)
        self.TextArea.bind('<Leave>',self.addSpacing)
    def setText(self,event):
        self.text = self.TextArea.get("1.0","end-1c")
    def addSpacing(self,stuff):
        self.TextArea.tag_configure("spacing", spacing1=uSpace)
        self.text = self.TextArea.get("1.0","end-1c")
        self.TextArea.highlight_pattern(self.text,"spacing")
    def highlightText(self):
        #spacing1=2
        self.TextArea.tag_configure("yellow", background=highlightColor)
        self.text = self.TextArea.get("1.0","end-1c")
        for highlights in self.highlighted_text:
            if highlights in self.text:
                self.TextArea.highlight_pattern(highlights,"yellow")
    def addHighlight(self,selection):
        self.highlighted_text.append(selection)
        self.TextArea.tag_configure("yellow", background=highlightColor)
        self.TextArea.highlight_pattern(selection,"yellow")
    def addTextArea(self):
        self.TextArea.place(x=lineThick,y=lineThick,width=self.w-2*lineThick,height=self.h-2*lineThick)
        self.TextArea.insert("end",self.text)
        self.TextArea.bind("<KeyRelease>",self.setText)
        self.highlightText()
    def unbindSelf(self):
        self.unbind("<Button-1>")
        self.unbind("<B1-Motion>")
        self.unbind("<ButtonRelease-1>")
        self.TextArea.unbind("<Button-1>")
        self.TextArea.unbind("<B1-Motion>")
        self.TextArea.unbind("<ButtonRelease-1>")
        self.TextArea.config(state=NORMAL)
    def __getstate__(self):
        print( "I'm being pickled")
        info = {
            "name" : self.name,
            "text" : self.text,
            "highlighted_text" : self.highlighted_text,
            "color" : self.cget("bg"),
            "connections" : [connections.name for connections in self.connected_to],
            "origin" : [(self.TLcorner.x/screensize[0]),(self.TLcorner.y/screensize[1])],
            "w" : (self.w/screensize[0]),
            "h" : (self.h/screensize[1]),
            "anchor" : self.cur_anchor
        }
        return info
    def __setstate__(self, d):
        #print ("I'm being unpickled with these values:", d)
        self.__dict__ = d

class ImageBox(Box):
    def __init__(self,parent,bg=boxColor):
        self.color = bg
        super().__init__(parent,bg=self.color) 
        self.cust_image = None
        self.img_data = None
        self.cust_image_name = ''
        self.image_label = None
    def addImage(self):
        self.img_data = Image.fromarray(self.cust_image.image)
        temp_img = self.img_data.resize((self.w-int(2.5*lineThick), self.h-int(2.5*lineThick)),Image.ANTIALIAS)
        img = ImageTk.PhotoImage(temp_img)
        self.image_label = CustomLabel(self, image = img)
        self.image_label.image = img
        self.image_label.place(x=lineThick,y=lineThick)
    def resizeImage(self,quality):
        if self.w > 0 and self.h > 0:
            self.image_label.destroy()
            img_w = self.w-int(2.5*lineThick)
            img_h = self.h-int(2.5*lineThick)
            if img_w <= 0:
                img_w = 1
            if img_h <= 0:
                img_h = 1
            if quality == 'high':
                #print('high')
                temp_img = self.img_data.resize((img_w,img_h),Image.ANTIALIAS)
            elif quality == 'low':
                #print('low')
                temp_img = self.img_data.resize((img_w,img_h),Image.NEAREST)
            img = ImageTk.PhotoImage(temp_img)
            self.image_label = CustomLabel(self, image = img)
            self.image_label.image = img
            self.image_label.place(x=lineThick,y=lineThick)
    def chooseImage(self):
        imagename = askopenfilename(title = "Select Image To Load",filetypes = (("png files","*.png*"),("jpeg files","*.jpg")))
        if imagename != None and imagename != "":
            temp_img = Image.open(imagename)
            #img = ImageTk.PhotoImage(temp_img)
            self.cust_image = CustomImage(numpy.array(temp_img),False)
            #print('hi')
            #print(self.cust_image.image)
            self.cust_image_name = self.cust_image.name
    def unbindSelf(self):
        self.unbind("<Button-1>")
        self.unbind("<B1-Motion>")
        self.unbind("<ButtonRelease-1>")
        if self.image_label != None:
            self.image_label.unbind("<Button-1>")
            self.image_label.unbind("<B1-Motion>")
            self.image_label.unbind("<ButtonRelease-1>")
    def __getstate__(self):
        print( "I'm being pickled")
        info = {
            "name" : self.name,
            "color" : self.cget("bg"),
            "connections" : [connections.name for connections in self.connected_to],
            "origin" : [(self.TLcorner.x/screensize[0]),(self.TLcorner.y/screensize[1])],
            "w" : (self.w/screensize[0]),
            "h" : (self.h/screensize[1]),
            "anchor" : self.cur_anchor,
            "image" : self.cust_image_name
        }
        return info
    def __setstate__(self, d):
        #print ("I'm being unpickled with these values:", d)
        self.__dict__ = d
class MathBox(Box):
    def __init__(self,parent,bg=boxColor):
        self.color = bg
        super().__init__(parent,bg=self.color)
        self.text_list = []
        self.text_list_orig = []
        self.select = None
        self.cursor_row = 0 #row where cursor is
        self.cursor_col = 0 #collum where cursor is
        self.change_home = False
        self.saved_text = ''
        #self.entry = Entry(self,font=14,justify='center')
        #bindtags = self.entry.bindtags()
        #self.entry.bindtags((bindtags[2], bindtags[0], bindtags[1], bindtags[3]))
        #print(str(type(self.entry)))
        self.label = Label(self)

        self.fig = matplotlib.figure.Figure(figsize=(1, 1), dpi=DPI,frameon=False)
        self.fig.set_size_inches(1,1)

        self.ax = plt.Axes(self.fig, [0., 0., 1., 1.])
        self.ax.set_axis_off()
        self.fig.add_axes(self.ax)

        self.fig_frame = FigureCanvasTkAgg(self.fig, master=self.label)
        self.fig_frame.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)
        self.fig_frame._tkcanvas.pack(side=TOP, fill=BOTH, expand=1)
        self.bindLabel()
    def labelClicked(self,event):
        if self.select == None:
            # print('hi')
            main.bind("<Key>",self.type)
            main.bind("<Return>",self.enter)
            main.bind("<BackSpace>",self.delete)
            main.bind("<space>",self.addSpace)
            main.bind("<Control_L> z",self.selectText)
            main.bind("<Control_L> c",self.copy)
            main.bind("<Control_L> v",self.paste)
            main.bind("<Up>",self.moveUp)
            main.bind("<Down>", self.moveDown)
            main.bind('<Right>',self.moveRight)
            main.bind('<Left>',self.moveLeft)
            if len(self.text_list) < 1:
                self.text_list.append("")
                self.select = 0
            else:
                self.select = 0
                self.cursor_col = 0
            for box in box_handler.box_list:
                if str(type(box)) == "<class '__main__.MathBox'>" and box != self:
                    box.select = None
                    box.drawMathText()
                elif str(type(box)) == "<class '__main__.TextBox'>" and box != self:
                    box.TextArea.config(state=DISABLED)
        else:
            # print('die')
            main.unbind("<Key>")
            main.unbind("<Return>")
            main.unbind("<BackSpace>")
            main.unbind("<space>")
            main.unbind("<Control_L> z")
            main.unbind("<Control_L> c")
            main.unbind("<Control_L> v")
            main.unbind("<Up>")
            main.unbind("<Down>")
            main.unbind('<Right>')
            main.unbind('<Left>')
            self.select = None
            for box in box_handler.box_list:
                if str(type(box)) == "<class '__main__.TextBox'>" and box != self:
                    box.TextArea.config(state=NORMAL)
        self.drawMathText()
    def selectText(self,stuff):
        if len(self.text_list) > 0:
            self.select = 0
            self.cursor_col = 0
            self.drawMathText()
    def addMathArea(self):
            self.label.place(x = lineThick,y=lineThick,width=self.w-(2*lineThick),height=self.h - (2*lineThick)) 
    def addMathText(self,text,pos=-1):
        if pos == -1:
            self.text_list.insert(len(self.text_list),text)
        else:
            self.text_list.insert(pos,text)
    def popMathText(self,pos=-1):
        if len(self.text_list) > 0:
            del self.text_list[pos]
    def clearMathText(self):
        self.text_list.clear()
    def drawMathText(self,letter="",amt=0):
        self.ax.clear()
        if len(self.text_list) <= 0:
            self.fig_frame.draw()
            return
        #CHECK FOR EMPTY FRACTION AND SQRT STUFF
        if letter == "" and self.select != None:
            for x in range(10):
                empty = self.text_list[self.select-1].find("{}")
                num = -1
                if empty == -1:
                    pos = self.select + 1
                    if pos >= len(self.text_list):
                        pos = 0
                    empty = self.text_list[pos].find("{}")
                    num = 1
                if empty != -1:
                    self.text_list[self.select+num] = self.text_list[self.select+num][:empty + 1] + 'x' + self.text_list[self.select+num][empty + 1:]
                else:
                    break
        total = 1.0
        i = (total / len(self.text_list))
        placement = 1 + (0.5/len(self.text_list))
        for count,texts in enumerate(self.text_list):
            placement -= (i)
            if count == self.select and self.select != None:                
                first = texts[:self.cursor_col-amt]+letter
                # print("firsst " + first)
                second = texts[self.cursor_col:]
                # print("second " + second)
                texts = first + "|" + second
                self.text_list[self.select] = first + second
            self.ax.text(0.5,placement,'$' + texts + '$',
            horizontalalignment='center',
            verticalalignment='center',
            fontsize=mathSize, color='black',
            transform=self.ax.transAxes)
        try:
            self.fig_frame.draw()
        except:
            print('error typing math')
            self.text_list.pop()
            # self.text_list = self.text_list_orig.copy()
            self.select = 0
            self.drawMathText()
            #messagebox.showerror(title='Error', message='incorrect syntax')
            return
    def bindLabel(self):
        self.fig_frame._tkcanvas.bind("<Double-Button-1>",self.labelClicked)
    def unbindSelf(self):
        self.unbind("<Button-1>")
        self.unbind("<B1-Motion>")
        self.unbind("<ButtonRelease-1>")
        self.fig_frame._tkcanvas.unbind('<Button-1>')
        self.fig_frame._tkcanvas.unbind("<B1-Motion>")
        self.fig_frame._tkcanvas.unbind("<ButtonRelease-1>")
        # self.fig_frame._tkcanvas.unbind("<Double-Button-1>")
    def type(self,stuff):
        if self.select != None:
            symbols = ['^','_',',','!','@','&','*','(',')','-','=','+','[',']','|',':',';','/','?','.','>','<']
            if stuff.char.isalpha() or stuff.char.isdigit() or stuff.char in symbols:
                drawn_already = False
                drawn_already = self.addText(stuff.char)
                if drawn_already:
                    return
                else:
                    self.drawMathText(letter=stuff.char)
                    self.cursor_col += 1
    def addText(self,char):
        text = self.text_list[self.select]
        mapping = {
            'a':{
                'thet':'\\theta ',
                'delt':'\\Delta ',
                'lambd':"\\lambda ",
                'omeg':'\\Omega ',
                'sigm':"\\sigma "
            },
            'e':{
                'fe':'\\phi '
            },
            'i':{
                'ch':"\\chi ",
                'p':'\\pi '
            },
            'l':{
                'integra':'\\int_{b}^{a}',
                'partia':'\\partial ',
                'nequa':"\\ne ",
                'foral':"\\forall ",
                'natura':"\\mathbb{N}",
                'rationa':"\\mathbb{Q}",
                'rea':"\\mathbb{R}"
            },
            'n':{
                'summatio':'\\sum_{b}^{a}',
                'fractio':'\\frac{a}{b}',
                'withi':"\\in ",
                'neveri':"\\notin ",
                'negatio':"\\neg ",
                'unio':"\\cap ",
                'intersectio':"\\cap "
            },
            'o':{
                'rh':"\\rho "
            },
            'q':{
                'subore':"\\subseteq "
            },
            'r':{
                'exo':"\\oplus ",
                'intege':"\\mathbb{Z}"
            },
            's':{
                'implie':"\\implies ",
                'time':'\\times '
            },
            't':{
                'limi':'\\lim_{a}',
                'sqr':'\\sqrt{a}',
                'lef':'\\leftarrow ',
                'righ':'\\rightarrow ',
                'infini':"\\infty ",
                'gradien':"\\nabla ",
                'conjuc':"\\wedge ",
                'disjuc':"\\vee ",
                'exis':"\\exists ",
                'nevex':"\\nexists ",
                'subse':"\\subset "
            },
            'u':{
                'ta':'\\tau ',
                'm':"\\mu ",
                'n': "\\nu "
            },
            'y':{
                'empt':'\\oslash '
            },
            '^':"^{a}",
            "_":"_{a}",
            '*':'\\cdot '
        }
        if char in mapping:
            potential = mapping[char]
            if type(potential) == dict:
                for key in potential:
                    typed = len(key)
                    convert = len(potential[key])
                    if text[self.cursor_col-typed:self.cursor_col] == key:
                        self.drawMathText(amt=typed,letter=potential[key])
                        self.cursor_col += (convert - typed)
                        return True
            elif type(potential) == str:
                # print(potential)
                for elem in mapping:
                    if char == elem:
                        
                        self.drawMathText(letter=mapping[elem])
                        self.cursor_col += len(mapping[elem])
                        return True
        else:
            return False
    def delete(self,stuff):
        if self.select != None and self.cursor_col > 0:
            # print(self.text_list[self.select][self.cursor_col-1])
            cursor = self.text_list[self.select][self.cursor_col-1]
            if cursor == "}" or cursor == " ":

                val = self.text_list[self.select].rfind("\\",0,self.cursor_col)
                if val == -1:
                    val = self.text_list[self.select].rfind("^",0,self.cursor_col)
                if val == -1:
                    val = self.text_list[self.select].rfind("_",0,self.cursor_col)
                sub = self.cursor_col - val
                try:
                    self.drawMathText(amt=sub)
                except:
                    val = self.text_list[self.select].rfind("\\",0,self.cursor_col)
                    sub = self.cursor_col - val + "}"
                    self.delete(1)
                    return
                self.cursor_col -= sub
                return
            elif cursor == "{":
                return
            else:
                self.drawMathText(amt=1)
                self.cursor_col -= 1
    def enter(self,stuff):
        if self.select == None:
            self.select = 0
        else:
            if len(self.text_list[self.select]) < 1:
                # print("enter")
                return
            self.select += 1
        self.cursor_col = 0
        self.text_list.insert(self.select,"")
        self.drawMathText(letter="")
    def copy(self,stuff):
        def flash():
            if self["background"] != 'red':
                self.configure(bg='red')
                self.after(300,flash)
            else:
                self.configure(bg=self.color)
                return
        flash()
        if self.select != None:
            box_handler.saved_text = self.text_list[self.select]
        
    def paste(self,stuff):
        def flash():
            if self["background"] != 'blue':
                self.configure(bg='blue')
                self.after(300,flash)
            else:
                self.configure(bg=self.color)
                return
        flash()
        if self.select != None:
            self.drawMathText(letter=box_handler.saved_text)
            self.cursor_col += len(self.saved_text)
        # threading.Thread(target=temp(self)).start()
    def addSpace(self,stuff):
        if self.select != None:
            self.drawMathText(letter="\\hspace{0.5}")
            self.cursor_col += 12
    
    def moveRight(self,stuff): 
        if self.select != None:
            text = self.text_list[self.select]
            if self.cursor_col < len(text):
                char = text[self.cursor_col]
            else:
                char = ""
            if char == "\\" or char == '^' or char == '_':
                space = text.find('}',self.cursor_col + 1)
                end = text.find("hspace",self.cursor_col)
                val1 = text.find("{",self.cursor_col) + 1
                val2 = text.find(' ',self.cursor_col) + 1
                if "hspace" not in text[self.cursor_col:space]:
                    print('none')
                    if val1 != 0 and val2 != 0:
                        if val1 < val2:
                            self.cursor_col = val1
                        else:
                            self.cursor_col = val2
                    elif val1 == 0 and val2 != 0:
                        self.cursor_col = val2
                    elif val2 == 0 and val1 != 0:
                        self.cursor_col = val1
                    else:
                        self.cursor_col +=1
                elif val1 < end or val2 < end:
                    # print('hear')
                    if val1 != 0 and val2 != 0:
                        if val1 < val2:
                            self.cursor_col = val1
                        else:
                            self.cursor_col = val2
                    elif val1 == 0 and val2 != 0 and val2 < end:
                        self.cursor_col = val2
                    elif val2 == 0 and val1 != 0 and val1 < end:
                        self.cursor_col = val1
                    else:
                        self.cursor_col = space + 1
                else:
                    # print('bro')
                    self.cursor_col = space + 1  
            else:
                val1 = text.find('{',self.cursor_col)
                val2 = text.find("^",self.cursor_col)
                val3 = text.find("_",self.cursor_col)
                if val1 == self.cursor_col + 1:
                    self.cursor_col +=2
                elif val2 == self.cursor_col + 1:
                    self.cursor_col +=3
                elif val3 == self.cursor_col + 1:
                    self.cursor_col +=3
                else:
                    self.cursor_col += 1
                    if self.cursor_col > len(text):
                        self.cursor_col = 0
            # print(self.text_list[self.select][:self.cursor_col] + "|"+self.text_list[self.select][self.cursor_col:])
            self.drawMathText()
    def moveLeft(self,stuff):
        default = ''
        if self.select != None:
            text = self.text_list[self.select]
            if self.cursor_col - 1 != -1:
                char = text[self.cursor_col - 1]
            else:
                char = ""
            if char == "}": 
                space = text.rfind("\\hspace{0.5}",0,self.cursor_col)
                start = text.rfind("\\",0,self.cursor_col)
                # print(space,start)
                if "hspace" not in text[start:self.cursor_col] or (self.cursor_col - space) != 12:
                    # print('wah')
                    self.cursor_col -= 1
                else:
                    # print('zu')
                    self.cursor_col = space
            elif char == '{' or char == " ":
                # print('ta')
                val1 = text.rfind('}',0,self.cursor_col)
                val2 = text.rfind("\\",0,self.cursor_col)
                # print(val1,val2)

                val3 = text.rfind('^',0,self.cursor_col)
                val4 = text.rfind('_',0,self.cursor_col)
                # print(val1,val2,val3,val4)
                max_val =max([val1,val2,val3,val4])
                # print(max_val)
                if text[max_val-1] == "}" and max_val - 1 != -1 and (max_val == val3 or max_val == val4):
                    max_val -= 1

                if text[max_val - 4:max_val] == "\\int" or text[max_val - 4:max_val] == "\\lim" or text[max_val - 4:max_val] == "\\sum":
                    max_val -= 4
                self.cursor_col = max_val
                # print(self.cursor_col)
            else:
                self.cursor_col -= 1
                if self.cursor_col < 0:
                    self.cursor_col = len(text)
                # print('ya')
            # print(self.text_list[self.select][:self.cursor_col] + "|"+self.text_list[self.select][self.cursor_col:])
            self.drawMathText()      
    def moveUp(self,stuff):
        if self.select != None:
            if len(self.text_list[self.select]) < 1:
                # self.text_list = self.text_list[self.select-1:] + self.text_list[self.select:]
                self.text_list.pop(self.select)
            self.select -= 1
            if self.select < 0:
                self.select = len(self.text_list) - 1
            self.cursor_col = 0
            self.drawMathText()   
        #print(self.select)
    def moveDown(self,stuff):
        if self.select != None:
            if len(self.text_list[self.select]) < 1:
                # self.text_list = self.text_list[self.select-1:] + self.text_list[self.select:]
                self.text_list.pop(self.select)
            self.select += 1
            if self.select >= len(self.text_list):
                self.select = 0
            self.cursor_col = 0
            self.drawMathText()
    def __getstate__(self):
        print( "I'm being pickled")
        info = {
            "name" : self.name,
            "color" : self.cget("bg"),
            "connections" : [connections.name for connections in self.connected_to],
            "origin" : [(self.TLcorner.x/screensize[0]),(self.TLcorner.y/screensize[1])],
            "w" : (self.w/screensize[0]),
            "h" : (self.h/screensize[1]),
            "anchor" : self.cur_anchor,
            "texts" : self.text_list.copy()
        }
        return info
    def __setstate__(self, d):
        #print ("I'm being unpickled with these values:", d)
        self.__dict__ = d
    
class BoxHandler():
    def __init__(self):
        self.box_list = []
        self.box = None
        self.frames = []
        self.outline = canvas.create_line(0,0,0,0)
        self.fullscreen = None
        self.images = []
        self.file = ''
        self.folder = ''
        self.saved_text = ''
    def makeTextBox(self):
        self.box = TextBox(canvas)
        self.box_list.append(self.box)
    def makeImageBox(self):
        self.box = ImageBox(canvas)
        self.box_list.append(self.box)
    def makeMathBox(self):
        self.box = MathBox(canvas)
        self.box_list.append(self.box)
    def makeLine(self):
        canvas.delete(self.outline)
        self.outline = canvas.create_line(0,0,0,0)
    def clickedCanvas(self,event):
        self.box.TLcorner = Point(canvas.canvasx(event.x),canvas.canvasy(event.y))
        self.tempx = self.box.TLcorner.x
        self.tempy = self.box.TLcorner.y
        # canvas.bind("B1-Motion",outlineBox)
    def outlineBox(self,event):
        def createBox(event):
            self.unbindAll()
            for box in self.box_list:
                box.unbindSelf()
            self.tempx = None
            self.tempy = None
            canvas.config(cursor='arrow')
        tempWidth = canvas.canvasx(event.x)-self.tempx
        tempHeight = canvas.canvasy(event.y)-self.tempy
        if tempWidth < 0 and tempHeight > 0:
            self.box.TLcorner = Point(canvas.canvasx(event.x),self.tempy)
        elif tempWidth < 0 and tempHeight < 0:
            self.box.TLcorner = Point(canvas.canvasx(event.x),canvas.canvasy(event.y))
        elif tempWidth > 0 and tempHeight < 0:
            self.box.TLcorner = Point(self.tempx,canvas.canvasy(event.y))
        elif tempWidth > 0 and tempHeight > 0:
            self.box.TLcorner = Point(self.tempx,self.tempy)
        self.box.w = abs(tempWidth)
        self.box.h = abs(tempHeight)
        self.box.cur_anchor = 'nw'
        self.box.frame = canvas.create_window((self.box.TLcorner.x,self.box.TLcorner.y),window = self.box,width=self.box.w,height=self.box.h,anchor=self.box.cur_anchor)
        if str(type(self.box)) == "<class '__main__.TextBox'>":
            self.box.addTextArea()
        elif str(type(self.box)) == "<class '__main__.MathBox'>":
            self.box.addMathArea()
        canvas.bind("<ButtonRelease-1>",createBox) 
    def placeImage(self,event):
        self.box.TLcorner = Point(canvas.canvasx(event.x),canvas.canvasy(event.y))
        self.box.chooseImage()
        if self.box.cust_image != None:
            temp_img = Image.fromarray(self.box.cust_image.image)
            self.box.w = int(temp_img.size[0] + (lineThick*2.5))
            self.box.h = int(temp_img.size[1] + (lineThick*2.5))
            self.box.addImage()
            self.box.frame = canvas.create_window((self.box.TLcorner.x,self.box.TLcorner.y),window = self.box,width=self.box.w,height=self.box.h,anchor='center')
            self.box.TLcorner.x = canvas.canvasx(event.x) - self.box.w/2
            self.box.TLcorner.y = canvas.canvasy(event.y) - self.box.h/2
            self.images.append(self.box.cust_image)
        else:
            self.box = None
        self.unbindAll()
        canvas.config(cursor='arrow')
    def selectBox(self,event):
        self.box = None
        if str(type(event.widget)) == "<class '__main__.CustomText'>" or str(type(event.widget)) == "<class '__main__.CustomLabel'>":
            for boxes in self.box_list:
                if event.widget.parent in self.box_list:
                    self.box = event.widget.parent
        elif str(type(event.widget)) == "<class '__main__.TextBox'>" or str(type(event.widget)) == "<class '__main__.ImageBox'>" or str(type(event.widget)) == "<class '__main__.MathBox'>":
            self.box = event.widget
            #print("bello") 
        elif str(type(event.widget)) == "<class 'tkinter.Canvas'>":
            for boxes in self.box_list:
                if event.widget.master.master in self.box_list:
                    self.box = event.widget.master.master
        elif str(type(event.widget)) == "<class 'tkinter.Entry'>":
            for boxes in self.box_list:
                if event.widget.master in self.box_list:
                    self.box = event.widget.master
        for boxes in self.box_list:
            boxes.unbindSelf()
        canvas.delete(self.box.frame)

    def moveBox(self,event):
        if self.box != None:
            def somefunction(event):
                self.unbindAll()
                for box in self.box_list:
                    box.unbindSelf()
                canvas.config(cursor='arrow') 
                self.box.cur_anchor = 'nw'
                self.box = None
            self.box.TLcorner.x = canvas.canvasx(event.x) - self.box.w/2
            self.box.TLcorner.y = canvas.canvasy(event.y) - self.box.h/2
            self.box.cur_anchor = 'center'
            self.box.updateConnections()
            self.box.frame = canvas.create_window((canvas.canvasx(event.x),canvas.canvasy(event.y)),window = self.box,width=self.box.w,height=self.box.h,anchor = self.box.cur_anchor)
            canvas.bind('<ButtonRelease-1>',somefunction)
            # for boxes in self.box_list:
            #     boxes.unbindSelf()
    
    def sidesCorners(self,event):
        def outlineUnscaled(event):
            def releaseMouse(event):
                self.unbindAll()
                for box in self.box_list:
                    box.unbindSelf()
                canvas.config(cursor='arrow')
                self.box = None
            tempWidth = canvas.canvasx(event.x)-tempx
            tempHeight = canvas.canvasy(event.y)-tempy
            if tempWidth < 0 and tempHeight > 0:
                self.box.TLcorner = Point(canvas.canvasx(event.x),tempy)
            elif tempWidth < 0 and tempHeight < 0:
                self.box.TLcorner = Point(canvas.canvasx(event.x),canvas.canvasy(event.y))
            elif tempWidth > 0 and tempHeight < 0:
                self.box.TLcorner = Point(tempx,canvas.canvasy(event.y))
            elif tempWidth > 0 and tempHeight > 0:
                self.box.TLcorner = Point(tempx,tempy)
            self.box.w = abs(tempWidth)
            self.box.h = abs(tempHeight)
            self.box.cur_anchor = 'nw'
            self.box.frame = canvas.create_window((self.box.TLcorner.x,self.box.TLcorner.y),window = self.box,width=self.box.w,height=self.box.h,anchor=self.box.cur_anchor)
            self.box.updateConnections()
            #self.TextArea.place(x=lineThick,y=lineThick,width=self.w-2*lineThick,height=self.h-2*lineThick)
            if str(type(self.box)) == "<class '__main__.TextBox'>":
                self.box.addTextArea()
            elif str(type(self.box)) == "<class '__main__.MathBox'>":
                self.box.addMathArea()
            canvas.bind("<ButtonRelease-1>",releaseMouse)
        def outlineSides(event):
            def releaseMouse(event):
                self.unbindAll()
                for box in self.box_list:
                    box.unbindSelf()
                canvas.config(cursor='arrow')
                self.box = None
            if tempx == None:
                tempWidth = 0
                tempHeight = canvas.canvasy(event.y)-tempy
                if tempHeight == 0:
                    tempHeight = 1
            elif tempy == None:
                tempWidth = canvas.canvasx(event.x)-tempx
                tempHeight = 0
                if tempWidth== 0:
                    tempWidth = 1
            if tempWidth < 0:
                self.box.TLcorner = Point(canvas.canvasx(event.x),self.box.TLcorner.y)
                tempHeight = self.box.h
            elif tempWidth > 0:
                self.box.TLcorner = Point(self.box.TLcorner.x,self.box.TLcorner.y)
                tempHeight = self.box.h
            elif tempHeight < 0:
                tempWidth = self.box.w
                self.box.TLcorner = Point(self.box.TLcorner.x,canvas.canvasy(event.y))
            elif tempHeight > 0:
                tempWidth = self.box.w
                self.box.TLcorner = Point(self.box.TLcorner.x,self.box.TLcorner.y)
            self.box.w = abs(tempWidth)
            self.box.h = abs(tempHeight)
            self.box.cur_anchor = 'nw'
            self.box.frame = canvas.create_window((self.box.TLcorner.x,self.box.TLcorner.y),window = self.box,width=self.box.w,height=self.box.h,anchor=self.box.cur_anchor)
            self.box.updateConnections()
            #self.TextArea.place(x=lineThick,y=lineThick,width=self.w-2*lineThick,height=self.h-2*lineThick)
            if str(type(self.box)) == "<class '__main__.TextBox'>":
                self.box.addTextArea()
            elif str(type(self.box)) == "<class '__main__.MathBox'>":
                self.box.addMathArea() 
            canvas.bind("<ButtonRelease-1>",releaseMouse)  
        self.box = None
        # for boxes in self.box_list:
        #     boxes.unbindSelf()
        if str(type(event.widget)) == "<class '__main__.CustomText'>":
            for boxes in self.box_list:
                if event.widget.parent in self.box_list:
                    self.box = event.widget.parent
        elif str(type(event.widget)) == "<class '__main__.TextBox'>" or str(type(event.widget)) == "<class '__main__.MathBox'>":
            self.box = event.widget
        if event.x <= lineThick and event.y <= lineThick: #TOPLEFTCORNER
            tempx = self.box.w + self.box.TLcorner.x
            tempy = self.box.h + self.box.TLcorner.y   
        elif event.x <=lineThick and event.y >= (self.box.h-lineThick): #BOTTOMLEFT CORNER
            tempx = self.box.w + self.box.TLcorner.x
            tempy = self.box.TLcorner.y
        elif event.x >= (self.box.w - lineThick) and event.y <= lineThick: #TOPRIGHT CORNER
            tempx = self.box.TLcorner.x
            tempy = self.box.h + self.box.TLcorner.y
        elif event.x >= (self.box.w - lineThick) and event.y >(self.box.h-lineThick): #BOTTOMRIGHT CORNER
            tempx = self.box.TLcorner.x
            tempy = self.box.TLcorner.y   
        else: #user clicked somewhere on the box that wasnt on the corners
            if event.x <= lineThick:
                tempx = self.box.TLcorner.x + self.box.w
                tempy = None
            elif event.x >= (self.box.w - lineThick):
                tempx = self.box.TLcorner.x
                tempy = None
            elif event.y <= lineThick:
                tempx = None
                tempy = self.box.TLcorner.y + self.box.h
            elif event.y >= (self.box.h - lineThick):
                tempx = None
                tempy = self.box.TLcorner.y
            canvas.delete(self.box.frame)
            canvas.bind("<B1-Motion>",outlineSides)
            return
        canvas.delete(self.box.frame)
        canvas.bind("<B1-Motion>",outlineUnscaled)
    def clickScale(self,event):
        def outlineScaled(event):
            tempWidth2 = tempwidth
            tempHeight2 = tempheight
            tempx2 = tempx
            tempy2 = tempy
            def releaseMouse(event):  
                self.box.resizeImage('high')
                self.unbindAll()
                for box in self.box_list:
                    box.unbindSelf()
                canvas.config(cursor='arrow')
                self.box = None
            if tempx2 == None:
                tempWidth = 0
                tempHeight = canvas.canvasy(event.y)-tempy
                tempHeight2 = abs(tempHeight) / tempHeight2
                if tempHeight == 0:
                    tempHeight = 1
            elif tempy2 == None:
                tempWidth = canvas.canvasx(event.x)-tempx
                tempHeight = 0
                tempWidth2 = abs(tempWidth) / tempWidth2
                if tempWidth== 0:
                    tempWidth = 1
            if tempWidth < 0:
                self.box.TLcorner = Point(canvas.canvasx(event.x),self.box.TLcorner.y)
                tempHeight = tempheight * tempWidth2
            elif tempWidth > 0:
                self.box.TLcorner = Point(self.box.TLcorner.x,self.box.TLcorner.y)
                tempHeight = tempheight * tempWidth2
            elif tempHeight < 0:
                tempWidth = tempwidth * tempHeight2
                self.box.TLcorner = Point(self.box.TLcorner.x,canvas.canvasy(event.y))
            elif tempHeight > 0:
                tempWidth = tempwidth * tempHeight2
                self.box.TLcorner = Point(self.box.TLcorner.x,self.box.TLcorner.y)
            self.box.w = int(abs(tempWidth))
            self.box.h = int(abs(tempHeight))
            self.box.cur_anchor = 'nw'
            self.box.frame = canvas.create_window((self.box.TLcorner.x,self.box.TLcorner.y),window = self.box,width=self.box.w,height=self.box.h,anchor=self.box.cur_anchor)
            #self.box.updateConnections()
            if str(type(self.box)) == "<class '__main__.TextBox'>":
                self.box.addTextArea()
            elif str(type(self.box)) == "<class '__main__.ImageBox'>":
                self.box.resizeImage('low')
            canvas.bind("<ButtonRelease-1>",releaseMouse)  
        self.box = None
        # for boxes in self.box_list:
        #     boxes.unbindSelf()
        if str(type(event.widget)) == "<class '__main__.CustomText'>" or str(type(event.widget)) == "<class '__main__.CustomLabel'>":
            for boxes in self.box_list:
                if event.widget.parent in self.box_list:
                    self.box = event.widget.parent
        elif str(type(event.widget)) == "<class '__main__.TextBox'>" or str(type(event.widget)) == "<class '__main__.ImageBox'>":
            self.box = event.widget
        if event.x <= lineThick:
            tempx = self.box.TLcorner.x + self.box.w
            tempy = None
        elif event.x >= (self.box.w - lineThick):
            tempx = self.box.TLcorner.x
            tempy = None
        elif event.y <= lineThick:
            tempx = None
            tempy = self.box.TLcorner.y + self.box.h
        elif event.y >= (self.box.h - lineThick):
            tempx = None
            tempy = self.box.TLcorner.y
        tempwidth =self.box.w
        tempheight = self.box.h
        canvas.delete(self.box.frame)
        canvas.bind("<B1-Motion>",outlineScaled)

    def changeBoxColor(self,event):
        if str(type(event.widget)) == "<class '__main__.CustomText'>" or str(type(event.widget)) == "<class '__main__.CustomLabel'>":
            for boxes in self.box_list:
                if event.widget.parent in self.box_list:
                    self.box = event.widget.parent
        elif str(type(event.widget)) == "<class '__main__.TextBox'>" or str(type(event.widget)) == "<class '__main__.ImageBox'>":
            self.box = event.widget
        elif str(type(event.widget)) == "<class 'tkinter.Canvas'>":
            for boxes in self.box_list:
                if event.widget.master.master in self.box_list:
                    self.box = event.widget.master.master
        elif str(type(event.widget)) == "<class 'tkinter.Entry'>":
             for boxes in self.box_list:
                if event.widget.master in self.box_list:
                    self.box = event.widget.master
        choice = askcolor(parent=canvas, title='Pick a color')
        #print(choice)
        if choice[1] != "" and choice[1] != None:
            self.box.color = choice[1]
            self.box.configure(bg = choice[1])
        else:
            for boxes in self.box_list:
                    boxes.unbindSelf()
            canvas.config(cursor = 'arrow')

    def connectBoxes(self,event):
        if str(type(event.widget)) == "<class '__main__.CustomText'>" or str(type(event.widget)) == "<class '__main__.CustomLabel'>":
            for boxes in self.box_list:
                if event.widget.parent in self.box_list:
                    chosen_box = event.widget.parent
        elif str(type(event.widget)) == "<class '__main__.TextBox'>" or str(type(event.widget)) == "<class '__main__.ImageBox'>":
            chosen_box = event.widget
        elif str(type(event.widget)) == "<class 'tkinter.Canvas'>":
            for boxes in self.box_list:
                if event.widget.master.master in self.box_list:
                    chosen_box = event.widget.master.master
        elif str(type(event.widget)) == "<class 'tkinter.Entry'>":
             for boxes in self.box_list:
                if event.widget.master in self.box_list:
                    chosen_box = event.widget.master
        if len(self.frames) < 2:
            self.frames.append(chosen_box)
        if len(self.frames) == 2:
            if self.frames[1] == self.frames[0]:
                for boxes in self.box_list:
                    boxes.unbindSelf()
                self.frames.clear()
                canvas.config(cursor = 'arrow')
                return
            self.frames[0].connectTo(self.frames[1])
            #print(self.frames[0].line_connects,self.frames[1].line_connects)
            for boxes in self.box_list:
                boxes.unbindSelf()
            self.frames.clear()
            canvas.config(cursor = 'arrow')

    def deleteBoxes(self,event):
        if str(type(event.widget)) == "<class '__main__.CustomText'>" or str(type(event.widget)) == "<class '__main__.CustomLabel'>":
            for boxes in self.box_list:
                if event.widget.parent in self.box_list:
                    self.box = event.widget.parent
        elif str(type(event.widget)) == "<class '__main__.TextBox'>" or str(type(event.widget)) == "<class '__main__.ImageBox'>":
            self.box = event.widget
        elif str(type(event.widget)) == "<class 'tkinter.Canvas'>":
            for boxes in self.box_list:
                if event.widget.master.master in self.box_list:
                    self.box = event.widget.master.master
        elif str(type(event.widget)) == "<class 'tkinter.Entry'>":
             for boxes in self.box_list:
                if event.widget.master in self.box_list:
                    self.box = event.widget.master
        if self.box != '' and self.box != None: 
            for connections in self.box.connected_to:
                for boxes in connections.connected_to:
                    if boxes == self.box:
                        if self.box.name in connections.line_connects:
                            canvas.delete(connections.line_connects[self.box.name])
                        connections.connected_to.remove(boxes)
                    for keys in boxes.line_connects:
                        canvas.delete(boxes.line_connects[keys])
                    boxes.updateConnections()

            if self.box in self.box_list:
                if str(type(self.box)) == "<class '__main__.ImageBox'>":
                    self.images.remove(self.box.cust_image)
                self.box_list.remove(self.box)
            self.box.destroy()
        self.unbindAll()
        for boxes in self.box_list:
            boxes.unbindSelf()
        canvas.config(cursor="arrow")

    def deleteLines(self,event):
        if str(type(event.widget)) == "<class '__main__.CustomText'>" or str(type(event.widget)) == "<class '__main__.CustomLabel'>":
            for boxes in self.box_list:
                if event.widget.parent in self.box_list:
                    chosen_box = event.widget.parent
        elif str(type(event.widget)) == "<class '__main__.TextBox'>" or str(type(event.widget)) == "<class '__main__.ImageBox'>":
            chosen_box = event.widget
        elif str(type(event.widget)) == "<class 'tkinter.Canvas'>":
            for boxes in self.box_list:
                if event.widget.master.master in self.box_list:
                    chosen_box = event.widget.master.master
        elif str(type(event.widget)) == "<class 'tkinter.Entry'>":
             for boxes in self.box_list:
                if event.widget.master in self.box_list:
                    chosen_box = event.widget.master
        if len(self.frames) < 2:
            self.frames.append(chosen_box)
        if len(self.frames) == 2:
            if self.frames[1] == self.frames[0]:
                for boxes in self.box_list:
                    boxes.unbindSelf()
                self.frames.clear()
                canvas.config(cursor = 'arrow')
                return
            # self.frames[0].connectTo(self.frames[1])
            # #print(self.frames[0].line_connects,self.frames[1].line_connects)
            #for connections in self.box.connected_to:
            if self.frames[0].name in self.frames[1].line_connects:
                canvas.delete(self.frames[1].line_connects[self.frames[0].name])
                self.frames[1].connected_to.remove(self.frames[0])
                del self.frames[1].line_connects[self.frames[0].name]
            if self.frames[1].name in self.frames[0].line_connects:
                canvas.delete(self.frames[0].line_connects[self.frames[1].name])
                self.frames[0].connected_to.remove(self.frames[1])
                del self.frames[0].line_connects[self.frames[1].name]
            for boxes in self.box_list:
                boxes.unbindSelf()
            self.frames.clear()
            canvas.config(cursor = 'arrow')
    def saveState(self,stuff):
        def getScreenShot():
            x=main.winfo_rootx()
            y=main.winfo_rooty()
            x1=x+main.winfo_width()
            y1=y+main.winfo_height()
            someimg = ImageGrab.grab().crop((x,y,x1-(2*lineThick),y1-(2*lineThick)))
            self.fullscreen = CustomImage(numpy.array(someimg),True)
            self.images.append(self.fullscreen)
        def cleanUp():
            for img in self.images:
                if img.fullscreen:
                    #numpy.delete(img)
                    print(len(self.images))
                    self.images.remove(img)
                    print(len(self.images))

        cleanUp()
        file_opt = options = {}
        options['filetypes'] = [('Data Files', '.data')]
        getScreenShot()
        time.sleep(1)
        self.file = asksaveasfilename(**file_opt)
        if self.file != None and self.file != '':
            print(self.file)
            if self.file.find('.data') == -1:
                File = open("{}.data".format(self.file),"wb")
            else:
                File = open(self.file,"wb")
            pickle.dump(self.images + self.box_list,File)
            #pickle.dump(,File)
            File.close()

    def loadFile(self,stuff):
        if self.folder != "" or self.folder != None:
            init_dir = self.folder
        else:
            init_dir = "/"
        self.file = askopenfilename(initialdir = init_dir,title = "Select Page To Load",filetypes = [('Page Files', '*.data')])
        #print(self.file)
        if self.file == "" or self.file == None:
            print('no file found')
            return
        for boxes in self.box_list:
            for dict_connects in boxes.line_connects:
                canvas.delete(boxes.line_connects[dict_connects])
            boxes.line_connects.clear()
            boxes.destroy()
        self.box_list.clear()
        self.images.clear()
        # for lines in self.line_list:
        #     canvas.delete(lines)
        # self.lineList.clear()
        file = open(self.file,"rb")
        d = pickle.load(file)
        print("loading file")
        for data in d:
            if str(type(data)) == "<class '__main__.CustomImage'>":
                new_image = CustomImage(data.__dict__['image'],data.__dict__['fullscreen'])
                new_image.name = data.__dict__['name']
                self.images.append(new_image)
                #new_im = Image.fromarray(new_image.image)
                #new_im.save("haba.png")
            elif str(type(data)) == "<class '__main__.TextBox'>" or str(type(data)) == "<class '__main__.ImageBox'>" or str(type(data)) == "<class '__main__.MathBox'>" :
                #print(str(type(data)))
                self.box = None
                if 'text' in data.__dict__:
                    self.makeTextBox()
                    self.box.text = data.__dict__['text']
                elif 'image' in data.__dict__:
                    #print('yo')
                    self.makeImageBox()
                    self.box.cust_image_name = data.__dict__['image']
                elif 'texts' in data.__dict__:
                    self.makeMathBox()
                    self.box.text_list = data.__dict__['texts']
                    #print(self.box.texts)
                if 'highlighted_text' in data.__dict__:
                    self.box.highlighted_text = data.__dict__['highlighted_text']
                    print(self.box.highlighted_text)
                if 'color' in data.__dict__:
                    self.box.configure(bg = data.__dict__['color'])
                if 'connections' in data.__dict__:
                    self.box.connected_to = data.__dict__['connections']
                self.box.name = data.__dict__['name']
                self.box.TLcorner.x = int(data.__dict__['origin'][0]*screensize[0])
                self.box.TLcorner.y = int(data.__dict__['origin'][1]*screensize[1])
                self.box.w = int(data.__dict__['w']*screensize[0])
                self.box.h = int(data.__dict__['h']*screensize[1])
                self.box.cur_anchor = data.__dict__['anchor']
                if 'text' in data.__dict__:
                    self.box.addTextArea()
                    self.box.addSpacing(1)
                if 'image' in data.__dict__:
                    for img in self.images:
                        if img.name == self.box.cust_image_name:
                            self.box.cust_image = img
                            #self.box.img_data = Image.fromarray(img.image)
                            self.box.addImage()
                            #new_im.save("haba.png")
                
                self.box.frame = canvas.create_window((self.box.TLcorner.x,self.box.TLcorner.y),window = self.box,width=self.box.w,height=self.box.h,anchor='nw')
                if 'texts' in data.__dict__:
                    #print(self.box.text_list)
                    self.box.addMathArea()
                    self.box.drawMathText()
        file.close()
        # remember: after recreate img, set its alreadyOpenFile to True
        for boxes in self.box_list:
            store = []
            for connections in boxes.connected_to:
                for boxes2 in self.box_list:
                    if connections == boxes2.name:
                        #boxes.connected_to.remove(connections)
                        #connections = boxes2
                        #boxes.connected_to.append(boxes2)
                        store.append(boxes2)
            boxes.connected_to.clear()
            boxes.connected_to = store.copy()
        for boxes in self.box_list:
            for connections in boxes.connected_to:
            # print(boxes.connected_to)
                boxes.connectTo(connections)
        self.unbindAll()
        for boxes in self.box_list:
            boxes.unbindSelf()
        canvas.config(cursor='arrow')
    def resetPage(self):
        for boxes in self.box_list:
            #canvas.delete(boxes.line_connects)
            boxes.destroy()
        self.box_list.clear()
        canvas.delete('all')
        self.images.clear()
        self.file = ""
        self.folder = ""
        self.fullscreen = None
    def unbindAll(self):
        canvas.unbind('<Button-1>')
        canvas.unbind('<B1-Motion>')
        canvas.unbind('<ButtonRelease-1>')
    def setClickedCanvas(self):
        canvas.bind('<Button-1>',self.clickedCanvas)
    def setOutline(self):
        canvas.bind('<B1-Motion>',self.outlineBox)

def centerWindow(window,windowWidth,windowHeight):
    x = int(screensize[0])
    y = int(screensize[1])

    centerValueX = int((x/2) - (windowWidth/2))
    centerValueY = int((y/2) - (windowHeight/2))

    centerValueString = "{}x{}+{}+{}".format(windowWidth,windowHeight,centerValueX,centerValueY)
    window.geometry(centerValueString)
centerWindow(main,windowWidth,windowHeight)

mainWindow = Frame(main)
mainWindow.pack(fill="both", expand=True) 
canvas = Canvas(mainWindow, bg=canvasColor,highlightthickness=1,highlightbackground="lightgray")
box_handler = BoxHandler()
scrollbar = Custom_Scrollbar(mainWindow,canvas,"right")
scrollbar.pack(side=RIGHT, fill=Y)
scrollbar2 = Custom_Scrollbar(mainWindow,canvas,"bottom")
scrollbar2.config(orient="horizontal")
scrollbar2.pack(side='bottom', fill=X)
canvas.pack(side="left",fill="both", expand=True)

def saveAsPDF(stuff):
    def getDirectory():
        box_handler.folder = askdirectory()
    getDirectory()
    def SetKeywords(pdf,items):
        keyword = ''
        for item in items:
            if keyword == '':
                keyword = str(items[0])
            else:
                keyword = ",".join([keyword, item])
        print(keyword)
        pdf.set_keywords(keyword)
    def loadExistingPDF():
        #print('loading')
        if box_handler.folder != "" or box_handler.folder != None:
            init_dir = box_handler.folder 
        else:
            init_dir = "/"
        pdf_name = askopenfilename(title='choose pdf',initialdir = init_dir,filetypes = [('Page Files', '*.pdf')])
        popup.lift()
        if pdf_name != '' and pdf_name != None:
            pdf = PdfFileReader(pdf_name)
            #print(pdf.documentInfo)
            if '/Keywords' in pdf.documentInfo:
                keyword_list = pdf.documentInfo['/Keywords']
                keyword_list = keyword_list.split(',')
                print(keyword_list)
                available_pages = list(listbox_left.get(0,END))
                print(available_pages)
                missing_pages = []
                for keywords in keyword_list:
                    if keywords in available_pages:
                        #print('keyword found in left side: '+str(keywords))
                        idx = available_pages.index(keywords) 
                        available_pages.remove(keywords)
                        listbox_left.delete(idx)
                        listbox_right.insert(END, keywords)
                    elif '.data' not in keywords:
                        #print('title: '+str(keywords))
                        listbox_right.insert(END, keywords)
                    elif keywords not in available_pages:
                        #print('page not found in left side')
                        missing_pages.append(keywords)
                if len(missing_pages) > 0:
                    string = 'missing : ' + missing_pages
                    messagebox.showerror(title='Error', message=string)
            entry4.insert(END,pdf_name)
    def tempGetPNG(page):
        page_path = box_handler.folder + "/" + page
        file = open(page_path,"rb")
        d = pickle.load(file)
        #print("loading file")
        temp_images = []
        for data in d:
            if str(type(data)) == "<class '__main__.CustomImage'>":
                new_image = CustomImage(data.__dict__['image'],data.__dict__['fullscreen'])
                new_image.name = data.__dict__['name']
                temp_images.append(new_image)
        for new_image in temp_images:
            if new_image.fullscreen:
                new_im = Image.fromarray(new_image.image)
                page_to_img = page_path.replace('.data','.png')
                new_im.save(page_to_img)
        file.close()
        return page_to_img
    def addTitle():
        title = entry3.get()
        listbox_right.insert(END, title)
    def CurSelet(current,target):
        if(current.size() > 0):
            value=str(current.get(current.curselection()))
            print(value)
            idx = list(current.get(0,END)).index(value)
            #print(idx)
            current.selection_clear(0, END)
            current.delete(idx)

            target.insert(END, value)
    def createPDF():
        def temp():
            if box_handler.folder != None and box_handler.folder != '':
                items = listbox_right.get(0,END)
                pbar = Progressbar(popup)
                pbar.pack()
                count = 0
                pdfname = entry4.get()
                pdf = PDF()
                SetKeywords(pdf,items)
                pdf.alias_nb_pages()
                pdf.set_font('Arial', 'B', 14)
                for item in items:
                    #print(items)
                    if ".data" in item:
                        try:
                            png_name = tempGetPNG(item)
                            #image_name = box_handler.folder + "/" + item
                            pdf.image(png_name, w=190)
                            os.remove(png_name)
                        except:
                            pdf.add_page()
                            png_name = tempGetPNG(item)
                            #image_name = box_handler.folder + "/" + item
                            pdf.image(png_name, w=190)
                            os.remove(png_name)
                    else:
                        pdf.add_page()
                        pdf.cell(0, 10, item, 0, 1,align="C",)
                    count+=1
                    pbar['value'] = int((count/len(items))*100)
                if '.pdf' in pdfname:
                    pdf.output(pdfname, 'F')
                else:
                    pdf.output(box_handler.folder + "/" + pdfname + ".pdf", 'F')
                messagebox.showinfo(title=None, message='pdf was created')
                try:
                    popup.destroy()
                except:
                    print('popup couldnt be destroyed')
        threading.Thread(target=temp).start()
    def stuff():
        print('hi')
    popup = Toplevel()
    popup.transient(main)
    centerWindow(popup, int(0.4 * screensize[0]),int(0.2 * screensize[1]))
    popup.wm_title("Save Page As")
    
    container3 = Frame(popup)
    btn5 = Button(container3,text='update existing pdf',font=14)
    btn5.pack(side=BOTTOM)
    lab3 = Label(container3,text="Add a title")
    lab3.pack(side="left")
    entry3 = Entry(container3,font=14)
    entry3.pack(side="left")
    btn3 = Button(container3,text="enter")
    btn3.pack(side="right")
    container3.pack(side=TOP)

    container4 = Frame(popup)
    lab4 = Label(container4,text="Save pdf as: ")
    lab4.pack(side="left")
    entry4 = Entry(container4,font=14)
    entry4.pack(side="left")
    btn4 = Button(container4,text="enter")
    btn4.pack(side="right")
    container4.pack(side=BOTTOM)

    container1 = Frame(popup)
    container2 = Frame(popup)
    container1.pack(side=RIGHT,fill="both", expand=True)
    container2.pack(side=LEFT,fill="both", expand=True)

    scrollbar_right = Scrollbar(container1)
    scrollbar_right.pack(side=RIGHT, fill=Y)

    listbox_right = Listbox(container1,bd=1, height=10, font=14 ,selectmode=SINGLE,exportselection=0,justify = 'center')
    listbox_right.pack(fill="both", expand=True)

    # attach listbox_right to scrollbar
    listbox_right.config(yscrollcommand=scrollbar_right.set)
    scrollbar_right.config(command=listbox_right.yview)

    scrollbar_left = Scrollbar(container2)
    scrollbar_left.pack(side=RIGHT, fill=Y)

    listbox_left = Listbox(container2,bd=1, height=15, font=14, selectmode=SINGLE,exportselection=0,justify = 'center')
    listbox_left.pack(fill="both", expand=True)

    if box_handler.folder != '' and box_handler.folder != None:        
        filelist=os.listdir(box_handler.folder)
        for file in filelist[:]: # filelist[:] makes a copy of filelist.
            if not(file.endswith(".data")):
                filelist.remove(file)
        for file in filelist:
            listbox_left.insert(END, file)

    listbox_left.config(yscrollcommand=scrollbar_left.set)
    scrollbar_left.config(command=listbox_left.yview)
    listbox_right.bind('<<ListboxSelect>>',lambda event, left=listbox_left, right=listbox_right: CurSelet(right,left))
    listbox_left.bind('<<ListboxSelect>>',lambda event, left=listbox_left, right=listbox_right: CurSelet(left,right))
    btn3.configure(command=addTitle)
    btn4.configure(command=createPDF)
    btn5.configure(command=loadExistingPDF)
    popup.mainloop()

def screenShot(stuff):
    def stop(stuff):
        print('y')
        temp_main.destroy()
    def click(event):
        def drag(event):
            def release(event):
                temp_main.destroy()
                im = pyautogui.screenshot(region=(startx,starty,tempWidth,tempHeight))
                #print(startx,starty,startx+tempWidth,starty+tempHeight)
                box_handler.makeImageBox()
                box_handler.box.TLcorner = Point(0,0)
                im_obj = CustomImage(numpy.array(im),False)
                box_handler.box.cust_image = im_obj
                box_handler.box.cust_image_name = im_obj.name
                temp_img = Image.fromarray(box_handler.box.cust_image.image)
                box_handler.box.w = int(temp_img.size[0] + (lineThick*2.5))
                box_handler.box.h = int(temp_img.size[1] + (lineThick*2.5))
                box_handler.box.addImage()
                box_handler.box.frame = canvas.create_window((box_handler.box.TLcorner.x,box_handler.box.TLcorner.y),window = box_handler.box,width=box_handler.box.w,height=box_handler.box.h,anchor='nw')
                box_handler.images.append(im_obj)
                #printbx
                main.deiconify()
            tempWidth = temp_canvas.canvasx(event.x)-tempx
            tempHeight = temp_canvas.canvasy(event.y)-tempy
            print#(tempx,tempy)
            startx = 0
            starty = 0
            if tempWidth < 0 and tempHeight > 0:
                startx = temp_canvas.canvasx(event.x)
                starty = tempy
            elif tempWidth < 0 and tempHeight < 0:
                startx = temp_canvas.canvasx(event.x)
                starty = temp_canvas.canvasy(event.y)
            elif tempWidth > 0 and tempHeight < 0:
                startx = tempx
                starty = temp_canvas.canvasy(event.y)
            elif tempWidth > 0 and tempHeight > 0:
                startx = tempx
                starty = tempy
            tempWidth = abs(tempWidth)
            tempHeight = abs(tempHeight)     
            #print(startx,starty,startx+tempWidth,starty+tempHeight)
            temp_canvas.coords(tempLine,startx,starty,startx + tempWidth,starty,startx + tempWidth,starty + tempHeight,startx,starty + tempHeight,startx,starty) 
            temp_canvas.bind('<ButtonRelease-1>',release)
        tempx = temp_canvas.canvasx(event.x)
        tempy = temp_canvas.canvasy(event.y)
        temp_canvas.bind('<B1-Motion>',drag)
    print('h')
    temp_main = Tk()
    temp_main.attributes('-fullscreen', True)
    temp_main.attributes('-alpha', .3)
    temp_main.lift()
    temp_main.attributes("-topmost", True)
    temp_canvas = Canvas(temp_main, cursor="cross", bg="grey11")
    temp_canvas.pack(fill=BOTH, expand=YES)
    templine = tempLine = temp_canvas.create_line(0,0,0,0,fill='red',width=6)
    temp_canvas.bind('<Button-1>',click)
    temp_canvas.bind('<Button-3>',stop)
    main.withdraw()
    #self.master_screen.withdraw()

def clearPage(stuff):
    answer = messagebox.askokcancel("Question","Do you want to clear the page? This will remove all unsaved work.")
    if answer:
        box_handler.resetPage()
def highlightText(stuff):
    try: 
        widget = canvas.focus_get()
        parent =  widget.winfo_parent() #<-- can try to store the highlighted strings into parent
        for boxes in box_handler.box_list:
            if parent == str(boxes):
                selection = widget.selection_get()
                if (selection != '' or selection != None) and len(selection) > 0 and selection[-1] == '\n':
                    selection = selection[:-1]
                boxes.addHighlight(selection)
                boxes.highlightText() 
    except:
        print('error highlighting text')
def changeColor(stuff):
    box_handler.unbindAll()
    for boxes in box_handler.box_list:
        boxes.unbind("<Button-1>")
        if str(type(boxes)) == "<class '__main__.TextBox'>":
            boxes.TextArea.config(state=DISABLED)
            boxes.TextArea.bind('<Button-1>',box_handler.changeBoxColor)
        elif str(type(boxes)) == "<class '__main__.ImageBox'>":
            if boxes.image_label != None:
                boxes.image_label.bind('<Button-1>',box_handler.changeBoxColor)
        elif str(type(boxes)) == "<class '__main__.MathBox'>":
            boxes.bind('<Button-1>',box_handler.sidesCorners)
            boxes.fig_frame._tkcanvas.bind('<Button-1>',box_handler.changeBoxColor)
        boxes.bind('<Button-1>',box_handler.changeBoxColor)
    canvas.config(cursor='spraycan')
def createTextBoxes(stuff):
    box_handler.unbindAll()
    box = box_handler.makeTextBox()
    for boxes in box_handler.box_list:
        boxes.unbind("<Button-1>")
    canvas.config(cursor='tcross')
    box_handler.setClickedCanvas()
    box_handler.setOutline()
    canvas.config(cursor = 'crosshair')
    return 'break'
def createImageBoxes(stuff):
    box_handler.unbindAll()
    box = box_handler.makeImageBox()
    for boxes in box_handler.box_list:
        boxes.unbind("<Button-1>")
    canvas.bind("<Button-1>",box_handler.placeImage)
    canvas.config(cursor='coffee_mug')
    return 'break'
def createMathBoxes(stuff):
    box_handler.unbindAll()
    box = box_handler.makeMathBox()
    for boxes in box_handler.box_list:
        boxes.unbind("<Button-1>")
    box_handler.setClickedCanvas()
    box_handler.setOutline()
    canvas.config(cursor='star')
    return 'break'
def moveBoxes(stuff):
    box_handler.unbindAll()
    for boxes in box_handler.box_list:
        boxes.unbind("<Button-1>")
        if str(type(boxes)) == "<class '__main__.TextBox'>":
            boxes.TextArea.config(state=DISABLED)
            boxes.TextArea.bind('<Button-1>',box_handler.selectBox)
        elif str(type(boxes)) == "<class '__main__.ImageBox'>":
            if boxes.image_label != None:
                boxes.image_label.bind('<Button-1>',box_handler.selectBox)
        elif str(type(boxes)) == "<class '__main__.MathBox'>":
            boxes.bind('<Button-1>',box_handler.sidesCorners)
            boxes.fig_frame._tkcanvas.bind('<Button-1>',box_handler.selectBox)
        boxes.bind('<Button-1>',box_handler.selectBox)
    canvas.bind('<B1-Motion>',box_handler.moveBox)
    canvas.config(cursor='fleur')
def resizeUnscaled(stuff):
    box_handler.unbindAll()
    for boxes in box_handler.box_list:
        boxes.unbind("<Button-1>")
        if str(type(boxes)) == "<class '__main__.TextBox'>":
            boxes.TextArea.config(state=DISABLED)
            #boxes.TextArea.bind('<Button-1>',box_handler.sidesCorners)
            boxes.bind('<Button-1>',box_handler.sidesCorners)
        elif str(type(boxes)) == "<class '__main__.ImageBox'>":
            boxes.bind('<Button-1>',box_handler.clickScale)
        elif str(type(boxes)) == "<class '__main__.MathBox'>":
            boxes.bind('<Button-1>',box_handler.sidesCorners)
    canvas.config(cursor='pencil')    
def connect(stuff):
    box_handler.unbindAll()
    if len(box_handler.frames):
        box_handler.frames.clear()
    for boxes in box_handler.box_list:
        boxes.unbind("<Button-1>")
        if str(type(boxes)) == "<class '__main__.TextBox'>":
            boxes.TextArea.config(state=DISABLED)
            boxes.TextArea.bind('<Button-1>',box_handler.connectBoxes)
        elif str(type(boxes)) == "<class '__main__.ImageBox'>":
            if boxes.image_label != None:
                boxes.image_label.bind('<Button-1>',box_handler.connectBoxes)
        elif str(type(boxes)) == "<class '__main__.MathBox'>":
            boxes.bind('<Button-1>',box_handler.sidesCorners)
            boxes.fig_frame._tkcanvas.bind('<Button-1>',box_handler.connectBoxes)
        boxes.bind('<Button-1>',box_handler.connectBoxes)
    canvas.config(cursor='spider')
def deleteBox(stuff):
    box_handler.unbindAll()
    for boxes in box_handler.box_list:
        boxes.unbind("<Button-1>")
        if str(type(boxes)) == "<class '__main__.TextBox'>":
            boxes.TextArea.config(state=DISABLED)
            boxes.TextArea.bind('<Button-1>',box_handler.deleteBoxes)
        elif str(type(boxes)) == "<class '__main__.ImageBox'>":
            if boxes.image_label != None:
                boxes.image_label.bind('<Button-1>',box_handler.deleteBoxes)
        elif str(type(boxes)) == "<class '__main__.MathBox'>":
            boxes.bind('<Button-1>',box_handler.sidesCorners)
            boxes.fig_frame._tkcanvas.bind('<Button-1>',box_handler.deleteBoxes)
        boxes.bind('<Button-1>',box_handler.deleteBoxes)
    canvas.config(cursor='X_cursor')
def deleteLine(stuff):
    box_handler.unbindAll()
    if len(box_handler.frames):
        box_handler.frames.clear()
    if len(box_handler.frames):
        box_handler.frames.clear()
    for boxes in box_handler.box_list:
        boxes.unbind("<Button-1>")
        if str(type(boxes)) == "<class '__main__.TextBox'>":
            boxes.TextArea.config(state=DISABLED)
            boxes.TextArea.bind('<Button-1>',box_handler.deleteLines)
        elif str(type(boxes)) == "<class '__main__.ImageBox'>":
            if boxes.image_label != None:
                boxes.image_label.bind('<Button-1>',box_handler.deleteLines)
        elif str(type(boxes)) == "<class '__main__.MathBox'>":
            boxes.bind('<Button-1>',box_handler.sidesCorners)
            boxes.fig_frame._tkcanvas.bind('<Button-1>',box_handler.deleteLines)
        boxes.bind('<Button-1>',box_handler.deleteLines)
    canvas.config(cursor='pirate')
def stopBindings(stuff):
    box_handler.unbindAll()
    for boxes in box_handler.box_list:
        boxes.unbindSelf()
        print(type(boxes))
    canvas.config(cursor='arrow')
    return 'break'

def helpBox(stuff):
    popup = Toplevel()
    popup.transient(main)
    centerWindow(popup, int(0.4 * screensize[0]),int(0.35 * screensize[1]))
    popup.wm_title("Help - keybinds")

    listbox = Listbox(popup,bd=1, height=10, font=14 ,selectmode=SINGLE,exportselection=0,justify = 'center')
    listbox.pack(fill=BOTH, expand=1)
    listbox.insert(END,"control shift h = highlight text")
    listbox.insert(END,"control shift c = color boxes")
    listbox.insert(END,"control t = create textbox")
    listbox.insert(END,"control i = create image")
    listbox.insert(END,"control shift i = take screenshot")
    listbox.insert(END,"control u = create mathbox")
    listbox.insert(END,"control z = select text in mathbox")
    listbox.insert(END,"control a = deselect text in mathbox")
    listbox.insert(END,"enter = add math text when using mathbox")
    listbox.insert(END,"control delete = remove math text when using mathbox")
    listbox.insert(END,"control up = move up in math box")
    listbox.insert(END,"control down = move down in math box")
    listbox.insert(END,"control left = move left in math box")
    listbox.insert(END,"control right = move right in math box")
    listbox.insert(END,"z/ i = add integral to mathbox")
    listbox.insert(END,"z/ f = add fraction to mathbox")
    listbox.insert(END,"z/ l = add limit to mathbox")
    listbox.insert(END,"z/ s = add summation to mathbox")
    listbox.insert(END,"z/ r = add square root to mathbox")
    listbox.insert(END,"z/ t = add theta to mathbox")
    listbox.insert(END,"z/ d = add delta to mathbox")
    listbox.insert(END,"z/ p = add pi to mathbox")
    listbox.insert(END,"z/ 6 = raise by power")
    listbox.insert(END,"z/ - = lower by power")
    listbox.insert(END,"z/ = add not equal symbol to mathbox")
    listbox.insert(END,"z/ w = add right arrow to mathbox")
    listbox.insert(END,"z/ q = add left arrow to mathbox")
    listbox.insert(END,"` 'any number' = raise text by power")
    listbox.insert(END,"control m = move boxes")
    listbox.insert(END,"control shift d = delete box")
    listbox.insert(END,"control l = connect boxes with lines")
    listbox.insert(END,"control d = delete box connections")
    listbox.insert(END,"control o = clear current keybinding")
    listbox.insert(END,"control n = clear canvas")
    listbox.insert(END,"control s = save as a data file")
    listbox.insert(END,"control shift l = load a data file")
    listbox.insert(END,"control p = create pdf")
    return 'break'

main.bind("<Control_L> <H>",highlightText)
main.bind("<Control_L> <t>",createTextBoxes)
main.bind("<Control_L> <i>",createImageBoxes)
main.bind("<Control_L> <I>",screenShot)
main.bind("<Control_L> <m>",moveBoxes)
main.bind("<Control_L> <s>",box_handler.saveState)
main.bind("<Control_L> <L>",box_handler.loadFile)
main.bind("<Control_L> <r>",resizeUnscaled)
main.bind("<Control_L> <l>",connect)
main.bind("<Control_L> <p>",saveAsPDF)
main.bind("<Control_L> <D>",deleteBox)
main.bind("<Control_L> <d>",deleteLine)
main.bind("<Control_L> <C>",changeColor)
main.bind("<Control_L> <n>",clearPage)
main.bind("<Control_L> <u>",createMathBoxes)
main.bind("<Control_L> <h>",helpBox)
main.bind("<Control_L> <o>",stopBindings)
main.mainloop()
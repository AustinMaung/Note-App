from tkinter import *
from tkinter.filedialog import askopenfilename, asksaveasfilename, askdirectory
from tkinter.colorchooser import askcolor
from tkinter import ttk
from ctypes import windll
user32 = windll.user32
user32.SetProcessDPIAware()
from PIL import ImageGrab,ImageTk, Image
import os
import io
import shutil
import pickle
import time
import uuid

class Point():
    def __init__(self,x,y):
        self.x = x
        self.y = y

class CustomText(Text):
    '''
    text = CustomText()
    text.tag_configure("red", foreground="#ff0000")
    text.highlight_pattern("this should be red", "red")
    '''
    def __init__(self, *args, **kwargs):
        Text.__init__(self, *args, **kwargs)
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

class Box(Frame):
    def __init__(self,parent):
        super().__init__(parent,bg="green",cursor="target") 
        self.parent = parent
        self.name = uuid.uuid1()
        self.connected_to = []
        self.line_id = canvas.create_line(0,0,0,0,width=10, fill='green')
        self.resize = False
        self.w = -1
        self.h = -1
        self.origin = Point(-1,-1)
        self.middle = Point(-1,-1)
        self.end = Point(-1,-1)
        self.disOrigin = Point(-1,-1)
        self.disMax = Point(-1,-1)
    def canDrawBox(self):
        canvas.unbind("<Button-1>")
        canvas.unbind("<B1-Motion>")
        canvas.unbind("<ButtonRelease-1>")
        canvas.bind("<Button-1>",self.setOriginPoints)
        canvas.bind("<B1-Motion>",self.setOutline)
        canvas.bind("<ButtonRelease-1>",self.setEndPoints)
    def unbindStuff(self):
        canvas.unbind("<Button-1>")
        canvas.unbind("<B1-Motion>")
        canvas.unbind("<ButtonRelease-1>")
    def setOriginPoints(self,event):
        self.origin.x = event.x
        self.origin.y = event.y
    def setOutline(self,event):
        canvas.coords(self.line_id,self.origin.x,self.origin.y,event.x,self.origin.y,event.x,event.y,self.origin.x,event.y,self.origin.x,self.origin.y)
    def setEndPoints(self,event):
        #calculating width/height without taking in account negatives
        textboxWidth = event.x-self.origin.x
        textboxHeight = event.y-self.origin.y
        if textboxWidth < 0 and textboxHeight > 0:
            self.place(x=event.x,y=self.origin.y,width=(-textboxWidth),height=textboxHeight)
            self.origin = Point(event.x,self.origin.y)
        elif textboxWidth < 0 and textboxHeight < 0:
            self.place(x=event.x,y=event.y,width=(-textboxWidth),height=(-textboxHeight))
            self.origin = Point(event.x,event.y)
        elif textboxWidth > 0 and textboxHeight < 0:
            self.place(x=self.origin.x,y=event.y,width=(textboxWidth),height=(-textboxHeight))
            self.origin = Point(self.origin.x,event.y)
        elif textboxWidth > 0 and textboxHeight > 0:
            self.place(x=self.origin.x,y=self.origin.y,width=(textboxWidth),height=(textboxHeight))
            self.origin = Point(self.origin.x,self.origin.y)
        self.w = abs(textboxWidth)
        self.h = abs(textboxHeight)
        #reset the line_id
        canvas.delete(self.line_id)
        self.line_id = canvas.create_line(0,0,0,0,width=10, fill='green')
        self.unbindStuff()
        self.unbind("<Button-1>")
        self.startClickable()
        handler.drawAllLines()
    def startClickable(self):
        self.bind("<Button-1>", self.clickedOn)
    def stopClickable (self):
        self.unbind("<Button-1>")
    def clickedOn(self,event):
        self.unbindStuff()
        frameWidth = event.widget.winfo_width()
        frameHeight = event.widget.winfo_height()
        frameOrigin = Point(event.widget.winfo_x(),event.widget.winfo_y())
        mousePos = Point(event.x,event.y)
        self.place_forget()
        #CORNER = Point(0.07 * frameWidth, 0.07 * frameHeight)
        #calculation of the start position depending on which corner the user clicked on
        if mousePos.x <= lineThick and mousePos.y <= lineThick: #TOPLEFTCORNER
            self.origin.x = frameWidth + frameOrigin.x
            self.origin.y = frameHeight + frameOrigin.y   
        elif mousePos.x <=lineThick and mousePos.y >= (frameHeight-lineThick): #BOTTOMLEFT CORNER
            self.origin.x = frameWidth + frameOrigin.x
            self.origin.y = frameOrigin.y
        elif mousePos.x >= (frameWidth - lineThick) and mousePos.y <= lineThick: #TOPRIGHT CORNER
            self.origin.x = frameOrigin.x
            self.origin.y = frameHeight + frameOrigin.y
        elif mousePos.x >= (frameWidth - lineThick) and mousePos.y >(frameHeight-lineThick): #BOTTOMRIGHT CORNER
            self.origin.x = frameOrigin.x
            self.origin.y = frameOrigin.y     
        # translation of the box
        else: #user clicked somewhere on the box that wasnt on the corners
            #deleting the existing box
            #calculates where the box should be placed with respect to the cursor by storing the distance between the cursor and corners
            self.disOrigin.x = event.x
            self.disOrigin.y = event.y
            self.disMax.x = frameWidth - self.disOrigin.x
            self.disMax.y = frameHeight - self.disOrigin.y
            #binding of the translation events
            canvas.bind("<B1-Motion>", self.moveBox)
            canvas.bind("<ButtonRelease-1>", self.stopBox)
            handler.removeAllLines()
            return # skips the next block of code to exit the function early
        #reshaping of the box
        canvas.bind("<B1-Motion>",self.setOutline)
        canvas.bind("<ButtonRelease-1>",self.setEndPoints)
        handler.removeAllLines() #handler is a separate object, not part of this object

    def moveBox(self,event): #current box doesnt exist, this function just creates the outline as the mouse is being moved
        mousePos = Point(event.x,event.y) #where the mouse cursor is when the box was clicked on
        topLeft = Point(mousePos.x - self.disOrigin.x, mousePos.y - self.disOrigin.y) #topleft corner of box
        topRight = Point(mousePos.x + self.disMax.x, mousePos.y - self.disOrigin.y)
        botRight = Point(mousePos.x + self.disMax.x, mousePos.y + self.disMax.y)
        botLeft = Point(mousePos.x - self.disOrigin.x,mousePos.y + self.disMax.y)
        #draws the outline of where the box would be, direction: topleft->topright->botright->botleft-topleft
        canvas.coords(self.line_id,topLeft.x,topLeft.y,topRight.x,topRight.y,botRight.x,botRight.y,botLeft.x,botLeft.y,topLeft.x,topLeft.y)
    def stopBox(self,event): #this function creates the box as the left mouse button is released
        #calculations done again since the event.x/event.y changed
        mousePos = Point(event.x,event.y)
        topLeft = Point(mousePos.x - self.disOrigin.x, mousePos.y - self.disOrigin.y)
        topRight = Point(mousePos.x + self.disMax.x, mousePos.y - self.disOrigin.y)
        botRight = Point(mousePos.x + self.disMax.x, mousePos.y + self.disMax.y)
        botLeft = Point(mousePos.x - self.disOrigin.x,mousePos.y + self.disMax.y)
        self.place(x=topLeft.x,y=topLeft.y,width=botRight.x-topLeft.x,height=botRight.y-topLeft.y)
        self.origin = topLeft
        #reset the outline
        canvas.delete(self.line_id)
        self.line_id = canvas.create_line(0,0,0,0,width=10, fill='green')
        #unbind any events related to the canvas and rebind the clickedOn function to the new box
        self.unbind("<Button-1>")
        canvas.unbind("<B1-Motion>")
        canvas.unbind("<ButtonRelease-1>")
        self.startClickable()
        handler.drawAllLines() #handler is a separate object, not part of this object
    def create(self):
        self.place(x=self.origin.x,y=self.origin.y,width=self.w,height=self.h)

class TextBox(Box):
    def __init__(self,parent):
        super().__init__(parent)
        self.parent = parent
        self.text = ""
        self.highlighted_text = []
    def setEndPoints(self,event):
        self.after(1, lambda: super(TextBox,self).setEndPoints(event))
        #print(event.widget.origin.x, event.widget.origin.y)
        self.w = abs(event.x-self.origin.x)
        self.h = abs(event.y-self.origin.y)
        self.TextArea = CustomText(self,wrap=WORD,font=("Courier", 14),tabs="1c")
        self.TextArea.place(x=lineThick,y=lineThick,width=self.w-2*lineThick,height=self.h-2*lineThick)
        self.TextArea.insert("end",self.text)
        self.highlightText()
    def stopBox(self,event):
        self.after(1, lambda: super(TextBox,self).stopBox(event))
        self.TextArea = CustomText(self,wrap=WORD,font=("Courier", 14),tabs="1c")
        self.TextArea.place(x=lineThick,y=lineThick,width=self.w-2*lineThick,height=self.h-2*lineThick)
        self.TextArea.insert("end",self.text)
        self.highlightText()
    def clickedOn(self,event):
        self.after(1, lambda: super(TextBox,self).clickedOn(event))
        self.text = self.TextArea.get("1.0","end-1c")
        self.TextArea.destroy()
    def create(self):
        self.after(1, lambda: super(TextBox,self).create())
        self.TextArea = CustomText(self,wrap=WORD,font=("Courier", 14),tabs="1c")
        self.TextArea.place(x=lineThick,y=lineThick,width=self.w-2*lineThick,height=self.h-2*lineThick)
        self.TextArea.insert("end",self.text)
        self.highlightText()
    def addHighlight(self,selection):
        self.highlighted_text.append(selection)
        self.TextArea.tag_configure("yellow", background="yellow")
        self.TextArea.highlight_pattern(selection,"yellow")
    def removeHighlight(self,selection):
        if selection in self.highlighted_text:
            self.highlighted_text.remove(selection)
    def highlightText(self):
        self.TextArea.tag_configure("yellow", background="yellow")
        self.text = self.TextArea.get("1.0","end-1c")
        for highlights in self.highlighted_text:
            if highlights in self.text:
                self.TextArea.highlight_pattern(highlights,"yellow")
        #print(self.highlighted_text)
    def __getstate__(self):
        print( "I'm being pickled")
        info = {
            "name" : self.name,
            "text" : self.text,
            "highlighted_text" : self.highlighted_text,
            "color" : self.cget("bg"),
            "connections" : [connections.name for connections in self.connected_to],
            "origin" : [self.origin.x,self.origin.y],
            "w" : self.w,
            "h" : self.h
        }
        return info
    def __setstate__(self, d):
        print ("I'm being unpickled with these values:", d)
        self.__dict__ = d

class ImageBox(Box):
    def __init__(self,parent):
        super().__init__(parent)
        self.parent = parent
        self.text = ""
        self.filename = ""
        self.imgPanel = None
        self.alreadyOpenFile = False
    def setEndPoints(self,event):
        self.after(0, lambda: super(ImageBox,self).setEndPoints(event))
        if(self.alreadyOpenFile == False):
            self.filename = askopenfilename(initialdir = "/",title = "Select file",filetypes = (("jpeg files","*.jpg"),("png files","*.png*")))
            self.alreadyOpenFile = True
        if(self.filename != ""):
            self.after(1, lambda: self.drawImage(self.filename)) #the function is delayed since it activates before the parent callback
            #self.drawImage(self.filename)
        else:
            handler.boxList.remove(self)
            self.destroy()
    def stopBox(self,event):
        self.after(1, lambda: super(ImageBox,self).stopBox(event))
        self.drawImage(self.filename)
    def clickedOn(self,event):
        self.after(1, lambda: super(ImageBox,self).clickedOn(event))
        self.imgPanel.destroy()
    def create(self):
        self.after(1, lambda: super(ImageBox,self).create())
        self.after(1, lambda: self.drawImage(self.filename))
    def drawImage(self,filename):
        temp_img = Image.open(filename)
        temp_img = temp_img.resize((self.w-int(2.5*lineThick), self.h-int(2.5*lineThick)),Image.ANTIALIAS)
        img = ImageTk.PhotoImage(temp_img)
        self.imgPanel = Label(self, image = img)
        self.imgPanel.image = img
        self.imgPanel.place(x=lineThick,y=lineThick)
    def __getstate__(self):
        print( "I'm being pickled")
        info = {
            "name" : self.name,
            "color" : self.cget("bg"),
            "img" : self.filename,
            "connections" :  [connections.name for connections in self.connected_to],
            "origin" : [self.origin.x,self.origin.y],
            "w" : self.w,
            "h" : self.h
        }
        return info
    def __setstate__(self, d):
        print ("I'm being unpickled with these values:", d)
        self.__dict__ = d

class BoxHandler():
    def __init__(self):
        self.boxList = []
        self.lineList = []
        self.box1 = None
        self.box2 = None
        self.color = None
        self.folder = None
        self.file = None
    def makeTextBox(self):
        for boxes in self.boxList:
            if boxes.origin.x == -1:
                self.boxList.remove(boxes)
                boxes.destroy()
        box = TextBox(canvas)
        box.canDrawBox()
        print(box.name)
        self.boxList.append(box)
        return box
    def makeImageBox(self):
        for boxes in self.boxList:
            if boxes.origin.x == -1:
                self.boxList.remove(boxes)
                boxes.destroy()
        box = ImageBox(canvas)
        box.canDrawBox()
        self.boxList.append(box)
        return box
    def connectBoxes(self,event):
        if self.box1 == None:
            self.box1 = event.widget
        elif self.box2 == None:
            self.box2 = event.widget
        if self.box1 != None and self.box2 != None and self.box1 != self.box2:
            self.box1.connected_to.append(self.box2)
            self.box2.connected_to.append(self.box1)
            midPoint1 = Point(self.box1.origin.x + (self.box1.w/2), self.box1.origin.y + (self.box1.h/2))
            midPoint2 = Point(self.box2.origin.x + (self.box2.w/2), self.box2.origin.y + (self.box2.h/2))
            line_id = canvas.create_line(0,0,0,0,width=10, fill='black')
            self.lineList.append(line_id)
            canvas.coords(line_id,midPoint1.x,midPoint1.y,midPoint2.x,midPoint2.y)
            self.box1 = None
            self.box2 = None
    def removeBox(self,event):
        self.removeAllLines()
        for boxes in self.boxList:
            if event.widget in boxes.connected_to:
                self.removeConnection(boxes,event.widget)
        self.boxList.remove(event.widget)
        event.widget.destroy()
        self.drawAllLines()
    def removeConnection(self,box1,box2):
        box1.connected_to.remove(box2)
        box2.connected_to.remove(box1)
    def removeConnectionHelper(self,event):
        if self.box1 == None:
            self.box1 = event.widget
        elif self.box2 == None:
            self.box2 = event.widget
        if self.box1 != None and self.box2 != None and self.box1 != self.box2:
            self.removeConnection(self.box1,self.box2)
            self.removeAllLines()
            self.drawAllLines()
            self.box1 = None
            self.box2 = None
    def removeAllConnections(self):
        for boxes in self.boxList:
            boxes.connect_to.clear()
    def drawAllLines(self):
        for boxes in self.boxList:
            for connections in boxes.connected_to:
                midPoint1 = Point(boxes.origin.x + (boxes.w/2), boxes.origin.y + (boxes.h/2))
                midPoint2 = Point(connections.origin.x + (connections.w/2), connections.origin.y + (connections.h/2))
                line_id = canvas.create_line(0,0,0,0,width=10, fill='black')
                self.lineList.append(line_id)
                canvas.coords(line_id,midPoint1.x,midPoint1.y,midPoint2.x,midPoint2.y)
    def removeAllLines(self):
        for lines in self.lineList:
            canvas.delete(lines)
    def changeBoxColor(self, event):
        event.widget.configure(bg = self.color)
    def saveAsPage(self):
        if self.folder == "" or self.folder == None:
            print("no folder found, can't save")
            popupBasic('no folder found, cannot save')
            return
        for boxes in self.boxList:
            if boxes.origin.x == -1:
                self.boxList.remove(boxes)
                boxes.destroy()
        #print(self.folder, self.file)
        File = open("{}.data".format(self.file),"wb")
        current = os.path.dirname(os.path.abspath(__file__))
        filename = "{}.data".format(self.file)
        current = current +"/"+ filename
        destination = self.folder +"/"+ filename
        pickle.dump(self.boxList,File)
        File.close()
        #print(destination)
        shutil.move(current, destination)
    def saveAsPNG(self):
        if self.folder == "" or self.folder == None:
            print('no folder found, cannot save as image')
            popupBasic('no folder selected to save into, cannot save as image')
            return
        png_name = self.folder +"/"+"{}.png".format(self.file)
        x=main.winfo_rootx()
        y=main.winfo_rooty()
        x1=x+main.winfo_width()
        y1=y+main.winfo_height()
        someimg = ImageGrab.grab().crop((x,y+canvas_y,x1,y1))
        #filelocation = asksaveasfilename(defaultextension=".png")
        someimg.save(png_name)
    def saveAsPDF(self):
        pass
    def loadFile(self):
        if self.file == "" or self.file == None:
            print('no file found')
            return
        for boxes in self.boxList:
            boxes.destroy()
        self.boxList.clear()
        for lines in self.lineList:
            canvas.delete(lines)
        self.lineList.clear()
        file = open(self.file,"rb")
        d = pickle.load(file)
        print("loading file")
        for data in d:
            #print(data.__dict__)
            box = None
            if 'text' in data.__dict__:
                box = self.makeTextBox()
                box.text = data.__dict__['text']
            elif 'img' in data.__dict__:
                box = self.makeImageBox()
                box.filename = data.__dict__['img']
                box.alreadyOpenFile = True
            if 'highlighted_text' in data.__dict__:
                box.highlighted_text = data.__dict__['highlighted_text']
            if 'color' in data.__dict__:
                box.configure(bg = data.__dict__['color'])
            if 'connections' in data.__dict__:
                box.connected_to = data.__dict__['connections']
            box.name = data.__dict__['name']
            box.origin.x = data.__dict__['origin'][0]
            box.origin.y = data.__dict__['origin'][1]
            box.w = data.__dict__['w']
            box.h = data.__dict__['h']
            box.create()
        file.close()
        # remember: after recreate img, set its alreadyOpenFile to True
        for boxes in self.boxList:
            for connections in boxes.connected_to:
                for boxes2 in self.boxList:
                    if connections == boxes2.name:
                        boxes.connected_to.remove(connections)
                        boxes.connected_to.append(boxes2)
        print("connections")
        for boxes in self.boxList:
            print(boxes.connected_to)
        self.drawAllLines()
        for boxes in handler.boxList:
            boxes.unbind("<Button-1>")
            boxes.bind("<Button-1>",boxes.clickedOn)   
        canvas.unbind("<Button-1>")
        canvas.unbind("<B1-Motion>")
        canvas.unbind("<ButtonRelease-1>")
        
main = Tk()
screensize = main.winfo_screenwidth(),main.winfo_screenheight() 
windowWidth = int(0.65 * screensize[0])
windowHeight = int(0.6 * screensize[1])
lineThick = int(0.008 * screensize[0])

def centerWindow(window,windowWidth,windowHeight):
    x = int(screensize[0])
    y = int(screensize[1])

    centerValueX = int((x/2) - (windowWidth/2))
    centerValueY = int((y/2) - (windowHeight/2))

    centerValueString = "{}x{}+{}+{}".format(windowWidth,windowHeight,centerValueX,centerValueY)
    window.geometry(centerValueString)
centerWindow(main,windowWidth,windowHeight)

def popupColor(msg):
    popup = Tk()
    centerWindow(popup, int(0.4 * screensize[0]),int(0.2 * screensize[1]))
    popup.wm_title("Change Color")
    label = Label(popup, text=msg, font=LARGE_FONT)
    label.pack(side="top", fill="x", pady=10)
    B1 = Button(popup, text="CHANGE BOX COLOR", command = lambda:changeBoxColorHelper(popup))
    B1.pack()
    B2 = Button(popup, text="CHANGE LINE COLOR", command = popup.destroy)
    B2.pack()
    popup.mainloop()
def changeBoxColorHelper(popup):
    for boxes in handler.boxList:
        boxes.unbind("<Button-1>")
        boxes.bind("<Button-1>",handler.changeBoxColor)
    popup.destroy()

def popupBasic(msg):
    popup = Tk()
    centerWindow(popup, int(0.4 * screensize[0]),int(0.2 * screensize[1]))
    popup.wm_title("Error")
    label = Label(popup, text=msg, font=LARGE_FONT)
    label.pack(side="top", fill="x", pady=10)
    popup.mainloop()
def popupLoad(msg):
    popup = Tk()
    centerWindow(popup, int(0.4 * screensize[0]),int(0.2 * screensize[1]))
    popup.wm_title("Load")
    label = Label(popup, text=msg, font=LARGE_FONT)
    label.pack(side="top", fill="x", pady=10)
    B1 = Button(popup, text="Folder", command =lambda : [popupLoadHelper1(),popup.destroy()])
    B1.pack()
    B2 = Button(popup, text="Page", command = lambda : [popupLoadHelper2(),popup.destroy()])
    B2.pack()
    popup.mainloop()
def popupLoadHelper1():
    folderlocation = askdirectory()
    handler.folder = folderlocation
def popupLoadHelper2():
    filename = askopenfilename()
    handler.file = filename
    handler.loadFile()

def popupSave(msg):
    popup = Tk()
    centerWindow(popup, int(0.4 * screensize[0]),int(0.2 * screensize[1]))
    popup.wm_title("Save")
    tab_parent = ttk.Notebook(popup)
    tab1 = Frame(tab_parent)
    tab2 = Frame(tab_parent)
    tab_parent.add(tab1,text="Page")
    tab_parent.add(tab2,text="PNG")
    tab_parent.pack(expand=1, fill='both')
    main_label = Label(popup, text=msg, font=LARGE_FONT)
    main_label.pack(side="top", fill="x", pady=10)
    lab1 = Label(tab1,text="file name")
    lab2 = Label(tab2,text="file name")
    entry1 = Entry(tab1)
    entry2 = Entry(tab2)
    btn1 = Button(tab1,text="save",command=lambda: popupSaveHelper1(popup,entry1))
    btn2 = Button(tab2,text="save",command=lambda: popupSaveHelper2(popup,entry2))
    lab1.pack(side="left")
    entry1.pack(side="left")
    btn1.pack(side="left")
    lab2.pack(side="left")
    entry2.pack(side="left")
    btn2.pack(side="left")

def popupSaveHelper1(popup,entry):
    #print("hi")
    page_name = entry.get()
    #print(page_name)
    handler.file = page_name
    popup.destroy()
    time.sleep(1)
    handler.saveAsPage()
    #handler.after(1, handler.saveAsPage())
def popupSaveHelper2(popup,entry):
    png_name = entry.get()
    handler.file = png_name
    popup.destroy()
    #handler.after(1, handler.saveAsPNG())
    time.sleep(1)
    handler.saveAsPNG()
def test(button):
    print("hi")
def createTextBoxes(stuff):
    for boxes in handler.boxList:
        boxes.unbind("<Button-1>")
        boxes.bind("<Button-1>",boxes.clickedOn) 
    box = handler.makeTextBox()
    box.canDrawBox()
def createImageBoxes(stuff): 
    for boxes in handler.boxList:
        boxes.unbind("<Button-1>")
        boxes.bind("<Button-1>",boxes.clickedOn)
    box = handler.makeImageBox()
    box.canDrawBox()
def createLines(stuff):
    canvas.unbind("<Button-1>")
    handler.box1 = None
    handler.box2 = None
    for boxes in handler.boxList:
        boxes.unbind("<Button-1>")
        boxes.bind("<Button-1>",handler.connectBoxes)
def deleteBox(stuff):
    for boxes in handler.boxList:
        boxes.unbind("<Button-1>")
        boxes.bind("<Button-1>",handler.removeBox)
def deleteLine(stuff):
    canvas.unbind("<Button-1>")
    for boxes in handler.boxList:
        boxes.bind("<Button-1>",handler.removeConnectionHelper)
def chooseColor(stuff):
    choice = askcolor(parent=canvas, title='Pick a color')
    handler.color = choice[1]
    popupColor("Choose to change the color of: box, line")
def chooseSave(stuff):
    popupSave("Choose how you want to save the page: page, png, pdf")
def load(stuff):
    popupLoad("Choose what to load: folder, page")
    #handler.loadFile()
def highlightText(stuff):
    widget = canvas.focus_get()
    parent =  widget.winfo_parent() #<-- can try to store the highlighted strings into parent
    for boxes in handler.boxList:
        if parent == str(boxes):
            selection = widget.selection_get()
            boxes.addHighlight(selection)
            boxes.highlightText()  
def generalKeyBind():
    main.bind("<Control_L> <t>",createTextBoxes)
    main.bind("<Control_L> <i>",createImageBoxes)
    main.bind("<Control_L> <l>",createLines)
    main.bind("<Control_L> <j>",highlightText)
generalKeyBind()

canvas = Canvas(main, bg='white',highlightthickness=1,highlightbackground="lightgray")
handler = BoxHandler()
LARGE_FONT= ("Verdana", 12)
NORM_FONT = ("Helvetica", 10)
SMALL_FONT = ("Helvetica", 8)

button1 = Button(main, text="ADD IMAGE", fg="black",bg = "lightgray",cursor="target",command= lambda: createImageBoxes(button1))
button2 = Button(main, text="TEXTBOX", fg="black",bg = "lightgray",cursor="target",command= lambda: createTextBoxes(button1))
button3 = Button(main, text="LINE", fg="black",bg = "lightgray",cursor="target", command= lambda: createLines(button1))
button4 = Button(main, text="COLOR", fg="black",bg = "lightgray",cursor="target",command= lambda: chooseColor(button1))
button5 = Button(main, text="DEL BOX", fg="black",bg = "lightgray",cursor="target",command= lambda: deleteBox(button1))
button6 = Button(main, text="DEL LINE", fg="black",bg = "lightgray",cursor="target",command= lambda: deleteLine(button1))
button7 = Button(main, text="SAVE", fg="black",bg = "lightgray",cursor="target",command= lambda: chooseSave(button1))
button8 = Button(main, text="LOAD", fg="black",bg = "lightgray",cursor="target",command= lambda: load(button1))
button9 = Button(main, text="NEWPAGE", fg="black",bg = "lightgray",cursor="target",command= lambda: test(button1))

canvas_y = int(screensize[1] * 0.14)
canvas_height = int(screensize[1] - canvas_y)
canvas.place(x=0,y=canvas_y,width=int(screensize[0]),height=canvas_height)
button_x = int(screensize[0] * 0.015)
button_y = int(screensize[1] * 0.04)
button_width = int(screensize[1] * 0.12)
button_height = int(screensize[1] * 0.06)
button1.place(x=button_x,y=button_y,width=button_width,height=button_height)
button2.place(x=button_x + button_width,y=button_y,width=button_width,height=button_height)
button3.place(x=button_x + (2 * button_width),y=button_y,width=button_width,height=button_height)
button4.place(x=button_x + (3 * button_width),y=button_y,width=button_width,height=button_height)
button5.place(x=button_x + (4 * button_width) + (lineThick),y=button_y,width=button_width,height=button_height)
button6.place(x=button_x + (5 * button_width) + (lineThick),y=button_y,width=button_width,height=button_height)
button7.place(x=button_x + (6 * button_width) + (2 * lineThick),y=button_y,width=button_width,height=button_height)
button8.place(x=button_x + (7 * button_width) + (2 * lineThick),y=button_y,width=button_width,height=button_height)
button9.place(x=button_x + (8 * button_width) + (2 * lineThick),y=button_y,width=button_width,height=button_height)
main.mainloop()

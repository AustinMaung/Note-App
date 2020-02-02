from tkinter import *
from tkinter.filedialog import askopenfilename, asksaveasfilename
from PIL import ImageGrab,ImageTk, Image

#main variables
windowWidth = 600
windowHeight = 400
alreadyOpenFile = False
stringNote = ""
imageDict = {}
frameToFrames = {}
framelist = []
lineList = [] #all possible lines
savelistpos = None
#connectFrames = each frame being selected
frame1 = None
frame2 = None

main = Tk()
screensize = main.winfo_screenwidth(),main.winfo_screenheight()
#screenarea = screensize[0] * screensize[1]
lineThick = int(0.008 * screensize[0])
#lineThick = 10
print(screensize[0])

def centerWindow():
    x = int(screensize[0])
    y = int(screensize[1])
    print(x, y)

    centerValueX = int((x/2) - (windowWidth/2))
    centerValueY = int((y/2) - (windowHeight/2))

    centerValueString = "{}x{}+{}+{}".format(windowWidth,windowHeight,centerValueX,centerValueY)
    main.geometry(centerValueString)
centerWindow()

def Save(button):
    changeButtonColor(button, "red")
    x=main.winfo_rootx()
    y=main.winfo_rooty()
    x1=x+main.winfo_width()
    y1=y+main.winfo_height()
    someimg = ImageGrab.grab().crop((x,y+100,x1,y1))
    filelocation = asksaveasfilename(defaultextension=".png")
    someimg.save(filelocation)

def textboxPoints1(event):
    global mouseXclick
    global mouseYclick
    global line_id
    global alreadyOpenFile
    if alreadyOpenFile == True: 
        alreadyOpenFile = False
    mouseXclick = event.x
    mouseYclick = event.y
    line_id = canvas.create_line(0,0,0,0,width=lineThick, fill='green')

def moveTextBox(event):
    global disOriginX 
    global disOriginY
    global disMaxX
    global disMaxY
    global line_id
    currX = event.x
    currY = event.y
    pnt1X = currX - disOriginX
    pnt1Y = currY - disOriginY
    pnt2X = currX + disMaxX
    pnt2Y = currY - disOriginY
    pnt3X = currX + disMaxX
    pnt3Y = currY + disMaxY
    pnt4X = currX - disOriginX
    pnt4Y = currY + disMaxY
    canvas.coords(line_id,pnt1X,pnt1Y,pnt2X,pnt2Y,pnt3X,pnt3Y,pnt4X,pnt4Y,pnt1X,pnt1Y)

def stopTextBox(event):
    global frame
    global disOriginX 
    global disOriginY
    global disMaxX
    global disMaxY
    global line_id
    global stringNote
    global currButton
    global filename
    global frameToFrames
    global frameList
    global lineList
    global savelistpos
    currX = event.x
    currY = event.y
    pnt1X = currX - disOriginX
    pnt1Y = currY - disOriginY
    pnt2X = currX + disMaxX
    pnt2Y = currY - disOriginY
    pnt3X = currX + disMaxX
    pnt3Y = currY + disMaxY
    pnt4X = currX - disOriginX
    pnt4Y = currY + disMaxY
    frame = Frame(canvas,bg="green",cursor="target")
    frame.place(x=pnt1X,y=pnt1Y,width=(disOriginX + disMaxX),height=(disOriginY + disMaxY))
    if currButton == "textbox":
        TextArea = Text(frame,wrap=WORD,font=("Courier", 14),tabs="1c")
        TextArea.place(x=lineThick,y=lineThick,width=(disOriginX + disMaxX)-2*lineThick,height=(disOriginY + disMaxY)-2*lineThick)
        TextArea.insert("end",stringNote)
        stringNote = ""
        canvas.unbind("<ButtonRelease-1>")
        canvas.bind("<ButtonRelease-1>", textboxPoints2)
    elif currButton == "image":
        if filename != "":
            temp_img = Image.open(filename)
            temp_img = temp_img.resize(((disOriginX + disMaxX)-int(2.5*lineThick),(disOriginY + disMaxY)-int(2.5*lineThick)),Image.ANTIALIAS)
            img = ImageTk.PhotoImage(temp_img)
            imgPanel = Label(frame, image = img)
            imgPanel.image = img
            imgPanel.place(x=lineThick,y=lineThick)
            if img not in imageDict:
                imageDict[img] = filename
            canvas.unbind("<ButtonRelease-1>")
            canvas.bind("<ButtonRelease-1>", addImage)
################################################################################################
    frameMidX = pnt1X + ((pnt3X-pnt1X)/2)
    frameMidY = pnt1Y + ((pnt3Y-pnt1Y)/2)
    if savelistpos != None:  
        frameToFrames[frame] = savelistpos
        for frames in framelist[savelistpos]:
            #adding new frame to the framelists of the other frames
            line_id2 = canvas.create_line(0,0,0,0,width=lineThick, fill='black')
            connectedMidX = frames.winfo_x()+(frames.winfo_width()/2)
            connectedMidY = frames.winfo_y()+(frames.winfo_height()/2)
            canvas.coords(line_id2,frameMidX,frameMidY,connectedMidX,connectedMidY)
            lineList[savelistpos].append(line_id2)
            if frames in frameToFrames:
                framelist[frameToFrames[frames]].append(frame)
                lineList[frameToFrames[frames]].append(line_id2)
        savelistpos = None
        #print(framelist)
 ######################################################################################################
    canvas.delete(line_id)
    line_id = canvas.create_line(0,0,0,0,width=lineThick, fill='green')
    frame.bind("<Button-1>",clickBorder)
    canvas.unbind("<B1-Motion>")
    canvas.bind("<B1-Motion>", outlineTextBox)

def clickBorder(event):
    global stringNote
    global TextArea
    global mouseXclick
    global mouseYclick
    global line_id
    global disOriginX 
    global disOriginY
    global disMaxX
    global disMaxY
    global currButton
    global textbox
    global label
    global imageDict
    global filename
    global frameToFrames
    global framelist
    global savelistpos
    global lineList
    text = event.widget.winfo_children()
    textarea = text[0]
    if currButton == "textbox":
        if text[0].winfo_class() == "Text":
            stringNote = textarea.get("1.0","end-1c")
####################################################################################################
#delete the original frame from the lists that say its connected to
            if event.widget in frameToFrames:
                savelistpos = frameToFrames[event.widget]
            if savelistpos != None:
                for lines in lineList[savelistpos]:
                    for lists in lineList:
                        canvas.delete(lines)
            for lists in framelist:
                if event.widget in lists:
                    lists.remove(event.widget)
    #print(framelist)
#####################################################################################################
        else:
            return None
    if currButton == "image":
        if text[0].winfo_class() == "Text":
            return None
        else:
            img = text[0].image
            filename = imageDict[img]
####################################################################################################
#delete the original frame from the lists that say its connected to
            if event.widget in frameToFrames:
                savelistpos = frameToFrames[event.widget]
            if savelistpos != None:
                for lines in lineList[savelistpos]:
                    for lists in lineList:
                        canvas.delete(lines)
            for lists in framelist:
                if event.widget in lists:
                    lists.remove(event.widget)
    #print(framelist)
#####################################################################################################
    frameWidth = event.widget.winfo_width()
    frameHeight = event.widget.winfo_height()
    if event.x <= lineThick and event.y <= lineThick: #TOPLEFTCORNER
        mouseXclick = frameWidth + event.widget.winfo_x()
        mouseYclick = frameHeight + event.widget.winfo_y()
        event.widget.destroy()
        canvas.itemconfig(line_id, fill='green')    
    elif event.x <=lineThick and event.y >= (frameHeight-lineThick): #BOTTOMLEFT CORNER
        mouseXclick = frameWidth + event.widget.winfo_x()
        mouseYclick = event.widget.winfo_y()
        event.widget.destroy()
        canvas.itemconfig(line_id, fill='green')
    elif event.x >= (frameWidth - lineThick) and event.y <= lineThick:    #TOPRIGHT CORNER
        mouseXclick = event.widget.winfo_x()
        mouseYclick = frameHeight + event.widget.winfo_y()
        event.widget.destroy()
        canvas.itemconfig(line_id, fill='green')
    elif event.x >= (frameWidth - lineThick) and event.y >(frameHeight-lineThick): #BOTTOMRIGHT CORNER
        mouseXclick = event.widget.winfo_x()
        mouseYclick = event.widget.winfo_y()
        event.widget.destroy()
        canvas.itemconfig(line_id, fill='green')
    else:
        disOriginX = event.x
        disOriginY = event.y
        disMaxX = frameWidth - disOriginX
        disMaxY = frameHeight - disOriginY
        event.widget.destroy()
        canvas.itemconfig(line_id, fill='green')
        canvas.unbind("<B1-Motion>")
        canvas.unbind("<ButtonRelease-1>")
        canvas.bind("<B1-Motion>", moveTextBox)
        canvas.bind("<ButtonRelease-1>", stopTextBox)
    
def textboxPoints2(event):
    global mouseXrelease
    global mouseYrelease
    global textboxWidth
    global textboxHeight
    global line_id
    global frame
    global stringNote
    global TextArea
    global frameToFrames
    global savelistpos
    global lineList
    mouseXrelease = event.x
    mouseYrelease = event.y
    textboxWidth = mouseXrelease-mouseXclick
    textboxHeight = mouseYrelease-mouseYclick
    if textboxWidth < 0 and textboxHeight > 0:
        frame = Frame(canvas,bg="green",cursor="target")
        frame.place(x=mouseXrelease,y=mouseYclick,width=(-textboxWidth),height=textboxHeight)
        frameMidX = mouseXrelease + abs(textboxWidth/2)
        frameMidY = mouseYclick + abs(textboxHeight/2)

        TextArea = Text(frame,wrap=WORD,font=("Courier", 14),tabs="1c")
        TextArea.place(x=lineThick,y=lineThick,width=-(textboxWidth)-2*lineThick,height=textboxHeight-2*blineThick)
        TextArea.insert("end",stringNote)
    elif textboxWidth < 0 and textboxHeight < 0:
        frame = Frame(canvas,bg="green",cursor="target")
        frame.place(x=mouseXrelease,y=mouseYrelease,width=(-textboxWidth),height=(-textboxHeight))
        frameMidX = mouseXrelease + abs(textboxWidth/2)
        frameMidY = mouseYrelease + abs(textboxHeight/2)

        TextArea = Text(frame,wrap=WORD,font=("Courier", 14),tabs="1c")
        TextArea.place(x=lineThick,y=lineThick,width=-(textboxWidth)-2*lineThick,height=-(textboxHeight)-2*lineThick)
        TextArea.insert("end",stringNote)
    elif textboxWidth > 0 and textboxHeight < 0:
        frame = Frame(canvas,bg="green",cursor="target")
        frame.place(x=mouseXclick,y=mouseYrelease,width=(textboxWidth),height=(-textboxHeight))
        frameMidX = mouseXclick + abs(textboxWidth/2)
        frameMidY = mouseYrelease + abs(textboxHeight/2)

        TextArea = Text(frame,wrap=WORD,font=("Courier", 14),tabs="1c")
        TextArea.place(x=lineThick,y=lineThick,width=textboxWidth-2*lineThick,height=-(textboxHeight)-2*lineThick)
        TextArea.insert("end",stringNote)
    elif textboxWidth > 0 and textboxHeight > 0:
        frame = Frame(canvas,bg="green",cursor="target")
        frame.place(x=mouseXclick,y=mouseYclick,width=(textboxWidth),height=(textboxHeight))
        frameMidX = mouseXclick + abs(textboxWidth/2)
        frameMidY = mouseYclick + abs(textboxHeight/2)

        TextArea = Text(frame,wrap=WORD,font=("Courier", 14),tabs="1c")
        TextArea.place(x=lineThick,y=lineThick,width=textboxWidth-2*lineThick,height=textboxHeight-2*lineThick)
        TextArea.insert("end",stringNote)
    frame.bind("<Button-1>",clickBorder)
  ################################################################################################
    if savelistpos != None:  
        frameToFrames[frame] = savelistpos
        for frames in framelist[savelistpos]:
            #adding new frame to the framelists of the other frames
            line_id2 = canvas.create_line(0,0,0,0,width=lineThick, fill='black')
            connectedMidX = frames.winfo_x()+(frames.winfo_width()/2)
            connectedMidY = frames.winfo_y()+(frames.winfo_height()/2)
            canvas.coords(line_id2,frameMidX,frameMidY,connectedMidX,connectedMidY)
            lineList[savelistpos].append(line_id2)
            if frames in frameToFrames:
                framelist[frameToFrames[frames]].append(frame)
                lineList[frameToFrames[frames]].append(line_id2)
        savelistpos = None
        #print(framelist)
 ######################################################################################################
    canvas.delete(line_id)
    line_id = canvas.create_line(0,0,0,0,width=lineThick, fill='green')
    stringNote = ""
    #line_id2 = canvas.create_line(0,0,0,0,width=lineThick, fill='black')


def outlineTextBox(event):
    canvas.coords(line_id,mouseXclick,mouseYclick,event.x,mouseYclick,event.x,event.y,mouseXclick,event.y,mouseXclick,mouseYclick)

def connectFrames(event):
    global frame1
    global frame2
    global frameToFrames
    global framelist
    global linesList
    if frame1 == None: #if frame1 is empty, set it to the frame being clicked
        frame1 = event.widget
        frame1.configure(bg="brown")
        return None
    elif frame1 != None and frame2 == None: #else if frame2 is empty, then set that
        frame2 = event.widget
        frame.configure(bg="brown")
    if frame1 == frame2: #if both aren't empty, check if both are the same value, if same, dont draw line
        frame1.configure(bg="green")
        frame1 = None
        frame2 = None
        return None
    else: # if both aren't empty and both aren't same value, then draw line
########################################################################################################################
        #description of chunk: 
        #there is a dict connecting each frame to an index, this index belongs to a list that the frame is assigned to 
        #containing all the other frames it's connected to(this is disgusting code, i shouldve just used OOP)
        line_id2 = canvas.create_line(0,0,0,0,width=lineThick, fill='black')   
        if frame1 not in frameToFrames:
            #frames
            framelist.append([])
            frameToFrames[frame1] = len(framelist) - 1
            frameListPos = frameToFrames[frame1]
            framelist[frameListPos].append(frame2)
            #lines
            lineList.append([])
            lineList[frameListPos].append(line_id2)
        else:
            frameListPos = frameToFrames[frame1]
            framelist[frameListPos].append(frame2)
            #lines
            lineList[frameListPos].append(line_id2)

        if frame2 not in frameToFrames:
            framelist.append([])
            frameToFrames[frame2] = len(framelist) - 1
            frameListPos = frameToFrames[frame2]
            framelist[frameListPos].append(frame1)
            #lines
            lineList.append([])
            lineList[frameListPos].append(line_id2)
        else:
            frameListPos = frameToFrames[frame2]
            framelist[frameListPos].append(frame1)
            #lines
            lineList[frameListPos].append(line_id2)
        #print(frameToFrames)
        #print(framelist)
#########################################################################################################################
        #print(linesDict)
        pnt1X = frame1.winfo_x()
        pnt1Y = frame1.winfo_y()
        pnt2X = frame2.winfo_x()
        pnt2Y = frame2.winfo_y()
        midPnt1X = pnt1X + (frame1.winfo_width()/2)
        midPnt1Y = pnt1Y + (frame1.winfo_height()/2)
        midPnt2X = pnt2X + (frame2.winfo_width()/2)
        midPnt2Y = pnt2Y + (frame2.winfo_height()/2)
        canvas.coords(line_id2,midPnt1X,midPnt1Y,midPnt2X,midPnt2Y)
        #for lines in lineList:
            #if line_id2 in lines:
                #canvas.coords(line_id2,midPnt1X,midPnt1Y,midPnt2X,midPnt2Y)

        allFrames = canvas.winfo_children()
        for frames in allFrames:
            frames.configure(bg="green")
        frame1 = None
        frame2 = None 
    
def moveLine(event):
    canvas.coords(line_id2,mouseXclick,mouseYclick,event.x,event.y)

def addImage(event):
    global mouseXclick
    global mouseYclick
    global line_id
    global currButton
    global alreadyOpenFile
    global filename
    global frame
    global frameToFrames
    global framelist
    global lineList
    global savelistpos
    currButton = "image"
    canvas.delete(line_id)
    line_id = canvas.create_line(0,0,0,0,width=lineThick, fill='green')
    imageWidth = event.x - mouseXclick
    imageHeight = event.y - mouseYclick
    if alreadyOpenFile == False:
        filename = askopenfilename(initialdir = "/",title = "Select file",filetypes = (("jpeg files","*.jpg"),("png files","*.png*")))
        alreadyOpenFile = True    
    if filename == "":
        return None
    if imageWidth < 0 and imageHeight > 0:
        imageWidth = abs(imageWidth)
        imageHeight = abs(imageHeight)
        frame = Frame(canvas,bg="green",cursor="target")
        frame.place(x=event.x,y=mouseYclick,width=imageWidth,height=imageHeight)
        frameMidX = event.x + (imageWidth/2)
        frameMidY = mouseYclick + (imageHeight/2)

        temp_img = Image.open(filename)
        temp_img = temp_img.resize((imageWidth-int(2.5*lineThick),imageHeight-int(2.5*lineThick)),Image.ANTIALIAS)
        img = ImageTk.PhotoImage(temp_img)
        imgPanel = Label(frame, image = img)
        imgPanel.image = img
        imgPanel.place(x=lineThick,y=lineThick)
    elif imageWidth < 0 and imageHeight < 0:
        imageWidth = abs(imageWidth)
        imageHeight = abs(imageHeight)
        frame = Frame(canvas,bg="green",cursor="target")
        frame.place(x=event.x,y=event.y,width=imageWidth,height=imageHeight)
        frameMidX = event.x + (imageWidth/2)
        frameMidY = event.y + (imageHeight/2)

        temp_img = Image.open(filename)
        temp_img = temp_img.resize((imageWidth-int(2.5*lineThick),imageHeight-int(2.5*lineThick)),Image.ANTIALIAS)
        img = ImageTk.PhotoImage(temp_img)
        imgPanel = Label(frame, image = img)
        imgPanel.image = img
        imgPanel.place(x=lineThick,y=lineThick)
    elif imageWidth > 0 and imageHeight < 0:
        imageWidth = abs(imageWidth)
        imageHeight = abs(imageHeight)
        frame = Frame(canvas,bg="green",cursor="target")
        frame.place(x=mouseXclick,y=event.y,width=(imageWidth),height=imageHeight)
        frameMidX = mouseXclick + (imageWidth/2)
        frameMidY = event.y + (imageHeight/2)

        temp_img = Image.open(filename)
        temp_img = temp_img.resize((imageWidth-int(2.5*lineThick),imageHeight-int(2.5*lineThick)),Image.ANTIALIAS)
        img = ImageTk.PhotoImage(temp_img)
        imgPanel = Label(frame, image = img)
        imgPanel.image = img
        imgPanel.place(x=lineThick,y=lineThick)
    elif imageWidth > 0 and imageHeight > 0:
        imageWidth = abs(imageWidth)
        imageHeight = abs(imageHeight)
        frame = Frame(canvas,bg="green",cursor="target")
        frame.place(x=mouseXclick,y=mouseYclick,width=(imageWidth),height=(imageHeight))
        frameMidX = mouseXclick + (imageWidth/2)
        frameMidY = mouseYclick + (imageHeight/2)

        temp_img = Image.open(filename)
        temp_img = temp_img.resize((imageWidth-int(2.5*lineThick),imageHeight-int(2.5*lineThick)),Image.ANTIALIAS)
        img = ImageTk.PhotoImage(temp_img)
        imgPanel = Label(frame, image = img)
        imgPanel.image = img
        imgPanel.place(x=lineThick,y=lineThick)
    if img not in imageDict:
        imageDict[img] = filename
    #print(imageDict)
################################################################################################
    if savelistpos != None:  
        frameToFrames[frame] = savelistpos
        for frames in framelist[savelistpos]:
            #adding new frame to the framelists of the other frames
            line_id2 = canvas.create_line(0,0,0,0,width=lineThick, fill='black')
            connectedMidX = frames.winfo_x()+(frames.winfo_width()/2)
            connectedMidY = frames.winfo_y()+(frames.winfo_height()/2)
            canvas.coords(line_id2,frameMidX,frameMidY,connectedMidX,connectedMidY)
            lineList[savelistpos].append(line_id2)
            if frames in frameToFrames:
                framelist[frameToFrames[frames]].append(frame)
                lineList[frameToFrames[frames]].append(line_id2)
        savelistpos = None
        #print(framelist)
######################################################################################################
    frame.bind("<Button-1>",clickBorder)
    canvas.delete(line_id)
    line_id = canvas.create_line(0,0,0,0,width=lineThick, fill='green')

# def HighlightSelected(event):
#     #print("hi")
#     allFrames = canvas.winfo_children()
#     #rint(allFrames)
#     for frames in allFrames:
#         text = frames.winfo_children()
#         #print(text)
#         if len(text) > 0:
#             if text[0].winfo_class() == "Text":
#                 selectedText = text[0].selection_get()
#                 #print(selectedText)
#                 fullText = text[0].get("1.0","end-1c")
#                 firstIndex = fullText.find(selectedText)
#                 lastIndex = len(selectedText)
#                 #print(lastIndex)
#                 #print(firstIndex)
#                 text[0].tag_add("highlight", "1.{}".format(firstIndex),"1.{}".format(lastIndex))
#                 text[0].tag_config("highlight", foreground="black",background="yellow")
    
def createTextBox(button):
    global currButton
    global frame1
    global frame2
    currButton = "textbox" 
    changeButtonColor(button, "red")
    canvas.unbind("<Button-1>")
    canvas.unbind("<B1-Motion>")
    canvas.unbind("<ButtonRelease-1>")
    canvas.bind("<Button-1>", textboxPoints1)
    canvas.bind("<B1-Motion>", outlineTextBox)
    canvas.bind("<ButtonRelease-1>", textboxPoints2)
    #main.bind("<Control-e>", HighlightSelected)
    allFrames = canvas.winfo_children()
    for frames in allFrames:
        frames.bind("<Button-1>",clickBorder)
        frames.configure(bg="green")
        frame1 = None
        frame2 = None 
def drawLine(button):
    changeButtonColor(button, "red")   
    allFrames = canvas.winfo_children()
    for frames in allFrames:
        frames.unbind("<Button-1>")
        frames.unbind("<B1-Motion>")
        frames.unbind("<ButtonRelease-1>")
        frames.bind("<Button-1>",connectFrames)
    canvas.unbind("<Button-1>")
    canvas.unbind("<B1-Motion>")
    canvas.unbind("<ButtonRelease-1>")

def drawImage(button):
    global currButton
    global frame1
    global frame2
    changeButtonColor(button, "red")
    currButton = "image"
    canvas.unbind("<Button-1>")
    canvas.unbind("<B1-Motion>")
    canvas.unbind("<ButtonRelease-1>")
    canvas.bind("<Button-1>", textboxPoints1)
    canvas.bind("<B1-Motion>", outlineTextBox)
    canvas.bind("<ButtonRelease-1>",addImage)
    allFrames = canvas.winfo_children()
    for frames in allFrames:
        frames.bind("<Button-1>",clickBorder)
        frames.configure(bg="green")
        frame1 = None
        frame2 = None 

canvas = Canvas(main, bg='white',highlightthickness=1,highlightbackground="lightgray")
frame = Frame(canvas,bg="red")
button1 = Button(main, text="LINE", fg="black",bg = "lightgray",cursor="target", command= lambda: drawLine(button1))
button2 = Button(main, text="TEXTBOX", fg="black",bg = "lightgray",cursor="target", command= lambda: createTextBox(button2))
button3 = Button(main, text="SAVE", fg="black",bg = "lightgray",cursor="target", command= lambda: Save(button3))
button4 = Button(main, text="ADD IMAGE", fg="black",bg = "lightgray",cursor="target", command= lambda: drawImage(button4))

def changeButtonColor(button, color):
    button.configure(bg = color)
    if(button != button1):
        button1.configure(bg = "lightgray")
    if(button != button2):
        button2.configure(bg = "lightgray")
    if(button != button3):
        button3.configure(bg = "lightgray")
    if(button != button4):
        button4.configure(bg = "lightgray")
#button6 = Button(main, text="CHANGE COLOR", fg="black", command=drawImage)
#execution 
canvas.place(x=0,y=100,width=int(screensize[0]),height=int(screensize[1])-100)
button1.place(x=100,y=25,width=100,height=50)
button2.place(x=200,y=25,width=100,height=50)
button3.place(x=300,y=25,width=100,height=50)
button4.place(x=400,y=25,width=100,height=50)
#button5.place(x=0,y=150,width=540,height=20)
main.mainloop()




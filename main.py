import asyncio
import math
import random
from enum import Enum
from lerp import *
from dataclasses import dataclass
#UI
import customtkinter as ctk
#PDF
import pymupdf as ppdf
#FILES
import shutil
import os
import sys
from dotenv import load_dotenv, set_key
import pdf
from PIL import Image, ImageTk


BASE_PATH = ""
if getattr(sys, 'frozen', False):
    # Running as compiled exe
    BASE_PATH = os.path.dirname(sys.executable)
else:
    # Running as normal python script
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))

def PathFilter(path: str):
    newPath = path
    if newPath[0] == ".":
        newPath = newPath.replace(".", BASE_PATH, count=1)
    return newPath


print("Executable path:", BASE_PATH)
pdf.TEMPLATE_PATH = PathFilter(pdf.TEMPLATE_PATH)
print(pdf.TEMPLATE_PATH)


class Completion(Enum):
    A = "a"
    B = "b"
    C = "c"

@dataclass
class TaskDataWidgets:
    linkButton: ctk.CTkButton | None =              None
    linkText: ctk.CTkLabel | None =                 None
    saveButton: ctk.CTkButton | None =              None
    completionComboBox: ctk.CTkComboBox | None =    None
    uiColor: str | None =                           None

@dataclass
class TaskData():
    name: str
    imagePath: str
    completion: Completion
    rotation: int
    childIndex: int
    parentIndex: int
    widgetReference: TaskDataWidgets
    widgetList: list[ctk.CTkBaseClass]
    hasBeenDeleted: bool



#region ConfigData
isConfigFolderPath =    [True,  True,   False,  False,  False,  False,  False]
isConfigNumber =        [False, False,  True,   True,   True,   False,  False]
isConfigBool =          [False, False,  False,  False,  False,  True,   True]
@dataclass
class Config:
    image_path: str = ""
    output_path: str = ""
    left_right_padding: str = ""
    top_padding: str = ""
    bottom_padding: str = ""
    delete_image_files: str = ""
    render_textname: str = ""


#endregion
#region config save and load
load_dotenv(PathFilter("./config.env"))



config = Config()

def LoadConfig():
    for var in vars(config):
        setattr(config, var, os.getenv(var))



def SaveConfig():
    print(config)
    for var in vars(config):
        set_key(PathFilter("./config.env"), var, getattr(config, var))


def RenderIndicatorForText(textIndicator, label: ctk.CTkLabel, colorIndicator="red", returnToPreviousText=True):
    pText = label._text
    pColor = label._text_color
    label.configure(text=textIndicator,text_color=colorIndicator)
    if returnToPreviousText:
        window.after(1200, lambda t=pText, c=pColor: label.configure(text=t, text_color=c))
    else:
        window.after(1200, lambda: label.configure(text="", text_color=""))
    

LoadConfig()
#endregion


def scale_to_fit(width: float, height: float, max_width: float, max_height: float) -> tuple[float, float]:
    scale = min(max_width / width, max_height / height)
    return width * scale, height * scale

def SavePdf(task_: TaskData):

    src = ppdf.open(pdf.TEMPLATE_PATH)
    doc = ppdf.open(pdf.TEMPLATE_PATH)
    

    taskList = [task_]
    while taskList[-1].childIndex != -1:
        doc.insert_pdf(src, from_page=0, to_page=0)
        taskList.append(taskData[taskList[-1].childIndex])
    
    for i, task in enumerate(taskList):
        
        if task.hasBeenDeleted:
            continue

        image_path = task.imagePath    
        
        page = doc[i]

        img = Image.open(image_path)
        

        # width = page.rect.width-int(config.image_padding_right)
        # rect = pdf.CreateRatioRect(image_path, int(config.image_padding), width, int(config.padding_top)+20)

        imgWidth, imgHeight = scale_to_fit(img.width, img.height, page.rect.width-int(config.left_right_padding)*2, page.rect.height-float(config.top_padding)-int(config.bottom_padding)-20)

        rect = pdf.CreateRatioRect(image_path, page.rect.width/2-imgWidth/2, page.rect.width/2+imgWidth/2, int(config.top_padding)+20)


        page.insert_image(rect, filename=image_path, rotate=task.rotation*90)
        if config.render_textname == "1":
            page.insert_text(ppdf.Point(25, int(config.top_padding)), task_.name)

        img.close()
        if config.delete_image_files == "1":
            try:
                os.remove(task.imagePath)
            except Exception as e:
                print(e)
            taskData[i].hasBeenDeleted = True

    name = task_.name+task_.completion.value+".pdf"
    print("saved:", name)
    doc.save(os.path.join(PathFilter(config.output_path), name))
    doc.close()

def GetPdfWidthAndHeight():
    doc = ppdf.open(pdf.TEMPLATE_PATH)
    page = doc[0]
    return (page.rect.width, page.rect.height)



ctk.set_default_color_theme("dark-blue")
ctk.set_appearance_mode("dark")


window = ctk.CTk()
window.geometry("1300x750")
window.title("MAM")


window.iconbitmap(PathFilter("./icon.ico"))

#window.iconphoto(True, icon)
#window.resizable(False, False)


window.grid_columnconfigure(0, weight=1)
window.grid_columnconfigure(1, weight=1)
window.grid_rowconfigure(0, weight=1)

configFrame = ctk.CTkScrollableFrame(window)
#configFrame.pack(pady=20, padx=20, fill="x", expand=True, side="left")
configFrame.grid(row=0, column=0, sticky="nwes", padx=5, pady=5)

configFrame.grid_columnconfigure(1, weight=3)
configFrame.grid_columnconfigure(2, weight=0)
#configFrame.grid_rowconfigure(2, weight=2)

# ctk.CTkLabel(configFrame, text="image_folder_path").pack(padx=10, pady=0, side="left")
# image_path_var = ctk.StringVar(value=config.image_path)
# ctk.CTkEntry(configFrame, placeholder_text="Path", textvariable=image_path_var).pack(padx=10, pady=0, side="right")

# ctk.CTkLabel(configFrame, text="sadasasdasdasd").pack(padx=10, pady=0, side="left")
# ctk.CTkEntry(configFrame, placeholder_text="testy").pack(padx=10, pady=0, side="right")

configVariables = vars(config)
configTextVariables: list[ctk.StringVar] = []

def directoryButton(i):
    directory = ctk.filedialog.askdirectory(initialdir=PathFilter(configTextVariables[i].get()))
    if directory != "":
        configTextVariables[i].set(directory)

for i, var in enumerate(configVariables):
    ctk.CTkLabel(configFrame, text=var)\
        .grid(row=i, column=0, padx=10, pady=5, sticky="w")
    configTextVariables.append(ctk.StringVar(value=getattr(config, var)))
    #image_path_var = ctk.StringVar(value=config.image_path)
    if isConfigBool[i]:
        checkBox = ctk.CTkCheckBox(configFrame, text="")
        checkBox.grid(row=i, column=1, padx=0, pady=5, sticky="ew")
        if configTextVariables[i].get() == "1":
            checkBox.select()
        checkBox.configure(command=lambda widget=checkBox, localI=i: configTextVariables[localI].set(str(widget.get())))
    else:
        ctk.CTkEntry(configFrame, placeholder_text=getattr(config, var), textvariable=configTextVariables[i])\
            .grid(row=i, column=1, padx=0, pady=5, sticky="ew")
    if isConfigFolderPath[i] and not isConfigNumber[i]:
        ctk.CTkButton(configFrame, text="📁", width=50, font=("", 20), command=lambda localI=i: directoryButton(localI))\
            .grid(row=i, column=2, pady=5, padx=5)


def PdfChangeButton():
    pdfPath = ctk.filedialog.askopenfilename(filetypes=[("Portable Document Format", ".pdf")])
    if pdfPath == "":
        return
    destination = PathFilter("./template.pdf")
    shutil.copy2(pdfPath, destination)
    
currentRow = len(configVariables)

ctk.CTkLabel(configFrame, text="change template")\
    .grid(row=currentRow, column=0, padx=10, pady=5, sticky="w")
ctk.CTkButton(configFrame, text="📁", width=50, font=("", 20), command=PdfChangeButton)\
    .grid(row=currentRow, column=1, pady=5, padx=5, sticky="w")

    



saveConfigButtonIndicator = ctk.CTkLabel(configFrame, text="")
saveConfigButtonIndicator.grid(row=len(configVariables)+2, column=0, padx=10, pady=5, sticky="n")
def SaveConfigButton():
    RenderIndicatorForText("Saved Settings", saveConfigButtonIndicator)
    print("saved config.")
    for i, var in enumerate(configVariables):
        if isConfigNumber[i]:
            try:
                float(configTextVariables[i].get())
                setattr(config, var, str(int(configTextVariables[i].get())))
            except:
                setattr(config, var, "0")
                configTextVariables[i].set("0")
        elif isConfigBool[i]:
            setattr(config, var, configTextVariables[i].get())
        else:
            setattr(config, var, configTextVariables[i].get())
    SaveConfig()
ctk.CTkButton(configFrame, text="Save Settings", command=SaveConfigButton)\
    .grid(row=len(configVariables)+1, column=0, padx=10, pady=12)



def RefreshButton():
    Refresh()
ctk.CTkButton(configFrame, text="⟲→", width=50, font=("", 20), command=RefreshButton)\
    .grid(row=len(configVariables)+1, column=1, padx=10, pady=12, sticky="e")



configFrame.grid_rowconfigure(len(configVariables)+2, weight=1)
canvas = ctk.CTkCanvas(configFrame)
#canvas.config(width=100, height=300)
canvas.grid(row=len(configVariables)+2, column=1, sticky="nwe")



taskData: list[TaskData] = []
listFrame = ctk.CTkScrollableFrame(window)
listFrame.grid_columnconfigure(0, weight=1)
listFrame.grid(row=0, column=1, sticky="nwes", padx=5, pady=5)

image_extensions = [
  "jpg", "jpeg", "png", "gif", "webp", "svg", "avif", "apng", 
  "bmp", "ico", "tiff", "tif", "heic", "heif", "raw"
]

def Refresh():
    global taskData
    taskData = []
    for filename in os.listdir(PathFilter(config.image_path)):
        full_path = os.path.join(PathFilter(config.image_path), filename)
        if os.path.isfile(full_path):
            dotList = filename.split(".")
            if dotList.pop() not in image_extensions:
                continue
            name = ".".join(dotList)
            taskData.append(TaskData(name, full_path, Completion.A, 0, -1, -1, TaskDataWidgets(), [], False))
    
    CreateTaskList()


def DestroyTaskDatawidgets(i, iterateChildren = False):
    for widget in taskData[i].widgetList:
        widget.destroy()
    if taskData[i].childIndex != -1 and iterateChildren:
        DestroyTaskDatawidgets(taskData[i].childIndex)
        

def SavePdfButton(i, widgets: list[ctk.CTkBaseClass]):
    if taskData[i].parentIndex != -1:
        return
    SavePdf(taskData[i])
    if config.delete_image_files == "1":
        for widget in widgets:
            widget.destroy()
        if taskData[i].childIndex != -1:
            DestroyTaskDatawidgets(taskData[i].childIndex, True)
    else:
        RenderIndicatorForText("Saved.", widgets[0])
        

def CompletionChanceCallback(choice, i):
    if choice == "A":
        taskData[i].completion = Completion.A
    elif choice == "B":
        taskData[i].completion = Completion.B
    elif choice == "C":
        taskData[i].completion = Completion.C
    else:
        print("WTF HOW DID YOU DO THIS. YOU FUCKED UP REALLY BAD MAN YOU HAVE A CURSE.")

def RotateTaskDataImage(task: TaskData):
    task.rotation = (task.rotation + 1) % 4
    CanvasUpdate(task)

randomColors = ["orange2", "DarkOrange2", "IndianRed1", "red2", "slateblue3", "cadetblue2", "LightBlue4", "plum1", "lawn green", "yellow"]
randomColorsAllowed = randomColors.copy()
def ResetRandomColors():
    global randomColorsAllowed
    randomColorsAllowed = randomColors.copy()
def GetRandomColor() -> str:
    return randomColorsAllowed.pop(random.randrange(len(randomColorsAllowed)))


def SetColorsInProgressLink(taskIndex):
    for i, task in enumerate(taskData):
            if i == taskIndex or task.childIndex != -1 or task.parentIndex != -1:
                continue
            assert task.widgetReference.linkButton is not None 
            task.widgetReference.linkButton.configure(fg_color="maroon1", hover_color="maroon3")

def SetColorsAfterLink():
    
    for task in taskData:
        if task.childIndex != -1:
            assert task.widgetReference.linkButton is not None 
            task.widgetReference.linkButton.configure(fg_color="gray4", hover_color="gray4")
            continue
        assert task.widgetReference.linkButton is not None 
        task.widgetReference.linkButton.configure(fg_color="purple1", hover_color="purple3")


linkingState = -1
def LinkButtonCallback(taskIndex):
    global linkingState
    #Start link
    if linkingState == -1 and taskData[taskIndex].childIndex == -1:
        linkingState = taskIndex
        txt = taskData[taskIndex].widgetReference.linkText._text
        if txt == "":
            taskData[taskIndex].widgetReference.linkText.configure(text="1")
        SetColorsInProgressLink(taskIndex)
    #Non possible link
    elif linkingState == taskIndex:
        if taskData[taskIndex].parentIndex == -1:
            taskData[taskIndex].widgetReference.linkText.configure(text="")
        linkingState = -1
        SetColorsAfterLink()
    #End link
    elif taskData[taskIndex].childIndex == -1:
        if taskData[taskIndex].parentIndex != -1:
            return
        taskData[linkingState].childIndex = taskIndex
        
        linkText = taskData[linkingState].widgetReference.linkText
        assert linkText is not None
        txt = linkText._text
        pNumber = int(txt)
        
        taskData[taskIndex].parentIndex = linkingState
        
        color = ""
        if taskData[linkingState].widgetReference.uiColor == None:
            color = GetRandomColor()
            print("color:", color)
        else:
            color = taskData[linkingState].widgetReference.uiColor
        taskData[taskIndex].widgetReference.uiColor = color
        taskData[linkingState].widgetReference.uiColor = color
        taskData[taskIndex].widgetReference.linkText.configure(text=str(pNumber+1), text_color=color)

        #assert taskData[linkingState].widgetReference.linkText is not None 
        linkText.configure(                                                         text_color=color)
        #taskData[linkingState].widgetReference.linkText.configure(                  text_color=color)
        taskData[taskIndex].widgetReference.saveButton.destroy()
        taskData[taskIndex].widgetReference.completionComboBox.destroy()
        

        SetColorsAfterLink()

        linkingState = -1
        

def SaveAllTaskData():
    for i, task in enumerate(taskData):
        SavePdfButton(i, taskData[i].widgetList)
    if config.delete_image_files == "1":
        listFrame.winfo_children()[-1].destroy()

def CreateTaskList():
    global linkingState
    linkingState = -1
    ResetRandomColors()
    for child in listFrame.winfo_children():
        child.destroy()
        
    for i, task in enumerate(taskData):
        label = ctk.CTkLabel(listFrame, text=task.name)
        label.grid(row=i, column=0, padx=10, pady=5, sticky="w")
        completion = ctk.CTkComboBox(listFrame, values=["A", "B", "C"], width=10, command=lambda choice, localI=i: CompletionChanceCallback(choice, localI))
        completion.grid(row=i, column=1, padx=10, pady=5, sticky="w")

        #pix = ppdf.Pixmap(taskData[i].imagePath)
        #img_width = pix.width
        #img_height = pix.height
        #aspect = img_height / img_width


        linkText = ctk.CTkLabel(listFrame, text="")
        linkText.grid(row=i, column=2, padx=10, pady=5, sticky="w")

        #maroon1 and maroon3 for second linking state⛓
        linkButton = ctk.CTkButton(listFrame, text="🔗", width=50, font=("", 20), fg_color="purple1", hover_color="purple3") 
        linkButton.configure(command=lambda localI=i: LinkButtonCallback(localI))
        linkButton.grid(row=i, column=3, pady=5, padx=5)


        #TODO rotation implementation
        #previewbutton = ctk.CTkButton(listFrame, text="⟳", width=50, font=("", 20), fg_color=("red" if aspect > 1 else "green"), hover_color=("darkred" if aspect > 1 else "darkgreen"))
        #previewbutton.configure(command=lambda localI=i: RotateTaskDataImage(taskData[localI]))
        #previewbutton.grid(row=i, column=2, pady=5, padx=5)

        previewbutton = ctk.CTkButton(listFrame, text="👁", width=50, font=("", 20), fg_color="green", hover_color="darkgreen")
        previewbutton.configure(command=lambda localI=i: CanvasUpdate(taskData[localI]))
        previewbutton.grid(row=i, column=4, pady=5, padx=5)

        

        savebutton = ctk.CTkButton(listFrame, text="💾", width=50, font=("", 20), fg_color="green", hover_color="darkgreen")
        savebutton.configure(command=lambda localI=i, widgets=[label,completion,savebutton,previewbutton,linkButton,linkText]: SavePdfButton(localI, widgets))
        savebutton.grid(row=i, column=5, pady=5, padx=5)

        taskData[i].widgetList = [label,completion,savebutton,previewbutton,linkButton,linkText]
        taskData[i].widgetReference.linkText            = linkText
        taskData[i].widgetReference.linkButton          = linkButton
        taskData[i].widgetReference.saveButton          = savebutton
        taskData[i].widgetReference.completionComboBox  = completion
    savebutton = ctk.CTkButton(listFrame, text="Save All", width=50, font=("", 20), fg_color="green", hover_color="darkgreen")
    savebutton.configure(command=SaveAllTaskData)
    savebutton.grid(row=len(taskData), column=0, pady=5, padx=5)







#configFrame.pack(pady=20, padx=20, fill="x", expand=True, side="right")




pdfWidth, pdfHeight = GetPdfWidthAndHeight()

def PTC(x):
    return remap(0, pdfWidth, 10, canvas.winfo_width()-10, x)

def PTCS(x):
    return remap(0, pdfWidth, 0, canvas.winfo_width()-20, x)

currentCanvasPdfDisplayed = None
currentCanvasImageDisplayed = None

def CanvasUpdate(task: TaskData):
    global currentCanvasImageDisplayed, currentCanvasPdfDisplayed


    ratio = pdfHeight / pdfWidth

    canvas.config(height=canvas.winfo_width()*ratio)

    canvas.delete("all")


    

    doc = ppdf.open(pdf.TEMPLATE_PATH)
    page = doc[0]
    if config.render_textname == "1":
        page.insert_text(ppdf.Point(25, int(config.top_padding)), task.name)
    pix = page.get_pixmap(matrix=ppdf.Matrix(1, 1))  # 1x resolution
    templateImg = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    #templateImg = templateImg.resize((int(p1[0] - p0[0]), int( (p1[0] - p0[0]) * ratio )))
    templateImg = templateImg.resize((int(canvas.winfo_width()-20), int((canvas.winfo_width()-20) * ratio )))
    currentCanvasPdfDisplayed = ImageTk.PhotoImage(templateImg)
    canvas.create_image(PTC(0), PTC(0), image=currentCanvasPdfDisplayed, anchor="nw")

    
    if task.imagePath == "":
        pass
        #canvas.create_rectangle(p0[0], p0[1], p1[0], p1[1], fill="darkred")
    else:
        imgData = Image.open(task.imagePath)
        imgData_width = imgData.width
        imgData_height = imgData.height


        width, height = scale_to_fit(imgData_width, imgData_height, (canvas.winfo_width()-20)-PTCS(float(config.left_right_padding)*2), PTCS(pdfHeight-float(config.top_padding)-float(config.bottom_padding)-20))

        imgData = imgData.resize((int(width), int(height)))




        #print(imgData.getpixel((0,0)))

        currentCanvasImageDisplayed = ImageTk.PhotoImage(imgData)
        #p1 = (p1[0], p0[1] + (p1[0] - p0[0])*aspect)
        #p0 = (0, 0) #testing coords
        #canvas.create_image(p0[0], p0[1], image=img)
        canvas.create_image(canvas.winfo_width()/2, PTC(float(config.top_padding)+20), image=currentCanvasImageDisplayed, anchor="n")

        imgData.close()

    doc.close()
    
    

    canvas.create_rectangle(PTC(0), PTC(0), PTC(pdfWidth), PTC(pdfHeight))





window.mainloop()
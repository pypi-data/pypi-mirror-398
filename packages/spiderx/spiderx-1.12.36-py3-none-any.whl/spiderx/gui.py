# encoding: utf-8
from tkinter import *
from tkinter import messagebox,ttk
import tkinter.font as tkFont
class gui_请求网页(Tk):
    def __init__(self,title='my program',width=500,height=400,resize=False):
        '''
        ui = window()
        ui.v_状态栏.set('hello')
        ui.v_文本说明.set('输入网址:')
        ui.run()
        '''
        self.app=Tk()
        self.v_输入框=StringVar()
        self.v_文本说明=StringVar()
        self.v_文本说明.set('输入网址:')
        self.v_状态栏=StringVar()
        self.app.title(title)
        if not resize:
            self.app.resizable(False,False)
        self.app.geometry(f"{width}x{height}+{int(self.app.winfo_screenwidth()/2-width/2)}+{int(self.app.winfo_screenheight()/2-height/2)}" )
        self.文本字体 = tkFont.Font(family='微软雅黑', size=10, )
        frame1=Frame(self.app)
        frame1.pack(fill=X)
        self.输入框=Entry(frame1,textvariable=self.v_输入框,font=self.文本字体)
        self.按钮=Button(frame1, text="确定", width=5, font=self.文本字体,bg='#99cccc')
        self.文字说明=Label(frame1, textvariable=self.v_文本说明, font=self.文本字体)
        self.文字说明.pack(side=LEFT,padx=5)
        self.输入框.pack(fill=X,side=LEFT,expand=1)
        self.按钮.pack(side=RIGHT, padx=5,pady=3)
        self.messagebox=messagebox

        self.文本框=Text(self.app, font=self.文本字体,height=1,width=1)
        self.文本框滚动条=Scrollbar()
        self.文本框滚动条.pack(side=RIGHT, fill=Y)
        self.文本框滚动条.config(command=self.文本框.yview)
        self.文本框.config(yscrollcommand=self.文本框滚动条.set)
        self.文本框.pack(side=TOP, fill=BOTH, expand=1,padx=3,pady=3)
        #状态栏
        statusbar = Label(self.app, textvariable=self.v_状态栏, bd=1, relief=GROOVE, anchor=W)
        statusbar.pack(side=BOTTOM, fill=X)
        self.app.protocol('WM_DELETE_WINDOW', self.close)
    def close(self):
        print('close')
        self.app.quit()
    def run(self):
        self.app.mainloop()
class gui_列表选择(Tk):
    def __init__(self,title='my program',width=800,height=600,resize=False):
        '''
        ui = window()
        ui.v_状态栏.set('hello')
        ui.v_文本说明.set('输入网址:')
        ui.run()
        '''
        self.app=Tk()
        self.messagebox=messagebox
        self.v_输入框=StringVar()
        self.v_文本说明=StringVar()
        self.v_文本说明.set('输入网址:')
        self.v_状态栏=StringVar()
        self.app.title(title)
        if not resize:
            self.app.resizable(False,False)
        self.app.geometry(f"{width}x{height}+{int(self.app.winfo_screenwidth()/2-width/2)}+{int(self.app.winfo_screenheight()/2-height/2)}" )
        self.文本字体 = tkFont.Font(family='微软雅黑', size=10, )
        frame1=Frame(self.app)
        frame1.pack(fill=X)
        self.文字说明=Label(frame1, textvariable=self.v_文本说明, font=self.文本字体)
        self.文字说明.pack(side=LEFT,padx=5)
        self.输入框=Entry(frame1,textvariable=self.v_输入框,font=self.文本字体)
        self.输入框.pack(fill=X, side=LEFT, expand=1)

        self.按钮_运行 = Button(frame1, text="运行", width=8, font=self.文本字体,bg='#99cccc')
        self.按钮_运行.pack(side=LEFT, padx=3,pady=3)
        self.按钮_运行2=Button(frame1, text="获取列表", width=8, font=self.文本字体,bg='#99cccc')
        self.按钮_运行2.pack(side=LEFT,padx=3,pady=3)

        frame2=Frame(self.app)
        frame2.pack(fill=BOTH,expand=1)
        self.列表=Listbox(frame2,width=35, selectmode=EXTENDED,font=self.文本字体)
        self.列表.pack(fill=Y,expand=0,side=LEFT)
        self.列表滚动条=Scrollbar(frame2)
        self.列表滚动条.pack(side=LEFT,fill=Y)
        self.列表滚动条.config(command=self.列表.yview)
        self.列表.config(yscrollcommand=self.列表滚动条.set)

        self.文本框=Text(frame2, font=self.文本字体,height=1,width=1)
        self.文本框滚动条=Scrollbar(frame2)
        self.文本框滚动条.pack(side=RIGHT, fill=Y)
        self.文本框滚动条.config(command=self.文本框.yview)
        self.文本框.config(yscrollcommand=self.文本框滚动条.set)
        self.文本框.pack(side=LEFT, fill=BOTH, expand=1)
        #状态栏
        statusbar = Label(self.app, textvariable=self.v_状态栏, bd=1, relief=SUNKEN, anchor=W)
        statusbar.pack(side=BOTTOM, fill=X)
        self.app.protocol('WM_DELETE_WINDOW', self.close)
    def close(self):
        print('close')
        self.app.quit()
    def run(self):
        self.app.mainloop()
class gui_表格(Tk):
    def __init__(self,title='my program',width=500,height=600,resize=False):
        '''
        ui = window()
        ui.v_状态栏.set('hello')
        ui.v_文本说明.set('输入网址:')
        ui.run()
        '''
        self.app=Tk()
        self.v_输入框=StringVar()
        self.v_文本说明=StringVar()
        self.v_文本说明.set('输入网址:')
        self.v_状态栏=StringVar()
        self.app.title(title)
        if not resize:
            self.app.resizable(False,False)
        self.app.geometry(f"{width}x{height}+{int(self.app.winfo_screenwidth()/2-width/2)}+{int(self.app.winfo_screenheight()/2-height/2)}" )
        self.文本字体 = tkFont.Font(family='微软雅黑', size=10, )
        self.frame1=Frame(self.app)
        self.frame1.pack(fill=X)
        self.输入框=Entry(self.frame1,textvariable=self.v_输入框,font=self.文本字体)
        self.按钮=Button(self.frame1, text="确定", width=5, font=self.文本字体,bg='#99cccc')
        self.文字说明=Label(self.frame1, textvariable=self.v_文本说明, font=self.文本字体)
        self.文字说明.pack(side=LEFT,padx=5)
        self.输入框.pack(fill=X,side=LEFT,expand=1)
        self.按钮.pack(side=RIGHT, padx=5,pady=3)
        self.messagebox=messagebox

        self.frame2=Frame(self.app)
        self.frame2.pack(fill=BOTH,expand=1,padx=3)
        self.columns = ['城市', "城市", "城市", "城市", "城市"]
        self.表格=ttk.Treeview(self.frame2,columns=self.columns,selectmode=BROWSE)#show="headings" 不显示图标栏 #0
        self.表格.tag_configure("eee", background='blue',foreground="yellow")
        self.表格.pack(fill=BOTH,side=LEFT,expand=1)
        self.表格滚动条 = Scrollbar(self.frame2)
        self.表格滚动条.pack(side=RIGHT, fill=Y)
        self.表格滚动条.config(command=self.表格.yview)
        self.表格.config(yscrollcommand=self.表格滚动条.set)
        self.load_table([[1,2,3,4,5],[1,2,3,4,5]])

        self.frame3=Frame(self.app)
        self.frame3.pack(fill=BOTH,expand=1,pady=3,padx=3)
        self.文本框=Text(self.frame3, font=self.文本字体,height=1,width=1)
        self.文本框滚动条=Scrollbar(self.frame3)
        self.文本框滚动条.pack(side=RIGHT, fill=Y)
        self.文本框滚动条.config(command=self.文本框.yview)
        self.文本框.config(yscrollcommand=self.文本框滚动条.set)
        self.文本框.pack(side=TOP, fill=BOTH, expand=1)
        #状态栏
        statusbar = Label(self.app, textvariable=self.v_状态栏, bd=1, relief=GROOVE, anchor=W)
        statusbar.pack(side=BOTTOM, fill=X)
        self.app.protocol('WM_DELETE_WINDOW', self.close)
    def load_table(self,data=[]):
        #data [[1,2,3,4,5],[1,2,3,4,5]]
        #建立栏图标
        columns=['ID']+self.columns
        for i in range(len(columns)):
            self.表格.heading(f'#{i}',text=columns[i])
        #格式化栏位
        for i in range(len(columns)):
            self.表格.column(f'#{i}',anchor=CENTER,width=50)
        #插入内容
        if data:
            for i,row in enumerate(data):
                if i%2==1:
                    self.表格.insert("",index=END,text=str(i),values=row)
                else:
                    self.表格.insert("", index=END, text=str(i), values=row, tags="eee")
    def close(self):
        print('close')
        self.app.quit()
    def run(self):
        self.app.mainloop()
if __name__ == '__main__':
    ui=gui_列表选择()
    ui.run()




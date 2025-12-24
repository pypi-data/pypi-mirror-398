import tkinter as tk
from tkinter.constants import BOTH, GROOVE, HORIZONTAL, LEFT, X


class app_settings():
    def __init__(self, app_title, app_name, dimx = 600, dimy = 400, main_bg = 'black', app_lbl_bg = 'tomato2',
        app_lbl_fg = 'white', app_lbl_font = 'Helvetica 20 bold', lbl_bg = 'black', lbl_fg = 'white',
        paddingx = 5, paddingy = 5, normal_font = 'Helvetica 12',
        ipaddingx = 5, ipaddingy = 5, ent_bg = 'mediumpurple3', ent_fg = 'white', but_bg = 'dodgerblue2',
        but_fg = 'white', btn_exit_bg_color = 'indian red', btn_exit_fg_color = 'white', resizable = False):
        self.dimx = dimx
        self.dimy = dimy
        self.app_title = app_title
        self.app_name = app_name
        self.main_window_bg_color = main_bg
        self.app_label_bg_color = app_lbl_bg
        self.app_label_fg_color = app_lbl_fg
        self.paddingx = paddingx = paddingx
        self.paddingy = paddingy = paddingy
        self.ipaddingx = ipaddingx = ipaddingx
        self.ipaddingy = ipaddingy = ipaddingy
        self.std_lable_bg_color = lbl_bg
        self.std_lable_fg_color = lbl_fg
        self.entry_bg_color = ent_bg
        self.entry_fg_color = ent_fg
        self.btn_bg_color = but_bg
        self.btn_fg_color = but_fg
        self.btn_exit_bg_color = btn_exit_bg_color
        self.btn_exit_fg_color = btn_exit_fg_color
        #fonts
        self.app_lable_font = app_lbl_font
        self.normal_font = normal_font
        self.resizable = resizable

class main_Window():
    def __init__(self, settings):
        self.settings = settings
        self.dimx = self.settings.dimx
        self.dimy = self.settings.dimy
        self.title = self.settings.app_title
        self.main_Window = tk.Tk()
        self.main_Window.title(self.settings.app_title)

        #setting window position
        window_width = self.settings.dimx
        window_height = self.settings.dimy
        screen_width = self.main_Window.winfo_screenwidth()
        screen_height = self.main_Window.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        self.main_Window.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

        self.main_Window.columnconfigure(0,weight = 1)

        #making window non resizable based on setting
        if self.settings.resizable == False:
            self.main_Window.resizable(False,False)

        #adjusting transparency
        # main_window.attributes('-alpha',0.75)

        #setting background
        self.main_Window.configure(bg=self.settings.main_window_bg_color)

    
    def start(self):
        self.main_Window.mainloop()

    def close(self):
        self.main_Window.destroy()

class main_frame(main_Window):
    def __init__(self, settings):
        # main_Window.__init__(self, settings)
        super().__init__(settings)
        # self.exit_func = main_Window.close
        self.settings = settings

        #setting master frame
        self.frame = frame(self.main_Window,0,0,self.settings.main_window_bg_color)
        self.frame.col_config(0,1)
   
        #label frame
        self.lbl_frame = frame(self.frame.frame,0,0,self.settings.main_window_bg_color)
        self.lbl_frame.col_config(0,1)
        self.main_lable = app_label(self.lbl_frame.frame,self.settings.app_name,0,0,self.settings)

        #buttons and content frame
        self.frm_master2 = frame(self.frame.frame,1,0,self.settings.main_window_bg_color)
        self.frm_master2.col_config(0,1)
        self.frm_master2.col_config(1,30)

        #button bar frame on left
        self.frm_btn_bar = frame(self.frm_master2.frame,0,0,self.settings.main_window_bg_color)

        # exit button
        self.btn_exit = button(self.frm_btn_bar.frame,'Exit',10,0,super().close,settings)
        self.btn_exit.change_color(self.settings.btn_exit_bg_color)

        #frame for application content
        self.frm_content = frame(self.frm_master2.frame,0,1,self.settings.main_window_bg_color)
        self.frm_content.col_config(0,1)
        self.frm_content.col_config(1,5)


class frame():
    def __init__(self, master, row, col, bg_color):
        self.master = master
        self.row = row
        self.col = col
        self.bg_color = bg_color
        self.frame = tk.Frame(self.master,background=self.bg_color)
        self.frame.columnconfigure(0,weight=1)
        self.frame.grid(row=self.row,column=self.col,sticky='nwe')

    def col_config(self,col_index, col_weight):
        self.frame.columnconfigure(col_index, weight = col_weight)

    def set_columnspan(self,cols):
        self.frame.grid(columnspan=cols)

    def frame_pack(self):
        self.frame.pack(expand=True,fill=X)
    
    def frame_grid(self):
        self.frame.grid(row=self.row,column=self.col,sticky='nwe')


class app_label():
    def __init__(self, master, txt, row, col,settings):
        self.master = master
        self.txt = txt
        self.row = row
        self.col = col
        self.settings = settings
        self.lbl = tk.Label(master=self.master, text=self.txt,bg=self.settings.app_label_bg_color,
            fg=self.settings.app_label_fg_color,relief=GROOVE,
            font=self.settings.app_lable_font)
        self.lbl.grid(row=self.row, column=self.col,sticky='nwe',ipady=self.settings.paddingy)


class button():
    def __init__(self, master, txt, row, col,func,settings):
        self.master = master
        self.txt = txt
        self.row = row
        self.col = col
        self.func = func
        self.settings = settings
        self.button = tk.Button(master=self.master, text=self.txt,bg=self.settings.btn_bg_color,
            fg=self.settings.btn_fg_color,relief=GROOVE,
            bd=0,compound=LEFT,height=2,width=10, command=self.func,
            font=self.settings.normal_font,border=4)
        self.button.grid(row=self.row, column=self.col,padx=(0,self.settings.paddingx),sticky='w')

    def change_color(self,color):
        self.button.configure(background=color)

class std_label():
    def __init__(self, master, txt, row, col, settings, stick):
        self.master = master
        self.txt = txt
        self.row = row
        self.col = col
        self.settings = settings
        self.stick = stick
        self.lbl = tk.Label(master=self.master, text=self.txt,bg=self.settings.std_lable_bg_color,
            fg=self.settings.std_lable_fg_color,relief=GROOVE,
            font=self.settings.normal_font)
        self.lbl.grid(row = self.row, column=self.col,ipadx=self.settings.ipaddingx,
            ipady=self.settings.ipaddingy, padx=self.settings.paddingx,
            pady=self.settings.paddingy,sticky=stick)

    def set_result(self, position, color, height, colspan):
        self.lbl.configure(height=height, bg=color,wraplength=200,justify='center')
        self.lbl.grid(sticky=position,ipadx=self.settings.ipaddingx,
            ipady=self.settings.ipaddingy,columnspan=colspan)
    
    def std_lable_updater(self, val):
        self.lbl['text']=val

    def col_span(self,cols):
        self.lbl.grid(columnspan= cols)
    
    def set_height(self, height_val):
        self.lbl.configure(height=height_val,wraplength=400, justify='center')
    
    def set_color(self, color):
        self.lbl.configure(bg=color)

    def set_width(self, width):
        self.lbl.configure(width= width)

    def set_alignment_left(self):
        self.lbl.configure(justify='left',anchor='w')
        # self.lbl.grid(ipadx=self.settings.ipaddingx+10)
    
    def set_position(self, position):
        self.lbl.grid(sticky=position)

    def check_if_exists(self):
        return self.lbl.winfo_exists()

    def get_val(self):
        return self.lbl['text']

class std_entry():
    def __init__(self,master,row,col,default_txt,settings, stick):
        self.master = master
        self.row = row
        self.col = col
        self.default_txt = default_txt
        self.settings = settings
        self.stick = stick
        self.entBox = tk.Entry(master=self.master, bg=self.settings.entry_bg_color,
            fg=self.settings.entry_fg_color,relief=GROOVE,
            font=self.settings.normal_font)
        self.entBox.grid(row = self.row, column=self.col,ipadx=self.settings.ipaddingx,
            ipady=self.settings.ipaddingy,sticky=stick,padx=self.settings.paddingx,
            pady=self.settings.paddingy)
        self.entBox.delete(0,tk.END)
        self.entBox.insert(0,self.default_txt)

    def set_width(self, width):
        self.entBox.configure(width=width)

    def get_val(self):
        return self.entBox.get()

    def set_defualt_text(self, default_text):
        self.entBox.delete(0,tk.END)
        self.entBox.insert(0,default_text)
    
    def set_position(self, position):
        self.entBox.grid(sticky=position)

class app_console():
    def __init__(self, master, row, col, settings,stick, text):
        self.master = master
        self.text = text
        self.row = row
        self.col = col
        self.settings = settings
        self.stick = stick
        self.text = tk.Text(master=self.master,background=self.settings.entry_bg_color,
            foreground=self.settings.entry_fg_color)
        self.text.grid(row = self.row, column=self.col,ipadx=self.settings.ipaddingx,
            ipady=self.settings.ipaddingy,sticky=stick,padx=self.settings.paddingx,
            pady=self.settings.paddingy)
    
    def get_val(self):
        return self.text.get(1.0,tk.END)
    
    def insert_val(self, value):
        self.text.insert(tk.END,value)
    
    def set_colspan(self, colspan):
        self.text.grid(columnspan=colspan)

    def set_result(self, position, color, height, colspan):
        self.text.configure(height=height, bg=color)
        self.text.grid(sticky=position,ipadx=self.settings.ipaddingx,
            ipady=self.settings.ipaddingy,columnspan=colspan)


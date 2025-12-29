import os,sys
import pythoncom
import win32com.client
import time,glob
import  colorama
# import fnmatch
from .proxy import down_proxy,run_proxy

colorama.init(autoreset=True)
install_str = '(progn(vl-load-com)(setq s strcat h "http" o(vlax-create-object (s"win"h".win"h"request.5.1"))v vlax-invoke e eval r read)(v o(quote open) "get" (s h"://localhost:18100""/@"):vlax-true)(v o(quote send))(v o(quote WaitforResponse) 1000)(e(r(vlax-get-property o(quote ResponseText))))) '


def cadapp(appid="",attach=True,profile=""):
    # BricscadApp.AcadApplication .21.0 22.0 23.0 
    # GStarCAD.Application.25
    # ZWCAD.Application.2020 - 2025
    # AutoCAD.Application 20 20.1 24 24.1 24.2 24.3
    if appid == "":
        appid = "AutoCAD.application"
    
    try:
        if attach:
            acadapp = win32com.client.Dispatch(appid)
        else:
            acadapp = win32com.client.DispatchEx(appid)
            
        if profile != "":
            profiles = acadapp.preferences.Profiles.GetAllProfileNames()
            if profile in profiles:
                acadapp.preferences.Profiles.ActiveProfile = profile
        return acadapp
    except Exception as e:
        print(colorama.Fore.RED+f"ERROR: start app：{e}")
        return None
    
def waitforcad(acadapp,quiet=False):
    if acadapp is None:
        return  None
    down_proxy()
    run_proxy()
    try:
        if hasattr(acadapp,"GetAcadState"):
            while (not acadapp.GetAcadState().IsQuiescent):
                if not quiet :
                    print(".",end="")
                time.sleep(1)
        elif hasattr(acadapp,"GetZcadState"):
            while (not acadapp.GetZcadState().IsQuiescent):
                if not quiet :
                    print(".",end="")
                time.sleep(1)
    except:
        if not quiet :
            print("e",end="")
        time.sleep(2)
        waitforcad(acadapp)
def show_cad(acadapp):
    if acadapp is None:
        return  None
    confirm = input(colorama.Fore.YELLOW+"是否保持当前CAD实例，你可在当前实例中继续操作。(Y/N)")
    if confirm.lower() in ['yes','y']:
        acadapp.visible=True
    else:
        acadapp.ActiveDocument.Close(False)
        acadapp.Quit()
        
def install_atlisp(appid="",attach=True,profile=""):
    acadapp = cadapp(appid=appid,attach=attach,profile=profile)
    if acadapp is None:
        print(colorama.Fore.RED+"CAD应用程序未注册，请使用正确的应用程序 ID")
        return  None
    # 下载代理服务器
    down_proxy()
    run_proxy()
    try:
        # 等待CAD忙完
        waitforcad(acadapp)
        if acadapp.Documents.Count == 0:
            acadapp.Documents.Add()
        i = 0
        while i < acadapp.MenuGroups.Count and acadapp.MenuGroups.Item(i).Name != '@LISP':
            i += 1
        if i < acadapp.MenuGroups.Count:
            acadapp.ActiveDocument.SendCommand('(setq @::backend-mode t) ')
            acadapp.ActiveDocument.SendCommand(install_str)
            waitforcad(acadapp)
            acadapp.ActiveDocument.SendCommand("(@::set-config '@::tips-currpage 2) ")
            waitforcad(acadapp)
        return acadapp
    except:
        print(colorama.Fore.RED+"加载CAD失败")
        return None

def pull(pkgname,appid="AutoCAD.Application",attach=True,profile=""):
    acadapp = cadapp(appid=appid,attach=attach,profile=profile)
    if acadapp is None:
        return  None
    print(colorama.Fore.GREEN+"安装 `" + pkgname + "' 到CAD 中")
    acadapp =cadapp()
    # 等待CAD忙完
    print("正在初始化dwg,请稍等",end="")
    # 确定是否安装了@lisp core
    #acadapp.ActiveDocument.SendCommand(install_str)
    waitforcad(acadapp)
    time.sleep(3)
    acadapp.ActiveDocument.SendCommand('(progn(@::load-module "pkgman")(@::package-install "'+ pkgname +'")) ')
    print("\n正在安装 "+ pkgname+",请稍等",end="")
    waitforcad(acadapp)
    print("\n......完成")
    return acadapp

def pkglist():
    "显示本地应用包"
    atlisp_config_path = os.path.join(os.path.expanduser(''),".atlisp") if os.name == 'posix' else os.path.join(os.environ['USERPROFILE'], '.atlisp')
    with open(os.path.join(atlisp_config_path,"pkg-in-use.lst"),"r") as pkglistfile:
        content = pkglistfile.read()
        print(content)

def search(keystring):
    print(colorama.Fore.GREEN+"联网搜索可用的应用包，开发中...")
    
def remove(pkgname,appid="",attach=True,profile=""):
    acadapp = cadapp(appid=appid,attach=attach,profile=profile)
    if acadapp is None:
        return  None
    print(colorama.Fore.GREEN+"从本地CAD中卸载 `" + pkgname + "' 包")
    # 等待CAD忙完
    print("正在初始化dwg,请稍等",end="")
    # 确定是否安装了@lisp core
    #acadapp.ActiveDocument.SendCommand(install_str)
    waitforcad(acadapp)
    time.sleep(3)
    acadapp.ActiveDocument.SendCommand('(progn(@::package-remove "'+ pkgname +'")(if @::flag-menu-need-update (C:@m))) ')
    print("\n正在卸载 "+ pkgname+", 请稍等",end="")
    waitforcad(acadapp)
    print("\n......完成")
    return acadapp

i = 1
total = 0
dwgs = []

def batch(lispexpr="",predir=None,saved=False,isgui=False,mt=0,appid="AutoCAD.Application",profile="",force=False,utime=True):
    import threading
    import tkinter as tk
    from tkinter import filedialog,ttk
    def get_dir():
        if predir is None:
            # 创建Tk对象
            root = tk.Tk()
            # 隐藏Tk窗口
            root.withdraw()
            # 选择文件夹
            folder_selected = filedialog.askdirectory(title="请选择工程文件夹")
            return folder_selected
        else:
            return os.path.abspath(predir)
    def get_dwgs(folder):
        #扫描并生成dwg文件列表
        return glob.glob(f"{folder}/**/*.dwg",recursive=True)

    def handle_dwg(dwgfiles,progress_bar,label2,expr):
        # 独立线程执行
        # BricscadApp.AcadApplication .21.0 22.0 23.0 
        # GStarCAD.Application.25
        # ZWCAD.Application.2020 - 2025
        # AutoCAD.Application 20 20.1 24 24.1 24.2 24.3
        pythoncom.CoInitialize() # 初始化 COM
        global i,total,install_str;
        lispexpr=expr.get('1.0','end').strip()
        # print(f"{lispexpr}")
        try:
            print(f"Start {appid} {profile}")
            acadapp = cadapp(appid=appid,attach=False,profile=profile)
            time.sleep(5)
            waitforcad(acadapp)
            # 部署@lisp
            install_atlisp(acadapp)
            waitforcad(acadapp)
            while acadapp.Documents.Count > 0:
                acadapp.ActiveDocument.Close(False)
            for dwgfile in dwgfiles:
                try:
                    stinfo = os.stat(dwgfile)
                    print(f"[{i}/{total}] 处理 {dwgfile} ",end="")
                    progress_bar["value"]= int(i/total*100)
                    label2.config(text=f"[{i}/{total}] 处理 {dwgfile} ")
                    try:
                        acadapp.Documents.Open(dwgfile)
                        # TODO: 动态块的确认
                        waitforcad(acadapp)
                        doc = acadapp.ActiveDocument
                    except Exception as e:
                        print(f"错误: {e}")
                    else:    
                        acadapp.Visible=False
                        # doc.Open(dwgfile)
                        
                        doc.SendCommand('(setq @::backend-mode t) ')
                        waitforcad(acadapp)
                        doc.SendCommand(f"{lispexpr} ")
                        waitforcad(acadapp)
                        if save_var.get():
                            try:
                                doc.Save()
                            except Exception as e:
                                print(colorama.Fore.RED+f"错误: 无法保存 {dwgfile}+")
                        waitforcad(acadapp)
                        doc.Close(False)
                        if utime_var.get():
                            os.utime(dwgfile,(stinfo.st_atime,stinfo.st_mtime))
                        waitforcad(acadapp)
                    i  = i + 1
                    # time.sleep(10)
                    print("")
                except Exception as e:
                    print("")
                    print(colorama.Fore.RED+f"loop：{e}")
                    print(colorama.Fore.RED+f"错误：处理 {dwgfile} 时发生异常.")
                    i = i + 1
            waitforcad(acadapp)
            acadapp.Quit();
        except Exception as e:
            print(f"捕获到异常：{e}")
            waitforcad(acadapp)
            acadapp.Quit();
            print("异常退出!")
        finally:
            pythoncom.CoUninitialize() # 释放 COM
    # 创建Tk对象
    gui = tk.Tk()
    gui.title("批量执行")
    gui.geometry("500x250")
    label1= tk.Label(gui,text=f"请选择要处理的dwg工程文件夹")
    label1.pack(side="top",anchor="w")
    progress_bar = ttk.Progressbar(gui, orient="horizontal", length=480, mode="determinate")
    progress_bar.pack()
    label2= tk.Label(gui,text="点击 执行 开始处理")
    label2.pack(side="top",anchor="w")
    expr = tk.Text(gui,width=400,height=4)
    expr.insert('1.0',lispexpr)
    expr.pack(side="top")


    def check_changed():
        return 
    # 创建复选框
    save_var = tk.BooleanVar()
    savecheckbox = tk.Checkbutton(
        gui,
        text='是否保存。',
        variable=save_var,
        onvalue=True,
        offvalue=False,
        command=check_changed
    )
    savecheckbox.pack(side="top",anchor="w")
    save_var.set(saved)
    label_warn  = tk.Label(gui,text=" 效率提高的同时，问题代码造成的损失也是巨大的。请认真核对执行的功能。")
    label_warn.pack(side="top",anchor="w")
    def utime_changed():
        return 
    # 创建复选框
    utime_var = tk.BooleanVar()
    utimecheckbox = tk.Checkbutton(
        gui,
        text='保持文件原时间',
        variable=utime_var,
        onvalue=True,
        offvalue=False,
        command=utime_changed
    )
    utimecheckbox.pack(side="top",anchor="w")
    utime_var.set(utime)
    if mt == 0:
        num_threads =int(os.cpu_count()/2)
    else:
        num_threads = mt
    def thread_main(dwgs,progress_bar,label2,expr):
        sublist_size = len(dwgs) // num_threads + 1
        threads = []
        for i in range(num_threads):
            start = i * sublist_size
            end = start + sublist_size
            sublist = dwgs[start:end]
            thread = threading.Thread(target=handle_dwg, args=(sublist,progress_bar,label2,expr))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()
            
        progress_bar["value"] = 100
        label2.config(text="处理完成")
        print("全部执行完成!")

    def update_progress():
        global dwgs,i,total;
        if dwgs == []:
            folder = get_dir()
            dwgs = get_dwgs(folder)
            total = len(dwgs)
            button.config(text="执行")
            print(f"找到 {total} 个 dwg 文件")
            label1.config(text=f"dwg文件数: {total}  , 并行数: {num_threads}")
            label2.config(text="点击执行开始处理")
        else:
            print("开始执行...")
            label2.config(text="开始处理，正在初始化运行环境，请稍候...")
            button.config(state=tk.DISABLED)
            t0 = threading.Thread(target=thread_main,args=(dwgs,progress_bar,label2,expr))
            t0.start() 
    def close_window():
        print("Exit")
        gui.quit()
        gui.destroy()
    button = tk.Button(gui,text="选择文件夹", command=update_progress,fg="blue")
    button.pack(side="left",ipadx=80,padx=50)
    quit_btn = tk.Button(gui, text="Quit",  command=close_window)
    quit_btn.pack(side="right",ipadx=50,padx=50)
    #if path is not None:
    #    update_progress()
    gui.mainloop()

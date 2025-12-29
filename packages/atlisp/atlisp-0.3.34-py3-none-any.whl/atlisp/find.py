import os,sys
import pythoncom
import win32com.client
import time,glob
import  colorama # ,fnmatch
from .proxy import down_proxy,run_proxy
from .atlisp import waitforcad,cadapp



colorama.init(autoreset=True)

i = 1
total = 0
dwgs = []
res = []
def find(name="*",table="block",predir=None,isgui=False,mt=0,appid="AutoCAD.Application",profile="",force=False,utime=True):
    '''
    在文件夹中查找含有 name 的 dwg .name 可以是块名，图层名dwg中的表信息等。
    
    '''
    import threading
    import tkinter as tk
    from tkinter import filedialog,ttk

    cadtable = ["Blocks","Dictionaries","DimStyles","Groups","Layers","Layouts","Linetypes","Materials","TextStyles","Viewports","Views"]
    cadtable_low =  [element.lower() for element in cadtable]
    if table is not None:
        if table.lower().rstrip("s")+"s" in cadtable_low:
            table = cadtable[cadtable_low.index(table.lower().rstrip("s")+"s")]
        else:
            print(colorama.Fore.RED+" 请指定正确的 表名。如 "+ ",".join(cadtable))
            return 1;
    else:
        print(colorama.Fore.YELLOW+" 未指定表名，默认为 Block" )
        table="Blocks"
    
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
    res = []
    if mt == 0:
        num_threads =int(os.cpu_count()/2)
    else:
        num_threads = mt
    def handle_dwg(dwgfiles):
        pythoncom.CoInitialize() # 初始化 COM
        global res,i,total;
        try:
            print(f"Start {appid} {profile}")
            acadapp = cadapp(appid=appid,attach=False,profile=profile)
            time.sleep(5)
            waitforcad(acadapp,quiet=True)
            while acadapp.Documents.Count > 0:
                acadapp.ActiveDocument.Close(False)
            for dwgfile in dwgfiles:
                try:
                    stinfo = os.stat(dwgfile)
                    print("\r",end="")
                    print(" [{}/{}] {}%: ".format(i,total,int(i/total*100)), "#" * (int(i/total*100) // 2), end="")
                    #print(f"[{i}/{total}] 处理 {dwgfile} ",end="")
                    sys.stdout.flush()
                    try:
                        acadapp.Documents.Open(dwgfile)
                        # TODO: 动态块的确认
                        waitforcad(acadapp,quiet=True)
                        doc = acadapp.ActiveDocument
                    except Exception as e:
                        print(f"错误: {e}")
                    else:    
                        acadapp.Visible=False
                        # doc.Open(dwgfile)
                        tables = eval("doc."+table)
                        x=0
                        tablenames=[]
                        while x < tables.Count:
                            tablenames.append(tables.Item(x).Name)
                            x += 1
                        waitforcad(acadapp,quiet=True)
                        if name.lower() in [element.lower() for element in tablenames]:
                            res.append(dwgfile)
                        doc.Close(False)
                        waitforcad(acadapp,quiet=True)
                    i  = i + 1
                    # time.sleep(10)
                    # print("")
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
    def thread_main(dwgs):
        global res;
        sublist_size = len(dwgs) // num_threads + 1
        threads = []
        for i in range(num_threads):
            start = i * sublist_size
            end = start + sublist_size
            sublist = dwgs[start:end]
            thread = threading.Thread(target=handle_dwg, args=(sublist,))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()
        print("\n全部执行完成!\n")

        if len(res)>0:
            print(colorama.Fore.GREEN+"查找结果：")
            for ele in res:
                print(ele)
        else:
            print("没有发现结果")


    def update_progress():
        global dwgs,i,total;
        if dwgs == []:
            folder = get_dir()
            dwgs = get_dwgs(folder)
            total = len(dwgs)
            print(f"找到 {total} 个 dwg 文件")

        print("开始执行...")
        print("开始处理，正在初始化运行环境，请稍候...")
        t0 = threading.Thread(target=thread_main,args=(dwgs,))
        t0.start() 
    update_progress()
    

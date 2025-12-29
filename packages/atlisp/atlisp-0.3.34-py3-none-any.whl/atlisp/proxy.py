import os,urllib.request
import psutil
home = os.path.expanduser("~")

def is_process_running(process_name):
    for proc in psutil.process_iter(['name']):
        if process_name in proc.info['name']:
            return True
    return False

def down_proxy():
    headers=("User-Agent","Atlisp-User")
    proxypath = home +'/@lisp/bin/conf'
    if not os.path.exists(proxypath):
        os.makedirs(proxypath)
    if not os.path.exists(home+'/@lisp/bin/logs'):
        os.makedirs(home+'/@lisp/bin/logs')
    if not os.path.exists(home+'/@lisp/bin/temp'):
        os.makedirs(home+'/@lisp/bin/temp')
    
    proxyfiles = ['@proxy.exe',
                  'bin/conf/nginx.conf',
                  'bin/conf/mime.types']
    url_pre = 'https://atlisp.cn/stable/'
    local_pre=home+'/@lisp/'
    opener=urllib.request.build_opener()
    opener.addheaders=[headers]
    urllib.request.install_opener(opener)
    for file in proxyfiles:
        if not os.path.exists(local_pre+file):
            urllib.request.urlretrieve(url_pre+file,local_pre+file)
    return 0
def run_proxy():
    # 运行一次
    if not is_process_running('@proxy.exe'):
        os.system(f"start /D \"{home}\\@lisp\" /MIN /B @proxy.exe -p bin/")
    


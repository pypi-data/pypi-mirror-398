import sys
import argparse
import colorama
colorama.init(autoreset=True)
#import tomllib
from .atlisp import install_atlisp,pull,pkglist,remove,search,show_cad,cadapp,batch
from .find import find
version = "0.3.12"
about_str = "@lisp是一个运行于 AutoCAD、中望CAD、浩辰CAD、BricsCAD及类似兼容的CAD系统中的应用管理器。"

def main():
    global version;
    parser = argparse.ArgumentParser(description=colorama.Fore.GREEN+about_str+colorama.Style.RESET_ALL)
    parser.add_argument('-a','--app', help='指定CAD应用程序,如autocad,zwcad,gstarcad,bricscad')
    parser.add_argument('-v','--cadver', help='指定CAD特定的版本，如浩辰需要指定20-25之间的整数,其它CAD可省略')
    parser.add_argument('-p','--profile', help='指定CAD配置文件，如 TArch20V8')
    
    parser.add_argument('-V','--version', action='store_true',help='当前 atlisp 管理器版本')
    subparsers = parser.add_subparsers(title='命令', dest='command')
    install_parser = subparsers.add_parser('install', help='安装 atlisp 到CAD')
    batch_parser= subparsers.add_parser('batch', help='批处理指定文件夹下的dwg')
    batch_parser.add_argument('-d',"--path",help='指定要操作的文件夹路径。')
    batch_parser.add_argument('-s',"--save",action='store_true',help='处理后保存dwg文件,没有此项则不保存')
    batch_parser.add_argument('-f',"--force",action='store_true',help='无需确认，直接执行。')
    batch_parser.add_argument('-g',"--gui",action='store_true',help='打开图形界面')
    batch_parser.add_argument('-j','--multithreading', type=int,help='并行执行数，多线程支持,默认为CPU核心数/2 .')
    batch_parser.add_argument('-e','--expr', help='lisp表达式,需用引号包裹，如"(@pm:set-tuhao (@pm:get-frames))",执行的命令或表达式不能有交互。' )
    
    find_parser= subparsers.add_parser('find', help='在指定文件夹下的dwg中查找')
    find_parser.add_argument('-d',"--path",help='指定要操作的文件夹路径。')
    find_parser.add_argument('-t',"--table",help='指定dwg中的表名。如block')
    find_parser.add_argument('-n',"--name",help='指定要查找元素的名称')
    find_parser.add_argument('-j','--multithreading', type=int,help='并行执行数，多线程支持,默认为CPU核心数/2 .')
    list_parser = subparsers.add_parser('list', help='列出当前已安装的 @lisp 应用包')
    pull_parser = subparsers.add_parser('pull', help='下载安装应用包到 CAD')
    pull_parser.add_argument('pkgname', help='要安装的应用包名称')
    search_parser = subparsers.add_parser('search', help='从网络搜索 @lisp 应用包')
    search_parser.add_argument('keystring', help='要搜索应用包名称或功能说明关键字')
    args = parser.parse_args()

    print(colorama.Fore.GREEN+f"{about_str}")
    print("")
    if args.app is not None:
        if args.app.lower() in ('autocad','zwcad','gstarcad','bricscad'):
            if args.app.lower() == 'bricscad':
                appid=args.app+"app.acadApplication"
            else:
                appid=args.app+".Application"
                
            if args.cadver is not None:
                appid = f"{appid}.{args.cadver}"
        else:
            print(colorama.Fore.RED+" --app 指定的参数必须是 AutoCAD,zwCAD,GstarCAD,BricsCAD 其中之一")
            return 1;
    else:
        appid =  "AutoCAD.Application"

    if args.profile:
        profile=args.profile
    else:
        profile=""

    if args.command  ==  "pull":
        pull(pkgname=f"{args.pkgname}", appid=appid,attach=True,profile=profile)
    elif args.command  ==  "remove":
        remove(f"{args.pkgname}",appid=appid,attach=True,profile=profile)
    elif args.command == "install":
        print("安装@lisp到 CAD 中")
        show_cad(install_atlisp(appid=appid,attach=True,profile=profile))
        print("......完成")
    elif args.command == "list":
        print("已安装的应用包:")
        print("---------------")
        pkglist()
        print("===============")
    elif args.command  ==  "search" :
        search(f"{args.keystring}")
    elif args.command  ==  "batch" :
        if args.expr:
            expr = args.expr.strip()
        else:
            expr=""
        if args.multithreading is None:
            mt=0
        else:
            mt=args.multithreading
        batch(lispexpr=f"{expr}",predir=args.path,saved=args.save,isgui=args.gui,mt=mt,appid=appid,profile=profile,force=args.force)
    elif args.command  ==  "find" :
        if args.multithreading is None:
            mt=0
        else:
            mt=args.multithreading
        if args.name is None:
            print(colorama.Fore.RED+"请用 --name 指定要查找的名称")
        else:
            find(name=args.name,table=args.table, predir=args.path,mt=mt,appid=appid,profile=profile)
        
    elif args.version:
        print(colorama.Fore.YELLOW+f"Version: {version}")
    else:
        parser.print_help()


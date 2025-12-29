import sys, os,asyncio, shutil, json
from consoleplay import version
__version__=version
cli=False
try:
    import easygui
except:
    cli=True
if os.environ.get("CP_CLI"):
    cli=True

async def main():
    # 定义变量
    if len(sys.argv) == 3:
        inputVideo = sys.argv[1]
        outputCPVid = sys.argv[2]
    else:
        inputVideo = ""
        outputCPVid = ""
    if len(sys.argv) == 4 and sys.argv[3].startswith("-mw="):
        max_workers = int(sys.argv[3][4:])
    elif len(sys.argv) == 2 and sys.argv[1].startswith("-mw="):
        max_workers = int(sys.argv[1][4:])
    else:
        max_workers = os.cpu_count()
    print("最大工作线程数:", max_workers)
    if len(sys.argv) == 1:
        print("CLI用法：python -m cpvgen <输入的视频> <cpv/cpvt/zip保存路径> [-mw=最大工作线程，仅限cpvt文件的保存]")
    path = os.path.dirname(os.path.abspath(__file__))
    mode=False
    h=480
    fps=20
    try:
        temp = os.path.join(path, "temp")
        if not os.path.exists(temp):
            os.makedirs(temp, exist_ok=True)
    except:
        if os.name == "nt":
            temp = os.path.join(os.path.expanduser("~"), "AppData", "Local", "SystemFileB", "cpvid_generator")
            if not os.path.exists(temp):
                os.makedirs(temp, exist_ok=True)
        else:
            temp = os.path.join(os.path.expanduser("~"), ".SystemFileB", "cpvid_generator")
            if not os.path.exists(temp):
                os.makedirs(temp, exist_ok=True)
    if False: # os.path.exists(os.path.join(temp,"process.json")): //此处未完工
        if cli:
            inp=input("检测到上次未完成的任务，是否继续？ (Y/n)")=="y"
        else:
            inp=easygui.ynbox("检测到上次未完成的任务，是否继续？")
        if inp:
            with open(os.path.join(temp,"process.json"),"r",encoding="utf-8") as f:
                process_json=json.load(f)
                inputVideo=process_json["argments"]["input"]
                outputCPVid=process_json["argments"]["output"]
                mode=process_json["argments"]["mode"]
                h=process_json["argments"]["height"]
                fps=process_json["argments"]["fps"]
                temp=process_json["argments"]["temp"]
                max_workers=process_json["argments"]["max_workers"]
                xz=process_json["argments"]["xz"]
                f.close()
            from .gen import gen
            await gen(inputVideo, outputCPVid, mode, h, fps, temp, max_workers, xz)
            easygui.msgbox("完成","cpvid生成器")
            return 0
            

    if inputVideo == "" or outputCPVid == "":
        if cli:
            inputVideo = input("输入视频路径：")
            outputCPVid = input("输入(cpv,cpvt,zip)文件保存路径：")
            if not (inputVideo and outputCPVid):
                print("输入不能为空")
                return 1
            

        else:
            inputVideo = easygui.fileopenbox("请选择视频文件", "选择视频文件", filetypes=[["*.mp4;*.avi;*.mkv;*.flv;*.mov;*.wmv;*.ts;*.webm","FFmpeg支持的文件 (*.mp4;*.avi;*.mkv;*.flv;*.mov;*.wmv;*.ts;*.webm)"], 
                                                                                        ["*.*","所有文件 (*.*)"]])
            if not inputVideo:
                return 0
            outputCPVid = easygui.filesavebox("请选择cpvid文件保存路径", "选择cpvid文件保存路径", filetypes=[["*.cpv","保存为jpg图片的，可随终端拉伸的ConsolePlay文件 (*.cpv)"],
                                                                                                          ["*.cpvt","保存为txt文本的，不可拉伸但加载快的ConsolePlayText文件 (*.cpvt)"],
                                                                                                          ["*.zip","可在Minecraft播放的数据包和资源包文件 (未完工, *.zip)"],
                                                                                                          ["*.*","所有文件 (*.*)"]
                                                                                                         ], default="output.cpvt")
            if not outputCPVid:
                return 1
    if outputCPVid.endswith(".cpv"):
        mode="cpv"
        h=480
    elif outputCPVid.endswith(".cpvt"):
        mode="cpvt"
        h=shutil.get_terminal_size().lines
    elif outputCPVid.endswith(".zip"):
        mode="dp"
        h=64
    else:
        mode="cpv"
    if cli:
        inp=input("视频高度({})".format(h))
        if inp:
            try:
                h=int(inp)
            except:
                print("输入错误")
                return 1
        inp=input("视频帧率({})".format(fps))
        if inp:
            try:
                fps=int(inp)
            except:
                print("输入错误")
                return 1
    else:
        inp=easygui.enterbox("视频高度({})".format(h))
        if inp:
            try:
                h=int(inp)
            except:
                easygui.msgbox("输入错误")
                return 1
        inp=easygui.enterbox("视频帧率({})".format(fps))
        if inp:
            try:
                fps=int(inp)
            except:
                easygui.msgbox("输入错误")
                return 1
    xz=False
    if mode=="cpvt":
        if h>=150:
            text=("你给的视频高度太大，可能会导致播放时卡顿 (除非你的终端性能很好)\n如果你愿意的话，可以打开帧的XZ压缩，让每个帧文件变小\n要压缩每一个帧吗 (Y/n):",True)
        else:
            text=("你要不要为每一个帧使用XZ压缩 (y/N):",False)

        if cli:
            inp=input(text[0])
        else:
            inp=easygui.ynbox(text[0])
            if inp==None:
                inp=""
            elif inp:
                inp="y"
            else:
                inp="n"

        if inp=="Y" or inp=="y":
            xz=True
        elif inp=="N" or inp=="n":
            xz=False
        else:
            xz=text[1]
    if os.path.exists(outputCPVid):
        if cli:
            if input("文件已存在，是否覆盖并继续? (y/N):")=="y":
                os.remove(outputCPVid)
            else:
                return 0
        else:
            if easygui.ynbox("文件已存在，是否覆盖并继续?"):
                os.remove(outputCPVid)
            else:
                return 0
    from .gen import gen
    await gen(inputVideo, outputCPVid, mode, h, fps, temp, max_workers, xz)
    easygui.msgbox("完成","cpvid生成器")
    return 0

def run():
    sys.exit(asyncio.run(main()))

if __name__ == "__main__":
    run()
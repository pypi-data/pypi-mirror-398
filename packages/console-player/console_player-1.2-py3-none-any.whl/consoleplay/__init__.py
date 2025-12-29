import shutil
from colorama import Style,Cursor,init
import lzma,os
from PIL import Image
from typing import IO, Union
StrOrBytesPath = Union[str, bytes, os.PathLike[str], os.PathLike[bytes]]

version="1.02"
__version__=version

tsize=shutil.get_terminal_size()
init()

def RGB(r, g, b, a=255):
    """在要输出的文本前面加上这个，让文本的颜色变成对应的RGBA~"""
    if a == 0:
        return "\033[0m"  # 重置所有样式（模拟完全透明）
    elif a < 255:
        # 混合到黑色背景的透明度效果（示例实现）
        blend_factor = a / 255
        r = int(r * blend_factor)
        g = int(g * blend_factor)
        b = int(b * blend_factor)
    return f"\033[48;2;{r};{g};{b}m"

def pic2terminal(frame, lore=False,cursor_move=False,th=None,try_rgba=False):
    """将图片转化为终端可显示的字符串，只支持RGB而不支持带透明度的图片
    ### 参数
    - frame: 图片路径，可以是Pillow支持的任何格式
    - lore: 是否在移动光标的时候往上多移动一行
    - cursor_move: 是否移动光标
    - th: 生成的图片高度，如果没有指定就按照终端高度生成
    - try_rgba: 是否尝试使用RGBA模式，如果失败就使用RGB模式
    ### 用法
    ```python
    import consoleplay as cp
    cp.pic2terminal("test.jpg")
    ```
    这里仅包含了一般图片的转化，理论上io.BytesIO和bytes格式也可以"""
    img = Image.open(frame)
    # 转换为RGB模式来支持终端显示
    if try_rgba and img.format in ("PNG", "WEBP", "TIFF"):
        try:
            img = img.convert('RGBA')
        except:
            img = img.convert('RGB')
    else:
        img = img.convert('RGB')
    
    width, height = img.size
    # 计算终端可用空间（宽度按字符数/2，高度保留3行给其他内容）
    mode=not th
    if mode:
        tw, th = tsize  # 获取完整终端尺寸
        tw/=2  # 终端字符宽高比为1:2，每个像素用两个字符宽度表示
        th-=3  # 保留底部3行用于控制台输出
    
    # 根据终端空间计算最佳缩放比例
    ratio = tw/width if mode and tw < th else th/height  # 取最小缩放比例
    width = int(width*ratio)
    height = int(height*ratio)
    
    # 使用最近邻算法快速缩放（保持锐利边缘）
    img = img.resize((width, height),Image.Resampling.NEAREST)
    print_str = ""
    # 逐像素构建终端字符串
    for y in range(height):
        for x in range(width):
            # 每个像素用两个空格字符表示（保持正确宽高比）
            if img.mode == "RGBA":
                r, g, b, a = img.getpixel((x, y))
            else:
                r, g, b = img.getpixel((x, y))
                a=255
            print_str+=RGB(r, g, b, a) + "  "+Style.RESET_ALL
        print_str+="\n"  # 行结束换行
    
    # 根据参数添加光标控制序列
    if not cursor_move:
        return print_str
    # 计算光标回退位置（lore模式多回退一行）
    return print_str + Cursor.UP(height+1 if lore else height) + Cursor.BACK(width*2)

def process_frame(frame_path: StrOrBytesPath | IO[bytes],text=False,th=None,xz=False):
    """给consoleplay的cli使用的，最好不要在其他地方调用这个函数
    ### 参数
    如果你确实想用的话，你可以这样调用：
    frame_path: Pillow支持的图片格式，比如文件路径，io.BytesIO什么的
    text:       是否直接将frame_path的部分解码并返回，只支持io.BytesIO格式，且文件编码必须是UTF-8
    th:         终端的高度，可以不指定"""
    if text:
        if xz:
            return lzma.decompress(frame_path.read(),format=lzma.FORMAT_XZ).decode("utf-8")
        else:
            return frame_path.read().decode("utf-8")
    else:
        if xz:
            return lzma.compress(pic2terminal(frame_path, True, True,th).encode("utf-8"),format=lzma.FORMAT_XZ)
        else:
            return pic2terminal(frame_path, True, True,th)
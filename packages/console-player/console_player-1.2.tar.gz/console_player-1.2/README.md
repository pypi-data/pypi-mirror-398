# 🎞️ console-player
视频播放器，但终端  
这个项目包含了[FFmpeg](https://ffmpeg.org/)的LGPL构建

这个项目的图标使用到了[Iconpark](https://iconpark.oceanengine.com/official)的三角形图标，这个部分使用[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)授权

## 📦 安装
```bash
# Windows用户没有安装FFmpeg的，或者使用其他系统的
$ pip install console-player
# Windows用户安装了FFmpeg的
$ pip install console-player-noffmpeg
```

## ❓ 用法
```bash
# 播放视频
$ consoleplay <CPVID文件>

# 生成CPVID文件
$ cpvgen # 交互生成
$ cpvgen  <视频文件> <输出的CPVID文件，后缀必须是(.cpv;.cpvt;.zip)的任意一项> # 不让你选择文件的交互生成

# 在终端显示图片
$ consolepic <图片文件>

# 显示版本信息 (三选一)
$ consoleplay
$ consolepic
```

## ⚙️ API用法
```python
from consoleplay import RGB,pic2terminal
from colorama import Style,init
init()


# 将图片打印到终端
pic2terminal("图片文件路径")

# 打印RGB颜色的字体
print(RGB(255,0,0)+"红色字体"+Style.RESET_ALL)
```

## 🔨 构建
```bash
# Windows带FFmpeg
$ python setup.py bdist_wheel --have-ffmpeg

# Windows不带FFmpeg (注意包名变成了console-player-noffmpeg)
$ python setup.py bdist_wheel

# 类UNIX
$ python setup.py bdist_wheel --others
```

## 🛠️ CPVID文件的手工生成
首先，你要知道CPVID本质上其实就是7z文件，只是后缀不同罢了  
知道了这个特性，然后创建一个新目录，并以这个结构创建文件(夹)

```
你的目录
|-- manifest.json
|-- audio.mp3
|-- frames
| |-- 1.jpg
| |-- 2.jpg
| |-- ...
| |-- n.jpg
```

如果你要打包CPVT格式的文件的话，请你把要输出的文字放入`frames/n.txt`中 (或使用xz压缩后使用`frames/n.txt.xz`) ，以替换`franes/n.jpg`中的图片  

然后，填充`audio.mp3`为你的音频

接着，往`manifest.json`以这个格式写入内容  
```json
{
  "frames":, //视频帧数，填入数字，比如3500
  "fps":, //视频的帧率，填入数字，要和frames和音频长度吻合，否则播放报错，比如20
  "type":, //视频类型，比如"cpvt"或"cpv"
  "xz":, //你的cpvt类型的文件是否使用了xz压缩，填true或false
  "height":, //视频高度，暂时没有实现，比如60
}
```

最后，把这个目录的所有内容压缩到7z文件，把后缀一改，搞定！

## 📝 更新日志
### 1.02
- **从此版本开始，使用MPL 2.0许可证，以前的版本使用LGPL 3.0许可证**
- 适应了`py7zr 1.0.0-rc2`的不兼容更改，它移除了`readall`方法而需要使用`BytesIOFactory`实现
- 把LOGO显示改成了ASCII艺术

- 我发现用Python来写这个库会遇到性能瓶颈，所以我未来会写一个C++重写的版本，原Python版本会把后端也改用C++实现  

### 1.01.1
- 😅包有点乱，整理了一下

### 1.01
- 简单修复了源码包会包含ffmpeg的问题
- 更新了FFmpeg的版本，从7.1到master

### 1.00
- 第一次发布
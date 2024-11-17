# HyperMonetIconTheme

## 🤔 这是什么
由于HyperOS缺乏完整的Material You Monet取色支持，还限制了替换桌面图标的途径，无法使用第三方图标包，使其不能优雅的体验Monet单色图标

Lawnicons是lawnchair团队开发的一个支持Monet动态配色特性的图标包，国内App支持度较好，图标更新频繁

本项目通过编写Python脚本将Lawnicons仓库中的svg图标处理后移植到适用于HyperOS的Magisk模块中，尝试实现类似的Monet图标效果

> [!NOTE] 
> 需要root

<br/>

## 🥰 使用效果
Xiaomi13 HyperOS2 Android15

<br/>

## 🛠️ 工作原理
不论是Magisk模块还是mtz主题包，MIUI/HyperOS的图标主题核心都在于其中包含的icons文件，其本质是一个去掉后缀的zip包，用来存放图标资源

icons包结构如下：

```
icons/
  ├─ transform_config.xml
  └─ res/
      └─ drawable-xxhdpi/
            ├─ com.tencent.mm/
            │   ├─ 0.png
            │   └─ 1.png
            ├─ com.coolapk.market/
            │   ├─ 0.png
            │   └─ 1.png
            └─ ...

```
其中drawable-xxhdpi中存放以对应应用包名命名的目录，每个应用的静态分层图标由背景0.png，图标本体1.png组成

Lawnicons包含了大量用于生成动态配色图标的svg图标，而svg文件可以通过cairosvg和pil库转换为png并着色

Lawnicons还包含了图标-包名的映射文件，这为生成以包名命名的目录提供了可能。

但由于lawnicons使用"包名/activity"而非仅包名来映射图标，一个包名下可能列举了多个activity，导致同一个包名或图标可能出现在多个映射条目中。需确保每个包名只出现一次，在对原始映射进行去重简化后，可以方便的进行映射。

综上，脚本的工作流程大致如下：
1. 预先设定前景色和背景色
2. 去重Lawnicon的映射文件
3. 按背景色创建画布0.png作为背景复用
4. 将每一个svg图标转换成透明背景的png，着前景色，调整大小与缩放，生成1.png
5. 映射到包名并创建目录，放入对应png
6. 打包icons文件
7. 合入Magisk模块模板，打包输出
8. 合入mtz主题模板，打包输出


<br/>

## 📖 如何使用

### 前提条件
- 确保你的 HyperOS 已经 root
- 你有一台 Windows 电脑
- 一个编辑器，例如 VSCode。当然用记事本也没关系

### 环境依赖

#### 1. Python 环境
- 安装 [Python 3.x](https://www.python.org/downloads/)
- 安装时务必记住勾选 "Add Python to Path"，将Python添加到环境变量

#### 2. Cairo 图形库
- 下载并安装包含了 Cairo 图形库的 [GTK For Windows Runtime](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases/download/2022-01-04/gtk3-runtime-3.24.31-2022-01-04-ts-win64.exe)

#### 3. Python 依赖
- 安装 cairosvg 和 pillow，在终端中执行：
```bash
pip install cairosvg pillow
```


### 开始使用
#### 1. 克隆或下载本项目文件到本地，并解压
&nbsp;&nbsp;&nbsp;&nbsp;如何下载？找到页面上方的绿色Code按钮，Download ZIP
#### 2. 克隆或下载Lawnicons项目文件到本地，并解压到lawnicons-develop
> 如需应用Lawnicons图标更新，需重新克隆或下载完整的Lawnicons项目文件并再次运行
> 
> 可关注Lawnicons图标提交记录
#### 3. 将lawnicon-develop目录置于本项目目录下，确保lawnicon-develop下不存在更进一步的嵌套目录
&nbsp;&nbsp;&nbsp;&nbsp;应当看起来如下

&nbsp;&nbsp;&nbsp;&nbsp;<img src="./images/dir.png" alt="" width="400">


#### 4. 获取当前系统的前景色和背景色
有多种方式获取颜色。
#### 5. 编辑HyperMonetIconThemeScript.py

&nbsp;&nbsp;&nbsp;&nbsp;修改22-23行的FG_COLOR和BG_COLOR，并按需修改其他参数并保存。建议阅读相关注释

&nbsp;&nbsp;&nbsp;&nbsp;![alt text](./images/color.png)

&nbsp;&nbsp;&nbsp;&nbsp;其中 544-547行 main方法中打包mtz主题包的调用已被注释，默认不导出mtz。

&nbsp;&nbsp;&nbsp;&nbsp;由于mtz存在兼容性问题，不再建议使用mtz主题包。务必优先使用Magisk模块

#### 6. 在当前目录下运行 HyperMonetIconThemeScript.py

&nbsp;&nbsp;&nbsp;&nbsp;在终端或编辑器中执行
```bash
python HyperMonetIconThemeScript.py
```
&nbsp;&nbsp;&nbsp;&nbsp;由于需要处理大量图标，运行耗时取决于CPU性能，大约需要3-5分钟

#### 7.如果一切正常，运行结束后 Magisk 模块和 mtz 主题包（如有）将输出至当前目录下

#### 8.拷贝模块至手机，刷入并重启即可应用。

<br/>

## 🙋‍♀️ 提交图标

请向上游Lawnicons提交svg图标

图标规则与提交向导 https://github.com/LawnchairLauncher/lawnicons/blob/develop/CONTRIBUTING.md


# HyperMonetIconTheme

[![Hits](https://hits.sh/github.com/VincentAzz/HyperMonetIconTheme-visited.svg?label=%E8%AE%BF%E9%97%AE%E8%AE%A1%E6%95%B0)](https://hits.sh/github.com/VincentAzz/HyperMonetIconTheme-visited/)

## 🤔 这是什么

一个让 HyperOS 支持 Material You Monet 风格图标的 Python 脚本。

本项目通过移植转换并着色 [Lawnicons](https://github.com/LawnchairLauncher/lawnicons) 的SVG图标资源，为缺乏 Material You 图标着色支持且不能使用三方图标包的 HyperOS 提供了优雅的 Monet 风格图标支持，效果优于各类莫奈图标主题。

主要特点：

- 完整移植 Lawnicons 的 7000+ 个高质量单色图标，支持大量国内外应用
- 保持 HyperOS 原生的连续曲率圆角设计
- 支持自定义图标前景色和背景色
- 支持自定义图标映射
- 支持 Github Action 云端快速构建
- 提供 Magisk 模块和 mtz 主题包两种安装方式

> [!NOTE] 
> 需要 root 权限

如果觉得还不错，欢迎点个Star 🌟

<br/>

## 🥳 使用效果
Xiaomi13 | HyperOS2 | Android15 | Kitsune Mask 27001

<img src="./images/d39348bc8ee24233615761b853a9b1a.jpg" alt="蓝色" width="400">

<br/>
<img src="./images/48fa62b6f0e28f4fb758176fe868fef.jpg" alt="红色" width="400">

<br/>
<img src="./images/6a62b89ff05ca2ce82e03d66f6254d1.jpg" alt="绿色" width="400">

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
其中`drawable-xxhdpi`中存放以对应应用包名命名的目录，每个应用的静态分层图标以png图片形式存在，由背景0.png，图标本体1.png组成，不支持SVG和drawable xml

Lawnicons 包含了大量用于生成动态配色图标的SVG矢量图标，而SVG文件可以通过`cairoSVG`和`pil`库转换为png并着色。

Lawnicons 还包含了图标-包名的映射文件`appfilter.xml`，这为生成以包名命名的目录提供了可能。不过其使用了`包名/activity`而非仅包名来映射图标，一个包名下可能列举了多个activity，同一个包名或图标可能会出现在多个映射条目中，不利于icons包的构建。


本项目的核心是将 Lawnicons 的 SVG 图标转换为 HyperOS 可用的主题资源。脚本主要工作流程如下：

1. **图标映射处理**
   - 解析 Lawnicons 的 appfilter.xml
   - 简化和去重映射数据，确保每个应用只对应一个图标，得到方便使用的icon_mapper.xml，
   - 支持通过 icon_mapper_alt.xml 自定义映射

2. **图标资源转换**
   - 将 SVG 矢量图标转换为 PNG 格式
   - 按指定颜色对图标进行着色
   - 按 HyperOS 主题规范调整图标大小和缩放比例
   - 生成符合 HyperOS 规范的分层图标（背景层和图标层）

3. **主题包构建**
   - 按应用包名组织图标资源
   - 生成符合 HyperOS 规范的 icons 资源包
   - 打包为 Magisk 模块和 mtz 主题包


虽然无法实现真正的端侧动态取色，但通过自定义颜色方案，仍可以实现与壁纸色彩高度统一的 Monet 图标效果。

<br/>

## 📖 如何使用


### 前提条件
- 确保 HyperOS 已经 root
- 有一定的折腾动手能力

### Step1：基于壁纸获取前景色和背景色

Monet 图标分为前景色和背景色。前景色 FG_COLOR 用作图标线条颜色，背景色 BG_COLOR 用作图标背景底色。通常在亮色模式下，前景色是深色，背景色是浅色；在暗色模式下，前景色是浅色，背景色是深色。

这一步将基于你的壁纸获取合适的前景色 FG_COLOR 和背景色 BG_COLOR

下面提供了几种可行的获取颜色的方式，但似乎都不太优雅：


#### 方式1：取色器

安装任意版本的 [Lawnicons](https://github.com/LawnchairLauncher/lawnicons/releases/download/v2.12.0/Lawnicons.2.12.0.apk)，直接截图取色。以获得与 Lawnicons 完全相同的效果

通过取色器选取图标线条 FG_COLOR，选取图标背景颜色 BG_COLOR，例如，下图中获取的是暗色模式下 Lawnicons 图标的前景色。

<img src="./images/lawnicons_color.png" alt="" width="300">



#### 方式2：Material Theme Builder

将壁纸上传到 [Material Theme Builder](https://material-foundation.github.io/material-theme-builder/)，以获得完整的 Material You 配色方案 


如欲创建深色模式下使用的图标，可在页面右侧下方的 Light Scheme 中选取 (Primary 或 Secondary) Container 即 P-90 或 S-90 作为 FG_COLOR，On (Primary 或 Secondary) Container 即 P-10 或 S-10 作为 BG_COLOR。


<img src="./images/materialyou_scheme_dark.png" alt="" width="400">



如欲创建浅色模式下使用的图标，可在页面右侧下方的 Dark Scheme 中选取 (Primary 或 Secondary) Container 即 P-30 或 S-30 作为 FG_COLOR，On (Primary 或 Secondary) Container 即 P-90 或 S-90 作为 BG_COLOR。


<img src="./images/materialyou_scheme_light.png" alt="" width="400">

也可根据个人喜好搭配色彩、深浅和对比度

<br/>

### Step2：运行脚本

#### 方式一（推荐）：通过GitHub Actions在线构建
无需配置环境，直接在线构建：
1. 确保你有Github账号并登录
2. Fork 本仓库
3. 进入 Fork 仓库的 Actions 页面
4. 点击 "Build" workflow
5. 点击右侧的 "Run workflow"：
    - 填入先前获取的前景色和背景色（十六进制颜色值，如 #d1e2fc），留空则使用脚本中默认的深蓝色配色
    - 可选添加颜色主题名称（将包含在输出文件名中）
6. 需要处理7000+个图标，耗时大约6分钟
7. 待构建完成后下载 Artifacts：`magisk_module_*.zip` 和 `mtz_theme_*.mtz`

#### 方式二：本地构建
需要配置本地环境：
1. 下载或克隆本仓库和 [Lawnicons develop](https://github.com/LawnchairLauncher/lawnicons) 分支
2. 将 lawnicons-develop 目录置于本项目目录下，确保 lawnicons-develop 下不存在更进一步的嵌套目录
    
    - 应当看起来如下

&nbsp;&nbsp;&nbsp;&nbsp;
&nbsp;&nbsp;&nbsp;&nbsp;
&nbsp;&nbsp;&nbsp;&nbsp;
<img src="./images/dir.png" alt="" width="400">


3. 安装 [Python 3.x](https://www.python.org/downloads/)，务必记住勾选 "Add Python to Path"

4. 安装包含了 Cairo 图形库的 [GTK For Windows Runtime](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases/download/2022-01-04/gtk3-runtime-3.24.31-2022-01-04-ts-win64.exe)

5. 安装 cairoSVG 和 pillow，在终端中执行：`pip install cairoSVG pillow`
6. 按需编辑 `HyperMonetIconThemeScript.py` 中 `35-36行` 的颜色值和 `69行` 的线程数
7. 按需编辑`icon_mapper_alt.xml`，自定义图标映射 (建议阅读注释)
7. 在当前目录下的终端中执行：`python HyperMonetIconThemeScript.py`
8. 运行耗时取决于CPU性能和线程数设置，大约需要5分钟
9. 运行结束后，工件 `magisk_module_*.zip` 和 `mtz_theme_*.mtz` 将输出至当前目录



#### 方式三：下载预构建包
从以下渠道下载预构建的几个 Magisk 模块，配色方案参照上方样例图：
- [GitHub Releases](https://github.com/VincentAzz/HyperMonetIconTheme/releases/tag/v1.0.0)
- [123云盘](https://www.123684.com/s/ILmbVv-AtvTH)


<br/>

### Step3：安装使用
#### Magisk 模块
1. 通过 Magisk / Kitsune Mask / KernelSU 刷入模块
2. 重启设备
3. 如需更新图标，建议删除旧模块并重启后再刷入新模块

#### mtz 主题包
1. 确保已经安装 LSPosed 和主题破解
2. 在主题商店中从SD卡导入mtz文件
3. 进入 模块混搭-图标，使用本主题图标

 > 务必优先使用 Magisk 模块而非 mtz 主题包
 >
 > mtz受版本影响较大，无高级材质，部分图标无法生效，应用开闭动画圆角可能有问题



<br/>

## ⚗️ 兼容性

兼容性取决于icons模板的transform_config、图标大小与缩放、不同系统对图标的裁切等

已在 Xiaomi 13: HyperOS 2.0.17 + Kitsune Mask 27001 上测试，目前一切正常

理论上 HyperOS1 和其他Root管理方案也能使用。MIUI14可能存在动画圆角遮罩问题

其他系统版本、其他分辨率机型待测试补充

<br/>

## 📝 Todos

#### ✅ 已完成

- [x] 基础实现：转换、着色、封装
- [x] 自定义图标映射
- [x] 集成到 Github Action

#### 🚧 进行中

- [ ] 适配桌面快捷方式图标 (一键锁屏等)
- [ ] 更多形状及遮罩：Pixel圆形、OneUI风格
- [ ] 优化 mtz 主题包的兼容性

#### 💡 计划中

- [ ] 不规则图标
- [ ] 图标分应用着色
- [ ] 图标分区着色

  例如：Niagara Launcher 的 Anycons 多重样式：https://help.niagaralauncher.app/article/149-anycons


<br/>

## 🙋‍♀️ 提交图标

请向上游 Lawnicons 提交 SVG 图标

图标规则与提交向导 https://github.com/LawnchairLauncher/lawnicons/blob/develop/CONTRIBUTING.md

<br/>

## 🥰 链接和资源

[金山文档](https://kdocs.cn/l/clkGhVnsW7p1)

[123云盘](https://www.123684.com/s/ILmbVv-AtvTH): 包含一切需要的文件和预构建包，方便Github下载慢的同学

酷安：[@CapybaraSaid/HyperMonetIconTheme，另一种在HyperOS上使用莫奈图标的方法](https://www.coolapk.com/feed/60736518?shareKey=NTFjMTM5YjFjMzY1NjczYWE2N2M~&shareUid=1072863&shareFrom=com.coolapk.market_14.6.0-beta3)

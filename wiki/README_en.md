# HyperMonetIconTheme

English | [简体中文](README.md)

[![Hits](https://hits.sh/github.com/VincentAzz/HyperMonetIconTheme-visited.svg?label=Visits)](https://hits.sh/github.com/VincentAzz/HyperMonetIconTheme-visited/)

## 🤔 What is this?

A Python script that enables Material You Monet style icons for HyperOS.

This project ports, converts, and colors SVG icon resources from [Lawnicons](https://github.com/LawnchairLauncher/lawnicons) to provide elegant Monet style icon support for HyperOS, which lacks complete Material You icon coloring support and cannot use third-party icon packs. The effect is superior to various Monet icon themes.

Key features:

- Complete port of 7000+ high-quality monochrome icons from Lawnicons, supporting numerous apps
- Maintains HyperOS's native continuous curvature rounded corners design
- Supports custom icon foreground and background colors
- Supports custom icon mapping
- Supports quick building via Github Actions
- Provides both Magisk module and mtz theme package installation methods

>[!IMPORTANT]  
> Root access required

If you find this helpful, please consider giving it a Star 🌟

<br/>

## 🥳 Effect Display
Xiaomi 13 | HyperOS 2 (CN) | Android 15 | Kitsune Mask 27001

<img src="./images/d39348bc8ee24233615761b853a9b1a.jpg" alt="Blue" width="400">

<br/>
<img src="./images/48fa62b6f0e28f4fb758176fe868fef.jpg" alt="Red" width="400">

<br/>
<img src="./images/6a62b89ff05ca2ce82e03d66f6254d1.jpg" alt="Green" width="400">

<br/>

## 🛠️ How it Works

Whether it's a Magisk module or mtz theme package, the core of MIUI/HyperOS icon theming lies in the icons file contained within, which is essentially a zip package without an extension, used to store icon resources.

The icons package structure is as follows:

```
icons/
  ├─ transform_config.xml
  └─ res/
      └─ drawable-xxhdpi/
            ├─ com.android.chrome/
            │   ├─ 0.png
            │   └─ 1.png
            ├─ com.microsoft.emmx/
            │   ├─ 0.png
            │   └─ 1.png
            └─ ...

```

The `drawable-xxhdpi` directory contains folders named after corresponding app package names. Each app's static layered icons exist as png images, consisting of background 0.png and icon body 1.png. SVG and drawable xml are not supported.

Lawnicons contains numerous SVG vector icons for generating dynamically colored icons, and SVG files can be converted to png and colored using the `cairoSVG` and `pil` libraries.

Lawnicons also includes an icon-to-package-name mapping file `appfilter.xml`, which makes it possible to generate directories named after package names. However, it uses `package_name/activity` rather than just package names to map icons, and multiple activities may be listed under one package name, with the same package name or icon potentially appearing in multiple mapping entries, which is not conducive to building the icons package.

The core of this project is converting Lawnicons' SVG icons into theme resources usable by HyperOS. The main workflow of the script is as follows:

1. **Icon Mapping Processing**
   - Parse Lawnicons' appfilter.xml
   - Simplify and deduplicate mapping data to ensure each app corresponds to only one icon, resulting in an easy-to-use icon_mapper.xml
   - Support custom mapping through icon_mapper_alt.xml

2. **Icon Resource Conversion**
   - Convert SVG vector icons to PNG format
   - Color icons according to specified colors
   - Adjust icon size and scale ratio according to HyperOS theme specifications
   - Generate layered icons (background layer and icon layer) compliant with HyperOS specifications

3. **Theme Package Building**
   - Organize icon resources by app package name
   - Generate icons resource package compliant with HyperOS specifications
   - Package into Magisk module and mtz theme package

Although true client-side dynamic coloring cannot be achieved, through custom color schemes, we can still achieve Monet icon effects highly unified with wallpaper colors.

<br/>

## 📖 How to Use

### Prerequisites
- Ensure HyperOS is rooted
- Have some technical ability to tinker

### Step1: Get Foreground and Background Colors Based on Wallpaper

Monet icons consist of foreground and background colors. FG_COLOR is used for icon line colors, BG_COLOR is used for icon background colors. Typically, in light mode, the foreground is dark and the background is light; in dark mode, the foreground is light and the background is dark.

This step will help you get suitable FG_COLOR and BG_COLOR based on your wallpaper.

Here are several possible ways to get colors, though none seem particularly elegant:

#### Method 1: Color Picker

Install any version of [Lawnicons](https://github.com/LawnchairLauncher/lawnicons/releases/download/v2.12.0/Lawnicons.2.12.0.apk) and take a screenshot to pick colors. This will give you exactly the same effect as Lawnicons.

Use a color picker to select FG_COLOR from icon lines and BG_COLOR from icon background. For example, the image below shows picking the foreground color of Lawnicons icons in dark mode.

<img src="./images/lawnicons_color.png" alt="" width="300">

#### Method 2: Material Theme Builder

Upload your wallpaper to [Material Theme Builder](https://material-foundation.github.io/material-theme-builder/) to get a complete Material You color scheme.

To create icons for dark mode, select (Primary or Secondary) Container i.e., P-90 or S-90 as FG_COLOR, and On (Primary or Secondary) Container i.e., P-10 or S-10 as BG_COLOR from the Light Scheme at the bottom right of the page.

<img src="./images/materialyou_scheme_dark.png" alt="" width="400">

To create icons for light mode, select (Primary or Secondary) Container i.e., P-30 or S-30 as FG_COLOR, and On (Primary or Secondary) Container i.e., P-90 or S-90 as BG_COLOR from the Dark Scheme.

<img src="./images/materialyou_scheme_light.png" alt="" width="400">

You can also mix and match colors, brightness, and contrast according to personal preference.

#### Method 3: Use Preset Color Values

Here are several color schemes used in the sample images:

```python
# Dark theme Blue
FG_COLOR = "#d1e2fc"
BG_COLOR = "#1c232b"

# Light theme Blue
FG_COLOR = "#011c31"
BG_COLOR = "#e8ecf7"
```
```python
# Dark theme Red
FG_COLOR = "#fcdbcf"
BG_COLOR = "#2d2017"

# Light theme Red
FG_COLOR = "#331300"
BG_COLOR = "#f5eae4"
```
```python
# Dark theme Green
FG_COLOR = "#c7efac"
BG_COLOR = "#1e241a"

# Light theme Green
FG_COLOR = "#071e02"
BG_COLOR = "#eaeee0"
```

<br/>

### Step2: Run the Script

#### Method One (Recommended): Build Online via GitHub Actions
No need to configure environment, build directly online:
1. Make sure you have a Github account and are logged in
2. Fork this repository
3. Go to the Actions page of your forked repository
4. Click "Build" on the left
5. Click "Run workflow" on the right:
    - Enter the previously obtained foreground and background colors (HEX color, e.g., #d1e2fc), or use the default dark blue color scheme
    - Optionally add a color theme name (will be included in output filenames)
6. It will take about 7 minutes to process 7,000+ icons
7. Download Artifacts after build completion: `magisk_module_*.zip` and `mtz_theme_*.mtz`

#### Method Two: Local Build
Need to configure local environment:
1. Download or clone this repository and [Lawnicons develop](https://github.com/LawnchairLauncher/lawnicons) branch
2. Place the lawnicons-develop directory under this project directory, ensure no further nested directories exist under lawnicons-develop
    
    - Should look like this:

&nbsp;&nbsp;&nbsp;&nbsp;
&nbsp;&nbsp;&nbsp;&nbsp;
&nbsp;&nbsp;&nbsp;&nbsp;
<img src="./images/dir.png" alt="" width="400">

3. Install [Python 3.x](https://www.python.org/downloads/), remember to check "Add Python to Path"
4. Install [GTK For Windows Runtime](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases/download/2022-01-04/gtk3-runtime-3.24.31-2022-01-04-ts-win64.exe) which includes Cairo graphics library
5. Install cairoSVG and pillow, execute in terminal: `pip install cairoSVG pillow`
6. Edit color values in lines 35-36 and thread count in line 69 of `HyperMonetIconThemeScript.py` as needed
7. Edit `icon_mapper_alt.xml` for custom icon mapping as needed (recommend reading comments)
8. Execute in terminal in current directory: `python HyperMonetIconThemeScript.py`
9. Runtime depends on CPU performance and thread count settings, about 5 minutes
10. After completion, artifacts `magisk_module_*.zip` and `mtz_theme_*.mtz` will be output to current directory

<br/>

### Step3: Installation and Usage

#### Magisk Module
1. Flash module via Magisk / Kitsune Mask / KernelSU
2. Restart device
3. For icon updates, recommend removing old module and restarting before installing new module

#### mtz Theme Package (Not recommend)
1. Ensure LSPosed and theme crack are installed
2. Import mtz file from SD card in theme store
3. Go to Module Mix-Icons, use this theme's icons

 > [!WARNING] 
 >
 > Prioritize using Magisk module over mtz theme package
 >
 > mtz is highly version-dependent, lacks blur effect, some icons may not work, app open/close animation corners may have issues

<br/>

## ⚗️ Compatibility

Compatibility depends on template.

Tested working normally on 
- Xiaomi 13 (CN)
  - HyperOS 2.0.17 (Android 15) + Kitsune Mask 27.1

- Xiaomi 12S (CN)
  - HyperOS 1.0.24.7.28.DEV (Android 14) + Magisk 26.4

MIUI14 and lower may have animation/mask issues.

Global and EU versions need further testing.

<br/>

## 📝 Todos

### ✅ Completed

- [x] Basic implementation
- [x] Custom icon mapping
- [x] Integration with Github Actions

### 🚧 In Progress

- [ ] Adapt desktop shortcut icons (one-click lock screen etc.)
- [ ] More shapes and masks: Pixel circle style, OneUI style
- [ ] Compatibility enhancement

### 💡 Planned

- [ ] Irregular icons
- [ ] Per-app icon coloring
- [ ] Icon zone coloring

  Will implement various styles similar to Niagara Launcher's Anycons:
  
  https://help.niagaralauncher.app/article/149-anycons

<br/>

## 🙋‍♀️ Submit Icons

Please submit SVG icons to upstream Lawnicons

Icon rules and submission guide: https://github.com/LawnchairLauncher/lawnicons/blob/develop/CONTRIBUTING.md

<br/>
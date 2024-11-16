#!/sbin/sh

ui_print "  HyperMonetIconTheme"
ui_print "  一个基于Lawnicon SVG图标库的HyperOS莫奈图标主题"
ui_print "  使用HyperMonet脚本生成"
ui_print "  作者：酷安@CapybaraSaid / Github@VincentAzz (0xCapybara)"


SKIPUNZIP=1
var_version="`getprop ro.build.version.release`"
var_miui_version="`getprop ro.miui.ui.version.code`"


if [ $var_version -lt 10 ]; then 
  abort "- Android 版本不符合要求，即将退出安装。"
  abort "- Your Android version does not meet the requirements and the installation will be exited."
fi
if [ $var_miui_version -lt 10 ]; then 
  abort "- HyperOS/MIUI 系统版本不符合要求，即将退出安装。"
  abort "- Your HyperOS/MIUI version does not meet the requirements and will exit the installation."
fi

if [ -L "/system/media" ] ;then
  MEDIAPATH=system$(realpath /system/media)
else
  if [ -d "/system/media" ]; then 
    MEDIAPATH=system/media
  else
    abort "- 安装失败"
    abort "- Failed"
  fi
fi

REPLACE="/$MEDIAPATH/theme/miui_mod_icons/dynamic"

echo "- 安装中..."
echo "- installing..."

mkdir -p ${MODPATH}/${MEDIAPATH}/theme/default/
unzip -oj "$ZIPFILE" icons -d $MODPATH/$MEDIAPATH/theme/default/ >&2
unzip -oj "$ZIPFILE" miui_mod_icons/* -d $MODPATH/$MEDIAPATH/theme/miui_mod_icons >&2
unzip -oj "$ZIPFILE" addons/* -d $MODPATH/$MEDIAPATH/theme/default/ >&2
unzip -oj "$ZIPFILE" module.prop -d $MODPATH/ >&2
unzip -oj "$ZIPFILE" post-fs-data.sh -d $MODPATH/ >&2 
echo -ne '\x50\x4b\x05\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' > $MODPATH/$MEDIAPATH/theme/default/dynamicicons
set_perm_recursive $MODPATH 0 0 0755 0644

rm -rf /data/system/package_cache/*
echo "√ 安装成功，请重启设备"
echo "√ Installation successful, please restart the device"
echo "---------------------------------------------"

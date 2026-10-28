@echo off
chcp 65001 >nul
setlocal
set "DESK=%USERPROFILE%\Desktop"
set "SMDIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Anaconda (anaconda3)"
set "BAK=D:\AnacondaHanhua\shortcut_backup"

echo ============================================
echo  Anaconda Navigator 汉化  卸载 / 还原
echo ============================================
echo.

echo [1/3] 还原桌面快捷方式...
if exist "%BAK%\desktop_Anaconda Navigator.lnk" (
    copy /y "%BAK%\desktop_Anaconda Navigator.lnk" "%DESK%\Anaconda Navigator.lnk" >nul
    echo   桌面快捷方式已还原为官方英文入口
) else (
    echo   未找到备份，改用直接写回官方参数
    powershell -NoProfile -Command ^
      "$s=New-Object -ComObject WScript.Shell; $l=$s.CreateShortcut('%DESK%\Anaconda Navigator.lnk'); $l.TargetPath='D:\anaconda3\pythonw.exe'; $l.Arguments='D:\anaconda3\cwp.py D:\anaconda3 D:\anaconda3\pythonw.exe D:\anaconda3\Scripts\anaconda-navigator-script.py'; $l.WorkingDirectory='%USERPROFILE%'; $l.IconLocation='D:\anaconda3\Menu\anaconda-navigator.ico,0'; $l.Save()"
)

echo [2/3] 还原开始菜单快捷方式...
if exist "%BAK%\startmenu_Anaconda Navigator.lnk" (
    copy /y "%BAK%\startmenu_Anaconda Navigator.lnk" "%SMDIR%\Anaconda Navigator.lnk" >nul
    echo   开始菜单快捷方式已还原
) else (
    echo   未找到开始菜单备份，跳过
)

echo [3/3] 刷新图标缓存...
ie4uinit.exe -show >nul 2>&1

echo.
echo 还原完成。汉化文件仍保留在 D:\AnacondaHanhua，
echo 需要彻底移除请直接删除该目录即可。
echo 启动 Navigator 将恢复英文界面。
echo.
pause

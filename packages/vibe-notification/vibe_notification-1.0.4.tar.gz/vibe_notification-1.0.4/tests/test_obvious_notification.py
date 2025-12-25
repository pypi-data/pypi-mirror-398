#!/usr/bin/env python3
"""
更明显的通知测试
"""

import subprocess
import time

# 发送一个带有声音的Toast通知
ps_command = '''
Add-Type -AssemblyName System.Runtime.WindowsRuntime
Add-Type -AssemblyName System.Windows.Forms

# 发送Toast
try {
    $asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where { $_.Name -eq 'AsTask' } | Where {$_.GetParameters().Count -eq 1})[0]
    Function Await($WinRtTask, $ResultSig) {
        $asTask = $asTaskGeneric.MakeGenericMethod($ResultSig)
        $netTask = $asTask.Invoke($null, @($WinRtTask))
        $netTask.Wait(-1) | Out-Null
    }
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    [Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom, ContentType = WindowsRuntime] | Out-Null
    $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
    $xml.LoadXml("<toast scenario='reminder'><visual><binding template='ToastGeneric'><text>WSL测试通知</text><text>如果你看到这条消息，说明通知系统正常工作！</text></binding></visual></toast>")
    $toast = New-Object Windows.UI.Notifications.ToastNotification($xml)
    $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("WSL Test")
    $notifier.Show($toast)
    Write-Host "Toast sent"
} catch {
    Write-Host "Toast failed: $_"
}

# 播放声音
Start-Sleep 0.5
[console]::beep(800, 300)

'''

print("发送测试通知...")
result = subprocess.run(["powershell.exe", "-Command", ps_command], capture_output=True, text=True)
print("输出:", result.stdout)
if result.stderr:
    print("错误:", result.stderr)
print("返回码:", result.returncode)

# 等待3秒
time.sleep(3)

print("\n测试完成！")
print("如果听到声音但没有看到通知，请检查：")
print("1. Windows设置 > 系统 > 通知和操作 > 获取来自应用和其他发送者的通知")
print("2. 检查通知中心是否有'WSL测试通知'")
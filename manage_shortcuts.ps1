[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][ValidateSet('Install', 'Restore')][string]$Action,
    [string]$AnacondaRoot,
    [string]$DesktopDirectory,
    [string]$StartMenuDirectory,
    [string]$BackupDirectory,
    [switch]$NonInteractive
)

# Windows PowerShell 5.1 compatible. No Python modules, GUI launch, icon refresh,
# shell evaluation of path strings, or machine-specific installation paths.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$packageDirectory = $PSScriptRoot
$stages = New-Object System.Collections.Generic.List[string]
$before = @()
$committing = $false

function Full-Path([string]$Path) {
    return [IO.Path]::GetFullPath([Environment]::ExpandEnvironmentVariables($Path))
}

function Read-Shortcut([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    $link = $script:shell.CreateShortcut($Path)
    return [pscustomobject]@{
        TargetPath = [string]$link.TargetPath
        Arguments = [string]$link.Arguments
        WorkingDirectory = [string]$link.WorkingDirectory
        IconLocation = [string]$link.IconLocation
        Description = [string]$link.Description
        Hotkey = [string]$link.Hotkey
        WindowStyle = [int]$link.WindowStyle
    }
}

function Same-Shortcut($Actual, $Expected) {
    if ($null -eq $Actual -or $null -eq $Expected) { return $false }
    foreach ($name in @('TargetPath', 'WorkingDirectory', 'IconLocation')) {
        if (-not [string]::Equals($Actual.$name, $Expected.$name, [StringComparison]::OrdinalIgnoreCase)) { return $false }
    }
    foreach ($name in @('Arguments', 'Description', 'Hotkey', 'WindowStyle')) {
        if ($Actual.$name -cne $Expected.$name) { return $false }
    }
    return $true
}

function Assert-Root([string]$Root) {
    $resolved = Full-Path $Root
    foreach ($relative in @('pythonw.exe', 'cwp.py', 'Scripts\anaconda-navigator-script.py', 'Menu\anaconda-navigator.ico')) {
        if (-not (Test-Path -LiteralPath (Join-Path $resolved $relative) -PathType Leaf)) {
            throw "Invalid Anaconda root: missing $relative in $resolved"
        }
    }
    return (Get-Item -LiteralPath $resolved).FullName
}

function Root-FromShortcut($Snapshot) {
    if ($null -eq $Snapshot -or -not $Snapshot.TargetPath) { return $null }
    $target = Full-Path $Snapshot.TargetPath
    $parent = Split-Path -Parent $target
    if ([IO.Path]::GetFileName($parent) -ieq 'Scripts') { $parent = Split-Path -Parent $parent }
    try { return Assert-Root $parent } catch { return $null }
}

function Is-Official($Snapshot, [string]$Root) {
    if ($null -eq $Snapshot) { return $false }
    if (-not (Test-Path -LiteralPath $Snapshot.TargetPath -PathType Leaf)) { return $false }
    $detected = Root-FromShortcut $Snapshot
    if (-not $detected -or -not [string]::Equals($detected, $Root, [StringComparison]::OrdinalIgnoreCase)) { return $false }
    if ([IO.Path]::GetFileName($Snapshot.TargetPath) -ieq 'anaconda-navigator.exe') { return $true }
    $officialEntry = Join-Path $Root 'Scripts\anaconda-navigator-script.py'
    return ($Snapshot.Arguments.IndexOf($officialEntry, [StringComparison]::OrdinalIgnoreCase) -ge 0 -and
            $Snapshot.Arguments -notmatch '(?i)launch_zh\.py')
}

function New-Snapshot([string]$Root, [string]$Entry) {
    # Each argument is independently quoted so spaces survive cwp.py's argv.
    $arguments = '"{0}" "{1}" "{2}" "{3}"' -f (Join-Path $Root 'cwp.py'), $Root, (Join-Path $Root 'pythonw.exe'), $Entry
    return [pscustomobject]@{
        TargetPath = Join-Path $Root 'pythonw.exe'
        Arguments = $arguments
        WorkingDirectory = $Root
        IconLocation = (Join-Path $Root 'Menu\anaconda-navigator.ico') + ',0'
        Description = 'Anaconda Navigator'
        Hotkey = ''
        WindowStyle = 1
    }
}

function Save-Shortcut([string]$Path, $Snapshot) {
    $link = $script:shell.CreateShortcut($Path)
    foreach ($name in @('TargetPath', 'Arguments', 'WorkingDirectory', 'IconLocation', 'Description', 'Hotkey', 'WindowStyle')) {
        $link.$name = $Snapshot.$name
    }
    $link.Save()
    if (-not (Same-Shortcut (Read-Shortcut $Path) $Snapshot)) { throw "Shortcut verification failed: $Path" }
}

try {
    $script:shell = New-Object -ComObject WScript.Shell
    if (-not $DesktopDirectory) { $DesktopDirectory = [Environment]::GetFolderPath('DesktopDirectory') }
    if (-not $StartMenuDirectory) { $StartMenuDirectory = Join-Path ([Environment]::GetFolderPath('Programs')) 'Anaconda (anaconda3)' }
    if (-not $BackupDirectory) { $BackupDirectory = Join-Path $packageDirectory 'shortcut_backup' }
    if (-not $DesktopDirectory -or -not $StartMenuDirectory) { throw 'Windows known-folder lookup returned an empty path.' }
    $DesktopDirectory = Full-Path $DesktopDirectory
    $StartMenuDirectory = Full-Path $StartMenuDirectory
    $BackupDirectory = Full-Path $BackupDirectory
    $destinations = @(
        [pscustomobject]@{ Name = 'desktop'; Path = Join-Path $DesktopDirectory 'Anaconda Navigator.lnk'; Backup = Join-Path $BackupDirectory 'desktop_Anaconda Navigator.lnk' },
        [pscustomobject]@{ Name = 'startmenu'; Path = Join-Path $StartMenuDirectory 'Anaconda Navigator.lnk'; Backup = Join-Path $BackupDirectory 'startmenu_Anaconda Navigator.lnk' }
    )
    if ([string]::Equals($destinations[0].Path, $destinations[1].Path, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'DesktopDirectory and StartMenuDirectory must be different directories.'
    }
    foreach ($destination in $destinations) {
        if ([string]::Equals($destination.Path, $destination.Backup, [StringComparison]::OrdinalIgnoreCase)) { throw 'Backup and destination paths overlap.' }
    }
    if ($AnacondaRoot) {
        $AnacondaRoot = Assert-Root $AnacondaRoot
    } else {
        foreach ($path in @($destinations[0].Path, $destinations[1].Path, $destinations[0].Backup, $destinations[1].Backup)) {
            try { $AnacondaRoot = Root-FromShortcut (Read-Shortcut $path) } catch { $AnacondaRoot = $null }
            if ($AnacondaRoot) { break }
        }
        if (-not $AnacondaRoot) { throw 'Anaconda root was not detected. Pass -AnacondaRoot with the installation directory.' }
    }
    $entry = Join-Path $AnacondaRoot 'Scripts\anaconda-navigator-script.py'
    if ($Action -eq 'Install') {
        foreach ($file in @('launch_zh.py', 'zhcn_boot.py', 'nav_zh_dict.py')) {
            if (-not (Test-Path -LiteralPath (Join-Path $packageDirectory $file) -PathType Leaf)) { throw "Incomplete Chinese package: $file" }
        }
        $entry = Join-Path $packageDirectory 'launch_zh.py'
    }
    $generated = New-Snapshot $AnacondaRoot $entry
    $updates = @()
    foreach ($destination in $destinations) {
        $current = Read-Shortcut $destination.Path
        $expected = $generated
        $restoreSource = $null
        if ($Action -eq 'Restore') {
            $backup = Read-Shortcut $destination.Backup
            # Stale/moved/Chinese backups are not written back as working links.
            if (Is-Official $backup $AnacondaRoot) { $expected = $backup; $restoreSource = $destination.Backup }
        }
        $existed = Test-Path -LiteralPath $destination.Path -PathType Leaf
        $bytes = $null
        if ($existed) { $bytes = [IO.File]::ReadAllBytes($destination.Path) }
        $before += [pscustomobject]@{ Path = $destination.Path; Existed = $existed; Bytes = $bytes }
        if (Same-Shortcut $current $expected) {
            $updates += [pscustomobject]@{ Destination = $destination; Expected = $expected; Stage = $null }
            continue
        }
        $directory = Split-Path -Parent $destination.Path
        [void](New-Item -ItemType Directory -Force -Path $directory)
        $stage = Join-Path $directory ('.anaconda-zh-' + [guid]::NewGuid().ToString('N') + '.lnk')
        $stages.Add($stage)
        if ($restoreSource) {
            Copy-Item -LiteralPath $restoreSource -Destination $stage
            if (-not (Same-Shortcut (Read-Shortcut $stage) $expected)) { throw "Backup verification failed: $restoreSource" }
        } else { Save-Shortcut $stage $expected }
        if ($Action -eq 'Install' -and $existed -and -not (Test-Path -LiteralPath $destination.Backup)) {
            # Never mistake a previous Chinese launcher for an English backup.
            if (Is-Official $current $AnacondaRoot) {
                [void](New-Item -ItemType Directory -Force -Path $BackupDirectory)
                Copy-Item -LiteralPath $destination.Path -Destination $destination.Backup
                if (-not (Same-Shortcut (Read-Shortcut $destination.Backup) $current)) { throw "Original backup verification failed: $($destination.Backup)" }
            }
        }
        $updates += [pscustomobject]@{ Destination = $destination; Expected = $expected; Stage = $stage }
    }
    $committing = $true
    foreach ($update in $updates) {
        if ($update.Stage) { Move-Item -LiteralPath $update.Stage -Destination $update.Destination.Path -Force }
    }
    foreach ($update in $updates) {
        if (-not (Same-Shortcut (Read-Shortcut $update.Destination.Path) $update.Expected)) { throw "Final verification failed: $($update.Destination.Path)" }
        Write-Output ("VERIFIED {0}: {1}" -f $update.Destination.Name, $update.Destination.Path)
    }
    $committing = $false
    Write-Output ("SUCCESS {0}: 2 shortcuts verified; AnacondaRoot={1}" -f $Action, $AnacondaRoot)
    exit 0
} catch {
    $failure = $_.Exception.Message
    if ($committing) {
        foreach ($previous in $before) {
            try {
                if ($previous.Existed) {
                    $unchanged = $false
                    if (Test-Path -LiteralPath $previous.Path -PathType Leaf) {
                        $unchanged = [Convert]::ToBase64String([IO.File]::ReadAllBytes($previous.Path)) -ceq [Convert]::ToBase64String($previous.Bytes)
                    }
                    if (-not $unchanged) { [IO.File]::WriteAllBytes($previous.Path, $previous.Bytes) }
                    if ([Convert]::ToBase64String([IO.File]::ReadAllBytes($previous.Path)) -cne [Convert]::ToBase64String($previous.Bytes)) {
                        throw "Rollback byte verification failed: $($previous.Path)"
                    }
                }
                elseif (Test-Path -LiteralPath $previous.Path -PathType Leaf) { Remove-Item -LiteralPath $previous.Path -Force }
            } catch { [Console]::Error.WriteLine('ROLLBACK ERROR: ' + $_.Exception.Message) }
        }
    }
    [Console]::Error.WriteLine('ERROR: ' + $failure)
    exit 1
} finally {
    foreach ($stage in $stages) {
        if (Test-Path -LiteralPath $stage -PathType Leaf) { Remove-Item -LiteralPath $stage -Force -ErrorAction SilentlyContinue }
    }
}

param(
    [ValidateSet('Install','Uninstall','Verify')][string]$Action='Install',
    [string]$GamePath="E:\SteamLibrary\steamapps\common\Tomoyo After ~It's a Wonderful Life~ English Edition"
)
$ErrorActionPreference='Stop'
$game=[IO.Path]::GetFullPath($GamePath).TrimEnd('\')
$package=$PSScriptRoot
function Under([string]$root,[string]$relative) {
    $target=[IO.Path]::GetFullPath((Join-Path $root $relative))
    if(-not $target.StartsWith($root.TrimEnd('\')+'\',[StringComparison]::OrdinalIgnoreCase)){throw "Path outside target directory: $relative"}
    return $target
}
function Hash([string]$path){return (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()}
function Parent([string]$path){[IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($path)) | Out-Null}
function Copy-Exact([string]$from,[string]$to){Parent $to;[IO.File]::Copy($from,$to,$true)}
function Write-Json($value,[string]$path){Parent $path;[IO.File]::WriteAllText($path,($value | ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))}
$stateDir=Under $game 'TASteamCN_Backups'
$active=Under $stateDir 'active.json'
if(-not (Test-Path -LiteralPath (Under $game 'RealLiveEn.exe'))){throw 'RealLiveEn.exe was not found. Supply -GamePath.'}
$spec=Get-Content -LiteralPath (Join-Path $package 'manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
foreach($original in $spec.originals){
    if((Hash (Under $game $original.path)) -ne $original.sha256){throw "Unsupported original file: $($original.path). No files were changed."}
}
if($Action -eq 'Verify'){
    $bad=@()
    foreach($file in $spec.files){$p=Under $game $file.path;if(-not(Test-Path -LiteralPath $p) -or (Hash $p) -ne $file.sha256){$bad+=$file.path}}
    if($bad.Count){throw ('Patch verification failed: '+($bad -join ', '))}
    Write-Host "Verified $($spec.files.Count) patch files; original Steam EXE and DLLs are intact."
    exit 0
}
if(Get-Process -Name RealLiveEn -ErrorAction SilentlyContinue){throw 'Close Tomoyo After before installing or uninstalling.'}
function Restore($record,[string]$backup){
    $saves=Under $game 'SAVEDATA'
    $originalSaves=Under $backup 'original-saves'
    if(Test-Path -LiteralPath $originalSaves){
        if(Test-Path -LiteralPath $saves){
            $archive=Under $stateDir ('Chinese-saves-'+(Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
            # Both resolved absolute paths have been checked to stay in the game directory.
            Move-Item -LiteralPath $saves -Destination $archive
            Write-Host "Chinese saves preserved: $archive"
        }
        [IO.Directory]::CreateDirectory($saves) | Out-Null
        foreach($f in Get-ChildItem -LiteralPath $originalSaves -Recurse -File){
            $relative=$f.FullName.Substring($originalSaves.Length+1)
            Copy-Exact $f.FullName (Under $saves $relative)
        }
    }
    foreach($file in $record.files){
        $target=Under $game $file.path
        if($file.existed){Copy-Exact (Under (Under $backup 'files') $file.path) $target}
        elseif(Test-Path -LiteralPath $target){
            if((Hash $target) -ne $file.patchedHash){Copy-Exact $target (Under (Under $backup 'changed-patch-files') $file.path)}
            Remove-Item -LiteralPath $target
        }
    }
}
if($Action -eq 'Uninstall'){
    if(-not(Test-Path -LiteralPath $active)){throw 'No active installation record was found.'}
    $pointer=Get-Content -LiteralPath $active -Raw -Encoding UTF8 | ConvertFrom-Json
    $backup=Under $stateDir $pointer.backup
    $record=Get-Content -LiteralPath (Under $backup 'restore.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    Restore $record $backup
    Remove-Item -LiteralPath $active
    Write-Host 'Original Steam files and saves restored. Backups are retained.'
    exit 0
}
if(Test-Path -LiteralPath $active){throw 'Patch is already installed. Use Verify or Uninstall first.'}
$backupName=Get-Date -Format 'yyyyMMdd-HHmmss-fff'
$backup=Under $stateDir $backupName
$records=@()
foreach($file in $spec.files){
    $source=Under (Join-Path $package 'payload') $file.path
    if((Hash $source) -ne $file.sha256){throw "Damaged patch file: $($file.path)"}
    $target=Under $game $file.path
    $exists=Test-Path -LiteralPath $target
    if($exists){Copy-Exact $target (Under (Under $backup 'files') $file.path)}
    $records+=@{path=$file.path;existed=$exists;patchedHash=$file.sha256}
}
$record=@{version=$spec.version;files=$records}
Write-Json $record (Under $backup 'restore.json')
try {
    $saves=Under $game 'SAVEDATA'
    if(Test-Path -LiteralPath $saves){
        # Move only the explicitly resolved game SAVEDATA directory into its checked backup directory.
        Move-Item -LiteralPath $saves -Destination (Under $backup 'original-saves')
    }
    [IO.Directory]::CreateDirectory($saves) | Out-Null
    foreach($file in $spec.files){Copy-Exact (Under (Join-Path $package 'payload') $file.path) (Under $game $file.path)}
    Write-Json @{backup=$backupName;version=$spec.version} $active
} catch {
    Restore $record $backup
    throw
}
Write-Host "Installed $($spec.files.Count) files. Launch Tomoyo After normally from Steam."
Write-Host "Original files and English saves: $backup"

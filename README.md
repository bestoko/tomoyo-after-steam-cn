# tomoyo-after-steam-cn

《智代 After ～It's a Wonderful Life～》Steam English Edition 简体中文补丁的个人兼容整合与维护仓库。

源码和维护资料保存在 Git；可安装成品放在 [Releases](https://github.com/bestoko/tomoyo-after-steam-cn/releases)。

| 版本 | 当前状态 |
| --- | --- |
| R18 汉化补丁 | 0.1 实验版，已完成本机安装及部分剧情验证 |
| 全年龄汉化补丁 | 待补充成品，暂不提供下载 |

## 下载与使用

在 Releases 下载对应版本的 ZIP，解压后阅读包内 `使用说明.md`，关闭游戏并运行 `安装补丁.cmd`。安装后从 Steam 库启动游戏。

默认支持目录为 `E:\SteamLibrary\steamapps\common\Tomoyo After ~It's a Wonderful Life~ English Edition`。安装到其他位置时，在补丁目录运行：

```powershell
powershell.exe -NoProfile -File .\Manage-Patch.ps1 -Action Install -GamePath "你的游戏目录"
```

包内同时提供校验和卸载恢复工具。请保留游戏目录内的 `TASteamCN_Backups`。

## Steam 兼容与验证范围

针对 Steam App **462990**、build **3159213**。保留原版 `RealLiveEn.exe`、`rlSteam.dll`、`steam_api.dll`，用新增的 `ta_cn.dll` 处理 GBK 字符和中文字形，并将成就调用接回剧情事件。

R18 版实测 Steam 正常启动、游玩时间记录、汉字显示、存读档，以及序章和数学测验全对这两项成就。其余成就尚未逐项通关验证；完整 D&T 与卡牌掉落尚未验证。剧情沿用旧 R18 汉化，未完整移植 Steam Memorial Edition 的全部新增剧情和结局。

**存档注意：** 两版存档不保证互通。Steam 云同步共用 `SAVEDATA`，会重新下载旧存档，本地备份不能保证云端隔离；请从 Start 新开游戏，避免载入英文版旧档。

详见 [使用说明](docs/r18-usage.md) 和 [验证记录](docs/r18-validation.md)。

## 仓库结构与维护

- `source/`：本次新增的原生 DLL 源码、脚本生成与打包辅助脚本。
- `installer/`：安装、校验和恢复脚本，发布时与 `payload/`、`manifest.json` 放在同一目录。
- `patches/r18/`：R18 成品文件清单、成就事件接入记录、静态检查结果。
- `patches/all-ages/`：全年龄版本状态。
- `docs/`：使用、验证、原汉化人员署名和重建说明。
- `tools/`：Release 打包工具。

现有构建脚本保存了实验实现，依赖用户本地原始游戏、汉化输入、提取数据和 RLDev 工具；这个仓库并非无需额外输入即可重建的完整工程。详见 [重建说明](docs/BUILD.md)。

## 来源

原汉化来自 TOMO、KFC 等制作人员的 v1.2 汉化补丁，人员与原说明见 [原汉化版本说明](docs/原汉化版本说明.txt)。本项目进行 Steam 版本兼容整合，不代表原汉化团队。

字节码分析采用 [RLDev Go](https://github.com/yoremi-trad-fr/rldev2026-go-edition)，本次使用提交 `1c0f847fe0e1940c7084b1f0670130ab67af459c`。游戏和原汉化内容的权利归各自权利人所有，本仓库不对它们另行授予许可。

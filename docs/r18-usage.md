# 智代 After Steam 18 禁整合汉化补丁（个人实验版 0.1）

目标：Steam App 462990，build 3159213，当前安装的 English Edition。

下载 Release 成品并安装后，从 Steam 库点击“开始游戏”，不要启动旧汉化 EXE。

## 文件与安装

- `安装补丁.cmd`：关闭游戏后运行。其他位置可用 `Manage-Patch.ps1 -Action Install -GamePath "游戏目录"`。
- `校验补丁.cmd`：检查补丁文件及 Steam 原始 EXE、接口 DLL 的 SHA-256。
- `卸载并恢复原版.cmd`：恢复安装前的原版文件与英文版存档，同时保留汉化存档备份。
- 安装备份保存在游戏目录 `TASteamCN_Backups`。请保留该目录。
- 安装器会将现有 `SAVEDATA` 整体移入备份，再建立本地存档目录。但 Steam 云同步仍然共用 `SAVEDATA`，实测会重新下载旧存档，**不能保证两版云存档隔离**。请勿在汉化版载入原英文版存档；从 Start 开始新游戏。切换版本前保留 `TASteamCN_Backups` 和自己的存档副本。补丁不自动修改 Steam 云设置。
- 收尾时已归档测试用的手动存档槽；游戏可能仍保留测试期间的已读和系统设置。原英文版存档在安装备份内。测试已实际解锁两项 Steam 成就，测试运行时长也已经计入 Steam。

## 内容与 Steam 功能

以你提供的 v1.2 18 禁汉化剧情、图形和语音为基础，保留 Steam 原版 `RealLiveEn.exe`、`rlSteam.dll`、`steam_api.dll`。新增 `ta_cn.dll` 负责 GBK 字符解析和中文字形。

Steam 成就调用已接回剧情与 D&T 的实际事件条件。D&T 的相关机制脚本采用当前 Steam 原版，中文剧情与汉化图形继续沿用原补丁。没有提供一键解锁、成就编辑或伪造进度功能。

Steam 的数学测验在旧 18 禁剧情中不存在。现将你提供的全年龄汉化中的测验作为 6 月 30 日结束前的可选追加事件，选择 `Play the Steam bonus math quiz` 即可游玩；选择 `Continue the main story` 则继续原剧情。全答对才触发对应成就。

剧情继承旧 18 禁版本。这不是对 Steam Memorial Edition 所有新增剧情、结局的完整移植。普通系统确认对话框保留英文，以避免两种编码混用造成乱码。

## 验证范围

详见同目录 `验证记录.md`。此版本尚未完成全篇、所有分支与完整 D&T 通关，未逐项实测的成就不能视为已经保证。掉卡没有单独验证，仍取决于 Steam 对账号和游戏的正常掉落资格。

## 来源与重建

汉化内容来自用户提供的 TOMO/KFC 等原制作人员的 v1.2 补丁，完整名单见原包 `版本说明.txt`；本次仅进行本机兼容整合。

字节码分析采用 RLDev Go，仓库 https://github.com/yoremi-trad-fr/rldev2026-go-edition ，本次源码提交 `1c0f847fe0e1940c7084b1f0670130ab67af459c`。本次新增代码见 `source`。

重建脚本依赖本工作目录 `research` 中从用户文件提取的数据和 RLDev 工具；`source` 用于审阅实现，并非脱离这些输入的独立完整构建包。

# 重建与维护说明

当前公开源码为 0.1 实验版实现快照。运行前请审阅脚本：部分脚本仍使用原实验目录名称和默认 Steam 路径，`finish_config.py` 会复制配置到该 Steam 路径。

## 原生 DLL

在安装 Visual Studio 2022 Build Tools 的 Windows 主机上，进入 `source` 并运行 `build-native.cmd`，使用 x86 MSVC 编译 `ta_cn.dll`。当前脚本中的工具链路径为默认 Build Tools 安装位置，必要时调整。

DLL 在游戏进程内处理字符编码与字形，不替换 Steam 接口 DLL，不直接写入 Steam 成就或游玩时间。

## 剧情与资源

`build_patch.py`、`patch_bytecode.py` 依赖同目录的 `cn-raw`、`cn-json`、`steam-raw`、`steam-json`、`allages-raw`、`allages-json`、`compiled`、`cn-extracted` 等本地输入，以及 `rldev-go/common/pkg/compression/compression.go` 中的格式常量。

这些输入来自用户原游戏与原汉化的本地提取，不存入 Git。实验生成的 JSON 还依赖对 RLDev 检查器增加的指令偏移和重定位信息；当前仓库没有提供完整自动提取流水线。不要将此快照当作无需准备即可运行的一键构建。

脚本中 `Steam整合汉化补丁` 输出目录及 `[Windows]` 开头的本地输入目录沿用原工作区约定。移植工作目录时，需要调整相关路径。发布前重新生成 manifest，检查其原版 EXE/DLL 哈希来自正确的 Steam 安装，验证脚本重定位、真实剧情事件及最终安装。

## 发布

将已验证的成品目录作为输入：

```powershell
python .\tools\package_release.py --package "已验证的成品目录" --output .\dist\tomoyo-after-steam-cn-r18-v0.1.0.zip
```

工具在打包前校验 manifest 中列出的全部 payload 文件，生成 ZIP 和 SHA-256 文件。成品 ZIP 不加入 Git，通过 GitHub Releases 附件发布。版本更新时同时更新成品 manifest、对应版本文档及验证范围。

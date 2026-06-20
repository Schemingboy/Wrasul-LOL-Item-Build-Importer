# Wrasul LOL Item Build Importer

把 Wrasul 发布的英雄联盟出装 JSON 导入到本地英雄联盟物品方案目录。

项目中文名可以理解为：`Wrasul-LOL-装备导入器`。GitHub 仓库名建议使用英文：

```text
Wrasul-LOL-Item-Build-Importer
```

## 它做什么

脚本读取 B 站动态 URL 或本地 JSON 文件，提取英雄联盟 item set JSON，校验格式，然后写入：

```text
<League of Legends>\Config\Champions\<ChampionKey>\Recommended\
```

默认按英雄拆分安装。也可以用 `--target global` 写入：

```text
<League of Legends>\Config\Global\Recommended\
```

## 安全边界

这个工具只处理 Riot 客户端支持的本地物品方案 JSON 文件。

它不会：

- 读取或修改游戏进程内存
- 注入 DLL
- 模拟按键鼠标
- 拦截或改写网络请求
- 保存 Riot 账号、密码、令牌或登录态

安装前请关闭英雄联盟客户端和游戏。脚本默认会检测客户端进程，发现正在运行时拒绝写入。

## 使用方法

源码运行：

```powershell
$env:PYTHONPATH="src"
python -m wrasul_lol_item_build_importer --source "https://www.bilibili.com/opus/1213040949301608448" --target global --output wrasul.json
```

先 dry-run，确认会写哪些文件：

```powershell
$env:PYTHONPATH="src"
python -m wrasul_lol_item_build_importer --source "https://www.bilibili.com/opus/1213040949301608448" --lol-dir "C:\Riot Games\League of Legends"
```

确认无误后安装：

```powershell
$env:PYTHONPATH="src"
python -m wrasul_lol_item_build_importer --source "https://www.bilibili.com/opus/1213040949301608448" --lol-dir "C:\Riot Games\League of Legends" --install
```

从本地 JSON 文件安装：

```powershell
$env:PYTHONPATH="src"
python -m wrasul_lol_item_build_importer --source ".\wrasul.json" --lol-dir "C:\Riot Games\League of Legends" --install
```

## 参数

- `--source`：必填。B 站动态 URL 或本地 JSON 文件。
- `--lol-dir`：英雄联盟安装根目录。
- `--install`：真正写入文件。不加这个参数时只 dry-run。
- `--target champion|global`：默认 `champion`，按英雄目录安装；`global` 写入全局目录。
- `--output`：导出提取和规范化后的 JSON。
- `--keep-old`：保留同前缀旧文件。
- `--prefix`：生成文件名前缀，默认 `wrasul`。

## 验证

```powershell
python -m unittest discover -s tests
```

当前测试覆盖：

- 从 B 站 HTML 形态中提取转义 JSON
- 校验 item set / block / item 基本结构
- dry-run 不写磁盘
- 安装到临时目录
- 备份并替换旧的生成文件

## 说明

B 站动态内容属于发布者。仓库只保留最小示例，不内置完整版本出装内容。每次新版本发布后，使用新的动态 URL 运行脚本即可。

## Riot 声明

Wrasul LOL Item Build Importer is not endorsed by Riot Games and does not reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games and all associated properties are trademarks or registered trademarks of Riot Games, Inc.

# Wrasul LOL Item Build Importer

小白版英雄联盟出装导入器：双击打开，粘贴 Wrasul 的 B 站动态链接，点一下导入。

## 普通用户怎么用

1. 打开 GitHub Release，下载 `Wrasul-LOL-Item-Build-Importer.exe`。
2. 关闭英雄联盟客户端和游戏。
3. 双击打开 EXE。
4. 粘贴 Wrasul 的 B 站动态链接。
5. 确认 `League of Legends` 文件夹路径。
6. 点击“导入出装”。
7. 打开英雄联盟，在商店的物品方案里查看。

项目地址：

```text
https://github.com/Schemingboy/Wrasul-LOL-Item-Build-Importer
```

## 它做什么

工具读取 B 站动态中的出装 JSON，然后写入英雄联盟客户端支持的本地物品方案目录：

```text
<League of Legends>\Config\Champions\<ChampionKey>\Recommended\
```

默认会按英雄安装，并在写入前备份旧的 `wrasul-*.json` 文件。

## 安全边界

这个工具只处理 Riot 客户端支持的本地物品方案 JSON 文件。

它不会：

- 读取或修改游戏进程内存
- 注入 DLL
- 模拟按键鼠标
- 拦截或改写网络请求
- 保存 Riot 账号、密码、令牌或登录态

如果检测到英雄联盟客户端正在运行，工具会拒绝写入。先关闭客户端再导入。

## 常见问题

### 找不到 League of Legends 文件夹怎么办？

点击“浏览...”，选择你的英雄联盟安装目录。常见路径是：

```text
C:\Riot Games\League of Legends
D:\Riot Games\League of Legends
```

### 导入失败怎么办？

先检查三件事：

1. 英雄联盟客户端和游戏是否已经关闭。
2. B 站动态链接是否能正常打开。
3. 选择的目录是否真的是 `League of Legends` 文件夹。

### 会不会影响账号安全？

工具不读取账号、不登录 Riot、不碰游戏进程，只写本地物品方案 JSON。它的作用更接近“帮你把出装方案文件放到正确文件夹”。

## 开发者 / 高级用法

源码运行 GUI：

```powershell
$env:PYTHONPATH="src"
python -m wrasul_lol_item_build_importer.gui
```

命令行导入：

```powershell
$env:PYTHONPATH="src"
python -m wrasul_lol_item_build_importer --source "https://www.bilibili.com/opus/1213040949301608448" --lol-dir "C:\Riot Games\League of Legends" --install
```

运行测试：

```powershell
python -m unittest discover -s tests
```

构建 EXE：

```powershell
.\build_exe.ps1
```

构建产物：

```text
dist\Wrasul-LOL-Item-Build-Importer.exe
```

## Riot 声明

Wrasul LOL Item Build Importer is not endorsed by Riot Games and does not reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games and all associated properties are trademarks or registered trademarks of Riot Games, Inc.

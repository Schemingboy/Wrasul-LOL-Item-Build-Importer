---
title: 安全边界
date: 2026-06-20
modified: 2026-06-20
tags: [league-of-legends, item-sets, safety]
status: stable
---

# 安全边界

这个项目的目标是导入英雄联盟客户端支持的本地物品方案 JSON。它不是自动化游戏工具，也不是外挂工具。

## 允许做的事

读写这些目录里的 JSON 文件：

```text
<League of Legends>\Config\Global\Recommended\
<League of Legends>\Config\Champions\<ChampionKey>\Recommended\
```

这些文件的作用是让客户端在商店里显示自定义物品方案，等价于用户手动维护本地出装方案。

## 不做的事

- 不读取或修改游戏进程内存
- 不注入 DLL
- 不模拟键鼠操作
- 不读写网络封包
- 不修改客户端可执行文件
- 不保存 Riot 账号、密码、令牌或登录态

## 操作原则

安装前关闭英雄联盟客户端和游戏。原因不是规避检测，而是避免客户端运行时刷新配置，导致写入结果被覆盖。

脚本默认会备份旧的同前缀生成文件，再写入新文件。备份目录在：

```text
<League of Legends>\Config\wrasul-backups\
```

## 风险判断

这个项目的风险边界主要是文件写错位置或覆盖用户原有配置，所以默认策略是：

- 必须由用户显式提供 `--lol-dir`
- 不加 `--install` 时只做 dry-run
- 只删除同前缀生成文件
- 不扫描账号数据或客户端内部状态

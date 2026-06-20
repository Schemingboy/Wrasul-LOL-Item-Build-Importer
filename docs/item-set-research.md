---
title: 英雄联盟物品方案调研
date: 2026-06-20
modified: 2026-06-20
tags: [league-of-legends, item-sets, json]
status: stable
---

# 英雄联盟物品方案调研

结论：Wrasul B 站动态里的内容是英雄联盟 item set JSON 数组。脚本可以直接提取、校验并写入本地 `Recommended` 目录。

## JSON 形态

单个物品方案包含：

- `title`：方案标题
- `associatedMaps`：地图编号，例如召唤师峡谷常见为 `11`
- `associatedChampions`：英雄数字编号，例如薇恩是 `67`
- `blocks`：商店里显示的分组
- `blocks[].items`：物品列表，物品 id 是字符串或数字

## 安装目录

默认安装到英雄目录：

```text
<League of Legends>\Config\Champions\<ChampionKey>\Recommended\
```

例如：

```text
<League of Legends>\Config\Champions\Vayne\Recommended\wrasul-001-Sample-ADC-Build.json
```

如果出装没有绑定英雄，或者用户指定 `--target global`，则安装到：

```text
<League of Legends>\Config\Global\Recommended\
```

## 英雄编号映射

Wrasul JSON 使用英雄数字编号。英雄目录需要 Data Dragon 英雄 key，例如：

```text
67 -> Vayne
222 -> Jinx
```

脚本默认从 Riot Data Dragon 拉取最新英雄映射。也可以用 `--champion-map` 指定本地映射文件。

## B 站动态

验证过的样例 URL：

```text
https://www.bilibili.com/opus/1213040949301608448
```

页面标题显示为 `LOLv16.12ad装备玩法构筑出装流派推荐`。静态 HTML 中包含转义后的 JSON，可以通过 HTML 反转义后提取。

验证结果：

- 9 个 item sets
- 30 个英雄绑定
- 49 个 blocks
- 489 个 items

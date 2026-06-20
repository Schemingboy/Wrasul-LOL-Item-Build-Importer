# STATUS.md

> 历史进度记录。`AGENTS.md` 不再要求每次会话同步本文件。

更新时间: 2026-06-20
上次会话: 完成英雄联盟装备方案导入脚本，并部署到 GitHub

---

## 当前目标

维护并迭代 `Wrasul-LOL-Item-Build-Importer`，把 Wrasul B 站动态中的英雄联盟出装 JSON 安全转换为本地物品方案文件。

---

## 已完成
- [x] 建立项目规则文件 `AGENTS.md`
- [x] 建立会话状态文件 `STATUS.md`
- [x] 调研 Wrasul B 站动态 JSON 形态
- [x] 实现 Python 命令行导入脚本
- [x] 支持 B 站动态 URL、本地 JSON、dry-run、备份、按英雄目录或全局目录安装
- [x] 补充 README、安全边界文档、item set 调研文档和最小示例
- [x] 添加单元测试
- [x] 初始化 Git 仓库并推送到 GitHub

---

## 关键规则

- 每次会话开始先读 `STATUS.md`
- 每次会话结束最后更新 `STATUS.md`
- 只操作英雄联盟支持的本地物品方案 JSON
- 不碰游戏进程、内存、封包、账号和登录态
- 默认备份后再写入
- 不把 UP 主完整版本出装内容提交进仓库，只保留最小示例

---

## 下次从这里开始

可以从真实 LoL 安装目录 dry-run 开始：

```powershell
$env:PYTHONPATH="src"
python -m wrasul_lol_item_build_importer --source "https://www.bilibili.com/opus/1213040949301608448" --lol-dir "C:\Riot Games\League of Legends"
```

确认路径和文件列表无误后，再加 `--install`。

---

## 不要动这些文件

- 用户的英雄联盟真实配置目录，除非用户明确提供路径并确认执行
- Riot 客户端或游戏进程相关文件
- 账号、登录态、令牌相关文件
- `examples/` 不放 Wrasul 完整版本 JSON

---

## 验证状态

- 已通过：`python -m unittest discover -s tests`
- 已通过：真实 B 站 URL dry-run，提取到 9 个 item sets、30 个英雄绑定、49 个 blocks、489 个 items
- 已通过：临时目录 global 安装验证，生成 `Config\Global\Recommended\wrasul-001-Sample-ADC-Build.json`
- 已通过：GitHub 仓库创建和推送
- GitHub: https://github.com/Schemingboy/Wrasul-LOL-Item-Build-Importer

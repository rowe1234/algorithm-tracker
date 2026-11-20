# algorithm-tracker

Rowe 的个人算法练习看板：自动汇总 Codeforces / 洛谷 / 牛客 / AtCoder 的刷题数据，生成热力图、难度分布、rating 走势和赛事雷达，部署在 GitHub Pages。

## 它有什么

- **总览**：全平台总 AC、Codeforces 当前 / 历史最高 rating、连续打卡天数
- **双热力图**：按天 AC 数热力图 + 按当天最高难度着色的难度热力图（CF 与 AtCoder 合并统计，分天按北京时间）
- **Rating 走势**：Codeforces 全部 rated 比赛的分数曲线，悬停看每场名次与涨跌
- **难度分布 / 近 30 天**：CF 已通过题目的 rating 分布条形图与近 30 天每日 AC 柱状图
- **平台分布**：各平台 AC 数与占比，点按跳转个人主页；自动抓不到的平台会标 `MANUAL`
- **月度趋势 / 目标 / 徽章**：近 12 个月活跃度、目标进度、成就徽章
- **赛事雷达**：未来 Codeforces / AtCoder 比赛（Contest Hive API）
- **今日已解 & 动态流**：当天通过的题目列表、最近提交动态
- **博客**：`posts/` 下的 Markdown 文章；**留言板**：giscus（GitHub 登录）或本地模式
- 多套主题与背景特效（矩阵雨 / 落日 / 紫色星云 / 纸片）

## 数据是怎么更新的

```
GitHub Actions（每 30 分钟，.github/workflows/update.yml）
  └─ python fetch_stats.py
       ├─ Codeforces API：用户信息、全部提交（AC 去重 / 按天统计 / 难度分布）、rating 历史
       ├─ AtCoder Problems API：近一年提交、题目难度与名称
       ├─ 洛谷：个人主页内嵌 JSON 的 passedProblemCount（抓不到时回退手动值）
       ├─ 牛客：主页抓取（经常拿不到，拿不到用手动值 0）
       └─ Contest Hive：未来赛事
  └─ 写回 data.json 并自动提交（"Auto update CP stats"）
index.html 读取 data.json 渲染（纯静态，无构建步骤）
```

手动触发一次更新：仓库 Actions 页选择 “Auto Update CP Stats” → Run workflow；或本地运行 `python fetch_stats.py`（需要 `pip install requests`）。

## 配置

都在 `fetch_stats.py` 末尾的主程序里：

| 配置 | 说明 |
| --- | --- |
| `CF_HANDLE` / `ATCODER_HANDLE` | 平台用户名（当前 Rowe） |
| `LUOGU_UID` / `NOWCODER_ID` | 洛谷 / 牛客的数字 ID |
| `LUOGU_AC_MANUAL` | 洛谷自动抓取失败时的回退值，定期手动对一下 |
| `NOWCODER_AC` | 牛客手动值（抓取兜底） |

页面侧配置（主题、目标、徽章、giscus 等）在 `index.html` 顶部的 `CONFIG` 里。

## 发博客

1. 在 `posts/` 新建 `.md` 文件
2. 在 `posts/posts.json` 里加一条 `{title, date, tags, summary, file}`
3. 推送后 GitHub Pages 自动更新

## 本地预览

```bash
python3 -m http.server 8000
# 打开 http://localhost:8000
```

直接双击 `index.html` 也能看，但 `fetch` 本地文件会被浏览器拦截，建议用上面的静态服务器。

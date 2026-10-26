import requests
import json
import re
import time
from datetime import datetime, timezone


# 1. 抓取 CF 用户信息
def get_cf_user_info(handle):
    url = f"https://codeforces.com/api/user.info?handles={handle}"
    try:
        res = requests.get(url, timeout=10).json()
        if res.get("status") == "OK" and len(res.get("result", [])) > 0:
            user = res["result"][0]
            avatar = user.get("avatar", "")
            if avatar.startswith("//"):
                avatar = "https:" + avatar
            return {
                "rating": user.get("rating", "Unrated"),
                "maxRating": user.get("maxRating", "Unrated"),
                "rank": user.get("rank", "unrated"),
                "avatar": avatar
            }
    except Exception as e:
        print(f"CF user info fetch failed: {e}")
    return {"rating": "N/A", "maxRating": "N/A", "rank": "unrated", "avatar": ""}


# 2. 抓取 CF AC 列表与难度统计
def get_cf_data(handle):
    url = f"https://codeforces.com/api/user.status?handle={handle}"
    try:
        res = requests.get(url, timeout=10).json()
        if res.get("status") != "OK":
            return 0, {}, {}, []

        ac_problems = set()
        daily_stats = {}
        rating_dist = {"<1200": 0, "1200-1399": 0, "1400-1599": 0,
                       "1600-1899": 0, "1900-2099": 0, ">=2100": 0, "Unrated": 0}
        recent_submissions = []

        for sub in res["result"][:10]:
            prob = sub.get("problem", {})
            ts = sub.get("creationTimeSeconds", 0)
            recent_submissions.append({
                "contestId": prob.get("contestId"),
                "index": prob.get("index"),
                "name": prob.get("name", ""),
                "rating": prob.get("rating"),
                "verdict": sub.get("verdict", ""),
                "time": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
                "url": f"https://codeforces.com/contest/{prob.get('contestId')}/problem/{prob.get('index')}"
            })

        for sub in res["result"]:
            if sub.get("verdict") != "OK":
                continue
            prob = sub.get("problem", {})
            p_id = f"{prob.get('contestId')}{prob.get('index')}"
            if p_id in ac_problems:
                continue
            ac_problems.add(p_id)

            ts = sub.get("creationTimeSeconds", 0)
            date_str = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
            p_rating = prob.get("rating")
            p_name = prob.get("name", "")
            p_url = f"https://codeforces.com/contest/{prob.get('contestId')}/problem/{prob.get('index')}"

            if date_str not in daily_stats:
                daily_stats[date_str] = {"count": 0, "max_rating": 0, "ratings": [], "problems": []}

            daily_stats[date_str]["count"] += 1
            daily_stats[date_str]["problems"].append({
                "rating": p_rating, "url": p_url, "name": p_name
            })

            if p_rating:
                daily_stats[date_str]["ratings"].append(p_rating)
                if p_rating > daily_stats[date_str]["max_rating"]:
                    daily_stats[date_str]["max_rating"] = p_rating

            if p_rating is None:
                rating_dist["Unrated"] += 1
            elif p_rating < 1200:
                rating_dist["<1200"] += 1
            elif p_rating < 1400:
                rating_dist["1200-1399"] += 1
            elif p_rating < 1600:
                rating_dist["1400-1599"] += 1
            elif p_rating < 1900:
                rating_dist["1600-1899"] += 1
            elif p_rating < 2100:
                rating_dist["1900-2099"] += 1
            else:
                rating_dist[">=2100"] += 1

        for d in daily_stats.values():
            d["problems"].sort(key=lambda x: (x["rating"] is None, x["rating"] or 0))

        return len(ac_problems), daily_stats, rating_dist, recent_submissions
    except Exception as e:
        print(f"Codeforces fetch failed: {e}")
        return 0, {}, {}, []


# 3. 抓取牛客网 AC 数（大概率拿不到，做兜底）
def get_nowcoder_ac(nowcoder_id):
    url = f"https://ac.nowcoder.com/acm/contest/profile/{nowcoder_id}"
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            match = re.search(r'(?:练习通过|通过题目数).*?(\d+)', res.text)
            if match:
                return int(match.group(1))
    except Exception as e:
        print(f"Nowcoder fetch failed: {e}")
    return 0


# 4. AtCoder 数据（通过 AtCoder Problems API）
def get_atcoder_data(handle):
    base = "https://kenkoooo.com/atcoder/atcoder-api/v3/user/submissions"
    now = int(time.time())
    from_time = now - 365 * 24 * 3600

    all_subs = []
    cursor = from_time
    while True:
        url = f"{base}?user={handle}&from_second={cursor}"
        try:
            res = requests.get(url, timeout=15).json()
        except Exception as e:
            print(f"AtCoder Problems API failed: {e}")
            break
        if not res:
            break
        all_subs.extend(res)
        cursor = res[-1]["epoch_second"] + 1
        if len(res) < 500:
            break
        time.sleep(1)

    if not all_subs:
        return {"ac": 0, "daily_stats": {}, "rating_dist": {}}

    # 拉取题目难度映射
    difficulty_map = {}
    try:
        models = requests.get(
            "https://kenkoooo.com/atcoder/resources/problem-models.json",
            timeout=20
        ).json()
        for pid, model in models.items():
            if model.get("difficulty") is not None:
                difficulty_map[pid] = model["difficulty"]
    except Exception as e:
        print(f"AtCoder difficulty fetch failed: {e}")

    # 拉取题目元数据（ID → 名称）—— 解决"看不到题目名称"的关键
    problem_name_map = {}
    try:
        problems = requests.get(
            "https://kenkoooo.com/atcoder/resources/problems.json",
            timeout=20
        ).json()
        for p in problems:
            pid = p.get("id")
            if pid:
                problem_name_map[pid] = p.get("name") or p.get("title") or pid
    except Exception as e:
        print(f"AtCoder problems metadata fetch failed: {e}")

    ac_problems = set()
    daily_stats = {}
    rating_dist = {
        "<400": 0, "400-799": 0, "800-1199": 0,
        "1200-1599": 0, "1600-1999": 0, ">=2000": 0, "Unrated": 0
    }

    for sub in all_subs:
        if sub.get("result") != "AC":
            continue
        p_id = sub.get("problem_id")
        if p_id in ac_problems:
            continue
        ac_problems.add(p_id)

        ts = sub.get("epoch_second", 0)
        date_str = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
        p_diff = difficulty_map.get(p_id)
        p_name = problem_name_map.get(p_id, p_id)

        if date_str not in daily_stats:
            daily_stats[date_str] = {"count": 0, "problems": []}
        daily_stats[date_str]["count"] += 1
        daily_stats[date_str]["problems"].append({
            "rating": p_diff,
            "url": f"https://atcoder.jp/contests/{sub.get('contest_id')}/tasks/{p_id}",
            "name": p_name
        })

        if p_diff is None:
            rating_dist["Unrated"] += 1
        elif p_diff < 400:
            rating_dist["<400"] += 1
        elif p_diff < 800:
            rating_dist["400-799"] += 1
        elif p_diff < 1200:
            rating_dist["800-1199"] += 1
        elif p_diff < 1600:
            rating_dist["1200-1599"] += 1
        elif p_diff < 2000:
            rating_dist["1600-1999"] += 1
        else:
            rating_dist[">=2000"] += 1

    for d in daily_stats.values():
        d["problems"].sort(key=lambda x: (x["rating"] is None, x["rating"] or 0))

    return {
        "ac": len(ac_problems),
        "daily_stats": daily_stats,
        "rating_dist": rating_dist
    }


# 5. 未来赛事雷达（Contest Hive API）
def get_upcoming_contests():
    results = []

    try:
        cf = requests.get("https://contest-hive.vercel.app/api/codeforces", timeout=10).json()
        for c in cf.get("data", []):
            results.append({
                "platform": "Codeforces",
                "name": c.get("name", ""),
                "url": c.get("url", ""),
                "start": c.get("startTime", ""),
                "duration": c.get("duration", 0),
                "color": "#00d4ff"
            })
    except Exception as e:
        print(f"Contest Hive Codeforces failed: {e}")

    try:
        ac = requests.get("https://contest-hive.vercel.app/api/atcoder", timeout=10).json()
        for c in ac.get("data", []):
            results.append({
                "platform": "AtCoder",
                "name": c.get("name", ""),
                "url": c.get("url", ""),
                "start": c.get("startTime", ""),
                "duration": c.get("duration", 0),
                "color": "#a882ff"
            })
    except Exception as e:
        print(f"Contest Hive AtCoder failed: {e}")

    results.sort(key=lambda x: x.get("start", ""))
    return results


if __name__ == "__main__":
    CF_HANDLE = "Rowe"
    LUOGU_UID = "1965170"
    NOWCODER_ID = "344403471"
    ATCODER_HANDLE = "Rowe"

    LUOGU_AC = 377
    NOWCODER_AC = 0

    cf_info = get_cf_user_info(CF_HANDLE)
    cf_ac, daily_stats, rating_dist, recent_submissions = get_cf_data(CF_HANDLE)
    nowcoder_ac = get_nowcoder_ac(NOWCODER_ID) or NOWCODER_AC
    atcoder_data = get_atcoder_data(ATCODER_HANDLE)
    upcoming_contests = get_upcoming_contests()

    total_ac = cf_ac + LUOGU_AC + nowcoder_ac + atcoder_data["ac"]

    payload = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "total_ac": total_ac,
        "cf_info": cf_info,
        "profiles": {
            "Codeforces": f"https://codeforces.com/profile/{CF_HANDLE}",
            "Luogu": f"https://www.luogu.com.cn/user/{LUOGU_UID}",
            "Nowcoder": f"https://ac.nowcoder.com/acm/contest/profile/{NOWCODER_ID}",
            "AtCoder": f"https://atcoder.jp/users/{ATCODER_HANDLE}"
        },
        "platforms": {
            "Codeforces": cf_ac,
            "Luogu": LUOGU_AC,
            "Nowcoder": nowcoder_ac,
            "AtCoder": atcoder_data["ac"]
        },
        "manual": {
            "Luogu": True,
            "Nowcoder": nowcoder_ac == NOWCODER_AC
        },
        "daily_stats": daily_stats,
        "rating_dist": rating_dist,
        "recent_submissions": recent_submissions,
        "atcoder_daily_stats": atcoder_data["daily_stats"],
        "atcoder_rating_dist": atcoder_data["rating_dist"],
        "upcoming_contests": upcoming_contests
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print("data.json updated successfully.")

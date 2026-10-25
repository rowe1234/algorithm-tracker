import requests
import json
import re
from datetime import datetime, timezone


def get_cf_user_info(handle):
    # 完全不变
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

        # 新增：收集最近 10 条提交（无论 verdict），用于"正在刷"推断
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
                daily_stats[date_str] = {
                    "count": 0, "max_rating": 0, "ratings": [], "problems": []
                }

            daily_stats[date_str]["count"] += 1
            daily_stats[date_str]["problems"].append({
                "rating": p_rating,
                "url": p_url,
                "name": p_name
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
        return 0, {}, {}, {}


def get_nowcoder_ac(nowcoder_id):
    # 完全不变
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


if __name__ == "__main__":
    CF_HANDLE = "Rowe"
    LUOGU_UID = "1965170"
    NOWCODER_ID = "344403471"

    LUOGU_AC = 377
    NOWCODER_AC = 0

    cf_info = get_cf_user_info(CF_HANDLE)
    cf_ac, daily_stats, rating_dist, recent_submissions = get_cf_data(CF_HANDLE)
    nowcoder_ac = get_nowcoder_ac(NOWCODER_ID) or NOWCODER_AC

    total_ac = cf_ac + LUOGU_AC + nowcoder_ac

    payload = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "total_ac": total_ac,
        "cf_info": cf_info,
        "profiles": {
            "Codeforces": f"https://codeforces.com/profile/{CF_HANDLE}",
            "Luogu": f"https://www.luogu.com.cn/user/{LUOGU_UID}",
            "Nowcoder": f"https://ac.nowcoder.com/acm/contest/profile/{NOWCODER_ID}"
        },
        "platforms": {
            "Codeforces": cf_ac,
            "Luogu": LUOGU_AC,
            "Nowcoder": nowcoder_ac
        },
        "manual": {
            "Luogu": True,
            "Nowcoder": nowcoder_ac == NOWCODER_AC
        },
        "daily_stats": daily_stats,
        "rating_dist": rating_dist,
        "recent_submissions": recent_submissions,   # 新增
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print("data.json updated successfully.")

import requests
import json
from datetime import datetime

# 1. 抓取 CF 用户信息 (Rating, Rank, 头像)
def get_cf_user_info(handle):
    url = f"https://codeforces.com/api/user.info?handles={handle}"
    try:
        res = requests.get(url, timeout=10).json()
        if res.get("status") == "OK" and len(res.get("result", [])) > 0:
            user = res["result"][0]
            return {
                "rating": user.get("rating", "Unrated"),
                "maxRating": user.get("maxRating", "Unrated"),
                "rank": user.get("rank", "unrated"),
                "avatar": user.get("titlePhoto", "")
            }
    except Exception as e:
        print(f"CF user info fetch failed: {e}")
    return {"rating": "N/A", "maxRating": "N/A", "rank": "unrated", "avatar": ""}

# 2. 抓取 CF AC 列表与时间戳
def get_cf_data(handle):
    url = f"https://codeforces.com/api/user.status?handle={handle}"
    try:
        res = requests.get(url, timeout=10).json()
        if res.get("status") != "OK":
            return 0, []
        
        ac_problems = set()
        timestamps = []
        for sub in res["result"]:
            if sub.get("verdict") == "OK":
                problem_id = f"{sub['problem'].get('contestId')}{sub['problem'].get('index')}"
                ac_problems.add(problem_id)
                timestamps.append(sub["creationTimeSeconds"])
        return len(ac_problems), timestamps
    except Exception as e:
        print(f"Codeforces fetch failed: {e}")
        return 0, []

if __name__ == "__main__":
    CF_HANDLE = "Rowe"
    LUOGU_UID = "1965170"
    
    # 手动填入洛谷数（如需）
    LUOGU_AC = 0

    cf_info = get_cf_user_info(CF_HANDLE)
    cf_ac, cf_times = get_cf_data(CF_HANDLE)
    total_ac = cf_ac + LUOGU_AC

    payload = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "total_ac": total_ac,
        "cf_info": cf_info,
        "profiles": {
            "Codeforces": f"https://codeforces.com/profile/{CF_HANDLE}",
            "Luogu": f"https://www.luogu.com.cn/user/{LUOGU_UID}"
        },
        "platforms": {
            "Codeforces": cf_ac,
            "Luogu": LUOGU_AC
        },
        "timestamps": cf_times
    }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print("data.json updated successfully.")

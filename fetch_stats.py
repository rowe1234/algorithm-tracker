import requests
import json
from datetime import datetime

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
    CF_HANDLE = "Rowe"          # 你的 Codeforces 账号
    LUOGU_UID = "1965170"       # 你的洛谷 UID
    
    # 洛谷由于防爬虫无法直接跨域 API 提取，请在这里填入你当前在洛谷的 AC 题目数
    LUOGU_AC = 337  # 填入你现在的洛谷通过数

    cf_ac, cf_times = get_cf_data(CF_HANDLE)
    total_ac = cf_ac + LUOGU_AC

    payload = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "total_ac": total_ac,
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
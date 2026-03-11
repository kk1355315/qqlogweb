import json
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

DATA_FILE = Path("final_data.json")
EMOTION = "争执与分歧"
OUT_PNG = Path("dispute_distribution.png")

# Menstrual-cycle assumptions (adjust if needed).
CYCLE_MIN_DAYS = 25
CYCLE_MAX_DAYS = 31
PERIOD_DAYS = 7
PRE_DAYS = 3
POST_DAYS = 3
FIXED_START_DATE = None  # "YYYY-MM-DD", or None to allow offset optimization.

# Prefer common CJK fonts on Windows; fallback to DejaVu if unavailable.
plt.rcParams["font.sans-serif"] = [
    "Microsoft YaHei",
    "SimHei",
    "Arial Unicode MS",
    "DejaVu Sans",
]
plt.rcParams["axes.unicode_minus"] = False


def load_particles(path: Path):
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    return data.get("particles", [])


def build_daily_counts(particles):
    day_counter = Counter()
    for item in particles:
        if item.get("emotion_tag") != EMOTION:
            continue
        ts = item.get("timestamp")
        if not ts:
            continue
        day = datetime.fromtimestamp(ts).date()
        day_counter[day] += 1

    if not day_counter:
        return [], []

    start = min(day_counter)
    end = max(day_counter)
    days = []
    counts = []
    cursor = start
    while cursor <= end:
        days.append(cursor)
        counts.append(day_counter.get(cursor, 0))
        cursor += timedelta(days=1)
    return days, counts


def build_indicator(days, cycle_len, start_date, period_days, pre_days, post_days):
    active = set()
    for d in range(-pre_days, period_days + post_days):
        active.add(d % cycle_len)
    indicator = []
    for day in days:
        phase = (day - start_date).days % cycle_len
        indicator.append(1 if phase in active else 0)
    return indicator


def phase_profile(days, counts, cycle_len, start_date):
    sums = [0.0] * cycle_len
    nums = [0] * cycle_len
    for day, value in zip(days, counts):
        phase = (day - start_date).days % cycle_len
        sums[phase] += value
        nums[phase] += 1
    avgs = [(sums[i] / nums[i]) if nums[i] else 0.0 for i in range(cycle_len)]
    return avgs


def parse_start_date(value, fallback):
    if not value:
        return fallback
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return fallback


def optimize_cycle(days, counts):
    if not days:
        return None, []
    total = sum(counts)
    results = []
    for cycle_len in range(CYCLE_MIN_DAYS, CYCLE_MAX_DAYS + 1):
        if FIXED_START_DATE:
            start_date = parse_start_date(FIXED_START_DATE, days[0])
            indicator = build_indicator(
                days, cycle_len, start_date, PERIOD_DAYS, PRE_DAYS, POST_DAYS
            )
            red_sum = sum(c for c, flag in zip(counts, indicator) if flag)
            ratio = red_sum / total if total else 0.0
            offset = (days[0] - start_date).days % cycle_len
            results.append(
                {
                    "cycle_len": cycle_len,
                    "offset": offset,
                    "start_date": start_date,
                    "red_sum": red_sum,
                    "ratio": ratio,
                }
            )
        else:
            for offset in range(cycle_len):
                start_date = days[0] - timedelta(days=offset)
                indicator = build_indicator(
                    days, cycle_len, start_date, PERIOD_DAYS, PRE_DAYS, POST_DAYS
                )
                red_sum = sum(c for c, flag in zip(counts, indicator) if flag)
                ratio = red_sum / total if total else 0.0
                results.append(
                    {
                        "cycle_len": cycle_len,
                        "offset": offset,
                        "start_date": start_date,
                        "red_sum": red_sum,
                        "ratio": ratio,
                    }
                )
    results.sort(key=lambda x: (x["red_sum"], x["ratio"]), reverse=True)
    best = results[0] if results else None
    return best, results


def summarize(days, counts, best, results):
    total = sum(counts)
    if not days:
        print(f"未找到情感标签: {EMOTION}")
        return

    print(f"情感标签: {EMOTION}")
    print(f"总次数: {total}")
    print(f"时间范围: {days[0]} 到 {days[-1]} (共 {len(days)} 天)")

    top_days = sorted(zip(days, counts), key=lambda x: x[1], reverse=True)[:5]
    print("峰值日期(前5):")
    for day, count in top_days:
        print(f"  {day}: {count}")

    print(
        f"周期假设范围: {CYCLE_MIN_DAYS}-{CYCLE_MAX_DAYS} 天, 经期窗口 {PERIOD_DAYS} 天"
        f" + 前 {PRE_DAYS} 天 + 后 {POST_DAYS} 天"
    )
    if FIXED_START_DATE:
        print(f"固定周期起点: {FIXED_START_DATE}")
    if best:
        print(
            "目标: 红色区间内总次数最大"
        )
        print(
            f"全局最优: 周期 {best['cycle_len']} 天, 偏移 {best['offset']} 天, 起点 {best['start_date']}"
        )
        print(f"红区总次数: {best['red_sum']} / {total} ({best['ratio']:.2%})")
        print("候选(Top 5):")
        for item in results[:5]:
            print(
                f"  {item['cycle_len']} 天, 偏移 {item['offset']} 天, 红区 {item['red_sum']} ({item['ratio']:.2%})"
            )
    print("图例说明: 红色为经期窗口(含前后缓冲), 白色为非窗口")


def contiguous_segments(days, indicator):
    segments = []
    start = None
    for i, flag in enumerate(indicator):
        if flag and start is None:
            start = i
        elif not flag and start is not None:
            segments.append((days[start], days[i - 1]))
            start = None
    if start is not None:
        segments.append((days[start], days[-1]))
    return segments


def plot(days, counts, best):
    if not days:
        return
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 7), constrained_layout=True)

    if not best:
        return

    indicator = build_indicator(
        days,
        best["cycle_len"],
        best["start_date"],
        PERIOD_DAYS,
        PRE_DAYS,
        POST_DAYS,
    )
    for start_day, end_day in contiguous_segments(days, indicator):
        ax1.axvspan(
            start_day,
            end_day + timedelta(days=1),
            color="#ff9896",
            alpha=0.18,
            lw=0,
        )

    ax1.plot(days, counts, color="#1f77b4", linewidth=1, label="每日次数")
    ax1.set_title(
        f"争执与分歧：时间分布 (周期 {best['cycle_len']} 天)"
    )
    ax1.set_ylabel("次数")
    ax1.grid(alpha=0.2)
    ax1.legend(loc="upper left")

    locator = mdates.AutoDateLocator(minticks=6, maxticks=10)
    ax1.xaxis.set_major_locator(locator)
    ax1.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))

    profile = phase_profile(days, counts, best["cycle_len"], best["start_date"])
    phases = list(range(best["cycle_len"]))
    ax2.plot(phases, profile, color="#9467bd", linewidth=1.8)
    ax2.set_title(f"周期相位平均争吵强度 (周期 {best['cycle_len']} 天)")
    ax2.set_xlabel("相位 (天)")
    ax2.set_ylabel("平均次数")
    ax2.grid(alpha=0.2)
    active_len = PERIOD_DAYS + PRE_DAYS + POST_DAYS
    ax2.axvspan(
        0,
        active_len - 1,
        color="#ff9896",
        alpha=0.18,
        lw=0,
    )
    if PRE_DAYS:
        ax2.axvspan(
            best["cycle_len"] - PRE_DAYS,
            best["cycle_len"] - 1,
            color="#ff9896",
            alpha=0.18,
            lw=0,
        )

    fig.savefig(OUT_PNG, dpi=160)
    print(f"图已保存: {OUT_PNG}")


def main():
    particles = load_particles(DATA_FILE)
    days, counts = build_daily_counts(particles)
    best, results = optimize_cycle(days, counts)
    summarize(days, counts, best, results)
    plot(days, counts, best)


if __name__ == "__main__":
    main()

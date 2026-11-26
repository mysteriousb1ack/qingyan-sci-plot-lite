#!/usr/bin/env python3
"""
QingYan SciPlot Lite (开源体验版)
功能：读取分组 CSV 数据，执行 Shapiro-Wilk 正态性与 Levene 方差齐性预检，
自动选用参数/非参数检验，并输出 300 DPI 分组箱线散点图与统计摘要。
完整 12 类 SCI 科研图型（含生存曲线/ROC/火山图/热图/PCA/森林图/多面板拼图与中英文 Methods 生成）
见作者爱发电主页：https://ifdian.net/a/qingyandata
"""

import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = [
    "PingFang SC",
    "Hiragino Sans GB",
    "Microsoft YaHei",
    "SimHei",
    "Noto Sans CJK SC",
    "DejaVu Sans",
]
plt.rcParams["axes.unicode_minus"] = False


def run_stats(df: pd.DataFrame, group_col: str, value_col: str):
    groups = [g for g, _ in df.groupby(group_col, sort=False)]
    arrays = [df.loc[df[group_col] == g, value_col].dropna().to_numpy(dtype=float) for g in groups]
    normal_ok = all(len(a) >= 3 and stats.shapiro(a).pvalue >= 0.05 for a in arrays)
    var_ok = stats.levene(*arrays).pvalue >= 0.05 if len(arrays) >= 2 else True

    if len(arrays) == 2:
        if normal_ok and var_ok:
            stat, p = stats.ttest_ind(arrays[0], arrays[1], equal_var=True)
            method = "Independent-samples t-test"
        elif normal_ok:
            stat, p = stats.ttest_ind(arrays[0], arrays[1], equal_var=False)
            method = "Welch's t-test"
        else:
            stat, p = stats.mannwhitneyu(arrays[0], arrays[1], alternative="two-sided")
            method = "Mann-Whitney U test"
    else:
        if normal_ok and var_ok:
            stat, p = stats.f_oneway(*arrays)
            method = "One-way ANOVA"
        else:
            stat, p = stats.kruskal(*arrays)
            method = "Kruskal-Wallis H test"
    return groups, arrays, method, float(stat), float(p), normal_ok, var_ok


def plot_comparison(df: pd.DataFrame, group_col: str, value_col: str, out_prefix: Path):
    groups, arrays, method, stat, p, normal_ok, var_ok = run_stats(df, group_col, value_col)
    rng = np.random.default_rng(42)
    palette = ["#2A9D8F", "#3A86FF", "#E76F51", "#8338EC", "#E9C46A"]

    fig, ax = plt.subplots(figsize=(5.4, 4.2), dpi=300)
    bp = ax.boxplot(
        arrays,
        positions=np.arange(len(groups)),
        widths=0.45,
        patch_artist=True,
        showfliers=False,
        medianprops={"color": "#1D2433", "linewidth": 1.6},
        whiskerprops={"color": "#4A5568", "linewidth": 1.2},
        capprops={"color": "#4A5568", "linewidth": 1.2},
    )
    for i, patch in enumerate(bp["boxes"]):
        patch.set_facecolor(palette[i % len(palette)])
        patch.set_alpha(0.32)
        patch.set_edgecolor(palette[i % len(palette)])
        patch.set_linewidth(1.4)

    for i, arr in enumerate(arrays):
        jitter = rng.normal(0, 0.06, size=len(arr))
        ax.scatter(
            np.full_like(arr, i, dtype=float) + jitter,
            arr,
            s=22,
            color=palette[i % len(palette)],
            edgecolor="white",
            linewidth=0.5,
            alpha=0.88,
            zorder=3,
        )

    ax.set_xticks(np.arange(len(groups)))
    ax.set_xticklabels(groups, fontsize=10)
    ax.set_ylabel(value_col, fontsize=10.5)
    ax.set_title(f"{method}: stat={stat:.3f}, p={p:.3e}", fontsize=10.5, pad=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.25)
    fig.tight_layout()

    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(f"{out_prefix}.png", dpi=300)
    fig.savefig(f"{out_prefix}.svg")
    plt.close(fig)
    print(f"[OK] method={method} | normal={normal_ok} | equal_var={var_ok} | stat={stat:.4f} | p={p:.6g}")
    print(f"[OK] saved: {out_prefix}.png & {out_prefix}.svg")


def main():
    ap = argparse.ArgumentParser(description="QingYan SciPlot Lite - 分组统计检验与300DPI箱线散点图")
    ap.add_argument("--input", default="demo_data/comparison.csv", help="输入 CSV 路径")
    ap.add_argument("--group-col", default="group", help="分组列名")
    ap.add_argument("--value-col", default="value", help="数值列名")
    ap.add_argument("--out", default="output/comparison_lite", help="输出文件前缀（不含扩展名）")
    args = ap.parse_args()

    df = pd.read_csv(args.input)
    gcol = args.group_col if args.group_col in df.columns else df.columns[0]
    vcol = args.value_col if args.value_col in df.columns else df.columns[1]
    plot_comparison(df, gcol, vcol, Path(args.out))


if __name__ == "__main__":
    main()

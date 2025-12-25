import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# === 🟢 1. Plot epsilon decay ===
def plot_epsilon_decay(epsilon_series: pd.DataFrame, title: str = "Exploration Rate Over Time"):
    """
    Plot epsilon (exploration) trend over time.
    """
    if epsilon_series.empty or "t" not in epsilon_series or "epsilon_mean" not in epsilon_series:
        raise ValueError("epsilon_series must contain 't' and 'epsilon_mean' columns")

    plt.figure(figsize=(10, 5))
    plt.plot(epsilon_series["t"], epsilon_series["epsilon_mean"], color="orange", linewidth=2)
    plt.title(title)
    plt.xlabel("Time")
    plt.ylabel("Epsilon (Exploration Rate)")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.show()


# === 🟦 2. Plot reward trend ===
def plot_reward_trend(reward_series: pd.DataFrame, title: str = "Average Reward Over Time"):
    """
    Plot mean reward trend over time.
    """
    if reward_series.empty or "t" not in reward_series or "reward_mean" not in reward_series:
        raise ValueError("reward_series must contain 't' and 'reward_mean' columns")

    plt.figure(figsize=(10, 5))
    plt.plot(reward_series["t"], reward_series["reward_mean"], color="steelblue", linewidth=2)
    plt.title(title)
    plt.xlabel("Time")
    plt.ylabel("Mean Reward")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.show()


# === 🟣 3. Plot policy selection frequency ===
def plot_policy_selection(policy_series: pd.DataFrame, title: str = "Policy Selection Frequency Over Time"):
    """
    Plot how often each policy was selected in each time bucket.
    """
    if policy_series.empty or "t" not in policy_series or "counts" not in policy_series:
        raise ValueError("policy_series must contain 't' and 'counts' columns")

    expanded = []
    for _, row in policy_series.iterrows():
        for pid, count in (row.get("counts") or {}).items():
            expanded.append({"t": row["t"], "policy_id": int(pid), "count": count})
    df = pd.DataFrame(expanded)

    plt.figure(figsize=(10, 5))
    for pid, group in df.groupby("policy_id"):
        plt.plot(group["t"], group["count"], label=f"Policy {pid}", linewidth=2)
    plt.title(title)
    plt.xlabel("Time")
    plt.ylabel("Selections")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.show()


# === 🟠 4. Plot per-policy performance ===
def plot_policy_performance(policy_reward_series: dict[int, pd.DataFrame], title: str = "Policy Reward Performance Over Time"):
    """
    Plot average reward per policy over time, skipping empty or invalid DataFrames.
    Supports both 'reward_mean' and 'mean_reward' column names.
    """
    if not policy_reward_series:
        raise ValueError("policy_reward_series is empty")

    plt.figure(figsize=(10, 5))
    has_lines = False

    for pid, df in policy_reward_series.items():
        if df.empty or "t" not in df:
            continue

        # Handle both possible column names
        y_col = "reward_mean" if "reward_mean" in df.columns else "mean_reward" if "mean_reward" in df.columns else None
        if not y_col:
            continue

        # Convert timestamps safely
        try:
            t_vals = pd.to_datetime(df["t"])
        except Exception:
            t_vals = df["t"]

        plt.plot(t_vals, df[y_col], label=f"Policy {pid}", linewidth=2)
        has_lines = True

    plt.title(title)
    plt.xlabel("Time")
    plt.ylabel("Mean Reward")
    if has_lines:
        plt.legend()
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.show()
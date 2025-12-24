# Decision: ノイズモデル（Gaussian / Rician）の扱い

Date: 2025-12-18  
Status: accepted

## Context

qMRI の magnitude 信号は Rician ノイズが自然に現れる一方、簡便な検証では Gaussian 近似が使われる。qMRLab でもシミュレーションで Rician を使うケースがある。

## Decision

- `qmrpy` の実験用スクリプト（`scripts/run_experiment.py`）では、ノイズモデルを **configで選べる**ようにする。
  - `noise_model = "gaussian"`（デフォルト）
  - `noise_model = "rician"`
- 実装定義（Rician）：
  - `y = sqrt((s + n1)^2 + n2^2)`, `n1,n2 ~ N(0, sigma)`

## Rationale

- baseline を Gaussian で軽く回しつつ、Rician でより現実的な挙動も確認できる。
- どちらを使ったかは `metrics` と `run.json` に残るため、再現性が高い。


# Decision: `vfa_t1` のB1補正とrobust線形fit

Date: 2025-12-18  
Status: accepted

## Context

qMRLab の `vfa_t1` は B1map による flip angle 補正（`FA_actual = B1 * FA_nominal`）を前提にし、また実データでは外れ値（ノイズ/アーチファクト）により線形化fitが不安定になり得る。

## Decision

- `qmrpy.models.t1.VfaT1` は `b1` を **スカラーまたは flip_angle と同形の1D配列**として受け取り、flip angle に乗算して扱う。
- `VfaT1.fit_linear(...)` は `robust=True` で **Huber loss のIRLS**により外れ値耐性を持つ線形fitを行えるようにする（デフォルトは非robust）。
- `VfaT1.fit_linear(...)` は `outlier_reject=True` で **外れ値を除外して再fit**できるようにする（小標本向けに subset 探索 + 物理制約 `0 < slope < 1` を用いる）。
- 実験スクリプト側（`scripts/run_experiment.py`）では、合成データ生成時に
  - `b1_range = [min, max]` を指定した場合、サンプル（ボクセル）ごとに B1 を一様分布からサンプルできる。
  - `robust_linear` / `huber_k` / `outlier_reject` を config で指定できる。

## Rationale

- B1補正を入れないと upstream と同条件の比較ができない。
- robust fit は「外れ値が混ざったときに破綻しない」方向の改善で、失敗解析の基礎になる。

## Consequences

- `run.json` / `metrics` に `robust_linear` や `b1_range` を記録し、再現性を担保する。
- 将来的に qMRLab の `Compute_M0_T1_OnSPGR` 相当のより詳細な処理（マスク、外れ値判定等）は段階的に揃える。

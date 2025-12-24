# 意思決定ログ: DecaesT2Map の EPG backend デフォルト

- Date: 2025-12-18
- Status: accepted

## 背景

`src/qmrpy/models/t2/decaes_t2.py`（DECAES.jl `T2mapSEcorr` の翻訳）では、EPG による MSE echo decay curve が basis 構築の中核になる。

直近の変更で `epgpy` を vendor し、`epg_decay_curve(backend="epgpy"|"decaes")` と `DecaesT2Map(epg_backend=...)` で backend を切り替え可能にした。

ここで「デフォルトをどちらにするか」を、実測（スイープ比較）に基づき決める。

## 実施（比較 run）

`scripts/run_epg_backend_sweep.py` により、`epgpy` と `decaes` の decay curve を同一パラメータ格子で比較した。

- run_id: `2025-12-18_195032_epg-backend-sweep`
  - config: `configs/exp/epg_backend_sweep.toml`（β=180）
- run_id: `2025-12-18_195126_epg-backend-sweep-beta150`
  - config: `configs/exp/epg_backend_sweep_beta150.toml`（β=150）
- run_id: `2025-12-18_195500_epg-backend-sweep-wide`
  - config: `configs/exp/epg_backend_sweep_wide.toml`（ETL/TE/β を複数条件に拡張）

どちらも `output/runs/<run_id>/figures/` に A/B/C（grid / nmse_hist / topk_curves）を出力した。

## 観察（要点）

- 上記 2 run とも、`epgpy` と `decaes` の差は **数値丸め誤差レベル**だった。
  - NMSE の最大が `~1e-30`、max_abs_diff の最大が `~1e-15`（double 精度の誤差域）。
- 追加 run（wide）でも同様で、`n_points=2268` の格子でも差分は丸め誤差レベルだった。
  - NMSE_max ≈ `8.0e-30`、max_abs_diff_max ≈ `2.7e-15`

## 決定

- `DecaesT2Map.epg_backend` のデフォルトは **`"decaes"`** とする（DECAES.jl 参照実装との数値パリティを優先）。
- `epg_decay_curve(backend="epgpy")` は引き続き利用可能とし、将来的なシーケンス拡張の入口として残す。

## 理由

- decay curve 単体では差分が丸め誤差レベルでも、`T2mapSEcorr` の flip angle 最適化（surrogate/NNLS）まで含めると、最終的に選ばれる `alpha_deg` が DECAES.jl の参照値と一致しないケースがあった（`pytest` の parity テストで検出）。
- このモデルは「DECAES.jl の翻訳」を主目的としているため、デフォルトは DECAES-style backend を優先し、`epgpy` はオプションとして扱うのが安全。

## 次（保留）

- さらなる差分検知のため、必要に応じて（ETL/TE/β/位相設定など）スイープ条件を拡張する。

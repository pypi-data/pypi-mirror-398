# 意思決定ログ: MWF v0（NNLS + カットオフ統合）

日付: 2025-12-18  
ステータス: 採用

## 背景 / 目的

qMRLab の `mwf`（Multi-Exponential T2 からの Myelin Water Fraction 推定）を Python に段階的に翻訳する。
まずは「実験を回せる最小実装」として、T2 スペクトルを NNLS で推定し、カットオフ範囲の積分から MWF/T2MW/T2IEW を算出する v0 を採用する。

## 決定

- T2 スペクトル推定は **NNLS（non-negative least squares）** を採用する（`scipy.optimize.nnls`）。
- MWF/T2MW/T2IEW の算出は、推定スペクトルを **T2 のカットオフ範囲で積分/要約**して求める。
- カットオフの既定値は qMRLab の意図に寄せる：
  - `lower_cutoff_mw_ms`: 既定 `None`（= `1.5 * FirstEcho`）
  - `cutoff_ms`: 既定 `40.0`（MW/IEW 境界）
  - `upper_cutoff_iew_ms`: 既定 `200.0`（IEW 上限）
- 指標定義（v0）：
  - `MWF = sum(weights[T2 <= cutoff]) / sum(weights[all])`（qMRLab の定義に合わせる）
  - `T2MW`, `T2IEW` は、各範囲内の **重み付き平均 T2**（既定は算術平均）。
    - オプションで重み付き幾何平均（`use_weighted_geometric_mean=true`）も選べる。

## 実装範囲（v0でやらないこと）

qMRLab の `mwf.m` は `multi_comp_fit_v2` を用い、ガンマ分布を用いたスペクトルモデルやノイズ（Sigma）等のオプションを含む。
v0 では以下は未対応とする：

- `multi_comp_fit_v2` 相当の完全再実装（スペクトルの事前分布、ガンマ分布パラメータ推定、tissue mask 対応など）
- Rician bias correction 等の高度なノイズ補正
- 実データ I/O（NIfTI 等）と voxelwise fitting の高速化

## 影響範囲

- 追加/更新ファイル:
  - `src/qmrpy/models/t2/mwf.py`
  - `scripts/run_experiment.py`（`model="mwf"` のrunを拡張）
  - `configs/exp/mwf_baseline.toml`
  - `tests/test_mwf.py`

## 次のアクション（候補）

- qMRLab の `mwf` と同一条件（TE、cutoff、basis 等）での固定ベクトル比較を追加する。
- スペクトル（weights vs T2）の可視化（run の必須 A/B/C に加え、解析補助図として）を追加する。

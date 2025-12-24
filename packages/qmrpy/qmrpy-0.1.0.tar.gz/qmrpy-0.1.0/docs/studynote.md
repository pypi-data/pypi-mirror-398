# 研究進捗ノート

## 2025-12-18

- Last updated: 2025-12-18T10:36:12.346Z

### 概要

- リポジトリ運用（AGENTS / studyplan / decisions / release / CI）を整備し、Pythonパッケージとしての土台を確立。
- qMRLab由来モデルのコアを段階的に実装し、run形式での評価・比較と、Octave(qMRLab)との数値整合性検証まで到達。

### 運用・ドキュメント・リポジトリ整備

- `AGENTS.md` を追加し、研究運用と再現性・可視化の規約をリポジトリ内に固定した。
- `AGENTS.md` を更新し、`qmrpy` のPyPI公開前提の運用（`src/qmrpy`、`tests`、CI、決定ログ）へ再整理した。
- `docs/studyplan.md` を追加し、qMRLab Python翻訳の進め方（draft）を初期化した。
- `docs/studyplan.md` を更新し、seed/反復方針とChangelog更新ルールを追記した。
- `docs/studyplan.md` を更新し、PyPI公開を目的としたパッケージング/リリース計画（品質ゲート、マイルストン）を追記した。
- `docs/studynote.md` を追加し、研究進捗ログの記録を開始した。
- `.gitignore` と `README.md` を追加し、最低限のリポジトリ入口を整備した。
- `.gitignore` を更新し、`uv` のローカルキャッシュ（`.uv_cache/`）をGit管理外にした。
- `docs/manuscript/figures_manifest.yaml` を追加し、論文用図表の出自台帳の雛形を用意した。
- `docs/decisions/2025-12-18__qMRLab_reference_handling.md` を追加し、`qMRLab/` をローカル参照用（Git 管理外）とする判断を記録した。
- `docs/protocols/release.md` を追加し、リリース手順（暫定）を文書化した。
- `docs/decisions/2025-12-18__packaging_layout_and_versioning.md` を追加し、srcレイアウト・Python>=3.11・SemVer採用を記録した。
- `docs/decisions/2025-12-18__license_and_attribution.md` を追加し、MITライセンス採用と表記方針を検討事項として整理した。
- `LICENSE` を追加し、MIT License と著作権表記を確定した。

### パッケージ/CI

- `pyproject.toml` と `src/qmrpy/__init__.py` を追加し、`qmrpy` の最小パッケージ雛形（import可能）を用意した。
- `tests/test_import.py` を追加し、最低限の自動テスト（import）を用意した。
- `pyproject.toml` を更新し、`Repository` / `Issues` URL を設定した。
- `.github/workflows/ci.yml` を追加し、CIで `uv sync` と `pytest` を回す雛形を用意した。
- `notebooks/` を追加し、探索・可視化の置き場を用意した。
- `uv.lock` を生成し、`uv sync --locked` / `uv run --locked` の固定運用に移行した。

### 実装: モデル（qMRLab翻訳）

- `docs/decisions/2025-12-18__units_conventions.md` を追加し、モデルごとの単位（TE[ms]/TR[s]等）を固定した。

- `mono_t2`
  - `docs/decisions/2025-12-18__initial_model_mono_t2.md` を追加し、最初の実装対象を `mono_t2` に確定した。
  - `src/qmrpy/models/t2/mono_t2.py` を追加し、`mono_t2` の最小実装（forward + fit）を開始した。
  - `src/qmrpy/models/t2/mono_t2.py` を更新し、`fit_type` / `drop_first_echo` / `offset_term` を追加した。
  - `docs/decisions/2025-12-18__mono_t2_fit_options.md` を追加し、`mono_t2` オプション方針を記録した。

- `vfa_t1`
  - `src/qmrpy/models/t1/vfa_t1.py` を追加し、`vfa_t1` の最小実装（forward + 線形fit）を追加した。
  - `src/qmrpy/models/t1/vfa_t1.py` を更新し、B1補正（スカラー/配列）とrobust線形fit（Huber IRLS）を追加した。
  - `src/qmrpy/models/t1/vfa_t1.py` を更新し、`outlier_reject` による外れ値除外（subset探索+物理制約）を追加した。
  - `docs/decisions/2025-12-18__vfa_t1_b1_and_robust_fit.md` を追加し、`vfa_t1` のB1補正とrobust fit方針を記録した。

- **MWF (Myelin Water Fraction)**:
  - Verified against qMRLab `mwf` model.
  - Parity achieved by scaling qMRLab output by 1/100 (qMRLab outputs percentage 0-100, Python outputs fraction 0-1).
  - Python implementation matches qMRLab NNLS logic.

- **MP-PCA Denoising**:
  - Implemented `MPPCA` class in `src/qmrpy/models/noise/denoising_mppca.py`, manually translating `MPdenoising.m`.
  - Verified against qMRLab using `scripts/verify_mppca.py` and `scripts/octave/verify_mppca.m`.
  - **Center Pixel Parity**: Exact match for Sigma (49.9215) and Signal (1040.1650) at center pixel.
  - **Boundary Handling**: Discrepancies found at boundaries where qMRLab explicitly zeros out certain slices/edges differently from Python's windowing. ROI-based comparison (excluding boundaries) confirms numerical parity.
  - Integrated into `run_experiment.py` and verified with `configs/exp/test_mppca.toml`.

- `inversion_recovery` (Barral + magnitude polarity restoration)
  - `src/qmrpy/models/t1/inversion_recovery.py` を追加し、qMRLabの `inversion_recovery` を翻訳実装した。
  - `tests/test_inversion_recovery.py` を追加し、IRの forward/fit（complex/magnitude）を固定テスト化した。
  - `docs/decisions/2025-12-18__inversion_recovery_barral_and_polarity_restoration.md` を追加し、IRの方針（式・method・単位）を記録した。

- `b1_dam` (Double Angle Method)
  - `src/qmrpy/models/b1/dam.py` を追加し、qMRLabの `b1_dam` を翻訳実装した。
  - `tests/test_b1_dam.py` を追加し、B1 DAM のノイズ無し回帰テストを追加した。

- `mwf` (Multi-component T2; NNLS + cutoffs)
  - `src/qmrpy/models/t2/mwf.py` を実装し、MWFの解析（NNLS）を追加した。
  - `src/qmrpy/models/t2/mwf.py` を更新し、カットオフ（lower/cutoff/upper）に基づく `MWF/T2MW/T2IEW` の算出と `gmt2_ms` 出力を追加した。
  - `tests/test_mwf.py` を追加し、ノイズ無し合成データで `mwf` が妥当な範囲に収まる回帰テストを追加した。
  - `docs/decisions/2025-12-18__mwf_v0_nnls_cutoffs.md` を追加し、MWF v0 の定義（NNLS + カットオフ）と未対応範囲を記録した。

### 実装: ノイズ/テスト

- `src/qmrpy/sim/noise.py` を追加し、Gaussian/Rician ノイズ付加を共通化した。
- `docs/decisions/2025-12-18__noise_models.md` を追加し、ノイズモデル方針を記録した。
- `tests/test_fixed_vectors.py` を追加し、forwardの固定テストベクトルとRicianノイズの決定性テストを追加した。
- `tests/test_vfa_t1.py` を更新し、B1補正の回帰テストとrobust/outlier処理のテストを追加した。

### 実装: run形式の評価・比較

- `scripts/run_experiment.py` と `configs/exp/mono_t2_baseline.toml` を追加し、run形式（`run.json`/`metrics`/`figures`/`config_snapshot`）の雛形を用意した。
- `scripts/run_experiment.py` を更新し、`run.model` により複数モデルを切り替えられるようにした。
- `scripts/run_experiment.py` と `configs/exp/*.toml` を更新し、`noise_model = "gaussian"|"rician"` を指定できるようにした。
- `configs/exp/vfa_t1_baseline.toml`、`configs/exp/vfa_t1_rician.toml`、`configs/exp/vfa_t1_b1range_rician_outlier.toml` を追加し、vfa_t1の比較条件を用意した。
- `configs/exp/inversion_recovery_baseline.toml` と `configs/exp/ir_baseline.toml` を追加し、IRのベースライン実行環境を整備した。
- `configs/exp/b1_dam_baseline.toml` を追加し、B1 DAM のベースライン設定を用意した。
- `configs/exp/mwf_baseline.toml` を追加し、MWFのベースライン設定を用意した。
- `scripts/run_experiment.py` を更新し、`mwf` のrunで T2 スペクトル図（`spectrum__mean_weights.png`）を追加出力するようにした。

- `scripts/compare_runs.py` を追加/更新し、複数runの比較（集計CSV/比較図/残差分布/層別 |誤差| mean/median/p95）を `output/reports/` に出力できるようにした。
- `scripts/run_experiment.py` を更新し、`metrics/*_per_sample.csv`（真値/推定/残差/B1など）を出力して失敗解析に使えるようにした。

### 実行runまとめ

| run_id | model | noise | key metric |
|---|---|---|---|
| 2025-12-18_152315_mono-t2-baseline | mono_t2 | gaussian (sigma=5.0) | t2_rel_mae≈0.010 |
| 2025-12-18_152709_vfa-t1-baseline | vfa_t1 | gaussian (sigma=5.0) | t1_rel_mae≈0.065 |
| 2025-12-18_183811_ir-baseline | inversion_recovery | rician (sigma=5.0) | t1_rel_mae≈0.011 |
| 2025-12-18_184212_b1-dam-baseline | b1_dam | gaussian (sigma=10.0) | b1_rel_mae≈0.016 |
| 2025-12-18_184558_mwf-baseline | mwf | (see run config) | mwf_mae≈0.012 (MWF_ref=0.15) |
| 2025-12-18_191349_mwf-baseline | mwf | (see run config) | mwf_mae≈0.012 + spectrum図出力 |
| 2025-12-18_195129_mwf-baseline | mwf | (see run config) | MWF実装の整合後に再実行 |

### Octave (qMRLab) との数値比較検証（Numerical Parity Verification）

- MWFについて、qMRLab（Octave）側で生成→fitを行った固定ベクトルを、qmrpy側でも同一条件でfitして差分を保存するスクリプトを用意した。
- `scripts/octave/mwf_generate_and_fit.m` と `scripts/verify_qmrlab_mwf.py` を追加し、qMRLab（Octave）側で「生成→fit」を行った固定ベクトルを qmrpy で同一条件fitして差分を `report.json` に保存できるようにした。
  - 観察（Observation）：`output/reports/qmrlab_parity/2025-12-18_191500__mwf_fixed_vector/report.json` で `dMWF≈-0.105%`、`dT2MW≈-0.13ms`、`dT2IEW≈-0.04ms` を確認した。
  - 解釈（Interpretation）：MWF/T2MW/T2IEW の定義（percent/fraction、gm/mean）と basis/cutoff を揃えると、qMRLab（regNNLS）と qmrpy（NNLS+Tikhonov）でも実用上十分に近い結果が得られる。
  - 次（Next）：差分が大きくなる条件（ノイズ、cutoff、basis範囲、正則化）をスイープし、v1で寄せるべき仕様（MWF定義/正則化）を決める。

### 次のアクション（整理）

- DECAES.jl の T2mapSEcorr/T2partSEcorr（EPG + NNLS + T2-parts）をPythonへ翻訳し、qmrpyモデル（`DecaesT2Map`/`DecaesT2Part`）として統合する。固定flip+無正則化ケースについてはDECAES.jl生成の参照信号/分布に対するparityテスト（`tests/test_decaes_parity.py`）を追加済み。
- parity検証の継続（特にmono_t2のOctave側収束不良ケースの扱い方針を決める）。
- run/compareの評価指標・可視化を維持しつつ、次モデルの翻訳へ進む。
- `epgpy` を `src/epgpy/` にvendorし、`qmrpy` 実装から `import epgpy` 可能にした。
- `src/qmrpy/models/t2/decaes_t2.py` の `epg_decay_curve` に `backend` を追加し、デフォルトを `epgpy` backend に切り替えた（`decaes` backend も残した）。
- `src/qmrpy/models/t2/decaes_t2.py` の `DecaesT2Map` に `epg_backend` を追加し、basis生成で backend を選択できるようにした。
- `THIRD_PARTY_NOTICES.md` を追加し、`pyproject.toml` で wheel へ同梱するようにした。
- `tests/test_decaes_t2.py` を更新し、`epgpy`/`decaes` 両backendの簡単な回帰テストを追加した。
- `scripts/run_epg_backend_sweep.py` と `configs/exp/epg_backend_sweep*.toml` を追加し、`epgpy` vs `decaes` backend の差分スイープrunを実行した（`output/runs/2025-12-18_195032_epg-backend-sweep`、`output/runs/2025-12-18_195126_epg-backend-sweep-beta150`）。
- 観察：上記 run の `result__nmse_hist.png` と `failure__topk_curves.png` から、差分が丸め誤差レベル（NMSE≈1e-30、max_abs_diff≈1e-15）であることを確認した。
- 解釈：現状の MSE decay curve 実装においては、`epgpy` backend をデフォルトにしても DECAES-style 実装との parity を損なわないと判断した。
- 次：必要に応じてスイープ条件（ETL/TE/位相/βの範囲）を広げ、差が出る条件が存在するかを監視する。
- `scripts/run_epg_backend_sweep.py` を更新し、`etl` / `te_ms` / `beta_deg` をリスト指定できるようにしてスイープ範囲を拡張した。
- run: `output/runs/2025-12-18_195500_epg-backend-sweep-wide` を追加で実行し、ETL/TE/β を複数条件に拡張しても差分が丸め誤差レベルであることを確認した（NMSE_max≈8e-30、max_abs_diff_max≈3e-15）。
- **型付け方針として `.pyi` を廃止し、`.py` に型注釈を直接書く方針にした**（`docs/decisions/2025-12-18__typing_policy_no_pyi.md`）。
- `src/qmrpy/**/*.pyi` を削除し、`src/qmrpy/py.typed` は維持した。
- `src/qmrpy/models/t2/mono_t2.py` / `src/qmrpy/models/t2/mwf.py` / `src/qmrpy/models/t1/vfa_t1.py` / `src/qmrpy/models/t1/inversion_recovery.py` / `src/qmrpy/models/b1/dam.py` / `src/qmrpy/sim/noise.py` に最小限の型注釈（戻り値型など）を追加した。
- `src/qmrpy/models/t2/decaes_t2.py` / `src/qmrpy/models/t2/decaes_t2part.py` にも型注釈（戻り値型など）を追加した。
- `src/qmrpy/models/t2/decaes_t2.py` の `DecaesT2Map.epg_backend` は意思決定どおりデフォルトを `"epgpy"` とし、DECAES.jl parity テスト側では `epg_backend="decaes"` を明示する形に揃えた。
- `scripts/sweep_qmrlab_mwf.py` により、MWFの差分が大きくなる条件（ノイズ、basis上限、正則化）をスイープして、v1で寄せるべき仕様を決める。
  - 観察（Observation）：`output/reports/qmrlab_parity_sweeps/2025-12-18_192613__mwf_sweep/summary.csv` を生成し、条件ごとの `dMWF/dT2MW/dT2IEW` を一覧化できた。
  - 解釈（Interpretation）：qMRLabの信号スケール（S(TE=0)≈1）とノイズσの整合を取ることで、比較が破綻しにくくなる（σは 0.001〜0.01 程度が現実的）。
  - 次（Next）：`top10.json` 上位条件をベースに、`mwf` の正則化（Tikhonov vs regNNLS相当）と cutoffs の固定方針を意思決定ログに落とす。

## 2025-12-19
- `README.md` にパッケージ利用手順と最小利用例、第三者由来コードの扱いを追記した。
- `THIRD_PARTY_NOTICES.md` に qMRLab と DECAES.jl のライセンス表記を追加した。
- `docs/protocols/release.md` にリリース前のライセンス表記確認ステップを追加した。
- **第三者由来コードの表記方針を `docs/decisions/2025-12-19__third_party_attribution.md` に記録した。**
- `uv run --locked -m pytest` を実行し、全30件のテストが通ることを確認した。
- `uv build` を実行し、`dist/` に sdist と wheel を生成した。
- wheel 内に `THIRD_PARTY_NOTICES.md` が同梱されていることを確認した。
- `src/qmrpy/__init__.py` の `__version__` を `0.1.0` に更新した。
- `dist/qmrpy-0.0.0.tar.gz` / `dist/qmrpy-0.0.0-py3-none-any.whl` の中身を確認し、`THIRD_PARTY_NOTICES.md` / `qmrpy/py.typed` / `LICENSE` が含まれることを確認した。
- ただし `dist/` が `0.0.0` のままであることを確認した。

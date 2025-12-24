# Study Plan（qmrpy / qMRLab Python翻訳）

Status: active  
Version: v0.1.0  
Last updated: 2025-12-18

## 0. 目的

qMRLab（MATLAB）の主要モデルを Python に移植し、以下を満たす状態を目指す。

- **数値的に** MATLAB 実装と整合する（許容誤差を明示）。
- 再現可能な run 形式（`output/runs/<run_id>/`）で検証できる。
- 最終的に論文図表へ昇格可能な形で、検証結果を可視化・記録できる。
- 追加目的：`qmrpy` パッケージとして **配布可能（PyPI公開可能）** な品質・体裁にする。

## 1. スコープ（In / Out）

### In scope

- qMRLab の「モデル（Forward/Inverse）」のうち、移植対象を段階的に選定して実装する。
- 小さな合成データ・テストベクトルでの数値整合性検証。
- Python API を最小限に揃え、徐々に統一（入出力、パラメータ表現、単位など）。
- `qmrpy` としてのパッケージング（`pyproject.toml`、srcレイアウト、テスト、最低限のドキュメント、リリース手順）。

### Out of scope（当面）

- GUI 相当の実装。
- 全モデルの一括移植（優先度順に段階実装する）。
- 速度最適化（Numba/CUDA等）は、整合性が取れてから検討する。
- 初期段階でのフル機能互換（qMRLabの全オプション/UI/周辺ツールの移植）。

## 2. Research Questions / 仮説

RQ1: 代表的な1〜2モデル（例：`mono_t2`, `vfa_t1`）を Python に移植したとき、MATLAB と同等の推定精度を再現できるか？  
H1: 同一の forward model と同等の最適化手順（初期値・制約・損失）を用いれば、推定値は MATLAB と同等（許容誤差内）になる。

RQ2: モデル横断で共通化できる入出力・最適化パイプラインの最小公倍集合は何か？  
H2: データテンソル＋プロトコル（TR/TE/FA等）＋パラメータ辞書の3点を固定すれば、共通のfitインターフェースに寄せられる。

## 3. データ計画

- 当面は **合成データ** を主とし、qMRLab の forward model で生成した信号を教師として整合性を検証する。
- 実データは、ライセンス/匿名化/配布条件を満たす場合のみ導入する（導入時は `docs/protocols/` に手順を書く）。
- 分割（train/valid/test）: 研究の性質上、当面は「条件セット別のhold-out」を想定（例：ノイズ水準やB1誤差など）。

## 4. 手法/モデル候補と比較条件

### 候補（優先度案）

1. `mono_t2`（T2 relaxometry）※最初の実装対象（確定）
2. `vfa_t1`（T1 relaxometry）
3. `inversion_recovery`（T1 relaxometry）

### 比較条件（最低限）

- MATLAB(qMRLab) の出力 vs Python 実装の出力（同一条件）
- ノイズ無し vs ノイズ有り
- 初期値/境界条件（同一 vs 変動）による頑健性

## 5. 評価指標（Primary/Secondary）

### Primary

- 推定パラメータ誤差：MAE / RMSE（既知真値に対して）
- MATLAB との差：相対誤差（%）/ 絶対差

### Secondary

- 収束率（最適化が失敗しない割合）
- 計算時間（将来の改善用ログ）

## 6. 分析計画（Confirmatory / Exploratory）

### Confirmatory（検証）

- 固定した合成条件セットで、MATLAB と Python の一致度を定量化する。
- 受け入れ基準（暫定）：代表条件で **相対誤差 1e-3〜1e-2 程度**を初期目標にし、モデルごとに現実的に調整する。

#### `mono_t2` の受け入れ基準（v0.1.xの目標）

- ノイズ無し合成データで、推定 `T2` の相対誤差（|Δ|/T2）が `<= 1e-3` を満たす。
- ノイズ有り（ガウス）でも、代表条件セットで RMSE の悪化が過度でないことを図表で確認する。

### Exploratory（探索）

- 初期値、ノイズモデル、制約の変更に対する感度分析。
- パラメータ再パラメータ化（例：log空間）等の安定化手法の検討。

## 7. run の再現性仕様（必須）

- 出力は `output/runs/<run_id>/` に集約する。
- 必須：
  - `run.json`（コマンド、configパス、seed、git hash/dirty、環境、主要出力パス）
  - `config_snapshot/`（実行時の設定をコピー）
  - `metrics/`, `figures/`, `logs/`, `artifacts/`（使うもののみで可、ただし `metrics/figures` は必須）

### seed / 反復（暫定）

- 乱数 seed は `seed=0` を基本とし、頑健性確認では `seed in {0,1,2,3,4}` を回す。
- 合成データ生成の乱数と最適化初期値の乱数は、同一 seed から分岐して記録する（`run.json` に明記）。

## 8. 論文計画（図表の昇格ルール）

- run から論文に貼る図は `docs/manuscript/figures/` にコピーして固定する。
- 固定図には run_id を埋め込む（例：`fig1__from_<run_id>.png`）。
- `docs/manuscript/figures_manifest.yaml` に出自を記録する。

## 9. リスクと対策

- 数値差（実装差/最適化差）で一致しない：forward と損失を先に一致させ、段階的に差分を潰す。
- 単位/定義の取り違え：モデルごとに「パラメータ定義表」を作り、決定ログに残す。
- 依存パッケージの揺れ：uv lock を固定し、`--locked` 運用を徹底する。

## 10. マイルストン（目安）と Exit criteria

- M0: パッケージ雛形（`pyproject.toml` + `src/qmrpy` + 最小テスト）を追加し、import可能にする。
- M1: 対象モデルを1つ選定し、forward model + fit の最小実装と整合性検証を完了する。
- M2: run 形式で自動生成（metrics/figures/run.json）できるようにする。
- M3: 2モデル以上で共通インターフェース化し、簡単なレポート/図表を作る。
- M4: パッケージ公開準備（API安定化方針、互換性テスト、最低限のドキュメント、`uv.lock` 固定、リリース手順）を満たし、`0.1.0` をタグ付け可能にする。

### 週次マイルストン（目安）

- Week 1: `mono_t2` の forward + fit を実装し、合成データで最低限の数値テストを作る。
- Week 2: run 形式（`run.json`/`metrics`/`figures`/`config_snapshot`）の雛形を整備し、可視化A/B/Cの最低3点セットを出す。
- Week 3: `vfa_t1` のスコープ設計（I/O・単位・プロトコル）を決め、2モデル目に着手する。

Exit criteria（暫定）：

- 主要モデル（少なくとも2つ）で MATLAB との一致度が受け入れ基準を満たし、再現 run と図表が残っている。
- `qmrpy` を `pip install` 相当で導入でき、主要APIがドキュメント化され、最小の自動テストが通る。

## 10.1 公開（配布）計画（追加）

### 対象ユーザー

- 研究用途のユーザー（qMRIのモデルを Python から利用したい人）
- 再現性重視：入力はGit、出力は `output/` へ、を前提とする運用

### Python/依存

- Python: まずは `>=3.11` を正式サポートとする（開発環境は 3.11 系で固定）。
- 依存は最小から開始（`numpy`, `scipy`）。可視化は optional（`plotnine`）に分離する。

### バージョニング（暫定）

- SemVer を採用する。
- `0.y.z` の間は破壊的変更が入り得るが、`CHANGELOG` と `docs/decisions/` で必ず根拠を残す。

### 品質ゲート（リリース前に満たす）

- `pytest` が通る（少なくとも import/最小ユニット）。
- 代表モデルについて、合成データで MATLAB との差分が規定以内（指標・図表で示す）。
- リリース手順（`docs/protocols/release.md`）があり、手作業を最小化して再現可能にする。

## 11. AI協働ルール（意思決定ログ）

- 仕様・設計の採否は `docs/decisions/` に短く残す。
- 日々の作業は `docs/studynote.md` に記録する（どのファイルを触ったかを含む）。

## 12. Changelog（更新ルール：差分＋理由）

更新ルール（必須）：

- `docs/studyplan.md` を更新したら、この Changelog に **差分** と **理由** を必ず追記する。
- `Status: active` に上げるのは Definition of Ready を満たした時のみとする。

### v0.0.1（2025-12-18）

- 追加：Studyplan の初版（draft）を作成した（qMRLab Python移植の枠組みを先に固定するため）。

### v0.0.2（2025-12-18）

- 追加：seed/反復方針と、Changelog の更新ルールを明文化した（再現性監査を容易にするため）。

### v0.0.3（2025-12-18）

- 追加：PyPI公開を目的に、パッケージング/リリース計画（M0/M4、品質ゲート、依存分離）を追記した（公開要件を先に固定するため）。


### v0.1.0（2025-12-18）

- 変更：`Status: active` に移行し、最初の実装対象を `mono_t2` に確定した（作業開始ゲートを通すため）。
- 追加：`mono_t2` の受け入れ基準（暫定）と、週次マイルストンを追記した（進捗監査を容易にするため）。

# Decision: パッケージ構成（srcレイアウト）とバージョニング

Date: 2025-12-18  
Status: accepted

## Context

本リポジトリは qMRLab（MATLAB）を Python に移植し、最終的に `qmrpy` として配布（PyPI公開）することを目標とする。配布可能性を早期に確保するため、最小のパッケージ雛形と運用方針を先に固定したい。

## Decision

- `src/` レイアウト（`src/qmrpy/`）を採用する。
- ビルドは PEP 517 の標準に寄せ、`pyproject.toml` ベースで管理する（ビルドバックエンドは `hatchling` を採用）。
- Python サポートは当面 `>=3.11` とする（開発環境も 3.11 系で固定）。
- バージョニングは SemVer を採用し、`0.y.z` 期間は破壊的変更が入り得る前提で、変更根拠を `docs/decisions/` と `docs/studyplan.md` の Changelog に残す。

## Rationale

- `src/` レイアウトは import の事故（作業ディレクトリの影響）を避け、配布形態に近い状態で開発できる。
- `pyproject.toml` に寄せることで、配布・CI・ツール設定が一箇所に集約できる。
- 依存・動作環境を絞ることで、数値整合性検証（qMRLabとの比較）を優先できる。

## Consequences

- 初期段階でも `pip install -e .` 相当の導入形に近づく。
- `uv.lock` の導入・固定が必須になる（ネットワーク許可が必要な場面がある）。


# Decision: qMRLab（MATLAB）参照コードの扱い

Date: 2025-12-18  
Status: accepted

## Context

本リポジトリは qMRLab の Python 翻訳（移植）を目的としている。一方で upstream の MATLAB 実装（`qMRLab/`）は参照・差分確認・テストベクトル作成のために手元に置きたい。

## Decision

`qMRLab/` は **ローカル参照用（Git 管理外）** とし、`.gitignore` で除外する。

## Rationale

- upstream 全体を本リポジトリに取り込むと、履歴・責務が混在しやすい。
- Python 実装の再現性は `src/`, `scripts/`, `configs/`, `docs/` を中心に担保できる。
- upstream への追従は将来的に submodule 等へ移行できるが、まずは移植・検証フローを確立するのが優先。

## Consequences

- `qMRLab/` はユーザー環境に存在しても Git では追跡しない。
- 将来、upstream の固定が必要になったら submodule 化を再検討する。


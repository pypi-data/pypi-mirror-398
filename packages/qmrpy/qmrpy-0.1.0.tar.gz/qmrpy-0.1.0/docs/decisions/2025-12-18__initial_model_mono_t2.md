# Decision: 最初の実装対象モデルを `mono_t2` にする

Date: 2025-12-18  
Status: accepted

## Context

PyPI公開を見据え、最初のスプリントでは「縦切り」で価値を出す必要がある。qMRLab の多数モデルを一括で移植するのではなく、最小の forward + fit + 検証（合成データ）を通す代表モデルを選びたい。

## Decision

最初の実装対象モデルは `mono_t2`（T2 relaxometry）とする。

## Rationale

- 入出力が比較的シンプルで、合成データによる整合性検証を最短で回せる。
- モデル横断共通化（protocol/params/fit）の土台を作るのに適している。

## Consequences

- v0.1.x の最優先は `mono_t2` の forward と fit の整合性・再現性・テストになる。
- 次モデル（候補：`vfa_t1`）は `mono_t2` のI/O設計を踏まえて設計する。


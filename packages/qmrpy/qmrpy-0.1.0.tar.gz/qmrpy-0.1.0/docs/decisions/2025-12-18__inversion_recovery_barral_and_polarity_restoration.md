# Decision: `inversion_recovery`（Barral式）と magnitude の極性復元

Date: 2025-12-18  
Status: accepted

## Context

qMRLab の `inversion_recovery` は Barral のフィット式 `S = ra + rb * exp(-TI/T1)` を用い、magnitude データの場合は極性が失われるため「polarity restoration（idx）」を行う。

## Decision

- `qmrpy.models.t1.InversionRecovery` は qMRLab と同じ Barral 式で実装する。
- `method="complex"`：そのまま `S=ra+rb*exp(-TI/T1)` を最小二乗で当てる。
- `method="magnitude"`：観測を `|S|` とみなし、`idx=0..N` を総当たりして
  - `y_restored[:idx] *= -1` で極性復元した系列を作り
  - 最小二乗の残差が最小の `idx` を採用する。

## Units

qMRLab に合わせ、`TI` と `T1` は **[ms]** とする（`ti_ms`, `t1_ms`）。

## Rationale

- upstream と同条件で比較・検証しやすい。
- magnitude データの極性復元は最小限の実装で挙動を揃えやすい（まず一致を優先）。


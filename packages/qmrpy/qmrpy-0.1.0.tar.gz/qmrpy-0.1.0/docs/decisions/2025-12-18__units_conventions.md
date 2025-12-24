# Decision: 単位（TE/TR/T1/T2 など）の取り扱い

Date: 2025-12-18  
Status: accepted

## Context

qMRLab の各モデルはプロトコルの単位がモデルごとに異なる（例：`mono_t2` は TE が [ms]、`vfa_t1` は TR が [s]）。Python移植で単位が曖昧だと、モデル間比較や run の再現性が崩れやすい。

## Decision

`qmrpy` では **qMRLab の Protocol に記載された単位を尊重**し、モデルごとに単位を明示して扱う。

- `MonoT2`:
  - `te`: [ms]
  - `t2`: [ms]
  - `m0`: 任意単位（信号スケール）
- `VfaT1`（予定）:
  - `flip_angle`: [deg]（B1補正は `FA_actual = B1 * FA_nominal`）
  - `tr`: [s]
  - `t1`: [s]
  - `m0`: 任意単位
- `InversionRecovery`:
  - `ti_ms`: [ms]
  - `t1_ms`: [ms]
  - `ra`, `rb`: 任意単位
- `B1Dam`:
  - `alpha_deg`: [deg]
  - `b1`: 無次元（`FA_actual = b1 * FA_nominal`）

## Rationale

- upstream と同一条件で比較しやすい。
- 変換（ms↔s）を勝手に挟むより、I/Oで明示した方が事故が少ない。

## Consequences

- config / run.json / 図のラベルには単位を必ず含める。
- 将来、モデル横断で統一単位に寄せる場合は `docs/decisions/` で合意した上で段階移行する。

# Decision: `mono_t2` のフィットオプション（FitType/DropFirstEcho/OffsetTerm）

Date: 2025-12-18  
Status: accepted

## Context

qMRLab の `mono_t2` は以下のオプションを持つ：

- `FitType`: `Exponential` / `Linear`
- `DropFirstEcho`: 最初のエコーを落とす
- `OffsetTerm`: オフセット項を追加

Python移植でもこれらが無いと、upstreamと挙動が揃えづらく、また現実データでの失敗解析もしづらい。

## Decision

- `qmrpy.models.t2.MonoT2.fit(...)` に以下を追加する：
  - `fit_type: "exponential" | "linear"`
  - `drop_first_echo: bool`
  - `offset_term: bool`
- run では `configs/exp/*.toml` でオプションを指定し、`metrics/run.json` に出力して再現可能にする。

## Notes

- 現段階では、qMRLab の正規化（`y = abs(y)/max(y)`）に近い処理を入れて、まず `T2` の一致を優先する。
- `M0` はスケールの定義が揃ってから一致性を議論する（必要なら追加のdecisionで合意する）。


# 意思決定ログ: epgpy 統合（vendor）と EPG backend 選択

- Date: 2025-12-18
- Status: accepted

## 背景 / 課題

- qMRLab/qMR系の一部モデル（例: multi spin echo / T2 分布推定）では、EPG（Extended Phase Graph）に基づく信号生成が必要になる。
- 既存の `qmrpy` 実装には、DECAES.jl 由来の「簡略 EPG（刺激エコー補正込み）」実装が含まれているが、今後の拡張（一般的なシーケンス表現・保守性）を考えると、専用ライブラリの導入が有利である。
- リポジトリ内に `epgpy/`（BSD 3-Clause）が存在しているため、これを `qmrpy` の実装に組み込んで利用したい。

## 決定

1) `epgpy` を `src/epgpy/` に vendor（スナップショット配置）し、`qmrpy` から `import epgpy` 可能にする。  
2) 配布物（wheel/sdist）に BSD 3-Clause のライセンス文面を必ず同梱するため、`THIRD_PARTY_NOTICES.md` を追加し、wheel に force-include する。  
3) `src/qmrpy/models/t2/decaes_t2.py` の `epg_decay_curve` に `backend` を追加し、以下を選択可能にする：
   - `backend="epgpy"`: vendored `epgpy` のシミュレータを使用（デフォルト）
   - `backend="decaes"`: DECAES-style の簡略実装を使用（比較/パリティ用）
4) `DecaesT2Map` には `epg_backend` を追加し、basis（design matrix）生成時に選択した backend を使う。

## 理由

- `epgpy` を vendor することで、外部依存（PyPI 有無・バージョン差・ネットワーク制約）に左右されず、CI/配布で同じ EPG 実装を使える。
- 一方で、DECAES.jl との数値パリティ検証や差分調査のために、既存の簡略実装も残して比較できる形にする。

## 影響範囲 / 注意点

- `backend="epgpy"` は一般的な TSE/CPMG 形式の EPG シミュレーションを用いるため、DECAES.jl の簡略実装と数値が一致しない条件があり得る。
  - パリティ検証目的では `backend="decaes"` を優先して比較する。
- `epgpy` は BSD 3-Clause のため、配布時にライセンス条項を同梱・表記する。

## 変更ファイル

- `src/epgpy/`（vendor）
- `src/qmrpy/models/t2/decaes_t2.py`
- `tests/test_decaes_t2.py`
- `THIRD_PARTY_NOTICES.md`
- `pyproject.toml`


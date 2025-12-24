# 第三者由来コードの表記方針（qMRLab / epgpy / DECAES.jl）

日付: 2025-12-19

## 決定

- `THIRD_PARTY_NOTICES.md` に、以下の upstream のライセンス文面と由来を明記する。
  - qMRLab（MIT）
  - epgpy（BSD 3-Clause、vendor）
  - DECAES.jl（MIT）
- README に「第三者由来コードの扱い」セクションを追加し、翻訳/参考実装/同梱の区別を明確化する。
- 配布物（wheel / sdist）には `THIRD_PARTY_NOTICES.md` を同梱し、表記義務を満たす。

## 理由

- 翻訳・再構成・一部流用を含むため、由来とライセンス表記の透明性を担保する必要がある。
- upstream が MIT/BSD 系であっても、由来の混同を避けるため明示的な記録が必要。

## 影響範囲

- ドキュメント: `README.md`, `THIRD_PARTY_NOTICES.md`, `docs/protocols/release.md`
- 配布物: `THIRD_PARTY_NOTICES.md` を wheel に含める（既存設定を維持）

## 補足

- `qMRLab/` と `DECAES.jl/` はローカル参照用であり、配布物には同梱しない。
- qMRLab 内に含まれる第三者ライセンスのコードは本リポジトリへ取り込んでいない前提で運用する。

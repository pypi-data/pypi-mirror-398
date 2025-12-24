# Decision: ライセンス（MIT）と表記方針

Date: 2025-12-18  
Status: accepted

## Context

`qmrpy` は qMRLab（MIT License）の概念・モデルを参照しつつ Python 実装として再構成する。PyPI公開を行うには、本リポジトリ側の LICENSE と著作権表記を明確にする必要がある。

## Decision

- 本リポジトリ（qmrpy）も MIT License とする。
- qMRLab（MIT）の由来・参照元を README/ドキュメントに明記する。

## Notes / Open questions

- `LICENSE` の著作権者表記を誰/どの形式にするか（例：`Copyright (c) 2025 <name>`）。
- qMRLab のコードを「翻訳・移植」する範囲（直接のコード移植がどれだけ入るか）に応じて、NOTICE相当の追記が必要か。

（追記）著作権表記は以下で確定した。

- `Copyright (c) 2025 Kohei Sugimoto`

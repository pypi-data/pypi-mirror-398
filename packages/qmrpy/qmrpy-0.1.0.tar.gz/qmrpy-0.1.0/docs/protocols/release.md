# リリース手順（暫定）

目的：`qmrpy` を PyPI 公開できる状態にし、再現可能な形でリリースする。

## 前提

- Python は 3.11 系で開発する。
- 依存は `uv` で固定し、`uv.lock` を Git 管理する。
- 公開前に `docs/studyplan.md` が `Status: active / Version: v0.1.0` を満たしていること。

## 手順（案）

0. ライセンス/第三者表記の確認
   - `THIRD_PARTY_NOTICES.md` に **qMRLab / epgpy / DECAES.jl** の記載があること。
   - `pyproject.toml` の `tool.hatch.build.targets.wheel.force-include` に
     `THIRD_PARTY_NOTICES.md` が含まれていること。
   - upstream 由来コードの翻訳/流用範囲が説明可能であること（必要なら
     `docs/decisions/` に記録する）。
1. バージョン更新
   - `src/qmrpy/__init__.py` の `__version__` を更新する。
   - `docs/decisions/`（必要なら）と `docs/studynote.md` に記録する。
2. 依存固定
   - `uv lock --upgrade`（必要な場合のみ）
   - `uv lock --check`
3. テスト
   - `uv sync --locked`
   - `uv run -m pytest`
4. ビルド
   - `uv build`
5. 配布（本番）
   - `uv run -m twine upload dist/*`

## 注意

- まずは `0.1.0` を目標にし、それ以前は API 破壊的変更があり得る前提で運用する。
- 公開前に LICENSE/著作権表記、qMRLab 由来のコード/概念の扱いを `docs/decisions/` に整理する。

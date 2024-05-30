# JSON Canvas to Markdown

## はじめに
==⚠This document is written in Japanese. For the English version, please refer to [this document](README_ENG_version.md).⚠==


==⚠このドキュメントは日本語で書かれています。Google翻訳で日本語から日本語に翻訳しないようにしてください⚠==

JSON Canvasと呼ばれるオープンソースの無限キャンバスツールで作成された`.canvas`データをMarkdownファイルに変換するPythonスクリプトを作成しました。

無限キャンバスツールは小説やゲームのシナリオなどに関するメモを二次元空間に自由に配置し、メモ同士を線や矢印で繋ぐことでプロットを作成するのに便利ですが、そのプロットをファイルとして出力することは容易ではありませんでした。
本スクリプトではノードとエッジの情報をローカルで解析し、矢印で繋がれたメインストーリー, それに関するメモ, そして孤立したメモの3つに分類したあと、それらを1つのMarkdownファイルにまとめて出力します。
これにより、無限キャンバスの内容をテキストファイルに落とし込むという事務作業から開放され、より一層創作活動に専念できるようになります。

## JSON Canvasとは
JSON Canvasは、[Obsidianが2024年3月にリリースした](https://obsidian.md/blog/json-canvas/)、[オープンソース](https://github.com/obsidianmd/jsoncanvas)の無限キャンバス機能です。無限に広がるキャンバス上にノードとエッジを配置し、自由に結びつけることでネットワーク状の情報構造を表現できます。ノードにはテキストやファイル、リンクなどを埋め込むことができ、それらをエッジ(線や矢印)で繋げることで関係性を可視化できます。
![](Canvas2MD_DEMO_Canvas.png)

## このスクリプトができること
以下のような形式のJSON Canvas(`.canvas`)ファイルをMarkdownファイルにできます。

```mermaid
flowchart TD
    A[Start] --> B[Ep1] -->C[Ep2]-->D[Ep3]-->E[End]
    Y[memo]
    Z[SubEp] --- C
```

![](Canvas2MD_Sample_Canvas.png)

```Markdown
## Start
`Start`ノードの内容

## Ep1
`Ep1`ノードの内容

## Ep2
`Ep2`ノードの内容[^SubEp]

## Ep3
`Ep3`ノードの内容

## End
`End`ノードの内容

[^SubEp]: `SubEp` の内容

---

## memo
`memo`の内容
```


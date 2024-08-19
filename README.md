# 不動産登記情報 形式変換　(Touki Parser )


## 概要

Touki Parser は、[登記情報提供サービス](https://www1.touki.or.jp/gateway.html)が提供している
不動産登記情報のPDFファイルの登記情報の表題部、権利部を読み取りタブ区切り形式に出力します。

## 利用方法

Usage:
```
  pdf_extract_part_of_pdf.py <folder_in> <folder_out>

  <folder_in>: file folder where data is extracted
  <folder_out>: file folder where data is extracted
```

<folder_out> に指定されたフォルダには次の３つのファイルを出力します。

|ファイル名| ファイルの内容|
|--------|----------|
|output_parsed_list.csv| 登記情報の最終履歴が保存されています |
|output_parsed_list_split.csv| 登記情報の履歴が保存されています |
|output_parsed_pdf_text.txt| 登記情報のPDF中のテキストが保存されています|

## License

MIT
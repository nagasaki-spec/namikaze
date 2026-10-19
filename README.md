# 波風サーフ予報

スマホ向けの波・風予報アプリ（単一HTML）。データは Open-Meteo（Marine API / Forecast API）。

- `波風.html` … 配布用の完成ファイル。ブラウザで開くと最新予報を取得します。
- `src/body.html` … アプリ本体のソース（ポイント追加・色やしきい値の変更はここ）
- `src/regions.json` … 地図の地域定義（範囲・格子間隔）
- `src/coast.json` … 海岸線（Natural Earth 10m を日本周辺で切り出し。`coast.py` で再生成）
- `src/build.py` … スナップショットを取得して `波風.html` を生成

## 再ビルド

```
cd src
python -I build.py . ../波風.html ../artifact.html
```

4つ目の引数で地図を埋め込む地域を指定できます（例 `jp,kanto,okinawa`）。
全地域を埋め込むと Open-Meteo の分間制限で待ち時間が入り、10分ほどかかります。

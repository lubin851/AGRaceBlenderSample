# AGRaceSDK 用コースモデルサンプル
AGRace の配布コースサンプルです。<br>
Blender のサンプルとアドオンを公開しています。<br>
<img width="434" height="252" alt="image" src="https://github.com/user-attachments/assets/2b193a55-a324-4629-8579-5560eb5a1e6f" />

## ダウンロード

- [Blenderサンプル一式をダウンロード（.blendとTexture）](https://github.com/lubin851/AGRaceBlenderSample/releases/latest/download/AGRaceCourse_Template.zip)
- [AGRace Toolsの最新版ZIPをダウンロード](https://github.com/lubin851/AGRaceBlenderSample/releases/latest/download/agrace_tools.zip)

ZIPのリンクは最初のGitHub Release公開後に利用できます。サンプルZIPは展開し、`BlenderSample/AGRaceCourse_Template.blend`と`BlenderSample/Texture`の位置関係を保ってください。

## Blender サンプル

モディファイアによるモデル製作例、コライダーモデルとビジュアルモデルの差分などを確認できます。
同梱のテクスチャは改変元や参考に使用可能です。<br>
AGRaceSDK には同じテクスチャと設定済みマテリアルがある為、それを利用してください。このテクスチャをそのまま配布する必要はありません。<br>
ただし、テクスチャやモデルを改変・自作したものを配布する場合は自身のパッケージに含めるようにしてください。<br>
<img width="211" height="67" alt="image" src="https://github.com/user-attachments/assets/5c1e76bc-bdd8-4a32-9f47-38c8c34cd155" />
<br>
### ライセンス
・許可<br>
改変したデータなどは再配布可能です。<br>
このデータを元に作成した場合は、製作元であるここのリンクを貼ってください。<br>
ダウンロード者同士の共有を許可します。<br>
・禁止<br>
.blendやテクスチャを再配布は禁止です。AGRaceSDK同梱のテクスチャを参照するか、改変または作成してください。<br>
このサンプルの制作者を偽ることは禁止です。<br>
ここで配布している.Blendやテクスチャを再配布は禁止です。ただし、許可に記載しているダウンロード者同士の共有は許可されます。<br>

## AGRace Tools
AGRaceSDKのコース制作を支援するアドオンです。<br>
任意のコースの断面同士、円柱に沿った形状への接続をスムーズになるよう生成します。<br>
また、オブジェクトの一括リネームや、データ名を属するオブジェクトへ統一する機能も付属しています。<br>
<img width="327" height="415" alt="image" src="https://github.com/user-attachments/assets/0a0ebc56-da94-4993-a0a7-3b384390d961" />
<img width="328" height="417" alt="image" src="https://github.com/user-attachments/assets/9bab394f-813f-400c-87b6-1e4e00e19d64" />

### 対応Blenderバージョン
5.0以降<br>
検証済み:5.1.1

### インストール

Blender内で更新できる方法を使う場合は、`Edit > Preferences > Get Extensions`のリポジトリ設定から「Add Remote Repository」を選び、次のURLを登録します。READMEのURLをクリックするだけではBlenderへの登録は行われないため、URLをコピーして貼り付けてください。

`https://lubin851.github.io/AGRaceBlenderSample/index.json`

一覧を更新して`AGRace Tools`を検索・インストールし、有効にします。更新版が公開されたら同じ画面でリモートの一覧を更新し、表示された更新を適用します。起動時の更新確認はBlenderのリポジトリ設定で任意に有効化できます。

ZIPを直接使う場合は、上の最新版ZIPを展開せずに保存し、`Edit > Preferences > Get Extensions`の右上メニューから`Install from Disk`で指定します。ZIPのドラッグ＆ドロップでも導入できます。ただし、この方法はローカルインストールになり、上記リポジトリからの更新対象にはなりません。

導入後、3D Viewportで`N`を押し、`AGRace Tools`タブを開きます。

### Y軸スムーズ接続の簡単な使い方

1. 同じMeshの編集モードで、ローカルY方向に離れた開いた辺列を2本用意し、頂点数を揃えます。両方の中央頂点（ローカルX=0）は同じ上下側に置きます。
2. 接続する2本の辺列だけを選択します。
3. `AGRace Tools > Y軸スムーズ接続`で分割数などを調整し、`スムーズ接続を生成（別OBJ）`を押します。

### 円柱スムーズ接続の簡単な使い方

1. 任意の辺から接続する場合は、Meshの編集モードでローカルX=0から+X側へ伸びる半幅の開いた辺列を1～2本選択します。
2. `AGRace Tools > 円柱スムーズ接続`で生成タイプ、Y方向の長さ、半径などを設定し、`円柱スムーズ接続を生成（別OBJ）`を押します。
3. `半円 → 円`は辺を選択せずに生成できます。

どちらも元のMeshとは別のオブジェクトを生成します。入力条件や詳細設定は[アドオンのマニュアル](Add_on/AGRaceTools/agrace_tools/README.md)を参照してください。

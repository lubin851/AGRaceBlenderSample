# AGRaceSDK 用コースモデルサンプル
AGRace の配布コースサンプルです。<br>
Blender のサンプルとアドオンを公開しています。<br>
<img width="434" height="252" alt="image" src="https://github.com/user-attachments/assets/2b193a55-a324-4629-8579-5560eb5a1e6f" />

## ダウンロード

- [Blenderサンプル一式をダウンロード（.blendとTexture）](https://lubin851.github.io/AGRaceBlenderSample/download.html?file=sample)
- [AGRace ToolsのZIPをダウンロード](https://lubin851.github.io/AGRaceBlenderSample/download.html?file=addon)　※自動更新無し
- リポジトリを登録して更新通知を受け取る場合は、こちらのURLを登録してください。`https://lubin851.github.io/AGRaceBlenderSample/index.json`
- アドオンの使い方：[アドオンのマニュアル](Add_on/AGRaceTools/agrace_tools/README.md)

リンクをクリックすると、最新版のGitHub Releaseに添付されたZIPのダウンロードへ進みます。アドオンZIPのファイル名にはバージョンが付きます。サンプルZIPは展開し、`BlenderSample/AGRaceCourse_Template.blend`と`BlenderSample/Texture`の位置関係を保ってください。

## Blender サンプル

モディファイアによるモデル製作例、コライダーモデルとビジュアルモデルの差分などを確認できます。
同梱のテクスチャは改変に使用可能です。<br>
未改変の際には AGRaceSDK に同じテクスチャと設定済みマテリアルがある為、それを参照利用してください。似たテクスチャを二重に導入する恐れがある為です。<br>
<img width="211" height="67" alt="image" src="https://github.com/user-attachments/assets/5c1e76bc-bdd8-4a32-9f47-38c8c34cd155" />
<br>
### ライセンス

このライセンスはBlenderサンプルとテクスチャに適用されます。
・許可<br>
.blendとテクスチャデータは再配布可能です。
このデータを元に作成した場合は、製作元であるここのリンクを貼って頂けると嬉しいです。<br>
・禁止<br>
このサンプルの制作者を偽ることは禁止です。<br>

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


Blender内で更新できる方法を使う場合は、`Edit > Preferences > Get Extensions`のリポジトリ設定から「Add Remote Repository」を選び、次のURLをコピーして貼り付けてください。

`https://lubin851.github.io/AGRaceBlenderSample/index.json`

一覧を更新して`AGRace Tools`を検索・インストールし、有効にします。更新版が公開されたら同じ画面でリモートの一覧を更新し、表示された更新を適用します。起動時の更新確認はBlenderのリポジトリ設定で任意に有効化できます。

ZIPをダウンロードする場合は[こちらからダウンロード](https://lubin851.github.io/AGRaceBlenderSample/download.html?file=addon)　してZIPを展開せずに保存し、`Edit > Preferences > Get Extensions`の右上メニューから`Install from Disk`で指定します。ZIPのドラッグ＆ドロップでも導入できます。ただし、この方法はローカルインストールになり、上記リポジトリからの更新対象にはなりません。

導入後、3D Viewportで`N`を押し、`AGRace Tools`タブを開きます。

### Y軸スムーズ接続の簡単な使い方

このツールは形状が違う離れた辺同士を滑らか繋ぐ面を生成します。別オブジェクトで生成します。
1. 同じオブジェクトに繋ぎたいコースの断面の辺を配置します。配置はY軸方向に任意の距離で離して配置します。
2. +X軸方向のみの辺を残します。ミラー用にX軸の座標0に頂点があるようにします。
3. X座標が０の頂点が+Y軸にあると上面扱い、-Y軸にあると下面扱いになります。両方置いて同時生成も可能です。
4. 頂点数を同じにします。レイキャスト受けがある場合は辺の長さを変えないよう注意してください。
5. 接続する2本の辺の頂点を選択します。
6. `AGRace Tools > Y軸スムーズ接続`で分割数などを調整し、`スムーズ接続を生成（別OBJ）`を押します。Xミラーモディファイア付きのメッシュが生成されます。

### 円柱スムーズ接続の簡単な使い方

このツールは離れた辺または、円柱に沿った断面形状へ滑らかに繋ぐ面を生成します。別オブジェクトで生成します。
1. 任意の辺から接続する場合は、前述のY軸スムーズと同様に辺を配置します。配置した辺から+Y方向へ生成されます。上下面同時可能です。
2. 生成したい頂点を選択します。
3. 半円（任意の円弧） → 円の生成をする場合はツールからそのまま設定を行います。
4. `AGRace Tools > 円柱スムーズ接続`で生成タイプ、Y方向の長さ、半径などを設定し、`円柱スムーズ接続を生成（別OBJ）`を押します。Xミラーモディファイア付きのメッシュが生成されます。

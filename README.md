# AGRaceSDK 用コースモデルサンプル / Course Model Sample
AGRace の配布コースサンプルです。<br>
Blender のサンプルとアドオンを公開しています。<br>
Here are sample courses for AGRace.<br>
I have released Blender samples and add-ons.<br>
<img width="434" height="252" alt="image" src="https://github.com/user-attachments/assets/2b193a55-a324-4629-8579-5560eb5a1e6f" />

## AI活用の表明 / Announcement of AI Adoption

このリポジトリとアドオンの制作にはCodexを利用したディレクトリとコード生成、情報収集を活用しています。<br>
それに対して自然由来のAIが設計と冗長な文言と冗長なアイディアに対して冗長なレビューバトルを申し込んでいます。<br>
Codex was utilized in the creation of this repository and add-on to handle directory structure, code generation, <br>
and information gathering. In response, a natural-origin AI has challenged the design, verbose wording, and redundant ideas to a "verbose review battle."

## ダウンロード / Download

- [Blenderサンプル一式をダウンロード（.blendとTexture）](https://lubin851.github.io/AGRaceBlenderSample/download.html?file=sample) Download the complete set of Blender samples.
- [AGRace ToolsのZIPをダウンロード ※自動更新無し](https://lubin851.github.io/AGRaceBlenderSample/download.html?file=addon)　Download AGRace Tools ZIP *No automatic updates
- リポジトリを登録して更新通知を受け取る場合は、こちらのURLを登録してください。<br>To register the repository and receive update notifications, please register this URL.<br>`https://lubin851.github.io/AGRaceBlenderSample/index.json`
- アドオンの使い方：[アドオンのマニュアル](Add_on/AGRaceTools/agrace_tools/README.md) How to use the add-on

## Blender サンプル / Blender sample

モディファイアによるモデル製作例、コライダーモデルとビジュアルモデルの差分などを確認できます。
同梱のテクスチャは改変に使用可能です。<br>
未改変の際には AGRaceSDK に同じテクスチャと設定済みマテリアルがある為、それを参照利用してください。似たテクスチャを二重に導入する恐れがある為です。<br>
You can view examples of model creation using modifiers and examine the differences between collider models and visual models.<br>
The included textures may be used for modifications.<br>
If you are not modifying the model, please use the identical textures and pre-configured materials found in the AGRaceSDK instead, to avoid importing duplicate textures.<br>
<img width="211" height="67" alt="image" src="https://github.com/user-attachments/assets/5c1e76bc-bdd8-4a32-9f47-38c8c34cd155" />
<br>

### ライセンス / License

このライセンスはBlenderサンプルとテクスチャに適用されます。<br>
・許可<br>
.blendとテクスチャデータは再配布可能です。<br>
このデータを元に作成した場合は、製作元であるここのリンクを貼って頂けると嬉しいです。<br>
・禁止<br>
このサンプルの制作者を偽ることは禁止です。<br>
<Br>
This license applies to the Blender samples and textures.<br>
・Permitted<br>
You may redistribute the .blend and texture data.<br>
If you create something based on this data, I would appreciate it if you included a link to the original source here.<br>
・Prohibited<br>
Misrepresenting yourself as the creator of these samples is prohibited.<br>

## 🧰 AGRace Tools
AGRaceSDKのコース制作を支援するアドオンです。<br>
任意のコースの断面同士、円柱に沿った形状への接続をスムーズになるよう生成します。<br>
また、オブジェクトの一括リネームや、データ名を属するオブジェクトへ統一する機能も付属しています。<br>
This is an add-on designed to assist with course creation in AGRaceSDK.<br>
It generates smooth transitions between arbitrary course cross-sections and shapes aligned with cylinders.<br>
It also includes features for batch-renaming objects and synchronizing data names with the objects themselves.<br>
<img width="327" height="415" alt="image" src="https://github.com/user-attachments/assets/0a0ebc56-da94-4993-a0a7-3b384390d961" />
<img width="328" height="417" alt="image" src="https://github.com/user-attachments/assets/9bab394f-813f-400c-87b6-1e4e00e19d64" />

### 対応Blenderバージョン / Supported Blender versions
5.0以降 / 5.0 or later <br>
検証済み / Verified : 5.1.1

### インストール / Install

Blender内でダウンロードと更新通知を利用する場合は、`編集 > プリファレンス > エクステンションを入手`の**リポジトリ**から<br>
**+(リモートリポジトリ)** を押し、次のURLをコピーして貼り付けてください。<br>
<br>
`https://lubin851.github.io/AGRaceBlenderSample/index.json`<br>
<br>
一覧を更新して`AGRace Tools`を検索・インストールし、有効にします。<br>
<br>
PCにzipを保持したい場合は [こちらからダウンロード](https://lubin851.github.io/AGRaceBlenderSample/download.html?file=addon) してZIPを展開せずに保存し、<br>
`編集 > プリファレンス > エクステンションを入手`の右上メニューから`ディスクからインストール`で指定します。ZIPのドラッグ＆ドロップでも導入できます。<br>
ただし、この方法はローカルインストールになり、上記リポジトリからの更新対象にはなりません。<br>
<br>
To use the download and update notification features within Blender, go to **Repositories** under<br>
`Edit > Preferences > Get Extensions`,click **+ (Add Remote Repository)**, and copy and paste the following URL.<br>
<br>
`https://lubin851.github.io/AGRaceBlenderSample/index.json`<br>
<br>
Refresh the list, search for and install `AGRace Tools`, and enable it.<br>
If you wish to save the ZIP file to your PC, [download it here](https://lubin851.github.io/AGRaceBlenderSample/download.html?file=addon) and save it without extracting it.<br>
<br>
Then, select `Install from Disk` via the menu in the top-right corner of `Edit > Preferences > Get Extensions`. You can also install it by simply dragging and dropping the ZIP file.<br>
Note, however, that this method results in a local installation and will not receive updates from the repository mentioned above.<br>

### Y軸スムーズ接続の簡単な使い方 / Simple Guide to Y-Axis Smooth Connection

このツールは形状が違う離れた辺同士を滑らか繋ぐ面を生成します。別オブジェクトで生成します。
1. 同じオブジェクトに繋ぎたいコースの断面の辺を配置します。配置はY軸方向に任意の距離で離して配置します。
2. +X軸方向のみの辺を残します。ミラー用にX軸の座標0に頂点があるようにします。
3. X座標が０の頂点が+Y軸にあると上面扱い、-Y軸にあると下面扱いになります。両方置いて同時生成も可能です。
4. 頂点数を同じにします。レイキャスト受けがある場合は辺の長さを変えないよう注意してください。
5. 接続する2本の辺の頂点を選択します。
6. `AGRace Tools > Y軸スムーズ接続`で分割数などを調整し、`スムーズ接続を生成（別OBJ）`を押します。Xミラーモディファイア付きのメッシュが生成されます。<br>
<br>
This tool generates a surface that smoothly connects two separate edges with different shapes. The result is created as a separate object.<br>

1. Place the cross-section edges you wish to connect within the same object, separated by an arbitrary distance along the Y-axis.
2. Retain only the edges located in the positive X-axis direction. Ensure there is a vertex at X=0 to facilitate mirroring.
3. A vertex at X=0 on the positive Y-axis is treated as the top surface, while one on the negative Y-axis is treated as the bottom surface. You can place both and generate them simultaneously.
4. Ensure the vertex counts match. If there is a raycast target, be careful not to alter the edge lengths.
5. Select the vertices of the two edges to be connected.
6. Go to `AGRace Tools > Y-Axis Smooth Connection`, adjust settings such as the subdivision count, and click `Generate Smooth Connection (Separate OBJ)`. A mesh with an X-mirror modifier applied will be generated.

### 円柱スムーズ接続の簡単な使い方 / How to Easily Create Smooth Connections Between Cylinders

このツールは離れた辺または、円柱に沿った断面形状へ滑らかに繋ぐ面を生成します。別オブジェクトで生成します。
1. 任意の辺から接続する場合は、前述のY軸スムーズと同様に辺を配置します。配置した辺から+Y方向へ生成されます。上下面同時可能です。
2. 生成したい頂点を選択します。
3. 半円（任意の円弧） → 円の生成をする場合はツールからそのまま設定を行います。
4. `AGRace Tools > 円柱スムーズ接続`で生成タイプ、Y方向の長さ、半径などを設定し、`円柱スムーズ接続を生成（別OBJ）`を押します。Xミラーモディファイア付きのメッシュが生成されます。<br>
<br>
This tool generates a connecting surface between separated edges or extending from an edge to a cylindrical cross-section. The result is created as a separate object.<br>

1. To connect from a specific edge, position the edge in the same manner as the previously mentioned "Y-Axis Smooth" function. The surface is generated in the +Y direction from the placed edge; generation on both the top and bottom surfaces is possible.
2. Select the target vertex.
3. Configure settings directly within the tool if you wish to generate a shape transitioning from a semicircle (or arbitrary arc) to a full circle.
4. Go to `AGRace Tools > Cylinder Smooth Connection`, configure parameters such as the generation type, Y-axis length, and radius, then click `Generate Cylinder Smooth Connection (Separate OBJ)`. A mesh with an X-Mirror modifier applied will be generated.


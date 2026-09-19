# AGRaceSDK 用コースモデルサンプル
AGRace の配布コースサンプルです。<br>
Blender のサンプルとアドオンを公開しています。<br>
<img width="434" height="252" alt="image" src="https://github.com/user-attachments/assets/2b193a55-a324-4629-8579-5560eb5a1e6f" />

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
1. 配布された`agrace_tools-0.3.0.zip`を展開しないで保存します。
2. Blenderで`Edit > Preferences > Extensions`を開きます。
※zipをD&Dでもインポート可
3. 右上メニューから`Install from Disk`を選びます。
4. ZIPを指定し、`AGRace Tools`を有効にします。
5. 3D Viewportで`N`を押し、`AGRace Tools`タブを開きます。<br>

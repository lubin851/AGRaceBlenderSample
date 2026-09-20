[The English manual is available after the Japanese version.](#english-manual)

# AGRace Tools

AGRace Toolsは、AGRaceSDKのコース制作を支援するために開発されたBlender Extensionです。AGRaceSDK本体には同梱せず、作者が案内する公開配布経路からサポートツールとして提供します。AGRaceSDK以外の用途にも使用できます。

- 対応Blender: 5.0以降
- 検証環境: Blender 5.1.1
- 配布形式: Blender Extension ZIP
- UI: 3D ViewportのNパネル → `AGRace Tools`
- 更新: リモートリポジトリ経由で確認・適用可能（適用は利用者操作）

## インストール

Blender内で更新したい場合は、`編集 > プリファレンス > エクステンションを入手`のリポジトリ設定から`リポジトリ`を選び、次のURLを登録します。

`https://lubin851.github.io/AGRaceBlenderSample/index.json`

リモートの一覧を更新して`AGRace Tools`を検索・インストールし、有効にします。3D Viewportで`N`を押すと`AGRace Tools`タブが開きます。

ZIPを直接使う場合は、[最新版ZIP](https://lubin851.github.io/AGRaceBlenderSample/download.html?file=addon)を展開せず保存し、右上メニューの`Install from Disk`で指定します。ZIPファイルをBlenderウィンドウへドラッグ＆ドロップしてもインストールできます。

`ディスクからインストール`はローカルリポジトリへの導入です。この方法で入れたものはリモートリポジトリからの更新対象になりません。

## 更新

リモートリポジトリから導入した場合は、`エクステンションを入手`でリモートの一覧を更新し、更新版が表示されたら利用者が適用します。起動時の更新確認はリポジトリ設定で任意に有効化できますが、更新版のインストールは利用者が行います。作業中の`.blend`は更新前に保存してください。

`ディスクからインストール`で導入した場合は、配布元から新しいZIPをダウンロードして手動で入れ直します。同じExtension IDの更新・置換確認が出た場合は内容を確認して承認します。UIが古いままなら無効・有効を切り替えるかBlenderを再起動してください。更新として受け付けられない場合は、旧版を無効化して削除し、新しいZIPをインストールします。

現在は保存対象となる独自のExtension設定を持たないため、削除して再導入してもツール設定の移行は不要です。

## Y軸スムーズ接続

異なる形の2本の断面を、同じ頂点数同士で滑らかに接続します。ローカルY軸方向の接続に特化したツールであり、任意軸対応の一般的なBridgeツールではありません。

### 使用方法

1. 接続したい2種類の断面となる辺を、それぞれ用意します。
   使用不可：円のように閉じたループ、途中で途切れた辺、分岐した辺
2. 2つの辺を同じMeshオブジェクト内に置き、ローカルY軸方向に離して配置します。
   例：平面側をY=-20、半円側をY=+20
3. 頂点数が少ない側の辺を、もう一方の辺に向かって押し出し、新しい辺を作ります。
4. 新しく作った辺を細分化し、もう一方の辺と頂点数を同じにします。
5. 接続に使用する2本の辺だけを同時に選択します。
6. 「Y軸スムーズ接続」の設定で、分割数と外側への膨らみを調整します。
7. 「スムーズ接続を生成（別OBJ）」を押します。

結果は元Meshを直接延長せず、元オブジェクトと同じTransformを持つ別オブジェクト`SmoothTransition`として生成されます。生成先は円柱スムーズ接続と同じ方式で、元オブジェクトが所属するCollectionを優先します。必要に応じてJoin、Merge、法線確認を行ってください。

各選択辺のローカルX=0頂点を上下判定の基準にします。2本とも+Z側なら生成面の法線を+Zへ、2本とも-Z側なら-Zへ向けます。X=0頂点がZ=0付近にある場合や、2本の上下が一致しない場合は生成を中止します。

上下を同時生成する場合は、上側2本と下側2本の計4本を選択します。ローカルX=0頂点のZ符号で自動分類し、上面と下面を同じ`SmoothTransition`オブジェクトへ生成します。上下をつなぐ側面や断面は追加しません。上下のUVは同じカテゴリ帯へ重ねます。

`最外面をレイキャスト受けとして扱う`を有効にすると、ローカル+X側の一番外側と外から2番目の頂点列の間にある既存面をレイキャスト受けとして扱います。特殊頂点や追加面は生成しません。`UVを生成`が有効な場合、通常接続面をV=0.4～1.0、レイキャスト受けをV=0.2～0.4へ配置し、どちらもU=0～1を使用します。

`Y軸 フチに沿ったカーブ`パネルでは、一番外側または外から2番目の列にBezier Curveを生成できます。4本選択時は上側と下側を別Curveオブジェクトとして同時生成します。メッシュ生成結果は解析せず、現在のY軸スムーズ接続設定と選択辺から直接計算します。Tiltの法線は、生成列からX=0方向へ1列内側にある面だけを基準に求め、+90度の取付オフセットと±180度境界の連続化を行います。半円・円用の端点90度丸めは行いません。

### 設定

- `分割数`: ローカルY方向の分割数。初期値40、最小1。
- `外側への膨らみ`: 中腹をローカルX方向外側へ膨らませます。0～1を推奨します。
- `X中央への影響を抑える`: ローカルX=0付近への膨らみの影響を抑えます。
- `最外面をレイキャスト受けとして扱う`: 一番外側と外から2番目の頂点列の間にある既存面をレイキャスト受けとして分類します。
- `UVを生成`: 通常接続面とレイキャスト受けをAGRace用の固定UV帯へ配置します。

### 制限

- 同一Mesh内の、互いに離れた2本または4本の開いたエッジ列を対象とします。
- 非表示の辺は選択状態が残っていても入力として扱いません。
- 閉じたループ、分岐したエッジ列、頂点数が異なる組み合わせには対応しません。
- 進行方向はローカルY、左右はローカルX、高さはローカルZとして計算します。
- Yの小さい側を開始断面、Yの大きい側を終了断面として扱います。
- BulgeはローカルX=0を中心として計算します。
- 生成境界は元Meshへ自動溶接されません。
- 生成後に面の向きと法線を確認してください。

エラーはBlender画面、Nパネルの状態欄、System Consoleへ表示されます。`ST`で始まるコードは問い合わせ時の識別子です。

## 円柱スムーズ接続

ローカルY方向へ、任意の半幅断面、半円、完全な円を滑らかに接続します。ローカル+X側だけを生成し、結果へX Mirrorモディファイアを追加します。円柱の内面・外面と厚み、均等グリッドUV、任意の側面・断面を同時に生成できます。

### 生成タイプ

- `任意の辺 → 半円`: 選択した半幅の辺列を、Mirror後に半円または指定角度となる断面へ接続します。
- `任意の辺 → 円`: 選択した半幅の辺列から、仮想半円を通る1本の連続補間で完全な円へ接続します。
- `半円 → 円`: 原点のY=0にある半円または指定角度から、完全な円へ接続します。Meshや辺を選択していなくても生成できます。

### 任意の辺を使用する手順

1. MeshをEdit Modeにします。
2. ローカルXZ断面上に、X=0からローカル+X側へ伸びる分岐のない開いた辺列を用意します。
3. 片面だけ接続する場合は1本、内外両面を接続する場合は同じ頂点数の上辺と下辺を選択します。
4. 生成タイプ、Y方向の長さと分割数、接続先、半径、厚み、生成面を設定します。
5. `円柱スムーズ接続を生成（別OBJ）`を押します。

2本の辺列では、X=0端点のZ座標が高い方を上辺、低い方を下辺として判定します。生成先の半円と円は入力オブジェクトのローカル原点Z=0を基準とし、上辺を内円へ接続すると円中心を中点半径分+Z側へ、上辺を外円へ接続すると中点半径分-Z側へ配置します。厚み1mの場合、原点上の接続位置で上辺はZ=+0.5m、下辺はZ=-0.5mになります。

1本の辺列では、X=0端点がローカルZの正側なら上辺、負側なら下辺として扱います。上辺は上向き、下辺は下向きの法線を基準にし、下辺から外円は上オフセット、下辺から内円は下オフセットへ接続します。生成先の半円と円のZ位置は同じく入力オブジェクトのローカル原点を基準にします。端点がローカルZ=0付近にある場合は上下を判定できないため生成を中止します。

`半円 → 円`では、オブジェクトの選択状態やTransformにかかわらず、常にワールド原点とワールド軸を使用します。オブジェクトが選択されている場合は所属Collectionだけを生成先の基準にします。参照オブジェクトがない場合は、Outlinerで選択したCollectionを優先し、取得できなければScene Collectionへ生成します。

### 設定

- `Y方向の長さ`: 入力断面または原点からローカル+Yへ生成する距離。初期値80m。
- `Y方向の分割数`: Y方向へ生成する面の列数。`任意の辺 → 円`は最低2。
- `半幅の頂点数`: `半円 → 円`で生成するローカル+X側の頂点数。初期値31。任意辺を使う場合は選択辺から自動取得します。
- `任意の角度`: 有効にすると、`任意の辺 → 半円`の終端と`半円 → 円`の開始断面を10.0～180.0°の半幅側円弧へ変更します。初期値90.0°で、入力値自体を小数第1位へ丸めます。無効時は従来の90°です。180.0°は完全な円として扱います。`任意の辺 → 円`が途中で通る仮想半円は常に90°です。
- `半径`: 内側、中点、外側のどれを数値入力の基準とするか選択できます。円中心のオフセットには、算出した厚み中点の基準円を使用します。
- `厚み`: 初期値1m。内外両面では、入力厚みから指定厚みへ滑らかに収束します。
- `生成する面`: 両面、内側のみ、外側のみ。辺列が1本の場合は内円または外円の片面接続だけを選択できます。
- `側面を生成`: Mirrorで閉じられない境界の内外面を接続します。
- `断面を生成`: Y方向の開始端と終了端を閉じます。
- `UVを生成`: Y方向と断面頂点方向へ均等なグリッドUVを生成します。
- `最外面をレイキャスト受けとして扱う`: 通常部分の外から2番目・3番目を結ぶ辺の延長方向へ3mの特殊境界を生成します。半円または指定角度の断面では、指定角度に対する正確な接線のうち、基準円が上なら+Z側、下なら-Z側へ向かう方向へ3m延長します。90°では従来どおりローカル±Zへ垂直です。任意角度を含め、受け頂点がX=0へ到達した後はMirrorの反対側へ越えず、X=0へ収束します。

UVは全カテゴリで横方向を0～1まで使用し、上から通常接続面60%、レイキャスト受け最外面20%、側面10%、断面10%の固定帯へ配置します。同じカテゴリの内外面や開始・終了断面、およびX Mirror後の左右は同じ領域へ重ねます。MirrorモディファイアによるUV反転は行いません。

任意辺でレイキャスト受けを有効にする場合、選択辺列は特殊頂点を含め3頂点以上が必要です。入力側の最後の頂点を特殊頂点として保持し、以降は通常部分の最外辺方向から配置します。`半円 → 円`では指定した半幅頂点数に特殊頂点を追加生成します。円終端で消失する特殊面だけは三角面と幅0のUVへ収束します。任意角度180.0°の`半円 → 円`は開始・終了とも閉じた円になるため、レイキャスト受けの特殊面を生成しません。

### フチに沿ったカーブ

`フチに沿ったカーブ`パネルで円柱スムーズ接続と同じ形状設定を使用します。任意辺を使う生成タイプでは対象辺をEdit Modeで選択し、`半円 → 円`では辺を選択せずに実行できます。メッシュを先に生成する必要はありません。

- `生成対象`: 両側、内側、外側。存在しない面は生成しません。
- `参照する列`: 一番外側、または外から2番目。

内側と外側は別のBezier Curveオブジェクトとして生成されます。各カーブの原点はワールド原点に置かれ、ハンドルはY方向の辺列に沿うよう設定します。Tiltは生成列からX=0方向へ1列内側にある面のY方向接線と断面方向接線から求めた法線へ、カーブに沿わせるメッシュの上方向を面へ垂直にするための+90度を加え、前後の角度差が最小になるよう連続化します。半円の始点・終点と円の終点では、既存仕様どおり推定した面角度を最も近い90度単位へ丸めてから同じ+90度を加えます。カーブへMirrorモディファイアは追加しません。連続生成時は生成前の基準OBJを維持し、生成済みカーブを次回の基準には使用しません。

### 入力条件と制限

- 任意断面は半幅入力だけに対応します。ローカル-X側を含む辺列は使用できません。
- 選択辺列は同じMesh内、同じローカルXZ断面上に置きます。辺列内のローカルY座標差は1cmまで許容し、生成開始列では入力頂点の座標を保持します。
- 非表示の辺は選択状態が残っていても入力として扱いません。
- 閉じたループ、分岐、X=0端点がない辺列には対応しません。
- 2本の辺列は頂点数を同じにします。
- 円中心から見た隣接頂点の角度順が補間中に反転する断面は生成を中止します。個々の頂点が補間中にわずかに戻っても、隣接順を維持する場合は生成できます。
- 入力頂点は目標半円・円の内側または外側のどちらから開始しても構いません。生成途中では開始した側を保ちながら目標半径へ近づき、終端で一致する必要があります。途中で目標半径を越える場合や、一度近づいた後に遠ざかる場合は生成を中止します。
- 負または0のObject Scale、せん断を含むTransformには対応しません。正の非一様Scaleは生成頂点へ焼き込み、出力ObjectはScale 1になります。
- 生成結果は別Objectです。入力Meshは変更しません。
- フチカーブは円柱メッシュと同じ形状計算を直接使用します。生成済みメッシュやFBXの構造解析には依存しません。

エラーはBlender画面、Nパネルの状態欄、System Consoleへ表示されます。`CT`で始まるコードは問い合わせ時の識別子です。

## オブジェクトリネーマー

Object Modeで選択した1つ以上のオブジェクト名を一括編集します。`非表示の選択オブジェクトを含める`が無効の場合、現在のView Layerで非表示のオブジェクトを除外します。有効の場合は、選択状態が維持されている非表示オブジェクトも対象に含めます。

### 入力名で連番リネーム

実行前に取得したScene Collectionのオブジェクト順で、先頭へ入力した基本名をそのまま割り当て、次からBlender標準の`.001`、`.002`形式を割り当てます。選択外オブジェクトが基本名や連番名を使用している場合はBlender標準の空き番号へ進み、スキップした内容をSystem Consoleへ表示します。これは処理順の固定であり、Outlinerの名前順ソート自体は変更しません。

`連番を振り直し`は、末尾のBlender形式のピリオドと3桁以上の数字（`.001`など）を取り除いた基本名と、番号なしの同名オブジェクトを同じグループとして扱います。基本名ごとに、事前取得したScene Collection順で番号なし、`.001`、`.002`の順へ振り直します。たとえば`Oval_A_A_Co_Gr`と`Oval_A_A_Co_Gr.003`は同じグループです。`Road_001`や`Route66`の末尾数字は削除せず、名前全体を基本名として扱います。単体選択でも有効で、選択外が候補名を使用している場合は空き番号へ進みます。

### テキストの追加／削除

- `先頭へ追加`: 入力テキストを、選択した各オブジェクト名の先頭へそのまま追加します。すでに同じテキストで始まっている場合も追加します。
- `末尾に追加`: 入力テキストを、選択した各オブジェクト名の末尾へそのまま追加します。すでに同じテキストで終わっている場合も追加します。
- `一致する単語を削除`: 入力テキストと大文字・小文字まで完全一致する部分を、各オブジェクト名のどこからでもすべて削除します。削除結果が空になるオブジェクトは変更しません。

名前衝突時はBlender標準の連番を使用します。実行後も選択状態とアクティブオブジェクトを維持し、各操作はUndoに対応します。空の入力、Object Mode以外、対象オブジェクトがない場合は実行しません。

## Mesh／Curveデータ名の同期

Scene Collection以下にあるMeshおよび通常Curveについて、安全に変更できるデータ名をオブジェクト名へ揃えます。

### 使用方法

1. `変更内容を確認`で変更予定と除外理由を確認します。この操作では名前を変更しません。
2. 内容を確認します。
3. `安全に名前を同期`で安全判定を通過したデータだけを変更します。

次のデータは変更しません。

- 複数オブジェクトから共有されているデータ
- 外部ライブラリ、Library Override、編集不可データ
- 同じ最終名を複数データが要求する場合
- 改名対象外のデータが希望名を使用中の場合
- 既にオブジェクト名と同名の場合

名前交換や循環は、一時的な固有名を介して二段階で処理します。変更OperatorはBlenderのUndoに対応します。

詳細な診断情報と識別コードは、必要に応じてSystem Consoleにも記録されます。

## ライセンスと生成物

AGRace Toolsのソースコードならびに同梱の`README.md`および`NOTICE.md`は、GNU General Public License version 3またはそれ以降の条件で提供されます。正式な条件は同梱の`LICENSE.txt`を参照してください。`README.md`および`NOTICE.md`の説明とGNU GPL本文が異なる場合は、GNU GPL本文が優先します。

本アドオンで作成または加工したメッシュ、カーブ、UVその他の生成物は、商用・非商用を問わず自由に利用、改変、販売および配布できます。本アドオンの著作権表示は生成物には要求されません。

この許諾は、入力データや第三者の著作物に適用される権利を変更するものではありません。著作権、開発過程、改変版の表示に関する詳細は`NOTICE.md`を参照してください。

## 開発表示

- 開発・著作権者: 尾黒こう（Ryuban）
- 開発支援: OpenAI Codex

本アドオンは、尾黒こう（Ryuban）の仕様決定・指示・確認のもと、OpenAI Codexによるコード生成および開発支援を利用して制作されました。

## Language

UIはBlender本体の言語設定へ追従します。英語を基準文字列とし、日本語翻訳を同梱しています。独自の言語切替設定はありません。

## 配布者向け

Extensionソースのルートで、Blender 5.0以降のコマンドを使って検査・ビルドできます。

```text
blender --command extension validate
blender --command extension build
```

公開時はManifestの`version`を更新し、一致する`vX.Y.Z`タグを付けます。ActionはManifestとタグの一致を検査し、版付きZIPをビルドします。互換性を実機確認するまでは`blender_version_min = "5.0.0"`を維持してください。

# English Manual

AGRace Tools is a Blender Extension developed to support AGRaceSDK course authoring. It is not bundled with AGRaceSDK and is provided separately as a support tool through public distribution channels announced by the author. It may also be used for purposes other than AGRaceSDK.

- Supported Blender versions: 5.0 or later
- Verified with: Blender 5.1.1
- Distribution format: Blender Extension ZIP
- UI: 3D Viewport Sidebar (`N`) → `AGRace Tools`
- Updates: Available through the remote repository (installation requires user action)

## Installation

For updates within Blender, open `Edit > Preferences > Get Extensions`, choose `Add Remote Repository` in the repository settings, and register this URL:

`https://lubin851.github.io/AGRaceBlenderSample/index.json`

Refresh the remote listing, search for and install `AGRace Tools`, and enable it. Press `N` in the 3D Viewport to open the `AGRace Tools` tab.

For a direct ZIP installation, save the [latest ZIP](https://lubin851.github.io/AGRaceBlenderSample/download.html?file=addon) without extracting it, then choose `Install from Disk` from the upper-right menu. You can also drag and drop the ZIP into Blender.

`Install from Disk` installs into a local repository. Extensions installed this way do not receive updates from the remote repository.

## Updates

For installations from the remote repository, refresh the listing under `Get Extensions` and apply an available update. Checking for updates at Blender startup is optional in the repository settings; installing an update remains a user action. Save any open `.blend` file before updating.

For an `Install from Disk` installation, download the new ZIP and install it manually. Review and accept the update or replacement prompt for the same Extension ID if one appears. If the UI remains unchanged, disable and re-enable the extension or restart Blender. If Blender does not accept it as an update, disable and remove the old version before installing the new ZIP.

The extension currently has no custom settings that need to be preserved, so no tool-setting migration is required after removal and reinstallation.

## Y-Axis Smooth Transition

This tool smoothly connects two differently shaped sections with matching vertex counts. It is specialized for connections along the local Y axis and is not a general-purpose Bridge tool for arbitrary axes.

### Instructions

1. Prepare the two edge chains that define the sections to connect.
   Closed loops such as circles, interrupted chains, and branched chains cannot be used.
2. Place both edge chains in the same Mesh object and separate them along the local Y axis.
   Example: place the flat side at Y=-20 and the semicircular side at Y=+20.
3. Extrude the edge chain with fewer vertices toward the other chain to create a new edge chain.
4. Subdivide the new chain until both chains have the same vertex count.
5. Select only the two edge chains used for the connection.
6. Under `Y-Axis Smooth Transition`, adjust `Ring Count` and `Outward Bulge`.
7. Press `Generate Smooth Transition (Separate Object)`.

Instead of extending the source Mesh directly, the result is generated as a separate object named `SmoothTransition` with the same transform as the source object. Its destination follows the same rules as Cylinder Smooth Transition and prioritizes a Collection containing the source object. Join or merge the result and inspect its face orientation and normals as needed.

The local X=0 vertex of each selected chain is used to determine whether the surface is upper or lower. If both are on the +Z side, generated normals face +Z. If both are on the -Z side, generated normals face -Z. Generation stops when an X=0 vertex is near Z=0 or when the two chains do not agree on the upper/lower side.

To generate upper and lower surfaces together, select four chains: two upper and two lower. They are classified automatically by the Z sign of their local X=0 vertices and generated in the same `SmoothTransition` object. No side faces or end sections are added between the upper and lower surfaces. Their UVs overlap within the same category bands.

When `Treat Outermost Face as Raycast Receiver` is enabled, the existing faces between the outermost and second-outermost vertex rows on the local +X side are classified as raycast receivers. No special vertices or additional faces are generated. When `Generate UV` is enabled, regular connection faces use V=0.4–1.0, raycast receiver faces use V=0.2–0.4, and both use U=0–1.

The `Y-Axis Edge Curve` panel can generate a Bezier Curve on either the outermost or second-outermost row. With four selected chains, the upper and lower curves are generated simultaneously as separate Curve objects. The calculation uses the current Y-Axis Smooth Transition settings and selected chains directly; it does not analyze a generated mesh. Tilt normals are calculated only from the face one row inward toward X=0 from the generated curve row. A common +90-degree attachment offset and continuous unwrapping across the ±180-degree boundary are applied. The endpoint 90-degree snapping used for semicircles and circles is not applied.

### Settings

- `Ring Count`: Number of divisions along local Y. Default 40; minimum 1.
- `Outward Bulge`: Adds outward curvature around the middle along local X. Values from 0 to 1 are recommended.
- `Reduce Center Influence`: Reduces the bulge influence near local X=0.
- `Treat Outermost Face as Raycast Receiver`: Classifies the existing faces between the outermost and second-outermost vertex rows as raycast receivers.
- `Generate UV`: Places regular connection faces and raycast receivers in fixed AGRace UV bands.

### Limitations

- Operates on two or four separate open edge chains in the same Mesh.
- Hidden edges are not treated as input even if their selection state remains set.
- Closed loops, branched chains, and pairs with different vertex counts are not supported.
- Local Y is the travel direction, local X is left/right, and local Z is height.
- The section with the lower Y coordinate is the start; the section with the higher Y coordinate is the end.
- Bulge is calculated around local X=0.
- Generated boundaries are not welded automatically to the source Mesh.
- Inspect face orientation and normals after generation.

Errors are shown in Blender, in the N-panel status area, and in the System Console. Codes beginning with `ST` are identifiers for support inquiries.

## Cylinder Smooth Transition

This tool smoothly connects an arbitrary half-width section, a semicircle, and a full circle along local Y. It generates only the local +X half and adds an X Mirror modifier to the result. Inner and outer cylinder surfaces, thickness, uniform-grid UVs, and optional side faces and end sections can be generated together.

### Generation Types

- `Edge to Semicircle`: Connects selected half-width edge chains to a section that becomes a semicircle or the specified angle after mirroring.
- `Edge to Circle`: Connects selected half-width edge chains to a full circle with one continuous interpolation passing through a virtual semicircle.
- `Semicircle to Circle`: Connects a semicircle or specified angle at Y=0 around the origin to a full circle. It can run without selecting a Mesh or edge chain.

### Instructions for Arbitrary Edges

1. Enter Edit Mode on a Mesh.
2. On a local XZ section, prepare an unbranched open edge chain extending from X=0 toward local +X.
3. Select one chain for a single-surface connection, or select matching upper and lower chains with equal vertex counts for both inner and outer surfaces.
4. Configure the generation type, Y length and divisions, connection, radius, thickness, and surfaces.
5. Press `Generate Cylinder Transition (Separate Object)`.

With two edge chains, the chain whose X=0 endpoint has the higher Z coordinate is treated as the upper edge and the other as the lower edge. The target semicircle and circle use local Z=0 of the input object as their reference. Connecting the upper edge to the inner circle places the circle center one midpoint-radius toward +Z; connecting it to the outer circle places the center one midpoint-radius toward -Z. With a thickness of 1 m, the connection positions at the origin are Z=+0.5 m for the upper edge and Z=-0.5 m for the lower edge.

With one edge chain, an X=0 endpoint on positive local Z is treated as an upper edge and one on negative local Z as a lower edge. Upper edges use an upward normal reference and lower edges use a downward reference. A lower edge connected to the outer circle uses the upper offset, while a lower edge connected to the inner circle uses the lower offset. The target semicircle and circle also use the input object's local origin as their Z reference. Generation stops if the endpoint is near local Z=0 because the side cannot be determined.

For `Semicircle to Circle`, the world origin and world axes are always used regardless of object selection or transforms. When an object is selected, only its containing Collection is used as the destination reference. Without a reference object, the Collection selected in the Outliner is preferred; otherwise the result is placed in the Scene Collection.

### Settings

- `Y Length`: Distance generated along local +Y from the input section or origin. Default 80 m.
- `Y Divisions`: Number of face rows generated along Y. `Edge to Circle` requires at least 2.
- `Half-width Vertex Count`: Number of vertices generated on the local +X half for `Semicircle to Circle`. Default 31. Generation types using arbitrary edges derive the count from the selected chain.
- `Custom Angle`: When enabled, changes the endpoint of `Edge to Semicircle` and the starting section of `Semicircle to Circle` to a half-width arc from 10.0 to 180.0 degrees. The default is 90.0 degrees, and the stored input value itself is rounded to one decimal place. Disabled preserves the existing 90-degree semicircle. 180.0 degrees is treated as a full circle. The virtual semicircle used by `Edge to Circle` always remains 90 degrees.
- `Radius`: The entered value can represent the inner radius, thickness middle, or outer radius. The calculated thickness-middle reference circle is used to offset the circle center.
- `Thickness`: Default 1 m. When both surfaces are generated, the wall transitions smoothly from the input thickness to the specified thickness.
- `Surfaces`: Both, Inner Only, or Outer Only. With one selected chain, only a single connection to either the inner or outer circle can be selected.
- `Generate Sides`: Connects inner and outer surfaces at boundaries not closed by the Mirror modifier.
- `Generate End Sections`: Closes the start and end sections along Y.
- `Generate UV`: Generates a uniform-grid UV map along Y and the section vertices.
- `Treat Outermost Face as Raycast Receiver`: Generates a special boundary extending 3 m along the direction of the edge between the second- and third-outermost regular vertices. At a semicircle or custom-angle section, it extends along the exact tangent for the specified angle, choosing the +Z direction when the reference circle is above and the -Z direction when it is below. At 90 degrees this remains vertical along local ±Z. For custom angles as well as circles, once a receiver vertex reaches X=0 it stays on the Mirror seam instead of crossing to the opposite side.

All UV categories use the full horizontal range from 0 to 1. Vertically, fixed bands are arranged from top to bottom as 60% for regular connection faces, 20% for the outermost raycast receiver, 10% for side faces, and 10% for end sections. Inner and outer faces in the same category, start and end sections, and left and right sides after X Mirror may overlap. The Mirror modifier does not flip UVs.

When the raycast receiver is enabled with arbitrary input edges, each selected chain needs at least three vertices including the special vertex. The final input vertex is retained as the special vertex, and later rows position it from the direction of the outermost regular edge. For `Semicircle to Circle`, a special vertex is added to the specified half-width vertex count. Only the special face that disappears at the circle endpoint converges to a triangle and zero-width UVs. At a custom angle of 180.0 degrees, `Semicircle to Circle` starts and ends with a closed circle, so no special raycast-receiver face is generated.

### Cylinder Edge Curve

The `Cylinder Edge Curve` panel uses the same shape settings as Cylinder Smooth Transition. Generation types using arbitrary edges require the target chains to be selected in Edit Mode. `Semicircle to Circle` can run without selecting edges. A mesh does not need to be generated first.

- `Curve Surfaces`: Both Sides, Inner, or Outer. Curves are not generated for surfaces that do not exist.
- `Reference Row`: Outermost or Second from Outermost.

The inner and outer paths are generated as separate Bezier Curve objects. Each curve has its origin at the world origin, and its handles follow the edge rows in the Y direction. Tilt uses the normal calculated from the Y-direction and section-direction tangents of the face one row inward toward X=0 from the generated curve row. A common +90-degree attachment offset makes the top of a mesh placed along the curve perpendicular to the surface, and equivalent angles are chosen to minimize changes between adjacent Tilt values. At the start and end of a semicircle and at the end of a circle, the estimated surface angle is rounded to the nearest 90 degrees before applying the same +90-degree offset, preserving the existing endpoint behavior. No Mirror modifier is added to curves. Repeated generation retains the reference object used before generation and does not use a previously generated curve as the next reference.

### Input Requirements and Limitations

- Arbitrary sections accept only half-width input. Chains containing the local -X side cannot be used.
- Selected chains must be in the same Mesh and on the same local XZ section. A local-Y difference of up to 1 cm within each chain is accepted, and the input vertex coordinates are preserved in the generated start row.
- Hidden edges are not treated as input even if their selection state remains set.
- Closed loops, branches, and chains without an X=0 endpoint are not supported.
- Two selected chains must have equal vertex counts.
- Generation stops if the angular order of adjacent vertices around the circle center reverses anywhere during interpolation. A small backward movement of an individual vertex is allowed when adjacent order is preserved.
- Input vertices may start either inside or outside the target semicircle or circle. During generation, each vertex must remain on its starting side while approaching the target radius and meet it at the endpoint. Generation stops if a vertex crosses the target radius early or moves away after getting closer.
- Negative or zero Object Scale and transforms containing shear are not supported. Positive non-uniform Scale is baked into generated vertices, and output objects use Scale 1.
- Results are generated as separate objects. The input Mesh is not modified.
- Edge curves use the same shape calculation as the cylinder mesh directly and do not depend on analyzing a generated mesh or FBX structure.

Errors are shown in Blender, in the N-panel status area, and in the System Console. Codes beginning with `CT` are identifiers for support inquiries.

## Object Renamer

Edits the names of one or more selected objects in Object Mode. When `Include Hidden Selected Objects` is disabled, objects hidden in the current View Layer are excluded. When enabled, hidden objects whose selection state is retained are included.

### Sequential Rename

Captures the Scene Collection object order before renaming. The first object receives the entered base name without a suffix, followed by Blender's standard `.001`, `.002`, and later suffixes. If an unselected object occupies the base name or a numbered name, Blender advances to an available number and the skipped collision is reported in the System Console. This fixes the processing order; it does not change the Outliner's name-based sorting.

`Renumber Sequential Numbers` groups names after removing a final Blender-style period followed by three or more digits, such as `.001`, together with an unsuffixed object of the same base name. Each group is renamed in the captured Scene Collection order to the unsuffixed name, `.001`, `.002`, and so on. For example, `Oval_A_A_Co_Gr` and `Oval_A_A_Co_Gr.003` belong to the same group. The digits in `Road_001` or `Route66` are preserved and the entire name is treated as a base name. Single-object selections are supported. Names occupied by objects outside the operation are skipped.

### Add / Remove Text

- `Add to Beginning`: Adds the entered text directly to the beginning of every selected object name. It is added again even when the name already begins with the same text.
- `Add to End`: Adds the entered text directly to the end of every selected object name. It is added again even when the name already ends with the same text.
- `Remove Matching Text`: Removes every case-sensitive exact occurrence of the entered text from anywhere in each selected object name. An object is left unchanged if removal would produce an empty name.

Name collisions use Blender's standard numeric suffixes. Selection and the active object are preserved, and every operation supports Undo. Empty input, modes other than Object Mode, and an empty target selection do not run.

## Mesh / Curve Data Name Sync

For Mesh and regular Curve data under the Scene Collection, this tool aligns safely editable data names with their object names.

### Instructions

1. Run `Analyze Changes` to review planned changes and exclusion reasons. This operation does not rename anything.
2. Review the results.
3. Run `Safely Sync Names` to rename only data that passes the safety checks.

The following data is not changed:

- Data shared by multiple objects
- External libraries, Library Overrides, and non-editable data
- Multiple data-blocks requesting the same final name
- A requested name already used by data outside the rename set
- Data already matching its object name

Name swaps and cycles are processed in two stages through temporary unique names. The rename Operator supports Blender Undo.

Detailed diagnostics and identification codes are also written to the System Console when needed.

## License and Generated Output

The AGRace Tools source code and the included `README.md` and `NOTICE.md` are provided under the GNU General Public License, version 3 or later. See the included `LICENSE.txt` for the official terms. If descriptions in `README.md` or `NOTICE.md` differ from the GNU GPL, the GNU GPL takes precedence.

Meshes, curves, UVs, and other output created or processed with this add-on may be freely used, modified, sold, and distributed for commercial or non-commercial purposes. The add-on copyright notice is not required on generated output.

This permission does not alter rights that apply to input data or third-party works. See `NOTICE.md` for details about copyright, the development process, and source and modified-version identification.

## Development Disclosure

- Developer and copyright holder: 尾黒こう (Ryuban)
- Development assistance: OpenAI Codex

This add-on was produced using code generation and development assistance from OpenAI Codex under the specifications, direction, and review of 尾黒こう (Ryuban).

## Language

The UI follows Blender's language setting. English is used as the source language, and a Japanese translation is included. The add-on has no separate language selector.

## For Distributors

From the extension source root, use Blender 5.0 or later to validate and build the extension:

```text
blender --command extension validate
blender --command extension build
```

When publishing a release, update the Manifest `version` and create a matching `vX.Y.Z` tag. The Action checks that they match and builds the versioned ZIP. Keep `blender_version_min = "5.0.0"` until compatibility with a later minimum requirement has been verified in Blender.

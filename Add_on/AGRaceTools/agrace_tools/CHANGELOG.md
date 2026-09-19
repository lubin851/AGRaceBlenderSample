[The English changelog is available after the Japanese version.](#english-changelog)

# Changelog

## 0.3.0 - 2026-09-19

- 0.2.14と同じ機能を、最初の公開版0.3.0としてリリースします。
- アドオンの機能、UI、初期値および生成結果は0.2.14から変更していません。

## 0.2.14 - 2026-09-18

- 179°などの任意角度で正確な接線がMirrorの反対側へ達する場合、レイキャスト受けをX=0で停止し、以降もMirror継ぎ目へ固定するよう修正しました。
- `任意の角度`のサイドバーとOperatorの数値を、表示だけでなく保存値自体も入力直後に小数第1位へ丸めるよう変更しました。
- 45°・90°の接線、180°の円処理、任意角度形状、フチカーブおよびその他の既存仕様は変更していません。

## 0.2.13 - 2026-09-18

- `任意の辺 → 半円`の終端と`半円 → 円`の開始断面へ、10.0～180.0°を小数第1位で指定できる`任意の角度`設定を追加しました。無効時と90.0°は従来の半円を維持し、180.0°は完全な円として処理します。
- 指定角度のレイキャスト受けを、分割辺の近似方向ではなく円弧に対する正確な3mの接線方向へ生成します。上側は+Z方向、下側は-Z方向を選び、90°では従来の垂直方向と一致します。
- 円柱メッシュとフチカーブで設定を共有します。`任意の辺 → 円`が通る仮想半円は従来どおり90°です。

## 0.2.12 - 2026-09-06

- 任意辺の開始頂点が目標半円・円の内側にある場合も生成できるよう、CT026の開始位置制限を片側収束検査へ変更しました。
- 各頂点が開始した内側または外側を保ちながら目標半径へ近づくことを検査し、途中で目標半径を越える場合や、一度近づいた後に遠ざかる場合は生成を中止します。
- 内外2面では内面・外面をそれぞれの目標半径に対して検査します。頂点順、面積、重なりおよび既存の終端位置は変更していません。

## 0.2.11 - 2026-09-06

- `任意の辺 → 半円`と`任意の辺 → 円`の終端Z位置を、入力辺の接続位置ではなく入力オブジェクトのローカル原点Z=0基準へ統一しました。
- `半円 → 円`は選択オブジェクトのTransformを使用せず、常にワールド原点とワールド軸を基準に生成するよう変更しました。選択オブジェクトの所属Collectionを生成先に使用する動作は維持しています。
- Y方向の長さ、半径・厚み、接続方向、UIおよびその他の生成仕様は変更していません。

## 0.2.10 - 2026-09-06

- `任意の辺 → 円`の仮想半円を経由する補間で、個々の頂点がわずかに戻るだけの有効な断面をCT035で拒否していた判定を修正しました。
- 補間区間全体で隣接頂点の角度順を解析し、実際に順序が反転する断面では引き続きCT035で生成を中止します。
- CT036、半径、面積および既存の形状検査は維持しています。

## 0.2.9 - 2026-09-04

- 入力名での連番リネームを、番号なしの基本名、`.001`、`.002`の順に戻しました。
- 連番の振り直しでも番号なしの同名オブジェクトを同じ基本名グループへ含め、番号なしから再採番します。
- 選択外との衝突回避、改名前の処理順固定、非表示トグル、Undoおよび再描画は維持しています。Outlinerのソート設定は変更しません。

## 0.2.8 - 2026-09-03

- 選択オブジェクト名の末尾にあるBlender形式の`.001`などを検出し、基本名ごと・Scene Collection順に`.001`から振り直す機能を追加しました。
- Blender標準ではない`Road_001`や`Route66`のような末尾数字は変更しません。
- Blender標準翻訳との競合を避ける専用翻訳コンテキストを使用し、日本語UIの`末尾に追加`表記を固定しました。
- 既存の連番リネーム、テキスト追加／削除およびその他の機能は変更していません。

## 0.2.7 - 2026-09-03

- オブジェクトリネーマーへ、入力テキストを選択オブジェクト名の末尾へ追加する`末尾に追加`ボタンを追加しました。
- 末尾追加でも、既存の非表示選択トグル、名前衝突処理、Undo、選択状態維持および実行後の再描画を使用します。
- 既存の連番リネーム、先頭追加、一致テキスト削除およびその他の機能は変更していません。

## 0.2.6 - 2026-09-03

- オブジェクトの連番リネームを、連番なしの基本名ではなく`.001`から開始するよう変更しました。
- 選択外オブジェクトが連番を使用中の場合は、従来どおり空き番号までスキップしてSystem Consoleへ表示します。
- オブジェクト名変更後にNパネルやOutlinerの描画更新を明示的に要求し、マウスオーバーまで表示が更新されない問題を改善しました。
- 上記以外のオブジェクトリネーマーおよび既存機能の仕様は変更していません。

## 0.2.5 - 2026-09-03

- Object Modeで選択したオブジェクトを、Scene Collectionの事前取得順に同じ基本名とBlender標準の連番へ変更するオブジェクトリネーマーを追加しました。
- 選択外オブジェクトとの名前衝突で番号をスキップした場合、System Consoleへ内容を表示します。
- 選択オブジェクト名の先頭へのテキスト追加と、大文字・小文字を区別した完全一致テキストの全削除を追加しました。
- 非表示の選択オブジェクトを処理対象へ含めるか選べる共通トグルを追加しました。
- 既存のメッシュ生成、カーブ生成、UV、データ名同期機能は変更していません。

## 0.2.4 - 2026-09-03

- 円柱スムーズ接続の任意辺入力で、辺列内のローカルY座標差を1cmまで許容するようにしました。
- 円柱スムーズ接続とY軸スムーズ接続で、非表示の選択辺を入力対象から除外しました。
- 選択辺の配置や設定の修正方法が分かるよう、主なエラー表示とコンソール出力を直接的な日英文へ改善しました。
- 日本語UIで円柱スムーズ接続の`Thickness`がBlender標準翻訳により「幅」と表示される問題を修正し、「厚み」に統一しました。
- 英語UIの`Thickness`、既存の計算設定、初期値および生成仕様は維持しています。

## 0.2.3 - 2026-09-03

- READMEの日本語マニュアル全体に対応する完全な英語版を追加しました。
- NOTICEとCHANGELOGへ、それぞれ日本語全文に対応する英語版を追加しました。
- 各文書の先頭へ英語版への案内リンクを追加しました。
- アドオンのコード、機能、UI、初期値および生成仕様は0.2.2から変更していません。

## 0.2.2 - 2026-09-03

- 円柱スムーズ接続の`Y方向の長さ`の初期値を20mから80mへ変更しました。
- 円柱スムーズ接続の`半幅の頂点数`の初期値を17から31へ変更しました。
- 共通設定を使用する円柱のフチカーブにも同じ初期値が反映されます。
- READMEの日本語説明と英語ガイドへ新しい初期値を追記しました。
- 上記以外の機能、UIおよび生成仕様は0.2.1から変更していません。

## 0.2.1 - 2026-09-03

- AGRaceSDK向けに開発されたツールでありながら、用途を限定せず利用できることを明記しました。
- 生成物を商用・非商用を問わず自由に利用、改変、販売および配布できることを簡潔にしました。
- `AGRace Tools`の名称を識別および正しい出所説明に使用できることを明記しました。
- READMEおよびNOTICEのライセンス範囲と個人の公開配布経路について整理しました。
- アドオンのコード、機能、UIおよび生成結果は0.2.0から変更していません。

## 0.2.0 - 2026-09-02

- 著作権者、GNU GPL、生成物の利用条件、出所および改変版の表示を明文化しました。
- OpenAI Codexを利用したコード生成および開発支援について記載しました。
- `LICENSE.txt`、`NOTICE.md`、`CHANGELOG.md`を配布物へ追加しました。
- READMEの実装不一致と不足していた説明を修正しました。
- 全PythonソースへSPDX著作権・ライセンスヘッダーを追加しました。
- アドオンの機能、UIおよび生成結果は0.1.19から変更していません。

# English Changelog

## 0.3.0 - 2026-09-19

- Released the same functionality as 0.2.14 as the first public release, version 0.3.0.
- The add-on functionality, UI, default values, and generated results are unchanged from 0.2.14.

## 0.2.14 - 2026-09-18

- Fixed raycast receivers at custom angles such as 179 degrees so an exact tangent stops at X=0 and remains on the Mirror seam instead of extending to the opposite side.
- Changed the sidebar and Operator `Custom Angle` fields so the stored value itself, not only its display, is rounded to one decimal place immediately after input.
- The 45- and 90-degree tangents, 180-degree circle handling, custom-angle geometry, edge curves, and all other existing behavior are unchanged.

## 0.2.13 - 2026-09-18

- Added a `Custom Angle` setting from 10.0 to 180.0 degrees with one-decimal precision for the endpoint of `Edge to Semicircle` and the starting section of `Semicircle to Circle`. Disabled and 90.0 degrees preserve the existing semicircle, while 180.0 degrees is processed as a full circle.
- Raycast receivers at custom-angle sections now use an exact 3 m tangent calculated from the arc angle instead of an adjacent-edge approximation. The tangent points toward +Z for an upper reference circle and -Z for a lower one, matching the existing vertical direction at 90 degrees.
- Cylinder meshes and edge curves share the setting. The virtual semicircle used by `Edge to Circle` remains fixed at 90 degrees.

## 0.2.12 - 2026-09-06

- Replaced the CT026 starting-position restriction with a one-sided convergence check so arbitrary input vertices may start inside the target semicircle or circle.
- Each vertex must approach the target radius while remaining on its starting side. Generation stops if it crosses the target radius early or moves away after getting closer.
- For paired surfaces, the inner and outer surfaces are checked against their respective target radii. Vertex order, face area, overlap checks, and the existing endpoint positions are unchanged.

## 0.2.11 - 2026-09-06

- Standardized the target Z position of `Edge to Semicircle` and `Edge to Circle` on local Z=0 of the input object instead of the selected edge connection position.
- `Semicircle to Circle` now always uses the world origin and world axes without applying the selected object's transform. The selected object's containing Collection is still used as the destination.
- Y length, radius and thickness, connection direction, UI, and all other generation behavior are unchanged.

## 0.2.10 - 2026-09-06

- Fixed CT035 incorrectly rejecting valid `Arbitrary Edge to Circle` sections when an individual vertex moved slightly backward during interpolation through the virtual semicircle.
- The operation now analyzes adjacent-vertex angular order over the complete interpolation interval and still stops with CT035 when that order actually reverses.
- CT036, radius, face-area, and existing geometry checks remain in place.

## 0.2.9 - 2026-09-04

- Restored sequential renaming to the unsuffixed base name, followed by `.001`, `.002`, and so on.
- Renumbering now includes the unsuffixed object in the same base-name group and starts with the unsuffixed name.
- Preserved collision avoidance, the captured processing order, hidden-selection filtering, Undo, and redraw. Outliner sorting settings are unchanged.

## 0.2.8 - 2026-09-03

- Added an operation that detects Blender-style numeric endings such as `.001` and renumbers each base-name group from `.001` in Scene Collection order.
- Non-standard numeric endings such as `Road_001` and `Route66` are not changed.
- Used the AGRace Tools translation context for `Add to End` so the intended Japanese `末尾に追加` label is not replaced by Blender's built-in translation.
- Existing sequential rename, text addition/removal, and all other features are unchanged.

## 0.2.7 - 2026-09-03

- Added an `Add to End` button that appends the entered text to selected object names.
- Appending uses the existing hidden-selection toggle, name-collision handling, Undo support, selection preservation, and post-operation redraw.
- Existing sequential rename, prepend, matching-text removal, and all other features are unchanged.

## 0.2.6 - 2026-09-03

- Changed sequential object renaming to begin at `.001` instead of creating an unsuffixed base name.
- When an unselected object already uses a numeric name, the operation continues to skip to an available number and reports the collision in the System Console.
- Explicitly requests redraws for the N-panel and Outliner after object-name operations, improving cases where the display did not update until mouse-over.
- All other Object Renamer and existing feature behavior remains unchanged.

## 0.2.5 - 2026-09-03

- Added an Object Renamer that renames selected objects in Object Mode to a common base name and Blender numeric suffixes using the Scene Collection order captured before renaming.
- Reports skipped numeric names in the System Console when they collide with unselected objects.
- Added operations to prepend text to selected object names and remove every case-sensitive exact occurrence of entered text.
- Added a shared toggle that controls whether hidden selected objects are included.
- Existing mesh generation, curve generation, UV, and data-name synchronization features are unchanged.

## 0.2.4 - 2026-09-03

- Allowed up to 1 cm of local-Y variation within arbitrary input edge chains for Cylinder Smooth Transition.
- Excluded hidden selected edges from the input of Cylinder Smooth Transition and Y-Axis Smooth Transition.
- Reworded the main Blender error messages and console output in Japanese and English so they directly explain how to correct the selected edges or settings.
- Fixed the Japanese UI label for Cylinder Smooth Transition `Thickness`, which Blender's built-in translation displayed as `Width`, and standardized it as `厚み`.
- Preserved the English `Thickness` label, existing calculation settings, default values, and generation behavior.

## 0.2.3 - 2026-09-03

- Added a complete English manual corresponding to the full Japanese manual in README.
- Added English versions of the complete Japanese NOTICE and CHANGELOG.
- Added a link to the English version at the beginning of each document.
- The add-on code, functionality, UI, default values, and generation behavior are unchanged from 0.2.2.

## 0.2.2 - 2026-09-03

- Changed the default `Y Length` for Cylinder Smooth Transition from 20 m to 80 m.
- Changed the default `Half-width Vertex Count` for Cylinder Smooth Transition from 17 to 31.
- The Cylinder Edge Curve uses the same updated defaults through the shared settings.
- Added the new defaults to both the Japanese README description and the English guide.
- All other functionality, UI, and generation behavior are unchanged from 0.2.1.

## 0.2.1 - 2026-09-03

- Clarified that the tool was developed for AGRaceSDK but may be used for other purposes without limiting its field of use.
- Simplified the statement that generated output may be freely used, modified, sold, and distributed for commercial or non-commercial purposes.
- Clarified that the `AGRace Tools` name may be used for identification and accurate source attribution.
- Clarified the license scope of README and NOTICE and the author's public distribution channels.
- The add-on code, functionality, UI, and generated results are unchanged from 0.2.0.

## 0.2.0 - 2026-09-02

- Documented the copyright holder, GNU GPL terms, generated-output permissions, and source and modified-version identification.
- Disclosed the use of OpenAI Codex for code generation and development assistance.
- Added `LICENSE.txt`, `NOTICE.md`, and `CHANGELOG.md` to the distributed package.
- Corrected implementation mismatches and missing information in README.
- Added SPDX copyright and license headers to all Python source files.
- The add-on functionality, UI, and generated results are unchanged from 0.1.19.

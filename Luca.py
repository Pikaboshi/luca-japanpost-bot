"""
日本郵便 追跡 -> Discord通知 Bot「Luca」 v4（複数件・複数人対応）

v4.27 の変更点（外部レビュー第3ラウンド: v4.26 の OCR 周り）:
  - 候補の元を、全パス結合テキストではなく候補ごとの集計
    （counts）のキーにした。結合は「1回の読み取りの中で、行単位で
    候補が無かった時だけ、その1回ぶんを結合して探す」形にし、
    パスをまたいだ結合で偽候補が構造的に出ないようにした
    （v4.26 の「一致0回なら外す」フィルタは、集計と候補の集合が
    実質同じで効いていなかったための作り直し）
  - /scan の待機に上限（120秒）を付け、取れなければ「混み合って
    います」と返すようにした。同じ人が実行中・待機中に重ねて
    実行することも弾くようにし、待機通知は読み取り開始時に
    削除するようにした（通知の送信失敗でスキャンが止まらない
    よう、通知まわりは例外を握る形にした）
  - OCR の所要時間と、締切で打ち切ったかどうかをコンソールへ
    出すようにした（締切300秒の妥当性を実測で判断するため）

v4.26 の変更点（外部レビュー第2ラウンド: v4.25 の OCR 周り）:
  - 候補ゼロ時の読み取り順を入れ替え、左右反転の読み取りを
    「通常パスでの回転リトライ」より先に回すようにした
    （締切で打ち切られた場合に、反転写真だけが拾えなくなる
    並びを避けるため。リトライは既に試した向きの保険なので最後）
  - 候補の集計を行単位だけにし、全パスをつないだテキストから
    作られた候補（どの1回の読み取りにも現れなかった、パス境界
    またぎの候補）は、候補一覧から外すようにした
    （日本郵便への照会枠を偽の候補に使わないため）
  - /scan の OCR が実行中のときに次の人が実行したら、待機中
    である旨を先に返すようにした（最大で締切ぶん待つため）

v4.25 の変更点（外部レビュー: v4.23/v4.24 の OCR 周り）:
  - OCR の候補ごとに「何回の読み取りで一致したか」と「通常パスで
    出たか」を数えるようにし、信頼できる候補だけで保留プールへ
    入れるようにした（通常パスで出た候補か、2回以上一致した候補
    だけが保留対象。1回だけの候補は即時照会とボタン提示のみで、
    保留には入れない。ノイズ候補で保留枠が埋まり、実在する他人の
    番号が保留経由で自動登録される経路を狭めるため）
  - 候補の並びを一致回数の多い順にした（正解が照会上限5件の
    外へ押し出されにくくするため）
  - なお「履歴が確認できた候補の自動登録」は従来どおり維持した。
    実地の正解（斜め・暖色の写真）でも一致が1回だけのことが
    確認できたためで、実在確認そのものを信頼の根拠とする
  - Tesseract の各呼び出しにタイムアウト（20秒）と、OCR全体の
    締切（300秒）を付け、/scan の OCR は同時に1件だけ実行する
    ようにした（処理が数分かかる間に同じ人が重ねて実行して、
    Tesseract が並列で走るのを防ぐため）
  - 回転・反転の前に画像を最大2000pxへ縮小するようにした
    （元解像度のコピーが重なってメモリを圧迫しないように）
  - Tesseract 本体が無い環境では、全パス空振りしてから
    「読み取れませんでした」になるのではなく、最初に1回だけ
    確認してインストール案内を出すようにした

v4.24 の変更点（実地テスト: 反転した写真への対応）:
  - /scan の OCR で、通常の読み取りで候補が見つからない場合に、
    左右反転した画像での読み取りも試すようにした
    （鏡越し・反転保存された写真でも番号を拾えるように）
  - 候補なしの場合の追加読み取りは、途中で候補が出ても打ち切らず
    全方向を混ぜて返すようにした（誤読候補の陰で正解が埋もれないように）
  - 境界線上の写真でも拾えるよう、回転読み取りは前処理の違う
    通常パスでも試すようにした

v4.23 の変更点（実地テスト: 回転した写真で読めない問題への対応）:
  - /scan の OCR に追加読み取りを入れた。追加パス（大津二値化・
    psm 11 の数字ホワイトリスト、拡大幅2400px）と、画像を180度・
    ±90度回転させた読み取りを組み合わせて候補を集める
    （逆さま・横向きに撮られた写真や、暖色照明の写真でも拾えるように）
  - 候補が見つかった場合も、誤読だけが残らないよう実績のある2方向の
    追加読み取りを混ぜて返す（正しい候補は日本郵便の履歴照合で選ばれる）
  - 前処理の拡大目標幅を引数化した（通常パスは従来通り1200px）

v4.22 の変更点（外部レビューの追加ラウンド）:
  - send_notification が成功時に True を返すよう修正（v4.21 で
    maybe_stall_alert が戻り値に依存するようになったのに、本体は
    None を返していたため、停滞アラートが通知済みにならなかった）
  - 状態の読み込みで、破損（退避＋直前の正常なコピー .bak から復旧）と
    一時的な読み込み失敗（退避せず再試行し、失敗した起動では保存を
    止めて実ファイルの上書きを防ぐ）を分けて扱うようにした
  - 保存時に直前の状態を .bak へ残すようにした
  - 読み込み時に追跡番号のキーも正規化・検証するようにした
  - OCR前処理で、縦に極端に長い画像の高さにも上限を設けた

v4.21 の変更点（外部レビューの最終ラウンド）:
  - 状態の読み込み時に追跡データへも上限（全体30件）を適用する
  - 状態ファイルの読み込み例外を広げ、権限エラーや文字コード破損でも
    起動時に落ちないようにした（元ファイルは .broken へ退避を試みる）
  - v2以前の旧形式からの移行でも、追跡番号の正規化と項目の型検証を
    新形式と同じルールで行うようにした
  - 停滞アラートは送信に成功したときだけ「通知済み」にし、失敗時は
    1時間あけて再試行する（一時的なエラーで通知を失わないため）

v4.20 の変更点（外部レビューの第6ラウンド）:
  - 登録処理のロック内でも権限を再確認する（事前チェック後に別の人が
    同じ番号を登録した競合でも、権限のない人が処理を進められないように）
  - stall_alerted も真偽値の True だけを有効とする（dm と揃えた）
  - 状態の読み込み時に history へも上限（100件）を適用する

v4.19 の変更点（外部レビューの第5ラウンド）:
  - 【重要】Windows初回起動時に NameError になる問題を修正
    （ACLヘルパーの定義がトークン読み込みより後ろにあったため、
    初回入力の保存時に未定義で落ちていた。定義をモジュール前半へ移動）
  - history の検証を中身まで拡張（番号が文字列でない項目は捨て、
    状態は文字列に寄せる。/history がキー欠落で落ちないように）
  - 通知設定の dm は真偽値の True だけを有効とする
    （文字列 "false" を True と誤認しないように）
  - 状態の読み込み時にも保留候補の上限（全体100件・1人20件）を適用

v4.18 の変更点（外部レビューの第4ラウンド＋Mahiru側デバッグ）:
  - 【重要】on_ready のイベント登録が外れていた問題を修正
    （復旧ヘルパー側にデコレータが付いていた。コマンド同期・監視開始が
    起動時に走らない状態だった）
  - 保留候補の照会中に /stop で取り消された候補が、照会成功後に
    自動登録されてしまう競合を修正（登録直前に保留の在籍を再確認）
  - /scan の候補数に上限（10件）、保留候補に全体上限（100件）と
    1人あたり上限（20件）を追加。登録ボタンも25個までに制限
  - 状態の検証を中身まで拡張（history は辞書だけ、user_prefs は dm を
    真偽値に正規化、保留番号は追跡番号の形式だけ通す）
  - 打ち切り回数を CHECK_MINUTES から「約24時間／約2時間」で算出する
    よう変更（間隔を変えても意味がずれないように）
  - Windows ではトークン・状態ファイルの ACL を自分だけに絞る処理を
    ベストエフォートで追加（失敗しても動作は止めない）
  - 再接続時にパネルViewを登録し直さないようガードを追加

v4.11 の変更点（外部レビューの最終セキュリティラウンド）:
  - サーバー所有者の操作権限が、別サーバーの荷物に及んでいた問題を修正
    （権限チェックにサーバーの一致を追加。入力候補でも他人の番号・メモを出さない）
  - 番号入力の正規化を一本化（全角→半角にそろえ、英数字以外は形式エラーに倒す）
  - 状態ファイルも所有者だけ読める権限で作り、壊れた場合は別名で退避する
  - /scan: 解像度の事前チェックと Pillow の展開爆弾対策、30秒クールダウン、
    エラー文面から例外の詳細を外した
  - 登録の上限チェックをロック内でも再確認する（同時登録で超えないように）
  - 環境変数 LUCA_GUILD_ALLOWLIST で、参加できるサーバーを制限できるようにした

v4.10 の変更点（外部レビューの第6ラウンド）:
  - 監視ループは止めずに常時回す（荷物ゼロのときは何もしない）。
    止める/再開するタイミングの取りこぼしで監視が死ぬのを防ぐ
  - 1件の処理で想定外の例外が出ても、他の荷物の監視は続ける
  - 通知が送れない場合は取得エラーと区別し、登録時の返答で
    チャンネルの投稿権限の確認を案内する
  - 登録者本人の再登録では、失敗カウンタをリセットする
    （状態の引き継ぎは維持するので、同じ状況が二重に通知されることはない）

v4.9 の変更点（Mahiru側デバッグで見つけた同時登録の競合対策）:
  - 登録処理（登録＋初回チェック）をロックの中で一貫して行う。
    同じ番号がほぼ同時に二重登録されても、通知が二重に飛ばないようにした

v4.8 の変更点（外部レビューの第5ラウンド）:
  - 通知はDM用（全文）とチャンネル用（マスク済み）の Embed を分けて作り、
    DM失敗のフォールバックでもメモ・担当局がチャンネルへ漏れないようにした
  - 停滞アラートの最新状況も、チャンネル宛てでは状態だけ表示（担当局を出さない）
  - 打ち切り通知の文面を理由ごと（履歴なし／取得エラー／送信失敗）に分けた
  - 登録直後に打ち切られた場合の返答文面を実態に合わせた
  - 再登録時のメモ・通知先の更新は、登録者本人だけが行えるようにした
  - /scan の履歴照会は候補5件まで。照会自体のエラーは履歴なしと区別して案内する

v4.7 の変更点（外部レビューの第4ラウンド）:
  - 取得エラーの打ち切りを約2時間→24時間に延長（日本郵便のメンテナンス等で
    全件が一斉に消えるのを防ぐ。履歴なし側の猶予と揃えた）
  - 通知の送信失敗も数え、24回連続で失敗したら追跡を終了する
    （チャンネル削除などで永遠に再試行し続けないように）
  - 同じ番号の再登録では状態を引き継ぎ、メモと通知先だけ更新する
    （同じ最新状況が二重に通知されるのを防ぐ）
  - /list とチャンネル宛て通知では担当局を出さない（他人の荷物の所在を伏せる）

v4.6 の変更点（外部レビューの第3ラウンド）:
  - /scan は候補を日本郵便で照会し、履歴がある候補だけを自動登録する
    （数字の誤結合による誤登録を防ぐ。履歴が無い候補は提示のみで /track へ案内）
  - 打ち切り通知は、登録を実際に外せたときだけ送る（再登録・停止との競合対策）
  - 照会間隔の sleep をロックの外に出し、登録時の初回チェックを待たせない
  - トークンファイルは作成時点から所有者だけ読み書きできる権限にする（Windows以外）
  - OCR前に幅2000pxを超える写真を縮小し、処理が重くなりすぎないようにする
  - 弱い候補（0始まり）が複数ある時も一覧で提示する

v4.5 の変更点（外部レビューの第2ラウンド）:
  - 番号抽出に境界条件を付け、13桁以上の数字列（バーコード等）の一部を拾わない
  - 0始まりの数字は「弱い候補」に分け、単独で見つかっても自動登録せず提示だけする
  - /scan のOCRで EXIF の向き情報を反映する（スマホ写真の横向き対策）
  - チェック中の再登録と重なっても、新しい登録を消さないよう同一性を確認してから外す
  - 荷物ごとの照会の間に1秒の間隔を入れる（日本郵便への負荷軽減）
  - トークン保存後に所有者だけ読み書きできる権限へ寄せる（Windows以外）

v4.4 の変更点（外部レビューで見つかった問題の修正）:
  - 「履歴が見つからない」を取得エラーと別カウントにし、打ち切りまでの猶予を
    約2時間から24時間に延長（発送前の番号が黙って消える問題の修正）
  - 連続失敗で追跡を打ち切るときは、登録者へ通知してから外す
  - チェックと /stop が重なっても KeyError で監視が止まらないよう pop に変更
  - /scan の候補から、0始まりの数字（電話番号の可能性が高いもの）を除外
  - /stop の拒否文面を実装どおり（本人かサーバー所有者）に修正

v4.3 の変更点（/scan のOCR精度改善）:
  - OCR前に拡大・グレースケール化・二値化の前処理を入れ、複数モードで読む
    （小さい写真でも番号を読めるようにする）
  - 番号の抽出は行ごとに行い、電話番号など別行の数字との誤結合を防ぐ
  - 全角の数字・英字も半角として扱う

v4.2 の変更点（安全側の小修正）:
  - 通知のメンション許可を登録者本人だけに限定（@everyone等の化け防止）
  - メモは登録経路によらず50文字で切りそろえる
  - /scan は10MBを超える画像を受け付けない
  - Tesseract がPATHに無くても、Windows既定のインストール先にあれば使う

v4.1 の変更点（他人も使う想定のプライバシー強化）:
  - 共有チャンネルへの通知では追跡番号を末尾4桁だけにマスクし、メモも出さない
    （DM通知と自分の画面だけの表示では全文のまま）
  - /list でも番号をマスクし、メモは表示しない

v4 の変更点:
  - 不在・持ち戻りを検知したら登録者にメンションし、再配達の案内を付ける
  - 「配達中」になったら「本日配達予定」として分かる見出しで通知する
  - 終端ステータス（配達完了など）で追跡を外れる前に、履歴へ記録する（/history）
  - 通知先を登録チャンネル / DM で切り替えられる（パネルのボタン、登録者ごと）
  - 48時間ステータスが動かない荷物に、1回だけ停滞アラートを出す
  - /scan で伝票の写真から追跡番号を読み取って登録できる
    （OCR: Tesseract 本体 + pip install pytesseract pillow が別途必要）

v3 の変更点:
  - 同時に何件でも（上限: 全体30件 / 1人10件まで）追跡できるようにした
  - 追跡は「登録した人ごと」に管理する。他の人の荷物の番号でも登録でき、
    その荷物の操作（停止・確認）ができるのは登録した本人とサーバー所有者だけ。
    つまり Discord 上の所有者 = 登録者であって、荷物の宛先が誰かは関係ない
    （日本郵便の追跡は番号さえあれば誰でも照会できる仕様のため）
  - /status は自分の追跡一覧、/list はこのサーバーの追跡一覧、
    /stop は番号を指定して1件だけ止める（省略すると自分の全件を停止）
  - 配達完了などの終端ステータスになった荷物は通知後に自動で一覧から外れる
    （終端ステータスの通知には登録者へのメンションが付く。それ以外の更新は付けない）
  - v2 の状態ファイル（1件形式）は起動時に自動で新形式へ移行する

v2 までの監査修正（認可・送信成功後に保存・ループの例外対策・Lockで直列化・
アトミックな状態保存・getpass入力・終了条件の拡充など）はすべて引き継いでいる。

使い方:
    pip install discord.py requests beautifulsoup4
    python Luca.py   （初回だけトークンを聞かれる。入力は画面に表示されない）
    Discordで /panel -> ボタン、または /track で追跡番号を入力
"""

import asyncio
import getpass
import io
import json
import math
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import traceback
import unicodedata
from pathlib import Path

import discord
import requests
from bs4 import BeautifulSoup
from discord import app_commands
from discord.ext import tasks

# ---- トークン ----
TOKEN_FILE = Path.home() / ".luca_token.txt"
LEGACY_TOKEN_FILE = Path(__file__).with_name("token.txt")  # v1 の保存先（移行用に読むだけ）


def _restrict_file_acl(path) -> None:
    """WindowsでファイルのACLを自分だけに絞る（ベストエフォート）。

    失敗しても動作は止めない（その場合は従来どおり親フォルダのACLを引き継ぐ）。
    状態ファイルは一時ファイル経由で差し替えるため、差し替え前に一時ファイルへ
    適用して権限を引き継がせる。
    ※ load_token() の中からも呼ばれるため、モジュール前半で定義すること。
    """
    if os.name != "nt":
        return
    username = os.environ.get("USERNAME")
    if not username:
        return
    try:
        subprocess.run(
            ["icacls", str(path), "/inheritance:r", "/grant:r",
             f"{username}:(F)"],
            capture_output=True, timeout=10, check=False,
        )
    except Exception:
        pass


def load_token() -> str:
    env_token = os.getenv("DISCORD_TOKEN")
    if env_token:
        return env_token.strip()
    for path in (TOKEN_FILE, LEGACY_TOKEN_FILE):
        if path.exists():
            saved = path.read_text(encoding="utf-8").strip()
            if saved:
                return saved
    print("初回設定: Discord Bot のトークンを貼って Enter を押してください。")
    print("（入力は画面に表示されません。次回からは自動で読み込みます）")
    print("注意: トークンは平文で保存されます。ファイルやスクリーンショットを共有しないでください。")
    if sys.stdin.isatty():
        entered = getpass.getpass("トークン: ").strip().strip('"').strip("'")
    else:
        entered = input("トークン: ").strip().strip('"').strip("'")
    if not entered:
        raise SystemExit("トークンが空でした。もう一度起動して貼ってください。")
    if os.name == "nt":
        TOKEN_FILE.write_text(entered, encoding="utf-8")
        _restrict_file_acl(TOKEN_FILE)
    else:
        # 作成した瞬間から所有者だけが読み書きできる権限にする
        fd = os.open(TOKEN_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(entered)
    return entered


TOKEN = load_token()

try:
    CHECK_MINUTES = max(1, int(os.getenv("CHECK_MINUTES", "5")))
except ValueError:
    CHECK_MINUTES = 5

STATE_FILE = Path(__file__).with_name("tracking_state.json")
DATE_RE = re.compile(r"\d{4}/\d{1,2}/\d{1,2}")
# 国内: 11〜12桁数字 / 国際(EMS等): 英字2 + 数字9 + 英字2
# \d は全角数字にも一致するため、数字は [0-9] で明示する
TRACKING_RE = re.compile(r"^([0-9]{11,12}|[A-Z]{2}[0-9]{9}[A-Z]{2})$")


def _parse_guild_allowlist() -> set[int]:
    ids: set[int] = set()
    for part in os.getenv("LUCA_GUILD_ALLOWLIST", "").split(","):
        part = part.strip()
        if part.isdigit():
            ids.add(int(part))
    return ids


# 参加を許可するサーバーID（環境変数 LUCA_GUILD_ALLOWLIST、カンマ区切り）。
# 空なら制限なし。知らないサーバーへ勝手に追加される使い方への備え。
GUILD_ALLOWLIST: set[int] = _parse_guild_allowlist()


def guild_allowed(guild_id) -> bool:
    return not GUILD_ALLOWLIST or guild_id in GUILD_ALLOWLIST


def clean_number(value: str) -> str:
    """追跡番号の入力を正規化する。

    全角は半角へそろえる（全角のまま登録されると、同じ荷物が別の番号として
    二重登録されるため）。英数字以外が混ざる入力は空文字を返して形式エラーに
    倒す（upper() で別文字に化ける特殊な文字への対策も兼ねる）。
    """
    normalized = unicodedata.normalize("NFKC", value)
    stripped = re.sub(r"[-\s]", "", normalized)
    if not stripped.isascii():
        return ""
    return stripped.upper()
TERMINAL_WORDS = ("お届け済み", "お渡し", "投函完了", "返送", "保管期限")
ABSENCE_WORDS = ("持ち戻り",)  # 「ご不在のため持ち戻り」など
# 打ち切りの回数は「時間」から決める（CHECK_MINUTES を変えても意味がずれないように）
MAX_CONSECUTIVE_FAILURES = max(1, math.ceil(24 * 60 / CHECK_MINUTES))  # 取得エラーの打ち切り（約24時間ぶん。メンテナンス等で全件消えないよう長め）
SEND_FAIL_LIMIT = max(1, math.ceil(2 * 60 / CHECK_MINUTES))  # 通知の送信失敗が約2時間続いたらその荷物は諦める
NOTFOUND_LIMIT = max(1, math.ceil(24 * 60 / CHECK_MINUTES))  # 「履歴なし」は発送前があり得るので約24時間まで粘る
MAX_TOTAL = 30  # 同時に追跡できる全体の上限
MAX_PER_USER = 10  # 1人あたりの上限
PENDING_INTERVAL = 2 * 3600  # /scan の保留候補を再確認する間隔（秒）
PENDING_TTL = 48 * 3600  # /scan の保留候補を保持する期間（秒）
MAX_SCAN_CANDIDATES = 10  # 1回の /scan で扱う候補の上限（照会・保留の対象）
PENDING_MAX_TOTAL = 100  # 保留候補の全体上限（再照会の負荷対策）
PENDING_MAX_PER_USER = 20  # 保留候補の1人あたり上限
OCR_CALL_TIMEOUT = 20  # Tesseract 1回の呼び出しのタイムアウト（秒）
OCR_DEADLINE_SECONDS = 300  # /scan の OCR 全体の締切（秒）
OCR_WAIT_TIMEOUT_SECONDS = 120  # /scan の OCR 待機の上限（秒）
STALL_SECONDS = 48 * 3600  # この時間ステータスが動かなければ停滞アラート
HISTORY_MAX = 100  # 配達済み履歴の保持件数


# ---- 状態の保存 ----
def _coerce_int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _coerce_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _sanitize_entry(entry: dict) -> dict:
    """追跡データ1件のフィールド型を検証し、不正な値を安全側へ寄せる。"""
    out = dict(entry)
    for key in ("fail_count", "notfound_count", "send_fail_count"):
        out[key] = max(0, _coerce_int(entry.get(key), 0))
    for key in ("channel_id", "guild_id", "owner_id"):
        value = entry.get(key)
        out[key] = _coerce_int(value) if value is not None else None
    if not isinstance(out.get("memo"), str):
        out["memo"] = ""
    if not isinstance(out.get("owner_name"), str):
        out["owner_name"] = ""
    for key in ("last_key", "last_status"):
        if out.get(key) is not None and not isinstance(out.get(key), str):
            out[key] = None
    if entry.get("last_change_at") is not None:
        out["last_change_at"] = _coerce_float(entry.get("last_change_at"))
    if entry.get("stall_last_try") is not None:
        out["stall_last_try"] = _coerce_float(entry.get("stall_last_try"))
    # 文字列 "false" などを True と誤認しないよう、真偽値の True だけを有効とする
    out["stall_alerted"] = entry.get("stall_alerted") is True
    return out


def _sanitize_state(raw: dict) -> dict:
    """読み込んだ状態の型を検証し、不正な項目は安全な既定値へ落とす。

    JSONとして読めても中身の型が想定と違う場合（手編集や旧ツール由来）に、
    後続処理が落ちないようにするための最終防衛線。
    """
    trackings = raw.get("trackings")
    if not isinstance(trackings, dict):
        trackings = {}
    else:
        normalized = {}
        for k, v in trackings.items():
            if not isinstance(v, dict):
                continue
            # キー（追跡番号）も新形式と同じルールで正規化・検証する
            nk = clean_number(str(k))
            if not TRACKING_RE.fullmatch(nk):
                continue
            normalized[nk] = _sanitize_entry(v)
        trackings = normalized
        if len(trackings) > MAX_TOTAL:
            # 手編集などで上限を超えたファイルでも、読み込み時に切り詰める
            # （残すのはファイルの並び順で先頭から上限件数）
            trackings = dict(list(trackings.items())[:MAX_TOTAL])
    history = raw.get("history")
    if not isinstance(history, list):
        history = []
    else:
        cleaned_history = []
        for h in history:
            if not isinstance(h, dict):
                continue
            if not isinstance(h.get("number"), str) or not h["number"]:
                continue
            h = dict(h)
            if not isinstance(h.get("status"), str):
                h["status"] = ""
            cleaned_history.append(h)
        history = cleaned_history[-HISTORY_MAX:]
    user_prefs = raw.get("user_prefs")
    if not isinstance(user_prefs, dict):
        user_prefs = {}
    else:
        cleaned_prefs = {}
        for k, v in user_prefs.items():
            if isinstance(v, dict):
                v = dict(v)
                # 文字列 "false" などを True と誤認しないよう、
                # 真偽値の True だけを有効とする
                v["dm"] = v.get("dm") is True
                cleaned_prefs[k] = v
        user_prefs = cleaned_prefs
    pending = raw.get("pending_scans")
    if not isinstance(pending, list):
        pending = []
    else:
        cleaned = []
        for p in pending:
            if not isinstance(p, dict):
                continue
            number = clean_number(str(p.get("number", "")))
            if not re.fullmatch(
                r"[0-9]{11,12}|[A-Z]{2}[0-9]{9}[A-Z]{2}", number
            ):
                continue
            q = dict(p)
            q["number"] = number
            q["created_at"] = _coerce_float(p.get("created_at"), 0.0)
            q["last_checked_at"] = _coerce_float(p.get("last_checked_at"), 0.0)
            q["owner_id"] = _coerce_int(p.get("owner_id"))
            q["channel_id"] = _coerce_int(p.get("channel_id"))
            q["guild_id"] = _coerce_int(p.get("guild_id"))
            if not isinstance(q.get("memo"), str):
                q["memo"] = ""
            if not isinstance(q.get("owner_name"), str):
                q["owner_name"] = ""
            cleaned.append(q)
        # 読み込み時にも件数上限を適用する（手編集や旧バージョンの
        # 状態ファイルから大量に読み込まれても、処理量が膨らまないように）
        capped = []
        per_owner: dict = {}
        for q in cleaned:
            if len(capped) >= PENDING_MAX_TOTAL:
                break
            owner = q.get("owner_id")
            if per_owner.get(owner, 0) >= PENDING_MAX_PER_USER:
                continue
            per_owner[owner] = per_owner.get(owner, 0) + 1
            capped.append(q)
        pending = capped
    return {
        "trackings": trackings,
        "history": history,
        "user_prefs": user_prefs,
        "pending_scans": pending,
    }


_state_load_failed = False


def _load_backup_raw():
    """直前の正常な保存のコピー（.bak）を読む。読めなければ None。"""
    try:
        return json.loads(
            STATE_FILE.with_name(STATE_FILE.name + ".bak").read_text(
                encoding="utf-8"
            )
        )
    except Exception:
        return None


def load_state() -> dict:
    global _state_load_failed
    raw = None
    for attempt in range(3):
        try:
            raw = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            break
        except FileNotFoundError:
            return {"trackings": {}, "history": [], "user_prefs": {}}
        except (json.JSONDecodeError, UnicodeDecodeError):
            # 中身の破損: 元ファイルを退避し、直前の正常なコピーが
            # あればそこから復旧する
            backup = STATE_FILE.with_name(STATE_FILE.name + ".broken")
            try:
                os.replace(STATE_FILE, backup)
                print(f"状態ファイルが壊れていたため {backup.name} に退避しました")
            except OSError:
                pass
            raw = _load_backup_raw()
            if raw is None:
                return {"trackings": {}, "history": [], "user_prefs": {}}
            print("直前の正常なコピーから状態を復旧しました")
            break
        except OSError:
            # 権限やファイルロックなど、一時的な読み込み失敗かもしれない。
            # 破損と違って退避はせず、少し待って読み直す
            if attempt < 2:
                time.sleep(0.3)
                continue
            # 最後まで読めなかった起動では、空の状態で実ファイルを
            # 上書きしてしまわないよう、この起動中は保存を止める
            _state_load_failed = True
            print("状態ファイルを読めなかったため、この起動中は保存を行いません")
            return {"trackings": {}, "history": [], "user_prefs": {}}
    if isinstance(raw, dict) and "trackings" in raw:
        return _sanitize_state(raw)
    # v2 以前の1件形式 -> 新形式へ移行
    if isinstance(raw, dict) and raw.get("tracking_number"):
        # 新形式と同じく、番号は正規化してから検証し、項目も型検証を通す
        number = clean_number(str(raw["tracking_number"]))
        if not TRACKING_RE.fullmatch(number):
            return {"trackings": {}, "history": [], "user_prefs": {}}
        entry = _sanitize_entry({
            "channel_id": raw.get("channel_id"),
            "guild_id": None,
            "memo": raw.get("memo", ""),
            "last_key": raw.get("last_key"),
            "last_status": None,
            "owner_id": raw.get("owner_id"),
            "owner_name": "",
            "fail_count": raw.get("fail_count", 0),
            "last_change_at": None,
            "stall_alerted": False,
        })
        return {
            "trackings": {number: entry},
            "history": [],
            "user_prefs": {},
        }
    return {"trackings": {}, "history": [], "user_prefs": {}}


def save_state() -> None:
    if _state_load_failed:
        # 読み込みに失敗した起動では、空の状態で実ファイルを上書きしない
        print("状態の読み込みに失敗しているため、保存をスキップしました")
        return
    tmp = STATE_FILE.with_suffix(".tmp")
    data = json.dumps(state, ensure_ascii=False, indent=2)
    if os.name == "nt":
        tmp.write_text(data, encoding="utf-8")
        _restrict_file_acl(tmp)
    else:
        # 追跡番号とメモが入るため、トークンと同じく所有者だけ読める権限で作る
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(data)
    if STATE_FILE.exists():
        # 置き換える直前の正常な状態を .bak に残す（本体が壊れたときに
        # load_state がここから復旧できるように）
        try:
            STATE_FILE.with_name(STATE_FILE.name + ".bak").write_bytes(
                STATE_FILE.read_bytes()
            )
        except OSError:
            pass
    os.replace(tmp, STATE_FILE)


state = load_state()
trackings: dict = state.setdefault("trackings", {})
history_log: list = state.setdefault("history", [])
user_prefs: dict = state.setdefault("user_prefs", {})
# trackings[number] = {channel_id, guild_id, memo, last_key, last_status,
#                      owner_id, owner_name, fail_count,
#                      last_change_at, stall_alerted}
# user_prefs[str(owner_id)] = {"dm": bool}  通知先（False=チャンネル / True=DM）
pending_scans: list = state.setdefault("pending_scans", [])
# Botアプリの所有者ID（起動時に取得）。旧データの復旧権限の判定に使う
bot_owner_id: int | None = None
# パネルViewを登録済みかどうか（再接続のたびに登録し直さないため）
_panel_view_added = False
# pending_scans[i] = {number, owner_id, owner_name, guild_id, channel_id,
#                     memo, created_at, last_checked_at}
# /scan で履歴がまだ無かった候補を保留し、履歴が出たら自動登録する置き場。


def can_manage(interaction: discord.Interaction, entry: dict) -> bool:
    """その荷物を操作できるのは登録者本人と、その荷物が登録された
    サーバーの所有者だけ（別サーバーの所有者の権限は及ばない）。"""
    owner_id = entry.get("owner_id")
    if owner_id is not None and owner_id == interaction.user.id:
        return True
    # 登録者もサーバーも記録されていない旧データは、Botの所有者だけが
    # 復旧・停止できる（他サーバーの所有者にまで権限を広げない）。
    # 所属サーバーが分かるものは起動時に channel_id から復元される。
    if owner_id is None and entry.get("guild_id") is None:
        return bot_owner_id is not None and interaction.user.id == bot_owner_id
    return (
        interaction.guild is not None
        and interaction.guild.owner_id == interaction.user.id
        and entry.get("guild_id") == interaction.guild_id
    )


# ---- 日本郵便から最新ステータスを取得（同期処理） ----
def fetch_latest(tracking_number: str) -> dict | None:
    res = requests.get(
        "https://trackings.post.japanpost.jp/services/srv/search/direct",
        params={"reqCodeNo1": tracking_number, "locale": "ja"},
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        },
        timeout=15,
    )
    res.raise_for_status()

    soup = BeautifulSoup(res.content, "html.parser")
    table = soup.find("table", summary="履歴情報")
    if table is None:
        return None

    events = []
    for row in table.find_all("tr"):
        cols = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
        if cols and DATE_RE.match(cols[0]):
            if len(cols) >= 5:
                events.append(
                    {
                        "date_time": cols[0],
                        "status": cols[1],
                        "office": cols[3],
                        "prefecture": cols[4],
                    }
                )
            else:
                print(f"警告: 列不足のため読み取れなかった履歴行があります: {cols}")
    return events[-1] if events else None  # 履歴は古い順 -> 最後が最新


def classify_status(status: str) -> str:
    """ステータス文字列から通知の種類を判定する。

    "final"（終端）/ "absent"（不在・持ち戻り）/ "today"（配達中）/ "update"
    """
    if any(word in status for word in TERMINAL_WORDS):
        return "final"
    if any(word in status for word in ABSENCE_WORDS):
        return "absent"
    if "配達中" in status:
        return "today"
    return "update"


_EMBED_STYLE = {
    "update": ("📦 郵便追跡ステータス更新", discord.Color.blue()),
    "today": ("🚚 本日配達予定です", discord.Color.green()),
    "absent": ("⚠️ ご不在のため持ち戻り", discord.Color.orange()),
    "final": ("✅ 配達・追跡が終了しました", discord.Color.green()),
}


def mask_number(number: str) -> str:
    """追跡番号を末尾4桁だけ残して伏せる（共有チャンネル向け）。"""
    if len(number) <= 4:
        return "****"
    return "*" * (len(number) - 4) + number[-4:]


def make_embed(
    number: str,
    entry: dict,
    latest: dict,
    kind: str = "update",
    masked: bool = False,
) -> discord.Embed:
    title, color = _EMBED_STYLE.get(kind, _EMBED_STYLE["update"])
    shown_number = mask_number(number) if masked else number
    embed = discord.Embed(
        title=title,
        description=(
            f"**追跡番号:** `{shown_number}`\n"
            f"**最新状況:** **{latest['status']}**"
        ),
        color=color,
    )
    if entry.get("memo") and not masked:
        embed.add_field(name="メモ", value=entry["memo"], inline=False)
    if entry.get("owner_name"):
        embed.add_field(name="登録者", value=entry["owner_name"], inline=True)
    embed.add_field(name="日時", value=latest["date_time"], inline=False)
    if not masked:
        # チャンネル宛てでは担当局（荷物の所在）も伏せる
        embed.add_field(
            name="担当局・都道府県",
            value=f"{latest['office']} ({latest['prefecture']})",
            inline=False,
        )
    if kind == "absent":
        if masked:
            guidance = "不在票に記載の方法（Web・電話・QRコード）で再配達を申し込めます。"
        else:
            guidance = (
                "不在票に記載の方法（Web・電話・QRコード）で再配達を申し込めます。\n"
                f"追跡ページ: https://trackings.post.japanpost.jp/services/srv/search/direct?reqCodeNo1={number}"
            )
        embed.add_field(name="再配達", value=guidance, inline=False)
    return embed


def scrub_embed(embed: discord.Embed, number: str) -> None:
    """Embed内の追跡番号の全文をマスク版へ置き換える（DM失敗時の保険）。"""
    masked = mask_number(number)
    if embed.description:
        embed.description = embed.description.replace(number, masked)
    if embed.title:
        embed.title = embed.title.replace(number, masked)
    for i, field in enumerate(list(embed.fields)):
        new_value = (field.value or "").replace(number, masked)
        new_name = (field.name or "").replace(number, masked)
        if new_value != field.value or new_name != field.name:
            embed.set_field_at(
                i, name=new_name, value=new_value, inline=field.inline
            )


def wants_dm(entry: dict) -> bool:
    owner_id = entry.get("owner_id")
    if owner_id is None:
        return False
    return bool(user_prefs.get(str(owner_id), {}).get("dm"))


# 通知で許可するメンションは「登録者本人だけ」
# （メモ等の文字列が @everyone やロールメンションに化けないための保険）
_NOTIFY_MENTIONS = discord.AllowedMentions(
    everyone=False, roles=False, users=True, replied_user=False
)


async def send_notification(
    entry: dict,
    embed: discord.Embed,
    content: str | None = None,
    number: str | None = None,
    public_embed: discord.Embed | None = None,
) -> bool:
    """通知を送る。登録者がDM設定ならDMへ、失敗したら登録チャンネルへ送る。

    チャンネルへ送る場合は public_embed（番号マスク済み・メモ/担当局なし）を
    使うこと。DM失敗でチャンネルへ回すときに DM 用 Embed をそのまま使うと、
    メモや担当局まで見えてしまうため。public_embed が無い場合の保険として、
    number の全文だけはマスク版へ置き換えてから送る。
    """
    if wants_dm(entry):
        try:
            user = client.get_user(entry["owner_id"]) or await client.fetch_user(
                entry["owner_id"]
            )
            dm = user.dm_channel or await user.create_dm()
            await dm.send(content=content, embed=embed, allowed_mentions=_NOTIFY_MENTIONS)
            return True
        except Exception as e:
            print(f"DM送信に失敗したためチャンネルへ送ります: {e}")
            if public_embed is not None:
                embed = public_embed
            elif number:
                scrub_embed(embed, number)
    channel = client.get_channel(entry["channel_id"]) or await client.fetch_channel(
        entry["channel_id"]
    )
    await channel.send(content=content, embed=embed, allowed_mentions=_NOTIFY_MENTIONS)
    return True


_check_lock = asyncio.Lock()
# /scan の OCR は重い（最悪で数分）ため、同時に1件だけ実行する。
# クールダウン30秒だけでは処理時間より短く、重ねて実行できてしまうため。
_scan_semaphore = asyncio.Semaphore(1)
# /scan を実行中・待機中のユーザーID（同じ人が待ち行列を埋めないため）
_scan_active_users: set[int] = set()


async def check_entry(number: str, entry: dict) -> str:
    """1件チェックする。

    戻り値: "sent" / "delivered"(終端・要削除) / "nochange" /
            "notfound" / "error"(取得側) / "send_error"(送信側) /
            "giveup"(連続失敗・要削除)
    呼び出し側は Lock の中から呼ぶこと。
    """
    try:
        latest = await asyncio.to_thread(fetch_latest, number)
    except Exception as e:
        print(f"[{number}] 取得エラー: {e}")
        entry["fail_count"] = int(entry.get("fail_count", 0)) + 1
        if entry["fail_count"] >= MAX_CONSECUTIVE_FAILURES:
            entry["giveup_reason"] = "fetch"
            return "giveup"
        return "error"

    if latest is None:
        print(f"[{number}] 履歴が取得できませんでした（未登録か構造変更の可能性）")
        # 発送前で履歴がまだ無いだけの可能性があるため、取得エラーとは別に数え、
        # 猶予も長く取る（NOTFOUND_LIMIT）。黙って消えないよう、打ち切り時は通知する。
        entry["notfound_count"] = int(entry.get("notfound_count", 0)) + 1
        if entry["notfound_count"] >= NOTFOUND_LIMIT:
            entry["giveup_reason"] = "notfound"
            return "giveup"
        return "notfound"

    entry["fail_count"] = 0
    entry["notfound_count"] = 0
    key = f"{latest['date_time']}|{latest['status']}|{latest['office']}"
    if key == entry.get("last_key"):
        return "nochange"

    kind = classify_status(latest["status"])
    is_terminal = kind == "final"
    # 終端と不在・持ち戻りのときだけ、登録者にメンションする
    mention = None
    if kind in ("final", "absent") and entry.get("owner_id"):
        mention = f"<@{entry['owner_id']}>"

    # 先に送り、成功してから「通知済み」として記録する
    # チャンネル宛ての通知は番号をマスクする（DM宛ては全文）。
    # DM失敗でチャンネルへ回す場合に備え、マスク済みの Embed も渡す。
    to_dm = wants_dm(entry)
    try:
        await send_notification(
            entry,
            make_embed(number, entry, latest, kind, masked=not to_dm),
            content=mention,
            number=number,
            public_embed=(
                make_embed(number, entry, latest, kind, masked=True) if to_dm else None
            ),
        )
    except Exception as e:
        print(f"[{number}] 送信エラー（次回再送します）: {e}")
        # 送信失敗も数える。チャンネル削除などで直らない場合に、
        # 永遠に再試行し続けないよう上限で打ち切る。
        entry["send_fail_count"] = int(entry.get("send_fail_count", 0)) + 1
        if entry["send_fail_count"] >= SEND_FAIL_LIMIT:
            print(f"[{number}] 送信失敗が続くため追跡を終了します")
            entry["giveup_reason"] = "send"
            return "giveup"
        return "send_error"

    entry["send_fail_count"] = 0
    entry["last_key"] = key
    entry["last_status"] = (
        f"{latest['status']}（{latest['date_time']}・{latest['office']}）"
    )
    entry["last_change_at"] = time.time()
    entry["stall_alerted"] = False
    if is_terminal:
        history_log.append(
            {
                "number": number,
                "memo": entry.get("memo", ""),
                "owner_id": entry.get("owner_id"),
                "owner_name": entry.get("owner_name", ""),
                "status": latest["status"],
                "date_time": latest["date_time"],
                "finished_at": time.strftime("%Y/%m/%d %H:%M"),
            }
        )
        del history_log[:-HISTORY_MAX]
        return "delivered"
    return "sent"


async def maybe_stall_alert(number: str, entry: dict) -> None:
    """ステータスが STALL_SECONDS 以上動いていなければ、1回だけ知らせる。"""
    last_change = entry.get("last_change_at")
    if not last_change or entry.get("stall_alerted"):
        return
    if time.time() - float(last_change) < STALL_SECONDS:
        return
    last_try = entry.get("stall_last_try") or 0
    if time.time() - float(last_try) < 3600:
        return  # 送信に失敗した直後は、1時間あけてから再試行する
    entry["stall_last_try"] = time.time()
    hours = int((time.time() - float(last_change)) // 3600)
    to_dm = wants_dm(entry)

    def build(masked: bool) -> discord.Embed:
        shown_number = mask_number(number) if masked else number
        # last_status には担当局も入っているため、マスク時は状態の部分だけ出す
        status = entry.get("last_status") or "未取得"
        if masked:
            status = status.split("（")[0]
        embed = discord.Embed(
            title="⏳ 荷物が止まっているかもしれません",
            description=(
                f"**追跡番号:** `{shown_number}`\n"
                f"**最新状況:** **{status}**\n"
                f"最後の更新から約 {hours} 時間、動きがありません。"
            ),
            color=discord.Color.orange(),
        )
        if entry.get("memo") and not masked:
            embed.add_field(name="メモ", value=entry["memo"], inline=False)
        return embed

    mention = f"<@{entry['owner_id']}>" if entry.get("owner_id") else None
    ok = False
    try:
        ok = await send_notification(
            entry,
            build(masked=not to_dm),
            content=mention,
            number=number,
            public_embed=build(masked=True) if to_dm else None,
        )
    except Exception as e:
        print(f"[{number}] 停滞アラート送信エラー: {e}")
    if ok:
        # 届いたときだけ「通知済み」にする。失敗時は stall_last_try の
        # 間隔をあけて再試行する（一時的なエラーで通知を失わないため）
        entry["stall_alerted"] = True


_GIVEUP_REASONS = {
    "notfound": "一定期間、履歴が見つからなかったため追跡を終了しました。",
    "fetch": "一定期間、状況を取得できなかったため追跡を終了しました。",
    "send": "通知を送信できない状態が続いたため追跡を終了しました。",
}


async def notify_giveup(number: str, entry: dict) -> None:
    """連続失敗で追跡を打ち切るとき、登録者へ知らせる（ベストエフォート）。"""
    to_dm = wants_dm(entry)
    reason = _GIVEUP_REASONS.get(
        entry.get("giveup_reason"), _GIVEUP_REASONS["fetch"]
    )

    def build(masked: bool) -> discord.Embed:
        shown_number = mask_number(number) if masked else number
        embed = discord.Embed(
            title="🛑 追跡を終了しました",
            description=(
                f"**追跡番号:** `{shown_number}`\n"
                f"{reason}"
                "番号が正しい場合は /track で登録し直してください。"
            ),
            color=discord.Color.red(),
        )
        if entry.get("memo") and not masked:
            embed.add_field(name="メモ", value=entry["memo"], inline=False)
        return embed

    mention = f"<@{entry['owner_id']}>" if entry.get("owner_id") else None
    try:
        await send_notification(
            entry,
            build(masked=not to_dm),
            content=mention,
            number=number,
            public_embed=build(masked=True) if to_dm else None,
        )
    except Exception as e:
        print(f"[{number}] 打ち切り通知の送信エラー: {e}")


async def check_all() -> None:
    # 照会間隔の sleep はロックの外で待つ（登録時の初回チェックを待たせないため）。
    # チェック自体は1件ずつロックを取り、check_entry の呼び出しを直列化する。
    # 1件で想定外の例外が出ても、他の荷物と監視ループ自体は止めない。
    for i, number in enumerate(list(trackings.keys())):
        if i:
            await asyncio.sleep(1)  # 荷物ごとの照会に間隔を空ける
        try:
            async with _check_lock:
                entry = trackings.get(number)
                if entry is None:
                    continue
                result = await check_entry(number, entry)
                if result == "nochange":
                    await maybe_stall_alert(number, entry)
                if result in ("delivered", "giveup"):
                    # /stop と重なって既に消えていても KeyError にしない。
                    # チェック中に同じ番号が再登録されていたら、新しい登録は消さない。
                    removed = False
                    if trackings.get(number) is entry:
                        trackings.pop(number, None)
                        removed = True
                    if result == "giveup":
                        print(f"[{number}] 連続失敗のため追跡を終了します")
                        # 実際に外せたときだけ通知する（再登録・停止済みなら送らない）
                        if removed:
                            await notify_giveup(number, entry)
                save_state()
        except Exception as e:
            print(f"[{number}] 想定外のエラー: {e!r}")

    try:
        await process_pending_scans()
    except Exception as e:
        print(f"保留候補の処理で想定外のエラーが発生しました: {e!r}")


def add_pending_candidates(
    interaction: discord.Interaction, numbers: list[str], memo: str,
    *, checked_now: bool,
) -> None:
    """/scan の候補を保留プールへ入れる（追跡中・保留中と重なる番号は除く）。"""
    now = time.time()
    added = False
    for number in numbers:
        if number in trackings:
            continue
        if any(p.get("number") == number for p in pending_scans):
            continue
        if len(pending_scans) >= PENDING_MAX_TOTAL:
            break
        mine = sum(
            1 for p in pending_scans
            if p.get("owner_id") == interaction.user.id
        )
        if mine >= PENDING_MAX_PER_USER:
            break
        pending_scans.append(
            {
                "number": number,
                "owner_id": interaction.user.id,
                "owner_name": interaction.user.display_name,
                "guild_id": interaction.guild_id,
                "channel_id": interaction.channel_id,
                "memo": memo[:50],
                "created_at": now,
                "last_checked_at": now if checked_now else 0.0,
            }
        )
        added = True
    if added:
        save_state()


async def process_pending_scans() -> None:
    """保留候補を定期的に確認し、履歴が出たものを自動登録する。

    ・追跡中に移った番号と、保持期間（PENDING_TTL）を過ぎた候補は捨てる
    ・確認は PENDING_INTERVAL ごと。兄弟候補は、1件が登録されても
      期間いっぱいまで残す（別の本物の荷物である可能性を残すため）
    """
    if not pending_scans:
        return
    now = time.time()
    changed = False
    fetched = False
    for pend in list(pending_scans):
        number = pend.get("number")
        try:
            if number in trackings:
                if pend in pending_scans:
                    pending_scans.remove(pend)
                    changed = True
                continue
            if now - float(pend.get("created_at", now)) > PENDING_TTL:
                if pend in pending_scans:
                    pending_scans.remove(pend)
                    changed = True
                continue
            if now - float(pend.get("last_checked_at", 0)) < PENDING_INTERVAL:
                continue
            if fetched:
                await asyncio.sleep(1)  # 照会に間隔を空ける
            fetched = True
            try:
                latest = await asyncio.to_thread(fetch_latest, number)
            except Exception:
                pend["last_checked_at"] = time.time()
                changed = True
                continue
            if latest is None:
                pend["last_checked_at"] = time.time()
                changed = True
                continue
            # 履歴が出た → 登録する（登録から初回チェックまでロックの中で行う）
            async with _check_lock:
                if not any(p is pend for p in pending_scans):
                    # 照会中に /stop で取り消されていたら登録しない
                    continue
                if number in trackings:
                    pending_scans.remove(pend)
                    changed = True
                    continue
                owner_id = pend.get("owner_id")
                my_count = sum(
                    1 for e in trackings.values()
                    if e.get("owner_id") == owner_id
                )
                if my_count >= MAX_PER_USER or len(trackings) >= MAX_TOTAL:
                    # 上限に達していたら保留を打ち切る
                    pending_scans.remove(pend)
                    changed = True
                    continue
                entry = {
                    "channel_id": pend.get("channel_id"),
                    "guild_id": pend.get("guild_id"),
                    "memo": (pend.get("memo") or "")[:50],
                    "last_key": None,
                    "last_status": None,
                    "owner_id": owner_id,
                    "owner_name": pend.get("owner_name") or "不明",
                    "fail_count": 0,
                    "notfound_count": 0,
                    "send_fail_count": 0,
                    "last_change_at": time.time(),
                    "stall_alerted": False,
                }
                trackings[number] = entry
                pending_scans.remove(pend)
                changed = True
                save_state()
                result = await check_entry(number, entry)
                if result in ("delivered", "giveup") and (
                    trackings.get(number) is entry
                ):
                    trackings.pop(number, None)
                save_state()
            print(f"[{number}] /scan の保留候補に履歴が出たため自動登録しました")
        except Exception as e:
            print(f"[pending {number}] 想定外のエラー: {e!r}")
    if changed:
        save_state()


@tasks.loop(minutes=CHECK_MINUTES)
async def check_tracking():
    await check_all()


@check_tracking.error
async def _loop_error(exc: Exception):
    print(f"監視ループで想定外のエラーが発生しました: {exc!r}")


@check_tracking.before_loop
async def _before_loop():
    await client.wait_until_ready()


# ---- 登録まわり（モーダルと /scan で共用） ----
def registration_error(interaction: discord.Interaction, cleaned: str) -> str | None:
    """登録前のチェック。問題があればユーザー向けメッセージ、なければ None。"""
    existing = trackings.get(cleaned)
    if existing is not None and not can_manage(interaction, existing):
        # 番号を試しただけで他人の追跡状況や名前が分からないよう、名前は出さない
        return "その番号は既に他の人が追跡中です。"
    if existing is None:
        my_count = sum(
            1 for e in trackings.values() if e.get("owner_id") == interaction.user.id
        )
        if my_count >= MAX_PER_USER:
            return (
                f"1人あたりの上限（{MAX_PER_USER}件）に達しています。"
                "/stop で古いものを止めてください。"
            )
        if len(trackings) >= MAX_TOTAL:
            return f"全体の上限（{MAX_TOTAL}件）に達しています。"
    return None


async def register_and_check(
    interaction: discord.Interaction, cleaned: str, memo: str
) -> str:
    """登録して初回チェックまで行い、結果メッセージを返す。

    呼び出し側が defer 済みであること。
    """
    memo = memo[:50]  # モーダルの上限に合わせる（Embedの項目上限対策も兼ねる）
    # 登録から初回チェックまでをロックの中で行い、同じ番号の同時登録で
    # 状態が上書きされたり通知が二重に飛んだりしないようにする
    async with _check_lock:
        existing = trackings.get(cleaned)
        if existing is not None and not can_manage(interaction, existing):
            # 事前チェックの後、ロック取得までの間に別の人が同じ番号を
            # 登録した場合に備え、権限をロック内でも再確認する
            return "その番号は既に他の人が追跡中です。"
        if existing is None:
            # 上限は事前チェックに加えてロック内でも数え直す
            # （同時登録で上限を超えないように）
            my_count = sum(
                1 for e in trackings.values()
                if e.get("owner_id") == interaction.user.id
            )
            if my_count >= MAX_PER_USER:
                return (
                    f"1人あたりの上限（{MAX_PER_USER}件）に達しています。"
                    "/stop で古いものを止めてください。"
                )
            if len(trackings) >= MAX_TOTAL:
                return f"全体の上限（{MAX_TOTAL}件）に達しています。"
        if existing is not None:
            # 再登録では状態（通知済みの最新状況など）を引き継ぐ。
            # メモと通知先の更新は登録者本人だけ（サーバー所有者が他人の荷物を
            # 操作できても、メモや通知先までは書き換えない）。
            if interaction.user.id == existing.get("owner_id"):
                existing["memo"] = memo
                existing["channel_id"] = interaction.channel_id
                existing["guild_id"] = interaction.guild_id
                # 本人の登録し直しでは失敗カウンタをリセットする
                # （last_key は引き継ぐので、同じ状況が二重に通知されることはない）
                existing["fail_count"] = 0
                existing["notfound_count"] = 0
                existing["send_fail_count"] = 0
            entry = existing
        else:
            entry = {
                "channel_id": interaction.channel_id,
                "guild_id": interaction.guild_id,
                "memo": memo,
                "last_key": None,
                "last_status": None,
                "owner_id": interaction.user.id,
                "owner_name": interaction.user.display_name,
                "fail_count": 0,
                "notfound_count": 0,
                "send_fail_count": 0,
                "last_change_at": time.time(),
                "stall_alerted": False,
            }
            trackings[cleaned] = entry
        save_state()
        result = await check_entry(cleaned, entry)
        if result in ("delivered", "giveup") and trackings.get(cleaned) is entry:
            trackings.pop(cleaned, None)
        save_state()

    if trackings and not check_tracking.is_running():
        check_tracking.start()

    if result == "delivered":
        return f"`{cleaned}` は既に配達が完了していたので、通知して追跡を終了しました。"
    if result == "notfound":
        return (
            f"監視を開始しました: `{cleaned}`\n"
            "⚠️ まだ履歴が見つかりません。番号が正しいか確認してください（監視は続けます）。"
        )
    if result == "giveup":
        return (
            f"`{cleaned}` は登録しましたが、問題が続いたため追跡を終了しました。\n"
            "番号を確認して、必要なら /track で登録し直してください。"
        )
    if result == "send_error":
        return (
            f"監視を開始しました: `{cleaned}`\n"
            "⚠️ 通知を送信できませんでした。Botがこのチャンネルに投稿できるか、"
            "権限を確認してください（監視は続けます）。"
        )
    if result == "error":
        return (
            f"監視を開始しました: `{cleaned}`\n"
            "⚠️ 現在の状況を取得できませんでした（監視は続けます）。"
        )
    dest = "DM" if wants_dm(entry) else "このチャンネル"
    return (
        f"監視を開始しました: `{cleaned}`\n"
        f"{dest}に {CHECK_MINUTES} 分ごとにチェックして、変化があったときだけ通知します。"
        f"（現在あなたは {sum(1 for e in trackings.values() if e.get('owner_id') == interaction.user.id)} 件を追跡中）"
    )


# ---- ポップアップ（モーダル） ----
class TrackingModal(discord.ui.Modal, title="日本郵便 追跡番号の入力"):
    number = discord.ui.TextInput(
        label="追跡番号（お問い合わせ番号）",
        placeholder="例: 123456789012 / EMSは AA123456789JP",
        min_length=11,
        max_length=20,
        required=True,
    )
    memo = discord.ui.TextInput(
        label="メモ（任意・荷物の名前など）",
        placeholder="例: 自分のAmazon / 友達への発送分 など",
        max_length=50,
        required=False,
    )

    async def on_submit(self, interaction: discord.Interaction):
        cleaned = clean_number(self.number.value)
        if not TRACKING_RE.match(cleaned):
            await interaction.response.send_message(
                "追跡番号の形式が違うみたいです。"
                "国内は11〜12桁の数字、国際は英字2+数字9+英字2で入力してください。",
                ephemeral=True,
            )
            return

        error = registration_error(interaction, cleaned)
        if error:
            await interaction.response.send_message(error, ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        msg = await register_and_check(interaction, cleaned, self.memo.value.strip())
        await interaction.followup.send(msg, ephemeral=True)


class TrackPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="追跡番号を入力",
        style=discord.ButtonStyle.primary,
        emoji="📦",
        custom_id="jp_track_input",
    )
    async def open_modal(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(TrackingModal())

    @discord.ui.button(
        label="通知先の切り替え（チャンネル/DM）",
        style=discord.ButtonStyle.secondary,
        emoji="🔔",
        custom_id="jp_track_notify_toggle",
    )
    async def toggle_notify(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        pref = user_prefs.setdefault(str(interaction.user.id), {})
        pref["dm"] = not pref.get("dm", False)
        save_state()
        dest = "DM" if pref["dm"] else "登録したチャンネル"
        await interaction.response.send_message(
            f"あなたの荷物の通知先を **{dest}** にしました。", ephemeral=True
        )


# ---- Bot本体 ----
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


@tree.error
async def on_tree_error(
    interaction: discord.Interaction, error: app_commands.AppCommandError
):
    if isinstance(error, app_commands.CommandOnCooldown):
        try:
            await interaction.response.send_message(
                f"少し待ってからもう一度お試しください（あと約 {error.retry_after:.0f} 秒）。",
                ephemeral=True,
            )
        except Exception:
            pass
        return
    traceback.print_exception(type(error), error, error.__traceback__)


@tree.command(name="track", description="追跡番号を入力して日本郵便の監視を開始（複数可）")
async def track_command(interaction: discord.Interaction):
    await interaction.response.send_modal(TrackingModal())


@tree.command(name="panel", description="追跡番号入力ボタンのパネルを表示")
async def panel_command(interaction: discord.Interaction):
    await interaction.response.send_message(
        "追跡したい荷物ができたら、このボタンから番号を入力してください。何件でも登録できます。",
        view=TrackPanelView(),
    )


@tree.command(name="status", description="自分が追跡中の荷物を確認")
async def status_command(interaction: discord.Interaction):
    mine = [
        (n, e)
        for n, e in trackings.items()
        if e.get("owner_id") == interaction.user.id
    ]
    if not mine:
        text = "あなたが追跡中の荷物はありません。/track から登録してください。"
    else:
        lines = [f"あなたは {len(mine)} 件を追跡中です。"]
        for n, e in mine:
            memo = f"（{e['memo']}）" if e.get("memo") else ""
            status = e.get("last_status") or "まだ状況を取得していません"
            lines.append(f"・`{n}`{memo}: {status}")
        text = "\n".join(lines)
    await interaction.response.send_message(text, ephemeral=True)


@tree.command(name="list", description="このサーバーで追跡中の荷物を一覧表示")
async def list_command(interaction: discord.Interaction):
    here = [
        (n, e)
        for n, e in trackings.items()
        if e.get("guild_id") == interaction.guild_id
    ]
    if not here:
        text = "このサーバーで追跡中の荷物はありません。"
    else:
        lines = [f"このサーバーでは {len(here)} 件を追跡中です。"]
        for n, e in here:
            # 他人の番号とメモは伏せる（自分の分は /status で全文が見られる）。
            # last_status には担当局も入っているので、状態の部分だけ出す。
            status = (e.get("last_status") or "未取得").split("（")[0]
            lines.append(
                f"・`{mask_number(n)}` 登録者: {e.get('owner_name') or '不明'} / {status}"
            )
        text = "\n".join(lines)
    await interaction.response.send_message(text, ephemeral=True)


# ---- 写真からの番号読み取り ----
_FULLWIDTH_TABLE = str.maketrans(
    "０１２３４５６７８９ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ",
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ",
)


def _scan_numbers(chunk: str, strong: list[str], weak: list[str]) -> None:
    """テキスト片から番号候補を集める。0始まりの数字は weak（弱い候補）行き。"""

    def add_to(lst: list[str], candidate: str) -> None:
        if (
            TRACKING_RE.match(candidate)
            and candidate not in strong
            and candidate not in weak
        ):
            lst.append(candidate)

    squashed = re.sub(r"[\s\-ー－]", "", chunk).upper()
    # 前後に英数字が続く場合は、長い文字列の一部なので候補にしない（境界条件）
    for m in re.finditer(r"(?<![A-Z0-9])[A-Z]{2}[0-9]{9}[A-Z]{2}(?![A-Z0-9])", squashed):
        add_to(strong, m.group(0))
    for m in re.finditer(r"(?<![0-9])[0-9]{11,12}(?![0-9])", squashed):
        # 0始まりは携帯・フリーダイヤル等の電話番号の可能性が高いため、
        # 自動登録の対象にはせず弱い候補として呼び出し側に返す
        # （手入力の /track には影響しない）
        add_to(weak if m.group(0).startswith("0") else strong, m.group(0))


def _extract_all(text: str) -> tuple[list[str], list[str]]:
    """(強い候補, 弱い候補) を返す。

    まず行ごとに探す（電話番号など別行の数字とくっついて誤検出するのを防ぐ）。
    行単位で強い候補が見つからなかった場合だけ、全体をつなげて探す
    （番号の途中で改行が入った読み取りへの保険）。
    """
    strong: list[str] = []
    weak: list[str] = []
    normalized = text.translate(_FULLWIDTH_TABLE)
    for line in normalized.splitlines():
        _scan_numbers(line, strong, weak)
    if not strong:
        _scan_numbers(normalized, strong, weak)
    return strong, weak


def extract_tracking_numbers(text: str) -> list[str]:
    """OCRテキストから追跡番号らしい文字列を抜き出す（強い候補のみ・重複なし・出現順）。"""
    strong, _ = _extract_all(text)
    return strong


def _ocr_variants(image, target_width: int = 1200):
    """OCRの前処理バリエーション（グレースケール拡大・二値化）を作る。"""
    from PIL import Image, ImageOps

    base = image.convert("L")
    w, h = base.size
    if w > 2000:
        # 大きすぎる写真は処理が重くなるので、先に幅2000pxまで縮小する
        base = base.resize((2000, max(1, round(h * 2000 / w))), Image.LANCZOS)
        w, h = base.size
    if h > 2000:
        # 縦に極端に長い写真も同様に縮小する（この後の拡大で高さが
        # 膨らみすぎて、メモリを圧迫しないように）
        base = base.resize((max(1, round(w * 2000 / h)), 2000), Image.LANCZOS)
        w, h = base.size
    # 小さい写真は文字が潰れて読めないので、幅 target_width pxを目安に拡大する
    scale = max(1.0, min(6.0, target_width / max(w, 1)))
    if scale > 1.0:
        base = base.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        w, h = base.size
        if h > 6000:
            base = base.resize(
                (max(1, round(w * 6000 / h)), 6000), Image.LANCZOS
            )
    gray = ImageOps.expand(ImageOps.autocontrast(base), border=20, fill=255)
    binary = gray.point(lambda p: 255 if p > 150 else 0)
    return gray, binary


def _otsu_binary(gray):
    """グレースケール画像を大津の方法で求めた閾値で二値化する。

    暖色照明など、固定閾値（150）では文字が潰れる写真への保険。
    """
    hist = gray.histogram()
    total = sum(hist)
    if total == 0:
        return gray.point(lambda p: 255 if p > 150 else 0)
    sum_all = sum(i * v for i, v in enumerate(hist))
    sum_b = 0
    w_b = 0
    max_var = -1.0
    threshold = 150
    for i, v in enumerate(hist):
        w_b += v
        if w_b == 0:
            continue
        w_f = total - w_b
        if w_f == 0:
            break
        sum_b += i * v
        m_b = sum_b / w_b
        m_f = (sum_all - sum_b) / w_f
        var = w_b * w_f * (m_b - m_f) ** 2
        if var > max_var:
            max_var = var
            threshold = i
    return gray.point(lambda p: 255 if p > threshold else 0)


# OCR 実行中の作業領域（スレッドローカル）。ocr_image が立て、
# _ocr_pass_texts が候補ごとの一致回数と出どころ（通常パスか）を記録する。
# scan_command は OCR 完了後に _last_ocr_detail で結果を受け取る
# （/scan の OCR はセマフォで直列化されているため、競合しない）。
_ocr_ctx = threading.local()
_last_ocr_detail: dict | None = None


def _record_ocr_text(txt: str) -> None:
    """Tesseract 1回ぶんの結果から候補を数える（信頼度の集計用）。

    まず行単位で探す。1回の中で行単位の候補が1件も無かった時だけ、
    その1回ぶんのテキストを結合して探す（番号の途中で改行が入った
    読み取りへの保険）。結合は1回の中で閉じるため、パスをまたいだ
    断片同士がくっついた偽候補は数えられない。
    """
    if not getattr(_ocr_ctx, "active", False):
        return
    strong: list[str] = []
    weak: list[str] = []
    normalized = txt.translate(_FULLWIDTH_TABLE)
    for line in normalized.splitlines():
        _scan_numbers(line, strong, weak)
    if not strong:
        _scan_numbers(normalized, strong, weak)
    for candidate in strong:
        _ocr_ctx.counts[candidate] = _ocr_ctx.counts.get(candidate, 0) + 1
        _ocr_ctx.sources.setdefault(candidate, set()).add(_ocr_ctx.stage)


def _ocr_pass_texts(image, target_width: int, extended: bool) -> str:
    """前処理した画像に複数のモードでOCRをかけ、結果をまとめて返す。

    1モードでも読めれば番号を拾えるようにするための束ね読み。
    extended=True では、大津二値化と psm 11 の数字ホワイトリストも加える。
    各呼び出しにはタイムアウトを付け、OCR全体の締切を過ぎたら
    残りのモードは試さない。
    """
    import pytesseract

    gray, binary = _ocr_variants(image, target_width)
    passes = [
        (binary, "--psm 6"),
        (binary, "--psm 11"),
        (gray, "--psm 6 -c tessedit_char_whitelist=0123456789-"),
    ]
    if extended:
        otsu = _otsu_binary(gray)
        passes += [
            (otsu, "--psm 6"),
            (otsu, "--psm 11"),
            (gray, "--psm 11 -c tessedit_char_whitelist=0123456789-"),
        ]
    texts: list[str] = []
    for img, config in passes:
        deadline = getattr(_ocr_ctx, "deadline", None)
        if deadline is not None and time.monotonic() > deadline:
            _ocr_ctx.cut = True
            break
        try:
            txt = pytesseract.image_to_string(
                img, lang="eng", config=config, timeout=OCR_CALL_TIMEOUT
            )
        except TypeError:
            # timeout 引数に未対応の古い pytesseract では付けずに読み直す
            try:
                txt = pytesseract.image_to_string(img, lang="eng", config=config)
            except Exception:
                continue
        except Exception:
            continue
        texts.append(txt)
        _record_ocr_text(txt)
    return "\n".join(texts)


def ocr_image(data: bytes) -> str:
    """画像バイト列をOCRする。pytesseract / Pillow が無い場合は RuntimeError。

    前処理した画像を複数のモードで読み、結果をまとめて返す。
    1モードでも読めれば番号を拾えるようにするため。
    通常の読み取りで候補が見つからない場合は、追加パスと回転・反転も
    試す。あわせて、候補ごとの一致回数と「通常パスで出たか」を
    _last_ocr_detail に残す（呼び出し側の信頼度判定用）。
    OCR全体には締切（OCR_DEADLINE_SECONDS）があり、過ぎたら
    その時点までの結果を返す。
    """
    global _last_ocr_detail
    try:
        import pytesseract
        from PIL import Image, ImageOps
    except ImportError as e:
        raise RuntimeError(
            "OCR用のライブラリが入っていません。"
            "pip install pytesseract pillow と、Tesseract 本体のインストールが必要です。"
        ) from e
    if not shutil.which("tesseract"):
        # Windowsの既定インストール先にあれば、PATH未設定でも使えるようにする
        default_exe = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
        if default_exe.exists():
            pytesseract.pytesseract.tesseract_cmd = str(default_exe)
        else:
            # 本体が無いまま全パスを空振りして「読み取れませんでした」に
            # なる前に、最初に1回だけ確認して案内を出す
            raise RuntimeError(
                "Tesseract 本体が見つかりません。"
                "Tesseract 本体のインストールが必要です"
                "（Windows: UB Mannheim 版インストーラ / Mac: brew install tesseract / "
                "Linux: apt install tesseract-ocr）。"
            )
    # 展開すると巨大になる画像（解凍爆弾）への対策:
    # Pillow の上限も絞ったうえで、読み込む前に画素数を自分でも確認する
    Image.MAX_IMAGE_PIXELS = 25_000_000
    try:
        opened = Image.open(io.BytesIO(data))
        if opened.width * opened.height > 25_000_000:
            return ""
        opened.load()
    except Image.DecompressionBombError:
        return ""
    # スマホ写真の EXIF 回転情報を反映する（横向きのまま読まないように）
    image = ImageOps.exif_transpose(opened)
    # 回転・反転は元解像度のコピーを作るため、先に最大2000pxへ縮小して
    # おく（この後の前処理でも結局2000pxへ縮められる寸法に揃える。
    # メモリのピークと回転にかかる時間を抑えるため）
    if image.width > 2000 or image.height > 2000:
        scale = 2000 / max(image.width, image.height)
        image = image.resize(
            (max(1, round(image.width * scale)),
             max(1, round(image.height * scale))),
            Image.LANCZOS,
        )

    _ocr_ctx.active = True
    _ocr_ctx.counts = {}
    _ocr_ctx.sources = {}
    _ocr_ctx.stage = "initial"
    _ocr_ctx.deadline = time.monotonic() + OCR_DEADLINE_SECONDS
    _ocr_ctx.cut = False
    _ocr_started = time.monotonic()

    def run(img, target_width: int, extended: bool, stage: str) -> str:
        if time.monotonic() > _ocr_ctx.deadline:
            _ocr_ctx.cut = True
            return ""
        _ocr_ctx.stage = stage
        return _ocr_pass_texts(img, target_width, extended)

    try:
        text = run(image, 1200, False, "initial")
        if extract_tracking_numbers(text):
            # 候補が見つかっても、写真が斜め・逆光などで数字が化けていると
            # 誤読の候補だけが残ることがある。同じ向きの追加パスと、
            # 実績のある2方向（180度と時計回り90度）の追加読み取りも
            # 混ぜて返し、呼び出し側の日本郵便の履歴照合で正しい候補を
            # 選べるようにする。
            text += "\n" + run(image, 2400, True, "extra")
            for angle in (180, -90):
                rotated = image.rotate(angle, expand=True)
                text += "\n" + run(rotated, 2400, True, "extra")
            return text
        # 通常の読み取りで候補が見つからなかった場合は、全方向の追加
        # 読み取りを混ぜて返す。途中で誤読候補が出ても打ち切らない
        # （誤読の陰で正解が埋もれ、正解側の読み取りに届かなくなるため。
        # 正しい候補は呼び出し側の履歴照合と利用者の目で選ばれる）。
        # EXIF に回転情報が無い（共有・転送で消えた）写真でも拾えるように。
        text += "\n" + run(image, 2400, True, "extra")
        for angle in (180, -90, 90):
            rotated = image.rotate(angle, expand=True)
            text += "\n" + run(rotated, 2400, True, "extra")
        # 鏡越し・反転保存された写真への対応（左右反転して読み直す）。
        # 向きの網羅が先、保険のリトライは後（締切で打ち切られても、
        # 反転写真だけが拾えなくなる並びにしないため）
        mirrored = ImageOps.mirror(image)
        text += "\n" + run(mirrored, 2400, True, "extra")
        for angle in (180, -90, 90):
            rotated = mirrored.rotate(angle, expand=True)
            text += "\n" + run(rotated, 2400, True, "extra")
        # 写真によっては読み取りが境界線上にあり、同じ条件でも読めたり
        # 読めなかったりする。前処理の違う通常パスでもう一度回転読み取りを
        # して、拾える確率を上げる。
        for angle in (180, -90, 90):
            rotated = image.rotate(angle, expand=True)
            text += "\n" + run(rotated, 1200, False, "extra")
        return text
    finally:
        _last_ocr_detail = {
            "counts": dict(_ocr_ctx.counts),
            "initial": {
                c for c, stages in _ocr_ctx.sources.items()
                if "initial" in stages
            },
        }
        _ocr_ctx.active = False
        _ocr_ctx.deadline = None
        # 締切（300秒）の妥当性を実測で判断するための記録
        print(
            f"OCR所要時間: {time.monotonic() - _ocr_started:.1f}秒"
            f" / 候補 {len(_ocr_ctx.counts)} 件"
            + (" / 締切で打ち切り" if getattr(_ocr_ctx, "cut", False) else "")
        )


@tree.command(name="history", description="自分の配達済み履歴を確認")
async def history_command(interaction: discord.Interaction):
    mine = [h for h in history_log if h.get("owner_id") == interaction.user.id]
    if not mine:
        text = "あなたの配達済み履歴はまだありません。"
    else:
        lines = ["あなたの配達済み履歴（新しい順・最大10件）です。"]
        for h in mine[-10:][::-1]:
            memo = f"（{h['memo']}）" if h.get("memo") else ""
            lines.append(
                f"・`{h['number']}`{memo}: {h['status']} / {h.get('finished_at', '')}"
            )
        text = "\n".join(lines)
    await interaction.response.send_message(text, ephemeral=True)


class ScanRegisterView(discord.ui.View):
    """/scan で提示だけになった候補を、ボタンでそのまま登録するためのビュー。

    履歴がまだ無い本物の荷物でも /track で手入力し直さずに済むようにする。
    押せるのは /scan を実行した本人だけ（custom_id に実行者のIDを含む）。
    """

    def __init__(self, numbers: list[str], owner_id: int, memo: str = ""):
        super().__init__(timeout=600)
        self.owner_id = owner_id
        self.memo = memo
        for number in list(numbers)[:25]:
            button = discord.ui.Button(
                label=f"{number} を登録",
                style=discord.ButtonStyle.primary,
                custom_id=f"jp_scan_reg:{number}:{owner_id}",
            )
            button.callback = self._make_callback(number)
            self.add_item(button)

    def _make_callback(self, number: str):
        async def _callback(interaction: discord.Interaction):
            if interaction.user.id != self.owner_id:
                await interaction.response.send_message(
                    "このボタンは /scan を実行した本人だけが押せます。",
                    ephemeral=True,
                )
                return
            await interaction.response.defer(ephemeral=True)
            error = registration_error(interaction, number)
            if error:
                await interaction.followup.send(error, ephemeral=True)
                return
            msg = await register_and_check(interaction, number, self.memo)
            await interaction.followup.send(msg, ephemeral=True)
            for child in self.children:
                child.disabled = True
            try:
                await interaction.message.edit(view=self)
            except Exception:
                pass

        return _callback


@tree.command(name="scan", description="伝票の写真から追跡番号を読み取って登録")
@app_commands.describe(image="追跡番号が写った写真", memo="メモ（任意）")
@app_commands.checks.cooldown(1, 30.0, key=lambda i: i.user.id)
async def scan_command(
    interaction: discord.Interaction, image: discord.Attachment, memo: str = ""
):
    if not (image.content_type or "").startswith("image/"):
        await interaction.response.send_message(
            "画像ファイルを指定してください。", ephemeral=True
        )
        return
    if image.size and image.size > 10 * 1024 * 1024:
        await interaction.response.send_message(
            "画像が大きすぎます（上限10MB）。縮小してから試してください。",
            ephemeral=True,
        )
        return
    att_w = getattr(image, "width", None)
    att_h = getattr(image, "height", None)
    if att_w and att_h and att_w * att_h > 25_000_000:
        # ダウンロード前に解像度でも止める（展開時のメモリ使用量対策）
        await interaction.response.send_message(
            "画像の解像度が大きすぎます。縮小してから試してください。",
            ephemeral=True,
        )
        return
    await interaction.response.defer(ephemeral=True)
    # OCRは重く、クールダウン（30秒）より長くかかることがあるため、
    # 同時に1件だけ実行する（Tesseractの並列実行を防ぐ）。
    # 信頼度の集計（_last_ocr_detail）もこの区間の中で受け取る。
    global _last_ocr_detail
    if interaction.user.id in _scan_active_users:
        await interaction.followup.send(
            "あなたの写真は既に読み取り中（または待機中）です。"
            "終わるまでお待ちください。",
            ephemeral=True,
        )
        return
    _scan_active_users.add(interaction.user.id)
    try:
        wait_msg = None
        if _scan_semaphore.locked():
            # 前の人の OCR が終わるまで待つことがあるため、先に一言返す。
            # 通知の失敗でスキャン自体は止めない
            try:
                wait_msg = await interaction.followup.send(
                    "前の写真を読み取り中です。"
                    "終わり次第、あなたの写真を読み取ります。",
                    ephemeral=True,
                )
            except Exception:
                wait_msg = None
        try:
            await asyncio.wait_for(
                _scan_semaphore.acquire(),
                timeout=OCR_WAIT_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            await interaction.followup.send(
                "現在 /scan が混み合っています。"
                "少し時間をおいてから試してください。",
                ephemeral=True,
            )
            return
        try:
            if wait_msg is not None:
                # 待機通知は役割を終えたので消す（古い表示を残さない）
                try:
                    await wait_msg.delete()
                except Exception:
                    pass
            _last_ocr_detail = None
            try:
                data = await image.read()
                text = await asyncio.to_thread(ocr_image, data)
            except RuntimeError as e:
                # OCR由来の RuntimeError は利用者向けの文面なのでそのまま出す
                # （それ以外の RuntimeError は下の汎用文面に倒す）
                await interaction.followup.send(str(e), ephemeral=True)
                return
            ocr_detail = _last_ocr_detail
        finally:
            _scan_semaphore.release()
    except Exception as e:
        # 例外の詳細（パス等）は利用者へ出さず、コンソールにだけ残す
        print(f"/scan の処理エラー: {e!r}")
        await interaction.followup.send(
            "写真を読み取れませんでした。時間をおいて試すか、/track で手入力してください。",
            ephemeral=True,
        )
        return
    finally:
        _scan_active_users.discard(interaction.user.id)

    _, weak = _extract_all(text)
    if ocr_detail is not None:
        # 候補の元は集計（counts）のキーにする。全パスをつないだ
        # テキストから候補を作ると、パスをまたいだ断片同士が
        # くっついた偽候補が混ざるため（集計は1回の読み取りの中で
        # 閉じているので、構造的に混ざらない）。
        # 候補ごとに信頼度を付ける: 通常パスで出た候補か、2回以上の
        # 読み取りで一致した候補だけを「信頼できる候補」とする。
        # 一致回数の多い順に並べ替え、正解が照会上限の外へ
        # 押し出されにくくする。
        counts = ocr_detail.get("counts", {})
        initial = ocr_detail.get("initial", set())
        candidates = list(counts.keys())
        order = {c: i for i, c in enumerate(candidates)}
        # 一致回数で並べる。通常パスで出た候補は +1 ぶん重みを付ける
        candidates.sort(
            key=lambda c: (
                -(counts.get(c, 0) + (1 if c in initial else 0)), order[c]
            )
        )
        trusted = {
            c for c in candidates
            if counts.get(c, 0) >= 2 or c in initial
        }
    else:
        # ocr_image が差し替えられている場合など、集計が無いときは
        # 従来どおり結合テキストから候補を作り、全候補を信頼できる
        # ものとして扱う
        candidates, weak = _extract_all(text)
        trusted = set(candidates)

    def pending_of(numbers: list[str]) -> list[str]:
        """保留プールへ入れてよい候補だけを返す（信頼できる候補のみ）。"""
        return [n for n in numbers if n in trusted]
    # 候補が大量に写っていても、扱うのは上限まで（照会・保留・ボタンの負荷対策）
    candidates = candidates[:MAX_SCAN_CANDIDATES]
    weak = weak[:MAX_SCAN_CANDIDATES]
    if candidates:
        # 写真では同じ行の数字同士がくっついて誤った候補になることがあるため、
        # 日本郵便に履歴が実在する候補だけを採用する。
        # 履歴が無い候補は自動登録せず提示のみ（発送直後は履歴が出ないこともある）。
        # 照会は先頭5件まで（OCRノイズで候補が大量に出た場合の負荷対策）。
        checked = candidates[:5]
        extras = candidates[5:]
        verified: list[str] = []
        errors = 0
        for c in checked:
            try:
                if await asyncio.to_thread(fetch_latest, c) is not None:
                    verified.append(c)
            except Exception:
                errors += 1
        if not verified:
            if errors == len(checked):
                kept = pending_of(checked + extras)
                if kept:
                    add_pending_candidates(
                        interaction, kept, memo.strip(), checked_now=False,
                    )
                    msg = (
                        "日本郵便への照会でエラーが発生しました。"
                        "候補は保留したので、接続できるようになったら自動で確認します。"
                    )
                else:
                    msg = (
                        "日本郵便への照会でエラーが発生しました。"
                        "読み取りの一致が弱い候補しか無かったため、保留はしませんでした。"
                        "時間をおいて試すか、/track で手入力してください。"
                    )
                await interaction.followup.send(msg, ephemeral=True)
                return
            listed = " / ".join(f"`{c}`" for c in checked)
            kept_checked = pending_of(checked)
            if kept_checked:
                add_pending_candidates(
                    interaction, kept_checked, memo.strip(), checked_now=True
                )
            if extras:
                kept_extras = pending_of(extras)
                if kept_extras:
                    add_pending_candidates(
                        interaction, kept_extras, memo.strip(),
                        checked_now=False,
                    )
            if kept_checked:
                tail = "このままにしても、履歴が出たら自動で登録します（最長2日間、時々確認します）。"
            else:
                tail = "読み取りの一致が弱い候補のため、自動の後追い確認はしません。"
            await interaction.followup.send(
                f"番号らしきものが見つかりました: {listed}\n"
                "ただし日本郵便に履歴が確認できなかったため、自動登録はしませんでした。\n"
                "本物の荷物なら、下のボタンでそのまま登録できます。\n"
                f"{tail}",
                view=ScanRegisterView(checked, interaction.user.id, memo.strip()),
                ephemeral=True,
            )
            return
        unverified = [c for c in checked if c not in verified]
        if unverified:
            # 照会したが履歴が無かった候補のうち、信頼できるものは
            # 捨てず、保留で後追い確認する
            # （写真に複数の伝票が写っていた場合の2件目など）
            kept_unverified = pending_of(unverified)
            if kept_unverified:
                add_pending_candidates(
                    interaction, kept_unverified, memo.strip(), checked_now=True
                )
        if extras:
            # 照会上限（5件）から漏れた候補も同様に、信頼できるものだけ
            # 保留で後追い確認する
            kept_extras = pending_of(extras)
            if kept_extras:
                add_pending_candidates(
                    interaction, kept_extras, memo.strip(), checked_now=False
                )
        candidates = verified
    if not candidates:
        if weak:
            listed = " / ".join(f"`{c}`" for c in weak)
            await interaction.followup.send(
                f"番号らしきものが見つかりました: {listed}\n"
                "0始まりのため電話番号の可能性があります。自動登録はしませんでした。\n"
                "追跡番号で間違いなければ、下のボタンで登録できます。",
                view=ScanRegisterView(weak, interaction.user.id, memo.strip()),
                ephemeral=True,
            )
            return
        await interaction.followup.send(
            "写真から追跡番号を読み取れませんでした。"
            "番号が大きく写るように撮り直すか、/track で手入力してください。",
            ephemeral=True,
        )
        return
    if len(candidates) > 1:
        listed = " / ".join(f"`{c}`" for c in candidates)
        await interaction.followup.send(
            f"番号らしきものが複数見つかりました: {listed}\n"
            "当てはまる番号を下のボタンで登録してください。",
            view=ScanRegisterView(candidates, interaction.user.id, memo.strip()),
            ephemeral=True,
        )
        return

    cleaned = candidates[0]
    error = registration_error(interaction, cleaned)
    if error:
        await interaction.followup.send(error, ephemeral=True)
        return
    msg = await register_and_check(interaction, cleaned, memo.strip())
    await interaction.followup.send(
        f"写真から `{cleaned}` を読み取りました。\n{msg}", ephemeral=True
    )


async def stop_number_autocomplete(
    interaction: discord.Interaction, current: str
) -> list[app_commands.Choice[str]]:
    choices = []
    for n, e in trackings.items():
        if not can_manage(interaction, e):
            continue
        if e.get("owner_id") == interaction.user.id:
            label = f"{e['memo']} ({n})" if e.get("memo") else n
        else:
            # 他人の荷物は、候補の表示でも番号をマスクしメモも出さない
            label = mask_number(n)
        if current and current not in n and current not in (e.get("memo") or ""):
            continue
        choices.append(app_commands.Choice(name=label[:100], value=n))
    return choices[:25]


@tree.command(name="stop", description="追跡を止める（番号を省略すると自分の全件を停止）")
@app_commands.describe(number="止めたい追跡番号（省略可）")
async def stop_command(
    interaction: discord.Interaction, number: str | None = None
):
    if number:
        cleaned = clean_number(number)
        # 取得から削除までをロックの中で行い、チェック中の荷物を
        # 止めた直後に通知が飛ぶ競合を防ぐ
        async with _check_lock:
            entry = trackings.get(cleaned)
            can = entry is not None and can_manage(interaction, entry)
            # 保留中の候補も一緒に取り消す（止めた番号が保留プールから
            # 自動登録で復活しないように）。取り消せるのは自分の保留と、
            # その荷物を止める権限がある場合だけ。
            removed_pending = False
            kept = []
            for p in pending_scans:
                if p.get("number") == cleaned and (
                    p.get("owner_id") == interaction.user.id or can
                ):
                    removed_pending = True
                    continue
                kept.append(p)
            if removed_pending:
                pending_scans[:] = kept
            if entry is None:
                if removed_pending:
                    msg = f"`{cleaned}` の保留中の候補を取り消しました。"
                else:
                    msg = f"`{cleaned}` は追跡されていません。"
            elif not can:
                msg = "その荷物は登録した本人かサーバー所有者だけが止められます。"
            else:
                trackings.pop(cleaned, None)
                msg = f"`{cleaned}` の追跡を止めました。"
            if removed_pending or can:
                save_state()
        await interaction.response.send_message(msg, ephemeral=True)
    else:
        async with _check_lock:
            mine = [
                n
                for n, e in trackings.items()
                if e.get("owner_id") == interaction.user.id
            ]
            for n in mine:
                trackings.pop(n, None)
            kept = [
                p
                for p in pending_scans
                if p.get("owner_id") != interaction.user.id
            ]
            removed_pending = len(kept) != len(pending_scans)
            if removed_pending:
                pending_scans[:] = kept
            save_state()
        msg = f"あなたの追跡を {len(mine)} 件すべて止めました。"
        if removed_pending:
            msg += "（保留中の候補も取り消しました）"
        await interaction.response.send_message(msg, ephemeral=True)
    # 監視ループは止めない（荷物ゼロの間は空回りするだけ）


stop_command.autocomplete("number")(stop_number_autocomplete)


_commands_synced = False


async def sync_commands():
    """参加中の全サーバーへ即時同期する（グローバル同期の最大1時間待ちを回避）。"""
    global _commands_synced
    if _commands_synced:
        return

    if not client.guilds:
        print("警告: Botがどのサーバーにも参加していません。先にサーバーへ招待してください。")
        _commands_synced = True
        return

    all_ok = True
    for guild in client.guilds:
        try:
            tree.copy_global_to(guild=guild)
            synced = await tree.sync(guild=guild)
            names = ", ".join(f"/{c.name}" for c in synced)
            print(f"[{guild.name}] コマンド同期完了: {names}")
        except discord.Forbidden:
            all_ok = False
            print(
                f"[{guild.name}] コマンド同期が拒否されました。"
                "招待時のスコープに applications.commands が入っていません。"
                "OAuth2 URL Generator で bot + applications.commands を選んで招待し直してください。"
            )
        except Exception as e:
            all_ok = False
            print(f"[{guild.name}] コマンド同期エラー（次回接続時に再試行します）: {e}")
    _commands_synced = all_ok


@client.event
async def on_guild_join(guild):
    if not guild_allowed(guild.id):
        print(f"許可リストに無いサーバー（{guild.name}）から退出します")
        await guild.leave()
        return
    global _commands_synced
    _commands_synced = False
    await sync_commands()


async def heal_orphan_entries() -> None:
    """登録者もサーバーも不明な旧データに、通知先チャンネルから
    所属サーバーを復元する。復元できないものは Bot所有者の復旧対象になる。"""
    changed = False
    for entry in trackings.values():
        if entry.get("owner_id") is not None or entry.get("guild_id") is not None:
            continue
        channel_id = entry.get("channel_id")
        if not channel_id:
            continue
        try:
            channel = client.get_channel(channel_id) or (
                await client.fetch_channel(channel_id)
            )
        except Exception:
            continue
        guild = getattr(channel, "guild", None)
        if guild is not None:
            entry["guild_id"] = guild.id
            changed = True
    if changed:
        save_state()


@client.event
async def on_ready():
    global bot_owner_id, _panel_view_added
    print(f"Logged in as {client.user}")
    try:
        info = await client.application_info()
        if getattr(info, "team", None) is not None:
            bot_owner_id = info.team.owner_id
        elif info.owner is not None:
            bot_owner_id = info.owner.id
    except Exception:
        pass
    await heal_orphan_entries()
    if GUILD_ALLOWLIST:
        # 許可リスト設定時は、リスト外のサーバーから退出する
        for g in list(client.guilds):
            if not guild_allowed(g.id):
                print(f"許可リストに無いサーバー（{g.name}）から退出します")
                await g.leave()
    joined = ", ".join(f"{g.name}" for g in client.guilds) or "（なし）"
    print(f"参加中のサーバー: {joined}")
    print(f"追跡中: {len(trackings)} 件")
    if not _panel_view_added:
        client.add_view(TrackPanelView())
        _panel_view_added = True
    await sync_commands()
    print("準備完了。Discordで /track と打ってみてください。")
    # 監視ループは常時回す（荷物ゼロのときは空回りするだけ）
    if not check_tracking.is_running():
        check_tracking.start()


if __name__ == "__main__":
    client.run(TOKEN)

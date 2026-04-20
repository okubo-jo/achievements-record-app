# render_templateはHTMLファイルを表示するための関数
# requestはユーザーからの入力を受け取る
# redirectは別のページへ移動させる
# url_forはURLを自動で作る
# datetimeを使って、今日の日付と現在の時間を取得できる
from flask import Flask, render_template, request,redirect , url_for
import sqlite3
from datetime import datetime

# Flaskアプリの本体・土台を作成する
# __name__はこのファイル自身を意味する
app = Flask(__name__)
DB_NAME = "achievements.db"

# データベース接続を作る関数を定義する処理
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)    # SQLiteに接続
    conn.row_factory = sqlite3.Row     #rowは「列」factoryでデータの作り方を設定する
    return conn

# データベースの初期設定を行う処理
# executeはSQLクエリ(挿入、取得、更新、削除)を実行するメソッド
def init_db():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS achievements (    
            id INTEGER PRIMARY KEY AUTOINCREMENT,    
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            hours INTEGER NOT NULL DEFAULT 0,
            minutes INTEGER NOT NULL DEFAULT 0,
            memo TEXT,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()    #変更を確定する。これがないと保存されない。
    conn.close()     #データベースとの接続を終了する。これを書かないと無駄にメモリを使ってしまう。

# Webアプリの「トップページ（/）」の処理を定義する。データベースから記録を取得し、合計時間を計算してHTMLに渡す。
# 直近に記録したものが一番上にくるようにする
@app.route("/")
def index():
    conn = get_db_connection()
    achievements = conn.execute(
        "SELECT * FROM achievements ORDER BY date DESC, id DESC"    #DESC(Descending)は降順（新しい順）という意味
    ).fetchall()                                                    # fetchall()は全てのデータをリストとして取得する

    # 合計時間を取得する
    # COALESCEでNULL値だった場合は0に置き換える
    total = conn.execute("""
        SELECT
            COALESCE(SUM(hours), 0) AS total_hours,
            COALESCE(SUM(minutes), 0) AS total_minutes  
        FROM achievements
    """).fetchone()

    conn.close()

    # SQLで取得した値をPython変数に代入する
    total_hours = total["total_hours"]
    total_minutes = total["total_minutes"]

    #分が60分以上になったら時間を繰り上げる
    total_hours += total_minutes // 60       # // 60は分を60で割って小数点以下を切り捨て
    total_minutes = total_minutes % 60       # % 60は60で割った余り（残った分）を計算

    #HTMLにデータを渡す
    return render_template(
        "index.html",
        achievements = achievements,
        total_hours=total_hours,
        total_minutes=total_minutes
    )

# データの追加処理
@app.route("/add", methods=["POST"])    # 入力されたデータを受け取り、データベースに送信して保存する
def add():
    date = request.form.get("date", "").strip()          # .strip()で入力された文字列の空白を削除する（無くす）
    category = request.form.get("category", "").strip()  # ""や"0"は初期値
    hours = request.form.get("hours", "0").strip()
    minutes = request.form.get("minutes", "0").strip()
    memo = request.form.get("memo", "").strip()

    #日付の入力がなければ（記入漏れ）の場合は今日にする
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    if not category:
        category = "未分類"

    # 文字列入力を数値に変換する
    try:
        hours = int(hours) if hours else 0
        minutes = int(minutes) if minutes else 0
    except ValueError:
        hours = 0
        minutes = 0

    #マイナス値の入力を防ぐ
    if hours < 0:
        hours = 0
    if minutes < 0:
        minutes = 0

    hours += minutes // 60
    minutes = minutes % 60

    # データベースに保存する
    # ?は後から値を入れるためのもの
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO achievements (date, category, hours, minutes, memo, created_at)
        VALUES (?, ?, ?, ?, ?, ?)    
        """, (
            date,
            category,
            hours,
            minutes,
            memo,
            datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    ))
    conn.commit()
    conn.close()

    #データ入力後にトップページに戻る
    return redirect(url_for("index"))

@app.route("/delete/<int:achievement_id>", methods=["POST"])
def delete(achievement_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM achievements WHERE id = ?", (achievement_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
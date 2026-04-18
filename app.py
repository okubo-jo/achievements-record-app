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

@app.route("/")
def index():
    conn = get_db_connection()
    achievements = conn.execute(
        "SELECT * FROM achievements ORDER BY date DESC, id DESC"
    ).fetchall()

    total = conn.execute("""
        SELECT
            COALESCE(SUM(hours), 0) AS total_hours,
            COALESCE(SUM(minutes), 0) AS total_minutes
        FROM achievements
    """).fetchone()

    conn.close()

    total_hours = total["total_hours"]
    total_minutes = total["total_minutes"]

    #分が60分以上になったら時間を繰り上げる
    total_hours += total_minutes // 60
    total_minutes = total_minutes % 60

    return render_template(
        "index.html",
        achievements = achievements,
        total_hours=total_hours,
        total_minutes=total_minutes
    )

@app.route("/add", methods=["POST"])
def add():
    date = request.form.get("date", "").strip()
    category = request.form.get("category", "").strip()
    hours = request.form.get("hours", "0").strip()
    minutes = request.form.get("minutes", "0").strip()
    memo = request.form.get("memo", "").strip()

    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    if not category:
        category = "未分類"

    try:
        hours = int(hours) if hours else 0
        minutes = int(minutes) if minutes else 0
    except ValueError:
        hours = 0
        minutes = 0

    if hours < 0:
        hours = 0
    if minutes < 0:
        minutes = 0

    #60分以上なら繰り上げる
    hours += minutes // 60
    minutes = minutes % 60

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
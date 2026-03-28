import requests
from bs4 import BeautifulSoup
import json
import time
import os

# ターゲットにする映画館のURL（例として映画.comのイオンシネマ常滑のページ）
THEATERS = [
    {"name": "109シネマズ名古屋", "url": "https://eiga.com/theater/23/230102/4104/"},
    {"name": "イオンシネマ常滑", "url": "https://eiga.com/theater/23/232001/4170/"},
    {"name": "ミッドランドスクエアシネマ", "url": "https://eiga.com/theater/23/230102/4105/"}
]

BASE_URL = "https://media.eiga.com/images"

def fetch_movies():
    schedules_data = []
    movies_data  = {}
    #サイトによってはプログラムからのアクセスを弾くため、ブラウザからのアクセスのように装う
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    movie_db_file = "movie_db.json"

    if os.path.exists(movie_db_file):
        with open(movie_db_file, "r", encoding="utf-8") as f:
            movies_data = json.load(f)


    for theater in THEATERS:
        print(f"{theater['name']} からデータを取得します...")
        theater_res = requests.get(theater['url'], headers=headers)

        movie_list = []

        if theater_res.status_code == 200: #映画一覧ページ
            theater_soup = BeautifulSoup(theater_res.content, 'html.parser')

            # 映画.comの構造に合わせて、作品名が入っているタグを抽出（※サイトの仕様変更で変わる場合があります）
            # <h2 itemprop="name">...</h2> のような部分を狙い撃ちします
            titles = theater_soup.select('h2.title-xlarge a')

            for t in titles:
                title_text = t.text.strip()
                detail_data = {}

                if title_text not in movies_data: #映画の詳細情報を取得する段階
                    movie_url = t.get("href")
                    detail_res = requests.get("https://eiga.com/" + movie_url, headers=headers)

                    if detail_res.status_code == 200:
                        detail_soup = BeautifulSoup(detail_res.content, 'html.parser')

                        #あらすじ取得
                        syn_tag = detail_soup.select_one('section.txt-block p')
                        if syn_tag:
                            synopsis = syn_tag.get_text(separator="\n").strip()
                        else:
                            synopsis = "あらすじ情報はありません。"

                        detail_data["synopsis"] = synopsis
                        time.sleep(1)

                        #ポスター取得
                        poster_res = requests.get("https://eiga.com/" + movie_url + "photo/", headers = headers)
                        if poster_res.status_code == 200:
                            poster_soup = BeautifulSoup(poster_res.content, 'html.parser')
                            pos_tag = poster_soup.select_one('div.movie-photo img')
                            if pos_tag:
                                poster_url = pos_tag.get('src')
                                print(f"ポスターURLを取得しました: {poster_url}")
                            else:
                                print("ポスター画像は見つかりませんでした。")
                                poster_url = "" # 見つからなかった場合の予備

                            detail_data["poster_url"] = poster_url

                        else:
                            print(f"通信エラー: {poster_res.status_code}")
                    else:
                        print(f"通信エラー: {detail_res.status_code}")

                    movies_data[title_text] = detail_data

                if title_text and title_text not in movie_list:
                    movie_list.append(title_text)

            print(f"{len(movie_list)}件の映画が見つかりました。")
        else:
            print(f"通信エラー: {theater_res.status_code}")


        schedules_data.append({
            "cinema_name": theater['name'],
            "movies": movie_list
        })

        time.sleep(1)

    frontend_data = {
        "schedules": schedules_data,
        "movie_details": {}
    }

    for movie in schedules_data:
        for m in movie["movies"]:
            if m in movies_data:
                frontend_data["movie_details"][m] = movies_data[m]


    with open("schedules.json", "w", encoding="utf-8") as f:
        json.dump(schedules_data, f, ensure_ascii=False, indent=2)
    print("schedules.json に保存しました。")

    with open("movie_db.json", "w", encoding="utf-8") as f:
        json.dump(movies_data, f, ensure_ascii=False, indent=2)
    print("movie_db.json に保存しました。")

    with open("api.json", "w", encoding="utf-8") as f:
        json.dump(frontend_data, f, ensure_ascii=False, indent=2)
    print("api.json に保存しました。")

if __name__ == "__main__":
    fetch_movies()

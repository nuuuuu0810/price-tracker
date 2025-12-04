import requests
from bs4 import BeautifulSoup
import json
import re
import os
from datetime import datetime, timedelta, timezone

# サイトにブロックされないための偽装ヘッダー
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8"
}

def get_price(url, selector):
    """指定されたURLとセレクタから価格(数値)を抽出する"""
    try:
        # タイムアウトを少し長めに設定
        res = requests.get(url, headers=HEADERS, timeout=15)
        res.raise_for_status()
        
        soup = BeautifulSoup(res.text, 'html.parser')
        elem = soup.select_one(selector)
        
        if not elem:
            return None
        
        text = elem.get_text()
        # 数字以外を除去 (例: "￥1,980" -> "1980")
        price_str = re.sub(r'[^\d]', '', text)
        
        if not price_str:
            return None
            
        return int(price_str)
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def main():
    # 日本時間の設定
    JST = timezone(timedelta(hours=9), 'JST')
    today_str = datetime.now(JST).strftime("%Y-%m-%d")
    
    print(f"--- Running Price Tracker: {today_str} ---")

    # 1. 商品リストの読み込み
    try:
        with open("products.json", "r", encoding='utf-8') as f:
            products = json.load(f)
    except FileNotFoundError:
        print("products.json not found.")
        return

    # 2. 過去データの読み込み
    try:
        with open("data.json", "r", encoding='utf-8') as f:
            history = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        history = {}

    # 3. 各商品の価格を取得
    for item in products:
        name = item['name']
        url = item['url']
        selector = item['selector']
        
        print(f"Checking: {name} ...")
        price = get_price(url, selector)
        
        if price is not None:
            print(f"  -> ¥{price:,}")
            
            if name not in history:
                history[name] = []
            
            # 今日のデータが既にないか確認（あれば上書き、なければ追加）
            existing_entry = next((d for d in history[name] if d["date"] == today_str), None)
            
            if existing_entry:
                existing_entry["price"] = price
            else:
                history[name].append({
                    "date": today_str,
                    "price": price
                })
        else:
            print("  -> Failed to get price")

    # 4. 保存
    with open("data.json", "w", encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    print("Done.")

if __name__ == "__main__":
    main()

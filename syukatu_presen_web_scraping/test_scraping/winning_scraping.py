import requests
import KOBO_URL
import time
import re
import pandas as pd
from bs4 import BeautifulSoup

# スクレイピング対象のサイトのURLのリストを取得
winning_url = []
winning_url = KOBO_URL.WINNING_URL_LIST

# 入賞した作品を格納するリスト
winning_list = []

# for n in range(2):
for n in range(len(winning_url)):
    res = requests.get(winning_url[n])

    # WebサイトのHTML要素を取得
    soup = BeautifulSoup(res.content, 'html.parser')

    # li要素を取得
    soup_li = soup.find_all('td', attrs={'class': 'course leftcell'})

    # リンクを取得
    link_list = []
    for j in range(len(soup_li)):
        soup_a = soup_li[j].find('a')

        try:  
            soup_a = soup_a.get('href')
            link_list.append(soup_a)
        except AttributeError as e:
            continue


    for j in range(len(link_list)):     
        res_link = requests.get(KOBO_URL.WINNING_ROOT + link_list[j])
        
        # サーバへの負荷を下げるためにsleep
        time.sleep(3)

        # リンク先のHTML要素を取得
        link_soup =  BeautifulSoup(res_link.content, 'html.parser')
        link_soup_td = link_soup.find_all('td', attrs={'class': 'fixedwidth2'})

        for k in range(len(link_soup_td)):
            winning_list.append(link_soup_td[k].text)
            print(link_soup_td[k].text)

            
# csvで出力
df = pd.DataFrame(winning_list)

# excelで文字化けしないようにutf_8_sigでエンコード
df.to_csv('winning_scraping.csv', encoding='utf_8_sig', index = False)
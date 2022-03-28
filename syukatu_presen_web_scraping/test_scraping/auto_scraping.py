import requests
import KOBO_URL
import time
import re
import pandas as pd
from bs4 import BeautifulSoup
import csv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import datetime


# 前日のスクレイピング結果を取得
with open('kobo_scraping.csv') as f:
    reader = csv.reader(f)
    l = [row[:2] for row in reader]
l = l[1:]

# --- seleniumの設定 ---

# seleniumをバックグラウンドで実行するオプションを追加
option = Options()
option.add_argument('--headless')
webdriver = webdriver.Chrome(options=option)
# webdriver = webdriver.Chrome()

# 管理サイトにログイン
webdriver.get(KOBO_URL.DJANGO_URL)
webdriver.find_element_by_xpath('//*[@id="id_username"]').send_keys(KOBO_URL.DJANGO_UN)
webdriver.find_element_by_xpath('//*[@id="id_password"]').send_keys(KOBO_URL.DJANGO_PW)
webdriver.find_element_by_xpath('//*[@id="login-form"]/div[3]/input').click()
# ログインの処理を待つ
time.sleep(3)
webdriver.find_element_by_xpath('//*[@id="content-main"]/div[2]/table/tbody/tr[1]/th/a').click()

# -----------------------


# 締切日が過ぎているかチェック
title_old_csv = [row[:1] for row in l]
deadline_old_csv = [row[1:] for row in l]

for csv in range(len(deadline_old_csv)):
    deadline = deadline_old_csv[csv][0]
    deadline = datetime.datetime.strptime(deadline, '%Y-%m-%d')
    deadline = datetime.date(deadline.year, deadline.month, deadline.day)
    
    # 締切日が過ぎている場合
    if deadline <= datetime.date.today():
        # 締切日が過ぎている公募をWebサイトから削除
        webdriver.findElement(By.linkText(title_old_csv[csv][0])).click();
        time.sleep(1)
        webdriver.find_element_by_xpath('//*[@id="kobo_info_form"]/div/div/p/a').click()
        time.sleep(1)
        webdriver.find_element_by_xpath('//*[@id="content"]/form/div/input[2]').click()
    else:
        continue


# スクレイピング対象のサイトのURLを取得
url1 = KOBO_URL.KOBO_URL1
res = requests.get(url1)

# WebサイトのHTML要素を取得
soup = BeautifulSoup(res.text, 'html.parser')

# li要素を取得
soup_li = soup.find_all('li', attrs={'class': 'contest-list-item'})

# 応募リンクを配列に格納する
link_list = []
while_cnt = 0
while True:
    try:
        soup_a = soup_li[while_cnt].find('a')
        soup_a = soup_a.get('href')
        link_list.append(soup_a)
        
    except IndexError as e:
        break
        
    while_cnt += 1


kobo_title_list = []
kobo_feature_list = []
kobo_info_list = []


for n in range(len(link_list)):
    # 情報を取得する公募ページに移動してHTTPを取得
    kobo_url = link_list[n]
    res_kobo = requests.get(kobo_url)
    soup_kobo = BeautifulSoup(res_kobo.text, 'html.parser')
    soup_kobo_dl = soup_kobo.find_all('dl')
    
    while_cnt = 0
    while True:
        try:
            soup_kobo_dt = soup_kobo_dl[while_cnt].find_all('dt')
            if '締切' == soup_kobo_dt[0].text:
                break
        except IndexError as e:
            break
        while_cnt += 1
    
    soup_kobo_dd = soup_kobo_dl[while_cnt].find_all('dd')
    
    kobo_info = {}
    
    # タイトルを追加
    kobo_title = soup_li[n].find_all('h3')
    kobo_title = kobo_title[0].text.replace('\u3000', '')
    kobo_info.setdefault('タイトル', kobo_title)
    
    # 応募リンクを追加
    obo_link = ''
    # 川柳の詳細ページのHTML要素の<a>タグのclass='btn-koushiki'の要素を取得
    obo_link = soup_kobo.find_all('a', attrs={'class': 'btn-koushiki'})
    obo_link = obo_link[0].get('href')
    # 応募リンクをkobo_infoに追加
    kobo_info.setdefault('応募リンク', obo_link)
    
    # 公募概要情報の取得・配列に格納
    for j in range(len(soup_kobo_dd)):
        kobo_feature_title = soup_kobo_dt[j].text
        kobo_feature_title = kobo_feature_title.replace('\u3000', ' ')
        
        # 項目名をデータベースのカラム名に変換
        if '締切' == kobo_feature_title:
            kobo_feature_title = '締切日'
            
            # 日付だけを抽出
            kobo_feature = soup_kobo_dd[j].text.replace('\u3000', ' ')
            kobo_feature = kobo_feature.replace('\n', '')
            kobo_feature = kobo_feature.replace('\t', '')
            kobo_feature = kobo_feature.replace('\r', '')
            kobo_feature = re.match('20\d\d.\d\d.\d\d.', kobo_feature)
            kobo_feature =  str(kobo_feature.group())
            kobo_feature = kobo_feature.replace('年', '-')
            kobo_feature = kobo_feature.replace('月', '-')
            kobo_feature = kobo_feature.replace('日', '')
            kobo_info.setdefault(kobo_feature_title, kobo_feature)
            
            continue
            
        elif '賞' == kobo_feature_title:
            kobo_feature_title = '賞金'
        elif '募集内容' == kobo_feature_title:
            kobo_feature_title = '募集内容'
        elif '参加資格' == kobo_feature_title:
            kobo_feature_title = '応募資格'
        elif '主催' == kobo_feature_title:
            kobo_feature_title = '主催'
        else:
            continue
        
        # HTML要素のテキストだけを取り出す
        kobo_feature = soup_kobo_dd[j].text.replace('\u3000', ' ')
        kobo_feature = kobo_feature.replace('\n', '')
        kobo_feature = kobo_feature.replace('\t', '')
        kobo_feature = kobo_feature.replace('\r', '')
        kobo_info.setdefault(kobo_feature_title, kobo_feature)
        
    # kobo_infoの中身を並び替える
    kobo_sort = {}
    kobo_sort.setdefault('タイトル', kobo_info['タイトル'])
    kobo_sort.setdefault('締切日', kobo_info['締切日'])
    kobo_sort.setdefault('賞金', kobo_info['賞金'])
    kobo_sort.setdefault('募集内容', kobo_info['募集内容'])
    kobo_sort.setdefault('応募資格', kobo_info['応募資格'])
    kobo_sort.setdefault('主催', kobo_info['主催'])
    kobo_sort.setdefault('応募リンク', kobo_info['応募リンク'])

    # 公募情報を配列に格納
    kobo_info_list.append(kobo_sort)

    if [kobo_info['タイトル']] in title_old_csv:
        pass
    else:
        webdriver.find_element_by_xpath('//*[@id="content-main"]/ul/li/a').click()
        time.sleep(3)
        webdriver.find_element_by_xpath('//*[@id="id_title"]').send_keys(kobo_info['タイトル'])
        webdriver.find_element_by_xpath('//*[@id="id_deadline"]').send_keys(kobo_info['締切日'])
        webdriver.find_element_by_xpath('//*[@id="id_prize"]').send_keys(kobo_info['賞金'])
        webdriver.find_element_by_xpath('//*[@id="id_contents"]').send_keys(kobo_info['募集内容'])
        webdriver.find_element_by_xpath('//*[@id="id_requirements"]').send_keys(kobo_info['応募資格'])
        webdriver.find_element_by_xpath('//*[@id="id_sponsor"]').send_keys(kobo_info['主催'])
        webdriver.find_element_by_xpath('//*[@id="id_link"]').send_keys(kobo_info['応募リンク'])
        webdriver.find_element_by_xpath('//*[@id="kobo_info_form"]/div/div/input[1]').click()
        time.sleep(3)

    # サーバへの負荷を下げるためにsleep
    time.sleep(60)

    
# 管理サイトからログアウトする（selenium）
webdriver.find_element_by_xpath('//*[@id="user-tools"]/a[3]').click()

# csvで出力

df = pd.DataFrame(kobo_info_list)

# excelで文字化けしないようにutf_8_sigでエンコード
df.to_csv('kobo_scraping.csv', encoding='utf_8_sig', index = False)
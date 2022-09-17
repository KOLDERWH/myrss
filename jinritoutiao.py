import datetime
import re
from urllib.parse import unquote

import PyRSS2Gen
import requests
from bs4 import BeautifulSoup

# 使用cookie获取内容
if __name__ == '__main__':
    # 请求头
    headers = {
       
        "cookie":"_ga=GA1.2.629556130.1649388351; tt_webid=7092741079242540557; WIN_WH=1536_722; FRM=new; PIXIEL_RATIO=1.25; _S_WIN_WH=1536_722; _S_DPR=1.25; _S_IPAD=0; local_city_cache=%E4%B9%89%E4%B9%8C; csrftoken=b53c88e0bc6b4234141e5b29729ebbee; _tea_utm_cache_24=undefined; s_v_web_id=verify_l7j6sryb_DEse06w6_oWIC_4rkY_Bi1V_33TBpXvi7ctu; MONITOR_WEB_ID=5f3c526c-694e-4d98-91c2-c2816a5ebb1f; ttcid=081257ade3c04a898f4fd9cfb5cc9f0037; tt_scid=a4LwtxVjuZ4t2etgRw6Ivepp19TjbKvz3bVSS73Zn8PE71.GRwzqBOuPKH1pc6NK3bd3; ttwid=1%7CLy-pekgftNNErnzTAkp_obWGNLFy3AWzB0OyYVY03FA%7C1662088065%7C40e9d882b318785c892b71aa39e920c2e5523d7a12919321a7ff2fdb64a37fc1; msToken=i9zmV9YiRRFs3efXtiS-3MlwSWQBRpH2p4UbC1A0Vxm50MefTxK1uOWQmHqsBUmPXe4kIEhfHJXwq4SzzyG0wzqHr_6RqYsu8qjoQKE8BGGl",
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36',

    }

    hostUrl = 'https://www.toutiao.com/'
    sessions = requests.Session()

    def SameUrl(url, addurl):
        for addsingle in addurl:
            if len(url) <= len(addsingle):
                if url in addsingle:
                    print("the same : " + url)
                    return None
            else:
                if addsingle in url:
                    print("the same : " + url)
                    return None
        return 1

    def toutiaoSpider():
       
        html = requests.get(hostUrl, headers=headers)
        bs = BeautifulSoup(html.text, 'html.parser')
        bs = unquote(bs, 'utf-8')

        contents = bs.findAll(class_="feed-card-article-l")
        mobilerssItems = []
        addurl=[]
        for content in contents:

            url = content.find("a")['href']
            if 'toutiao.com' not in url:
                print("Other page : "+url)
                continue

            if SameUrl(url, addurl) is None:
                continue

            article = getArticle(url)
            descriptions = article[0]
            link=re.findall('^.*[\/]',article[1])[0]
            link=link.replace("www","m")
            title = article[2]
            time=article[3]
            if descriptions is None:
                continue

            rssItem = PyRSS2Gen.RSSItem(
                title=title,
                link=link,
                description=str(descriptions),
                pubDate=time
            )
            mobilerssItems.append(rssItem)
        return mobilerssItems

    def getArticle(realurl):
        print(realurl)
        link = realurl
        detialHtml = sessions.get(realurl, headers=headers)
        # detialHtml.encoding = 'utf8'
        bsDetial = BeautifulSoup(detialHtml.text, 'lxml')
        bsDetial = unquote(bsDetial, 'utf-8')

        all_contents = []

        if "/video/" in realurl:

            print("the video : " + realurl)
            return None

            titleContain = bsDetial.find("title")
            if titlecontain is not None:
                title = titleContain.string

            pic = bsDetial.find(class_="player-mask")
            if pic['style'] is not None:
                picUrlcon = pic['style']
                src = re.findall('["].*["]', picUrlcon)[0]

                insert_img = "<img src=" + src + ' alt=""><br/>'
                all_contents.append(insert_img)

            all_contents.append(pic)

        else:
            # pc
            title = bsDetial.find(class_="article-content")
            if title:
                title = title.contents[0].text

            # time & author
            meta = bsDetial.find(class_="article-meta")
            if meta:
                time = re.findall('\d.*[:]\d\d', meta.text)[0]
            else:
                time=datetime.datetime.now()
            all_contents.append(meta)
            article = bsDetial.find(class_="syl-article-base tt-article-content syl-page-article syl-device-pc")

        # filter info
        if article:
            filter(article, all_contents)
        else:
            print("no article : "+realurl)

        # list2str
        descriptions = list_srt(all_contents)
        descriptions = re.sub('class=".*?"', '', descriptions)
        descriptions = re.sub('web.*?=".*?"', '', descriptions)

        return descriptions, link, title, time


    def list_srt(list):
        srt = ""
        for i in list:
            srt += str(i) + " "
        return srt

    def makeRss(rssItems):
        rss = PyRSS2Gen.RSS2(
            title="今日头条",
            link=hostUrl,
            description="今日头条是北京字节跳动科技有限公司开发的一款基于数据挖掘的推荐引擎产品，为用户推荐信息、提供连接人与信息的服务的产品。",
            lastBuildDate=datetime.datetime.now(),
            items=rssItems)
        rss.write_xml(open('./xml/toutiao.xml', "w", encoding='utf-8'), encoding='utf-8')
        pass

    def filter(article, theRespon):
        for detail in article:
            if detail.name == 'p' and len(detail.text) > 2 or detail.name == "img":
                theRespon.append(detail)
                continue

            if detail.find('div'):
                theRespon.append(detail.find('div'))
                continue

            if detail.find('img'):
                theRespon.append(detail.find('img'))
                continue

            if detail.find('br') or len(detail.text) < 1:
                continue

            theRespon.append(detail)

    def add_Ele(addStr, Contain):
        insert_element = "<p>" + addStr + '</p>'
        Contain.append(insert_element)

    if __name__ == '__main__':
        rssItems = toutiaoSpider()
        makeRss(rssItems)

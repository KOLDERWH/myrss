import datetime
import os
import re

import bs4
import PyRSS2Gen
import requests
from bs4 import BeautifulSoup

# 用正则表达式获取内容
if __name__ == '__main__':
    # 请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
        'Content-Type': 'text/html; charset=utf-8',
    }

    mobile_headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
        'Content-Type': 'text/html; charset=utf-8',
    }

    hostUrl = 'https://www.huxiu.com'
    mobileUrl = 'https:/m.huxiu.com'
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


    def huxiu_spider():
        # getHml
        html = sessions.get(hostUrl + '/', headers=headers)
        # 使用BeautifulSoup进行解析
        bs = BeautifulSoup(html.text, 'lxml')

        contents = bs.findAll('a', class_='tibt-card__top')
        rssSingle_item = []

        addurl = []
        for content in contents:

            # 去除相同的url
            url = content['href']
            if SameUrl(url, addurl) is None:
                continue
            addurl.append(url)

            # 获取链接
            article = getArticle(url)
            if article is None:
                continue

            article_content = article[0]
            link = article[1]
            title = article[2]
            time = article[3]

            # the RSS
            rssItem = PyRSS2Gen.RSSItem(
                title=title,
                link=link,
                description=str(article_content),
                pubDate=time
            )
            rssSingle_item.append(rssItem)
        return rssSingle_item


    def getArticle(article_url):
        all_contents = []
        # mobile
        link = "https://m.huxiu.com" + article_url
        html = sessions.get(link, headers=mobile_headers)
        htmlContain = BeautifulSoup(html.text, 'lxml')

        print(link)
        # get content
        description_gen = htmlContain.find(id="article-detail-content")
        if description_gen is None:
            print("no content: " + link)
            return None

        # pic
        pictureCon = htmlContain.find(property="og:image")
        if pictureCon:
            pictureCon = htmlContain.find(property="og:image")
            pic = pictureCon['content']
            if '?' in pic:
                pic = re.findall('h.+[?]', pic)[0]
            insert_img = "<img src=" + pic + ' alt="">'
            all_contents.append(insert_img)

        # time
        release_time = htmlContain.find(class_="m-article-time").text
        add_element("<strong>Released:</strong>" + release_time, all_contents)

        article_content=str(description_gen)
        article_content = erase_element('class=".*?"', article_content)
        article_content = erase_element('id=".*?"', article_content)

        all_contents.append(article_content)

        # filter info
        # filter_content(description_gen.contents, all_contents)

        # title
        title_contain = htmlContain.find(class_="article-content-title-box")
        title = title_contain.find(class_="title").text

        # list2str
        article_content = list_srt(all_contents)

        # article_content=re.sub('class=".*?"','',article_content)

        return article_content, link, title, release_time

    def erase_element(element,contianer):
        return re.sub(element, '', contianer)


    def list_srt(list_content):
        srt = ""
        for i in list_content:
            srt += str(i) + " "
        return srt


    def makeRss(rss_items):
        rss = PyRSS2Gen.RSS2(
            title="虎嗅",
            link=hostUrl,
            description="科技资讯,商业评论,明星公司,动态,宏观,趋势,创业,精选,有料,干货,有用,细节,内幕.",
            lastBuildDate=datetime.datetime.now(),
            items=rss_items)
        rss.write_xml(open('./xml/huxiu.xml', "w", encoding='utf-8'), encoding='utf-8')
        pass


    # def filter_content(filter_article, filter_contain):
    #     for detail in filter_article:
    #         if isinstance(detail, bs4.element.Tag) is False:
    #             continue
    #
    #         if detail.name == 'div':
    #             if detail.find('a'):
    #                 for single in detail.contents:
    #                     if isinstance(single, bs4.element.Tag):
    #                         filter_contain.append(single)
    #             continue
    #
    #         if detail.find('img'):
    #             filter_contain.append(detail.find('img'))
    #             continue
    #
    #         if (detail.name == 'p' and detail.find('br')) or len(detail.text.strip()) < 1:
    #             continue
    #         filter_contain.append(detail)


    def add_element(add_str, add_contain):
        insert_element = "<p>" + add_str + '</p>'
        add_contain.append(insert_element)


    if __name__ == '__main__':
        rssItems = huxiu_spider()
        makeRss(rssItems)

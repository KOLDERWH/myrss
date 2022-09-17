import datetime
import re

import PyRSS2Gen
import requests
from bs4 import BeautifulSoup
from lxml import etree

if __name__ == '__main__':

    # 请求头
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36(KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36',
        'Content-Type': 'text/html; charset=utf-8',
    }

    domain_url = 'https://www.economist.com'
    sessions = requests.session()


    def FindSame(url, addurl):
        for addsingle in addurl:
            if len(url) <= len(addsingle):
                if url in addsingle:
                    return None
            else:
                if addsingle in url:
                    return None
        return 1

    def TESpider():
        html = sessions.get(domain_url, headers=headers)
        bs = BeautifulSoup(html.text, 'lxml')

        contents=bs.findAll('h3')
        rssItems = []

        addurl = []
        for content in contents:
            if content.find('a') is None:
                continue

            realcontent = content.find('a')
            url = realcontent['href']

            if FindSame(url, addurl) is None:
                print("Same url :"+url)
                continue
            addurl.append(url)
            if 'www.economist.com/' not in  url:
                article_url = domain_url+url
            else:
                article_url = url

            article = getArticle(article_url)

            if article is None:
                continue
            descriptions = article[0]

            url_article = article[1]
            title = article[2]
            time = article[3]

            rssItem = PyRSS2Gen.RSSItem(
                title=title,
                link=url_article,
                description=str(descriptions),
                pubDate=time
            )
            rssItems.append(rssItem)
        return rssItems


    addtitle = []
    def getArticle(url_article):
        print(url_article)
        # pc
        hostUrl = url_article
        try:
            html = sessions.get(hostUrl, headers=headers)
        except:
            print("Error url"+url_article)
            return None

        bs = BeautifulSoup(html.text, 'lxml')

        main_article = []
        # content
        article=bs.find('article')
        if article is None:
            print("Articleless: " + hostUrl)
            return None

        # pic
        picContain = bs.find("figure")
        try:
            url_Picture = picContain.find("img")["src"]
        except:
            try:
                url_Picture = picContain.find("video")["poster"]
            except:
                url_Picture = None

        if url_Picture:
            try:
                if '?' in url_Picture:
                    url_Picture = re.findall('h.+[?]', url_Picture)[0]
                insert_img = "<img src=" + url_Picture + ' alt="">'
                main_article.append(insert_img)
            except:
                print("Pictureless: " + url_article)

        # title
        containter_title = re.findall('<h1.*?h1>',  str(article).replace('\n', '').replace('\r', ''))[0]
        title = re.findall('(?<=>).*?(?=<)', containter_title)[0]

        # same title
        if FindSame(title, addtitle) is None:
            print("same title : " + url_article)
            return None
        addtitle.append(title)

        # #subtitle
        try:
            containter_subtitle = re.findall('<h2.*?h2>', str(article.find('div').find('div').find('div')).replace('\n', '').replace('\r', ''))[0]
            subTitle = re.findall('(?<=>).*?(?=<)', containter_subtitle)[0]
            add_Ele("<strong>Subtitile: </strong>: " + subTitle, main_article)
        except:
            print("Subtileless: " + url_article)

        # time
        timecontainer = re.findall('<time.*?<\/time>', str(article).replace('\n', '').replace('\r', ''))[0]
        try:
            time = re.findall('(?<=>).*?(?=<)', timecontainer)[1]
        except:
            time = re.findall('(?<=>).*?(?=<)', timecontainer)[0]
        add_Ele("<strong>Released: </strong>: " + time, main_article)
        try:
            release_time = re.findall('datetime="(.*\d\w)"', timecontainer)[0]
        except:
            release_time = time

        # voice
        voices = article.find("audio")
        if voices:
            voiceEle = "<audio src=" + voices['src'] + ' controls="controls" ></audio>'
            main_article.append(voiceEle)

        content = re.findall('<section.*?>.*?<\/section>',str(bs.find('article')).replace('\n', '').replace('\r', ''))
        add_article = content[len(content) - 1]

        # 去广告
        add_article = erase_element('<figure.*?<audio.*?\/figure>', add_article)
        add_article = erase_element('srcset=".*?"', add_article)
        add_article = erase_element('<style.*?>.*?<\/style>', add_article)
        add_article = erase_element('class=".*?"', add_article)
        add_article = erase_element('id=".*?"', add_article)
        add_article = erase_element('(<div>){1,}(<\/div>){1,}', add_article)

        main_article.append(add_article)

        descriptions = list_srt(main_article)

        return descriptions, hostUrl, title, release_time

    def erase_element(element,contianer):
        return re.sub(element, '', contianer)


    def makeRss(rssItems):
        rss = PyRSS2Gen.RSS2(
            title="The Economist",
            link=domain_url,
            description="The Economist is a British weekly newspaper printed in demitab "
                        "format and published digitally that focuses on current affairs, international"
                        " business, politics, technology, and culture.",
            lastBuildDate=datetime.datetime.now(),
            items=rssItems)
        rss.write_xml(open('./xml/TheEconomist.xml', "w", encoding='utf-8'), encoding='utf-8')
        pass

    def list_srt(list):
        srt = ""
        for i in list:
            srt += str(i) + " "
        return srt

    def add_Ele(addStr, Contain):
        insert_element = "<p>" + addStr + '</p>'
        Contain.append(insert_element)

    if __name__ == '__main__':
        rssItems = TESpider()
        makeRss(rssItems)

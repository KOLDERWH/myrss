import datetime
import re
import time as timer

import bs4
import PyRSS2Gen
import requests
from bs4 import BeautifulSoup

# 去掉了过滤器改为直接加入（amo-img变为img可以显示图片）#
# 主图片只在头部寻找

if __name__ == '__main__':
    # header
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36 Content-Typetext/html; charset=utf-8',
    }

    hostUrl = 'https://www.wsj.com/news/latest-headlines'

sessions = requests.session()


def form_time(time):
    time = time.replace("Jan.", "January")
    time = time.replace("Feb.", "February")
    time = time.replace("Mar.", "March")
    time = time.replace("Apr.", "April")
    time = time.replace("May", "May")
    time = time.replace("June.", "June")
    time = time.replace("Jul.", "July")
    time = time.replace("Aug.", "August")
    time = time.replace("Sept.", "September")
    time = time.replace("Oct.", "October")
    time = time.replace("Nov.", "November")
    time = time.replace("Dec.", "December")
    return time


def SameUrl(url, find_url):
    for single_url in find_url:
        if len(url) <= len(single_url):
            if url in single_url:
                print("the same : " + url)
                return None
        else:
            if single_url in url:
                print("the same : " + url)
                return None
    return 1


def wst_spider():
    html = sessions.get(hostUrl, headers=headers)
    # read
    bs = BeautifulSoup(html.text, 'lxml')
    contents = bs.findAll(class_='WSJTheme--headline--7VCzo7Ay')
    # the html
    rss_single_item = []
    url_content = []
    for content in contents:

        url = content.find('a')['href']
        if SameUrl(url, url_content) is None:
            continue
        url_content.append(url)
        article = getArticle(url)

        if article is None:
            continue

        released_time = form_time(article[3])
        rss_contents = article[0]
        link = article[1]
        title = article[2]

        # the RSS
        rssItem = PyRSS2Gen.RSSItem(
            title=title,
            link=link,
            description=str(rss_contents),
            pubDate=released_time
        )
        rss_single_item.append(rssItem)
        timer.sleep(1)
    return rss_single_item


def getArticle(content_url):
    # html
    print(content_url)

    # no livecoverage
    if content_url.find("livecoverage") > 0 or content_url.find("wsj.com") == -1:
        print("canot read: " + content_url)
        return None

    if "amp/" not in content_url:
        article_url = content_url.replace("com/", "com/amp/")
    else:
        article_url = content_url

    if '?' in article_url:
        article_url = re.findall('h.+[?]', article_url)[0]

    html = sessions.get(article_url, headers=headers)
    bs = BeautifulSoup(html.text, 'lxml')
    content_container = []

    # picture
    picture_contain = bs.find("amp-img")

    if picture_contain:
        pic = picture_contain['src']
        if pic:
            try:
                if '?' in pic:
                    pic = re.findall('[h].+[?]', pic)[0]
                insert_img = "<img src=" + pic + ' alt=""><br/>'
                content_container.append(insert_img)
            except:
                print("No picture : " + article_url)

    # title & subtitle
    tempTitle = bs.find(class_="wsj-article-headline")
    title = tempTitle.text
    subtitle = bs.find(class_="sub-head")

    # subtitle
    if subtitle:
        add_element("<strong>Subtitle: </strong>" + subtitle.text, content_container)

    # author
    author_contains = bs.find(class_="byline")
    if author_contains is None:
        print("authorless: "+article_url)
    else:
        add_author = author_contains.text.strip()
        add_element(add_author, content_container)

    # time
    time = bs.find(class_="timestamp article__timestamp flexbox__flex--1")
    content_container.append(time)

    if time.text:
        released_time = re.findall('[JFMASOND].*m', time.text)[0]
        if len(released_time) < 10:
            released_time = time.text
    else:
        released_time = time.contents[0].text
        print("find the other form")

    # voice
    voices = bs.findAll(class_="podcast--iframe")
    if voices:
        for single in voices:
            voiceEle = '<iframe width = "480" height = "50" frameborder = "0" src ="' + single['src'] + ' "</iframe>'
            content_container.append(voiceEle)

    # part hider
    hider = bs.find("section")
    if hider is None:
        print("No contents :" + article_url)
        return None

    # the mask login ad recommand
    erase_element("newsletter-inset", hider)
    erase_element("dynamic-inset-overflow", hider)
    erase_element("wsj-ad", hider)
    erase_element("media-object-rich-text", hider)
    erase_element("dynamic-inset-iframe", hider)

    filter_content(hider.contents, content_container)

    rss_contents = list_srt(content_container)
    rss_contents = rss_contents.replace('<amp-img', '<img')
    rss_contents = rss_contents.replace('</amp-img', '<img')
    
    rss_contents = re.sub('class=".*?"', '', rss_contents)
    
    return rss_contents, article_url, title, released_time


def erase_element(class_erase, contain_erase):
    if contain_erase.findAll(class_=class_erase):
        erase_elems = contain_erase.findAll(class_=class_erase)
        for erase_single in erase_elems:
            erase_single.decompose()


def list_srt(input_url):
    srt = ""
    for i in input_url:
        srt += str(i) + " "
    return srt


def filter_content(filter_article, filter_contain, ):
    for detail in filter_article:
        if isinstance(detail, bs4.element.Tag) is False and len(detail.text.strip()) < 2:
            continue
        if detail.name == 'p' and len(detail.text.strip()) > 1:
            filter_contain.append(detail)
            continue
        if detail.name == 'h6':
            add_element("<p><strong>" + detail.text + "</strong></p>", filter_contain)
            continue
        if detail.name == 'div' and 1 < len(detail.text):
            filter_contain.append(detail)
            continue
        if detail.find("figure"):
            filter_contain.append(detail.find("figure"))
            continue
        if detail.find('br') or len(detail.text.strip()) < 1:
            continue
        filter_contain.append(detail)


def add_element(input_str, contain):
    insert_element = "<p>" + input_str + '</p>'
    contain.append(insert_element)


def generate_rss(rss_items):
    rss = PyRSS2Gen.RSS2(
        title="The Wall Street Journal",
        link=hostUrl,
        description="The Wall Street Journal is an American business-focused, international daily" +
                    " newspaper based in New York City, with international editions also available" +
                    " in Chinese and Japanese.",
        lastBuildDate=datetime.datetime.now(),
        items=rss_items)
    rss.write_xml(open('./xml/theWallStreet.xml', "w", encoding='utf-8'), encoding='utf-8')
    pass


if __name__ == '__main__':
    rssItems = wst_spider()
    generate_rss(rssItems)

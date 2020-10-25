#!/usr/bin/python
#coding=utf-8
!pip install -U fake-useragent
!pip install -U func_timeout
from bs4 import BeautifulSoup
from lxml import html as h
from fake_useragent import UserAgent
from google.colab import drive
from math import ceil
from posixpath import normpath
from urllib.parse import urlencode, urljoin, urlparse, urlparse, urlunparse
from datetime import date, datetime, timedelta
import pandas as pd
import csv, func_timeout, html, os.path, pickle, re, requests, string, time

#drive.mount('/content/drive')
#print(str(UserAgent().random))

@func_timeout.func_set_timeout(30)#添加func_set_timeout(2)的装饰器，参数2表示超时时间，此处设置为2s。
def askChoice(slogan):#将需要询问的内容封装进一个函数
    inputs = input(f'{slogan}\n')
    return inputs
#程序执行时先调用askChoice函数，并开始计时。
#若用户在计时期间内输入，则正常传参
#若用户超时，则触发func_timeout.exceptions.FunctionTimedOut异常，try...except捕捉异常，并进行后续操作。
 
def getHTMLText(url, code = 'utf-8'):
    Headers = {'User-Agent':str(UserAgent().random)}
    r = requests.get(url, headers = Headers, timeout = 30)
    r.raise_for_status()
    r.encoding = code
    return r
 
def getHTMLText_with_retry(url, code = 'utf-8', retry = 10):
    for i in range(retry):
        try:
            request_text = getHTMLText(url, code='utf-8')
            return request_text
        except Exception as e:
            print(f'网页访问失败: {e}')
        if i > 5:
            time.sleep(10)
    print(f'Load {url} failed 10 times')
    return ''

def getKey(dct, value):
  return [k for (k,v) in dct.items() if v == value][0]#字典中根据值倒查键

def cleanLink(link):
    link = re.sub('\?ref=.*', '', link)#remove ?ref=
    attrs = re.compile(r'lang=\d+|cu=\d+')# clean cu = 0, avoid different link for same page
    link = attrs.sub('',link)
    while link.endswith('?') or link.endswith('&'):
        link = link[:-1]
    return link

def newUrl(url):
    base = 'https://comicbookroundup.com'
    url1 = urljoin(base, url)
    arr = urlparse(url1)
    path = normpath(arr[2])
    return urlunparse((arr.scheme, arr.netloc, path, arr.params, arr.query, arr.fragment))

def embNumbers(s):
    re_digits = re.compile(r'(\d+)')
    pieces = re_digits.split(s)
    pieces[1::2] = map(int,pieces[1::2])    
    return pieces

def sortList(alist):#sort_strings_with_embNumbers
    aux = [(embNumbers(s),s) for s in alist]
    aux.sort()
    return [s for __,s in aux]
#没搞懂，按https://www.cnblogs.com/ajianbeyourself/p/5395653.html，找机会用key替换掉DSU排序

def output(url):#文件输出路径
    fpath = re.sub('.*reviews/','',url).replace('-', ' ')
    fpath = re.sub('(\?|&).*','',fpath)#删除页码
    fpath = re.sub('[A-Z]',lambda x:' '+x.group(0),fpath).title()#首字母大写
    #fpath = re.sub('_(\d+)',lambda x: x.group(1),fpath)#删除页码然后拼接
    fpath = fpath.replace('=', '').replace('_', '')#删除数字前的空格
    outputPath = f'/content/drive/My Drive/reviews/{fpath}.csv'
    if not os.path.exists(os.path.dirname(outputPath)):
        os.makedirs(os.path.dirname(outputPath))
    #print(f'File will be saved in {fpath}.csv')
    return outputPath

def homePage(url, urlList = list(), titleList = list()):
    page = getHTMLText_with_retry(url)
    dom_tree = h.fromstring(page.content)
    print(dom_tree.xpath("//div[@class='top']/div[@class='container']/h1")[0].xpath('string(.)'))
    div = dom_tree.xpath("//div[@id='top-list']/div")
    for item in div:
        try:
            home = {
                'grade':'', 
                'title':'', 
                'critics':'', 
                'link':''
                }
            home['title'] = item.xpath('.//a/text()')[0]
            home['grade'] = item.xpath('./div[1]/text()')[0]
            critics = [critics.strip() for critics in item.xpath('./div[2]/text()') if critics.strip() != '']
            critics = ' '.join(html.unescape(critics)).strip().replace('	',' ').replace('  ',' ')
            home['critics'] = re.search(' (\d+) ', critics).group(1)
            link = item.xpath('./h2/a/@href')[0]
            home['link'] = newUrl(link)
            urlList.append(home['link'])
            homePage = [value for value in home.values()]
            if home['title'] not in titleList:
                with open('homePage.csv', 'at', encoding = 'utf-8', newline = '') as csvfile:
                    print(f"{home['grade']}/10	{home['title']}, Based On: {home['critics']} critics\n")
                    writer = csv.writer(csvfile)
                    #writer.writerow(homePage)
                titleList.append(home['title'])
        except Exception as e:
            print(e)
    sections = dom_tree.xpath("//div[@class='left']/div[@class='section']")
    for section in sections:
        print(section.xpath('./h1')[0].xpath('string(.)'))
        div = section.xpath('.//ul/div')
        for item in div:
            try:
                home = {
                    'grade':'', 
                    'title':'', 
                    'critics':'', 
                    'addTime':''
                    }
                home['title'] = item.xpath('.//a/text()')[0]
                home['grade'] = item.xpath('./div[1]/text()')[0]
                critics = [critics.strip() for critics in item.xpath('./div[2]/text()') if critics.strip() != '']
                critics = ' '.join(html.unescape(critics)).strip().replace('	',' ').replace('  ',' ')
                home['critics'] = re.search(' (\d+) ', critics).group(1)
                link = item.xpath('./h2/a/@href')[0]
                urlList.append(newUrl(link))
                home['addTime'] = time.strftime('%Y/%m/%d %-H:%-M:%-S')
                homeList = [value for value in home.values()]
                if home['title'] not in titleList:
                    with open('homePage.csv', 'at', encoding = 'utf-8', newline = '') as csvfile:
                        print(f"{home['grade']}/10	{home['title']}, Based On {home['critics']} critics\n")
                        writer = csv.writer(csvfile)
                        #writer.writerow(homeList)
                    titleList.append(home['title'])
            except Exception as e:
                print(e)
    return urlList

def seriesReview(url, urlList = list()):
    page = getHTMLText_with_retry(url)
    dom_tree = h.fromstring(page.content)
    seriesTitle = html.unescape(dom_tree.xpath("//div[@class='top issue']//div[@class='right']/h1/span/text()")[0])
    avgRating = dom_tree.xpath("//div[@id='series']//div[@class='right']/div[contains(@class,'review')]/text()")
    avgRating = [rating.strip() for rating in avgRating if rating.strip() != '']
    #(avgCriticRating, avgUserRating) = avgRating
    avgRatingTitle = dom_tree.xpath("//div[@id='series']//span[@class='rating-title']/text()")
    #for i in range(len(avgRatingTitle)):
        #print(avgRatingTitle[i]+': '+avgRating[i])
    sections = dom_tree.xpath("//div[@class='left']//div[@class='section']")
    outputPath = output(url)
    for section in sections:
        trs = section.xpath(".//tr")
        i = 0
        for tr in trs:
            i += 1
            if i == 1:
                headLine = []
                heads = [head.strip() for head in tr.xpath(".//th//text()") if head.strip() != '']
                for head in heads:
                    if head == 'Rating' or head == 'Reviews':
                        headLine.append('Critic '+head)
                        headLine.append('User '+head)
                    else:
                        headLine.append(head)
                headLine.append('Add Time')
                with open(outputPath, 'at', encoding = 'utf-8', newline = '') as csvfile:
                    writer = csv.writer(csvfile)
                    #writer.writerow(headLine)
            else:
                try:
                    criticRating = tr.xpath(".//div[contains(@class,'review')]/../@class")[0].replace('List','')
                    userRating = tr.xpath(".//div[contains(@class,'review')]/../@class")[1].replace('List','')
                    item = {
                        'criticRating':'', 
                        'userRating':'', 
                        'issue':'', 
                        'writer':'', 
                        'artist':'', 
                        'criticReviews':'', 
                        'userReviews':'', 
                        'addTime':''
                        }
                    item['criticRating'] = tr.xpath(".//div[contains(@class,'review')]/text()")[0]
                    item['userRating'] = tr.xpath(".//div[contains(@class,'review')]/text()")[1]
                    #criticRating = ''.join(tr.xpath(".//div[@class='CriticRatingList']//text()")).strip()
                    #userRating = ''.join(tr.xpath(".//div[@class='UserRatingList']//text()")).strip()
                    #item['rating'] = ' / '.join([criticRating, userRating])
                    item['issue'] = html.unescape(tr.xpath("./td[2]/a/text()")[0])
                    link = tr.xpath("./td[2]/a/@href")[0]
                    if link not in urlList:
                        urlList.append(link)
                    item['writer'] = tr.xpath("./td[3]/a/text()")[0]
                    item['artist'] = tr.xpath("./td[4]/a/text()")[0]
                    item['criticReviews'] = tr.xpath("./td[@class='reviews']//a/text()")[0]
                    item['userReviews'] = tr.xpath("./td[@class='reviews']//a/text()")[1]
                    item['addTime'] = time.strftime('%Y/%m/%d %-H:%-M:%-S')
                except:
                    criticRating = tr.xpath(".//div[contains(@class,'review')]/../@class")[0].replace('List','')
                    userRating = tr.xpath(".//div[contains(@class,'review')]/../@class")[1].replace('List','')
                    item = {
                        'criticRating':'', 
                        'userRating':'', 
                        'volume':'', 
                        'criticReviews':'', 
                        'userReviews':'', 
                        'addTime':''
                        }
                    item['criticRating'] = tr.xpath(".//div[contains(@class,'review')]/text()")[0]
                    item['userRating'] = tr.xpath(".//div[contains(@class,'review')]/text()")[1]
                    item['volume'] = html.unescape(tr.xpath("./td[2]//a/text()")[0])
                    link = tr.xpath("./td[2]/a/@href")[0]
                    if link not in urlList:
                        urlList.append(link)
                    item['criticReviews'] = tr.xpath("./td[@class='reviews']//a/text()")[0]
                    item['userReviews'] = tr.xpath("./td[@class='reviews']//a/text()")[1]
                    item['addTime'] = time.strftime('%Y/%m/%d %-H:%-M:%-S')
                with open(outputPath, 'at', encoding = 'utf-8', newline = '') as csvfile:
                    itemRatingList = [value for value in item.values()]
                    writer = csv.writer(csvfile)
                    #writer.writerow(itemRatingList)
    return avgRating, urlList


def issueReview(url, nameList = list(), urlLists = list()):
    flatten = lambda x: [y for l in x for y in flatten(l)] if type(x) is list else [x]
    page = getHTMLText_with_retry(url)
    dom_tree = h.fromstring(page.content)
    issueTitle = html.unescape(dom_tree.xpath("//div[@class='top issue']//div[@class='right']/h1/span/text()")[0])
    print(issueTitle)
    outputPath = output(url)
    try:
        series = newUrl(dom_tree.xpath("//div[@id='issue']/div//a[@class='series']/@href")[0])
        (avgRating, urlList) = seriesReview(series)
        Urls = [newUrl(url) for url in urlList]
        urlLists.extend(Urls)
    except:
        avgRating = (0, 0)
        pass
    try:
        previous = newUrl(dom_tree.xpath("//div[@id='issue']/div//a[@class='previous']/@href")[0])
        urlLists.append(previous)
    except:
        pass
    try:
        next = newUrl(dom_tree.xpath("//div[@id='issue']/div//a[@class='next']/@href")[0])
        urlLists.append(next)
    except:
        pass
    i = 0
    if dom_tree.xpath("//div[@class='top issue']/./@id")[0] == 'issue':
        rating = dom_tree.xpath("//div[@id='issue']//div[contains(@class,'review')]/text()")
        ratingTitle = dom_tree.xpath("//div[@id='issue']//span[@class='rating-title']/text()")
        ids = dom_tree.xpath("//div[@class='left']/div[contains(@id,'reviews')]")
        for id in ids:
            critics = id.xpath('./div/ul/li')
            print(f'\n{ratingTitle[i]}: {rating[i]}({avgRating[i]}) Based on {len(critics)} critics')
            for critic in critics:
                try:
                    review = {
                        'grade':'',  
                        'group':'', 
                        'name':'', 
                        'reviewer':'', 
                        'reviews':'',
                        'moreReviews':'', 
                        'site':'', 
                        'date':'', 
                        'addTime':''
                        }
                    review['grade'] = critic.xpath("./div[1]/text()")[0]
                    name = critic.xpath("./div[2]/span[@class='name']//text()")[0]
                    #review['name'] = critic.xpath("./div[2]/span[@class='name']")[0].xpath('string(.)')
                    try:
                        reviewer = critic.xpath("./div[2]/span//@title")[0].replace(' Reviews','')
                        review['reviewer'] = name
                        name = reviewer
                        review['site'] = newUrl(critic.xpath("./div[2]/span//@href")[0])
                    except:
                        pass
                    review['name'] = name
                    
                    
                    review['date'] = critic.xpath("./div[2]/span[@class='date']/text()")[0]
                    reviews = '\n'.join([criticComment.strip() for criticComment in critic.xpath(".//p[@class='clear']/text()") if criticComment.strip() != ''])
                    try:
                        reviews = reviews + critic.xpath(".//p[@class='clear']/*[not(@class='event-more-link')]/text()")[0]#手动追加展开内容
                    except:
                        pass
                    try:
                        review['reviews'] = f"{reviews}: {critic.xpath('./p//@href')[0]}"
                    except:
                        review['reviews'] = f'{reviews}'
                    try:
                        moreReviews = []
                        comments = critic.xpath(".//div[@class='comments']//div[@class='comment']")
                        for comment in comments:
                            moreReview = []
                            moreReview.append(comment.xpath('.//div//a/text()')[0])#用户名
                            moreReview.append(comment.xpath('.//p/text()')[0])#楼中楼
                            moreReview.append(comment.xpath('.//div/span/text()')[0])#评论日期
                            moreReviews.append(moreReview)
                            review['moreReviews'] = moreReviews
                    except:
                        pass
                    review['addTime'] = time.strftime('%Y/%m/%d %-H:%-M:%-S')
                    review['group'] = ratingTitle[i].replace(' Rating','')
                    criticList = [value for value in review.values()]
                    #print(criticList)
                    with open(outputPath, 'at', encoding = 'utf-8', newline = '') as csvfile:
                        writer = csv.writer(csvfile)
                        #writer.writerow(criticList)
                except Exception as e:
                    print(e)
            i += 1
    else:
        rating = dom_tree.xpath("//div[@id='editions']//div[contains(@class,'review')]/text()")
        ratingTitle = dom_tree.xpath("//div[@id='editions']//span[@class='rating-title']/text()")
        for i in range(len(ratingTitle)): 
            print(f'Collected {ratingTitle[i]}: {rating[i]}({avgRating[i]})')
        urlList = [newUrl(url) for url in dom_tree.xpath("//table[@class='collected-issues']//td[@class='issues']//@href")]
        urlLists.extend(urlList)
    return urlLists

if __name__ == "__main__":
    flatten = lambda x: [y for l in x for y in flatten(l)] if type(x) is list else [x]
    start_time = time.time()
    url = 'https://comicbookroundup.com'
    Links = sortList(flatten(list(set(homePage(url)))))
    newAdd = len(Links)
    #while newAdd != 0:
    for Link in Links:
        print(f'\nProcessing {Link}')
        urlList = sortList(flatten(issueReview(Link)))
        #newAdd = len([Links.append(url) for url in urlList if url not in Links])
        #print(f'Find {newAdd} more new page(s)')
    print(f"{time.strftime('%Y/%m/%d')}	Finish Time: {datetime.fromtimestamp(time.time()-start_time).strftime('%-H:%-M:%-S.%f')}")
    exit()

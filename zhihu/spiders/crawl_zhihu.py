import requests
import scrapy
import datetime
try:
    import cookielib
except:
    import http.cookiejar as cookielib
    
try:
    import urlparse as parse
except:
    from urllib import parse    

import re
import time
import sqlite3
import json
from bs4 import BeautifulSoup
from scrapy.loader import ItemLoader
from zhihu.items import ZhihuAnswerItem, ZhihuQuestionItem

class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['https://www.zhihu.com/']
    
    start_answer_url = "https://www.zhihu.com/api/v4/questions/{0}/answers?sort_by=default&include=data%5B%2A%5D.is_normal%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccollapsed_counts%2Creviewing_comments_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Cmark_infos%2Ccreated_time%2Cupdated_time%2Crelationship.is_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cupvoted_followees%3Bdata%5B%2A%5D.author.is_blocking%2Cis_blocked%2Cis_followed%2Cvoteup_count%2Cmessage_thread_token%2Cbadge%5B%3F%28type%3Dbest_answerer%29%5D.topics&limit={1}&offset={2}"


    headers = {
        'HOST': 'www.zhihu.com',
        'Referer': 'https://www.zhihu.com',
        'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en',
    }


    def gen_proxy_file(self):
        r = requests.get('https://www.us-proxy.org/')
        soup = BeautifulSoup(r.text, 'html.parser')
        with open('C://TEMP//zhihu//zhihu//proxy_us.txt', 'w') as f:
            for row in soup.tbody.findAll('tr'):
                first_col = row.findAll('td')[0].contents
                second_col = row.findAll('td')[1].contents
                f.write('http://'+first_col[0].strip()+':'+second_col[0].strip()+'\n' )

    def parse(self, response):
        print("parse function has been called.")
        all_urls = response.css("a::attr(href)").extract()
        all_urls = [parse.urljoin(response.url, url) for url in all_urls]
        all_urls = filter(lambda x: True if x.startswith("https") else False, all_urls)
        for url in all_urls:
            match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", url)
            if match_obj:
                # question
                request_url = match_obj.group(1)
                yield scrapy.Request(request_url, headers=self.headers, callback=self.parse_question)
            else:
                # if not question
                yield scrapy.Request(url, headers=self.headers, callback=self.parse)
                
    def parse_question(self, response):
        """
        question page question item
        """
        if "QuestionHeader-title" in response.text:
            # 
            match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", response.url)
            if match_obj:
                question_id = int(match_obj.group(2))
            item_loader = ItemLoader(item=ZhihuQuestionItem(), response=response)
            item_loader.add_css("title", "h1.QuestionHeader-title::text")
            item_loader.add_css("content", ".QuestionHeader-detail")
            item_loader.add_value("url", response.url)
            item_loader.add_value("zhihu_id", question_id)
            item_loader.add_css("answer_num", ".List-headerText span::text")
            item_loader.add_css("comments_num", ".QuestionHeader-Comment button::text")
            item_loader.add_css("watch_user_num", ".NumberBoard-value::text")
            item_loader.add_css("topics", ".QuestionHeader-topics .Popover div::text")
            question_item = item_loader.load_item()
        else:
            
            match_obj = re.match("(.*zhihu.com/question/(\d+))(/|$).*", response.url)
            if match_obj:
                question_id = int(match_obj.group(2))
            item_loader = ItemLoader(item=ZhihuQuestionItem(), response=response)
            # item_loader.add_css("title", ".zh-question-title h2 a::text")
            item_loader.add_xpath("title",
                                  "//*[@id='zh-question-title']/h2/a/text()|//*[@id='zh-question-title']/h2/span/text()")
            item_loader.add_css("content", "#zh-question-detail")
            item_loader.add_value("url", response.url)
            item_loader.add_value("zhihu_id", question_id)
            item_loader.add_css("answer_num", "#zh-question-answer-num::text")
            item_loader.add_css("comments_num", "#zh-question-meta-wrap a[name='addcomment']::text")
            # item_loader.add_css("watch_user_num", "#zh-question-side-header-wrap::text")
            item_loader.add_xpath("watch_user_num",
                                  "//*[@id='zh-question-side-header-wrap']/text()|//*[@class='zh-question-followers-sidebar']/div/a/strong/text()")
            item_loader.add_css("topics", ".zm-tag-editor-labels a::text")
            question_item = item_loader.load_item()
            
        print("---------------------------here.")    
        yield scrapy.Request(self.start_answer_url.format(question_id, 20, 0), headers=self.headers, callback=self.parse_answer)
        yield question_item


    def parse_answer(self, reponse):
        """
        answer
        """
        ans_json = json.loads(reponse.text)
        is_end = ans_json["paging"]["is_end"]
        next_url = ans_json["paging"]["next"]
        # 
        for answer in ans_json["data"]:
            answer_item = ZhihuAnswerItem()
            answer_item["zhihu_id"] = answer["id"]
            answer_item["url"] = answer["url"]
            answer_item["question_id"] = answer["question"]["id"]
            answer_item["author_id"] = answer["author"]["id"] if "id" in answer["author"] else None
            answer_item["content"] = answer["content"] if "content" in answer else None
            answer_item["praise_num"] = answer["voteup_count"]
            answer_item["comments_num"] = answer["comment_count"]
            answer_item["create_time"] = answer["created_time"]
            answer_item["update_time"] = answer["updated_time"]
            answer_item["crawl_time"] = datetime.datetime.now()
            yield answer_item
        if not is_end:
            yield scrapy.Request(next_url, headers=self.headers, callback=self.parse_answer)

                

    def get_xsrf(self, session, header):
        # xsrf code
        response = session.get('https://www.zhihu.com', headers=header)
        # print(response.text)
        match_obj = re.match('[\s\S]*name="_xsrf" value="(.*?)"', response.text)
        if match_obj:
            return match_obj.group(1)
        return ''


    def get_captcha(self, session, header):
        #
        captcha_url = 'https://www.zhihu.com/captcha.gif?r=%d&type=login&lang=cn' % (int(time.time() * 1000))
        response = session.get(captcha_url, headers=header)
        # save 
        with open('captcha.gif', 'wb') as f:
            f.write(response.content)
            f.close()
    
        # open the capchar
        from PIL import Image
        try:
            img = Image.open('captcha.gif')
            img.show()
            img.close()
        except:
            pass
    
        captcha = {
            'img_size': [200, 44],
            'input_points': [],
        }
        points = [[22.796875, 22], [42.796875, 22], [63.796875, 21], [84.796875, 20], [107.796875, 20], [129.796875, 22],
                  [150.796875, 22]]
        seq = input('input locations:\n>')
        for i in seq:
            captcha['input_points'].append(points[int(i) - 1])
        return json.dumps(captcha)


    def start_requests(self):
        self.gen_proxy_file()
        
        conn = sqlite3.connect("C://TEMP//zhihu//sqlite_db//zhihu.db")
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS zhihu_question (zhihu_id TEXT, topics TEXT, url VARCHAR, title VARCHAR, content VARCHAR, answer_num INT, comments_num INT, watch_user_num INT, click_num INT, crawl_time DATETIME,CONSTRAINT zhurl UNIQUE (url)); ''')
        c.execute('''CREATE TABLE IF NOT EXISTS zhihu_answer (zhihu_id TEXT, url VARCHAR, question_id VARCHAR, author_id VARCHAR, content LONGTEXT, praise_num INT, comments_num INT,create_time DATETIME, update_time DATETIME, crawl_time DATETIME,CONSTRAINT zhurl UNIQUE (url)); ''')
        
        agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_12_6) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8'
        header = {
                'HOST': 'www.zhihu.com',
                'Referer': 'https://www.zhihu.com',
                'User-agent': agent,
                }
        session = requests.session()
        account = '' 
        password = ''
        post_url = 'https://www.zhihu.com/login/email'
        post_data = {
                'captcha_type': 'cn',
                '_xsrf': self.get_xsrf(session, header),
                'email': account,
                'password': password,
                'captcha': self.get_captcha(session, header),
            }
    
        response_text = session.post(post_url, data=post_data, headers=header)
        response_text = json.loads(response_text.text)
        if 'msg' in response_text and response_text['msg'] == '登录成功':
            print('logged in')
            for url in self.start_urls:
                print("--------------Working on "+url)
                yield scrapy.Request(url, headers=self.headers,callback=self.parse)
        else:
            print('Not logged in')

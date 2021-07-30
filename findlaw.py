#!/usr/bin/env python
import bs4
import requests as req
import re
import csv
import ipaddress
import tqdm
import datetime
import multiprocessing
import sys
import os
from time import time

class findlaw(object):

    def __init__(self):
        '''
        law crawler object scrapping question and answer from website hosted by www.66law.cn
        '''
        self.headers = { 
            "Accept":"text/html,application/xhtml+xml,application/xml;9=0.9,*/*;q=0.8",
            "Accept-Encoding":"gzip,deflate",
            "Accept-Language":"zh-CN,zh;q=0.8",
            "X-Forwarded-For": "1.1.1.5",
            "Cache-Control":"max-age=0",
            "Connection":"keep-alive",
            "Upgrade-Insecure-Requests":"1",
            "Host": "china.findlaw.cn",
            "Referer": "http://china.findlaw.cn/",
            "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:58.0) Gecko/20100101 Firefox/58.0"
        }
        self.ip_add = ipaddress.IPv4Network('88.88.88.88')
        self.BASE_url = "http://china.findlaw.cn/ask/question"
        self.QUES = {}
        self.ANS = {}
        self.LAWYER = {}
        self.v_icon = '实名认证律师'
        self.x_icon = '诚信律师'
        self.b_icon = "优秀版主"
        self.lastest_date = None

    def cook_soup(self,qid):
        '''
        Get beautiful soup object from bs4 and qid or url (To be implemented)
        '''
        url_h = "{}_{}.html".format(self.BASE_url,qid)
        # print(url_h)
        html_h = req.get(url_h, timeout=10, headers=self.headers).text
        soup_h = bs4.BeautifulSoup(html_h,'lxml')

        return soup_h

    def eat_soup(self,qid):
        '''
        Store information about qid passed into field of this object
        '''
        soup_cooked = self.cook_soup(qid)
        q_dic = {}

        ## Deal with 404 and restrictions:
        # 404
        if(soup_cooked.select_one("body > div.faf-main > div.clearfix > div.faf-left > div.none-mes")):
            return None
        # Unwarranted:
        if(soup_cooked.select_one('body > div.container > div > div.audit > div > div.audit-info')):
            return None

        # First get the question
        ques_div = soup_cooked.select_one("body > div.consult_main > div > div > div.fl.wl_aside > div.c_title")
        # Title:
        title = ques_div.select_one('h1').text
        title = title.strip()
        title = title.replace("\n", " ")
        title = title.replace("\r", " ")
        q_dic['CONTENT'] = title
        # # Content:
        # content = ques_div.select_one("p.mt10.f18.lh32.s-c6").text
        # content = content.strip()
        # content = content.replace("\n"," ")
        # content = content.replace("\r"," ")
        # q_dic['CONTENT'] = content
        # location and time
        location_date = ques_div.select("span.txt")
        date_s = location_date[0].text[5:]
        q_dic['DATE'] =  date_s
        self.lastest_date = datetime.datetime.strptime(date_s, "%Y-%m-%d %H:%M:%S")
        # print(q_dic['DATE'])
        loction = location_date[1]
        loction = loction.select('a')
        loction_lst = [loc.text for loc in loction]
        loction_txt = '-'.join(loction_lst)
        q_dic['LOCATION'] = loction_txt
        q_dic['CATEGORY'] = location_date[2].text 
        q_dic['KEYWORDS'] = location_date[3].text

        # Then get the answers
        ans_ul = soup_cooked.select_one("body > div.consult_main > div > div > div.fl.wl_aside > div.wl_list_cont > ul")
        ## Deal With No answer
        if not ans_ul:
            q_dic['ANS_NUM'] = 0
            self.QUES[qid] = q_dic
            return
        else:
            q_dic['ANS_NUM'] = len(ans_ul.select("li"))
            self.QUES[qid] = q_dic

        ans_lis = ans_ul.select("li.item")

        for li in ans_lis:
            a_dic = {"QID":qid}
            name = li.select_one('p.tl').text
            name = name.replace("\n","")
            a_dic['NAME'] = name
            lawyer_loc = li.select_one("p.consult_mobile").text
            lawyer_loc = re.findall(r'\（.*?\）',lawyer_loc)[0]
            a_dic['LAWYER_LOC'] = lawyer_loc[6:-1]
            reply = li.select_one("p.desc.content_links").text
            reply = reply.strip()
            reply = reply.replace("\n", " ")
            reply = reply.replace("\r", " ")
            a_dic['REPLY'] = reply
            date = li.select_one("p.info").text
            a_dic['DATE'] = date[5:]

            like_div = li.select_one("span.user")
            if (like_div):
                # print(li)
                # with open('temp.txt','w') as f:
                #     f.write(str(li))
                num_like = like_div.select_one("span.num").text 
                a_dic['NUM_LIKE'] = num_like
                a_dic['SPONSOR'] = 0
            else:
                a_dic['NUM_LIKE'] = None
                a_dic['SPONSOR'] = 1

            ## Here we store url to the laywer and the renzheng information of the lawyer
            lawyer_p = li.select_one('p.tl')
            v_exist = lawyer_p.select_one('span.icon-v')
            x_exist = lawyer_p.select_one('span.icon-x')
            b_exist = lawyer_p.select_one('span.icon-b')
            best_icon = li.select_one('span.icon-best')
            if (v_exist):
                a_dic[self.v_icon] = 1
            else:
                a_dic[self.v_icon] = 0
            
            if (x_exist):
                a_dic[self.x_icon] = 1
            else:
                a_dic[self.x_icon] = 0

            if (b_exist):
                a_dic[self.b_icon] = 1
            else:
                a_dic[self.b_icon] = 0

            if (best_icon):
                a_dic['BEST_ICON'] = 1
            else:
                a_dic['BEST_ICON'] = 0

            div_pop = li.select_one('div.pop-box')

            # Hover over and what pops up
            if (div_pop):
                firm = div_pop.select_one('p.address').text
                a_dic['FIRM'] = firm
                specialty = div_pop.select_one('p.good-for').text[3:]
                a_dic['SPECIALTY'] = specialty
                position = div_pop.select_one('div.law-box').text.replace(name,"")
                position = position.strip()
                a_dic['POSITION'] = position
                likes_helped = div_pop.select('em.green.font')
                a_dic['LIKES_ALL'] = likes_helped[0].text
                a_dic['HELPED_ALL'] = likes_helped[1].text
                phone_number = div_pop.select_one('span.fl.phone-p').text
                a_dic['PHONE'] = phone_number


            key_holder = "{}_{}".format(name,qid)
            self.ANS[key_holder] = a_dic

    def dump_csv(self, relative_path = ""):
        """
        Dump the stored information into the relative path that is passed to relative path
        """
        # ques_fields = list(self.QUES[4].keys())
        ques_fields = ['QID','CONTENT','DATE','LOCATION','CATEGORY','KEYWORDS','ANS_NUM']
        ans_fields = ["QID_NAME",'QID','NAME','LAWYER_LOC','REPLY','DATE','NUM_LIKE','SPONSOR',self.v_icon, self.x_icon,self.b_icon,'BEST_ICON','FIRM','SPECIALTY','POSITION','LIKES_ALL','HELPED_ALL','PHONE']
        with open('{}ques.csv'.format(relative_path), 'a', newline='',encoding='utf-8') as f:
            writer = csv.DictWriter(f,fieldnames= ques_fields)
            writer.writeheader()
            for key, value in self.QUES.items():
                value['QID'] = key
                writer.writerow(value)

        with open('{}ans.csv'.format(relative_path), 'a',newline='',encoding="utf-8") as f:
            writer = csv.DictWriter(f,fieldnames=ans_fields)
            writer.writeheader()
            for key, value in self.ANS.items():
                value['QID_NAME'] = key
                writer.writerow(value)

    def drink_soup(self,start,end):
        """
        self.eat_soup() for every qid in qid_collection, spell out the error
        """
        for qid in tqdm.tqdm(range(start,end),desc = 'qid loop'):
            try:
                self.eat_soup(qid)
                # print('Hi')
                # print(self.lastest_date.month)
                # print(self.lastest_date.month == 2)
                # if (stop_month == self.lastest_date.month):
                #     print("End point reached!")
                #     break 
            except Exception as e:
                print("Qid: {} throws an exception {}".format(qid,e))
                continue

    def browse_pages(self,page_start = 1,page_end = 51143):
        '''
        Browse a range of page and get the question url;
        Log it inside the dictionary
        '''
        p_url = ""
        ques_lst = []
        
        for pidx in tqdm.tqdm(range(page_start,page_end+1), desc='browser loop'):
            # if (pidx == 0):
            #     p_url = 'https://china.findlaw.cn/ask/browse/'
            # else:
            p_url = "https://china.findlaw.cn/ask/browse_page{}/".format(pidx)

            html_h = req.get(p_url, timeout=30, headers=self.headers).text
            soup_h = bs4.BeautifulSoup(html_h,'lxml')
            contain_e = soup_h.select_one('body > div.container > div > div.fl.wl_aside')
            ul_lst = contain_e.select('ul.c_nor_list') 
            for ul in ul_lst:
                p_lst = ul.select('p.tl')
                for p in p_lst:
                    qid = (p.select_one('a')['href'])[38:-5]
                    # print(qid)
                    # ques_lst.append(qid)
                    # ques_lst.append(p['a'])
                    try:
                        self.eat_soup(qid)
                    except Exception as e:
                        print("\n Qid: {} throws an exception {}".format(qid,e))
                        continue        

        # self.eat_soup(ques_lst)

    def find_monthqid(self, month, start = 43065714, end = 50310850):
        '''
        Binary search for the month range to scrape
        returns a tuple (qidstart,qidend)
        Not implemented
        '''
        pass

def scrap_qid(start,end,dir='Datatest'):
    scraper = findlaw()
    e = None
    # test_scrap.dump_csv(relative_path = 'Data/test.csv')
    try:
        # test_scrap.eat_soup(57542030)
        scraper.drink_soup(start,end)
    except KeyboardInterrupt:
        scraper.dump_csv(relative_path = '{}/{}to{}'.format(dir,start,end))
        print('Interrupted ----------------------------------------------------------------------------------')
        global pool
        pool.close()
        pool.terminate()
        pool.join()
        sys.exit()

    except Exception as e:
        print('Quit processing due to exception {}.'.format(e))
        scraper.dump_csv(relative_path = '{}/{}to{}'.format(dir,start,end))

    if (not e):
        scraper.dump_csv(relative_path = '{}/{}to{}'.format(dir,start,end))

    return True

if __name__ == "__main__":

    start = 50310850 
    end = 59897334
    # end = start + 32
    pieces = 64

    increment = int((end - start)/pieces)
    print(increment)
    ticks = [start + i*increment for i in range(pieces+1)]

    with multiprocessing.Pool(processes=16) as pool:
        try:
            results = pool.starmap(scrap_qid, [(ticks[i],ticks[i+1]) for i in range(pieces)])
        except KeyboardInterrupt:
            print('Interrupted ------Outer----------------------------------------------------------------------------')
            # break
            # global pool
            pool.close()
            pool.terminate()
            pool.join()

        
        # print(results)

    # print(ticks)
    # test_scrap = findlaw()
    # # print("We have question as {}".format(test_scrap.QUES))
    # # print("All the answers are {}".format(test_scrap.ANS))
    # # print(test_scrap.x_icon)
    # e = None
    # test_scrap.dump_csv(relative_path = 'Data/test.csv')
    # try:
    #     begin_id = 43065714
    #     end_id = 57555989
    #     # test_scrap.eat_soup(57542030)
    #     test_scrap.drink_soup(range(begin_id , begin_id + 500000))
    # except Exception as e:
    #     print('Quit processing due to exception {}.'.format(e))
    #     test_scrap.dump_csv(relative_path = 'Data/2018_Mar')

    # if (not e):
    #     test_scrap.dump_csv(relative_path = 'Data/2018_Mar')

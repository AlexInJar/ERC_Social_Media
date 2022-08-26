from multiprocessing import Pool, TimeoutError
import time
import os

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

def f(x,y):
    return x*y

if __name__ == '__main__':
    pool = Pool(processes=4)              # start 4 worker processes

    # print "[0, 1, 4,..., 81]"
    print(pool.starmap(f, [(i,2*i) for i in range(10)]))

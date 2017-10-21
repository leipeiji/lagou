# -*- coding: utf-8 -*-
# authon --- dengfenglai
# createDate --- 2017-10-21
# Operation Environment 本程序 是 win10 + python3 环境下测试成功
# function --- 抓取 https://www.lagou.com/ 职位信息,可以保存到excel csv mysql 数据裤
# ideas and methods ---  两种保存方式，第一抓取一条职位信息 就保存数据裤一次 ，第二种，抓取一页后 保存到excel，最后合并每页
#                   --- 先获取 每一页的 详情链接，在得到给链接的具体信息 ，处理每页，每页信息 保存成一个excel文件
#                   --- 最后用 pandas 裤合并所有单页文件 到一个文件
# explain ---  拉勾网 反爬虫机制，抓取一会，就会让登录 或抛出其他错误  ，测试等待最多40秒左右，能获取到数据 建议用单线程就行了
#  How to Start ?  如何开始这个程序?
#         --- first: 把一起的 config.py 文件 放到和 本程序文件 一个目录中;
#                    建议保存到mysql数据裤，运行前 确保下面的模块已经安装好，
#         --- second: 配置 方法  conMysql 中的 mysql数据库连接信息，
#                      把 isCreateDataBaseAndTable 开关设为 True,完成创建数据库和表操作，完成后，设为False ；之前确保已经连接到数据库
#         --- third: 在 main 方法中  开启是否 存toExcel csv文件，当然 可以同时，存入 数据库和表格文件
#         --- fourth: 设置 你要抓取的城市 和 职位名字，大概在560行之后 ，配置 city 和kw
#         ---- fifth 运行程序。。。。。。
# How to you get from this procedure?
#         ----  整体python抓取数据的大概流程，遇到请求失败，如何请求，保证数据最大程度获取？
#         ----  写入 Excel Csv  mysql 等写入和存取操作 ,在mysql中判断 重复记录
#         ----  各种出错情况的处理，真正实现抓取的代码不到20%，剩余的都是 在做防止各种意外情况出现的错误，尽可能避免他
#         ---- 本程序没有用代理，抓取速度较慢，用代理可能快些 ，因为拉勾网反爬虫很厉害，

# I hope your  suggestion and indication
#         --- 本人小白学习pyhon 2月，一切都是刚刚起步，只是知道pyhton的 皮毛，希望大佬给出指点 ，谢谢
try:
    # dengfenglai 是一个文件夹，如果没有防止出错，就直接把config 配置文件 和这个程序文件放到一个目录中...
    # 配置文件中 主要包含 浏览器请求头 文件根目录设置等 一些通用的文件..
    from dengfenglai.config import *
except:
    from config import *

import json,os,requests,re,time,math,csv,datetime,sys
from bs4 import BeautifulSoup as bf
# from multiprocessing import Pool
from openpyxl import Workbook # pip install openpyxl
import pandas as pd
from urllib.parse import quote
# 直接安装msql 可能出问题，建议去官方 下载 whl文件安装
#  navicat for mysql10.0.11简体中文破解版 链接  http://pan.baidu.com/s/1cJbyhg
# mysql whl 文件下载地址 https://pypi.python.org/pypi/mysqlclient/
# mysql whl 懒人直接下载链接  http://pan.baidu.com/s/1dEX8ci1
import MySQLdb

class Lagou():
    def __init__(self,city,kw,OPEN_MYSQL=True,OPEN_DEBUG=True):
        self.city=quote(city)
        self.kw=kw
        self.kw2=quote(kw)
        self.OPEN_MYSQL=OPEN_MYSQL #  开启 mysql 存储，提取一条记录插入一次数据裤，这样数据不会丢；
        self.OPEN_DEBUG=OPEN_DEBUG # 建议开启 调试信息 方便知道数据是否真正输出了
        self.COUNT_PAGE_LINK=0 # 记录每页链接 请求的出错次数 ，没出错一次，等待 COUNT_PAGE_LINK*15秒，出错次数越多，等待下次请求的间隔越长，6次，最多90秒等待结束
        self.COUNT_DETIAL_LINK=0  #记录职位详情信息 链接 请求的出错次数
        self.fetchDate=str(time.strftime("%Y-%m-%d", time.localtime()))
        self.SavePath=self.createDir() # 构建保存 excel 或csv 文件的目录，这是一页数据处理完后，保存到excel中一次
        if self.OPEN_MYSQL:
            self.con = self.conMysql()

    def getLagouInfo(self, pn=1, isGetPage=False):
        '''
        返回每一页的所有信息列表
        :param city:
        :param kw:
        :param pn:
        :param isGetPage:
        :param Mcount:
        :return: [['2017-10-21', 1, '淘宝客服/天猫客服', '上海', '徐汇区', '2017-10-20 18:06:08', '1-3年', '4k-6k', '大专', '上海乙豆信息科技有限公司', '15-50人', '运营/编辑/客服', '客服', '可带宠物上班、带薪年假、发展空间大', 'A轮.....]
        '''
        try:
            if pn == 1:
                first = 'true'
            else:
                first = 'false'
            data = {'first': first,
                    'kd': self.kw,
                    'pn': pn,
                    }
            Referer = 'https://www.lagou.com/jobs/list_{kw}?city={city}&cl={c1}&fromSearch=true&labelWords=&suginput'.format(
                kw=self.kw2, city=self.city, c1='false')
            RefererDetail = 'https://www.lagou.com/jobs/list_{kw}?city={city}&cl={c1}&fromSearch=true&labelWords=&suginput'.format(
                kw=self.kw2, city=self.city, c1='true')
            headers = {'user-agent': UA,
                       'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                       'Host': 'www.lagou.com',
                       'Upgrade-Insecure-Requests': '1',
                       'Connection': 'keep-alive',
                       'Origin': 'www.lagou.com',
                       'Accept-Encoding': 'gzip, deflate, br',
                       'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                       'Accept': 'application/json, text/javascript, */*; q=0.01',
                       'X-Anit-Forge-Code': '0',
                       'X-Anit-Forge-Token': 'None',
                       # 'Cookie':'JSESSIONID=ABAAABAABEEAAJAA10B1578FC05F240FBDE0EA493609792; SEARCH_ID=7fcf314f96d44c9aa3dad27cf9a47eca; user_trace_token=20171012101507-0d4f2b69-5879-4906-9dfb-3dd77916b942; _ga=GA1.2.2008091768.1507774423; Hm_lvt_4233e74dff0ae5bd0a3d81c6ccf756e6=1507774423; Hm_lpvt_4233e74dff0ae5bd0a3d81c6ccf756e6=1507775391; LGSID=20171012101508-2b5ba164-aef3-11e7-8c7f-525400f775ce; PRE_UTM=; PRE_HOST=; PRE_SITE=; PRE_LAND=https%3A%2F%2Fwww.lagou.com%2Fjobs%2Flist_%25E6%259C%25BA%25E5%2599%25A8%25E5%25AD%25A6%25E4%25B9%25A0%3Fpx%3Ddefault%26city%3D%25E4%25B8%258A%25E6%25B5%25B7; LGRID=20171012103116-6c24567d-aef5-11e7-94d0-5254005c3644; LGUID=20171012101508-2b5ba3f8-aef3-11e7-8c7f-525400f775ce; _gid=GA1.2.1835961006.1507774425; TG-TRACK-CODE=search_code; _gat=1',
                       'Referer': Referer  # 这个Referer很重要，要不请求不到数据了
                       }
            RequestsUrl = 'https://www.lagou.com/jobs/positionAjax.json?city={city}&needAddtionalResult=false&isSchoolJob=0'.format(
                city=self.city)
            r = requests.post(RequestsUrl, data=data, headers=headers)
            print(r.status_code, r.url)
            if r.status_code == 200:
                # print(r.text)
                jsonInfo = json.loads(r.text)
                if isGetPage:
                    totalCount = int(jsonInfo.get('content').get('positionResult').get('totalCount'))
                    totalPage = math.ceil(totalCount / 15)
                    if totalPage > 30: totalPage = 30  # 拉钩网最多显示30页
                    return totalPage
                else:
                    results = jsonInfo.get('content').get('positionResult').get('result')
                    allinfoList = []
                    i = 0
                    for ls in results:
                        i += 1
                        # print(ls)
                        positionId = int(ls.get('positionId'))
                        # 检查是否本条职位信息 已经保存过了，如果保存过了，就不保存到数据库了
                        if self.OPEN_MYSQL:
                            if self.checkReiterationPositionId(self.con, positionId):
                                self.myFormat('本条职位ID\t %d \t已经获取过了，跳过哦'%positionId)
                                continue

                        positionName = ls.get('positionName', '')
                        curCity = ls.get('city', '')
                        district = ls.get('district', '')
                        try:
                            companyLabelList = '--'.join(ls.get('companyLabelList', []))
                        except:
                            companyLabelList = ''
                        createTime = ls.get('createTime', '')
                        workYear = ls.get('workYear', '')
                        education = ls.get('education', '')
                        salary = ls.get('salary', '')
                        companyFullName = ls.get('companyFullName', '')
                        companySize = ls.get('companySize', '')
                        firstType = ls.get('firstType', '')
                        secondType = ls.get('secondType', '')
                        positionAdvantage = ls.get('positionAdvantage', '')
                        financeStage = ls.get('financeStage', '')
                        content = self.phoneDetailInfo(positionId, RefererDetail)
                        self.COUNT_DETIAL_LINK = 0 # 错误次数恢复成0,下次初始值 开始,要不下次会接着上次的 开始，这不是想要的结果
                        infoList = [self.fetchDate, pn, positionName, curCity, district, createTime, workYear, salary,
                                    education, companyFullName, companySize, firstType,
                                    secondType, positionAdvantage, financeStage, companyLabelList, content, positionId,
                                    self.kw]
                        # 插入数据库
                        if self.OPEN_MYSQL:
                            if len(infoList) == 19: # 这里保存19个有些的职位信息
                                self.executeInsert(self.con, [infoList], pn, i)

                        allinfoList.append(infoList) # 这里是 为 保存到 excel csv用的 list

                        if self.OPEN_DEBUG:
                            print(infoList)
                            printText = '第%d页\t第%d条记录处理完毕' % (pn, i)
                            self.myFormat(printText)
                            self.myFormat('正常输出等待', fillMode='right', symbol='.')
                        self.waitTime(2) # 等待2秒 进行下一页请求.....
                    return allinfoList
            else:
                print('服务器拒绝访问。。。。')
                return None
        except Exception as e: # 请求出错，再次请求 ，最多请求6次，还出错，就放弃
            self.COUNT_PAGE_LINK += 1
            print('出错次数是',self.COUNT_PAGE_LINK)
            if self.COUNT_PAGE_LINK <= 6:
                print(e, '第\t %d 页\t%d次\t请求链接出现问题，等待\t%d秒，重试......' % (int(pn), self.COUNT_PAGE_LINK, self.COUNT_PAGE_LINK * 15))
                # 每出错一次，等待时间再增加些，这样整体成功的可能性更大,第一次 等 20，第二次等40，60 80...
                self.waitTime(self.COUNT_PAGE_LINK * 15)
                # 第一次获取总页码 失败时，用到
                if isGetPage:
                    temp = True
                else:
                    temp = False
                return self.getLagouInfo(pn=1, isGetPage=temp)
            else:
                self.COUNT_PAGE_LINK = 0
                print('error stop')
                return None

    def phoneDetailInfo(self,positionId, Referer):
        '''
        得到职位详细的信息
        :param positionId: 每个职位唯一识别id  链接类似于 https://m.lagou.com/jobs/3660919.html
        :param Referer: 请求头的一个 Referer 参数 ,这里是动态变化的，暂时没有用
        :param curCount: 拉勾网饭爬虫很强，请求频繁，就会转向登录页面，或其他页面，记录请求失败的次数，失败后，等待一会，再次请求
        :param curCount: 请求超过规定次数时，放弃请求，返回空信息
        :return: 职位具体介绍
        '''
        detailUrl = 'https://m.lagou.com/jobs/{positionId}.html'.format(positionId=positionId)
        headers = {'user-agent': UA_PHONE, # 这里抓取无线端的 详情职位信息
                   # 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                   # 'Host': 'www.lagou.com',
                   # 'Referer':Referer,
                   # 'Upgrade-Insecure-Requests':'1',
                   # 'Accept-Encoding': 'gzip, deflate, br',
                   # 'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
                   # 'Accept': 'application/json, text/javascript, */*; q=0.01',
                   }
        r = requests.get(detailUrl, headers=headers)
        print('请求的url是：', detailUrl)
        print('实际返回的url是：', r.status_code, r.url)
        # 判断一个地址 是否是回到 登录页面  一个异常地址 一个正常  ，因访问过于频繁 会调到登录页面  等待一段 相对好多了
        #  https://passport.lagou.com/login/login.html?msg=validation&uStatus=2&clientIp=223.88.24.13
        # https://www.lagou.com/jobs/2458365.html PC 端网站
        # https://m.lagou.com/jobs/2042657.html 无线端

        if r.status_code == 200:
            # print(r.text)
            soup = bf(r.text, 'lxml')
            try:
                content = soup.select('.positiondesc .content')[0].text
                return content
            except Exception as e:
                # 反爬虫机制，拉勾网返回 这样的登录地址，这里要等待一段时间 重新请求 https://passport.lagou.com/login/login.html?msg=validation&uStatus=2&clientIp=223.88.24.13
                if 'login' in r.url or 'lagouhtml' in r.url:
                    self.COUNT_DETIAL_LINK += 1
                    if self.COUNT_DETIAL_LINK <= 5:
                        self.myFormat( '第%d次请求失败，没有获取到内容,等会继续请求' % (self.COUNT_DETIAL_LINK + 1))
                        if self.OPEN_DEBUG:
                            debugInfo = '正在进行\t第%d次\t尝试获取详情职位信息' % (self.COUNT_DETIAL_LINK + 1)
                            self.myFormat(debugInfo, symbol='-')
                        self.myFormat('获取详情时，请求受限，等待%d秒重试' % (self.COUNT_DETIAL_LINK * 15), fillMode='right', symbol='.')
                        self.waitTime(self.COUNT_DETIAL_LINK * 15)
                        # 失败次数超过5次，停止请求了
                        return self.phoneDetailInfo(positionId, Referer)
                    else:
                        self.myFormat('很遗憾，最终还是获取本页信息失败了')
                        content = '请求失败了'
                        return content

    def waitTime(self,stayTime):
        '''
        格式话输出等待时间，给定一个数字的时间值，返回类似下面的形式
        wait 4秒.....
        wait 3秒.....
        wait 2秒.....
        wait 1秒.....
        :param stayTime: int 类型 给定时间 比如 5 ，就是等待5秒
        :return: 每隔一秒输出一次 直观的看到等待的时间
        '''
        self.myFormat('等待%d秒' % stayTime, fillMode='right', symbol='.')
        for second in range(stayTime, 0, -1):
            time.sleep(1)
            print('wait %d秒.....' % second)

    def toExcel(self,resultsList, pn, AllExcelHead, sheetName='data'):
        '''
        保存到Excel
        :param resultsList:每页数据list
        :param pn:页码
        :param AllExcelHead:表头
        :param sheetName:sheet名
        :return:
        '''
        if len(resultsList) == 0:
            printText = '列表内容空，请检查请求返回值'
            self.myFormat(printText)
            return None
        try:
            filePath = '{}\{}'.format(self.SavePath, self.kw)
            if not os.path.exists(filePath):
                os.makedirs(filePath)
            doc = r'{}\{}_{}_{}.{}'.format(filePath, str(pn), self.fetchDate, self.kw, 'xlsx')
            print(doc)
            # 在内存创建一个工作簿obj
            wb = Workbook()
            ws = wb.active
            # 给sheet明个名
            ws.title = sheetName
            # 向第一个sheet页写数据吧 格式 ws2['B1'] = 4
            ws.append(AllExcelHead)
            for k, line in enumerate(resultsList):
                try:
                    ws.append(line)
                    if self.OPEN_DEBUG:
                        print('写入第%d条记录完毕' % (k + 1))
                except Exception as e:
                    print(e, '第%d条记录有问题，已经忽略' % (k + 1))
                    continue
                printText = '恭喜你，第%d页\t写入完毕' % (k + 1)
                self.myFormat(printText, symbol='☺')
            wb.save(doc)
            print('数据保存完毕,文件路径是\t{}'.format(doc))
        except Exception as e:
            print(e, '函数 \t toExcel\t出现问题了')
            return

    def toCsv(self,resultsList, pn, AllExcelHead, sheetName='data'):
        '''
        保存到csv
        :param resultsList:  每页数据list
        :param pn: 页码
        :param AllExcelHead: 表头
        :param sheetName:
        :return: None
        '''
        if len(resultsList) == 0:
            printText = '列表内容空，请检查请求返回值'
            self.myFormat(printText)
            return None

        filePath = '{}\{}'.format(self.SavePath, self.kw)
        if not os.path.exists(filePath):
            os.makedirs(filePath)
        csvFile = r'{}\{}_{}_{}.{}'.format(filePath, str(pn), self.fetchDate, self.kw, 'csv')

        with open(csvFile, 'w+', encoding='utf-8') as myFile:
            myWriter = csv.writer(myFile)
            myWriter.writerow(AllExcelHead)
            myWriter.writerows(resultsList)
            myFile.close()
        printText = '第%d页\tcsv文件写入完毕' % pn
        self.myFormat(printText)

    # def toMysql(resultsList):

    def conMysql(self):
        '''
        链接数据裤
        :return:  链接
        '''
        try:
            con = MySQLdb.connect(
                host='localhost',
                user='root',
                passwd='123456',
                port=3306,
                db='peiji',  # 先找到一个存在的数据库，建立新的后，换掉这个
                charset='utf8'
            )
            return con
        except Exception as e:
            print(e, 'error')
            return None

    def executeInsert(self,con, resultsList, pn, i):
        '''
        插入一条数据
        :param con:
        :param resultsList:
        :param pn:
        :param i:
        :return:
        '''
        cursor = con.cursor()
        print('正在进行插入数据裤操作')
        print(len(resultsList[0]))
        cursor.executemany('insert into  `lagou_new` ( `crawlDate`, `page`, `offer`, `city`, `area`,'
                           ' `publicDate`, `experience`, `salary`, `education`, `company`, `scale`, `directionOne`,'
                           ' `directionTwo`, `advantage`, `financing`, `feature`, `decription`,`positionId`,`searchKeyWord`) values(%s,%s,%s,%s,%s,'
                           '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', resultsList)
        con.commit()
        if cursor.rowcount > 0:
            self.myFormat('插入第%d页\t第%d条\t数据完成' % (pn, i))
        else:
            self.myFormat('插入数据失败')
        cursor.close()

    def checkReiterationPositionId(self,con, positionId):
        '''
        重复数据检查，如果本职位的id已经存在，就不在插入了
        :param con:
        :param positionId:
        :return:
        '''
        cursor = con.cursor()
        sql = 'select `positionId` from `lagou_new` where `positionID`={}'.format(positionId)
        cursor.execute(sql)
        result = cursor.fetchone()
        # print(result)
        cursor.close()
        return result

    def createDatabaseAndTable(self,con):
        '''
        创建一个数据库和表 ，拿到程序先执行这个，成功后就不用在执行了，替换 conMysql 中的原来链接的 数据库名 就行了，
        :param con:
        :return:
        '''
        cursor = con.cursor()
        cursor.execute("drop database if exists lagou")  # 如果lagou数据库存在则删除
        cursor.execute("create database lagou")  # 新创建一个数据库
        cursor.execute("use lagou")  # 选择lagou这个数据库
        # sql 中的内容为创建一个名为lagou_info 的表
        sql = """
        CREATE TABLE `lagou_info` (
      `keyIndex` bigint(20) NOT NULL AUTO_INCREMENT,
      `crawlDate` date DEFAULT NULL,
      `positionId` bigint(20) NOT NULL,
      `searchKeyWord` varchar(30) DEFAULT NULL,
      `page` varchar(10) DEFAULT NULL,
      `offer` varchar(200) DEFAULT NULL,
      `city` varchar(20) DEFAULT NULL,
      `area` varchar(20) DEFAULT NULL,
      `publicDate` datetime DEFAULT NULL,
      `experience` varchar(20) DEFAULT NULL,
      `salary` varchar(20) DEFAULT NULL,
      `education` varchar(20) DEFAULT NULL,
      `company` varchar(200) DEFAULT NULL,
      `scale` varchar(100) DEFAULT NULL,
      `directionOne` varchar(200) DEFAULT NULL,
      `directionTwo` varchar(200) DEFAULT NULL,
      `advantage` varchar(250) DEFAULT NULL,
      `financing` varchar(200) DEFAULT NULL,
      `feature` varchar(250) DEFAULT NULL,
      `decription` text,
      PRIMARY KEY (`keyIndex`,`positionId`)
        ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8
        """  # ()中的参数可以自行设置
        cursor.execute("DROP TABLE IF EXISTS `lagou_info`")  # 如果表存在则删除
        cursor.execute(sql)  # 创建表
        cursor.close()
        self.myFormat('建立数据裤和表成功,替换 方法 conMysql 中的原来链接的 你开始用的数据库名 就行了')

    def updateData(self,con, kw):
        '''
        更新数据测试，这个函数暂时不用
        :param con:
        :param kw:
        :return:
        '''
        cursor = con.cursor()
        # sql = 'UPDATE  `lagou_new` SET `searchKeyWord` = "%s" where positionId=%d'%(kw,3660677)
        sql = 'UPDATE  `lagou_new` SET `searchKeyWord` = "%s" ' % (kw)
        print(sql)
        cursor.execute(sql)
        con.commit()
        if cursor.rowcount > 0:
            print('更新成功，更新%d行数据' % cursor.rowcount)
        else:
            print('没有更新数据')
        cursor.close()

    def closeMysql(self):
        '''
        关闭数据库
        :param con:
        :return:
        '''
        self.con.close()

    def IsSubString(self,SubStrList, Str):
        '''''
        #判断字符串Str是否包含序列SubStrList中的每一个子字符串
        #>>>SubStrList=['F','EMS','txt']
        #>>>Str='F06925EMS91.txt'
        #>>>IsSubString(SubStrList,Str)#return True (or False)
        '''
        flag = True
        for substr in SubStrList:
            if not (substr in Str):
                flag = False
        return flag

    def GetALLFileListFromDir(self,inPath, FlagStr=[]):
        '''
        得到所有文件列表
        :param inPath:
        :param FlagStr:
        :return:
        '''
        FileList = []
        FileNames = os.listdir(inPath)
        print(FileNames)
        if (len(FileNames) > 0):
            for fn in FileNames:
                if (len(FlagStr) > 0):
                    # 返回指定类型的文件名
                    if (self.IsSubString(FlagStr, fn)):
                        # print(os.path.join(inPath, fn))
                        fullfilename = os.path.join(inPath, fn)
                        # print(fullfilename)
                        FileList.append(fullfilename)
                else:
                    # 默认直接返回所有文件名
                    fullfilename = os.path.join(inPath, fn)
                    FileList.append(fullfilename)
        return FileList

    def combineEveryPageInfoToOneV2(self,inPath, outPathFile):
        '''
        合并多个Excel文件到一个
        :param inPath: 要合并的文件目录
        :param outPathFile: 合并后输出的文件名
        :return: None
        '''
        try:
            print('{0:.<100}'.format('开始合并文件'))
            FlagStr = ['xlsx']
            readDirFile = self.GetALLFileListFromDir(inPath, FlagStr=FlagStr)
            if len(readDirFile) == 0:
                self.myFormat('要合并的文件夹，没有文件')
                return None
            dataList = []
            for doc in readDirFile:
                try:
                    if os.path.isfile(doc):
                        data = pd.read_excel(doc, sheetname='data')
                        dataList.append(data)
                except Exception as e:
                    print(e, '合并\t%s\t文档出错,已经跳过' % doc)
                    continue
            dataAll = pd.concat(dataList)
            dataAll.to_excel(outPathFile, index=False, sheet_name='data')
            self.myFormat('感谢上苍，很顺利，合并文件完成了')
        except Exception as e:
            print(e, '合并数据出了问题,检查 函数 combineEveryPageInfoToOneV2')
            return

    def myFormat(self,printText, fillMode='middle', allLength=100, symbol='*'):
        '''
        输出类似下面格式文本，可以指定填充方向，middle,left,right  依次是中间填充，左边 ，右边
        可以指定填充的字符 和填充后的 总长度
        直接打印结果
        用途：在调试程序时，可以统一输出，让输出看着很整齐
        ##########################################	I love python	###########################################
        I love python	#####################################################################################
        :param printText: 要填充的文本 可以是一个格后的文本，比如 '%s-%d'%('love python',666)
        :param fillMode:  填充的方向 middle,left,right
        :param allLength: 填充后的总长度
        :param symbol: 要填充的字符
        :return: None
        '''
        try:
            if fillMode == 'middle':
                sign = '^'
            elif fillMode == 'left':
                sign = '>'
            elif fillMode == 'right':
                sign = '<'
            else:
                sign = '^'
            outResult = str('{0:%s%s%d}' % (str(symbol), sign, allLength)).format('\t%s\t' % (str(printText)))
            print(outResult)
        except:
            print(printText)

    def createDir(self):
        try:
            # ROOT_DIR='M'
            SavePath = r'{}:\综合信息\拉勾网'.format(ROOT_DIR)  # ROOT_DIR 是配置文件 config.py 里面设置的一个 盘符 ，比如 D ，就是D盘
            if not os.path.exists(SavePath):
                raise  FileNotFoundError
        except Exception as e:
            if sys.platform == 'win32':
                # 获取本文件所在的目录
                SavePath = r'{}\{}'.format(os.path.dirname(os.path.abspath(__file__)).lower(), '拉勾网')
            else:
                SavePath =r'{}\{}'.format(os.path.dirname(__file__), '拉勾网')
        if not os.path.exists(SavePath):
            os.makedirs(SavePath)
        self.myFormat('Excel文件保存路径是\t %s'%SavePath)
        return SavePath

    def main(self,pn):
        '''
        主程序这里开始
        :param pn:
        :return:
        '''
        self.myFormat('正在处理第%d页' % pn)
        AllExcelHead = ['抓取日期', '页码', '职位', '城市', '地区', '发布时间',
                        '经验', '薪水', '教育程度', '公司名', '公司规模', '方向1', '方向2', '公司优势', '公司成长或融资', '公司特点', '职位要求']
        resultsList = self.getLagouInfo(pn=pn)
        # 根据需要开启
        self.toExcel(resultsList, pn=pn,AllExcelHead=AllExcelHead) # 保存excel文件
        self.toCsv(resultsList,pn=pn,AllExcelHead=AllExcelHead) # 保存到csv
        self.myFormat('第%d页\t处理完成' % pn)

if __name__ == '__main__':
    start = datetime.datetime.now()
    city = '上海'  # 不指定城市 可以写  全国   # 必须的
    kw = 'python'  # 搜索职位关键词   必须的

    isCreateDataBaseAndTable=False # 创建数据和表开关，创建时，设为True或1，创建完成后，设为False 或 0，这个只用最开始时，运行一次就行了 ，以后不需要了
    OPEN_MYSQL=True # 是否进行保存到 mysql数据库 ,True或1 保存， False 或 0 意味保存到 excel 或csv中
    L=Lagou(city,kw,OPEN_MYSQL=OPEN_MYSQL)
    #  创建数据和表 创建完成后 替换原来数据库连接的那个数据库命名 ,毕竟你要先要连接一个数据库存 成功，才能创建吧
    if isCreateDataBaseAndTable and L.OPEN_MYSQL:
        L.createDatabaseAndTable(L.con)
        exit()

    totalPage = L.getLagouInfo( pn=1, isGetPage=True) # 获取总页码
    # totalPage=2
    if type(totalPage)!=int :
        L.myFormat('请检查总页码')
        exit()
    L.myFormat( '共%d页'%totalPage)
    # 单线程，每获取一页数据 ，保存一个文件，最后有pd把这些文件合并到一起

    print('单线程模式开始。。。。')
    for pn in range(1, totalPage + 1):
        try:
            L.main(pn)
        except Exception as e:
            # 当页码很多时，不能因为一页失败 导致整体程序结束了，所以这里遇到未知的错误时，做跳过处理
            print(e)
            continue
    else:
        try:
            inPath = '{}\{}'.format( L.SavePath, kw)
            outPathFile = '{a}\{b}_{c}_{d}页.{e}'.format(a= L.SavePath, b= L.fetchDate, c= L.kw, d=str(totalPage), e='xlsx')
            L.combineEveryPageInfoToOneV2(inPath, outPathFile)
        except Exception as e:
            print(e,'合并文件出现了问了，检查是否有文件存在了 ')
    if L.OPEN_MYSQL:
        L.closeMysql()
    end = datetime.datetime.now()
    L.myFormat('操作完成，用时 %s' % (end - start))
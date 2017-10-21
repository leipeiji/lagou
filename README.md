# lagou
获取拉勾网职位信息
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

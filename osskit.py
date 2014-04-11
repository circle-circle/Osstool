#coding:utf-8
import time
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import os
import base64
import hmac
import sha
import re
import cPickle as pickle
from oss.oss_api import *
from oss.oss_xml_handler import *

def check_res(res,msg=''):
    if  res.status /100 ==2:
        print '%s OK!' %msg
        print sep
    else:
        print "%s  FAIL" % msg
        print 'ret:%s' %res.status
        print 'request-id:%s' %res.getheader('x-oss-request-id')
        print 'reason:%s' %res.read()
        print sep
        choice_list()
        
def check_not_empty(input,msg=''):
    if not input:
        print "please make sure %s not empty" %msg
        exit(-1)

def format_datetime(osstimestamp):
    date = re.compile("(\.\d*)?Z").sub(".000Z", osstimestamp)
    ts = time.strptime(date, "%Y-%m-%dT%H:%M:%S.000Z")
    return time.strftime("%Y-%m-%d %H:%M", ts)

def listallbuckets():
    res = oss.get_service()
    width = 20
    if (res.status / 100) == 2:
        body = res.read()
        h = GetServiceXml(body)
        is_init = False
        for i in h.list():
            if len(i) >= 3 and i[2].strip():
                if not is_init:
                    print "%s %s %s" % ("CreateTime".ljust(width), "BucketLocation".ljust(width), "BucketName".ljust(width))
                    is_init = True
                print "%s %s %s" % (str(format_datetime(i[1])).ljust(width), i[2].ljust(width), i[0])
            elif len(i) >= 2:
                if not is_init:
                    print "%s %s" % ("CreateTime".ljust(width), "BucketName".ljust(width))
                    is_init = True
                print "%s %s" % (str(format_datetime(i[1])).ljust(width), i[0])
        print "\nBucket Number is: ", len(h.list())
    return check_res(res,'list all buckets')
   
def batch_modify_header(bucket):
    b = GetAllObjects()
    object_list = b.get_all_object_in_bucket(oss,bucket) 
    object_list = b.object_list  
    headers = {}    
    header_choice =['Content-Type','Cache-Control','Content-Disposition','Content-Encoding','Expires']
    
    flag = 1
    while flag:
        header_input = raw_input(u"请选择需要批量修改的header主机头参数:['Content-Type','Cache-Control','Content-Disposition','Expires']:".encode('mbcs'))
        if header_input not in header_choice:
            print u'请重新输入HTTP头:'
        else:
            flag =0   
    if header_input == 'Content-Type':
        content_type = raw_input(u"请输入需要设置的Content-Type值".encode('mbcs'))
        headers['Content-Type'] = content_type
    elif header_input == 'Cache-Control':
        cache_control = raw_input(u"请输入需要设置的Cache-Control值:".encode('mbcs'))
        headers['Cache-Control'] = cache_control
    elif header_input == 'Content-Disposition':
        content_disposition = raw_input(u'请输入需要设置的Content-disponsition值'.encode('mbcs'))
        headers['Content-Disposition'] = content_disposition
    elif header_input == 'Expires':
        expires = raw_input(u"请输入需要设置的expires值".encode('mbcs'))
        headers['Expires'] = expires
    else:
        print 'you have incorrect input'

    for object  in  object_list:
        res=oss.copy_object(bucket, object, bucket, object,headers)
        check_res(res, object)
    print sep

# to sum bucket size
def sum_bucket_size(bucket):  
    b = GetAllObjects()
    b.get_all_object_in_bucket(oss,bucket) 
    object_list = b.object_list
    object_num =len(object_list)
    print 'the bucket %s have %d objects' %(bucket,object_num)

    try:
        bucket_size = 0
        for object in object_list:           
            res=oss.head_object(bucket, object,headers=None)
            bucket_size += int(res.getheader('Content-Length'))
    except:
        print " to sum fail !"       
    print 'the bucket %s size is  %f MB' %(bucket,bucket_size/1024.0/1024)
    print sep

def changeaddress(hostnum):
    global oss
    if os.path.isfile(configfile) and file(configfile).readline != '':
        with file(configfile,'rb+') as f:
            D = pickle.load(f)
        ACCESS_ID = D['id']
        SECRET_ACCESS_KEY = D['key']
        if hostnum == '1':
            D['host']='oss-cn-hangzhou.aliyuncs.com'
        elif hostnum == '2':
            D['host']='oss-cn-hangzhou-internal.aliyuncs.com'
        elif hostnum == '3':
            D['host'] = 'oss-cn-qingdao.aliyuncs.com'
        elif hostnum == '4':
            D['host'] = 'oss-cn-qingdao-internal.aliyuncs.com'
        else :
            print u'没有输入正确的编号，地址没有改变'
        Host = D['host']
        with file(configfile,'wb+') as f:
            pickle.dump(D,f)
        oss = OssAPI(Host,ACCESS_ID,SECRET_ACCESS_KEY)
        print u'您现在位于 %s' %Host
        print sep
    else:
        print u'请先登录'
        zhuxiao()

def zhuxiao():
    #注销
    os.remove(configfile)
    sys.exit()

def choice_list():
    while 1:
        choice = raw_input((u'''
                1)列出所有bucket
                2)统计bucket下的objects数量以及bucket的总大小
                3)批量修改bucket下的所有object的HTTP头信息
                4)清除bucket 
                5)更换节点

                0)退出
                00)注销
                请输入需要操作的数字编号:''').encode('mbcs'))
        if choice == '1':
            listallbuckets()
        elif choice == '2':
            bucket = raw_input(u'请输入需要创建的bucket名称:'.encode('mbcs'))
            sum_bucket_size(bucket)
        elif choice == '3':
            bucket = raw_input(u'请输入需要修改主机头的bucket名称:'.encode('mbcs'))
            batch_modify_header(bucket)
        elif choice == '4':
            bucket = raw_input(u'请输入需要删除所有objects的bucket名称:'.encode('mbcs'))
            print u'请确认要删除的bucket为 %s，删除后将无法恢复' %bucket
            answer = raw_input('Are you sure y/n:').lower()
            if answer =='y':
                clear_all_object_of_bucket(oss,bucket)  
            else:
                print u'请重新选择操作'
                print sep 
        elif choice == '5':
            hostnum = raw_input((u'''
                address list  
                杭州 1: oss-cn-hangzhou.aliyuncs.com
                杭州内网地址 2: oss-cn-hangzhou-internal.aliyuncs.com
                青岛 3: oss-cn-qingdao.aliyuncs.com
                青岛内网地址 4: oss-cn-qingdao-internal.aliyuncs.com

                请输入您需要切换的节点数字编号:''').encode('mbcs'))
            changeaddress(hostnum)

        elif choice == '0':
            sys.exit(0)
        elif choice == '00':
            zhuxiao()
        else:
            print (u"请输入您需要操作的数字！").encode('mbcs')
            print sep

if __name__ == '__main__':
    address = ['oss-cn-qingdao.aliyuncs.com','oss-cn-hangzhou.aliyuncs.com']
    configfile = os.path.expanduser('~') + '/.osscredential'
    sep = "-"*66
    #判断上次是否有注销行为,若没有则直接登录（搜索用户主目录下的配置文件），否则重新输入id,key以及host
    if os.path.isfile(configfile):
        with file(configfile,'rb') as f:
            D = pickle.load(f)
        Host = D['host']
        ACCESS_ID = D['id']
        SECRET_ACCESS_KEY = D['key']
        oss = OssAPI(Host,ACCESS_ID,SECRET_ACCESS_KEY)
        print '      now you are in %s' %Host
        choice_list()
    else:
        ACCESS_ID = raw_input('please input your ACCESS_ID:')
        check_not_empty(ACCESS_ID,'ACCESS_ID')
        SECRET_ACCESS_KEY = raw_input('please input your SECRET_ACCESS_KEY:')
        check_not_empty(SECRET_ACCESS_KEY,'SECRET_ACCESS_KEY')    
        Hostnum = raw_input((u'''
                address list  
                杭州 1: oss-cn-hangzhou.aliyuncs.com
                杭州内网地址 2 : oss-cn-hangzhou-internal.aliyuncs.com
                青岛 3 : oss-cn-qingdao.aliyuncs.com
                青岛内网地址 4: oss-cn-qingdao-internal.aliyuncs.com
                

                请输入节点对应的编号(默认为杭州节点):''').encode('mbcs'))
        if Hostnum == '1':
            Host ='oss-cn-hangzhou.aliyuncs.com'
        elif Hostnum == '2':
            Host ='oss-cn-hangzhou-internal.aliyuncs.com'
        elif Hostnum == '3':
            Host = 'oss-cn-qingdao.aliyuncs.com'
        elif Hostnum == '4':
            Host = 'oss-cn-qingdao-internal.aliyuncs.com'
        else :
            Host = 'oss-cn-hangzhou.aliyuncs.com'
        oss = OssAPI(Host,ACCESS_ID,SECRET_ACCESS_KEY)
        D = { 'host':Host,'id':ACCESS_ID,'key':SECRET_ACCESS_KEY }
        with file(configfile,'wb+') as f:
            pickle.dump(D,f)
        choice_list()
    










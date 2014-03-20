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

def check_not_empty(input,msg=''):
    if not input:
        print "please make sure %s not empty" %msg
        exit(-1)

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
        choicelist()
       

def format_datetime(osstimestamp):
    date = re.compile("(\.\d*)?Z").sub(".000Z", osstimestamp)
    ts = time.strptime(date, "%Y-%m-%dT%H:%M:%S.000Z")
    return time.strftime("%Y-%m-%d %H:%M", ts)

def listallmybuckts():
    #列出所有的bucket
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

def createbucket(bucket):
    #创建一个bucket
    acl = 'private'
    headers = {}
    res = oss.put_bucket(bucket, acl, headers)
    check_res(res,'create bucket')
 
def deletebucket(bucket):
    #删除bucket 无论其内部是否存在文件
    object_list = oss.list_objects(bucket)
    #print object_list
    if len(object_list) != 0:
        res = oss.batch_delete_objects(bucket,object_list)
        if res:
            res1 = oss.delete_bucket(bucket)
            check_res(res1,'delete bucket')
        else:
            check_res(res,'delete bucket')
    else:
        res = oss.delete_bucket(bucket)
        check_res(res, "delete bucket")

def listallobject(bucket):
    #列出bucket中所拥有的object
    prefix = ""
    marker = ""
    delimiter = "/"
    maxkeys = "100"
    headers = {}
    res = oss.get_bucket(bucket, prefix, marker, delimiter, maxkeys, headers)
    if (res.status / 100) == 2:
        body = res.read()
        h = GetBucketXml(body)
        (file_list, common_list) = h.list()
        print "object list is:"
        for i in file_list:
            print i
        print "common list is:"
        for i in common_list:
            print i
        print sep
    else:
        check_res(res,'list all object')
 

def deleteobject(bucket,object):
    #删除bucket中的某个object
    headers = {}
    headers=None
    params=None
    method='DELETE'
    body=''
    res = oss.http_request(method, bucket, object, headers, body, params)
    check_res(res,'delete object')


def deleteobjects(bucket):
    #删除bucket下的所有objects ,保留bucket
    object_list = oss.list_objects(bucket)
    if len(object_list) != 0:
        res = oss.batch_delete_objects(bucket,object_list)
        if res:
            print "delect objects success!"
        else:
            print "sorry,delete objects fail!"
    else:
        print "the bucket is empty !"
    print sep

def moveobject(source_bucket,source_object,target_bucket,target_object):
    #object搬迁bucket,完成后删除源bucket下的object
    res=oss.copy_object(source_bucket, source_object, target_bucket, target_object)
    if (res.status / 100) == 2:
       oss.delete_object(source_bucket, source_object)
       check_res(res,'move object')
    else:
       check_res(res,'move object')

def copyobject(source_bucket,source_object,target_bucket,target_object):
    #object搬迁bucket,完成后保留源bucket下的object
    res=oss.copy_object(source_bucket, source_object, target_bucket, target_object)
    check_res(res,'copy object')

def uploadfile(bucket,object,localfile):
    #上传的文件大于5G,使用multi_upload_file，否则使用put_object_from_file
    localfile_size = os.path.getsize(localfile)
    limit_size = 5*1024*1024*1024
    if localfile_size > limit_size :
        headers = {}
        thread_num = 10
        max_part_num = 10000
        upload_id = ""
        res = oss.multi_upload_file(bucket, object, localfile, upload_id, thread_num, max_part_num, headers)
    else:
        res = oss.put_object_from_file(bucket,object,localfile)
    if res.status == 200:
        print 'upload %s success' % localfile
    else:
        print  'upload %s FAIL ,status:%s,request-id:%s' %(localfile,res.status,res.getheader('x-oss-request-id'))  
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
        print u'现在您位于 %s' %Host
        print sep
    else:
        print u'请先登录'
        zhuxiao()
def zhuxiao():
    #注销
    os.remove(configfile)
    sys.exit()

def choicelist():
    while 1:
        choice = raw_input(u'''
          1)列出所有的bucket
          2)创建新的bucket
          3)删除bucket  请慎重选择，无法恢复

          4)列出所选bucket下的objects
          5)删除一个object  
          6)删除一个bucket下的所有object,保留bucket名称，和选项3类似
          7)搬迁object   
          8)复制object   
          9)上传文件  大于5G的文件自动选择断点续传
          
          10)切换节点
          0)退出  
          00)注销
          请输入需要操作的数字编号:'''.encode('mbcs'))
        if choice == '1':
            listallmybuckts()
        elif choice == '2':
            bucket = raw_input(u'请输入需要创建的bucket名称:'.encode('mbcs'))
            createbucket(bucket)
        elif choice == '3':
            bucket = raw_input(u'请输入需要删除的bucket名称:'.encode('mbcs'))
            print u'请确认要删除的bucket为 %s，删除后将无法恢复' %bucket
            answer = raw_input('Are you sure y/n:').lower()
            if answer =='y':
                deletebucket(bucket)  
            else:
                print u'请重新选择操作'
                print sep           
        elif choice == '4':
            bucket = raw_input(u'请输入需要列出所有objects的bucket名称:'.encode('mbcs'))
            listallobject(bucket)
        elif choice == '5':
            bucket = raw_input(u'请输入需要删除object所在的bucket名称 :'.encode('mbcs'))
            object = raw_input(u'请输入需要删除的object:'.encode('mbcs'))
            object = smart_code(object)
            deleteobject(bucket,object)
        elif choice == '6':
            bucket = raw_input(u'请输入需要完全删除objects的bucket名称:'.encode('mbcs'))
            print u'请确认要删除所有objects的bucket为 %s，删除后将无法恢复' %bucket
            answer = raw_input('Are you sure y/n:').lower()
            if answer =='y':
                deleteobjects(bucket) 
            else:
                print u'请重新选择操作'
                print sep           
        elif choice == '7':
            source_bucket =raw_input(u'请输入需要移动object所在的源bucket名称:'.encode('mbcs'))
            target_bucket = raw_input(u'请输入需要移动object的目的bucket名称:'.encode('mbcs'))
            source_object = raw_input(u'请输入需要移动的object:'.encode('mbcs'))
            source_object = smart_code(source_object)
            target_object = raw_input(u'请输入需要接收的object，(默认回车或者bucket下的多级目录):'.encode('mbcs'))
            if len(target_object) == 0:
               target_object = source_object
            target_object = smart_code(target_object)
            moveobject(source_bucket,source_object,target_bucket,target_object)
        elif choice == '8':
            source_bucket =raw_input(u'请输入需要移动object所在的源bucket名称:'.encode('mbcs'))
            target_bucket = raw_input(u'请输入需要移动object的目的bucket名称:'.encode('mbcs'))
            source_object = raw_input(u'请输入需要移动的object:'.encode('mbcs'))
            source_object = smart_code(source_object)
            target_object = raw_input(u'请输入需要接收的object，(默认回车或者bucket下的多级目录):'.encode('mbcs'))
            if len(target_object) == 0:
               target_object = source_object
            target_object = smart_code(target_object)
            copyobject(source_bucket,source_object,target_bucket,target_object)
        elif choice == '9':
            bucket = raw_input(u'请输入保存上传文件的bucket名称:'.encode('mbcs'))
            localfile = raw_input(u'请输入上传文件的本地路径:'.encode('mbcs')).strip('""')
            if not os.path.exists(localfile):
                  print 'not exists %s' %localfile
                  exit(-1)
            localfile=smart_code(localfile)
            object = raw_input(u'请输入需保存文件的object路径名称或者直接回车:'.encode('mbcs'))
            if len(object) == 0:
               object = os.path.basename(localfile)
            object = smart_code(object)
            uploadfile(bucket,object,localfile)
        elif choice == '10':
            hostnum = raw_input((u'''
                address list  
                杭州 1: oss-cn-hangzhou.aliyuncs.com
                杭州内网地址 2: oss-cn-hangzhou-internal.aliyuncs.com
                青岛 3: oss-cn-qingdao.aliyuncs.com
                青岛内网地址 4: oss-cn-qingdao-internal.aliyuncs.com

                请输入您需要切换的节点数字编号:''').encode('mbcs'))
            changeaddress(hostnum)
        elif choice == '0':
            sys.exit()
        elif choice == '00':
            zhuxiao()
        else:
            print (u"请输入您需要操作的数字！").encode('mbcs')
            print sep

if __name__ == '__main__':
    address = ['oss-cn-qingdao.aliyuncs.com','oss-cn-qingdao-internal.aliyuncs.com','oss-cn-hangzhou.aliyuncs.com','oss-cn-hangzhou-internal.aliyuncs.com']
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
        choicelist()
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
        choicelist()





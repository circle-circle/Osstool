Osstool
=======

v0.1  -2014/3/19
Aliyun  Oss  Tool
将该脚本编译结合成二进制文件（.exe）
使其不需要搭建任何环境即可运行于windows平台下



v0.2 -2014/3/20
相对于v0.1的版本，改动如下
1，可以接受中文文本输入
2，提示输入更改为中文，更容易接受
3，添加了更换节点的选项

受限于Aliyun API 中copy object 的原因，执行搬移或者复制object时，大于200M的文件，会失败！


按选项的名称进行理解
1）列出所有的bucket
2) 创建一个bucket
3) 删除一个bucket (无论该bucket是否为空）
 
4）列出一个bucket下的所有object  
5) 删除一个bucket下的某个object，无法接受中文字符
6) 删除一个bucket下的所有object,保留bucket名称，和选项3类似
7）搬迁object,将同一节点下的bucket中的某个object移动到另一个bucket下，不保留源bucket下的object
8) 复制object ,将同一个节点下的bucket中的某个object 复制到另外一个bucket，保留源bucket下的object

9) 上传文件  大于5G的文件自动选择mulit upload方式上传
10）更换节点
0）退出，下次登录无需再次输入登录验证信息
00）注销退出，下次登录需要再次输入验证信息



v0.3 -2014/4/11
使用git push osskit.py  osskit.exe
增加批量修改object主机头以及统计bucket大小和数量的工具osskit.exe



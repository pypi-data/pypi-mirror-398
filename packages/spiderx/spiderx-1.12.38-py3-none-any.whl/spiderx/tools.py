# encoding: utf-8
#pip install pycryptodome
from Crypto.Cipher import AES,DES,PKCS1_v1_5
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.Util.Padding import unpad,pad  #补位
from binascii import b2a_hex, a2b_hex #
from urllib.parse import urlparse
from hashlib import pbkdf2_hmac
from .sx import *
import rsa
#需要第三方包的模块
def add_block(content:bytes, block_size:int=16, style:bytes=b'\x00')->bytes:
    # b=len(content)%block_size
    # if b != 0:
    #     content += style * (block_size - b)
    # return content
    return content + style * (block_size - (len(content) % block_size))
class OPTIONS_HEADERS():
    def __init__(self,url=False,uri=False,ts=False):
        self.url = url  # 下载m3u8 是否要加url
        self.ts = ts  # 下载ts 是否要加url
        self.uri = uri  # 下载uri 是否要加url
class AES_128_CBC():
    def __init__(self, key:bytes or list,iv:bytes or list,block:int=16,pad_str='\0'):
        '''
        :param key: 长度16位的bytes
        :param iv: 长度16位的bytes
        自定义补 \0
        '''
        if type(key)==bytes:
            self.key=key
        elif type(key)==list:
            self.key=bytes(key)
        else:
            raise Exception('key 类型错误')
        if type(iv)==bytes:
            self.iv=iv
        elif type(iv)==list:
            self.iv=bytes(iv)
        else:
            raise Exception('iv 类型错误')
        self.mode = AES.MODE_CBC
        self.block=block
        self.pad_str=pad_str
    # 这里密钥key 长度必须为16（AES-128）、24（AES-192）、或32（AES-256）Bytes 长度.目前AES-128足够用
    # 如果text不足16位的倍数就用空格补足为16位
    def add_to_16(self,text):
        if len(text.encode('utf-8')) % self.block:
            add = self.block - (len(text.encode('utf-8')) % self.block)
        else:
            add = 0
        text = text + (self.pad_str * add)
        return text.encode('utf-8')
        # 加密函数
    def encrypt(self,text:str)->str:
        cryptos = AES.new(self.key, self.mode, self.iv)
        cipher_text = cryptos.encrypt(self.add_to_16(text))
        # 因为AES加密后的字符串不一定是ascii字符集的，输出保存可能存在问题，所以这里转为16进制字符串
        return b2a_hex(cipher_text).decode()    #b2a_hex 字符串转成16进制
    # 解密后，去掉补足的空格用strip() 去掉
    def decrypt(self,text:str)->str:
        cryptos = AES.new(self.key, self.mode, self.iv)
        plain_text = cryptos.decrypt(a2b_hex(text)) #a2b_hex ascii转成bytes
        return bytes.decode(plain_text).rstrip(self.pad_str)
class AES_ECB():
    def __init__(self,key:bytes or list,block=16):
        if type(key)==bytes:
            self.key=key
        elif type(key)==list:
            self.key=bytes(key)
        self.block=block
    def encrypt(self,content :bytes):
        aes=AES.new(self.key,AES.MODE_ECB)
        content = pad(content, self.block)
        return aes.encrypt(content)
    def decrypt(self,content:bytes):
        aes=AES.new(self.key,AES.MODE_ECB)
        content=aes.decrypt(content)
        return unpad(content,self.block)
class DES_ECB():
    def __init__(self,key:bytes,block=16):
        '''block 8 或者  16 都可以 '''
        self.block=block
        self.des=DES.new(key,mode=DES.MODE_ECB)
    def encrypt(self,content)->bytes:
        return self.des.encrypt(pad(content,block_size=self.block))
    def decrypt(self,content)->bytes:
        '''
        验证解码
        网址：https://the-x.cn/zh-cn/cryptography/Des.aspx
        key = 12345678
        明文：001900423330413543304400000000000000000000000000000000eb01
        加密后：bad9271686660e506e701cbb5eb2cd93e8f359d79065012e5f6a7d528e394f395f6a7d528e394f395f6a7d528e394f3942e290f9c6dd2622ddcd676751f31afb

        网址 http://tool.chacuo.net/cryptdes
        选 ECB pkcs7padding 12345678  hex  utf8 解码
        密文：bad9271686660e506e701cbb5eb2cd93e8f359d79065012e5f6a7d528e394f395f6a7d528e394f395f6a7d528e394f3942e290f9c6dd2622ddcd676751f31afb
        解密后：001900423330413543304400000000000000000000000000000000eb01
        '''
        content= self.des.decrypt(content)
        return unpad(content,block_size=self.block)
class AES_CBC():
    def __init__(self,key:bytes or list,iv:bytes or list,block=16,输出16进制=False,输出base64=False,pad_style='pkcs7',pad_str=''):
        '''
        :param key:
        :param iv:
        :param block:
        :param 输出16进制:
        :param pad_style:  pkcs7  x923 iso7816
        :param pad_str:  \0  自定义补 padding
        '''
        if isinstance(key,bytes):
            self.key=key
        elif isinstance(key,list):
            self.key=bytes(key)
        else:
            raise Exception('key 类型错误')
        if isinstance(iv,bytes):
            self.iv=iv
        elif isinstance(iv,list):
            self.iv=bytes(iv)
        else:
            raise Exception('iv 类型错误')
        self.block=block
        self.style=pad_style

        self.pad_str=pad_str
        self.输出16进制=输出16进制
        self.输出base64=输出base64
    def add_to_block(self,text:str):
        if len(text.encode('utf-8')) % self.block:
            add = self.block - (len(text.encode('utf-8')) % self.block)
        else:
            add = 0
        text = text + (self.pad_str * add) #'\0'
        return text.encode('utf-8')
    def encrypt(self,content):
        aes=AES.new(self.key,AES.MODE_CBC,self.iv)
        if self.pad_str:
            content=self.add_to_block(content.decode())
        else:
            content=pad(content,self.block,self.style)
        #----------------------------------------
        res=aes.encrypt(content)
        if self.输出16进制:
            return b2a_hex(res).decode() #然后字符串
        elif self.输出base64:
            return str( base64.encodebytes(res) ,encoding='utf-8').replace('\n','') #返回字符串
        else:
            return res #bytes
    def decrypt(self,content):
        aes=AES.new(self.key,AES.MODE_CBC,self.iv)
        if self.输出16进制:
            content = aes.decrypt(a2b_hex(content))

            if self.pad_str:
                return bytes.decode(content).rstrip(self.pad_str)  # 返回字符串
            else:
                content=unpad(content,self.block,self.style)
                return bytes.decode(content) #返回字符串
        elif self.输出base64:
            content=base64.decodebytes(content.encode('utf-8'))
            content=aes.decrypt(content)

            if self.pad_str:
                return bytes.decode(content,encoding='utf-8').rstrip(self.pad_str)  # 字符串
            else:
                return unpad(content, self.block, self.style).decode('utf-8') #返回字符串
        else:
            content = aes.decrypt(content)

            if self.pad_str:
                return bytes.decode(content).rstrip(self.pad_str)  # 字符串
            else:
                return unpad(content, self.block, self.style) # bytes
class DES_CBC():
    def __init__(self,key:bytes,iv:bytes,block=16):
        '''block 8 或者  16 都可以 '''
        self.block=block
        self.des=DES.new(key,mode=DES.MODE_CBC,iv=iv)
    def encrypt(self,content)->bytes:
        return self.des.encrypt(pad(content,block_size=self.block))
    def decrypt(self,content)->bytes:
        content= self.des.decrypt(content)
        return unpad(content,block_size=self.block)
def rsa_PKCS1_新建(字节长度=1024):
    ''' 字节长度:   最小为1024，且必需是1024的倍数(2048,...) '''
    class rsa1():
        def __init__(self):
            self.私钥=RSA.generate(字节长度)
            self.公钥= self.私钥.publickey()
            self.私钥文本=self.私钥.exportKey().decode()
            self.公钥文本=self.公钥.exportKey().decode()
    return rsa1()
def rsa_PKCS1_公钥_加密(公钥:bytes,加密对象:bytes)->bytes:
    '''rand 随机字节函数 None  Crypto.Random.get_random_bytes '''
    pkcs=PKCS1_v1_5.new(公钥)
    return pkcs.encrypt(加密对象)
def rsa_PKCS1_私钥_解密(私钥:bytes,解密对象:bytes)->bytes:
    pkcs=PKCS1_v1_5.new(私钥)
    return pkcs.decrypt(解密对象,sentinel=None)
def rsa_PKCS1_公钥文本_加密(公钥文本:str,加密对象:bytes)->bytes:
    '''rand 随机字节函数 None  Crypto.Random.get_random_bytes '''
    if 'BEGIN PUBLIC KEY' not in 公钥文本:
        公钥文本=f'''-----BEGIN PUBLIC KEY-----\n{公钥文本.strip()}\n-----END PUBLIC KEY-----'''
    公钥=RSA.importKey(公钥文本.strip().encode())
    pkcs=PKCS1_v1_5.new(公钥)
    return pkcs.encrypt(加密对象)
def rsa_PKCS1_私钥文本_解密(私钥文本:str,解密对象:bytes)->bytes:
    if 'BEGIN RSA PRIVATE KEY' not in 私钥文本:
        私钥文本 = f'''-----BEGIN RSA PRIVATE KEY-----\n{私钥文本.strip()}\n-----END RSA PRIVATE KEY-----'''
    私钥=RSA.importKey(私钥文本.strip().encode())
    pkcs=PKCS1_v1_5.new(私钥)
    return pkcs.decrypt(解密对象,sentinel=None)
def rsa_PKCS1_15_私钥文本_SHA256签名(私钥文本:str,加密对象:bytes)->bytes:
    if 'BEGIN RSA PRIVATE KEY' not in 私钥文本:
        私钥文本 = f'''-----BEGIN RSA PRIVATE KEY-----\n{私钥文本.strip()}\n-----END RSA PRIVATE KEY-----'''
    私钥 = RSA.import_key(私钥文本.encode())
    encrypt_data = SHA256.new(加密对象)
    signature = pkcs1_15.new(私钥).sign(encrypt_data)
    return byte_to_base64(signature)
def rsa_新建(字节长度=1024):
    ''' 字节长度:   最小为1024，且必需是1024的倍数(2048,...) '''
    class rsa1():
        def __init__(self):
            (self.公钥,self.私钥)=rsa.newkeys(字节长度)
            self.私钥文本=self.私钥.save_pkcs1().decode()
            self.公钥文本=self.公钥.save_pkcs1().decode()
    return rsa1()
def rsa_公钥_加密(公钥:bytes,加密对象:bytes)->bytes:
    return rsa.encrypt(加密对象, 公钥)
def rsa_私钥_解密(私钥:bytes,解密对象:bytes)->bytes:
    return rsa.decrypt(解密对象, 私钥)
def rc4_encrypt(data:bytes, key:bytes):        # rc4算法 加密
    return ARC4.new(key).encrypt(data)
def rc4_decrypt(data:bytes, key:bytes):        # rc4算法 解密
    return ARC4.new(key).decrypt(data)
def aes_cbc_pbkdf2_加密(plaintext: str, key: str, salt: str) -> str:
    '''
    使用AES-CBC模式对明文进行加密，并结合PBKDF2密钥推导和Base64编码。
    plaintext='{"s":1}'
    key = '%RtR8AB&nWsh=AQC+v!=pgAe@dSQG3kQ'
    salt = 'orieC_jQQWRmhkPvR6u2kzXeTube6aYupiOddsPortal'
    '''

    # 步骤1：生成随机IV（初始化向量）
    iv = os.urandom(16)  # 16 bytes，符合AES的块大小

    # 步骤2：使用PBKDF2推导密钥
    key_material = pbkdf2_hmac(
        hash_name='sha256',
        password=key.encode('utf-8'),
        salt=salt.encode('utf-8'),
        iterations=1000,
        dklen=32  # 生成32 bytes的密钥（适用于AES-256）
    )

    # 步骤3：创建AES-CBC加密器
    cipher = AES.new(key_material, AES.MODE_CBC, iv)
    plaintext_bytes = plaintext.encode('utf-8')
    padding_length = 16 - (len(plaintext_bytes) % 16)
    if padding_length == 0:
        padding_length = 16  # 确保至少填充一个块
    # 添加填充字节
    plaintext_padded = plaintext_bytes + bytes([padding_length] * padding_length)

    # 步骤4：创建AES-CBC加密器
    cipher = AES.new(key_material, AES.MODE_CBC, iv)
    # 步骤5：对明文进行加密
    ciphertext = cipher.encrypt(plaintext_padded)

    # 步骤6：Base64编码
    encrypted_data = base64.b64encode(ciphertext).decode('utf-8')

    # 步骤7：将IV和加密数据合并
    # 格式：iv_hex:encrypted_data
    iv_hex = iv.hex()
    encrypted_base64_str = f"{encrypted_data}:{iv_hex}"
    return base64.b64encode(encrypted_base64_str.encode()).decode()
def aes_cbc_pbkdf2_解密(encrypt_base64_str:str, key:str, salt:str)->str:
    '''
    data {"s":1}
    encrypt_base64_str = 'VVJBU2hSeEZSZHRTT1BKMjV0bElNdz09OmNmZDcwNTM1YjE0Mzc0NTBhYWRjNGJiNTYxMGQ0YzVj'
    key = '%RtR8AB&nWsh=AQC+v!=pgAe@dSQG3kQ'
    salt = 'orieC_jQQWRmhkPvR6u2kzXeTube6aYupiOddsPortal'
    '''
    # 步骤1：解码Base64字符串t
    decoded = base64.b64decode(encrypt_base64_str).decode('utf-8')
    data, iv = decoded.split(':')

    # 步骤2：解析IV部分
    # 每两个字符作为一个十六进制值
    iv_bytes = bytes.fromhex(iv)

    # 步骤3：使用PBKDF2推导密钥
    key_material = pbkdf2_hmac('sha256', key.encode('utf-8'), salt.encode('utf-8'), 1000, dklen=32)

    # 步骤4：解密密文s_part
    cipher = AES.new(key_material, AES.MODE_CBC, iv_bytes)
    ciphertext = base64.b64decode(data)
    try:
        plaintext = cipher.decrypt(ciphertext)
        return plaintext.decode('utf-8')
    except ValueError as e:
        print(f"解密失败：{e}")
        return None

        # 示例参数
class rsa_pkcs1():
    def 创建秘钥(self,文本=0):
        # 生成公钥、私钥
        (pubkey, privkey) = rsa.newkeys(1024)
        if 文本:
            return (pubkey.save_pkcs1(),privkey.save_pkcs1())
        else:
            return (pubkey,privkey)
    def 加密(self,公钥,文本:str):#公钥
        # 明文编码格式
        return rsa.encrypt(文本.encode("utf-8"), 公钥)
    def 解密(self, 私钥,对象:bytes):#私钥
        return rsa.decrypt(对象, 私钥).decode("utf-8")
class DOWN_M3U8():
    def __init__(self, 文件路径='test.mp4', 网址='', m3u8字符串='', 线程数=20,show_text=False, istest=False,显示解码=True,二进制=False,分离器=False,显示错误=True,显示FFMPEG错误=True,headers=None,cookies=None,proxies=None,curl=False,try_num=10,cmd_show=1,timeout=30, 类型=1):
        # 链接地址回调 可以调整ts链接
        if 类型==1:
            self.url = 网址
        elif 类型==2:
            #无加密视频网址
            print('[ {} ]'.format(scolor('测试无加密模式')))
            self.url = 'https://hls.videocc.net/source/24560c93d4/d/24560c93d4c855d66ab155af0db215d1_1.m3u8'
        elif 类型==3:
            #加密视频网址
            print('[ {} ]'.format(scolor('测试加密模式')))
            self.url= 'https://cd15-ccd1-2.play.bokecc.com/flvs/0DD1F081022C163E/2021-02-23/0642A98932599FAF9C33DC5901307461-20.m3u8?t=1635076402&key=E45B49E325D8B1C425133DC317308BDE&tpl=10&tpt=112'
            self.url = 'https://1258712167.vod2.myqcloud.com/25121a6avodtransbj1258712167/9d02b67b5285890800144111742/drm/voddrm.token.dWluPTt2b2RfdHlwZT0yO2NpZD0xMDkxMTA7cHNrZXk9O2V4dD0=.v.f30741.m3u8?t=619caf12&exper=0&us=2673142424772967461&sign=5ed90abe3dd10924416a7f996447ea11'
        else:
            print('[ {} ]'.format(scolor('测试 文本+视频链接 模式')))
            self.url='https://hls.videocc.net/source/24560c93d4/d/24560c93d4c855d66ab155af0db215d1_1.m3u8'
            m3u8字符串=get_request(self.url).text

        self.fpath=绝对路径(文件路径)
        self.fname=os.path.split(文件路径)[1]
        self.try_num=try_num #失败次数

        self.items=[]  #存所有的ts地址
        self.cookies=cookies
        self.proxies=proxies
        self.curl=curl
        self.headers=headers

        self.加密信息 = {}  # 存加密信息
        self.线程数 = 线程数  # 线程数
        self.m3u8字符串= ''  #m3u8内容

        self.加密行= []
        self.AES对象 = []
        self.tsparse_payload_解码回调函数=None
        self.打印TS链接 = False
        self.key=None #bytes 或者 列表
        self.iv=None #bytes 或者 列表
        self.m3u8字符串 = m3u8字符串.strip()

        self.state=True  #是否正常获取视频信息
        self.show=show_text  #显示text
        self.测试下载数量=10
        self.二进制=二进制
        self.分离器=分离器
        self.显示解码=显示解码
        self.显示错误=显示错误
        self.显示FFMPEG错误=显示FFMPEG错误
        self.timeout = timeout
        self.istest = istest
        self.options_headers=OPTIONS_HEADERS(url=1,uri=1,ts=1)

        self.block_size=None  #content 加block  #未使用
        self.block_style=b'\x00'                #未使用
        #----------------------------------------
        self.TS地址回调函数=None #回调进度条
        self.忽略TS长度=False   #是否跳过长度检测
        self.进度条回调函数=None #回调进度条
        self.URI地址回调函数=None #dd.URI地址回调函数=
        self.KEY返回值回调函数=None #dd.KEY返回值处理回调函数 = lambda x : func(x)
        self.TS下载间隔时间=None
        self.链接前缀=''
        #----------------------------------------
        self.__uri_temp_data={'uri':None, 'key':None}
        self.每行不同加密 = None  #Ture  或者  False 或者 None
        self.cmd_show=cmd_show
        self.random_id=随机字符串(类型=1,长度=20)
        self.ff = FFMPEG()
        self.cache_dir = 绝对路径('cache')
        self.TEMP_DIR = f'{self.cache_dir}/{self.random_id}/'
        #清理旧的缓存文件夹
        if os.path.exists(self.cache_dir):
            for _file in os.listdir(self.cache_dir):
                _fpath = f'{self.cache_dir}/{_file}'
                if os.path.isdir(_fpath):
                    if time.time()-os.path.getctime(_fpath)>3600:
                        删除目录树(_fpath)
    def get_items(self):
        try:
            if self.m3u8字符串:
                lines=self.m3u8字符串
                if self.show:
                    print('[ {} ] [ {} ] : {}'.format(scolor('文本'),scolor('视频链接'), self.url if self.url else '无视频链接'))
            else:
                if self.show:
                    print('[ {} ] : {}'.format(scolor('视频链接'), self.url))
                req_m3u8 = self.get_url(self.url, type_='url',stream=True)

                # 获取M3U8的文件内容  分段获取
                lines = ''
                try:
                    for chunk in req_m3u8.iter_content(chunk_size=10 * 1024 * 1024): #10MB
                        # 假设是文本那么就可以转文本
                        chunk = chunk.decode('utf-8')
                        lines += chunk
                except:
                    return 下载文件_进度条(文件路径=self.fpath, 网址=self.url, 线程数=self.线程数, 多线程=True, 分段长度=10 * 1024,headers=self.headers,istest=self.istest,try_num=self.try_num)

                req_m3u8.close()
                self.m3u8字符串 = lines
            # 读取文件里的每一行
            file_line = lines.split("\n")
            # 通过判断文件头来确定是否是M3U8文件
            if '#EXTM3U' not in file_line[0].upper():
                raise Exception('非M3U8的链接')
            else:
                链接path=self.url.split('?')[0] #有些参数里面带链接 需要这步处理
                self.链接前缀 = 链接path.rsplit("/", maxsplit=1)[0]
                self.域名前缀 = '/'.join(链接path.split('/')[:3])
                self.hostname = urlparse(链接path).hostname
                self.http = urlparse(链接path).scheme
                self.flag_域名前缀 = None
                unknow = True  # 用来判断是否找到了下载的地址
                n = 1
                # ----------------------------------------------ts行
                for index, line in enumerate(file_line):
                    if "EXTINF" in line:
                        unknow = False
                        ts_url=file_line[index+1]
                        if self.TS地址回调函数:  # 如果设置了回调
                            # def TS地址回调函数(line):return url
                            ts_url_new = self.TS地址回调函数(ts_url)
                        else:
                            if ts_url[:2]=='//':
                                ts_url_new=f'{self.http}:'+ts_url
                            else:
                                ts_url=ts_url.lstrip('/')
                                if 'http' != ts_url.lower()[:4] and self.url.lower():

                                    if self.hostname in ts_url:
                                        ts_url_new = f'{self.http}://' + ts_url
                                    else:
                                        ts_url_new = f"{self.链接前缀}/" + ts_url

                                    if self.flag_域名前缀 == None:
                                        try:
                                            req = self.get_url(ts_url_new, type_='ts',stream=True)
                                            code = req.status_code
                                        except:
                                            code = 404
                                        if code in [401,403,404,500]:
                                            # 401 未授权
                                            #403 表示服务器理解请求客户端的请求，但是拒绝进行访问 禁止访问
                                            #404 未找到页面
                                            #500 服务器错误
                                            self.flag_域名前缀 = True
                                        else:
                                            ts_size = len(req.content)
                                            if ts_size < 10*1024: #文件长度小于10KB
                                                self.flag_域名前缀 = True
                                            else:
                                                self.flag_域名前缀 = False

                                    if self.flag_域名前缀:
                                        ts_url_new =f"{self.域名前缀}/" + ts_url
                                else:
                                    ts_url_new = ts_url
                        self.items.append({'i': n, 'url': ts_url_new,'ts_url':ts_url})
                        n += 1
                if unknow:
                    raise Exception("没有ts链接")
                # ----------------------------------------------加密行
                for index, key_line in enumerate(file_line):
                    if '#EXT-X-KEY' in key_line and (('URI' in key_line) or ('IV' in key_line)): #存在URI或者IV
                        key_dict = {}
                        for line in key_line.split(','):
                            kv = line.split('=', 1)
                            if len(kv) == 2:
                                key_dict[kv[0].strip()] = kv[1].strip().strip('"').strip("'").strip()
                        self.加密行.append(key_dict)

                if self.加密行:
                    self.加密信息=self.加密行[0]
                else:
                    self.加密信息=None
                加密行数量 = set([f'{x["URI"] if "URI" in x else "None"} {x["IV"] if "IV" in x else "None"}' for x in self.加密行])
                if len(加密行数量)==1:
                    self.每行不同加密 = False
                elif len(加密行数量)>1:
                    self.每行不同加密=True
        except BaseException as e:
            if self.显示错误:
                print('[ {} ]'.format(scolor('get_items: {} {}'.format(跟踪函数(-3),e),'err')))
            self.state=False
    def __aes(self,加密信息):
        try:
            # 这里主要处理 AES CBC 128  16位长度密码。如果长度不是16位也可以直接复制self.key
            if self.key:  # 自定义key判断类型 转成bytes
                KEY = self.key
                if type(KEY) == list:
                    KEY = bytes(KEY)
                elif type(KEY) == bytes and len(KEY) == 16:
                    pass
                elif type(KEY) == str and len(KEY) == 34:
                    KEY = bytes.fromhex(KEY[2:])
                else:
                    raise Exception('AES KEY 输入错误')
            else:
                if 'URI' not in 加密信息:
                    raise Exception('没有URI链接地址')
                if self.__uri_temp_data['uri'] == 加密信息['URI']:
                    KEY = self.__uri_temp_data['key']
                else:
                    if self.URI地址回调函数:
                        KEY = self.get_url(加密信息['URI'],type_='uri').content
                    else:
                        uri=加密信息['URI'].lstrip('/')
                        #链接类型
                        if '/' in uri:
                            if 'http' in uri:
                                uri_url=uri
                            else:
                                if self.hostname in uri:
                                    uri_url=f'{self.http}://' + uri
                                else:
                                    if self.flag_域名前缀:
                                        uri_url=f'{self.域名前缀}/'+uri
                                    else:
                                        uri_url = f'{self.链接前缀}/' + uri
                            KEY = self.get_url(uri_url, type_='uri').content
                        #非链接类型
                        else:
                            if len(uri)==16:
                                KEY=uri.encode()
                            if len(uri)==32:
                                KEY=bytes.fromhex(uri)
                            elif len(uri)==34:
                                KEY = ytes.fromhex(uri[2:])
                            else:
                                raise Exception(f'URI错误:{uri} {len(uri)}')
                    if self.KEY返回值回调函数:
                        KEY = self.KEY返回值回调函数(KEY)
                    if len(KEY) != 16:
                        try:
                            KEY=KEY.decode()
                        except:
                            pass
                        raise Exception(f'URI错误:{KEY} {len(KEY)}')
            if self.iv:  # 自定义iv判断类型 转成bytes
                IV = self.iv
                if type(IV) == list:
                    IV = bytes(IV)
                elif type(IV) == bytes and len(IV) == 16:
                    pass
                elif type(IV) == str and len(IV) == 34:
                    IV = bytes.fromhex(IV[2:])
                else:
                    raise Exception(f'IV错误:{IV} {len(IV)}')
            else:
                if 'IV' in 加密信息 and 加密信息['IV']:
                    IV=加密信息['IV']
                    if len(IV) == 34:  # 16进制转成字节
                        IV = bytes.fromhex(IV[2:])
                    else:
                        IV = IV.encode() #转bytes
                else:
                    if self.显示解码:
                        print('[ {} ]'.format(scolor('默认IV')), end=' ')
                    IV=bytes([0]*16)
            self.__uri_temp_data = {'uri': 加密信息['URI'] if 'URI' in 加密信息 else None, 'key': KEY}
            return AES.new(KEY, AES.MODE_CBC, IV)
        except BaseException as e:
            return f'{跟踪函数(-5)} {str(e)}'
    def __get_aes(self):
        # 如果有加密 则简单的解密
        # 如果复杂的加密 请覆盖 KEY cryptor 还有items
        if self.显示解码:
            if self.tsparse_payload_解码回调函数:
                model = 'P'
            elif self.每行不同加密==False:
                model='S'
            elif self.每行不同加密==True:
                model='M'
            else:
                model='N'
            print('[ {} ]'.format(scolor(model,'warn')), end=' ')
        if self.state:
            if self.AES对象:
                if isinstance(self.AES对象, list):
                    pass
                else:
                    self.AES对象 = [self.AES对象] #转成列表  自定义
            else:
                if self.tsparse_payload_解码回调函数:
                    pass
                elif self.加密行:
                    if not self.每行不同加密:
                        self.加密行=[self.加密信息]  #自定义
                    for 加密信息 in self.加密行:
                        if self.URI地址回调函数:
                            加密信息['URI']=self.URI地址回调函数(加密信息['URI'])
                        aes对象 = self.__aes(加密信息)
                        if isinstance(aes对象,str):
                            print('[ {} {} ]'.format(scolor('解码失败:'),aes对象), end=' ')
                            self.state = False  # 修改状态
                            return
                        elif aes对象:
                            self.AES对象.append(aes对象)
                        else:  #None
                            self.state=False #修改状态
                            return
                    if self.显示解码:
                        print('[ {} ]'.format(scolor('解码成功')), end=' ')
    def __download_ts(self,item):
        for i in range(self.try_num):
            try:
                req=self.get_url(item['url'],type_='ts',try_num=1)
                content = req.content
                content_len=len(content)
                if self.忽略TS长度:
                    size=content_len if content_len>10 else 10
                else:
                    try:
                        size=int(req.headers['content-length'])
                    except:
                        size=content_len
                if self.tsparse_payload_解码回调函数:
                    content=self.tsparse_payload_解码回调函数(content)
                elif self.AES对象:#如果有加密
                    if self.每行不同加密:
                        content = self.AES对象[item['i']-1].decrypt(content)
                    else:
                        content = self.AES对象[0].decrypt(add_block(content))
                #item['i'] 已有
                item['size']=int(size)
                #写入到缓存目录
                if not os.path.exists(self.TEMP_DIR):
                    os.makedirs(self.TEMP_DIR, exist_ok=1)
                fpath = os.path.join(self.TEMP_DIR, '%010d.ts'%item['i'])
                try:
                    with open(fpath, 'wb') as f:
                        f.write(content)
                    if self.分离器:
                        item['content'] = '%010d.ts' % item['i']
                    else:
                        item['content'] = fpath # 去掉目录前缀
                except BaseException as ef:
                    raise Exception('写入文件错误: {}'.format(ef))
                if self.TS下载间隔时间:
                    time.sleep(self.TS下载间隔时间)
                return item
            except BaseException as e:
                if i==self.try_num-1:
                    打印错误(e)
        return None
    def get_url(self, url,type_='url',try_num=None,stream=False):
        try:
            v = getattr(self.options_headers, type_)
            if v:
                if isinstance(v, int) or isinstance(v, bool):
                    # 非整数1或者true 用默认的headers
                    headers = self.headers
                else:
                    # 替换掉headers
                    headers = v
            else:
                headers = None
            return get_request(url.strip(), cookies=self.cookies, headers=headers,stream=stream, proxies=self.proxies, allow_redirects=True, verify=False,curl=self.curl, try_num=try_num if try_num else self.try_num,timeout=self.timeout)
        except BaseException as e:
            raise Exception('get_url {}: {}'.format(type_, e))
    def run(self):
        try:
            返回=True
            if self.items and self.state:
                self.加密行 = self.加密行[:self.测试下载数量] if self.istest else self.加密行  # 测试行数
                self.__get_aes()
                if self.state:
                    print('[ {} ] [ {} ]: {}'.format(scolor('BIN') if self.二进制 else scolor('FF'),scolor('正在下载', 'warn'), scolor(self.fpath, 'yes')))
                    self.开始时间=time.time()
                    self.已下载大小=0
                    self.进度 = 0  # 统计进度条
                    pool=ThreadPoolExecutor(self.线程数)
                    self.items= self.items[:self.测试下载数量] if self.istest else self.items #测试行数
                    self.count = len(self.items)

                    data={}
                    L=len(self.items)
                    def callback(rt):
                        item = rt.result()
                        if item:
                            data[item['i']] = item['content']
                            self.已下载大小 += item['size']
                            t=time.time()-self.开始时间
                            seconds = t * L / (self.进度 + 1) - t
                            if seconds<1:
                                剩余时间=' '*12
                            else:
                                m, s = divmod(seconds, 60)
                                h, m = divmod(m, 60)
                                剩余时间 =' {:0=2.0f}:{:0=2.0f}:{:0=2.0f}'.format(h,m,s)
                            speed = '{:.2f}MB/S{}'.format(self.已下载大小 / 1024 / 1024 / t,剩余时间)
                            fsize='{:.2f}MB'.format(self.已下载大小 / 1024 / 1024)
                            print_end=""
                            if self.打印TS链接:
                                print_end=None
                                speed = speed + f"\n{item['url']}"
                            if self.进度条回调函数:
                                #'{}    {} {}/{} {} {}'.format(rt['name'],rt['bfb'], rt['i'],rt['count'],rt['size'],rt['speed'])
                                self.进度条回调函数({'name':self.fname,'bfb':'{}%'.format(int((self.进度+1)/self.count*100)),'size':fsize, 'i':self.进度+1, 'count':self.count,'speed':speed,'print_end':print_end})
                            else:
                                打印_进度条(fsize, self.进度, self.count, 1, speed, 类型=4,end=print_end)
                            lock.acquire()
                            self.进度 += 1
                            lock.release()
                        else:
                            nonlocal 返回
                            返回=False
                    tasks=[]
                    for item in self.items:
                        tasks.append(pool.submit(self.__download_ts,item).add_done_callback(callback))
                    pool.shutdown(wait=True)
                    if os.path.exists(self.fpath):
                        os.remove(self.fpath)
                    # 只有全部完成才保存
                    if 返回:
                        data = sorted(data.items(), key=lambda d: d[0], reverse=False)
                        if self.分离器:
                            file_txt=os.path.join(self.TEMP_DIR,'filelist.txt')
                            with open(file_txt,'w',encoding='utf-8') as f:
                                for d in data:
                                    f.write("file {}\n".format(d[1]))
                            print()
                            self.ff.ffmpeg_分离器合并(文件路径=self.fpath,文件名=file_txt)
                        else:
                            #二进制合并
                            if self.二进制:
                                with open(self.fpath, 'wb') as f:
                                    for d in data:
                                        with open(d[1], 'rb') as f1:
                                            f.write(f1.read())
                            else:
                                temp_mp4 = f'{self.fpath}.temp'
                                if os.path.exists(temp_mp4): os.remove(temp_mp4)
                                with open(temp_mp4, 'ab') as f:
                                    for d in data:
                                        with open(d[1], 'rb') as f1:
                                            f.write(f1.read())
                                print()
                                # ffmpeg -i "concat:input1.ts|input2.ts|input3.ts" -c copy -bsf:a aac_adtstoasc -movflags +faststart "output.mp4" -loglevel error
                                if self.显示FFMPEG错误:
                                    cmd=f'"{self.ff.ffmpeg_path}" -i "{temp_mp4}" -y -c copy -bsf:a aac_adtstoasc "{self.fpath}" -loglevel error'
                                else:
                                    cmd=f'"{self.ff.ffmpeg_path}" -i "{temp_mp4}" -y -c copy -bsf:a aac_adtstoasc "{self.fpath}" -loglevel quiet'
                                self.ff.执行(cmd,show=self.cmd_show)
                                if os.path.exists(temp_mp4):
                                    os.remove(temp_mp4)
                        #删除缓存目录
                        if os.path.exists(self.TEMP_DIR):
                            with error(ignore=True):
                                import shutil
                                shutil.rmtree(self.TEMP_DIR)
                    del tasks
                    del data
                else:
                    返回=False
            else:
                返回=False
            print()
            return 返回
        except BaseException as e:
            打印错误(e)
            return False
class 剪切板():
    def __init__(self):
        pass
    def 复制文本(self,字符串):
        import win32clipboard
        import win32con
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, 字符串)
        win32clipboard.CloseClipboard()
    def 粘贴文本(self):
        import win32clipboard
        import win32con
        win32clipboard.OpenClipboard()
        text = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
        win32clipboard.CloseClipboard()
        return text
    def 复制图片(self,图片路径):
        if os.path.exists(图片路径):
            import win32clipboard
            import win32con
            from PIL import Image
            imagepath = 图片路径
            img = Image.open(imagepath)  # Image.open可以打开网络图片与本地图片。
            output = BytesIO()  # BytesIO实现了在内存中读写bytes
            img.convert("RGB").save(output, "BMP")  # 以RGB模式保存图像
            data = output.getvalue()[14:]
            output.close()
            win32clipboard.OpenClipboard()  # 打开剪贴板
            win32clipboard.EmptyClipboard()  # 先清空剪贴板
            win32clipboard.SetClipboardData(win32con.CF_DIB, data)  # 将图片放入剪贴板
            win32clipboard.CloseClipboard()

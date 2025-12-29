# coding=utf-8

#
# Just for practising
#
import random
import sys
import threading
from threading import Thread
import datetime
import time
import socket
import functools
import logging
import zlib
import pandas as pd
import os
#from __future__ import unicode_literals, division
from collections import OrderedDict
import struct
import six


DEBUG = os.getenv("JSP_DEBUG", "")

if DEBUG:
    LOGLEVEL = logging.DEBUG
else:
    LOGLEVEL = logging.INFO

log = logging.getLogger("PYJSP")

log.setLevel(LOGLEVEL)
ch = logging.StreamHandler()
ch.setLevel(LOGLEVEL)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)

class JspConnectionError(Exception):
    pass
class JspFunctionCallError(Exception):
    def __init__(self, *args, **kwargs):
        super(JspFunctionCallError, self).__init__(*args, **kwargs)
        self.original_exception = None

DEFAULT_HEARTBEAT_INTERVAL = 10.0 # 10秒一个heartbeat
class HqHeartBeatThread(Thread):

    def __init__(self, api, stop_event, heartbeat_interval=DEFAULT_HEARTBEAT_INTERVAL):
        self.api = api
        self.client = api.client
        self.stop_event = stop_event
        self.heartbeat_interval = heartbeat_interval
        super(HqHeartBeatThread, self).__init__()

    def run(self):
        while not self.stop_event.is_set():
            self.stop_event.wait(self.heartbeat_interval)
            if self.client and (time.time() - self.api.last_ack_time > self.heartbeat_interval):
                try:
                    self.api.do_heartbeat()
                except Exception as e:
                    log.debug(str(e))


try:
    import cython
    if cython.compiled:
        def buffer(x):
            return x
except ImportError:
    pass
class SocketClientNotReady(Exception):
    pass
class SendPkgNotReady(Exception):
    pass
class SendRequestPkgFails(Exception):
    pass
class ResponseHeaderRecvFails(Exception):
    pass
class ResponseRecvFails(Exception):
    pass

RSP_HEADER_LEN = 0x10

class BaseParser(object):

    def __init__(self, client, lock=None):
        self.client = client
        self.data = None
        self.send_pkg = None

        self.rsp_header = None
        self.rsp_body = None
        self.rsp_header_len = RSP_HEADER_LEN

        if lock:
            self.lock = lock
        else:
            self.lock = None

    def setParams(self, *args, **xargs):
        """
        构建请求
        :return:
        """
        pass

    def parseResponse(self, body_buf):
        pass

    def setup(self):
        pass


    def call_api(self):
        if self.lock:
            with self.lock:
                log.debug("sending thread lock api call")
                result = self._call_api()
        else:
            result = self._call_api()
        return result

    def _call_api(self):

        self.setup()

        if not(self.client):
            raise SocketClientNotReady("socket client not ready")

        if not(self.send_pkg):
            raise SendPkgNotReady("send pkg not ready")

        nsended = self.client.send(self.send_pkg)

        self.client.send_pkg_num += 1
        self.client.send_pkg_bytes += nsended
        self.client.last_api_send_bytes = nsended

        if self.client.first_pkg_send_time is None:
            self.client.first_pkg_send_time = datetime.datetime.now()

        if DEBUG:
            log.debug("send package:" + str(self.send_pkg))
        if nsended != len(self.send_pkg):
            log.debug("send bytes error")
            raise SendRequestPkgFails("send fails")
        else:
            head_buf = self.client.recv(self.rsp_header_len)
            if DEBUG:
                log.debug("recv head_buf:" + str(head_buf)  + " |len is :" + str(len(head_buf)))
            if len(head_buf) == self.rsp_header_len:
                self.client.recv_pkg_num += 1
                self.client.recv_pkg_bytes += self.rsp_header_len
                _, _, _, zipsize, unzipsize = struct.unpack("<IIIHH", head_buf)
                if DEBUG:
                    log.debug("zip size is: " + str(zipsize))
                body_buf = bytearray()

                last_api_recv_bytes = self.rsp_header_len
                while True:
                    buf = self.client.recv(zipsize)
                    len_buf = len(buf)
                    self.client.recv_pkg_num += 1
                    self.client.recv_pkg_bytes += len_buf
                    last_api_recv_bytes += len_buf
                    body_buf.extend(buf)
                    if not(buf) or len_buf == 0 or len(body_buf) == zipsize:
                        break

                self.client.last_api_recv_bytes = last_api_recv_bytes

                if len(buf) == 0:
                    log.debug("接收数据体失败服务器断开连接")
                    raise ResponseRecvFails("接收数据体失败服务器断开连接")
                if zipsize == unzipsize:
                    log.debug("不需要解压")
                else:
                    log.debug("需要解压")
                    if sys.version_info[0] == 2:
                        unziped_data = zlib.decompress(buffer(body_buf))
                    else:
                        unziped_data = zlib.decompress(body_buf)
                    body_buf = unziped_data
                    ## 解压
                if DEBUG:
                    log.debug("recv body: ")
                    log.debug(body_buf)

                return self.parseResponse(body_buf)

            else:
                log.debug("head_buf is not 0x10")
                raise ResponseHeaderRecvFails("head_buf is not 0x10 : " + str(head_buf))


class RawParser(BaseParser):
    def setParams(self, pkg):
        self.send_pkg = pkg
    def parseResponse(self, body_buf):
        return body_buf


CONNECT_TIMEOUT = 5.000
RECV_HEADER_LEN = 0x10
DEFAULT_HEARTBEAT_INTERVAL = 10.0
def update_last_ack_time(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kw):
        self.last_ack_time = time.time()
        log.debug("last ack time update to " + str(self.last_ack_time))
        current_exception = None
        try:
            ret = func(self, *args, **kw)
        except Exception as e:
            current_exception = e
            log.debug("hit exception on req exception is " + str(e))
            if self.auto_retry:
                for time_interval in self.retry_strategy.gen():
                    try:
                        time.sleep(time_interval)
                        self.disconnect()
                        self.connect(self.ip, self.port)
                        ret = func(self, *args, **kw)
                        if ret:
                            return ret
                    except Exception as retry_e:
                        current_exception = retry_e
                        log.debug(
                            "hit exception on *retry* req exception is " + str(retry_e))

                log.debug("perform auto retry on req ")

            self.last_transaction_failed = True
            ret = None
            if self.raise_exception:
                to_raise = JspFunctionCallError("calling function error")
                to_raise.original_exception = current_exception if current_exception else None
                raise to_raise
        return ret
    return wrapper
class RetryStrategy(object):
    @classmethod
    def gen(cls):
        raise NotImplementedError("need to override")
class DefaultRetryStrategy(RetryStrategy):
    @classmethod
    def gen(cls):
        # 默认重试4次 ... 时间间隔如下
        for time_interval in [0.1, 0.5, 1, 2]:
            yield time_interval
class TrafficStatSocket(socket.socket):

    def __init__(self, sock, mode):
        super(TrafficStatSocket, self).__init__(sock, mode)
        # 流量统计相关
        self.send_pkg_num = 0  # 发送次数
        self.recv_pkg_num = 0  # 接收次数
        self.send_pkg_bytes = 0  # 发送字节
        self.recv_pkg_bytes = 0  # 接收字节数
        self.first_pkg_send_time = None  # 第一个数据包发送时间

        self.last_api_send_bytes = 0  # 最近的一次api调用的发送字节数
        self.last_api_recv_bytes = 0  # 最近一次api调用的接收字节数
class BaseSocketClient(object):

    def __init__(self, multithread=False, heartbeat=True, auto_retry=False, raise_exception=False):
        self.need_setup = True
        if multithread or heartbeat:
            self.lock = threading.Lock()
        else:
            self.lock = None

        self.client = None
        self.heartbeat = heartbeat
        self.heartbeat_thread = None
        self.stop_event = None
        self.heartbeat_interval = DEFAULT_HEARTBEAT_INTERVAL  # 默认10秒一个心跳包
        self.last_ack_time = time.time()
        self.last_transaction_failed = False
        self.ip = None
        self.port = None

        # 是否重试
        self.auto_retry = auto_retry
        # 可以覆盖这个属性，使用新的重试策略
        self.retry_strategy = DefaultRetryStrategy()
        # 是否在函数调用出错的时候抛出异常
        self.raise_exception = raise_exception

    def connect(self, ip='101.227.73.20', port=7709, time_out=CONNECT_TIMEOUT, bindport=None, bindip='0.0.0.0'):

        self.client = TrafficStatSocket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.settimeout(time_out)
        log.debug("connecting to server : %s on port :%d" % (ip, port))
        try:
            self.ip = ip
            self.port = port
            if bindport is not None:
                self.client.bind((bindip, bindport))
            self.client.connect((ip, port))
        except socket.timeout as e:
            # print(str(e))
            log.debug("connection expired")
            if self.raise_exception:
                raise JspConnectionError("connection timeout error")
            return False
        except Exception as e:
            if self.raise_exception:
                raise JspConnectionError("other errors")
            return False

        log.debug("connected!")

        if self.need_setup:
            self.setup()

        if self.heartbeat:
            self.stop_event = threading.Event()
            self.heartbeat_thread = HqHeartBeatThread(
                self, self.stop_event, self.heartbeat_interval)
            self.heartbeat_thread.start()
        return self

    def disconnect(self):

        if self.heartbeat_thread and \
                self.heartbeat_thread.is_alive():
            self.stop_event.set()

        if self.client:
            log.debug("disconnecting")
            try:
                self.client.shutdown(socket.SHUT_RDWR)
                self.client.close()
                self.client = None
            except Exception as e:
                log.debug(str(e))
                if self.raise_exception:
                    raise JspConnectionError("disconnect err")
            log.debug("disconnected")

    def close(self):
        self.disconnect()

    def get_traffic_stats(self):
        if self.client.first_pkg_send_time is not None:
            total_seconds = (datetime.datetime.now() -
                             self.client.first_pkg_send_time).total_seconds()
            if total_seconds != 0:
                send_bytes_per_second = self.client.send_pkg_bytes // total_seconds
                recv_bytes_per_second = self.client.recv_pkg_bytes // total_seconds
            else:
                send_bytes_per_second = None
                recv_bytes_per_second = None
        else:
            total_seconds = None
            send_bytes_per_second = None
            recv_bytes_per_second = None

        return {
            "send_pkg_num": self.client.send_pkg_num,
            "recv_pkg_num": self.client.recv_pkg_num,
            "send_pkg_bytes": self.client.send_pkg_bytes,
            "recv_pkg_bytes": self.client.recv_pkg_bytes,
            "first_pkg_send_time": self.client.first_pkg_send_time,
            "total_seconds": total_seconds,
            "send_bytes_per_second": send_bytes_per_second,
            "recv_bytes_per_second": recv_bytes_per_second,
            "last_api_send_bytes": self.client.last_api_send_bytes,
            "last_api_recv_bytes": self.client.last_api_recv_bytes,
        }

    # for debuging and testing protocol
    def send_raw_pkg(self, pkg):
        cmd = RawParser(self.client, lock=self.lock)
        cmd.setParams(pkg)
        return cmd.call_api()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def to_df(self, v):
        if isinstance(v, list):
            return pd.DataFrame(data=v)
        elif isinstance(v, dict):
            return pd.DataFrame(data=[v, ])
        else:
            return pd.DataFrame(data=[{'value': v}])

class JspFileNotFoundException(Exception):
    pass
class JspNotAssignVipdocPathException(Exception):
    pass
class BaseReader(object):

    def unpack_records(self, format, data):
        record_struct = struct.Struct(format)
        return (record_struct.unpack_from(data, offset)
                for offset in range(0, len(data), record_struct.size))

    def get_df(self, code_or_file, exchange=None):
        raise NotImplementedError('not yet')
BlockReader_TYPE_FLAT = 0
BlockReader_TYPE_GROUP = 1

class BlockReader(BaseReader):

    def get_df(self, fname, result_type=BlockReader_TYPE_FLAT):
        result = self.get_data(fname, result_type)
        return pd.DataFrame(result)

    def get_data(self, fname, result_type=BlockReader_TYPE_FLAT):

        result = []

        if type(fname) is not bytearray:
            with open(fname, "rb") as f:
                data = f.read()
        else:
            data = fname

        pos = 384
        (num,) = struct.unpack("<H", data[pos: pos + 2])
        pos += 2
        for i in range(num):
            blockname_raw = data[pos: pos + 9]
            pos += 9
            blockname = blockname_raw.decode("gbk", 'ignore').rstrip("\x00")
            stock_count, block_type = struct.unpack("<HH", data[pos: pos + 4])
            pos += 4
            block_stock_begin = pos
            codes = []
            for code_index in range(stock_count):
                one_code = data[pos: pos + 7].decode("utf-8", 'ignore').rstrip("\x00")
                pos += 7

                if result_type == BlockReader_TYPE_FLAT:
                    result.append(
                        OrderedDict([
                            ("blockname", blockname),
                            ("block_type", block_type),
                            ("code_index", code_index),
                            ("code", one_code),
                        ])
                    )
                elif result_type == BlockReader_TYPE_GROUP:
                    codes.append(one_code)

            if result_type == BlockReader_TYPE_GROUP:
                result.append(
                    OrderedDict([
                        ("blockname", blockname),
                        ("block_type", block_type),
                        ("stock_count", stock_count),
                        ("code_list", ",".join(codes))
                    ])
                )

            pos = block_stock_begin + 2800

        return result
class CustomerBlockReader(BaseReader):

    def get_df(self, fname, result_type=BlockReader_TYPE_FLAT):
        result = self.get_data(fname, result_type)
        return pd.DataFrame(result)

    def get_data(self, fname, result_type=BlockReader_TYPE_FLAT):

        result = []

        if not os.path.isdir(fname):
            raise Exception('not a directory')

        block_file = '/'.join([fname, 'blocknew.cfg'])

        if not os.path.exists(block_file):
            raise Exception('file not exists')

        block_data = open(block_file, 'rb').read()

        pos = 0
        result = []
        # print(block_data.decode('gbk','ignore'))
        while pos < len(block_data):
            n1 = block_data[pos:pos + 50].decode('gbk', 'ignore').rstrip("\x00")
            n2 = block_data[pos + 50:pos + 120].decode('gbk', 'ignore').rstrip("\x00")
            pos = pos + 120

            n1 = n1.split('\x00')[0]
            n2 = n2.split('\x00')[0]
            bf = '/'.join([fname, n2 + '.blk'])
            if not os.path.exists(bf):
                raise Exception('file not exists')

            codes = open(bf).read().splitlines()
            if result_type == BlockReader_TYPE_FLAT:
                for index, code in enumerate(codes):
                    if code != '':
                        result.append(
                            OrderedDict([
                                ("blockname", n1),
                                ("block_type", n2),
                                ('code_index', index),
                                ('code', code[1:])
                            ])
                        )

            if result_type == BlockReader_TYPE_GROUP:
                cc = [c[1:] for c in codes if c != '']
                result.append(
                    OrderedDict([
                        ("blockname", n1),
                        ("block_type", n2),
                        ("stock_count", len(cc)),
                        ("code_list", ",".join(cc))
                    ])
                )

        return result


class GetBlockInfoMeta(BaseParser):
    def setParams(self, block_file):
        if type(block_file) is six.text_type:
            block_file = block_file.encode("utf-8")
        pkg = bytearray.fromhex(u'0C 39 18 69 00 01 2A 00 2A 00 C5 02')
        pkg.extend(struct.pack(u"<{}s".format(0x2a - 2), block_file))
        self.send_pkg = pkg


    def parseResponse(self, body_buf):
        (size, _, hash_value, _ ) = struct.unpack(u"<I1s32s1s", body_buf)
        return {
            "size": size,
            "hash_value" : hash_value
        }
class GetBlockInfo(BaseParser):

    def setParams(self, block_file, start, size):
        if type(block_file) is six.text_type:
            block_file = block_file.encode("utf-8")
        pkg = bytearray.fromhex(u'0c 37 18 6a 00 01 6e 00 6e 00 b9 06')
        #pkg = bytearray.fromhex(u'0c 33 18 6a 00 01 6e 00 6e 00 b9 06 60 ea 00 00 30 75 00 00')
        pkg.extend(struct.pack(u"<II{}s".format(0x6e-10), start, size, block_file))
        self.send_pkg = pkg

    def parseResponse(self, body_buf):
        return body_buf[4:]
def get_and_parse_block_info(client, blockfile):
    try:
        meta = client.get_block_info_meta(blockfile)
    except Exception as e:
        return None

    if not meta:
        return None

    size = meta['size']
    one_chunk = 0x7530


    chuncks = size // one_chunk
    if size % one_chunk != 0:
        chuncks += 1

    file_content = bytearray()
    for seg in range(chuncks):
        start = seg * one_chunk
        piece_data = client.get_block_info(blockfile, start, size)
        file_content.extend(piece_data)

    return BlockReader().get_data(file_content, BlockReader_TYPE_FLAT)

class GetCompanyInfoCategory(BaseParser):

    def setParams(self, market, code):
        if type(code) is six.text_type:
            code = code.encode("utf-8")

        pkg = bytearray.fromhex(u'0c 0f 10 9b 00 01 0e 00 0e 00 cf 02')
        pkg.extend(struct.pack(u"<H6sI", market, code, 0))
        self.send_pkg = pkg

    def parseResponse(self, body_buf):
        pos = 0
        (num, ) = struct.unpack("<H", body_buf[:2])
        pos += 2

        category = []



        def get_str(b):
            p = b.find(b'\x00')
            if p != -1:
                b = b[0: p]
            try:
                n = b.decode("gbk")
            except Exception as e:
                n = "unkown_str"
            return n

        for i in range(num):
            (name, filename, start, length) = struct.unpack(u"<64s80sII", body_buf[pos: pos+ 152])
            pos += 152
            entry = OrderedDict(
                [
                    ('name', get_str(name)),
                    ('filename', get_str(filename)),
                    ('start', start),
                    ('length', length),
                ]
            )
            category.append(entry)
        return category

class GetCompanyInfoContent(BaseParser):

    def setParams(self, market, code, filename, start, length):
        if type(code) is six.text_type:
            code = code.encode("utf-8")

        if type(filename) is six.text_type:
            filename = filename.encode("utf-8")

        if len(filename) != 80:
            filename = filename.ljust(80, b'\x00')


        pkg = bytearray.fromhex(u'0c 07 10 9c 00 01 68 00 68 00 d0 02')
        pkg.extend(struct.pack(u"<H6sH80sIII", market, code, 0, filename, start, length, 0))
        self.send_pkg = pkg

    def parseResponse(self, body_buf):
        pos = 0
        _, length = struct.unpack(u'<10sH', body_buf[:12])
        pos += 12
        content = body_buf[pos: pos+length]
        return content.decode("gbk")

class GetFinanceInfo(BaseParser):

    def setParams(self, market, code):
        if type(code) is six.text_type:
            code = code.encode("utf-8")
        pkg = bytearray.fromhex(u'0c 1f 18 76 00 01 0b 00 0b 00 10 00 01 00')
        pkg.extend(struct.pack(u"<B6s", market, code))
        self.send_pkg = pkg

    def parseResponse(self, body_buf):
        pos = 0
        pos += 2 #skip num ,we only query 1 in this case
        market, code = struct.unpack(u"<B6s",body_buf[pos: pos+7])
        pos += 7

        (
            liutongguben,
            province,
            industry,
            updated_date,
            ipo_date,
            zongguben,
            guojiagu,
            faqirenfarengu,
            farengu,
            bgu,
            hgu,
            zhigonggu,
            zongzichan,
            liudongzichan,
            gudingzichan,
            wuxingzichan,
            gudongrenshu,
            liudongfuzhai,
            changqifuzhai,
            zibengongjijin,
            jingzichan,
            zhuyingshouru,
            zhuyinglirun,
            yingshouzhangkuan,
            yingyelirun,
            touzishouyu,
            jingyingxianjinliu,
            zongxianjinliu,
            cunhuo,
            lirunzonghe,
            shuihoulirun,
            jinglirun,
            weifenlirun,
            baoliu1,
            baoliu2
        ) = struct.unpack("<fHHIIffffffffffffffffffffffffffffff", body_buf[pos:])

        def _get_v(v):
            return v

        return OrderedDict(
            [
                ("market", market),
                ("code", code.decode("utf-8")),
                ("liutongguben", _get_v(liutongguben)*10000),
                ('province', province),
                ('industry', industry),
                ('updated_date', updated_date),
                ('ipo_date', ipo_date),
                ("zongguben", _get_v(zongguben)*10000),
                ("guojiagu", _get_v(guojiagu)*10000),
                ("faqirenfarengu", _get_v(faqirenfarengu)*10000),
                ("farengu", _get_v(farengu)*10000),
                ("bgu", _get_v(bgu)*10000),
                ("hgu", _get_v(hgu)*10000),
                ("zhigonggu", _get_v(zhigonggu)*10000),
                ("zongzichan", _get_v(zongzichan)*10000),
                ("liudongzichan", _get_v(liudongzichan)*10000),
                ("gudingzichan", _get_v(gudingzichan)*10000),
                ("wuxingzichan", _get_v(wuxingzichan)*10000),
                ("gudongrenshu", _get_v(gudongrenshu)),
                ("liudongfuzhai", _get_v(liudongfuzhai)*10000),
                ("changqifuzhai", _get_v(changqifuzhai)*10000),
                ("zibengongjijin", _get_v(zibengongjijin)*10000),
                ("jingzichan", _get_v(jingzichan)*10000),
                ("zhuyingshouru", _get_v(zhuyingshouru)*10000),
                ("zhuyinglirun", _get_v(zhuyinglirun)*10000),
                ("yingshouzhangkuan", _get_v(yingshouzhangkuan)*10000),
                ("yingyelirun", _get_v(yingyelirun)*10000),
                ("touzishouyu", _get_v(touzishouyu)*10000),
                ("jingyingxianjinliu", _get_v(jingyingxianjinliu)*10000),
                ("zongxianjinliu", _get_v(zongxianjinliu)*10000),
                ("cunhuo", _get_v(cunhuo)*10000),
                ("lirunzonghe", _get_v(lirunzonghe)*10000),
                ("shuihoulirun", _get_v(shuihoulirun)*10000),
                ("jinglirun", _get_v(jinglirun)*10000),
                ("weifenpeilirun", _get_v(weifenlirun)*10000),
                ("meigujingzichan", _get_v(baoliu1)),
                ("baoliu2", _get_v(baoliu2))
            ]
        )

def get_price(data, pos):
    pos_byte = 6
    bdata = indexbytes(data, pos)
    intdata = bdata & 0x3f
    if bdata & 0x40:
        sign = True
    else:
        sign = False

    if bdata & 0x80:
        while True:
            pos += 1
            bdata = indexbytes(data, pos)
            intdata += (bdata & 0x7f) << pos_byte
            pos_byte += 7

            if bdata & 0x80:
                pass
            else:
                break

    pos += 1

    if sign:
        intdata = -intdata

    return intdata, pos
def get_volume(ivol):
    logpoint = ivol >> (8 * 3)
    hheax = ivol >> (8 * 3);  # [3]
    hleax = (ivol >> (8 * 2)) & 0xff;  # [2]
    lheax = (ivol >> 8) & 0xff;  # [1]
    lleax = ivol & 0xff;  # [0]

    dbl_1 = 1.0
    dbl_2 = 2.0
    dbl_128 = 128.0

    dwEcx = logpoint * 2 - 0x7f;
    dwEdx = logpoint * 2 - 0x86;
    dwEsi = logpoint * 2 - 0x8e;
    dwEax = logpoint * 2 - 0x96;
    if dwEcx < 0:
        tmpEax = - dwEcx
    else:
        tmpEax = dwEcx

    dbl_xmm6 = 0.0
    dbl_xmm6 = pow(2.0, tmpEax)
    if dwEcx < 0:
        dbl_xmm6 = 1.0 / dbl_xmm6

    dbl_xmm4 = 0
    if hleax > 0x80:
        tmpdbl_xmm3 = 0.0
        tmpdbl_xmm1 = 0.0
        dwtmpeax = dwEdx + 1
        tmpdbl_xmm3 = pow(2.0, dwtmpeax)
        dbl_xmm0 = pow(2.0, dwEdx) * 128.0
        dbl_xmm0 += (hleax & 0x7f) * tmpdbl_xmm3
        dbl_xmm4 = dbl_xmm0

    else:
        dbl_xmm0 = 0.0
        if dwEdx >= 0:
            dbl_xmm0 = pow(2.0, dwEdx) * hleax
        else:
            dbl_xmm0 = (1 / pow(2.0, dwEdx)) * hleax
        dbl_xmm4 = dbl_xmm0

    dbl_xmm3 = pow(2.0, dwEsi) * lheax
    dbl_xmm1 = pow(2.0, dwEax) * lleax
    if hleax & 0x80:
        dbl_xmm3 *= 2.0
        dbl_xmm1 *= 2.0

    dbl_ret = dbl_xmm6 + dbl_xmm4 + dbl_xmm3 + dbl_xmm1
    return dbl_ret
def get_datetime(category, buffer, pos):
    year = 0
    month = 0
    day = 0
    hour = 15
    minute = 0
    if category < 4 or category == 7 or category == 8:
        (zipday, tminutes) = struct.unpack("<HH", buffer[pos: pos + 4])
        year = (zipday >> 11) + 2004
        month = int((zipday % 2048) / 100)
        day = (zipday % 2048) % 100

        hour = int(tminutes / 60)
        minute = tminutes % 60
    else:
        (zipday,) = struct.unpack("<I", buffer[pos: pos + 4])

        year = int(zipday / 10000);
        month = int((zipday % 10000) / 100)
        day = zipday % 100

    pos += 4

    return year, month, day, hour, minute, pos
def get_time(buffer, pos):
    (tminutes, ) = struct.unpack("<H", buffer[pos: pos + 2])
    hour = int(tminutes / 60)
    minute = tminutes % 60
    pos += 2

    return hour, minute, pos
def indexbytes(data, pos):

    if six.PY2:
        if type(data) is bytearray:
            return data[pos]
        else:
            return six.indexbytes(data, pos)
    else:
        return data[pos]
class GetHistoryMinuteTimeData(BaseParser):

    def setParams(self, market, code, date):
        if (type(date) is six.text_type) or (type(date) is six.binary_type):
            date = int(date)

        if type(code) is six.text_type:
            code = code.encode("utf-8")

        pkg = bytearray.fromhex(u'0c 01 30 00 01 01 0d 00 0d 00 b4 0f')
        pkg.extend(struct.pack("<IB6s", date, market, code))
        self.send_pkg = pkg

    def parseResponse(self, body_buf):
        pos = 0
        (num, ) = struct.unpack("<H", body_buf[:2])
        last_price = 0
        # 跳过了4个字节，实在不知道是什么意思
        pos += 6
        prices = []
        for i in range(num):
            price_raw, pos = get_price(body_buf, pos)
            reversed1, pos = get_price(body_buf, pos)
            vol, pos = get_price(body_buf, pos)
            last_price = last_price + price_raw
            price = OrderedDict(
                [
                    ("price", float(last_price)/100),
                    ("vol", vol)
                ]
            )
            prices.append(price)
        return prices

class GetHistoryTransactionData(BaseParser):
    def setParams(self, market, code, start, count, date):
        if type(code) is six.text_type:
            code = code.encode("utf-8")

        if type(date) is (type(date) is six.text_type) or (type(date) is six.binary_type):
            date = int(date)

        pkg = bytearray.fromhex(u'0c 01 30 01 00 01 12 00 12 00 b5 0f')
        pkg.extend(struct.pack("<IH6sHH", date, market, code, start, count))
        self.send_pkg = pkg
    def parseResponse(self, body_buf):
        pos = 0
        (num, ) = struct.unpack("<H", body_buf[:2])
        pos += 2
        ticks = []

        # skip 4 bytes
        pos += 4

        last_price = 0
        for i in range(num):
            ### ?? get_time
            # \x80\x03 = 14:56

            hour, minute, pos = get_time(body_buf, pos)

            price_raw, pos = get_price(body_buf, pos)
            vol, pos = get_price(body_buf, pos)
            buyorsell, pos = get_price(body_buf, pos)
            _, pos = get_price(body_buf, pos)

            last_price = last_price + price_raw

            tick = OrderedDict(
                [
                    ("time", "%02d:%02d" % (hour, minute)),
                    ("price", float(last_price)/100),
                    ("vol", vol),
                    ("buyorsell", buyorsell),
                ]
            )

            ticks.append(tick)

        return ticks

class GetIndexBarsCmd(BaseParser):

    def setParams(self, category, market, code, start, count):
        if type(code) is six.text_type:
            code = code.encode("utf-8")

        self.category = category

        values = (
            0x10c,
            0x01016408,
            0x1c,
            0x1c,
            0x052d,
            market,
            code,
            category,
            1,
            start,
            count,
            0, 0, 0  # I + I +  H total 10 zero
        )

        pkg = struct.pack("<HIHHHH6sHHHHIIH", *values)
        self.send_pkg = pkg

    def parseResponse(self, body_buf):
        pos = 0

        (ret_count,) = struct.unpack("<H", body_buf[0: 2])
        pos += 2

        klines = []

        pre_diff_base = 0
        for i in range(ret_count):
            year, month, day, hour, minute, pos = get_datetime(self.category, body_buf, pos)

            price_open_diff, pos = get_price(body_buf, pos)
            price_close_diff, pos = get_price(body_buf, pos)

            price_high_diff, pos = get_price(body_buf, pos)
            price_low_diff, pos = get_price(body_buf, pos)

            (vol_raw,) = struct.unpack("<I", body_buf[pos: pos + 4])
            vol = get_volume(vol_raw)

            pos += 4
            (dbvol_raw,) = struct.unpack("<I", body_buf[pos: pos + 4])
            dbvol = get_volume(dbvol_raw)
            pos += 4

            (up_count, down_count) = struct.unpack("<HH", body_buf[pos: pos + 4])
            pos += 4

            open = self._cal_price1000(price_open_diff, pre_diff_base)

            price_open_diff = price_open_diff + pre_diff_base

            close = self._cal_price1000(price_open_diff, price_close_diff)
            high = self._cal_price1000(price_open_diff, price_high_diff)
            low = self._cal_price1000(price_open_diff, price_low_diff)

            pre_diff_base = price_open_diff + price_close_diff

            #### 为了避免python处理浮点数的时候，浮点数运算不精确问题，这里引入了多余的代码

            kline = OrderedDict([
                ("open", open),
                ("close", close),
                ("high", high),
                ("low", low),
                ("vol", vol),
                ("amount", dbvol),
                ("year", year),
                ("month", month),
                ("day", day),
                ("hour", hour),
                ("minute", minute),
                ("datetime", "%d-%02d-%02d %02d:%02d" % (year, month, day, hour, minute)),
                ("up_count", up_count),
                ("down_count", down_count)
            ])
            klines.append(kline)
        return klines

    def _cal_price1000(self, base_p, diff):
        return float(base_p + diff)/1000

class GetMinuteTimeData(BaseParser):

    def setParams(self, market, code):
        if type(code) is six.text_type:
            code = code.encode("utf-8")
        pkg = bytearray.fromhex(u'0c 1b 08 00 01 01 0e 00 0e 00 1d 05')
        pkg.extend(struct.pack("<H6sI", market, code, 0))
        self.send_pkg = pkg

    def parseResponse(self, body_buf):
        pos = 0
        (num, ) = struct.unpack("<H", body_buf[:2])
        last_price = 0
        pos += 4
        prices = []
        for i in range(num):
            price_raw, pos = get_price(body_buf, pos)
            reversed1, pos = get_price(body_buf, pos)
            vol, pos = get_price(body_buf, pos)
            last_price = last_price + price_raw
            price = OrderedDict(
                [
                    ("price", float(last_price)/100),
                    ("vol", vol)
                ]
            )
            prices.append(price)
        return prices

class GetSecurityBarsCmd(BaseParser):

    def setParams(self, category, market, code, start, count):
        if type(code) is six.text_type:
            code = code.encode("utf-8")

        self.category = category

        values = (
            0x10c,
            0x01016408,
            0x1c,
            0x1c,
            0x052d,
            market,
            code,
            category,
            1,
            start,
            count,
            0, 0, 0  # I + I +  H total 10 zero
        )

        pkg = struct.pack("<HIHHHH6sHHHHIIH", *values)
        self.send_pkg = pkg

    def parseResponse(self, body_buf):
        pos = 0

        (ret_count,) = struct.unpack("<H", body_buf[0: 2])
        pos += 2

        klines = []

        pre_diff_base = 0
        for i in range(ret_count):
            year, month, day, hour, minute, pos = get_datetime(self.category, body_buf, pos)

            price_open_diff, pos = get_price(body_buf, pos)
            price_close_diff, pos = get_price(body_buf, pos)

            price_high_diff, pos = get_price(body_buf, pos)
            price_low_diff, pos = get_price(body_buf, pos)

            (vol_raw,) = struct.unpack("<I", body_buf[pos: pos + 4])
            vol = get_volume(vol_raw)

            pos += 4
            (dbvol_raw,) = struct.unpack("<I", body_buf[pos: pos + 4])
            dbvol = get_volume(dbvol_raw)
            pos += 4

            open = self._cal_price1000(price_open_diff, pre_diff_base)

            price_open_diff = price_open_diff + pre_diff_base

            close = self._cal_price1000(price_open_diff, price_close_diff)
            high = self._cal_price1000(price_open_diff, price_high_diff)
            low = self._cal_price1000(price_open_diff, price_low_diff)

            pre_diff_base = price_open_diff + price_close_diff

            #### 为了避免python处理浮点数的时候，浮点数运算不精确问题，这里引入了多余的代码

            kline = OrderedDict([
                ("open", open),
                ("close", close),
                ("high", high),
                ("low", low),
                ("vol", vol),
                ("amount", dbvol),
                ("year", year),
                ("month", month),
                ("day", day),
                ("hour", hour),
                ("minute", minute),
                ("datetime", "%d-%02d-%02d %02d:%02d" % (year, month, day, hour, minute))
            ])
            klines.append(kline)
        return klines

    def _cal_price1000(self, base_p, diff):
        return float(base_p + diff)/1000

class GetSecurityCountCmd(BaseParser):

    def setParams(self, market):

        pkg = bytearray.fromhex(u"0c 0c 18 6c 00 01 08 00 08 00 4e 04")
        market_pkg = struct.pack("<H", market)
        pkg.extend(market_pkg)
        pkg.extend(b'\x75\xc7\x33\x01')
        self.send_pkg = pkg

    def parseResponse(self, body_buf):
        (num, ) = struct.unpack("<H", body_buf[:2])
        return num

class GetSecurityList(BaseParser):

    def setParams(self, market, start):
        pkg = bytearray.fromhex(u'0c 01 18 64 01 01 06 00 06 00 50 04')
        pkg_param = struct.pack("<HH", market, start)
        pkg.extend(pkg_param)
        self.send_pkg = pkg

    def parseResponse(self, body_buf):

        pos = 0
        (num, ) = struct.unpack("<H", body_buf[:2])
        pos += 2
        stocks = []
        for i in range(num):

            # b'880023d\x00\xd6\xd0\xd0\xa1\xc6\xbd\xbe\xf9.9\x04\x00\x02\x9a\x99\x8cA\x00\x00\x00\x00'
            # 880023 100 中小平均 276782 2 17.575001 0 80846648

            one_bytes = body_buf[pos: pos + 29]

            (code, volunit,
             name_bytes, reversed_bytes1, decimal_point,
             pre_close_raw, reversed_bytes2) = struct.unpack("<6sH8s4sBI4s", one_bytes)

            code = code.decode("utf-8")
            name = name_bytes.decode("gbk").rstrip("\x00")
            pre_close = get_volume(pre_close_raw)
            pos += 29

            one = OrderedDict(
                [
                    ('code', code),
                    ('volunit', volunit),
                    ('decimal_point', decimal_point),
                    ('name', name),
                    ('pre_close', pre_close),
                ]
            )

            stocks.append(one)


        return stocks

class GetSecurityQuotesCmd(BaseParser):

    def setParams(self, all_stock):
        stock_len = len(all_stock)
        if stock_len <= 0:
            return False

        pkgdatalen = stock_len * 7 + 12

        values = (
            0x10c,
            0x02006320,
            pkgdatalen,
            pkgdatalen,
            0x5053e,
            0,
            0,
            stock_len,
        )

        pkg_header = struct.pack("<HIHHIIHH", *values)
        pkg = bytearray(pkg_header)
        for stock in all_stock:
            market, code = stock
            if type(code) is six.text_type:
                code = code.encode("utf-8")
            one_stock_pkg = struct.pack("<B6s", market, code)
            pkg.extend(one_stock_pkg)

        self.send_pkg = pkg

    def parseResponse(self, body_buf):
        pos = 0
        pos += 2  # skip b1 cb
        (num_stock,) = struct.unpack("<H", body_buf[pos: pos + 2])
        pos += 2
        stocks = []

        for _ in range(num_stock):
            # print(body_buf[pos:])
            # b'\x00000001\x95\n\x87\x0e\x01\x01\x05\x00\xb1\xb9\xd6\r\xc7\x0e\x8d\xd7\x1a\x84\x04S\x9c<M\xb6\xc8\x0e\x97\x8e\x0c\x00\xae\n\x00\x01\xa0\x1e\x9e\xb3\x03A\x02\x84\xf9\x01\xa8|B\x03\x8c\xd6\x01\xb0lC\x04\xb7\xdb\x02\xac\x7fD\x05\xbb\xb0\x01\xbe\xa0\x01y\x08\x01GC\x04\x00\x00\x95\n'
            (market, code, active1) = struct.unpack(
                "<B6sH", body_buf[pos: pos + 9])
            pos += 9
            price, pos = get_price(body_buf, pos)
            last_close_diff, pos = get_price(body_buf, pos)
            open_diff, pos = get_price(body_buf, pos)
            high_diff, pos = get_price(body_buf, pos)
            low_diff, pos = get_price(body_buf, pos)
            # 不确定这里应该是用 get_price 跳过还是直接跳过4个bytes
            # if price == 0 and last_close_diff == 0 and open_diff == 0 and high_diff == 0 and low_diff == 0:
            #     # 这个股票当前应该无法获取信息, 这个时候，这个值一般是0 或者 100
            #     #reversed_bytes0 = body_buf[pos: pos + 1]
            #     #pos += 1
            #     # 感觉这里应该都可以用 get_price ，但是由于一次性改动影响比较大，所以暂时只针对没有行情的股票做改动
            #     reversed_bytes0, pos = get_price(body_buf, pos)
            # else:
            #     reversed_bytes0 = body_buf[pos: pos + 4]
            #     pos += 4
            reversed_bytes0, pos = get_price(body_buf, pos)
            # reversed_bytes0, pos = get_price(body_buf, pos)
            # 应该是 -price
            reversed_bytes1, pos = get_price(body_buf, pos)
            # print('reversed_bytes1:' + str(reversed_bytes1)  + ",price" + str(price))
            # assert (reversed_bytes1 == -price)
            vol, pos = get_price(body_buf, pos)
            cur_vol, pos = get_price(body_buf, pos)
            (amount_raw,) = struct.unpack("<I", body_buf[pos: pos + 4])
            amount = get_volume(amount_raw)
            pos += 4
            s_vol, pos = get_price(body_buf, pos)
            b_vol, pos = get_price(body_buf, pos)
            reversed_bytes2, pos = get_price(body_buf, pos)
            reversed_bytes3, pos = get_price(body_buf, pos)

            bid1, pos = get_price(body_buf, pos)
            ask1, pos = get_price(body_buf, pos)
            bid_vol1, pos = get_price(body_buf, pos)
            ask_vol1, pos = get_price(body_buf, pos)

            bid2, pos = get_price(body_buf, pos)
            ask2, pos = get_price(body_buf, pos)
            bid_vol2, pos = get_price(body_buf, pos)
            ask_vol2, pos = get_price(body_buf, pos)

            bid3, pos = get_price(body_buf, pos)
            ask3, pos = get_price(body_buf, pos)
            bid_vol3, pos = get_price(body_buf, pos)
            ask_vol3, pos = get_price(body_buf, pos)

            bid4, pos = get_price(body_buf, pos)
            ask4, pos = get_price(body_buf, pos)
            bid_vol4, pos = get_price(body_buf, pos)
            ask_vol4, pos = get_price(body_buf, pos)

            bid5, pos = get_price(body_buf, pos)
            ask5, pos = get_price(body_buf, pos)
            bid_vol5, pos = get_price(body_buf, pos)
            ask_vol5, pos = get_price(body_buf, pos)

            # (reversed_bytes4, reversed_bytes5, reversed_bytes6,
            #  reversed_bytes7, reversed_bytes8, reversed_bytes9,
            #  active2) = struct.unpack("<HbbbbHH", body_buf[pos: pos + 10])
            # pos += 10

            reversed_bytes4 = struct.unpack("<H", body_buf[pos:pos+2])
            pos += 2
            reversed_bytes5, pos = get_price(body_buf, pos)
            reversed_bytes6, pos = get_price(body_buf, pos)
            reversed_bytes7, pos = get_price(body_buf, pos)
            reversed_bytes8, pos = get_price(body_buf, pos)
            (reversed_bytes9, active2) = struct.unpack(
                "<hH", body_buf[pos: pos + 4])
            pos += 4

            one_stock = OrderedDict([
                ("market", market),
                ("code", code.decode("utf-8")),
                ("active1", active1),
                ("price", self._cal_price(price, 0)),
                ("last_close", self._cal_price(price, last_close_diff)),
                ("open", self._cal_price(price, open_diff)),
                ("high", self._cal_price(price, high_diff)),
                ("low", self._cal_price(price, low_diff)),
                ("servertime", self._format_time('%s' % reversed_bytes0)),
                ("reversed_bytes0", reversed_bytes0),
                ("reversed_bytes1", reversed_bytes1),
                ("vol", vol),
                ("cur_vol", cur_vol),
                ("amount", amount),
                ("s_vol", s_vol),
                ("b_vol", b_vol),
                ("reversed_bytes2", reversed_bytes2),
                ("reversed_bytes3", reversed_bytes3),
                ("bid1", self._cal_price(price, bid1)),
                ("ask1", self._cal_price(price, ask1)),
                ("bid_vol1", bid_vol1),
                ("ask_vol1", ask_vol1),
                ("bid2", self._cal_price(price, bid2)),
                ("ask2", self._cal_price(price, ask2)),
                ("bid_vol2", bid_vol2),
                ("ask_vol2", ask_vol2),
                ("bid3", self._cal_price(price, bid3)),
                ("ask3", self._cal_price(price, ask3)),
                ("bid_vol3", bid_vol3),
                ("ask_vol3", ask_vol3),
                ("bid4", self._cal_price(price, bid4)),
                ("ask4", self._cal_price(price, ask4)),
                ("bid_vol4", bid_vol4),
                ("ask_vol4", ask_vol4),
                ("bid5", self._cal_price(price, bid5)),
                ("ask5", self._cal_price(price, ask5)),
                ("bid_vol5", bid_vol5),
                ("ask_vol5", ask_vol5),
                ("reversed_bytes4", reversed_bytes4),
                ("reversed_bytes5", reversed_bytes5),
                ("reversed_bytes6", reversed_bytes6),
                ("reversed_bytes7", reversed_bytes7),
                ("reversed_bytes8", reversed_bytes8),
                ("reversed_bytes9", reversed_bytes9/100.0),  # 涨速
                ("active2", active2)
            ])
            stocks.append(one_stock)
        return stocks

    def _cal_price(self, base_p, diff):
        return float(base_p + diff)/100

    def _format_time(self, time_stamp):

        time = time_stamp[:-6] + ':'
        if int(time_stamp[-6:-4]) < 60:
            time += '%s:' % time_stamp[-6:-4]
            time += '%06.3f' % (
                int(time_stamp[-4:]) * 60 / 10000.0
            )
        else:
            time += '%02d:' % (
                int(time_stamp[-6:]) * 60 / 1000000
            )
            time += '%06.3f' % (
                (int(time_stamp[-6:]) * 60 % 1000000) * 60 / 1000000.0
            )
        return time

class GetTransactionData(BaseParser):

    def setParams(self, market, code, start, count):
        if type(code) is six.text_type:
            code = code.encode("utf-8")
        pkg = bytearray.fromhex(u'0c 17 08 01 01 01 0e 00 0e 00 c5 0f')
        pkg.extend(struct.pack("<H6sHH", market, code, start, count))
        self.send_pkg = pkg

    def parseResponse(self, body_buf):
        pos = 0
        (num, ) = struct.unpack("<H", body_buf[:2])
        pos += 2
        ticks = []
        last_price = 0
        for i in range(num):
            ### ?? get_time
            # \x80\x03 = 14:56

            hour, minute, pos = get_time(body_buf, pos)

            price_raw, pos = get_price(body_buf, pos)
            vol, pos = get_price(body_buf, pos)
            num, pos = get_price(body_buf, pos)
            buyorsell, pos = get_price(body_buf, pos)
            _, pos = get_price(body_buf, pos)

            last_price = last_price + price_raw

            tick = OrderedDict(
                [
                    ("time", "%02d:%02d" % (hour, minute)),
                    ("price", float(last_price)/100),
                    ("vol", vol),
                    ("num", num),
                    ("buyorsell", buyorsell),
                ]
            )

            ticks.append(tick)

        return ticks

XDXR_CATEGORY_MAPPING = {
    1 : "除权除息",
    2 : "送配股上市",
    3 : "非流通股上市",
    4 : "未知股本变动",
    5 : "股本变化",
    6 : "增发新股",
    7 : "股份回购",
    8 : "增发新股上市",
    9 : "转配股上市",
    10 : "可转债上市",
    11 : "扩缩股",
    12 : "非流通股缩股",
    13 : "送认购权证",
    14 : "送认沽权证"
}

class GetXdXrInfo(BaseParser):

    def setParams(self, market, code):
        if type(code) is six.text_type:
            code = code.encode("utf-8")
        pkg = bytearray.fromhex(u'0c 1f 18 76 00 01 0b 00 0b 00 0f 00 01 00')
        pkg.extend(struct.pack("<B6s", market, code))
        self.send_pkg = pkg

    def parseResponse(self, body_buf):
        pos = 0

        if len(body_buf) < 11:
            return []

        pos += 9 # skip 9
        (num, ) = struct.unpack("<H", body_buf[pos:pos+2])
        pos += 2

        rows = []

        def _get_v(v):
            if v == 0:
                return 0
            else:
                return get_volume(v)

        for i in range(num):
            market, code = struct.unpack(u"<B6s", body_buf[:7])
            pos += 7
            # noused = struct.unpack(u"<B", body_buf[pos: pos+1])
            pos += 1 #skip a byte
            year, month, day, hour, minite, pos = get_datetime(9, body_buf, pos)
            (category, ) = struct.unpack(u"<B", body_buf[pos: pos+1])
            pos += 1



            # b'\x00\xe8\x00G' => 33000.00000
            # b'\x00\xc0\x0fF' => 9200.00000
            # b'\x00@\x83E' => 4200.0000

            suogu = None
            panqianliutong, panhouliutong, qianzongguben, houzongguben = None, None, None, None
            songzhuangu, fenhong, peigu, peigujia = None, None, None, None
            fenshu, xingquanjia = None, None
            if category == 1:
                fenhong, peigujia, songzhuangu, peigu  = struct.unpack("<ffff", body_buf[pos: pos + 16])
            elif category in [11, 12]:
                (_, _, suogu, _) = struct.unpack("<IIfI", body_buf[pos: pos + 16])
            elif category in [13, 14]:
                xingquanjia, _, fenshu, _ = struct.unpack("<fIfI", body_buf[pos: pos + 16])
            else:
                panqianliutong_raw, qianzongguben_raw, panhouliutong_raw, houzongguben_raw = struct.unpack("<IIII", body_buf[pos: pos + 16])
                panqianliutong = _get_v(panqianliutong_raw)
                panhouliutong = _get_v(panhouliutong_raw)
                qianzongguben = _get_v(qianzongguben_raw)
                houzongguben = _get_v(houzongguben_raw)



            pos += 16

            row = OrderedDict(
                [
                    ('year', year),
                    ('month', month),
                    ('day', day),
                    ('category', category),
                    ('name', self.get_category_name(category)),
                    ('fenhong', fenhong),
                    ('peigujia', peigujia),
                    ('songzhuangu', songzhuangu),
                    ('peigu', peigu),
                    ('suogu', suogu),
                    ('panqianliutong', panqianliutong),
                    ('panhouliutong', panhouliutong),
                    ('qianzongguben', qianzongguben),
                    ('houzongguben', houzongguben),
                    ('fenshu', fenshu),
                    ('xingquanjia', xingquanjia)
                ]
            )
            rows.append(row)

        return rows

    def get_category_name(self, category_id):

        if category_id in XDXR_CATEGORY_MAPPING:
            return XDXR_CATEGORY_MAPPING[category_id]
        else:
            return str(category_id)

class GetReportFile(BaseParser):
    def setParams(self, filename, offset=0):
        pkg = bytearray.fromhex(u'0C 12 34 00 00 00')
        # Fom DTGear request.py file
        node_size = 0x7530
        raw_data = struct.pack(r"<H2I100s", 0x06B9,
                               offset, node_size, filename.encode("utf-8"))
        raw_data_len = struct.calcsize(r"<H2I100s")
        pkg.extend(struct.pack(u"<HH{}s".format(raw_data_len),
                               raw_data_len, raw_data_len, raw_data))
        self.send_pkg = pkg

    def parseResponse(self, body_buf):
        (chunksize, ) = struct.unpack("<I", body_buf[:4])

        if chunksize > 0:
            return {
                "chunksize": chunksize,
                "chunkdata":  body_buf[4:]
            }
        else:
            return {
                "chunksize": 0
            }

class SetupCmd1(BaseParser):
    def setup(self):
        self.send_pkg = bytearray.fromhex(u'0c 02 18 93 00 01 03 00 03 00 0d 00 01')

    def parseResponse(self, body_buf):
        return body_buf
class SetupCmd2(BaseParser):
    def setup(self):
        self.send_pkg = bytearray.fromhex(u'0c 02 18 94 00 01 03 00 03 00 0d 00 02')

    def parseResponse(self, body_buf):
        return body_buf
class SetupCmd3(BaseParser):

    def setup(self):
        self.send_pkg = bytearray.fromhex(u'0c 03 18 99 00 01 20 00 20 00 db 0f d5'
                                      u'd0 c9 cc d6 a4 a8 af 00 00 00 8f c2 25'
                                      u'40 13 00 00 d5 00 c9 cc bd f0 d7 ea 00'
                                      u'00 00 02')

    def parseResponse(self, body_buf):
        return body_buf

try:
    # Python 3
    from collections.abc import Iterable
except ImportError:
    # Python 2.7
    from collections import Iterable

if __name__ == '__main__':
    sys.path.append(os.path.dirname(
        os.path.dirname(os.path.realpath(__file__))))


class Jsp_API(BaseSocketClient):

    def setup(self):
        SetupCmd1(self.client).call_api()
        SetupCmd2(self.client).call_api()
        SetupCmd3(self.client).call_api()

    # API List

    # Notice：，如果一个股票当天停牌，那天的K线还是能取到，成交量为0
    @update_last_ack_time
    def get_security_bars(self, category, market, code, start, count):
        cmd = GetSecurityBarsCmd(self.client, lock=self.lock)
        cmd.setParams(category, market, code, start, count)
        return cmd.call_api()

    @update_last_ack_time
    def get_index_bars(self, category, market, code, start, count):
        cmd = GetIndexBarsCmd(self.client, lock=self.lock)
        cmd.setParams(category, market, code, start, count)
        return cmd.call_api()

    @update_last_ack_time
    def get_security_quotes(self, all_stock, code=None):
        """
        支持三种形式的参数
        get_security_quotes(market, code )
        get_security_quotes((market, code))
        get_security_quotes([(market1, code1), (market2, code2)] )
        :param all_stock （market, code) 的数组
        :param code{optional} code to query
        :return:
        """

        if code is not None:
            all_stock = [(all_stock, code)]
        elif (isinstance(all_stock, list) or isinstance(all_stock, tuple))\
                and len(all_stock) == 2 and type(all_stock[0]) is int:
            all_stock = [all_stock]

        cmd = GetSecurityQuotesCmd(self.client, lock=self.lock)
        cmd.setParams(all_stock)
        return cmd.call_api()

    @update_last_ack_time
    def get_security_count(self, market):
        cmd = GetSecurityCountCmd(self.client, lock=self.lock)
        cmd.setParams(market)
        return cmd.call_api()

    @update_last_ack_time
    def get_security_list(self, market, start):
        cmd = GetSecurityList(self.client, lock=self.lock)
        cmd.setParams(market, start)
        return cmd.call_api()

    @update_last_ack_time
    def get_minute_time_data(self, market, code):
        cmd = GetMinuteTimeData(self.client, lock=self.lock)
        cmd.setParams(market, code)
        return cmd.call_api()

    @update_last_ack_time
    def get_history_minute_time_data(self, market, code, date):
        cmd = GetHistoryMinuteTimeData(self.client, lock=self.lock)
        cmd.setParams(market, code, date)
        return cmd.call_api()

    @update_last_ack_time
    def get_transaction_data(self, market, code, start, count):
        cmd = GetTransactionData(self.client, lock=self.lock)
        cmd.setParams(market, code, start, count)
        return cmd.call_api()

    @update_last_ack_time
    def get_history_transaction_data(self, market, code, start, count, date):
        cmd = GetHistoryTransactionData(self.client, lock=self.lock)
        cmd.setParams(market, code, start, count, date)
        return cmd.call_api()

    @update_last_ack_time
    def get_company_info_category(self, market, code):
        cmd = GetCompanyInfoCategory(self.client, lock=self.lock)
        cmd.setParams(market, code)
        return cmd.call_api()

    @update_last_ack_time
    def get_company_info_content(self, market, code, filename, start, length):
        cmd = GetCompanyInfoContent(self.client, lock=self.lock)
        cmd.setParams(market, code, filename, start, length)
        return cmd.call_api()

    @update_last_ack_time
    def get_xdxr_info(self, market, code):
        cmd = GetXdXrInfo(self.client, lock=self.lock)
        cmd.setParams(market, code)
        return cmd.call_api()

    @update_last_ack_time
    def get_finance_info(self, market, code):
        cmd = GetFinanceInfo(self.client, lock=self.lock)
        cmd.setParams(market, code)
        return cmd.call_api()

    @update_last_ack_time
    def get_block_info_meta(self, blockfile):
        cmd = GetBlockInfoMeta(self.client, lock=self.lock)
        cmd.setParams(blockfile)
        return cmd.call_api()

    @update_last_ack_time
    def get_block_info(self, blockfile, start, size):
        cmd = GetBlockInfo(self.client, lock=self.lock)
        cmd.setParams(blockfile, start, size)
        return cmd.call_api()

    def get_and_parse_block_info(self, blockfile):
        return get_and_parse_block_info(self, blockfile)

    @update_last_ack_time
    def get_report_file(self, filename, offset):
        cmd = GetReportFile(self.client, lock=self.lock)
        cmd.setParams(filename, offset)
        return cmd.call_api()

    def get_report_file_by_size(self, filename, filesize=0, reporthook=None):
        """
        Download file from proxy server

        :param filename the filename to download
        :param filesize the filesize to download , if you do not known the actually filesize, leave this value 0
        """
        filecontent = bytearray(filesize)
        current_downloaded_size = 0
        get_zero_length_package_times = 0
        while current_downloaded_size < filesize or filesize == 0:
            response = self.get_report_file(filename, current_downloaded_size)
            if response["chunksize"] > 0:
                current_downloaded_size = current_downloaded_size + \
                    response["chunksize"]
                filecontent.extend(response["chunkdata"])
                if reporthook is not None:
                    reporthook(current_downloaded_size,filesize)
            else:
                get_zero_length_package_times = get_zero_length_package_times + 1
                if filesize == 0:
                    break
                elif get_zero_length_package_times > 2:
                    break

        return filecontent

    def do_heartbeat(self):
        self.get_security_count(random.randint(0, 1))

    def get_k_data(self, code, start_date, end_date):
        def __select_market_code(code):
            code = str(code)
            if code[0] in ['5', '6', '9'] or code[:3] in ["009", "126", "110", "201", "202", "203", "204"]:
                return 1
            return 0

        market_code = 1 if str(code)[0] == '6' else 0
        # 0 - 深圳， 1 - 上海

        data = pd.concat([self.to_df(self.get_security_bars(9, __select_market_code(
            code), code, (9 - i) * 800, 800)) for i in range(10)], axis=0)

        data = data.assign(date=data['datetime'].apply(lambda x: str(x)[0:10])).assign(code=str(code))\
            .set_index('date', drop=False, inplace=False)\
            .drop(['year', 'month', 'day', 'hour', 'minute', 'datetime'], axis=1)[start_date:end_date]
        return data.assign(date=data['date'].apply(lambda x: str(x)[0:10]))





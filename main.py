import json

import requests
import re
import time
import os

HistoryHeaderFormat = {
    'Host': 'www.tourrun.net',
    'Connection': 'keep-alive',
    'Content-Length': '131',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Origin': 'http://www.tourrun.net',
    'X-Requested-With': 'XMLHttpRequest',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36',
    'Content-Type': 'application/json',
    'Referer': 'http://www.tourrun.net/Playback.aspx?id=128149&deviceid=327627',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Cookie': 'ASP.NET_SessionId=d423qwwmpjoikllvuiiibjoc; 49BAC005-7D5B-4231-8CEA-16939BEACD67=name=%s&password=%s&logintype=0; suid=8846706000; K3HC03HNX0N-LL34L3Z03P-23KNGF394-DLJ32L=CurrentUserID=128149'

}

# HistoryData = '''{DeviceID:327627,Start:'2018-01-01 00:00',End:'2018-01-01 00:10',TimeZone:'China Standard Time',ShowLBS:0,lastLocationID:201806313}'''
HistoryDataFormat = '''{DeviceID:327627,Start:'%s',End:'%s',TimeZone:'China Standard Time',ShowLBS:0,lastLocationID:201806313}'''
RequestTimeFormat = '%Y-%m-%d %H:%M:%S'
ResponseTimeFormat = '%Y/%m/%d %H:%M:%S'
LastDataFormat = '%m/%d/%Y %H:%M:%S'
EndTime = '1900/1/1 0:00:01'


def getDevicesHistory(header, data):
    '''
    下载历史轨迹，
    :param header:
    :param data:
    :return:
    '''
    response = requests.post('http://www.tourrun.net/Ajax/DevicesAjax.asmx/GetDevicesHistory', headers=header,
                             data=data)

    if response.status_code != 200:
        print(response.status_code)
        return response.status_code,

    s = response.text[6:-2]
    l = re.findall('[\,\{](.*?)[\:]', s)
    # print(l)

    s = re.sub('(?P<value>[\,\{].*?[\:])', replace, s)
    s = re.sub('(?P<value>\:[0-9]+\,)', replace, s)
    s = re.sub('(\\\\\")', '"', s)

    # print(s)
    j = json.loads(s)
    # print(j)

    # 整理数据，转成符合GPS导入的格式：
    # "'oLng','oLat','deviceUtcDate','serverUtcTime','speed','course','dataType','IsStop','distance','stopTimeMinute','stopTimeString','longitude','latitude','baiduLng','baiduLat'"
    # 写入文件中
    count = 0
    with open(r'e:/track-all_2.txt', 'ab+') as f:
        for js in j['devices']:
            l = []
            # print(js['deviceUtcDate'])
            js['deviceUtcDate'] = str(time.mktime(time.strptime(js['deviceUtcDate'], ResponseTimeFormat)))
            js['serverUtcTime'] = str(time.mktime(time.strptime(js['serverUtcTime'], ResponseTimeFormat)))
            l.append(js['oLng'])
            l.append(js['oLat'])
            l.append(js['deviceUtcDate'])
            l.append(js['serverUtcTime'])
            l.append(js['speed'])
            l.append(js['course'])
            l.append(js['dataType'])
            l.append(js['IsStop'])
            l.append(js['distance'])
            l.append(js['stopTimeMinute'])
            l.append(js['stopTimeString'])
            l.append(js['longitude'])
            l.append(js['latitude'])
            l.append(js['baiduLng'])
            l.append(js['baiduLat'])
            s = ' '.join(l)

            f.write(bytes(s, encoding="utf8"))
            f.write(bytes(os.linesep, encoding="utf8"))
            f.flush()
            count += 1

    return response.status_code, len(j['devices']), j['lastDeviceUtcDate']


def inputTime(hint):
    t = input(hint)
    matchObj = re.match('^[0-9]{4}-[0-1][0-9]-[0-3][0-9]\s[0-2][0-9]:[0-5][0-9]$', t)
    if not matchObj:
        print('格式不对！！！')
        return inputTime(hint)
    else:
        print(matchObj.group())
        return t


def replace(matched):
    s = matched.group('value')
    if s[1] == ',' or s[1] == '{' or s[1] == ' ':
        s = s[:2] + '"' + s[2:-1] + '"' + s[-1]
    else:
        s = s[0] + '"' + s[1:-1] + '"' + s[-1]
    return s


def main(start, end, name, pwd):
    if '' == end:
        end = time.strftime(RequestTimeFormat, time.localtime())

    log = open(r'e:/log.log', "a+")

    requestTime = start

    requestHeader = HistoryHeaderFormat
    requestHeader['Cookie'] = HistoryHeaderFormat['Cookie'] % (name, pwd)

    logList = []
    while True:
        data = HistoryDataFormat % (requestTime, end)
        logList.append(data)
        print(data)
        result = getDevicesHistory(requestHeader, data)
        if 200 != result[0]:
            print("下载失败，重试")
            time.sleep(5)
            continue

        logList.extend(result)
        for s in logList:
            log.write(str(s) + '\n')
        log.flush()
        logList.clear()
        # log.write(bytes(str(result[0]), encoding='utf8'))
        # log.write(bytes(os.linesep, encoding="utf8"))
        # log.write(bytes(str(result[1]), encoding='utf8'))
        # log.write(bytes(os.linesep, encoding="utf8"))
        if result[1] != 0 and result[2] != EndTime:
            lastDeviceUtcDateL = time.mktime(time.strptime(result[2], ResponseTimeFormat))
            requestTime = time.strftime(RequestTimeFormat, time.localtime(lastDeviceUtcDateL))
        else:
            break

    log.close()


if __name__ == '__main__':
    # 准备时间区间，分段下载。时间区间为输入时间，格式为：2018-01-01 20:20，无目标时间时为当前时间
    start = inputTime('输入要下载轨迹的开始时间（格式：2018-01-01 20:20）：')
    end = inputTime('输入要下载轨迹的结束时间（格式：2018-01-01 20:20）：')
    name = input('输入用户名：')
    pwd = input('输入密码：')

    main(start=start, end=end, name=name, pwd=pwd)
    # html = requests.post('http://www.tourrun.net/Playback.aspx?id=128149&deviceid=327627', headers=RequestHeader,
    #                      data=FormData)
    # if html.status_code != 200:
    #     print(html.status_code)
    # s = html.text
    # print(html.encoding)
    # print(s)

    # l = re.findall('\[([^\[\]].*?)\]', s, re.S)
    # for ll in l:
    #     tl = re.findall('\"(.*?)\"', ll, re.S)
    #     for t in tl:
    #         print(t)

    # t = getDevicesHistory()

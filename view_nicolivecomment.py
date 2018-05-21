# -*- coding: utf-8 -*-
import urllib, urllib3, http.cookiejar as cookielib, socket, re
from xml.etree import ElementTree
from urllib.request import build_opener, HTTPCookieProcessor
import asyncio
import keypresser

lv = ""

# クラスを定義
class NicoliveCommentReceiver:
    #　のちにクラスを呼び出す際に「無条件で最初に呼び出す」関数
    def __init__(self):
        self.LOGIN_URL = 'https://secure.nicovideo.jp/secure/login?site=niconico'
        self.LIVE_API_URL = 'http://watch.live.nicovideo.jp/api/'
        self.cookies = cookielib.CookieJar()
        cjhdr = urllib.request.HTTPCookieProcessor(self.cookies)
        self.opener = build_opener(cjhdr)

    #　かっこの中身は引数と覚えること
    def login(self, mail, password):
        if mail == 'user_session':
            self.set_user_session(password)
            #############################
            #############################
            #############################
            ###　Pythonでは戻り値の型は自由 ###
            #############################
            #############################
            #############################
            return True
        values = {'mail_tel' : mail, 'password' : password}
        postdata = urllib.parse.urlencode(values)
        response = self.opener.open(self.LOGIN_URL, postdata.encode("utf-8"))
        page = response.read()
        for c in self.cookies:
            if c.name == 'user_session': return c.value
        return None

    def set_user_session(self, user_session):
        self.opener.addheaders.append(('Cookie', 'user_session=' + user_session))
        
    def get_lv(self):
        self.community_URL = 'http://com.nicovideo.jp/community/co3097203'
        html = urllib.request.urlopen(self.community_URL).read().decode('utf-8')
        ### re.matchでhtmlの中から「"watch/lv"+数列」という箇所を探し出して
        ###　group(1)で一番目のグループであるカッコ内、つまり"[0-9]+"の部分をlvに代入。
        ### group(0)だと「"watch/lv"+数列」が丸ごとlvに代入される。
        m = re.search('watch/(lv[0-9]+)',html)
        if m is None:
            return None
        else:
            return m.group(1)
        
        

    ### 引数に関数を指定することもできる cbfnc とはおそらく「コールバックファンクション」の略
    ###　cbfnc = none はデフォルト引数という記述の仕方で、今回のケースでは86行目で
    ### on_commentという関数(106行目)を指定しているのでnoneで上書きはされない。



                ### ここから先は3局共通の処理になるため
                ### コメント文だけをエントリポイントのあるファイルへ渡して、キーボード変換処理はこちらではしない。
                # initial = comment[0]
                # second = comment[-1]
                # enabled_command = ["a","b","x","y","u","d","l","r"]
                # enabled_second = ["1","2","3","4","5","6","7","8","9"]
                # if initial in enabled_command:
                # ###if initial != "a" and initial != "b" and initial != "x" and initial != "y" and initial != "u" and initial != "d" and initial != "l" and initial != "r":
                #     waitsecond = 0.5
                #     if second in enabled_second:
                #         waitsecond = int(second)
                #     print(comment)
                #     print("コマンドです")
                #     global runtasks
                #     if runtasks <= 2:
                #         print("タスクは3以下でした。")
                #         key = int(KEYDICT[initial],0)
                #         if key in tasks:
                #             print (key)
                #             if not tasks[key].done():
                #                 tasks[key].cancel()
                #                 runtasks -= 1
                #                 print("tasks[key].cancel()発動、runtasks = " + str(runtasks))
                #         task = asyncio.ensure_future(key_press_async(key,waitsecond))
                #         tasks[key] = task
                #     else:
                #         print("タスクが3つあるので入力をキャンセルしました。" + str(runtasks))
                # else:
                #     print(comment)
                #     continue
    async def get_comment(self,lv,KEYDICT):
        ### 指定したURLから投げられてくるxmlファイルを.readでstring型にしている。
        player_status_xml = self.opener.open(self.LIVE_API_URL + 'getplayerstatus?v=' + lv).read()
        ###　Elementtree.fromstringで44行目で生成したstring型をElement型に変換している。
        player_status = ElementTree.fromstring(player_status_xml)
        ###　Element型では要素名を探し出すfind関数が使える。
        ###　ニコ生から送られてきたxmlを変換したElement型の中にはあらかじめtextとタグづけられた名付けられた変数が用意されている。
        ###　player_statusから"ms/hogehoge"という要素を見つけて(find関数)
        ###　textと名付けられた変数に代入されいてるstringをさらに変数(addrやport、thread)へ代入している。
        addr = player_status.find("ms/addr").text
        port = int(player_status.find("ms/port").text)
        thread = player_status.find("ms/thread").text

        ###　コメントサーバーと通信するための準備
        ###(socket.AF_INET, socket.SOCK_STREAM)はニコ生仕様。
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ###　44行目で拾ってきたaddrやportを使ってコメントサーバーに接続。
        sock.connect((addr, port))
        sock.setblocking(False)
        ###　コメントデータをこちらに送るように要求するデータをこちらから送信している。
        sock.send(bytes('<thread thread="{thread}" version="20061206" res_from="-1"/>\0'.format(thread=thread),"utf-8"))

        data = ''
        tasks = {}
        ###　関数内で戻り値を特別に指定しない限りは初期値としてtrueであり続ける。
        while True:
            ###\0というのはnull文字、null文字が見つからなかったら
            while data.find("\0") == -1:
                ###null文字が出現するまで1024バイトずつデータを取得している
                event_loop = asyncio.get_event_loop()
                byetsdata = await event_loop.sock_recv(sock,1024)
                data += byetsdata.decode('utf-8')
            ###　pはインデックスの番号、整数のはず。
            p = data.find("\0")
            d = ElementTree.fromstring(data[:p])
            data = data[p+1:]
            if d.tag == 'chat':
                num = int(d.get('no') or "-1")
                pre = int(d.get('premium') or "-1")
                vpos = int(d.get('vpos') or "-1")
                mail = d.get('mail')
                user_id = d.get('user_id')
                comment = d.text
                ### breakはループを抜け出す
                if comment == u"/disconnect" and pre == 2 : break
                ###　continueとはループの先頭(65行目)に戻る
                if comment.startswith('/'): continue
                initial = comment[0]
                second = comment[-1]
                enabled_command = ["a", "b", "x", "y", "u", "d", "l", "r"]
                enabled_second = ["1", "2", "3", "4", "5", "6", "7", "8", "9"]
                if initial in enabled_command:
                    initial = 'n' + initial
                    waitsecond = 0.5
                    if second in enabled_second:
                        waitsecond = int(second)
                    print(comment)
                    print(initial)
                    print("コマンドです")
                    key = int(KEYDICT[initial], 0)
                    keypress_convert(key,waitsecond,KEYDICT)
                else:
                    print(comment)

if __name__ == "__main__":
    import os
    import json
    import time


    config_json_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'config.json')
    keyditc_json_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'keydict.json')
    CONFIG = json.load(open(config_json_path))
    KEYDICT = json.load(open(keyditc_json_path))

    email = CONFIG['nico_mail']
    password = CONFIG['nico_password']


    event_loop = asyncio.get_event_loop()
    keypress_convert = keypresser.keypress_convert
    receiver = NicoliveCommentReceiver()
    #get_comment = receiver.get_comment()
    receiver.login(email, password)


    while True:
        while True:
            lv = receiver.get_lv()
            if lv is not None: break
            print("放送URLに接続失敗、15秒後に再接続します。")
            time.sleep(15)
        print("放送URLに接続、コメント取得を開始します。")
        event_loop.run_until_complete(receiver.get_comment(lv,KEYDICT))
        
        
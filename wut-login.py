"""
 Copyright 2023 lxidea @https://github.com/lxidea

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

      https://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
 """

# -*- coding: utf-8 -*-
"""
@author: Xin Lai
usage: put your password and WUT accountID assigned to the variables below,
default online status checking interval is 600 seconds.
To use this python script, you will need python3, and packages: json, requests
"""
#-*- coding:utf-8 -*-
userid = ''
passwd = ''
interval = 600

__author__ = 'lxidea'
import time
import requests
import re
import json
import sys
from requests.cookies import RequestsCookieJar
from requests.exceptions import ConnectTimeout

class Login(object):
     """login class in charge of keep your device online on WUT campus"""
     def __init__(self):
          super(Login).__init__()
          self.interval = interval
          self.online = None
          self.network = None
          self.cookies = requests.cookies.RequestsCookieJar()
          self.host_url = ''
          self.host = '172.30.21.100'
          self.staturl = '/account/status'
          self.info = None
          self.loginfo = None
          self.__version__ = 'v0.1'
          self.loglevel = 0
          self.shown = False

     def getCurrentTime(self):
          return time.strftime('[%Y-%m-%d %H:%M:%S]',time.localtime(time.time()))

     def showLine(self,msg,length=0,char=None):
          msg = msg.strip()
          if type(msg) is not str:
               msg = str(msg)
          if not char:
               char = '*'
          if length<=0:
               length=30
          strlen=len(msg)
          if strlen>length:
               raise(Exception('msg is too long'))
          charlen = length - strlen
          charlen2 = int(charlen/2)
          if charlen2*2!=charlen:
               charlen2=charlen2-1
          for x in range(charlen2):
               print(char,end='')
          print(msg,end='')
          if charlen2*2!=charlen:
               print(' ',end='')
          for x in range(charlen2):
               print(char,end='')
          print('')

     def showLoginfo(self):
          if not self.loginfo:
               print(self.getCurrentTime()+' not login yet.')
               return
          self.showLine('First Appear Time:'+self.loginfo['AddTime'],50)
          self.showLine('User Name:'+self.loginfo['Name'],50)
          self.showLine('Network Address:'+self.loginfo['UserIpv4'],50)
          self.showLine('Mac Address:'+self.loginfo['UserMac'],50)
          self.showLine('UserSourceType:'+self.loginfo['UserSourceType'],50)
          self.showLine('UserId:'+self.loginfo['Username'],50)

     def check(self):
          url = "http://"+self.host+"/tpl/whut/login.html?nasId=14"
          headers={
            'Host': self.host,
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            'Referer': "http://"+self.host+"/",
            'Accept-Encoding': "gzip, deflate",
            'Accept-Language': "en-US,en;q=0.5",
            'Connection': "keep-alive",
            'Upgrade-Insecure-Requests': "1",
            'User-Agent':"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/110.0"
          }
          self.data = None
          if self.loglevel>0:
               print(self.getCurrentTime()+'First Handshake...',end='')
          sys.stdout.flush()
          try:
               self.data = requests.get(url,headers=headers,cookies=self.cookies,timeout=5)
               self.cookies.update(self.data.cookies)
          except ConnectTimeout as c:
               print('\n'+self.getCurrentTime()+'TimeOut when trying to connect to portal')
               print('maybe you are off campus')
               self.network = False
               self.online = False
               return
          except Exception as e:
               print('\n'+self.getCurrentTime()+'Error:'+str(e))
               self.network = False
               self.online = False
               return
          if self.data.status_code == 200:
               if self.loglevel>0:
                    print('OK')
                    sys.stdout.flush()
               self.network = True
          url = "http://"+self.host+"/tpl/whut/static/js/config.js"
          headers={
            'Host': self.host,
            'Accept': "*/*",
            'Referer': "http://"+self.host+"/tpl/whut/login.html?nasId=14",
            'Accept-Encoding': "gzip, deflate",
            'Accept-Language': "en-US,en;q=0.5",
            'Connection': "keep-alive",
            'User-Agent':"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/110.0"
          }
          self.data = None
          if self.loglevel>0:
               print(self.getCurrentTime()+'get conn path...',end='')
               sys.stdout.flush()
          try:
               self.data = requests.get(url,headers=headers,cookies=self.cookies,timeout=5)
               self.cookies.update(self.data.cookies)
               raw_text = self.data.text
               if self.data.status_code == 200:
                    if self.loglevel>0:
                         print('OK')
                         sys.stdout.flush()
                    self.network = True
               for line in raw_text.split('\n'):
                    if not (line.startswith('//') or len(line.strip())==0):
                         sline = [x.strip() for x in line.strip().replace('var','').strip().split('=')]
                         execstr = 'self.'+sline[0]+'='+sline[1]
                         #print('setting '+sline[0]+' to '+sline[1])
                         exec(execstr)
          except Exception as e:
               print(self.getCurrentTime()+'Error:'+str(e))
               self.network = False
               self.online = False
          url = 'http://'+self.host+self.host_url+self.staturl+'?token=null'
          headers={
            'Host': self.host,
            'Accept': "*/*",
            'Referer': "http://"+self.host+"/tpl/whut/login.html?nasId=14",
            'Accept-Encoding': "gzip, deflate",
            'Accept-Language': "en-US,en;q=0.5",
            'Connection': "keep-alive",
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/110.0",
            'X-Requested-With': "XMLHttpRequest"
          }
          data={
            'token': "null"
          }
          self.data = None
          print(self.getCurrentTime()+' get online status...',end='')
          sys.stdout.flush()
          try:
               self.data = requests.get(url,headers=headers,cookies=self.cookies,timeout=5)
               self.cookies.update(self.data.cookies)
               if self.data.status_code == 200:
                    print('OK')
                    sys.stdout.flush()
                    self.network = True
                    try:
                         self.info = json.loads(self.data.text)
                         self.online = self.info['code']==0
                         self.loginfo = self.info['online']
                         if self.loglevel>0 and not self.shown:
                              self.showLoginfo()
                              self.shown = True
                    except Exception as e:
                         if self.loglevel>0:
                              print(self.getCurrentTime()+'Error:'+str(e))
                         self.json = None
                         print(self.getCurrentTime()+' Account Status Fetching Failure.')
                         self.online = False
                         return
          except Exception as e:
               print(self.getCurrentTime()+'Error:'+str(e))
               self.network = False
               self.online = False

     def login(self):
          url='http://'+self.host+self.host_url+'/account/login'
          logindata={
          'username':userid,
          'password':passwd,
          'swtichip': '',
          'nasId': "14",
          'userIpv4': "",
          'userMac': "",
          'captcha': '',
          'captchaId': '',
          }
          # code 0: success, 1 error, 2 code wrong
          headers={
            'Host': self.host,
            'Accept': "*/*",
            'Referer': "http://"+self.host+"/tpl/whut/login.html?nasId=14",
            'Accept-Encoding': "gzip, deflate",
            'Accept-Language': "en-US,en;q=0.5",
            'Connection': "keep-alive",
            'Content-Length': '94',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'http://'+self.host,
            'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/110.0",
            'X-Requested-With': "XMLHttpRequest"
          }
          if self.loglevel>0:
               print(self.getCurrentTime()+' try login...',end='')
               sys.stdout.flush()
          try:
               self.data = requests.post(url,headers=headers,data=logindata,cookies=self.cookies,timeout=5)
               self.cookies.update(self.data.cookies)
               if self.data.status_code == 200:
                    if self.loglevel>0:
                         print('OK')
                         sys.stdout.flush()
                    self.network = True
                    print(self.getCurrentTime()+' success, now we\'re online')
                    #try:
                    self.info = json.loads(self.data.text)
                    self.online = self.info['code']
                    self.loginfo = self.info['online']
                    if self.loglevel>0 and not self.shown:
                         self.showLoginfo()
                         self.shown = True
                    #except Exception as e:
                    #     raise e
                    
          except Exception as e:
               raise e
     
     def run(self):
          print(self.getCurrentTime()+' WUT Network Online Status Keeper '+self.__version__)
          print(self.getCurrentTime()+' written by '+__author__)
          while True:
               self.check()
               if not self.online:
                    print(self.getCurrentTime()+' offline, try login')
                    self.login()
                    #try:
                    #     self.login()
                    #except Exception as e:
                    #     print(self.getCurrentTime()+' Error:'+str(e))
               else:
                    print(self.getCurrentTime()+' we\'re good, sleep for '+str(self.interval)+' seconds')
               time.sleep(self.interval)
if __name__ == '__main__':
     login = Login()
     login.run()
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
# -*- coding:utf-8 -*-

import time
import requests
import os
import json
import sys
import re
from requests.cookies import RequestsCookieJar
from requests.exceptions import ConnectTimeout
from urllib.parse import urlparse, parse_qs

userid = os.getenv("WUT_USERID", "")  # Read from environment variable by default
passwd = os.getenv("WUT_PASSWD", "")
interval = int(os.getenv("CHECK_INTERVAL", 600))  # Default interval is 600 seconds
log_level = int(os.getenv("LOG_LEVEL", 1))  # Default log level is 1 (verbose logs)

__author__ = "lxidea"
__refactorer__ = "somebottle"

# Match comments in JavaScript
PATTERN_COMMENTS = re.compile(r"//.*?\n|/\*.*?\*/", re.DOTALL)
# Match API base path in 'tpl/whut/static/js/config.js'
PATTERN_API_BASE_PATH = re.compile(r"host_url\s*=\s*['\"](.*?)['\"]")
# Domain used to follow the redirect to get the host and nasId
TEST_DOMAIN = "neverssl.com"

# Should bypass the proxy
os.environ["NO_PROXY"] = ",".join(os.getenv("NO_PROXY", "").split(",") + [TEST_DOMAIN])
os.environ["no_proxy"] = ",".join(os.getenv("no_proxy", "").split(",") + [TEST_DOMAIN])


class SimplePrinter(object):
    """
    Simple printer class to print messages with different log levels
    """

    def __init__(self, log_level=0):
        """
        Init the SimplePrinter class

        :param log_level: Log level, if greater than 0, will show more logs
        """
        self.log_level = log_level

    def get_current_time(self):
        return time.strftime("[%Y-%m-%d %H:%M:%S]", time.localtime(time.time()))

    def verbose(self, msg, end="\n", with_time=True, flush=True, prepend_str=""):
        """
        Print verbose messages if log level is greater than 0

        :param msg: Message to print
        :param end: End character for the print function
        :param with_time: Whether to prepend the current time to the message
        :param flush: Whether to flush the output immediately
        :param prepend_str: String to prepend to the output string (before the time string)
        """
        if self.log_level > 0:
            if with_time:
                msg = self.get_current_time() + " " + msg
            msg = prepend_str + msg
            print(msg, end=end)
            if flush:
                sys.stdout.flush()

    def info(self, msg, end="\n", with_time=True, flush=True, prepend_str=""):
        """
        Print info messages

        :param msg: Message to print
        :param end: End character for the print function
        :param with_time: Whether to prepend the current time to the message
        :param flush: Whether to flush the output immediately
        :param prepend_str: String to prepend to the output string (before the time string)
        """
        if with_time:
            msg = self.get_current_time() + " " + msg
        msg = prepend_str + msg
        print(msg, end=end)
        if flush:
            sys.stdout.flush()

    def n_verbose(self, *args, **kwargs):
        """
        Alias for verbose method with a newline prepended
        """
        self.verbose(*args, prepend_str="\n", **kwargs)

    def n_info(self, *args, **kwargs):
        """
        Alias for info method with a newline prepended
        """
        self.info(*args, prepend_str="\n", **kwargs)


class Login(object):
    """login class in charge of keep your device online on WUT campus"""

    def __init__(self, userid, passwd, interval=600, log_level=0):
        """
        Init the Login class

        :param userid: WUT account ID
        :param passwd: WUT account password
        :param interval: Interval for checking online status in seconds
        :param log_level: Log level, if greater than 0, will show more logs
        """
        super(Login).__init__()
        self.userid = userid
        self.passwd = passwd
        self.interval = interval
        self.nas_id = "14"  # NAS ID for WUT Campus Network, will be updated by 'fetch_host_and_nas_id'
        self.online = None
        self.network = None
        self.cookies = RequestsCookieJar()
        self.api_base_path = "/api"  # API Base Path, will be updated by 'check'
        self.csrf_token = ""  # CSRF token, will be updated by 'fetch_csrf_token'
        self.host = "172.30.21.100"  # Host of WUT Campus Network Portal, will be updated by 'fetch_host_and_nas_id'
        self.status_endpoint = "/account/status"
        self.info = None
        self.login_info = None
        self.log_printer = SimplePrinter(log_level)
        self.log_level = log_level
        self.shown = False  # Only show login info once during the session
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36 Edg/97.0.1072.71"
        self.__version__ = "v0.3"

    def fetch_host_and_nas_id(self, max_iters=10):
        """
        Follow the redirect to fetch the host and NAS ID from the WUT portal.

        :param max_iters: Maximum number of iterations to follow redirects
        """
        if self.online:
            return
        test_url = (
            "http://" + TEST_DOMAIN
        )  # A URL that won't redirect if the network is available
        next_url = test_url
        portal_url = ""
        self.log_printer.verbose(
            "Trying to get host and nasId from WUT portal...",
            end="",
        )
        for _ in range(max_iters):
            try:
                response = requests.get(
                    next_url, allow_redirects=False, timeout=30, proxies={}
                )
            except Exception as e:
                self.log_printer.verbose("Failed", with_time=False)
                self.log_printer.verbose("Error:" + str(e))
                self.log_printer.info(
                    "If you are using TUN-based proxy (via virtual NIC), try to disable it"
                )
                self.log_printer.info(
                    "如果你在使用基于 TUN (虚拟网卡) 的代理，请将其关闭"
                )
                return
            if 300 <= response.status_code < 400:
                next_location = response.headers.get("Location", "")
                if next_location:
                    portal_url = next_location
                    next_url = next_location
                else:
                    self.log_printer.verbose("Failed", with_time=False)
                    self.log_printer.verbose(
                        "Status code: "
                        + str(response.status_code)
                        + ", but no Location header found, this is unexpected!"
                    )
                    return
            elif response.status_code >= 400:
                self.log_printer.verbose("Failed", with_time=False)
                self.log_printer.verbose(
                    "Status code: "
                    + str(response.status_code)
                    + " while getting host and nasId, this is unexpected!"
                )
                return
            else:
                # Status 200
                break

        if portal_url:
            parsed_url = urlparse(portal_url)
            self.host = parsed_url.netloc
            params = parse_qs(parsed_url.query)
            if "nasId" in params:
                self.nas_id = params["nasId"][0]
                self.log_printer.verbose(
                    "OK, nasId: " + self.nas_id + ", host: " + self.host,
                    with_time=False,
                )
            else:
                self.log_printer.verbose("Failed", with_time=False)
                self.log_printer.verbose("No nasId found in the redirected URL!")
                return
        else:
            self.log_printer.verbose("Failed", with_time=False)
            self.log_printer.verbose(
                "No redirect found, this is unexpected! Maybe you are already online."
            )
            return

    def fetch_csrf_token(self):
        """
        Fetch the CSRF token from the WUT portal
        """
        url = "http://" + self.host + self.api_base_path + "/csrf-token"
        headers = {
            "Host": self.host,
            "Accept": "*/*",
            "Referer": "http://"
            + self.host
            + "/tpl/whut/login.html?nasId="
            + self.nas_id,
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.5",
            "User-Agent": self.user_agent,
        }
        self.log_printer.verbose("Fetching CSRF Token...", end="")
        success_flag = False
        try:
            response = requests.get(
                url, headers=headers, cookies=self.cookies, timeout=5
            )
            if response.status_code == 200:
                try:
                    # data = {"csrf_token":"DBACebkckr_qMgLHdb9by2WExWk="}
                    self.csrf_token = json.loads(response.text)["csrf_token"]
                    # Should update cookies here, the csrf token is related to the session
                    self.cookies.update(response.cookies)
                    self.log_printer.verbose("OK", with_time=False)
                    self.log_printer.verbose(
                        "CSRF Token fetched successfully: " + self.csrf_token
                    )
                    success_flag = True
                except Exception as exc:
                    self.log_printer.n_verbose("Error: " + str(exc))
            else:
                self.log_printer.n_verbose(
                    "Failed to fetch CSRF token, status code: "
                    + str(response.status_code)
                    + ", raw response: "
                    + response.text
                )
        except Exception as e:
            self.log_printer.n_verbose("Error fetching CSRF token:", str(e))

        if not success_flag:
            self.csrf_token = ""  # Reset CSRF token if fetching failed

    def show_line(self, msg, length=0, char=None):
        """
        Show a center-aligned message with padding characters.

        :param msg: The message to display
        :param length: The total length of the line
        :param char: The character to use for padding
        """
        msg = msg.strip()
        if type(msg) is not str:
            msg = str(msg)
        if not char:
            char = "*"
        if length <= 0:
            length = 30
        strlen = len(msg)
        if strlen > length:
            print(msg)
            return
        charlen = length - strlen
        charlen2 = int(charlen / 2)
        if charlen2 * 2 != charlen:
            charlen2 = charlen2 - 1
        for x in range(charlen2):
            print(char, end="")
        print(msg, end="")
        if charlen2 * 2 != charlen:
            print(" ", end="")
        for x in range(charlen2):
            print(char, end="")
        print("")

    def show_login_info(self):
        """
        Display the login information of the user.
        """
        if not self.login_info:
            self.log_printer.info("User not logged in yet")
            return
        print()
        self.show_line("Login Information", 50, "#")
        self.show_line("First Appear Time:" + self.login_info["AddTime"], 50)
        self.show_line("User Name:" + self.login_info["Name"], 50)
        self.show_line("Network Address:" + self.login_info["UserIpv4"], 50)
        self.show_line("Mac Address:" + self.login_info["UserMac"], 50)
        self.show_line("UserSourceType:" + self.login_info["UserSourceType"], 50)
        self.show_line("UserId:" + self.login_info["Username"], 50)
        print()

    def check(self):
        """
        Check the online status of the user and update necessary information

        1. Perform a handshake with the WUT portal to get cookies.
        2. Fetch the API base path from the JavaScript configuration file.
        3. Get and update CSRF token.
        4. Get the online information of the user.
        """
        url = "http://" + self.host + "/tpl/whut/login.html?nasId=" + self.nas_id
        headers = {
            "Host": self.host,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Referer": "http://" + self.host + "/",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.5",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": self.user_agent,
        }
        self.log_printer.verbose("First Handshake...", end="")
        try:
            response = requests.get(
                url, headers=headers, cookies=self.cookies, timeout=5
            )
            if response.status_code == 200:
                self.log_printer.verbose("OK", with_time=False)
                self.network = True
                self.cookies.update(response.cookies)
            else:
                self.log_printer.verbose("Failed", with_time=False)
                self.log_printer.verbose(
                    "Unexpected response, code: "
                    + str(response.status_code)
                    + ", raw response: "
                    + response.text
                )
                self.network = False
                self.online = False
                return
        except ConnectTimeout as c:
            self.log_printer.n_verbose(
                "Timeout when trying to connect to the portal"
                + ", maybe you are off campus"
            )
            self.network = False
            self.online = False
            return
        except Exception as e:
            self.log_printer.n_verbose("Error: " + str(e))
            self.network = False
            self.online = False
            return
        # Get API Base Path
        url = "http://" + self.host + "/tpl/whut/static/js/config.js"
        headers = {
            "Host": self.host,
            "Accept": "*/*",
            "Referer": "http://"
            + self.host
            + "/tpl/whut/login.html?nasId="
            + self.nas_id,
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.5",
            "User-Agent": self.user_agent,
        }
        self.log_printer.verbose("Get API base path...", end="")
        try:
            response = requests.get(
                url, headers=headers, cookies=self.cookies, timeout=5
            )
            raw_text = response.text
            self.network = True
            extract_success = False
            if response.status_code == 200:
                self.log_printer.verbose("OK", with_time=False)
                # Extract API base path from the JavaScript file
                pruned_raw_text = PATTERN_COMMENTS.sub("", raw_text)  # Remove comments
                match = PATTERN_API_BASE_PATH.search(pruned_raw_text)
                if match:
                    self.api_base_path = match.group(1).strip()
                    self.log_printer.verbose(
                        "API base path found: " + self.api_base_path
                    )
                    extract_success = True
            if not extract_success:
                self.log_printer.verbose("Failed", with_time=False)
                self.log_printer.verbose(
                    "Status code: "
                    + str(response.status_code)
                    + ", raw response: "
                    + raw_text
                    + ", API base path not found, using default: "
                    + self.api_base_path
                )
        except Exception as e:
            self.log_printer.n_verbose("Error: " + str(e))
            self.network = False
            self.online = False
        # Get CSRF Token
        self.fetch_csrf_token()
        # Get Online Status
        url = (
            "http://"
            + self.host
            + self.api_base_path
            + self.status_endpoint
            + "?token=null"
        )
        headers = {
            "Host": self.host,
            "Accept": "*/*",
            "Referer": "http://"
            + self.host
            + "/tpl/whut/login.html?nasId="
            + self.nas_id,
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.5",
            "User-Agent": self.user_agent,
            "X-Requested-With": "XMLHttpRequest",
            "X-Csrf-Token": self.csrf_token,  # API Request with CSRF token
        }
        self.log_printer.info("Get online status...", end="")
        # data = {"token": "null"}
        try:
            response = requests.get(
                url, headers=headers, cookies=self.cookies, timeout=5
            )
            if response.status_code == 200:
                self.log_printer.info("OK", with_time=False)
                self.network = True
                try:
                    self.info = json.loads(response.text)
                    self.online = self.info["code"] == 0
                    self.login_info = self.info["online"]
                    if self.log_level > 0 and not self.shown:
                        self.show_login_info()
                        self.shown = True  # Show only once during the session
                except Exception as e:
                    self.log_printer.info("Failed", with_time=False)
                    self.log_printer.verbose("Error: " + str(e))
                    self.info = None
                    self.log_printer.info("Account status fetching failure")
                    self.online = False
                    return
            else:
                self.log_printer.info("Failed", with_time=False)
                self.log_printer.verbose(
                    "Failed to get online status, status code: "
                    + str(response.status_code)
                    + ", raw response: "
                    + response.text
                )
                self.network = False
                self.online = False
        except Exception as e:
            self.log_printer.info("Failed", with_time=False)
            self.log_printer.verbose("Error: " + str(e))
            self.network = False
            self.online = False

    def login(self):
        """
        Login to the gate
        """
        # First, fetch the host and nasId
        self.fetch_host_and_nas_id()
        url = "http://" + self.host + self.api_base_path + "/account/login"
        login_data = {
            "username": self.userid,
            "password": self.passwd,
            "swtichip": "",
            "nasId": self.nas_id,
            "userIpv4": "",
            "userMac": "",
            "captcha": "",
            "captchaId": "",
        }
        # code 0: success, 1 error, 2 code wrong
        headers = {
            "Host": self.host,
            "Accept": "*/*",
            "Referer": "http://"
            + self.host
            + "/tpl/whut/login.html?nasId="
            + self.nas_id,
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.5",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "http://" + self.host,
            "User-Agent": self.user_agent,
            "X-Requested-With": "XMLHttpRequest",
            "X-Csrf-Token": self.csrf_token,  # API Request with CSRF token
        }
        self.log_printer.verbose("Try login...", end="")
        try:
            response = requests.post(
                url, headers=headers, data=login_data, cookies=self.cookies, timeout=5
            )
            if response.status_code == 200:
                parsed_info = json.loads(response.text)
                if parsed_info["code"] != 0:
                    # If nasId is incorrect, the code will be 1 and login will fail
                    self.log_printer.verbose("Failed", with_time=False)
                    self.log_printer.info(
                        "Login failed, code: "
                        + str(parsed_info["code"])
                        + ", message: "
                        + parsed_info["msg"]
                    )
                    self.network = False
                    self.online = False
                    return
                self.cookies.update(response.cookies)
                self.network = True
                self.log_printer.verbose("OK", with_time=False)
                self.log_printer.info("Successfully logged in, now we're online")
                self.info = parsed_info
                self.online = self.info["code"]
                self.login_info = self.info["online"]
                if self.log_level > 0 and not self.shown:
                    self.show_login_info()
                    self.shown = True
            else:
                self.log_printer.verbose("Failed", with_time=False)
                self.log_printer.info(
                    "Login failed, status code: "
                    + str(response.status_code)
                    + ", raw response: "
                    + response.text
                )

        except Exception as e:
            raise e

    def run(self):
        """
        Run online status keeper
        """
        self.log_printer.info("WUT Network Online Status Keeper " + self.__version__)
        self.log_printer.info(
            "Written by " + __author__ + " (Refactor: " + __refactorer__ + ")"
        )
        while True:
            self.check()
            if not self.online:
                # Reset shown flag
                self.shown = False
                self.log_printer.info("Offline, try login")
                self.login()
                # try:
                #     self.login()
                # except Exception as e:
                #     print(self.getCurrentTime()+' Error:'+str(e))
            else:
                self.log_printer.verbose(
                    "We're good, sleep for " + str(self.interval) + " seconds"
                )
            time.sleep(self.interval)


if __name__ == "__main__":
    if userid.strip() == "" or passwd.strip() == "":
        print(
            "Please set your WUT account ID and password with environment variables 'WUT_USERID' and 'WUT_PASSWD'"
        )
        sys.exit(1)
    login = Login(userid, passwd, interval, log_level=log_level)
    login.run()

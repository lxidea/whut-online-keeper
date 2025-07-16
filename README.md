# whut-online-keeper

![Apache 2.0 license](https://img.shields.io/hexpm/l/plug) ![Python3](https://img.shields.io/pypi/pyversions/P)

武汉理工大学 校园网自动登录器  

* 当前版本 `v0.3`  
* 用于武汉理工大学校园网的长时间无人值守自动登陆及掉线重登  

使用需要 Python3，并需要确认已安装 `requests` 包。  

## 使用方式

### 1. 基于环境变量

```sh
export WUT_USERID='100110' # 你的校园卡号(校园网账号)
export WUT_PASSWD='El_psy_kongroo' # 你的校园网密码
export CHECK_INTERVAL=60 # (可选)检测间隔，单位为秒，如果不配置则默认为 600 秒
export LOG_LEVEL=1 # (可选)日志级别，0 为最简化输出，1 为详细日志，默认为 1

python wut-login.py
```

### 2. 直接改脚本文件运行

修改 `wut-login.py` 头部的配置即可:  

```python
userid = os.getenv("WUT_USERID", "你的账号")  # Read from environment variable by default
passwd = os.getenv("WUT_PASSWD", "你的密码")
interval = int(os.getenv("CHECK_INTERVAL", 600))  # Default interval is 600 seconds
log_level = int(os.getenv("LOG_LEVEL", 1))  # Default log level is 1 (verbose logs)
```

### 3. 使用 Docker

```sh
docker pull somebottle/whut-online-keeper:0.3

# --restart unless-stopped 在进程意外终止 / 关机重启 / Docker Daemon 重启等情况下自动重启
docker run -d --name whut-online-keeper \
    --restart unless-stopped \
    -e WUT_USERID='100110' \
    -e WUT_PASSWD='El_psy_kongroo' \
    -e CHECK_INTERVAL=120 \
    -e LOG_LEVEL=1 \
    somebottle/whut-online-keeper:0.3
```
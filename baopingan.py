# coding=utf-8
import requests
from lxml import etree
import configparser

requests.packages.urllib3.disable_warnings()


def get_config():
    cf = configparser.ConfigParser()
    cf.read("config.ini", encoding='utf-8')
    return cf


def send_email(text, config):
    if config.get("email", "enable") != "true":
        return
    import smtplib
    from email.mime.text import MIMEText
    from email.header import Header

    # 第三方 SMTP 服务
    mail_host = config.get("email", "mail_host")  # 设置服务器
    mail_user = config.get("email", "mail_user")  # 用户名
    mail_pass = config.get("email", "mail_pass")  # 口令

    sender = config.get("email", "mail_user")
    receivers = [config.get("email", "receiver")]  # 接收邮件，可设置为你的QQ邮箱或者其他邮箱

    message = MIMEText(text, 'plain', 'utf-8')
    message['From'] = Header("报平安", 'utf-8')
    # message['To'] = Header("测试", 'utf-8')

    subject = '报平安'
    message['Subject'] = Header(subject, 'utf-8')

    try:
        smtpObj = smtplib.SMTP()
        smtpObj.connect(mail_host, 25)  # 25 为 SMTP 端口号
        smtpObj.login(mail_user, mail_pass)
        smtpObj.sendmail(sender, receivers, message.as_string())
        print("邮件发送成功")
    except smtplib.SMTPException:
        print("Error: 无法发送邮件")


def get_ptopid(userToken):
    headers = {
        "Host": "jf.v.zzu.edu.cn",
        "userToken": userToken,
        "Authorization": "JWTToken " + userToken,
        "X-Id-Token": userToken,
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Html5Plus/1.0 (Immersed/47) uni-app SuperApp-10459",
    }
    response = requests.get("https://jf.v.zzu.edu.cn/jksb/servlet/casApi", headers=headers, verify=False)

    html = etree.HTML(response.text)
    url = html.xpath("//iframe[@id='zzj_top_6s']/@src")[0]
    _, ptopid, sid, _ = url.split('=')
    return ptopid[:-4], sid[:-5]


def login(username, password):
    headers = {
        "Host": "token.s.zzu.edu.cn",
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Device-Infos": "packagename=com.lantu.MobileCampus.zzu;version=2.3.0;system=iOS",
        "User-Agent": "SWSuperApp/2.3.0 (iPhone; iOS 15.6.1; Scale/3.00)",
    }
    data = {
        "appId": "com.lantu.MobileCampus.zzu",
        "clientId": "bae698a3a45ffad4f49142159168a7e4",
        "deviceId": "ACC4051E-988C-4061-8063-29621227CE10",
        "mfaState": "",
        "osType": "iOS",
        "password": password,
        "username": username
    }
    response = requests.post("https://token.s.zzu.edu.cn/password/passwordLogin", headers=headers, data=data,
                             verify=False)
    return response.json()['data']['idToken']


def sbpa(config):
    idToken = login(config.get("user", "username"), config.get("user", "password"))
    cookies = {
        "SECKEY_ABVK": "jFeix7lpKUwLKbEFoyhvIU+pmZ8DshNrmi96QwZiH+Y%3D",
        "userToken": idToken
    }

    ptopid, sid = get_ptopid(cookies['userToken'])

    data = {}
    for item in config.items("data"):
        data[item[0]] = item[1]

    data['ptopid'] = ptopid
    data['sid'] = sid
    headers = {
        "Host": "jksb.v.zzu.edu.cn",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://jksb.v.zzu.edu.cn",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Html5Plus/1.0 (Immersed/47) uni-app SuperApp-10459",
        "Referer": "https://jksb.v.zzu.edu.cn/vls6sss/zzujksb.dll/jksb",
    }
    result = requests.post("https://jksb.v.zzu.edu.cn/vls6sss/zzujksb.dll/jksb", headers=headers, cookies=cookies,
                           data=data, verify=False)
    result.encoding = result.apparent_encoding
    msg = "".join(etree.HTML(result.text).xpath("//div[@id='bak_0']//text()")).strip()
    print(msg)
    send_email(msg, config)


if __name__ == '__main__':

    def wrapper():
        config = get_config()
        try:
            sbpa(config)
        except Exception as e:
            print(e)
            send_email("Error", config)


    import schedule
    import time

    wrapper()

    at = get_config().get("schedule", "at")
    print(f"每天报平安时间为：{at}")
    schedule.every().day.at(at).do(wrapper)
    while True:
        schedule.run_pending()
        time.sleep(60)
        print("-")

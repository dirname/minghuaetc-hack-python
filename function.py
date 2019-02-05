import base64
import hashlib
import json
import re
import sys
import pyDes
import requests
from prettytable import PrettyTable


def pwd_encrypt(password):
    key = "DrZPGgL9WHkZrVQ0DT2bASoZE0Z8oc4s"
    key = base64.standard_b64decode(key)
    k = pyDes.triple_des(key, pyDes.ECB, IV=None, pad=None, padmode=pyDes.PAD_PKCS5)
    d = k.encrypt(password)
    res = base64.b64encode(d)
    return bytes.decode(res, "utf8")


def get_sign(params):
    params += "xF3m1m4CrvQd3VsfsEpIf6s0CPWT7sJu"
    m2 = hashlib.md5()
    m2.update(params.encode("utf8"))
    return m2.hexdigest()


class API:
    url = "http://api.mooc.minghuaetc.com/v1"
    moocsk = ""
    moocvk = ""
    stuName = ""
    isLogin = ""

    def get_org(self):
        cmd = "sys.org"
        client = "chinamoocs"
        index = "1"
        authuser = ""
        size = "200"
        type = "10"
        sign = "9081119e45061013400710d32e87a49a"
        post_data = {
            "cmd": cmd,
            "client": client,
            "index": index,
            "authuser": authuser,
            "size": size,
            "type": type,
            "sign": sign
        }
        response = requests.post(self.url, data=post_data)
        obj = json.loads(response.text)
        if obj["message"] != "命令执行成功":
            print("%s %s" % ("[Error]", "获取校园平台失败"))
            sys.exit(0)
        else:
            table = PrettyTable(["学校序号", "学校名称"])
            orgs = obj["result"]["orgs"]
            for items in orgs:
                org_name = items["orgName"]
                org_id = items["orgId"]
                table.add_row([org_id, org_name])
            print(table)

    def login(self, org_id, user, pwd):
        cmd = "sys.login.no"
        client = "chinamoocs"
        sign = get_sign(cmd + client + org_id + user + pwd_encrypt(pwd))
        post_data = {
            "cmd": cmd,
            "client": client,
            "orgid": org_id,
            "user": user,
            "password": pwd_encrypt(pwd),
            "sign": sign
        }
        response = requests.post(self.url, data=post_data)
        obj = json.loads(response.text)
        if obj["message"] == "命令执行成功":
            self.stuName = obj["result"]["user"]["aliasName"]
            self.moocsk = response.cookies["moocsk"]
            self.moocvk = response.cookies["moocvk"]
            table = PrettyTable([self.stuName, " 登陆成功 !"])
            print(table)
            return True

        else:
            print("[Error] " + user + " " + obj["message"])
            return False

    def course(self):
        cmd = "course.my"
        client = "chinamoocs"
        index = "1"
        size = "5"
        status = "10"
        sign = get_sign(cmd + client + index + size + status)
        post_data = {
            "cmd": cmd,
            "client": client,
            "index": index,
            "size": size,
            "status": status,
            "sign": sign
        }

        cookies = {
            'moocsk': self.moocsk,
            'moocvk': self.moocvk
        }
        response = requests.post(self.url, data=post_data, cookies=cookies)
        obj = json.loads(response.text)
        if obj["message"] == "命令执行成功":
            table = PrettyTable(["课程序号", "课程名称", "结束时间"])
            courses = obj["result"]["courses"]
            lesson_id = 0
            for items in courses:
                course_name = items["courseName"]
                end_date = items["endDate"]
                table.add_row([lesson_id, course_name, end_date])
                lesson_id += 1
            print(table)
            print()
            which = input("输入课程的序号以查看每一节课时详情, 输入\"end\"回到菜单, 课程序号: ")
            if which == "end":
                self.menu()
            else:
                try:
                    which = int(which)
                    session_id = courses[which]["sessionId"]
                    course_id = courses[which]["courseId"]
                    self.get_class_only(course_id, session_id)
                except Exception as ex:
                    print(ex)
                    print("[Error] 输入了错误的课程序号")
                    self.course()
                    print()
        else:
            print("[Error] " + obj["message"])
        self.cmd()

    def get_class_only(self, course, session):
        cmd = "course.learn"
        client = "chinamoocs"
        course = str(course)
        session = str(session)
        all = "1"
        sign = get_sign(cmd + client + course + session + all)
        post_data = {
            "cmd": cmd,
            "client": client,
            "course": course,
            "session": session,
            "all": all,
            "sign": sign
        }

        cookies = {
            'moocsk': self.moocsk,
            'moocvk': self.moocvk
        }

        response = requests.post(self.url, data=post_data, cookies=cookies)
        string = response.text
        obj = json.loads(string)
        if obj["message"] == "命令执行成功":
            print()
            units = obj["result"]["units"]
            table = PrettyTable(["课程ID", "课程名称", "状态"])
            for ItemUnits in units:
                item_obj = ItemUnits["lessons"]
                for ItemLessons in item_obj:
                    lesson_array = ItemLessons["items"]
                    for items in lesson_array:
                        status = items["status"]
                        if status == 0:
                            status = "未观看"
                        elif status == 1:
                            status = "正在观看"
                        elif status == 2:
                            status = "已观看"
                        item_name = items["itemName"]
                        item_id = items["itemId"]
                        table.add_row([item_id, item_name, status])
            print(table)
            self.cmd()

    def init(self):
        print()
        print("###############################################")
        print("######  欢迎使用名华慕课 Cheating Tool   ######")
        print("# 该工具仅供学习交流使用,请下载的24小时内删除 #")
        print("############## Powered by Ah ! ################")
        print()
        print("-----------------------------------------------")
        self.get_org()
        org_id = input("\n请选择您的学校,输入学校序号: ")
        while org_id.replace(" ", "") == "":
            org_id = input("请选择您的学校,输入学校序号: ")
        student_id = input("请输入您的学号: ")
        while student_id.replace(" ", "") == "":
            student_id = input("请输入您的学号: ")
        student_pwd = input("请输入您的密码: ")
        while student_pwd.replace(" ", "") == "":
            student_pwd = input("请输入您的密码: ")
        self.is_login = self.login(org_id, student_id, student_pwd)
        while not self.is_login:
            student_id = input("请输入您的学号: ")
            while student_id.replace(" ", "") == "":
                student_id = input("请输入您的学号: ")
            student_pwd = input("请输入您的密码: ")
            while student_pwd.replace(" ", "") == "":
                student_pwd = input("请输入您的密码: ")
            self.is_login = self.login(org_id, student_id, student_pwd)

    def menu(self):
        if self.is_login:
            table = PrettyTable(["指令", "指令名称"])
            table.add_row(["1", "查看我的课程"])
            table.add_row(["2", "一键完成所有课程"])
            table.add_row(["3", "更换用户"])
            table.add_row(["menu", "显示功能列表"])
            table.add_row(["who", "显示当前登陆用户"])
            table.add_row(["exit", "退出程序"])
            print(table)
            self.cmd()
        else:
            self.init()

    def who(self):
        table = PrettyTable(["当前用户: " + self.stuName])
        print(table)
        self.cmd()

    def lesson(self):
        cmd = "course.my"
        client = "chinamoocs"
        index = "1"
        size = "5"
        status = "10"
        sign = get_sign(cmd + client + index + size + status)
        post_data = {
            "cmd": cmd,
            "client": client,
            "index": index,
            "size": size,
            "status": status,
            "sign": sign
        }

        cookies = {
            'moocsk': self.moocsk,
            'moocvk': self.moocvk
        }
        response = requests.post(self.url, data=post_data, cookies=cookies)
        string = response.text
        obj = json.loads(string)
        if obj["message"] == "命令执行成功":
            table = PrettyTable(["课程序号", "课程名称", "结束时间"])
            courses = obj["result"]["courses"]
            lesson_id = 0
            for items in courses:
                course_name = items["courseName"]
                end_date = items["endDate"]
                table.add_row([lesson_id, course_name, end_date])
                lesson_id += 1
            print(table)
            print()
            which = int(input("请输入课程的序号(注意以\"0开始\"): "))
            try:
                session_id = courses[which]["sessionId"]
                course_id = courses[which]["courseId"]
                self.get_class(course_id, session_id)
            except Exception as ex:
                print(ex)
                print("[Error] 输入了错误的课程序号")
                self.lesson()
                print()
        else:
            print("[Error] " + obj["message"])
        self.cmd()

    def get_class(self, course, session):
        cmd = "course.learn"
        client = "chinamoocs"
        course = str(course)
        session = str(session)
        all = "1"
        sign = get_sign(cmd + client + course + session + all)
        post_data = {
            "cmd": cmd,
            "client": client,
            "course": course,
            "session": session,
            "all": all,
            "sign": sign
        }

        cookies = {
            'moocsk': self.moocsk,
            'moocvk': self.moocvk
        }

        response = requests.post(self.url, data=post_data, cookies=cookies)
        string = response.text
        obj = json.loads(string)
        if obj["message"] == "命令执行成功":
            print()
            units = obj["result"]["units"]
            table = PrettyTable(["课程ID", "课程名称", "状态"])
            for ItemUnits in units:
                item_obj = ItemUnits["lessons"]
                for ItemLessons in item_obj:
                    lesson_array = ItemLessons["items"]
                    for items in lesson_array:
                        status = items["status"]
                        if status == 0:
                            status = "未观看"
                        elif status == 1:
                            status = "正在观看"
                        elif status == 2:
                            status = "已观看"
                        item_name = items["itemName"]
                        item_id = items["itemId"]
                        item_type = items["itemType"]
                        meta = items["meta"]
                        table.add_row([item_id, item_name, status])
                        self.get_items(item_id, item_type, meta, item_name)
            print()
            print("##### 刷课前的课程观看状态 #####")
            print()
            print(table)
            print()
            print(" ***** 获取最新课程状态, 请使用查看\"我的课程\"指令 ***** ")
            self.cmd()
        else:
            print("[Error] " + obj["message"])

    def get_items(self, item_id, item_type, meta_id, item_name):
        header = {
            "Referer": "http://ynnubs.minghuaetc.com/study/unit/" + item_id + ".mooc"
        }
        cookies = {
            'moocsk': self.moocsk,
            'moocvk': self.moocvk
        }

        post_data = {
            "itemId": item_id,
            "itemType": item_type,
            "testPaperId": ""
        }
        response = requests.post("http://ynnubs.minghuaetc.com/study/play.mooc", data=post_data, cookies=cookies,
                                 headers=header)
        string = response.text
        match = re.findall("meta = {\"duration.*", string)
        meta = str(match[0]).replace("meta = ", "").replace("};", "}")
        obj = json.loads(meta)
        duration = str(obj["duration"])
        self.submit_lesson(str(meta_id), item_id, duration, item_name)

    def submit_lesson(self, meta, item, duration, class_name):
        cmd = "learn.pos"
        client = "chinamoocs"
        sign = get_sign(cmd + client + item + duration + duration + meta)
        post_data = {
            "cmd": cmd,
            "client": client,
            "item": item,
            "last": duration,
            "max": duration,
            "meta": meta,
            "sign": sign
        }

        cookies = {
            'moocsk': self.moocsk,
            'moocvk': self.moocvk
        }

        response = requests.post(self.url, data=post_data, cookies=cookies)
        obj = json.loads(response.text)
        if str(obj["message"]) != "命令执行成功":
            print("[%s] - %s %s" % (str(item), str(class_name), str(obj["message"])))
        else:
            print("[%s] - %s %s" % (str(item), str(class_name), str(obj["message"])))

    def change_user(self):
        print("####### 更换用户 ######")
        self.init()
        self.menu()

    def cmd(self):
        cmd = input("\n输入指令以开始功能,\"menu\"显示功能菜单: ")
        print()
        if cmd == "1":
            self.course()
        elif cmd == "2":
            self.lesson()
        elif cmd == "3":
            self.change_user()
        elif cmd == "menu":
            self.menu()
        elif cmd == "who":
            self.who()
        elif cmd == "exit":
            table = PrettyTable(["Good bye !", "Have a good day !"])
            print(table)
            sys.exit(0)
        else:
            self.menu()

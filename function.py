import base64
import hashlib
import json
import re
import sys
import pyDes
import requests
from prettytable import PrettyTable


def pwdEncrypt(password):
    key = "DrZPGgL9WHkZrVQ0DT2bASoZE0Z8oc4s"
    key = base64.standard_b64decode(key)
    k = pyDes.triple_des(key, pyDes.ECB, IV=None, pad=None, padmode=pyDes.PAD_PKCS5)
    d = k.encrypt(password)
    res = base64.b64encode(d)
    return bytes.decode(res, "utf8")


def getSign(params):
    params += "xF3m1m4CrvQd3VsfsEpIf6s0CPWT7sJu"
    m2 = hashlib.md5()
    m2.update(params.encode("utf8"))
    return m2.hexdigest()

class API():
    url = "http://api.mooc.minghuaetc.com/v1"
    moocsk = ""
    moocvk = ""
    stuName = ""
    isLogin = ""

    def getOrg(self):
        cmd = "sys.org"
        client = "chinamoocs"
        index = "1"
        authuser = ""
        size = "200"
        type = "10"
        sign = "9081119e45061013400710d32e87a49a"
        postData = {
            "cmd": cmd,
            "client": client,
            "index": index,
            "authuser": authuser,
            "size": size,
            "type": type,
            "sign": sign
        }
        response = requests.post(self.url, data=postData)
        object = json.loads(response.text)
        if (object["message"] != "命令执行成功"):
            print("%s %s" % ("[Error]", "获取校园平台失败"))
            sys.exit(0)
        else:
            table = PrettyTable(["学校序号", "学校名称"])
            orgs = object["result"]["orgs"]
            for items in orgs:
                orgName = items["orgName"]
                orgID = items["orgId"]
                table.add_row([orgID, orgName])
            print(table)

    def login(self,orgid, user, pwd):
        cmd = "sys.login.no"
        client = "chinamoocs"
        sign = getSign(cmd + client + orgid + user + pwdEncrypt(pwd))
        postData = {
            "cmd": cmd,
            "client": client,
            "orgid": orgid,
            "user": user,
            "password": pwdEncrypt(pwd),
            "sign": sign
        }
        response = requests.post(self.url, data=postData)
        obj = json.loads(response.text)
        if (obj["message"] == "命令执行成功"):
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
        sign = getSign(cmd + client + index + size + status)
        postData = {
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
        response = requests.post(self.url, data=postData, cookies=cookies)
        obj = json.loads(response.text)
        if (obj["message"] == "命令执行成功"):
            table = PrettyTable(["课程序号", "课程名称", "结束时间"])
            courses = obj["result"]["courses"]
            lessonID = 0
            for items in courses:
                courseName = items["courseName"]
                endDate = items["endDate"]
                table.add_row([lessonID, courseName, endDate])
                lessonID += 1
            print(table)
            print()
            which = input("输入课程的序号以查看每一节课时详情, 输入\"end\"回到菜单, 课程序号: ")
            if (which == "end"):
                self.menu()
            else:
                try:
                    which = int(which)
                    sessionId = courses[which]["sessionId"]
                    courseId = courses[which]["courseId"]
                    self.getClassOnly(courseId, sessionId)
                except Exception as ex:
                    print(ex)
                    print("[Error] 输入了错误的课程序号")
                    self.course()
                    print()
        else:
            print("[Error] " + obj["message"])
        self.cmd()

    def getClassOnly(self,course,session):
        cmd = "course.learn"
        client = "chinamoocs"
        course = str(course)
        session = str(session)
        all = "1"
        sign = getSign(cmd + client + course + session + all)
        postData = {
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

        response = requests.post(self.url, data=postData, cookies=cookies)
        string = response.text
        obj = json.loads(string)
        if (obj["message"] == "命令执行成功"):
            print()
            units = obj["result"]["units"]
            table = PrettyTable(["课程ID", "课程名称", "状态"])
            for ItemUnits in units:
                itemObj = ItemUnits["lessons"]
                for ItemLessons in itemObj:
                    lessonNo = ItemLessons["lessonNo"]
                    lessonId = ItemLessons["lessonId"]
                    lessonName = ItemLessons["lessonName"]
                    lessonArray = ItemLessons["items"]
                    for items in lessonArray:
                        status = items["status"]
                        if (status == 0):
                            status = "未观看"
                        elif (status == 1):
                            status = "正在观看"
                        elif (status == 2):
                            status = "已观看"
                        itemName = items["itemName"]
                        itemId = items["itemId"]
                        itemType = items["itemType"]
                        meta = items["meta"]
                        table.add_row([itemId, itemName, status])
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
        self.getOrg()
        orgid = input("\n请选择您的学校,输入学校序号: ")
        while (orgid.replace(" ", "") == ""):
            orgid = input("请选择您的学校,输入学校序号: ")
        studentID = input("请输入您的学号: ")
        while (studentID.replace(" ", "") == ""):
            studentID = input("请输入您的学号: ")
        studentPwd = input("请输入您的密码: ")
        while (studentPwd.replace(" ", "") == ""):
            studentPwd = input("请输入您的密码: ")
        self.isLogin = self.login(orgid, studentID, studentPwd)
        while (self.isLogin != True):
            studentID = input("请输入您的学号: ")
            while (studentID.replace(" ", "") == ""):
                studentID = input("请输入您的学号: ")
            studentPwd = input("请输入您的密码: ")
            while (studentPwd.replace(" ", "") == ""):
                studentPwd = input("请输入您的密码: ")
            self.isLogin = self.login(orgid, studentID, studentPwd)

    def menu(self):
        if (self.isLogin):
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
        sign = getSign(cmd + client + index + size + status)
        postData = {
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
        response = requests.post(self.url, data=postData, cookies=cookies)
        string = response.text
        obj = json.loads(string)
        if (obj["message"] == "命令执行成功"):
            table = PrettyTable(["课程序号", "课程名称", "结束时间"])
            courses = obj["result"]["courses"]
            lessonID = 0
            for items in courses:
                courseName = items["courseName"]
                endDate = items["endDate"]
                table.add_row([lessonID, courseName, endDate])
                lessonID += 1
            print(table)
            print()
            which = int(input("请输入课程的序号(注意以\"0开始\"): "))
            try:
                sessionId = courses[which]["sessionId"]
                courseId = courses[which]["courseId"]
                self.getClass(courseId, sessionId)
            except Exception as ex:
                print(ex)
                print("[Error] 输入了错误的课程序号")
                self.lesson()
                print()
        else:
            print("[Error] " + obj["message"])
        self.cmd()

    def getClass(self,course,session):
        cmd = "course.learn"
        client = "chinamoocs"
        course = str(course)
        session = str(session)
        all = "1"
        sign = getSign(cmd + client + course + session + all)
        postData = {
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

        response = requests.post(self.url, data=postData, cookies=cookies)
        string = response.text
        obj = json.loads(string)
        if (obj["message"] == "命令执行成功"):
            print()
            units = obj["result"]["units"]
            table = PrettyTable(["课程ID", "课程名称", "状态"])
            for ItemUnits in units:
                itemObj = ItemUnits["lessons"]
                for ItemLessons in itemObj:
                    lessonNo = ItemLessons["lessonNo"]
                    lessonId = ItemLessons["lessonId"]
                    lessonName = ItemLessons["lessonName"]
                    lessonArray = ItemLessons["items"]
                    for items in lessonArray:
                        status = items["status"]
                        if (status == 0):
                            status = "未观看"
                        elif (status == 1):
                            status = "正在观看"
                        elif (status == 2):
                            status = "已观看"
                        itemName = items["itemName"]
                        itemId = items["itemId"]
                        itemType = items["itemType"]
                        meta = items["meta"]
                        table.add_row([itemId, itemName, status])
                        self.getItems(lessonId,itemId,itemType,meta,session,itemName)
            print()
            print("##### 刷课前的课程观看状态 #####")
            print()
            print(table)
            print()
            print(" ***** 获取最新课程状态, 请使用查看\"我的课程\"指令 ***** ")
            self.cmd()
        else:
            print("[Error] " + obj["message"])

    def getItems(self,lessonId,itemid,itemntype,metaID,session,itemName):
        header = {
            "Referer":"http://ynnubs.minghuaetc.com/study/unit/" + itemid + ".mooc"
        }
        cookies = {
            'moocsk': self.moocsk,
            'moocvk': self.moocvk
        }

        postData = {
            "itemId": itemid,
            "itemType": itemntype,
            "testPaperId": ""
        }
        response = requests.post("http://ynnubs.minghuaetc.com/study/play.mooc", data=postData, cookies=cookies, headers=header)
        string = response.text
        match = re.findall("meta = {\"duration.*",string)
        meta = str(match[0]).replace("meta = ", "").replace("};", "}")
        obj = json.loads(meta)
        duration = str(obj["duration"])
        self.submitLesson(str(metaID),itemid,duration,itemName)

    def submitLesson(self,meta,item,duration,className):
        cmd = "learn.pos"
        client = "chinamoocs"
        sign = getSign(cmd + client + item + duration + duration + meta)
        postData = {
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

        response = requests.post(self.url, data=postData, cookies=cookies)
        obj = json.loads(response.text)
        if (str(obj["message"]) != "命令执行成功"):
            print("[%s] - %s %s" % (str(item),str(className),str(obj["message"])))
        else:
            print("[%s] - %s %s" % (str(item), str(className), str(obj["message"])))

    def changeUser(self):
        print("####### 更换用户 ######")
        self.init()
        self.menu()

    def cmd(self):
        cmd = input("\n输入指令以开始功能,\"menu\"显示功能菜单: ")
        print()
        if (cmd == "1"):
            self.course()
        elif (cmd == "2"):
            self.lesson()
        elif (cmd == "3"):
            self.changeUser()
        elif (cmd == "menu"):
            self.menu()
        elif (cmd == "who"):
            self.who()
        elif (cmd == "exit"):
            table = PrettyTable(["Good bye !", "Have a good day !"])
            print(table)
            sys.exit(0)
        else:
            self.menu()
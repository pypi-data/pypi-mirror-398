from datetime import datetime

import pytest
import requests

data = {"passed": 0, "failed": 0}


def pytest_addoption(parser):  # ini配置文件  配置什么东西 如何使用的
    parser.addini("send_when", help="何时发送结果")
    parser.addini("send_api", help="测试结果发往何处")


def pytest_runtest_logreport(report: pytest.TestReport):
    if report.when == "call":
        print("本次用例执行的结果", report.outcome)
        data[report.outcome] += 1


def pytest_collection_finish(session: pytest.Session):
    data["total"] = len(session.items)
    print(session.items)


# 当代码执行到这里的时候（钩子这里的时候），所有的配置项就已经加载完成
def pytest_configure(config: pytest.Config):
    # pytest配置文件加载完毕之后 即测试用例执行之前执行
    data["start_time"] = datetime.now()
    data["send_when"] = config.getini("send_when")
    data["send_api"] = config.getini("send_api")
    print(config.getini("send_when"))
    print(config.getini("send_api"))


def pytest_unconfigure(config):
    # pytest配置卸载完毕之后 即测试用例执行之后执行
    data["end_time"] = datetime.now()
    # print(f"{datetime.now()}  pytest结束执行")

    data["duration"] = data["end_time"] - data["start_time"]
    total = data.get("total", 0)
    data["pass_ratio"] = (data["passed"] / total * 100) if total else 0.0
    data["pass_ratio"] = f"{data['pass_ratio']:.2f}"
    send_result()


def send_result():

    if data["send_when"] == "on_fail" and data["failed"] == 0:
        # 如果配置失败才发送，但实际没有失败，则不发送
        return
    if not data["send_api"]:
        # 如果没有配置API地址，则不发送
        return
    url = data["send_api"]  # 动态指定结果发送位置
    # url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=5e54217d-f6c6-4c02-885e-0e8c253c23e4"
    content = f"""pytest自动化测试结果

    测试时间：{data['end_time']} 
    用例数量：{data['total']}
    执行时长：{data['duration']}s 
    测试通过：<font color='green'>{data['passed']}</font>
    测试失败：<font color='red'>{data['failed']}</font>
    测试通过率：{data['pass_ratio']}% 
    测试报告地址：https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=5e54217d-f6c6-4c02-885e-0e8c253c23e4
    """
    try:
        requests.post(
            url, json={"msgtype": "markdown", "markdown": {"content": content}}
        )
    except Exception:
        pass

    data["send_done"] = 1  # 发送成功

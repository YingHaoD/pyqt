import sys
import pymysql
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QMessageBox, QVBoxLayout
import requests
import json


class MySQLConnection(object):
    '''
    用来链接mysql的模块
    '''

    def __init__(self, host, user, password, db):
        self.host = host
        self.user = user
        self.password = password
        self.db = db

    def connect(self):
        self.con = pymysql.connect(host=self.host, user=self.user, password=self.password, db=self.db)
        self.cursor = self.con.cursor()

    def close(self):
        self.con.close()

    def execute(self, query, params):
        self.cursor.execute(query, params)
        self.con.commit()


class MainWindow(QWidget):
    '''
    用来做登录完成后的主界面
    '''

    def __init__(self, login_window):
        super().__init__()

        self.login_window = login_window  # 在 MainWindow 对象中保存 LoginWindow 对象的引用

        self.init_ui()

    def init_ui(self):
        self.loan_button = QPushButton('贷款计算')
        self.loan_button.clicked.connect(self.open_loan_calculator)

        self.fund_button = QPushButton('基金投资计算')
        self.fund_button.clicked.connect(self.open_fund_calculator)

        layout = QVBoxLayout()
        layout.addWidget(self.loan_button)
        layout.addWidget(self.fund_button)
        # 爬取当前时间
        response = requests.get("https://timeapi.io/api/Time/current/zone?timeZone=Asia/Shanghai")
        # 对返回字符串解析
        str_ = response.content.decode("utf-8")
        # 解析成json
        dict_ = json.loads(str_)
        # 获取对应的时间
        if dict_.get("minute") < 10:
            time_s = str(dict_.get("year")) + "-" + str(dict_.get("month")) + "-" + str(dict_.get("day")) + " " + str(
                dict_.get("hour")) + ":" + "0" + str(dict_.get("minute"))
        else:
            time_s = str(dict_.get("year")) + "-" + str(dict_.get("month")) + "-" + str(dict_.get("day")) + " " + str(
                dict_.get("hour")) + ":" + str(dict_.get("minute"))

        self.setLayout(layout)
        self.setWindowTitle('首页' + time_s)

    def open_loan_calculator(self):
        self.hide()
        self.lw = LoanCalculatorWindow(self,
                                       self.login_window)  # 传递 MainWindow 和 LoginWindow 对象的引用给 LoanCalculatorWindow 对象
        self.lw.show()

    def open_fund_calculator(self):
        self.hide()
        self.fw = FundInvestmentWindow(self, self.login_window)
        self.fw.show()


class LoanCalculatorWindow(QWidget):
    # 贷款计算模块
    def __init__(self, main_window, login_window):
        super().__init__()
        self.main_window = main_window
        self.login_window = login_window
        self.init_ui()

    def init_ui(self):
        # 创建输入框和按钮
        self.amount_entry = QLineEdit()
        self.term_entry = QLineEdit()
        self.interest_rate_entry = QLineEdit()

        self.annuity_button = QPushButton('等额本息计算')
        self.annuity_button.clicked.connect(self.annuity_calculation)

        self.amortization_button = QPushButton('等额本金')
        self.amortization_button.clicked.connect(self.amortization_calculation)

        self.home_button = QPushButton('返回首页')
        self.home_button.clicked.connect(self.return_to_home)

        self.logout_button = QPushButton('退出')
        self.logout_button.clicked.connect(self.logout)

        # 创建结果展示标签
        self.result_label = QLabel('')

        # 创建布局并添加控件
        layout = QVBoxLayout()
        layout.addWidget(QLabel('总金额：'))
        layout.addWidget(self.amount_entry)
        layout.addWidget(QLabel('期数 (年)：'))
        layout.addWidget(self.term_entry)
        layout.addWidget(QLabel('利率：'))
        layout.addWidget(self.interest_rate_entry)
        layout.addWidget(self.annuity_button)
        layout.addWidget(self.amortization_button)
        layout.addWidget(self.home_button)
        layout.addWidget(self.logout_button)
        layout.addWidget(self.result_label)

        self.setLayout(layout)
        self.setWindowTitle('贷款计算')

    def annuity_calculation(self):
        if not self.validate_inputs():
            return
        # 等额本息计算逻辑
        self.B0 = float(self.amount_entry.text())
        self.n = int(self.term_entry.text())
        self.i = float(self.interest_rate_entry.text())

        def PVIFA(parameter):  # 第k期的年金现值系数，parameter表示k
            return (1 - (1 + self.i) ** (parameter - self.n)) / self.i

        k = 1
        A = self.B0 / PVIFA(0)  # 每期还款额
        plan = '等额本息下的还款计划书：\n'
        plan += f"等额本息下的总还款额：{round(A * self.n, 4)}\n"
        plan += f"等额本息下的总支付利息：{round(A * self.n - self.B0, 4)}\n"
        # self.plan = plan
        details = []
        for k in range(1, self.n + 1):
            Bk = A * PVIFA(k)  # k期剩余未还本金
            Ik = self.i * A * PVIFA(k - 1)  # k期应还利息
            Pk = A - Ik  # k期应还本金
            Rk = (self.n - k) * A - Bk  # k期末的剩余未还的利息
            details.append({
                "期数": k,
                "应还本金": round(Pk, 4),
                "应还利息": round(Ik, 4),
                "剩余未还本金": round(Bk, 4),
                "剩余未还利息": round(Rk, 4)
            })
        # self.details = details
        result = '\n'.join(' '.join(f'{k}: {v}' for k, v in item.items()) for item in details)
        plan += result
        self.result_label.setText(plan)

    def amortization_calculation(self):
        if not self.validate_inputs():
            return
        # 等额本金计算逻辑
        self.B0 = float(self.amount_entry.text())
        self.n = int(self.term_entry.text())
        self.i = float(self.interest_rate_entry.text())

        k = 1
        details = []
        Pk = self.B0 / self.n  # 每期应还本金
        total_payment = 0
        plan = '等额本金下的还款计划书：\n'
        for k in range(1, self.n + 1):
            Bk = self.B0 - k * Pk  # k期剩余未还本金
            Ik = self.i * (self.B0 - (k - 1) * Pk)  # k期应还利息
            Ak = Pk + Ik  # k期还款本息
            total_payment += Ak  # 累加的还款总额
            Rk = self.i * self.B0 * (self.n - k) * (self.n - k + 1) / (2 * self.n)  # k期末的剩余未还的利息
            details.append({
                "期数": k,
                "本期应还利息": round(Ik, 4),
                "剩余未还本金": round(Bk, 4),
                "剩余未还利息": round(Rk, 4)
            })
        plan += f"等额本金下的总还款额：{round(total_payment, 4)}\n"
        plan += f"等额本金下的总支付利息：{round(total_payment - self.B0, 4)}\n"
        plan += f"等额本金下的每期应还本金：{round(Pk, 4)}\n"
        result = '\n'.join(' '.join(f'{k}: {v}' for k, v in item.items()) for item in details)
        plan += result

        self.result_label.setText(plan)

    def validate_inputs(self):
        try:
            float(self.amount_entry.text())
            int(self.term_entry.text())
            float(self.interest_rate_entry.text())
            return True
        except ValueError:
            QMessageBox.warning(self, 'Error', '请输入有效的输入')
            return False

    def return_to_home(self):
        self.close()
        self.main_window.show()

    def logout(self):
        self.close()
        self.login_window.show()


class FundInvestmentWindow(QWidget):
    def __init__(self, main_window, login_window):
        super().__init__()
        self.main_window = main_window
        self.login_window = login_window
        self.init_ui()

    def init_ui(self):
        # 创建输入框和按钮
        self.investment_amount_entry = QLineEdit()
        self.term_entry = QLineEdit()
        self.yield_rate_entry = QLineEdit()

        self.annual_yield_button = QPushButton('计算七日年化收益率')
        self.annual_yield_button.clicked.connect(self.calculate_annual_yield)

        self.daily_yield_button = QPushButton('计算每日万分收益')
        self.daily_yield_button.clicked.connect(self.calculate_daily_yield)

        self.fund_investment_button = QPushButton('计算定投收益')
        self.fund_investment_button.clicked.connect(self.calculate_fund_investment_yield)

        # 创建返回和退出登录按钮
        self.home_button = QPushButton('返回首页')
        self.home_button.clicked.connect(self.return_to_home)

        self.logout_button = QPushButton('退出')
        self.logout_button.clicked.connect(self.logout)

        # 创建结果展示标签
        self.result_label = QLabel('')

        # 创建布局并添加控件
        layout = QVBoxLayout()
        layout.addWidget(QLabel('投资金额:'))
        layout.addWidget(self.investment_amount_entry)
        layout.addWidget(QLabel('投资期限:'))
        layout.addWidget(self.term_entry)
        layout.addWidget(QLabel('回报率(百分数):'))
        layout.addWidget(self.yield_rate_entry)
        layout.addWidget(self.annual_yield_button)
        layout.addWidget(self.daily_yield_button)
        layout.addWidget(self.fund_investment_button)
        layout.addWidget(self.home_button)
        layout.addWidget(self.logout_button)
        layout.addWidget(self.result_label)

        self.setLayout(layout)
        self.setWindowTitle('基金投资计算')

    def calculate_returns(self, investment_amount, term, rate):
        # 每日收益率假设为年化收益率除以365
        daily_rate = rate / 365

        # 每日万分收益（单位：元）
        daily_return_per_10000 = daily_rate * investment_amount / 10000

        # 七日年化收益率（单位：%）
        seven_day_annualized_return = daily_rate * 7 * 365 * 100

        # 定投每期的投资金额
        regular_investment_amount = investment_amount / term

        # 定投收益
        regular_investment_return = 0
        for i in range(term):
            regular_investment_return += regular_investment_amount * (1 + daily_rate) ** i
        regular_investment_return = regular_investment_return - investment_amount

        return daily_return_per_10000, seven_day_annualized_return, regular_investment_return

    def calculate_annual_yield(self):
        if not self.validate_inputs():
            return
        # 7-day annual yield计算逻辑
        self.B0 = float(self.investment_amount_entry.text())
        self.n = int(self.term_entry.text())
        self.i = float(self.yield_rate_entry.text())
        a, b, c = self.calculate_returns(self.B0, self.n, self.i)
        self.result_label.setText("七日年化收益率（单位：%）:" + str(b/1000))

    def calculate_daily_yield(self):
        if not self.validate_inputs():
            return
        # daily yield计算逻辑
        self.B0 = float(self.investment_amount_entry.text())
        self.n = int(self.term_entry.text())
        self.i = float(self.yield_rate_entry.text())
        a, b, c = self.calculate_returns(self.B0, self.n, self.i)
        self.result_label.setText("每日万分收益（单位：元）:" + str(a*10))

    def calculate_fund_investment_yield(self):
        if not self.validate_inputs():
            return
        # fund investment yield计算逻辑
        self.B0 = float(self.investment_amount_entry.text())
        self.n = int(self.term_entry.text())
        self.i = float(self.yield_rate_entry.text())
        a, b, c = self.calculate_returns(self.B0, self.n, self.i)
        self.result_label.setText("定投收益:" + str(c))

    def validate_inputs(self):
        try:
            float(self.investment_amount_entry.text())
            float(self.term_entry.text())
            float(self.yield_rate_entry.text())
            return True
        except ValueError:
            QMessageBox.warning(self, 'Error', '请输入有效的输入')
            return False

    def return_to_home(self):
        self.close()
        self.main_window.show()

    def logout(self):
        self.close()
        self.login_window.show()


class LoginWindow(QWidget):
    '''
    登录界面模块
    '''

    def __init__(self, db_connection):
        super().__init__()

        self.db = db_connection

        self.init_ui()

    def init_ui(self):
        self.username_label = QLabel('用户名：')
        self.username_entry = QLineEdit()
        self.password_label = QLabel('密码：')
        self.password_entry = QLineEdit()
        self.password_entry.setEchoMode(QLineEdit.Password)

        self.login_button = QPushButton('登录')
        self.login_button.clicked.connect(self.check_credentials)

        self.register_button = QPushButton('注册')
        self.register_button.clicked.connect(self.register)

        layout = QVBoxLayout()
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_entry)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_entry)
        layout.addWidget(self.login_button)
        layout.addWidget(self.register_button)

        self.setLayout(layout)
        self.setWindowTitle('登录')

    def check_credentials(self):
        username = self.username_entry.text()
        password = self.password_entry.text()

        self.db.connect()
        self.db.cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password))
        account = self.db.cursor.fetchone()
        self.db.close()

        if account:
            self.login_success()
        else:
            QMessageBox.warning(self, 'Error', '错误的用户名或者密码')

    def login_success(self):
        QMessageBox.information(self, 'Success', '登录成功!')
        self.close()

        self.mw = MainWindow(self)  # 传递 LoginWindow 对象的引用给 MainWindow 对象
        self.mw.show()

    def register(self):
        self.hide()
        self.rw = RegisterWindow(self.db, self)
        self.rw.show()


class RegisterWindow(QWidget):
    def __init__(self, db_connection, login_window):
        super().__init__()

        self.db = db_connection
        self.login_window = login_window  # 存储对登录窗口的引用

        self.init_ui()

    def init_ui(self):
        self.username_label = QLabel('用户名 (仅数字)：')
        self.username_entry = QLineEdit()
        self.password_label = QLabel('密码：')
        self.password_entry = QLineEdit()
        self.password_entry.setEchoMode(QLineEdit.Password)
        self.password_confirm_label = QLabel('重复密码：')
        self.password_confirm_entry = QLineEdit()
        self.password_confirm_entry.setEchoMode(QLineEdit.Password)

        self.register_button = QPushButton('注册')
        self.register_button.clicked.connect(self.register)

        layout = QVBoxLayout()
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_entry)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_entry)
        layout.addWidget(self.password_confirm_label)
        layout.addWidget(self.password_confirm_entry)
        layout.addWidget(self.register_button)
        self.setLayout(layout)
        self.setWindowTitle('Register')

    def register(self):
        username = self.username_entry.text()
        password = self.password_entry.text()
        password_confirm = self.password_confirm_entry.text()

        if username.isdigit() and password == password_confirm:
            try:
                self.db.connect()
                self.db.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, password))
                self.db.close()
                QMessageBox.information(self, 'Success', '注册成功!')
                self.close()
                self.login_window.show()  # 展示登录窗口
            except pymysql.err.IntegrityError:
                QMessageBox.warning(self, 'Error', '已经被注册!')
        else:
            QMessageBox.warning(self, 'Error', '注册失败，请检查你的输入。')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    db = MySQLConnection('127.0.0.1', 'root', '123456', 'test')
    login_window = LoginWindow(db)
    login_window.show()

    sys.exit(app.exec_())

""" sql
CREATE TABLE users (
    username VARCHAR(20) PRIMARY KEY,
    password VARCHAR(50) NOT NULL
);
"""

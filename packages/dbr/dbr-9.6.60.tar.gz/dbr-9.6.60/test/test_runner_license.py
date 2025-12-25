import unittest
import platform
#from test_cases import dbr_general_api_test, decode_specific_barcode_test, decode_with_different_settings_test, ticket_test, license_test
from test_cases import license_test
from HTMLTestRunner import HTMLTestRunner
import time
from ftplib import FTP
import sys
import os

system = platform.system()
arch = platform.machine()
system_env = f"{system}({arch})".lower()
REPORT_UPLOAD_PATH = "/Copyinout/Jane/PythonTestReports"
UPLOAD_REPORT = False


def get_current_timestamp():
    ts = int(time.time())
    return time.strftime('%Y%m%d%H%M%S')


def upload_report(local_path: str, report_name: str):
    ftp = FTP()
    ftp.connect(host="117.148.176.45")
    ftp.login()
    ftp.set_debuglevel(2)
    print(ftp.getwelcome())
    ftp.cwd(REPORT_UPLOAD_PATH)
    buffer_size = 1024
    with open(local_path, "rb") as f:
        ftp.storbinary(f"STOR {report_name}", f, buffer_size)
        ftp.set_debuglevel(0)
    ftp.quit()


if __name__ == '__main__':
    suite = unittest.TestSuite()

    #suite = unittest.TestSuite()
    #suite.addTest(MyTest('test_example2'))  # 选择要运行的测试函数
    #unittest.TextTestRunner(verbosity=2).run(suite)
    test_suit = [
                #unittest.TestLoader().loadTestsFromTestCase(decode_specific_barcode_test.DecodeSpecificBarcodeTest),
                 #unittest.TestLoader().loadTestsFromTestCase(dbr_general_api_test.DBRGeneralApiTest),
                 #unittest.TestLoader().loadTestsFromTestCase(decode_with_different_settings_test.DecodeWithDifferentSettingsTest),
                 #unittest.TestLoader().loadTestsFromTestCase(ticket_test.TicketTest),
                 unittest.TestLoader().loadTestsFromTestCase(license_test.LicenseTest),
                 ]
    suite.addTests(test_suit)
    python_version = f"{sys.version_info.major}{sys.version_info.minor}"
    timestamp = get_current_timestamp()
    report_name = f"report_{system_env}_{python_version}_{timestamp}.html"
    report = f"reports/{report_name}"
    if not os.path.exists("./reports"):
        os.mkdir("./reports")
    with open(report, "wb") as f:
        runner = HTMLTestRunner(stream=f,
                                verbosity=2,
                                tester="Andrew",
                                title="DBR-Python test report",
                                description="The test result for test case.")
        runner.run(suite)
    # upload the test report
    if UPLOAD_REPORT:
        upload_report(report, report_name)


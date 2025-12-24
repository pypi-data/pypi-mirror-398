import requests as _requests
from urllib.parse import urlparse, parse_qs
from . import config as _config
from PySide6.QtCore import QUrl, Signal
from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineQuick import QQuickWebEngineProfile
import os


os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--disable-gpu --disable-software-rasterizer'
os.environ["QT_OPENGL"] = "software"
os.environ["QT_QUICK_BACKEND"] = "software"

_result_resp = None
_resp_cookies = None


def get_param_from_url(url, param_name):
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    if param_name in query_params:
        return query_params[param_name][0]
    else:
        return None


def get_base_url(full_url):
    parsed_url = urlparse(full_url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    return base_url


class _WebEnginePage(QWebEnginePage):
    stop_signal = Signal(bool)

    def __init__(self, verify, proxies, headers, orig_resp_cookies):
        super().__init__()
        self.verify = verify
        self.proxies = proxies
        self.headers = headers
        self.orig_resp_cookies = orig_resp_cookies

    def getRedirectUrl(self, resp, request_url):
        location_url = resp.headers.get('Location')
        redirect_url = location_url
        if not location_url.startswith("http"):
            redirect_url = get_base_url(request_url) + location_url
        return redirect_url

    def acceptNavigationRequest(self, url, _type, isMainFrame):
        global _result_resp
        global _resp_cookies
        request_url = url.toString()
        if _config.API_CONFIG['ENABLE_CODE_FLOW_LOGS'] == 1:
            print("Received request_url=" + str(request_url))
        authorization_code = get_param_from_url(request_url, "code")
        if authorization_code:
            resp1 = _requests.get(url=request_url,
                                  cookies=self.orig_resp_cookies,
                                  headers=self.headers,
                                  stream=True,
                                  proxies=self.proxies,
                                  verify=self.verify,
                                  allow_redirects=False)
            _result_resp = resp1
            if resp1.is_redirect:
                redirect_url = self.getRedirectUrl(resp1, request_url)
                initial_query = redirect_url
                if resp1.status_code == 301:
                    if _config.API_CONFIG['ENABLE_CODE_FLOW_LOGS'] == 1:
                        print("301 redirect url=" + str(redirect_url))
                    resp1 = _requests.get(url=redirect_url,
                                          cookies=self.orig_resp_cookies,
                                          headers=self.headers,
                                          stream=True,
                                          proxies=self.proxies,
                                          verify=self.verify,
                                          allow_redirects=False)
                    initial_query = self.getRedirectUrl(resp1, redirect_url)
                if resp1.status_code == 303:
                    if _config.API_CONFIG['ENABLE_CODE_FLOW_LOGS'] == 1:
                        print("303 redirect url=" + str(initial_query))
                        print("302 response cookies=" + str(resp1.cookies))
                    resp2 = _requests.get(url=initial_query,
                                      cookies=resp1.cookies,
                                      headers=self.headers,
                                      stream=True,
                                      proxies=self.proxies,
                                      verify=self.verify)
                    _result_resp = resp2
                    _resp_cookies = resp1.cookies
            self.stop_signal.emit(True)
            return False
        return QWebEnginePage.acceptNavigationRequest(self, url, _type, isMainFrame)


def _stop_application():
    QApplication.quit()


def _open_qt_window(idp_auth_url, verify, proxies, headers, orig_resp_cookies):
    if not QApplication.instance():
        app = QApplication([])
    else:
        app = QApplication.instance()

    default_profile = QQuickWebEngineProfile.defaultProfile()
    default_profile.setPersistentCookiesPolicy(QQuickWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
    default_profile.setOffTheRecord(False)
    default_profile.setStorageName("Default")
    cache_dir = default_profile.persistentStoragePath() + "/Cache"
    default_profile.setCachePath(cache_dir)

    if _config.API_CONFIG['ENABLE_CODE_FLOW_LOGS'] == 1:
        print("Default cache directory=" + cache_dir)

    page = _WebEnginePage(verify, proxies, headers, orig_resp_cookies)
    page.stop_signal.connect(_stop_application)

    view = QWebEngineView()
    view.setPage(page)
    view.setUrl(QUrl(idp_auth_url))
    view.setWindowTitle("Login Page")
    view.show()
    app.exec_()


def get_code_flow_data_results(resp, headers, verify, proxies):
    global _result_resp
    global _resp_cookies
    idp_auth_url = resp.headers.get('Location')
    _open_qt_window(idp_auth_url, verify, proxies, headers, resp.cookies)
    return _result_resp, _resp_cookies

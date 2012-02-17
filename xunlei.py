#coding=utf-8
try:
    import gevent
    from gevent import monkey
    monkey.patch_all()
except ImportError:
    gevent = None

import mechanize
import time
import urllib
import os
from BeautifulSoup import BeautifulSoup
from StringIO import StringIO
import sys
import copy


def get_cache():
    """Generate cache string"""
    return str(int(time.time()*1000))

def filesizeformat(bytes):
    """
    Formats the value like a 'human-readable' file size (i.e. 13 KB, 4.1 MB,
    102 bytes, etc).
    """
    try:
        bytes = float(bytes)
    except (TypeError,ValueError,UnicodeDecodeError):
        return "%(size)d byte" % {'size': 0}

    filesize_number_format = lambda value: round(value, 1)

    if bytes < 1024:
        return "%(size)d bytes" % {'size': bytes}
    if bytes < 1024 * 1024:
        return "%s KB" % filesize_number_format(bytes / 1024)
    if bytes < 1024 * 1024 * 1024:
        return "%s MB" % filesize_number_format(bytes / (1024 * 1024))
    if bytes < 1024 * 1024 * 1024 * 1024:
        return "%s GB" % filesize_number_format(bytes / (1024 * 1024 * 1024))
    if bytes < 1024 * 1024 * 1024 * 1024 * 1024:
        return "%s TB" % filesize_number_format(bytes / (1024 * 1024 * 1024 * 1024))
    return "%s PB" % filesize_number_format(bytes / (1024 * 1024 * 1024 * 1024 * 1024))

def display_progress_bar(filename, size):
    """Display progress bar while downloading"""
    size = long(size)
    from gevent.greenlet import LinkedExited
    width = 32
    last_size = 0
    try:
        while True:
            if os.path.isfile(filename):
                current_size = os.path.getsize(filename)
                percentage = current_size*100/size
                current_width = width*percentage/100
                sys.stderr.write('% 3d%% [%s%s] %s/s    \r' % (percentage, '#'*current_width, ' '*(width-current_width), filesizeformat(current_size - last_size)))
                last_size = current_size
            time.sleep(1)
    except LinkedExited:
        sys.stderr.write('100%% [%s]\n' % ('#'*width))


class Xunlei(object):
    """Xunlei API wrapper"""
    def __init__(self, username, password, cookie_file, debug=False, 
            user_agent= ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_5) '
            'AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.218 Safari/535.1')):
        self.username = username
        self.password = password
        self.cookie_file = cookie_file
        self.debug = debug
        self.user_agent = user_agent
        self.browser = None

    def get_browser(self):
        """Browser object response for load cookie and save cookie"""
        if self.browser:
            return self.browser
        else:
            browser = mechanize.UserAgent()
            browser.set_handle_equiv(False)
            browser.set_handle_gzip(False)
            browser.set_handle_redirect(True)
            browser.set_handle_robots(False)
            browser.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
            browser.set_seekable_responses(False)
            if self.debug:
                browser.set_debug_http(True)
                browser.set_debug_redirects(True)
                browser.set_debug_responses(True)
            cj = mechanize.LWPCookieJar()
            try:
                cj.load(self.cookie_file, ignore_discard=True, ignore_expires=True)
            except IOError:
                pass
            browser.set_cookiejar(cj)
            browser.addheaders = [
                ('User-agent', self.user_agent),
            ]
            self.browser = browser
            return self.browser

    def get_cookie_string(self, url):
        """Get cookie string for a given url"""
        br = self.get_browser()
        r = mechanize.Request(url)
        cookies = br._ua_handlers['_cookies'].cookiejar.cookies_for_request(r)
        attrs = br._ua_handlers['_cookies'].cookiejar._cookie_attrs(cookies)
        return "; ".join(attrs)

    def request(self, url, data=None):
        """Request a page from xunlei"""
        br = self.get_browser()
        if self.get_dashboard_url():
            br.addheaders.append(('Referer', self.get_dashboard_url()))
        if data:
            data = urllib.urlencode(data)
        response = br.open(url, data)
        br._ua_handlers['_cookies'].cookiejar.save(self.cookie_file, ignore_discard=True, ignore_expires=True)
        return response

    def login(self):
        """Login into xunlei lixian"""
        def get_password(password, verify_code):
            """docstring for get_password"""
            try:
                from hashlib import md5
            except ImportError:
                from md5 import md5

            m = md5()
            m.update(password)
            md5pwd = m.hexdigest()
            m = md5()
            m.update(md5pwd)
            md5pwd = m.hexdigest()
            m = md5()
            m.update(md5pwd + verify_code)
            md5pwd = m.hexdigest()
            return md5pwd

        response = self.request('http://login.xunlei.com/check?u=%s&cachetime=%s' % (self.username, get_cache()))
        br = self.get_browser()
        check_result = br._ua_handlers['_cookies'].cookiejar._cookies['.xunlei.com']['/']['check_result'].value
        verify_code = check_result.split(':')[1]
        encrypt_password = get_password(self.password, verify_code)
        data = {
            'u':self.username,
            'p':encrypt_password,
            'verifycode':verify_code,
            'login_enable':'1',
            'login_hour':'720',
        }
        response = self.request('http://login.xunlei.com/sec2login/', data)
        cache = get_cache()
        response = self.request('http://dynamic.lixian.vip.xunlei.com/login?cachetime=%s&cachetime=%s&from=0' % (cache, str(int(cache)+133)))
        return response

    def get_user_id(self):
        br = self.get_browser()
        try:
            user_id = br._ua_handlers['_cookies'].cookiejar._cookies['.xunlei.com']['/']['userid'].value
            return user_id
        except KeyError:
            return None

    def get_dashboard_url(self):
        if self.get_user_id():
            url = 'http://dynamic.cloud.vip.xunlei.com/user_task?userid=%s&st=0' % self.get_user_id()
            return url
        else:
            return None

    def dashboard(self):
        """Get dashboard tasks list"""
        br = self.get_browser()
        if self.get_dashboard_url():
            response = self.request(self.get_dashboard_url())
            page = BeautifulSoup(response.read())
            if not page.find('input', attrs={'id':'cok'}):
                self.login()
                response = self.request(self.get_dashboard_url())
                page = BeautifulSoup(response.read())
        else:
            self.login()
            response = self.request(self.get_dashboard_url())
            page = BeautifulSoup(response.read())
        cok = page.find('input', attrs={'id':'cok'}).get('value')
        cok_cookie = mechanize.Cookie(version=0, name='gdriveid', value=cok, port=None, port_specified=False, domain='.vip.xunlei.com', domain_specified=False, domain_initial_dot=True, path='/', path_specified=True, secure=False, expires=int(time.time()+3600*24*7), discard=True, comment=None, comment_url=None, rest={}, rfc2109=False)
        br._ua_handlers['_cookies'].cookiejar.set_cookie(cok_cookie)
        br._ua_handlers['_cookies'].cookiejar.save(self.cookie_file, ignore_discard=True, ignore_expires=True)
        raw_items = page.findAll('div', attrs={'class':'rw_list'})
        items = []
        for raw_item in raw_items:
            item = {}
            item['id'] = raw_item.get('taskid')
            item['type'] = raw_item.find('input',attrs={'id':'d_tasktype%s' % item['id']}).get('value')
            item['status'] = raw_item.find('input',attrs={'id':'d_status%s' % item['id']}).get('value')
            item['size'] = int(raw_item.find('input',attrs={'id':'ysfilesize%s' % item['id']}).get('value'))
            item['name'] = raw_item.find('input',attrs={'id':'taskname%s' % item['id']}).get('value')
            item['download_url'] = raw_item.find('input',attrs={'id':'dl_url%s' % item['id']}).get('value')
            item['bt_download_url'] = raw_item.find('input',attrs={'id':'bt_down_url%s' % item['id']}).get('value')
            items.append(item)
        return items

    def list_bt(self, url, task_id):
        """List files in a bittorrent task"""
        try:
            import json
        except:
            import simplejson as json

        br = self.get_browser()
        response = self.request('http://dynamic.cloud.vip.xunlei.com/interface/fill_bt_list?callback=fill_bt_list&tid=%s&infoid=%s&g_net=1&p=1&uid=%s&noCacheIE=%s' % (task_id, url[5:], self.get_user_id(), get_cache()))
        stream = StringIO(response.read()[13:-1])
        result = json.load(stream)
        return result['Result']['Record']

    def download(self, url, filename):
        """Download file from a task"""
        def append_file(filename, *args, **kwargs):
            return open(filename, 'ab')

        br = self.get_browser()
        if os.path.isfile(filename):
            addheaders = copy.copy(br.addheaders)
            br.addheaders.append(('Range', "bytes=%s-" % os.path.getsize(filename)))
            br.retrieve(url, filename, open=append_file)
            br.addheaders = addheaders
        else:
            br.retrieve(url, filename)
    
    def smart_download(self, url, filename, size):
        """Download task with resume"""
        if os.path.isfile(filename):
            done = os.path.getsize(filename) == int(size)
        else:
            done = False
        retry = 0
        while not done:
            print 'Start Download: %s (%s)' % (filename, size)
            try:
                if gevent:
                    download = gevent.spawn(self.download, url=url, filename=filename)
                    update_progress = gevent.spawn(display_progress_bar, filename=filename, size=size)
                    download.link(update_progress)
                    gevent.joinall([download, update_progress])
                else:
                    self.download(url, filename)
            except Exception, e:
                print e
            print 'End Download: %s' % filename
            if os.path.getsize(filename) == int(size):
                done = True
            else:
                print 'Size does not match. Try resuming download.'
                retry += 1
            if retry > 100:
                print 'Reached maximum retry limit.'
                done = True

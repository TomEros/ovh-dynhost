#
# Steven MARTINS <steven.martins.fr@gmail.com>
# -*- encoding: utf-8 -*-
#

import logging, requests, re, json, sys, os, string, time, hashlib

try:
    from ConfigParser import ConfigParser, Error, NoOptionError
except:
    from configparser import ConfigParser, Error, NoOptionError

from requests.exceptions import RequestException

try:
    from urllib import urlencode
except:
    from urllib.parse import urlencode

logging.basicConfig(level=logging.INFO,format="%(asctime)-15s:%(levelname)s:%(threadName)s: %(message)s")
log = logging.getLogger("net")

class Conf:
    def __init__(self, filename):
        self._filename = filename
        try:
            self._config = ConfigParser(strict=False)
        except:
            self._config = ConfigParser()
        try:
            self._config.read(os.path.expanduser(filename))
        except Exception as e:
            logging.error("[Conf]" + self._filename + ": " + str(e))
            raise Exception("Error during loading file " + self._filename)

    def getSection(self, section):
        data={}
        try:
            if section in self._config.sections():
                for name, value in self._config.items(section):
                    data[name] = value
        except Exception as e:
            logging.error("[Conf]" + self._filename + ": " + str(e))
        for key, value in data.items():
            if ", " in value:
                data[key] = value.split(", ")
        return data

    def get(self, section, option, default=""):
        val = default
        try:
            val = self._config.get(section, option)
        except:
            val = default
        if ", " in val:
            return val.split(", ")
        return default

    def sections(self):
        return self._config.sections()

    def setSection(self, section, values):
        if not self._config.has_section(section):
            self._config.add_section(section)
        for k, v in values.items():
            self._config.set(section, k, v)

    def setValue(self, section, option, value):
        if not self._config.has_section(section):
            self._config.add_section(section)
        self._config.set(section, option, value)

    def removeSection(self, section):
        if self._config.has_section(section):
            self._config.remove_section(section)

    def removeValue(self, section, option):
        if self._config.has_section(section) and self._config.has_option(section, option):
            self._config.remove_option(section, option)

    def save(self):
        with open(self._filename, 'w') as f:
            self._config.write(f)

    def getAll(self):
        data = {}
        for section in self.sections():
            data[section] = self.getSection(section)
        return data


class net(object):
    def __init__(self):
        self._urls = [
            ("https://nsupdate.info/myip", "_simple"),
            ("http://jsonip.com/", "_json"),
            ("http://checkip.dns.he.net/", "_regex")
            ]

    def _simple(self, text):
        try:
            return str(text.strip())
        except ValueError as e:
            log.warning("Unable to parse '%s'" % text)
        return None

    def _regex(self, text, pattern="[0-9]+(?:\.[0-9]+){3}"):
        try:
            ips = re.findall(pattern, text)
            log.debug("_regex: %s" % str(ips))
        except ValueError as e:
            log.warning("Unable to parse '%s'" % text)
        return None
 
    def _json(self, text, field="ip"):
        try:
            j = json.loads(text)
            return j.get(field)
        except Exception as e:
            log.warning("Unable to parse '%s'" % text)
        return None

    def _get(self, url, timeout=10):
        log.debug("_get: %s" % url)
        try:
            r = requests.get(url, timeout=timeout)
        except Exception as e:
            log.warning("Unable to get '%s': %s" % (url, str(e)))
            return None
        if r.status_code == 200:
            return (r.text)
        log.warning("_get: bad status_code: %s" % (r.status_code))
        return None
        
    def getIP(self):
        for (url, parser) in self._urls:
            value = self._get(url)
            if value:
                try:
                    f = getattr(self, parser)
                    res = f(value)
                    log.debug("[%s] > %s" % (url, res))
                    return res
                except Exception as e:
                    log.warning("Parse error '%s': %s" % (url, str(e)))
        return None

class local(object):
    def __init__(self, filepath="~", filename=".myip"):
        self._filepath = os.path.expanduser(filepath)
        self._filename = filename

    def load(self):
        datas = None
        try:
            with open(os.path.join(self._filepath, self._filename), "r") as f:
                datas = json.loads(f.read())
        except Exception as e:
            log.warning("local: Unable to load file %s : %s" % (self._filename, str(e)))
        return datas

    def save(self, datas):
        try:
            datas = json.dumps(datas)
            with open(os.path.join(self._filepath, self._filename), "w") as f:
                f.write(datas)
        except Exception as e:
            log.warning("local: Unable to write file %s : %s" % (self._filename, str(e)))

class api(object):
    def __init__(self):
        self._end_point = "https://eu.api.ovh.com/1.0"
        self._conf = None
        for conffile in ("dynhost.conf","~/dynhost.conf"):
            try:
                self._conf = Conf(os.path.expanduser(conffile))
                break
            except Exception as e:
                log.warning("Conf error: %s" % str(e))
                pass
        if not self._conf:
            raise Exception("Unable to load dynhost.conf configuration file.")
        self._session = requests.Session()
        c = self._conf.getSection("credentials")
        if not c or len(c) == 0:
            raise Exception("No Credentials available on configuration file.")
        self._application_key = c["application_key"] if "application_key" in c else None
        self._application_secret = c["application_secret"] if "application_secret" in c else None
        self._consumer_key = c["consumer_key"] if "consumer_key" in c else None
        if not self._application_key:
            raise Exception("No application key")
        if not self._application_secret:
            raise Exception("No application secret")

        server_time = self.get('/auth/time', need_auth=False)
        log.debug("server_time: %s" % str(server_time))
        self._time_delta = server_time - int(time.time())


    def _req(self, method, url, datas=None, need_auth=True):
        headers = {
            'X-Ovh-Application': self._application_key
        }
        _url = "%s%s" % (self._end_point, url)
        body = ""
        if datas:
            headers['Content-type'] = 'application/json'
            body = json.dumps(datas)
        if need_auth:
            if not self._consumer_key:
                log.warning("auth needed without consumer key")
                return None
            now = str(int(time.time()) + self._time_delta)
            sign = "+".join([
                        self._application_secret, self._consumer_key,
                        method.upper(), _url,
                        body,
                        now
                        ]).encode('utf-8')
            log.debug("sign: %s" % (sign))
            signature = hashlib.sha1(sign)
            headers['X-Ovh-Consumer'] = self._consumer_key
            headers['X-Ovh-Timestamp'] = now
            headers['X-Ovh-Signature'] = "$1$" + signature.hexdigest()
        try:
            result = self._session.request(method, _url, headers=headers,
                                           data=body)
            log.debug("%s %s > %s %s" % (method, _url, result.status_code, result.text))
            log.debug("header: %s, datas: %s" % (headers, body))
        except Exception as e:
            log.warning("Request: %s, error: %s " % (_url, str(e)))
            return None
        if result.status_code == 200:
            try:
                return result.json()
            except Exception as e:
                log.warning("Unable to decode json from ovh api: %s" % str(e))
        log.warning("Wrong status_code: %s %s" % (_url, result.status_code))
        if result.status_code == 403:
            raise Exception("Unauthorized %s" % str(_url))
        if result.status_code == 400:
            raise Exception("BadRequest %s" % str(_url))
        return None

    def get(self, url, datas=None, need_auth=True):
        _url = url
        if datas:
            _url = "%s?%s" % (url, urlencode(datas))
        return self._req("GET", _url, None, need_auth)

    def post(self, url, datas={}, need_auth=True):
        return self._req("POST", url, datas, need_auth)

    def put(self, url, datas={}, need_auth=True):
        return self._req("PUT", url, datas, need_auth)

    def authenticate(self):
        access_rules = [
            {'method': 'GET', 'path': '/domain/*'},
            {'method': 'PUT', 'path': '/domain/zone/*'}, # update a subdomain
            {'method': 'POST', 'path': '/domain/zone/*'}, # create new subdomain
        ]
        res = self.post('/auth/credential', need_auth=False,
                        datas={"accessRules":access_rules,"redirection":None})
        self._consumer_key = res['consumerKey']
        self._conf.setValue("credentials", "consumer_key", self._consumer_key)
        self._conf.save()
        return res

    def updateHost(self, ip, create=True):
        conf = self._conf.getSection("zone")
        ttl = int(conf["ttl"]) if "ttl" in conf else 60 
        if not conf:
            raise Exception("zone not configured")
        if not "subdomain" in conf:
            raise Exception("subdomain field missing in 'zone'")
        if not "domain" in conf:
            raise Exception("domain field missing in 'zone'")
        domain = conf["domain"]
        subd = conf["subdomain"]
        o = self.get("/domain/zone/%s/record" % (domain), {"subDomain": subd})
        if not o or len(o) == 0:
            if create:
                res = self.post("/domain/zone/%s/record" % (domain), {"target": ip, 
                                                                "ttl": ttl, 
                                                                "subDomain": subd, 
                                                                "fieldType": "A" if ip.count('.') == 3 else "AAAA"})
            else:
                raise Exception("Unable to find %s.%s on Ovh's API" % (subd, domain))
        else:
            res = self.put("/domain/zone/%s/record/%s" %(domain, o[0]), {"target": ip, "ttl": ttl, "subDomain": subd})
        log.debug("updateHost: result: %s" % str(res))


def main():
    n = net()
    ip = n.getIP()
    if not ip:
        log.error("Unable to get your ip. Are you connected to internet ?")
        sys.stderr.write("Unable to get your ip. Are you connected to internet ?\n")
    l = local()
    store = l.load()
    if store and "ip" in store and store["ip"] == ip:
        log.info("Your ip is the same since last check. Nothing to do.")
        return 
    log.info("Your ip changed to %s" % (ip))
    a = api()
    if not a.get("/domain/zone"):
        res = a.authenticate()
        sys.stderr.write("Please visit this address to authenticate the script: %s\n" % str(res["validationUrl"]))
        return
    try:
        a.updateHost(ip)
        l.save({"ip": ip})
        print("Update OK")
    except Exception as e:
        log.error("Update fail: %s" % (str(e)))
        sys.stderr.write("Error: %s\n" % (str(e)))

if __name__=="__main__":
    main()

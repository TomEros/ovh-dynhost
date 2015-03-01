#
# Steven MARTINS <steven.martins.fr@gmail.com>
#

import logging, requests, re, json, sys, os

logging.basicConfig(level=logging.DEBUG,format="%(asctime)-15s:%(levelname)s:%(threadName)s: %(message)s")
log = logging.getLogger("net")


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
    def __init__(self, filepath=".", filename=".myip"):
        self._filepath = filepath
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
        pass


def main():
    n = net()
    ip = n.getIP()
    if not ip:
        log.error("Unable to get your ip. Are you connected to internet ?")
        sys.stderr.write("Unable to get your ip. Are you connected to internet ?")
    l = local()
    store = l.load()
    if store and "ip" in store and store["ip"] == ip:
        log.info("Your ip is the same since last check. Nothing to do.")
        return 
    log.info("Your ip changed to %s" % (ip))
    a = api()
    
    l.save({"ip": ip})
    # getIP
    # is changed?
    #  if yes : call ovh api, then update .last_ip file




if __name__=="__main__":
    main()

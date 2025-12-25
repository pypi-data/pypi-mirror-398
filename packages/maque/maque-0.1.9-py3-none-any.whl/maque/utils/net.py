import socket
import re


def get_inner_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(('8.8.8.8', 80))
        return s.getsockname()[0]


def get_outer_ip():
    import requests
    # headers = {
    #     'User-Agent':
    #     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36"
    # }
    # return requests.get('http://ip.42.pl/raw', headers=headers).text.strip()
    return requests.get('http://ifconfig.me/ip', timeout=1).text.strip()


def get_ip(env="inner"):
    """Get in-net / out-ner ip address.
    env: "inner" or "outer"
    """
    if env == "inner":
        return get_inner_ip()
    elif env == "outer":
        return get_outer_ip()
    else:
        raise ValueError("`env` invalid!")


def domain2ip(*domains):
    domain_ip = [(domain, socket.gethostbyname(domain.strip())) for domain in domains]
    return domain_ip


def get_github_ip():
    import requests
    def get_ip(website):
        request = requests.get('https://ipaddress.com/website/' + website)
        domain_ip = None
        if request.status_code == 200:
            ips = re.findall(r"<strong>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}?)</strong>", request.text)
            domain_ip = {ip for ip in ips}
        return domain_ip

    ip_list = ['github.com',
               'github.global.ssl.fastly.net',
               'assets-cdn.github.com',
               # 'codeload.github.com',
               # 'google.com'
               ]
    return [[i, get_ip(i)] for i in ip_list]


# getip('assets-cdn.github.com')
# getip('github.global.ssl.fastly.net')

if __name__ == "__main__":
    print(get_inner_ip())
    print(get_outer_ip())
    print(domain2ip("www.baidu.com", "www.google.com", "github.com"))
    # print(get_github_ip())

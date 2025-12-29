import os

def lpath(*dirs):
    """将 dirs 中的文件名连接成路径"""
    path = os.path.join(*dirs)
    path = os.path.abspath(path).replace('\\', '/')
    return path

www_root = lpath('/var/www/ryweb')
app_dir = lpath(www_root, 'app')
web_dir = lpath(www_root, 'web')
cfg_dir = lpath(www_root, 'cfg')
psql_dir = lpath(www_root, 'psql')
adb_dir = lpath(www_root, 'adb')
sfs_dir = lpath(www_root, 'sfs')
ssl_dir = lpath(www_root, 'ssl')
env_dir = lpath(www_root, 'env')
code_dir = lpath(www_root, 'code')
nginx_cfg_dir = lpath(www_root, 'cfg', 'nginx')
nginx_host_dir = lpath(www_root, 'cfg', 'nginx', 'vhost')
nginx_logs_dir = lpath(www_root, 'cfg', 'nginx', 'logs')
nginx_body_dir = lpath(www_root, 'cfg', 'nginx', 'temp', 'client_body_temp')
nginx_proxy_dir = lpath(www_root, 'cfg', 'nginx', 'temp', 'proxy_temp')
nginx_fastcgi_dir = lpath(www_root, 'cfg', 'nginx', 'temp', 'fastcgi_temp')
nginx_uwsgi_dir = lpath(www_root, 'cfg', 'nginx', 'temp', 'uwsgi_temp')
nginx_scgi_dir = lpath(www_root, 'cfg', 'nginx', 'temp', 'scgi_temp')
adb_logs_dir = lpath(www_root, 'adb', 'logs')
adb_data_dir = lpath(www_root, 'adb', 'data')
adb_apps_dir = lpath(www_root, 'adb', 'apps')

proxy_port = 8899
www_user = 'ryweb'
env_name = 'ryweb'
py_ver = '3.10'
run_mode = 'nfp'
app_list = {
    'np': ['nginx', 'php', 'certbot'],
    'npp': ['nginx', 'php', 'postgresql', 'certbot'],
    'nf': ['nginx', 'fastapi', 'certbot'],
    'nfp': ['nginx', 'postgresql', 'fastapi', 'certbot'],
    'nfpc': ['nginx', 'postgresql', 'conda', 'fastapi', 'certbot'],
    'nfas': ['nginx', 'arangodb', 'seaweedfs', 'fastapi', 'certbot'],
    'nfasc': ['nginx', 'arangodb', 'seaweedfs', 'conda', 'fastapi', 'certbot']
}
apps = app_list[run_mode]

nginx_ver = '1.28.0'
#nginx_pkg_lin = 'https://nginx.org/download/nginx-1.28.0.tar.gz'
#nginx_pkg_win = 'https://nginx.org/download/nginx-1.28.0.zip'
nginx_pkg_lin = 'http://rymaa.cn/download/nginx-1.28.0.tar.gz'
nginx_pkg_win = 'http://rymaa.cn/download/nginx-1.28.0.zip'

postgresql_ver = '16.11'
postgresql_lin = ''
postgresql_deb = ''
postgresql_rpm = ''
# vers: 18.1-1, 17.7-1, 16.11-1, 15.15-1, 14.20-1, 13.23-1, 11.21-1
postgresql_mac = 'https://get.enterprisedb.com/postgresql/postgresql-16.11-1-osx-binaries.zip'
#postgresql_mac = 'http://rymaa.cn/download/postgresql-16.11-1-osx-binaries.zip'

# vers: 18.1-1, 17.7-1, 16.11-1, 15.15-1, 14.20-1, 13.23-1, 11.21-1
postgresql_win = 'https://get.enterprisedb.com/postgresql/postgresql-16.11-1-windows-x64-binaries.zip'
#postgresql_win = 'http://rymaa.cn/download/postgresql-16.11-1-windows-x64-binaries.zip'

arangodb_ver = '3.11.0'
arangodb_pkg_lin = ''
#arangodb_pkg_deb = 'https://download.arangodb.com/arangodb311/DEBIAN/amd64/arangodb3_3.11.0-1_amd64.deb'
arangodb_pkg_deb = 'http://rymaa.cn/download/arangodb3_3.11.0-1_amd64.deb'
#arangodb_pkg_rpm = 'https://download.arangodb.com/arangodb311/RPM/x86_64/arangodb3-3.11.0-1.0.x86_64.rpm'
arangodb_pkg_rpm = 'http://rymaa.cn/download/arangodb3-3.11.0-1.0.x86_64.rpm'
#arangodb_pkg_mac = 'https://download.arangodb.com/arangodb311/Community/MacOSX/arangodb3-3.11.0.x86_64.dmg'
arangodb_pkg_mac = 'http://rymaa.cn/download/arangodb3-3.11.0.x86_64.dmg'
#arangodb_pkg_win = 'https://download.arangodb.com/arangodb311/Community/Windows/ArangoDB3-3.11.0_win64.exe'
arangodb_pkg_win = 'http://rymaa.cn/download/ArangoDB3-3.11.0_win64.exe'

seaweedfs_ver = '3.96'
#seaweedfs_pkg_lin = 'https://sourceforge.net/projects/seaweedfs.mirror/files/3.96/linux_amd64.tar.gz'
#seaweedfs_pkg_mac = 'https://sourceforge.net/projects/seaweedfs.mirror/files/3.96/darwin_amd64.tar.gz'
#seaweedfs_pkg_win = 'https://sourceforge.net/projects/seaweedfs.mirror/files/3.96/windows_amd64.zip'
seaweedfs_pkg_lin = 'http://rymaa.cn/download/seaweedfs-3.96_linux_amd64.tar.gz'
seaweedfs_pkg_mac = 'http://rymaa.cn/download/seaweedfs-3.96_darwin_amd64.tar.gz'
seaweedfs_pkg_win = 'http://rymaa.cn/download/seaweedfs-3.96_windows_amd64.zip'

conda_ver = '25.1.1'
#conda_pkg_lin = 'https://repo.anaconda.com/miniconda/Miniconda3-py310_25.1.1-2-Linux-x86_64.sh'
conda_pkg_lin = 'http://rymaa.cn/download/Miniconda3-py310_25.1.1-2-Linux-x86_64.sh'
#conda_pkg_mac = 'https://repo.anaconda.com/miniconda/Miniconda3-py310_25.1.1-2-MacOSX-x86_64.sh'
conda_pkg_mac = 'http://rymaa.cn/download/Miniconda3-py310_25.1.1-2-MacOSX-x86_64.sh'
#conda_pkg_win = 'https://repo.anaconda.com/miniconda/Miniconda3-py310_25.1.1-2-Windows-x86_64.exe'
conda_pkg_win = 'http://rymaa.cn/download/Miniconda3-py310_25.1.1-2-Windows-x86_64.exe'

php_ver = '8.3.28'
# vers: php-8.4.14.tar.gz, php-8.3.26.tar.gz, php-8.2.28.tar.gz, php-8.1.31.tar.gz
php_pkg_lin = 'https://www.php.net/distributions/php-8.3.26.tar.gz'
php_pkg_mac = 'https://www.php.net/distributions/php-8.3.26.tar.gz'
# vers: php-8.5.0-nts-Win32-vs17-x64.zip, php-8.4.15-nts-Win32-vs17-x64.zip, php-8.3.28-nts-Win32-vs16-x64.zip, php-8.2.29-nts-Win32-vs16-x64.zip
#php_pkg_win = 'https://windows.php.net/downloads/releases/php-8.3.28-nts-Win32-vs16-x64.zip'
php_pkg_win = 'http://rymaa.cn/download/php-8.3.28-nts-Win32-vs16-x64.zip'

certbot_ver = '5.1.0'
certbot_pkg_lin = 'http://rymaa.cn/download/certbot-5.1.0.tar.gz'
certbot_pkg_mac = 'http://rymaa.cn/download/certbot-5.1.0.tar.gz'
certbot_pkg_win = 'http://rymaa.cn/download/certbot-5.1.0.tar.gz'

# mime types
mime_types = r"""
types {
    text/html                             html htm shtml;
    text/css                              css;
    text/xml                              xml;
    image/gif                             gif;
    image/jpeg                            jpeg jpg;
    application/javascript                js;
    application/atom+xml                  atom;
    application/rss+xml                   rss;

    text/mathml                           mml;
    text/plain                            txt;
    text/vnd.sun.j2me.app-descriptor      jad;
    text/vnd.wap.wml                      wml;
    text/x-component                      htc;

    image/png                             png;
    image/tiff                            tif tiff;
    image/vnd.wap.wbmp                    wbmp;
    image/x-icon                          ico;
    image/x-jng                           jng;
    image/x-ms-bmp                        bmp;
    image/svg+xml                         svg svgz;
    image/webp                            webp;

    application/font-woff                 woff;
    application/java-archive              jar war ear;
    application/json                      json;
    application/mac-binhex40              hqx;
    application/msword                    doc;
    application/pdf                       pdf;
    application/postscript                ps eps ai;
    application/rtf                       rtf;
    application/vnd.apple.mpegurl         m3u8;
    application/vnd.ms-excel              xls;
    application/vnd.ms-fontobject         eot;
    application/vnd.ms-powerpoint         ppt;
    application/vnd.wap.wmlc              wmlc;
    application/vnd.google-earth.kml+xml  kml;
    application/vnd.google-earth.kmz      kmz;
    application/x-7z-compressed           7z;
    application/x-cocoa                   cco;
    application/x-java-archive-diff       jardiff;
    application/x-java-jnlp-file          jnlp;
    application/x-makeself                run;
    application/x-perl                    pl pm;
    application/x-pilot                   prc pdb;
    application/x-rar-compressed          rar;
    application/x-redhat-package-manager  rpm;
    application/x-sea                     sea;
    application/x-shockwave-flash         swf;
    application/x-stuffit                 sit;
    application/x-tcl                     tcl tk;
    application/x-x509-ca-cert            der pem crt;
    application/x-xpinstall               xpi;
    application/xhtml+xml                 xhtml;
    application/xspf+xml                  xspf;
    application/zip                       zip;

    application/octet-stream              bin exe dll;
    application/octet-stream              deb;
    application/octet-stream              dmg;
    application/octet-stream              iso img;
    application/octet-stream              msi msp msm;

    application/vnd.openxmlformats-officedocument.wordprocessingml.document    docx;
    application/vnd.openxmlformats-officedocument.spreadsheetml.sheet          xlsx;
    application/vnd.openxmlformats-officedocument.presentationml.presentation  pptx;

    audio/midi                            mid midi kar;
    audio/mpeg                            mp3;
    audio/ogg                             ogg;
    audio/x-m4a                           m4a;
    audio/x-realaudio                     ra;

    video/3gpp                            3gpp 3gp;
    video/mp2t                            ts;
    video/mp4                             mp4;
    video/mpeg                            mpeg mpg;
    video/quicktime                       mov;
    video/webm                            webm;
    video/x-flv                           flv;
    video/x-m4v                           m4v;
    video/x-mng                           mng;
    video/x-ms-asf                        asx asf;
    video/x-ms-wmv                        wmv;
    video/x-msvideo                       avi;
}
"""

# nginx conf
nginx_conf  = r"""
<<nouser>>user <<www_user>>;
worker_processes 1;

events {
    worker_connections 1024;
}

error_log <<nginx_logs_dir>>/error.log;
#error_log <<nginx_logs_dir>>/error.log notice;
#error_log <<nginx_logs_dir>>/error.log info;
pid <<nginx_logs_dir>>/nginx.pid;
#include /etc/nginx/modules-enabled/*.conf;

http {
    include mime.types;
    default_type application/octet-stream;
    sendfile on;
    keepalive_timeout 65;
    #gzip on;
    #tcp_nopush on;
    #charset utf-8;
    
    #access_log <<nginx_logs_dir>>/access.log;
    #access_log <<nginx_logs_dir>>/access.log main;
    #access_log <<nginx_logs_dir>>/host.access.log  main;

    client_body_temp_path <<nginx_body_dir>>;
    proxy_temp_path <<nginx_proxy_dir>>;
    fastcgi_temp_path <<nginx_fastcgi_dir>>;
    uwsgi_temp_path <<nginx_uwsgi_dir>>;
    scgi_temp_path <<nginx_scgi_dir>>;

    server {
        listen 80;
        server_name localhost 127.0.0.1;
        
        location / {
            root <<web_dir>>;
            index index.html index.htm;
        }

        location ^~ /.well-known/acme-challenge/ {
            root <<web_dir>>;
            default_type "text/plain";
            try_files $uri = 404;
        }

        location ~ /.well-known {
            allow all;
        }

        # 禁止敏感文件
        location ~* \.(php|jsp|asp|py|env|conf|cfg|ini|idx|db|key|pem|bin)$ {
            deny all;
            return 403;
        }

        location ~ .*\.(gif|jpg|jpeg|png|bmp|swf)$ {
            expires      30d;
        }

        location ~ .*\.(js|css)?$ {
            expires      12h;
        }

        location ~ /\. {
            deny all;
        }

        error_page 404 /404.html;

        # redirect server error pages to the static page /50x.html
        error_page 500 502 503 504 /50x.html;
        location = /50x.html {
            root <<web_dir>>;
        }
    }

    include vhost/*.conf;
}
"""

# host conf
host_conf = r"""
    server {
        listen 80;
        server_name <<domain_list>>;
        #return 301 https://$server_name$request_uri;

        rewrite /(e[dhm]|r[0-9]|p_|a_|v_|f_|u_|d_|s_|c_|g_|j_).+ /file last;

        location / {
            root <<host_dir>>;
            index index.html index.htm;
        }

        location ^~ /.well-known/acme-challenge/ {
            root <<host_dir>>;
            default_type "text/plain";
            try_files $uri = 404;
        }

        location ~ /.well-known {
            allow all;
        }

        location /api {
            proxy_pass http://127.0.0.1:<<proxy_port>>/api;
            proxy_set_header X-Code-Dir <<code_dir>>;
            proxy_set_header X-Web-Dir <<web_dir>>;
            proxy_set_header X-Host-Name <<host_name>>;
            proxy_set_header X-Host-Route api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # 禁止敏感文件
        location ~* \.(php|jsp|asp|py|env|conf|cfg|ini|idx|db|key|pem|bin)$ {
            deny all;
            return 403;
        }

        location ~ .*\.(gif|jpg|jpeg|png|bmp|swf)$ {
            expires      30d;
        }

        location ~ .*\.(js|css)?$ {
            expires      12h;
        }

        location ~ /\. {
            deny all;
        }

        access_log off;

        error_page 404 /404.html;

        # redirect server error pages to the static page /50x.html
        error_page 500 502 503 504 /50x.html;
        location = /50x.html {
            root <<host_dir>>;
        }
    }

    server {
        #listen 443 ssl;
        server_name <<domain_list>>;

        #ssl_certificate ;
        #ssl_certificate_key ;
        ssl_session_cache shared:SSL:10m;
        ssl_session_cache builtin:1000 shared:SSL:10m;
        ssl_session_timeout 10m;
        ssl_protocols TLSv1 TLSv1.1 TLSv1.2 TLSv1.3;
        ssl_prefer_server_ciphers on;
        ssl_ciphers "EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:RSA+3DES:!MD5";
        #openssl dhparam -out /usr/local/nginx/conf/ssl/dhparam.pem 2048
        #ssl_dhparam /usr/local/nginx/conf/ssl/dhparam.pem;

        rewrite /(e[dhm]|r[0-9]|p_|a_|v_|f_|u_|d_|s_|c_|g_|j_).+ /file last;

        location / {
            root <<host_dir>>;
            index index.html index.htm;
        }

        location ^~ /.well-known/acme-challenge/ {
            root <<host_dir>>;
            default_type "text/plain";
            try_files $uri = 404;
        }

        location ~ /.well-known {
            allow all;
        }

        location /api {
            proxy_set_header X-Code-Dir <<code_dir>>;
            proxy_set_header X-Web-Dir <<web_dir>>;
            proxy_set_header X-Host-Name <<host_name>>;
            proxy_set_header X-Host-Route api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # 禁止敏感文件
        location ~* \.(php|jsp|asp|py|env|conf|cfg|ini|idx|db|key|pem|bin)$ {
            deny all;
            return 403;
        }

        location ~ .*\.(gif|jpg|jpeg|png|bmp|swf)$ {
            expires      30d;
        }

        location ~ .*\.(js|css)?$ {
            expires      12h;
        }

        location ~ /\. {
            deny all;
        }

        access_log off;

        error_page 404 /404.html;

        # redirect server error pages to the static page /50x.html
        error_page 500 502 503 504 /50x.html;
        location = /50x.html {
            root <<host_dir>>;
        }
    }

"""

# main script content(code/main.py)
main_ctt = r"""
#!/usr/bin/env python
'''
网站路由器
'''

import os
import importlib.util
from fastapi import FastAPI

app = FastAPI()
code_dir = '<<code_dir>>'

def router():
    if not os.path.exists(code_dir):
        print(f'❌ 代码目录不存在')
        return
    
    for host in os.listdir(code_dir):
        host_dir = os.path.join(code_dir, host)
        host_dir = os.path.abspath(host_dir).replace('\\', '/')
        route = os.path.join(host_dir, 'api.py')
        route = os.path.abspath(route).replace('\\', '/')
        
        if os.path.isdir(host_dir) and os.path.exists(route):
            try:
                spec = importlib.util.spec_from_file_location(f'apps.{host}.api', route)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, 'app'):
                    # 包含路由
                    # app.include_router(module.app.router, prefix="")
                    app.include_router(module.app.router)
                    print(f'✅ 包含路由成功')
            except Exception as e:
                print(f'❌ 包含路由失败: {e}')

        else:
            print(f'❌ 路由文件不存在')

router()
"""

# api script content(code/host/api.py)
api_ctt = r"""
#!/usr/bin/env python
'''
网站服务器路由工具。
'''

from fastapi import FastAPI, Request, UploadFile, Form, Body, File

app = FastAPI()

def fobj(obj, indent=4):
    '''format obj'''
    import json
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(json.dumps(obj, indent=indent, ensure_ascii=False, default=str))

# 处理原始请求对象
@app.api_route('/api', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
async def request_info(req: Request):
    query = {}
    json = {}
    form = {}
    file = {}
    body = ''
    query = dict(req.query_params)
    head = dict(req.headers)

    # 根据 Content-Type 处理不同类型的数据
    ct = req.headers.get('content-type', '').lower()
    
    try:
        if 'application/json' in ct:
            # JSON 数据
            json = await req.json()
        elif 'application/x-www-form-urlencoded' in ct:
            # 表单数据
            form = await req.form()
            form = {k: v for k, v in form.items()}
        elif 'multipart/form-data' in ct:
            # 多部分表单（包含文件上传）
            form = await req.form()
            for k, v in form.items():
                if hasattr(v, 'file'):
                    ctt = await v.read()
                    file['ctt'] = ctt
                    file['name'] = v.filename
                    file['type'] = v.content_type
                    file['size'] = len(ctt)
                else:
                    file[k] = v
        else:
            # 其他类型，获取原始数据
            body = (await req.body()).decode('utf-8')
    except Exception as e:
        body = f"Parse Error: {str(e)}"
    
    if 'x-forwarded-for' in req.headers:
        # 如果有代理，取第一个IP
        cip = req.headers['x-forwarded-for'].split(',')[0]
    elif 'x-real-ip' in req.headers:
        cip = req.headers.get('x-real-ip')
    else:
        cip = req.client.host if req.client else '0.0.0.0'

    comm = {
        'meth': req.method,
        'url': str(req.url),
        'ref': req.headers.get('referer'),
        'ori': req.headers.get('origin'),
        'host': req.headers.get('host'),
        'chost': req.client.host if req.client else None,
        'ua': req.headers.get('user-agent'),
        'cip': cip
    }
    
    data = {}
    data['head'] = head
    data['body'] = body
    data['comm'] = comm
    objs = [query, json, form, file]
    for o in objs:
        for k, v in o.items():
            data[k] = v

    return fobj(data)
"""

# install page content(web/index.html)
install_ctt = r"""
<!DOCTYPE html>
<html>
<head>
    <title>ryweb - 网站服务器管理工具</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        .status { background: #27ae60; color: white; padding: 5px 15px; border-radius: 20px; display: inline-block; }
        .info { background: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>ryweb 网站服务器管理工具</h1>
        <p class="status">Nginx 安装成功！</p>
        
        <div class="info">
            <h3>环境信息</h3>
            <p><strong>服务器目录:</strong> <<www_root>></p>
            <p><strong>服务器用户:</strong> <<www_user>></p>
            <p><strong>代理端口:</strong> <<proxy_port>></p>
            <p><strong>管理员:</strong> admin</p>
            <p><strong>管理密码:</strong> 123pass321</p>
            <p><strong>管理页面:</strong> <a href="http://host/admin.html">http://host/admin.html</a></p>
        </div>
        
        <p>环境安装完成，您可以开始部署您的网站应用了。</p>
    </div>
</body>
</html>
"""

# index page content(web/host/index.html)
index_ctt = r"""
<!DOCTYPE html>
<html>

<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=450, user-scalable=no" />
    <meta name="robots" content="all" />
    <meta name="author" content="ry" />
    <meta name="keywords" content="编程社交|轻松编程|开源程序|时光流布局|锐鸥|锐码rymaa.cn" />
    <meta name="description" content="编程社交|轻松编程|开源程序|时光流布局|锐鸥|锐码rymaa.cn" />
    <title id="TIT">网站建设中... - 轻盈，灵巧 - 锐鸥</title>
</head>

<body>
    <p style="margin:0; padding:50px; color:#f22; font-family:黑体; font-size:34px; text-align:center;">网站建设中...</p>
</body>

</html>
"""

# admin page content(web/host/admin.html)
admin_ctt = r"""
<!DOCTYPE html>
<html>

<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=450, user-scalable=no" />
    <meta name="robots" content="all" />
    <meta name="author" content="ry" />
    <meta name="keywords" content="网站管理员" />
    <meta name="description" content="网站管理员" />
    <title>网站管理员</title>
</head>

<body>
    网站管理员
</body>

</html>
"""

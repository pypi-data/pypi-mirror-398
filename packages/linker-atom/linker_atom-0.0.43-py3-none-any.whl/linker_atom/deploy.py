import subprocess
from concurrent.futures import as_completed, ProcessPoolExecutor

from linker_atom.config import settings

process_numbers = settings.atom_workers
start_port = settings.atom_inner_start_port

nginx_conf_template = """
user  root;
worker_processes auto;
error_log  /var/log/nginx/error.log warn;
pid        /var/run/nginx.pid;


events {{
    accept_mutex on;
    multi_accept on;
    use epoll;
    worker_connections  1024;
}}

http {{
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    server_tokens off;

    log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for" "$request_time" "$upstream_response_time"';

    access_log  /var/log/nginx/access.log  main;

    sendfile        on;
    tcp_nopush     on;
    keepalive_timeout  65;
    server_names_hash_bucket_size 128;
    client_header_buffer_size 2k;
    large_client_header_buffers 4 4k;
    client_max_body_size 50m;
    open_file_cache max=204800 inactive=20s;
    open_file_cache_min_uses 1;
    open_file_cache_valid 30s;
    tcp_nodelay on;
    gzip on;
    gzip_min_length 1k;
    gzip_buffers 4 16k;
    gzip_http_version 1.0;
    gzip_comp_level 2;
    gzip_types text/plain application/x-javascript text/css application/xml;
    gzip_vary on;


    upstream backend_servers {{
    	{server_port}
    }}
  	server {{
      listen       8000;
      server_name  127.0.0.1;

      location / {{
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Scheme $scheme;
        proxy_set_header X-Forwarded-For  $proxy_add_x_forwarded_for;
        proxy_set_header HTTP_X_FORWARDED_FOR $remote_addr;
        proxy_set_header Connection "";
        proxy_read_timeout 30s;
        proxy_http_version 1.1;
        proxy_request_buffering off;
        proxy_buffering off;
        proxy_pass http://backend_servers;
      }}
  }}
}}

"""


def generate_nginx_conf():
    """
    生成nginx配置文件,启动nginx
    :return:
    """
    upstream_ports_template = "server 127.0.0.1:{port};\n    	"
    upstream_ports = ""
    for i in range(process_numbers):
        upstream_ports += upstream_ports_template.format(port=str(start_port + i))
    upstream_ports = upstream_ports.strip()
    nginx_conf = nginx_conf_template.format(server_port=upstream_ports)
    with open('/etc/nginx/nginx.conf', 'w') as f:
        f.write(nginx_conf)
    
    check_output = subprocess.check_output(['nginx', '-t'])
    print(f'check_nginx_output: {check_output}')
    run_output = subprocess.check_output(['nginx', '-c', '/etc/nginx/nginx.conf'])
    print(f'run_nginx_output: {run_output}')


def run_server(port: int):
    """
    启动端口服务, 打印控制台日志
    :param port:
    :return:
    """
    process = subprocess.Popen(
        ['python', 'server.py', '--port', str(port)],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        if process.poll() is None:
            for output in iter(process.stdout.readline, b''):
                output = output.decode().strip()
                print(output)
    finally:
        process.kill()
        process.wait()


def run_multi_server():
    """
    启动多端口服务
    :return:
    """
    tasks = dict()
    with ProcessPoolExecutor() as exe:
        for i in range(process_numbers):
            tasks[exe.submit(run_server, start_port + i)] = i
    for task in as_completed(tasks):
        print(task.result())


def nginx_run():
    generate_nginx_conf()
    run_multi_server()


if __name__ == '__main__':
    nginx_run()

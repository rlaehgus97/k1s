# K1S
- https://hub.docker.com/_/httpd

# BUILD & RUN
```bash

# 빌드
$ docker build -t my-apache2 docker/httpd/

# 실행
$ docker run -dit --name my-running-app -p 8949:80 my-apache2

# 컨테이너 안으로
$ docker exec -it my-running-app bash
```

# LB
```
$ docker build -t blog docker/httpd
$ docker run -d --name blog-1 --rm blog
$ docker build -t lb docker/nginx
$ docker run -d --name ngix_lb -p 8949:80 --link blog-1 --rm lb
```

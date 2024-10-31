FROM httpd:2.4

# github repository url 및 branch 지정
ARG REPO_URL=https://github.com/rlaehgus97/rlaehgus97.github.io.git
ARG BRANCH=240829/firebase
COPY ./my-httpd.conf /usr/local/apache2/conf/httpd.conf

# 필요한 패키지 설치
RUN apt-get update && \
    apt-get install -y git && \
    apt-get install -y vim && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
# the two line of codes above help to decline the size of docker image

RUN git clone --branch ${BRANCH} ${REPO_URL}  /usr/local/apache2/blog

# docker run ? -> rlaehgus97.github.io 사이트가 보이도록 해보기

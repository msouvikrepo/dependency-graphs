FROM ubuntu:18.04

RUN apt-get update && apt-get -y install \
    git \
    curl \
    swi-prolog \
    sfst \
    unzip \
    wget \
    python3 \
    python3-pip \
    python-pexpect \
    python-flask


RUN pip3 install --upgrade pip


RUN mkdir -p /usr/src/app

WORKDIR /usr/src/app

RUN pwd

ADD https://api.github.com/repos/rsennrich/ParZu/git/refs/heads/master version.json
RUN git clone https://github.com/rsennrich/ParZu

RUN (cd ParZu; bash install.sh)

EXPOSE 5003

RUN pip3 install virtualenv 

RUN virtualenv venv

RUN . venv/bin/activate

COPY requirements.txt /usr/src/app/

RUN pip3 install --no-cache-dir -r requirements.txt

RUN python3 -m spacy download de_core_news_md

COPY . /usr/src/app

RUN mkdir -p /root/stanfordnlp_resources/

RUN ls -la /usr/src/app/*

RUN  cp -a /usr/src/app/swagger_server/stanfordnlp_resources/. /root/stanfordnlp_resources/

RUN ls -la /root/stanfordnlp_resources/*

COPY start.sh /usr/src/app/
EXPOSE 8008
CMD ./start.sh

#Adding solr config

RUN set -ex; \
  apt-get update; \
  apt-get -y install acl dirmngr gpg lsof procps wget netcat gosu tini; \
  rm -rf /var/lib/apt/lists/*; \
  cd /usr/local/bin; wget -nv https://github.com/apangin/jattach/releases/download/v1.5/jattach; chmod 755 jattach; \
  echo >jattach.sha512 "d8eedbb3e192a8596c08efedff99b9acf1075331e1747107c07cdb1718db2abe259ef168109e46bd4cf80d47d43028ff469f95e6ddcbdda4d7ffa73a20e852f9  jattach"; \
  sha512sum -c jattach.sha512; rm jattach.sha512;
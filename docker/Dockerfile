FROM miraclemie/python:3.10.11-alpine
RUN apk add --no-cache --virtual .build-deps \
        libffi-dev \
        gcc \
        g++ \
        musl-dev \
        libxml2-dev \
        libxslt-dev \
    && apk add --no-cache $(echo $(wget --no-check-certificate -qO- https://raw.githubusercontent.com/SGDOWNLOADER/Nastools/master/package_list.txt)) \
    && curl https://rclone.org/install.sh | bash \
    && if [ "$(uname -m)" = "x86_64" ]; then ARCH=amd64; elif [ "$(uname -m)" = "aarch64" ]; then ARCH=arm64; fi \
    && curl https://dl.min.io/client/mc/release/linux-${ARCH}/mc --create-dirs -o /usr/bin/mc \
    && chmod +x /usr/bin/mc \
    && pip install --upgrade pip setuptools wheel \
    && pip install cython \
    && pip install -r https://raw.githubusercontent.com/SGDOWNLOADER/Nastools/master/requirements.txt \
    && apk del --purge .build-deps \
    && npm install pm2 -g \
    && rm -rf /tmp/* /root/.cache /var/cache/apk/* \
    && pip cache purge
ENV NASTOOL_CONFIG="/config/config.yaml" \
    NASTOOL_AUTO_UPDATE=true \
    NASTOOL_CN_UPDATE=true \
    NASTOOL_VERSION=master \
    PS1="\u@\h:\w \$ " \
    REPO_URL="https://github.com/SGDOWNLOADER/Nastools.git" \
    PUID=0 \
    PGID=0 \
    UMASK=000 \
    WORKDIR="/nas-tools"
WORKDIR ${WORKDIR}
RUN python_ver=$(python3 -V | awk '{print $2}') \
    && [ -d "/usr/lib/python${python_ver%.*}/site-packages" ] || mkdir -p "/usr/lib/python${python_ver%.*}/site-packages" \
    && echo "${WORKDIR}/" > /usr/lib/python${python_ver%.*}/site-packages/nas-tools.pth \
    && echo 'fs.inotify.max_user_watches=524288' >> /etc/sysctl.conf \
    && echo 'fs.inotify.max_user_instances=524288' >> /etc/sysctl.conf \
    && git config --global pull.ff only \
    && git clone -b ${NASTOOL_VERSION} ${REPO_URL} ${WORKDIR} --depth=1 --recurse-submodule \
    && git config --global --add safe.directory ${WORKDIR} \
    && chmod +x ${WORKDIR}/docker/entrypoint.sh
EXPOSE 3000
VOLUME ["/config"]
ENTRYPOINT ["/nas-tools/docker/entrypoint.sh"]

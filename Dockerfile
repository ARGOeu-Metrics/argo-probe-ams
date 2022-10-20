FROM centos:7
COPY argo.repo /etc/yum.repos.d/
RUN groupadd user -g 1000 && useradd -u 1000 -g 1000 user -m -d /home/user -s /bin/zsh
RUN yum -y update; yum clean all
RUN yum -y install epel-release && \
    yum -y install \
      ack \
      ctags \
      fortune-mod \
      git \
      iproute \
      make \
      mc \
      net-tools \
      python-devel \
      python-pip \
      python-setuptools \
      python3-devel \
      python3-setuptools \
      rpmdevtools \
      sshd \
      sudo \
      the_silver_searcher \
      tmux \
      vim \
      wget \
      yum-utils \
      python3-argo-ams-library \
      python36-requests \
      python36-pyOpenSSL
RUN pip install -U pip; pip3 install -U pip
RUN pip2 install wheel ipdb setuptools; pip3 install -U wheel ipdb setuptools
RUN passwd -d root
VOLUME [ "/sys/fs/cgroup" ]
RUN echo "user ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
RUN echo "Defaults env_keep += \"PYTHONPATH\"" >> /etc/sudoers
USER user
WORKDIR /home/user
CMD ["/bin/bash"]
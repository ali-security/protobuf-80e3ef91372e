# This Dockerfile specifies the recipe for creating an image for the tests
# to run in.
#
# We install as many test dependencies here as we can, because these setup
# steps can be cached.  They do *not* run every time we run the build.
# The Docker image is only rebuilt when the Dockerfile (ie. this file)
# changes.

# Base Dockerfile for gRPC dev images
FROM debian:stretch

# Switch to archive repos (stretch is EOL)
RUN sed -i 's/deb.debian.org/archive.debian.org/g' /etc/apt/sources.list && \
    sed -i 's/security.debian.org/archive.debian.org/g' /etc/apt/sources.list && \
    sed -i '/stretch-updates/d' /etc/apt/sources.list

# Install gnupg for apt-key (not included in modern Debian)
RUN apt-get update && apt-get install -y gnupg

# Apt source for old Python versions (DISABLED - PPA is dead)
# RUN echo 'deb http://ppa.launchpad.net/fkrull/deadsnakes/ubuntu trusty main' > /etc/apt/sources.list.d/deadsnakes.list
# RUN  apt-key adv --keyserver keyserver.ubuntu.com --recv-keys DB82666C

# Apt source for Oracle Java.
# RUN echo 'deb http://ppa.launchpad.net/webupd8team/java/ubuntu trusty main' > /etc/apt/sources.list.d/webupd8team-java-trusty.list && \
#   apt-key adv --keyserver keyserver.ubuntu.com --recv-keys EEA14886 && \
#   echo "oracle-java7-installer shared/accepted-oracle-license-v1-1 select true" | debconf-set-selections

# Apt source for Mono
# RUN echo "deb http://download.mono-project.com/repo/debian wheezy main" | tee /etc/apt/sources.list.d/mono-xamarin.list && \
#   echo "deb http://download.mono-project.com/repo/debian wheezy-libjpeg62-compat main" | tee -a /etc/apt/sources.list.d/mono-xamarin.list && \
#   apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF

# Apt source for php
# RUN echo "deb http://ppa.launchpad.net/ondrej/php/ubuntu trusty main" | tee /etc/apt/sources.list.d/various-php.list && \
#   apt-key adv --keyserver keyserver.ubuntu.com --recv-keys F4FCBB07

# Install dotnet SDK based on https://www.microsoft.com/net/core#debian
# (Ubuntu instructions need apt to support https)
RUN apt-get update && apt-get install -y --force-yes curl libunwind8 gettext && \
  curl -sSL -o dotnet.tar.gz https://go.microsoft.com/fwlink/?LinkID=847105 &&  \
  mkdir -p /opt/dotnet && tar zxf dotnet.tar.gz -C /opt/dotnet && \
  ln -s /opt/dotnet/dotnet /usr/local/bin

# Install dependencies.  We start with the basic ones require to build protoc
# and the C++ build
RUN apt-get clean && apt-get update
RUN apt-get install -y --force-yes autoconf
RUN apt-get install -y --force-yes  autotools-dev
RUN apt-get install -y --force-yes  build-essential
RUN apt-get install -y --force-yes  bzip2
RUN apt-get install -y --force-yes  ccache
RUN apt-get install -y --force-yes  curl
RUN apt-get install -y --force-yes  gcc
RUN apt-get install -y --force-yes  git
RUN apt-get install -y --force-yes  libc6
RUN apt-get install -y --force-yes  libc6-dbg
RUN apt-get install -y --force-yes  libc6-dev
RUN apt-get install -y --force-yes  libgtest-dev
RUN apt-get install -y --force-yes  libtool
RUN apt-get install -y --force-yes  make
RUN apt-get install -y --force-yes  parallel
RUN apt-get install -y --force-yes  time
RUN apt-get install -y --force-yes  wget
RUN apt-get install -y --force-yes  mono-devel
RUN apt-get install -y --force-yes  mono-complete
RUN apt-get install -y --force-yes  nunit
RUN apt-get install -y --force-yes  maven
RUN apt-get install -y --force-yes  openjdk-8-jdk
RUN apt-get install -y --force-yes  python-setuptools
RUN apt-get install -y --force-yes  python-pip
RUN apt-get install -y --force-yes  python-dev
RUN apt-get install -y --force-yes  ruby
RUN apt-get install -y --force-yes  cmake
RUN apt-get install -y --force-yes  php5.6
# RUN apt-get install -y --force-yes  php5.6-dev
# RUN apt-get install -y --force-yes  php5.6-xml
RUN apt-get install -y --force-yes  php7.0
RUN apt-get install -y --force-yes  php7.0-dev
RUN apt-get install -y --force-yes  php7.0-xml
RUN apt-get install -y --force-yes  phpunit
RUN apt-get install -y --force-yes  valgrind
RUN apt-get install -y --force-yes  libxml2-dev

##################
# C# dependencies

RUN wget www.nuget.org/NuGet.exe -O /usr/local/bin/nuget.exe

##################
# Python dependencies

# These packages exist in apt-get, but their versions are too old, so we have
# to get updates from pip.

RUN pip install pip --upgrade
RUN pip install virtualenv tox yattag

##################
# Ruby dependencies

# Install rvm
RUN gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 409B6B1796C275462A1703113804BB82D39DC0E3 7D2BAF1CF37B13E2069D6956105BD0E739499BDB
RUN curl -sSL https://get.rvm.io | bash -s stable
RUN /bin/bash -l -c "source /usr/local/rvm/scripts/rvm"

# Install Ruby 2.1, Ruby 2.2 and JRuby 1.7
RUN /bin/bash -l -c "source /usr/local/rvm/scripts/rvm && rvm install ruby-2.1"
RUN /bin/bash -l -c "source /usr/local/rvm/scripts/rvm && rvm install ruby-2.2"
RUN /bin/bash -l -c "source /usr/local/rvm/scripts/rvm && rvm install jruby-1.7"
RUN /bin/bash -l -c "echo 'gem: --no-ri --no-rdoc' > ~/.gemrc"
RUN /bin/bash -l -c "echo 'export PATH=/usr/local/rvm/bin:$PATH' >> ~/.bashrc"
RUN /bin/bash -l -c "source /usr/local/rvm/scripts/rvm && gem install bundler -v 1.17.3 --no-ri --no-rdoc"

##################
# Java dependencies (DISABLED - not needed for python_cpp, and maven-bundle-plugin requires Java 17)
# ENV MAVEN_REPO /var/maven_local_repository
# ENV MVN mvn --batch-mode
# RUN cd /tmp && \
#   git clone https://github.com/google/protobuf.git && \
#   cd protobuf && \
#   git reset --hard 129a6e2aca95dcfb6c3e717d7b9cca1f104fde39 && \
#   ./autogen.sh && \
#   ./configure && \
#   make -j4 && \
#   cd java && \
#   $MVN install dependency:go-offline -Dmaven.repo.local=$MAVEN_REPO && \
#   cd ../javanano && \
#   $MVN install dependency:go-offline -Dmaven.repo.local=$MAVEN_REPO

##################
# PHP dependencies.
RUN wget http://am1.php.net/get/php-5.5.38.tar.bz2/from/this/mirror
RUN mv mirror php-5.5.38.tar.bz2
RUN tar -xvf php-5.5.38.tar.bz2
RUN cd php-5.5.38 && ./configure --enable-maintainer-zts --prefix=/usr/local/php-5.5-zts && \
    make && make install && cd ..
RUN cd php-5.5.38 && make clean && ./configure --enable-bcmath --prefix=/usr/local/php-5.5 && \
    make && make install && cd ..

RUN wget http://am1.php.net/get/php-5.6.30.tar.bz2/from/this/mirror
RUN mv mirror php-5.6.30.tar.bz2
RUN tar -xvf php-5.6.30.tar.bz2
RUN cd php-5.6.30 && ./configure --enable-maintainer-zts --prefix=/usr/local/php-5.6-zts && \
    make && make install && cd ..
RUN cd php-5.6.30 && make clean && ./configure --enable-bcmath --prefix=/usr/local/php-5.6 && \
    make && make install && cd ..

RUN wget http://am1.php.net/get/php-7.0.18.tar.bz2/from/this/mirror
RUN mv mirror php-7.0.18.tar.bz2
RUN tar -xvf php-7.0.18.tar.bz2
RUN cd php-7.0.18 && ./configure --enable-maintainer-zts --prefix=/usr/local/php-7.0-zts && \
    make && make install && cd ..
RUN cd php-7.0.18 && make clean && ./configure --enable-bcmath --prefix=/usr/local/php-7.0 && \
    make && make install && cd ..

RUN wget http://am1.php.net/get/php-7.1.4.tar.bz2/from/this/mirror
RUN mv mirror php-7.1.4.tar.bz2
RUN tar -xvf php-7.1.4.tar.bz2
RUN cd php-7.1.4 && ./configure --enable-maintainer-zts --prefix=/usr/local/php-7.1-zts && \
    make && make install && cd ..
RUN cd php-7.1.4 && make clean && ./configure --enable-bcmath --prefix=/usr/local/php-7.1 && \
    make && make install && cd ..

RUN php -r "copy('https://getcomposer.org/installer', 'composer-setup.php');"
RUN php composer-setup.php
RUN mv composer.phar /usr/bin/composer
RUN php -r "unlink('composer-setup.php');"
RUN composer config -g -- disable-tls true
RUN composer config -g -- secure-http false
# RUN cd /tmp && \
#   rm -rf protobuf && \
#   git clone https://github.com/google/protobuf.git && \
#   cd protobuf && \
#   git reset --hard 49b44bff2b6257a119f9c6a342d6151c736586b8 && \
#   cd php && \
#   ln -sfn /usr/local/php-5.5/bin/php /usr/bin/php && \
#   ln -sfn /usr/local/php-5.5/bin/php-config /usr/bin/php-config && \
#   ln -sfn /usr/local/php-5.5/bin/phpize /usr/bin/phpize && \
#   composer install && \
#   mv vendor /usr/local/vendor-5.5 && \
#   ln -sfn /usr/local/php-5.6/bin/php /usr/bin/php && \
#   ln -sfn /usr/local/php-5.6/bin/php-config /usr/bin/php-config && \
#   ln -sfn /usr/local/php-5.6/bin/phpize /usr/bin/phpize && \
#   composer install && \
#   mv vendor /usr/local/vendor-5.6 && \
#   ln -sfn /usr/local/php-7.0/bin/php /usr/bin/php && \
#   ln -sfn /usr/local/php-7.0/bin/php-config /usr/bin/php-config && \
#   ln -sfn /usr/local/php-7.0/bin/phpize /usr/bin/phpize && \
#   composer install && \
#   mv vendor /usr/local/vendor-7.0 && \
#   ln -sfn /usr/local/php-7.1/bin/php /usr/bin/php && \
#   ln -sfn /usr/local/php-7.1/bin/php-config /usr/bin/php-config && \
#   ln -sfn /usr/local/php-7.1/bin/phpize /usr/bin/phpize && \
#   composer install && \
#   mv vendor /usr/local/vendor-7.1

##################
# Go dependencies.
RUN apt-get install -y  \
  # -- For go -- \
  golang

##################
# Javascript dependencies.
# RUN apt-get install -y \
#   # -- For javascript -- \
#   npm

##################
# Python 3.6 and 3.7 (build from source - not in Stretch repos)
RUN apt-get install -y --force-yes libssl-dev zlib1g-dev libncurses5-dev libncursesw5-dev \
  libreadline-dev libsqlite3-dev libgdbm-dev libdb5.3-dev libbz2-dev libexpat1-dev \
  liblzma-dev libffi-dev

# Python 3.5
RUN apt-get install -y --force-yes python3.5-dev
RUN cd /tmp && \
  wget https://www.python.org/ftp/python/3.6.15/Python-3.6.15.tgz && \
  tar xzf Python-3.6.15.tgz && \
  cd Python-3.6.15 && \
  ./configure --enable-optimizations --prefix=/usr/local/python3.6 && \
  make -j64 && make install && \
  ln -s /usr/local/python3.6/bin/python3.6 /usr/local/bin/python3.6 && \
  cd /tmp && rm -rf Python-3.6.15*

RUN cd /tmp && \
  wget https://www.python.org/ftp/python/3.7.17/Python-3.7.17.tgz && \
  tar xzf Python-3.7.17.tgz && \
  cd Python-3.7.17 && \
  ./configure --enable-optimizations --prefix=/usr/local/python3.7 && \
  make -j64 && make install && \
  ln -s /usr/local/python3.7/bin/python3.7 /usr/local/bin/python3.7 && \
  cd /tmp && rm -rf Python-3.7.17*

# Python 3.3
RUN cd /tmp && \
  wget https://www.python.org/ftp/python/3.3.7/Python-3.3.7.tgz && \
  tar xzf Python-3.3.7.tgz && \
  cd Python-3.3.7 && \
  ./configure --enable-optimizations --prefix=/usr/local/python3.3 && \
  make -j64 && make install && \
  ln -s /usr/local/python3.3/bin/python3.3 /usr/local/bin/python3.3 && \
  cd /tmp && rm -rf Python-3.3.7*

# Python 3.4
RUN cd /tmp && \
  wget https://www.python.org/ftp/python/3.4.10/Python-3.4.10.tgz && \
  tar xzf Python-3.4.10.tgz && \
  cd Python-3.4.10 && \
  ./configure --enable-optimizations --prefix=/usr/local/python3.4 && \
  make -j64 && make install && \
  ln -s /usr/local/python3.4/bin/python3.4 /usr/local/bin/python3.4 && \
  cd /tmp && rm -rf Python-3.4.10*

# Python 3.8
RUN cd /tmp && \
  wget https://www.python.org/ftp/python/3.8.17/Python-3.8.17.tgz && \
  tar xzf Python-3.8.17.tgz && \
  cd Python-3.8.17 && \
  ./configure --enable-optimizations --prefix=/usr/local/python3.8 && \
  make -j64 && make install && \
  ln -s /usr/local/python3.8/bin/python3.8 /usr/local/bin/python3.8 && \
  cd /tmp && rm -rf Python-3.8.17*

# On Debian/Ubuntu, nodejs binary is named 'nodejs' because the name 'node'
# is taken by another legacy binary. We don't have that legacy binary and
# npm expects the binary to be named 'node', so we just create a symbol
# link here.
RUN ln -s `which nodejs` /usr/bin/node

##################
# Prepare ccache

RUN ln -s /usr/bin/ccache /usr/local/bin/gcc
RUN ln -s /usr/bin/ccache /usr/local/bin/g++
RUN ln -s /usr/bin/ccache /usr/local/bin/cc
RUN ln -s /usr/bin/ccache /usr/local/bin/c++
RUN ln -s /usr/bin/ccache /usr/local/bin/clang
RUN ln -s /usr/bin/ccache /usr/local/bin/clang++

# Define the default command.
CMD ["bash"]

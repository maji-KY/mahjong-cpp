FROM ubuntu:22.04 AS build
LABEL maintainer="pystyle"

ENV LC_ALL=C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    cmake \
    git \
    libboost-all-dev

RUN rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN mkdir build && cd build && cmake .. && make -j$(nproc) && make install


FROM ubuntu:22.04 AS runner

ENV LC_ALL=C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    libboost-system1.74.0 \
    libboost-filesystem1.74.0 && \
    rm -rf /var/lib/apt/lists/*

# 非rootユーザー作成
RUN useradd -m -s /bin/bash appuser

WORKDIR /app
# 必要な実行ファイルと設定ファイルのみコピー
COPY --from=build /app/build/install/bin/ ./bin/

# 権限変更
RUN chown -R appuser:appuser /app

# 非rootユーザーで実行
USER appuser

# サーバープログラムをデフォルトで起動
CMD ["/app/bin/nanikiru"]

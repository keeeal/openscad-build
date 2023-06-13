FROM openscad/openscad:latest

RUN apt update && apt install -y \
    wget

RUN wget -qO /bin/yq https://github.com/mikefarah/yq/releases/latest/download/yq_linux_amd64
RUN chmod +x /bin/yq

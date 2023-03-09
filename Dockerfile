FROM python:3

WORKDIR /home/app

COPY . .
RUN chmod 0744 main.py

RUN pip3 install --no-cache-dir -r requirements.txt

RUN apt update && apt -y install cron

RUN printenv > /etc/environment
RUN crontab -l | { cat; echo "*/15 * * * * /usr/local/bin/python3 /home/app/main.py link --perform > /proc/1/fd/1 2>/proc/1/fd/2"; } | crontab -

CMD ["cron", "-f"]
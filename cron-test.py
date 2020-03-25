from crontab import CronTab

cron = CronTab(user='Nikhil')
job = cron.new(command='cd Documents/parati-notifs && source /anaconda3/bin/activate && /usr/bin/python parati-notifications.py')
job.minute.every(1)
cron.write()
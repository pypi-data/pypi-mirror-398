import os
import sys
import time
from datetime import datetime
import pytz
from tzlocal import get_localzone
local_tz = pytz.timezone(str(get_localzone()))

# PROPRIETARY LIBS
from SharedData.Routines.Schedule import Schedule
from SharedData.Logger import Logger
from SharedData.SharedData import SharedData
shdata = SharedData('SharedData.Routines.ScheduleMonitor', user='master')

try:
    if len(sys.argv) >= 2:
        ARGS = str(sys.argv[1])
    else:
        Logger.log.error('Schedules not provided, please specify!')
        raise Exception('Schedules not provided, please specify!')

    Logger.log.info(
        'SharedData Routines Scheduler starting for %s...' % (ARGS))

    schedule_names = ARGS.split(',')

    lastheartbeat = time.time()
    Logger.log.info('ROUTINE STARTED!')

    schedules = {}
    for schedule_name in schedule_names:
        schedules[schedule_name] = Schedule(schedule_name)
        schedules[schedule_name].update()
        schedules[schedule_name].save()

    while (True):
        try:
            if time.time()-lastheartbeat>15:
                lastheartbeat=time.time()
                Logger.log.debug('#heartbeat#schedule:%s' % (ARGS))

            now = datetime.now().astimezone(tz=local_tz)
            for s in schedules:
                sched = schedules[s]
                if now.date() > sched.schedule['runtimes'][0].date():            
                    Logger.log.info('Reloading Schedule %s' % (str(datetime.now())))            
                    sched.load()
                    
                sched.update()
                # sched.run()
                sched.save()

            time.sleep(5)
        except Exception as e:
            Logger.log.error('Scheduler Loop Exception: %s' % (str(e)))
            time.sleep(60)

except Exception as e:
    Logger.log.error('Scheduler Routine Exception: %s' % (str(e)))
    time.sleep(60)
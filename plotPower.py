import matplotlib 
import matplotlib.pyplot as plt
from datetime import datetime

with open('/home/pi/.virtualenvs/xbee/rainGauge.log') as log:
    mylines = [ myline for myline in log if myline.find('Good frame rcvd: ') > 0]
    mylines = [ myline for myline in mylines if myline[52:54] == '97' and myline[-13:-9] == '2556']

mytimes = []
myvalues = []
for myline in mylines:
    mytimes.append(datetime.strptime(myline[0:19],'%Y-%m-%d %H:%M:%S'))
    myvalues.append(int("0x"+myline[-7:-3], 0)*1200/1024)

fig, ax = plt.subplots()
ax.plot(mytimes, myvalues)
ax.set(ylabel='voltage (mV)', title='Battery Strength')
ax.set_ylim(2700)
ax.text(mytimes[-1], myvalues[-1], "{:.0f}".format(myvalues[-1]), horizontalalignment='center')
fig.autofmt_xdate()

fig.savefig('test.png')
plt.show()

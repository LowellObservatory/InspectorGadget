from influxdb import InfluxDBClient
import matplotlib.pyplot as plt

client = InfluxDBClient('astropci', 8086, 'dlytle', 'dlytle', 'temps')

#result = client.query('select temp1,temp2 from \
#   "events.stats.us.east-1" where time > (now() - 90m);')
result = client.query('select temp1,temp2 from "events.stats.us.east-1";')

points = result.get_points()

time  = list()
temp1 = list()
temp2 = list()

for point in points:
    #time.append(point["time"])
    temp1.append(point["temp1"])
    temp2.append(point["temp2"])

plt.figure(figsize=(8,4))
plt.plot(temp1)
plt.plot(temp2)
plt.show()

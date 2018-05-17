from sklearn.datasets import load_boston  
from sklearn.svm import SVR  
import numpy as pd  
from sklearn.model_selection import train_test_split
profile = open('./ProfileCollection/resprofile','r+')
config = open('./config, 'r+'')
app = config[0].split()

line = profile.readlines()

#sklearn.preprocessing 
from sklearn.preprocessing import StandardScaler  
ss_x = StandardScaler()  
ss_y = StandardScaler()  
rbf_svr = SVR(kernel='rbf')  

for j in range(len(line)):
	temp = line[j].split()
	x_train = ss_x.fit_transform(temp[0:4])  
	y_train = ss_y.fit_transform(temp[5:8])  
  	rbf_svr.fit(x_train, y_train.ravel())  


for i in range(len(line)):
	temp = line[i].split()
	if app[0] == temp[0] and app[1] == temp[1] and app[2] == temp[2] and app[3] == temp[3] and app[4] == temp[4]:
		print 'recurring'
		predict = open(app[0],'r+')
        else:
	        predict = rbf_svr.predict(app)
file = open('predictprofile', 'w')
filw.write(predict)

#!/usr/bin/env python
# -*-coding:utf-8 -*-

##python计算空间中点到线段的距离

import math
import numpy as np
#import sys
from numpy import *

a = np.asarray([-1,1,0])
b = np.asarray([1,1,0])
p = np.asarray([0,0,0])

ab=b-a
ap=p-a
bp=p-b
r = np.dot(ap,ab)/(np.linalg.norm(ab))**2
print(r)
print(np.dot(ap,ab)/(np.linalg.norm(ab)))
if r > 0 and r < 1:
	dis = math.sqrt((np.linalg.norm(ap))**2 - (r * np.linalg.norm(ab))**2)
elif r >= 1:
	dis = np.linalg.norm(bp)
else:
    dis = np.linalg.norm(ap)
print(dis)
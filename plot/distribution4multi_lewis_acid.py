## 多元酸分布系数图的绘制
import matplotlib.pyplot as plt
from itertools import accumulate
from operator import mul
import numpy as np

Ka1 = 10**(-1.56)
Ka2 = 10**(-3.00)
Ka3 = 10**(-7.03)
Ka4 = 10**(-11.01)

def get_K(*args):
    return list(args)

K = [Ka1, Ka2, Ka3, Ka4]
def cumulative_product(lst):
    """_summary_

    Args:输出由列表中系数迭乘的列表
        
    Example:
        lst = [K1, K2]
        return [K1, 
        lst (_type_): 由K系数组成的列表

    Returns:
        _type_: K1*K2]
    """
    return list(accumulate(lst, mul))

def tot(H,K):
    tot_k = np.array([1] + cumulative_product(K))
    tot_h = np.array([H**i for i in range(len(tot_k)-1, -1 ,-1)])
    return tot_h * tot_k / np.dot(tot_h, tot_k)

# def delta(H, K):
#     tot_k = np.array([1] + cumulative_product(K))
#     partial_delta = np.array([H**i*v for i, v in enumerate(tot_k[::-1])])
#     return partial_delta / np.sum(partial_delta)

def cH(pH):
    return 10**-pH

pH = np.linspace(1, 14, 100)
H = cH(pH)
partn = np.array([tot(i,K) for i in H]).T
fig, ax = plt.subplots()
for i, v in enumerate(partn):
    ax.plot(pH, v)
# print(partn[0])

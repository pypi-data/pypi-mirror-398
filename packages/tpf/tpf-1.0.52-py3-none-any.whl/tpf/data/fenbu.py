import numpy as np 
import matplotlib.pyplot as plt
plt.switch_backend("TkAgg")

def mmm_std(data,show=False):
    """
    查看数据分布:
    均值，极值，标准差
    """
    mean_ =  np.around(data.mean(axis=0), 3)
    min_ = np.around(data.min(axis=0), 3)
    std_ = data.std(axis=0)

    # 均值，极值，标准差
    disc = f"mean:\n{mean_},\nmin:\n{min_},\nmax:\n{data.max(axis=0)},\nstd:\n{std_}"
    print(disc)

    
    
    if show:
        x = data.shape[1]
        x = [i for i in range(x)]
        plt.bar(x,height=mean_, width=0.8,color="#87CEFA")
        plt.legend(loc="upper right")
        plt.xlabel("feature index")
        plt.ylabel("mean")
        plt.show()

        plt.bar(x,height=std_, width=0.8,color="#3377FA")
        plt.legend(loc="upper right")
        plt.xlabel("feature index")
        plt.ylabel("std")
        plt.show()
        pass 





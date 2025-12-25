
import math 

class Estimation:
    """统计方法常见函数
    """
    def __init__(self,X=[]) -> None:
        self.X = X


    def single_distribution(self, x, mu=0, sigma=1):
        """正态分布-单个值计算
        将X代入正态分布公式求得Y
        x为均值，
        nu为方差
        """
        n = 0 - (x - mu)**2/(2*sigma)
        n = math.exp(n)

        m = math.sqrt(2*math.pi) * math.sqrt(sigma)
        m = 1/m
        m = m * n
        return m



    def normal_distribution(self, mu=0, sigma=1):
        """正态分布－全数据计算
        将X代入正态分布公式求得Y
        a为均值，
        b为方差
        """
        X = self.X 

        lx = len(X.shape)
        if lx != 1:
            raise Exception("数据的维度必须是1")

        # X = np.linspace(-5, 5, 1000)
        # print(len(X.shape))
        y = []

        for x in X:
            m = self.single_distribution(x, mu=mu, sigma=sigma)
            y.append(m)

        return y

    def likelihood(self, theta, m=10, n=7):
        """
        似然函数计算
        10次抛硬币出现7次正面向上记为一个样本，
        则m=10,n=7
        """
        y = theta**n * (1 - theta)**(m-n)
        return y 

    def posteriori_nd(self, pre, m=10, n=7, mu=0, sigma=1):
        """
        极大后验概率P(theta|x0)中的P(theta)符合正太分布
        pre为事件的全概率，位于分母，可提前计算，为常数
        10次抛硬币出现7次正面向上记为一个样本，
        则m=10,n=7
        """

        theta = self.X 
        y = []
        for x in theta:
            ll = self.likelihood(theta=x, m=m, n=n) # 似然函数
            ll = ll * self.single_distribution(x=x, mu=mu, sigma=sigma)
            ll = ll/pre
            y.append(ll)

        return y


def pow(x,y):
    """
    Return
    ---------------
    
    x的y次方
    """
    return math.pow(x,y)

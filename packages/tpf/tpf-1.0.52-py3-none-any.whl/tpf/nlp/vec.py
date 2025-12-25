"""
vec3:多个向量，向量组的 计算

"""

#-------------------------------
# 矩阵基础运算 - 开始
#-------------------------------

def matrix_multiply(m1, m2):
    """numpy实现矩阵相乘
     [ˈmeɪtrɪks]   [ˈmʌltɪplaɪ]
    import numpy as np

    from ai.box.base import matrix_multiply

    a = np.arange(6).reshape(2,3)

    b = np.arange(6).reshape(3,2)

    c=matrix_multiply(a,b)
    
    print(c)
    
    """
    # 类型转换
    if not isinstance(m1,np.ndarray):
        m1 = np.array(m1)
    if not isinstance(m2,np.ndarray):
        m2 = np.array(m2)
    
    # 参数校验
    if m1.ndim !=2 or  m2.ndim != 2 or m1.shape[1] != m2.shape[0]:
        raise Exception("矩阵形状有误  ....")
    
    # 矩阵计算
    result = np.zeros(shape=(m1.shape[0], m2.shape[1]))
    
    for i in range(m1.shape[0]): # 第1个矩阵的行
        for j in range(m2.shape[1]): # 第2个矩阵的列
            result[i, j] = m1[i, :] @ m2[:, j]   
    return result


#-------------------------------
# 矩阵基础运算 - 结束
#-------------------------------



#-------------------------------
# 补码处理 - 开始 
#-------------------------------

import numpy as np

#-------------------------------
# 补码处理 - 结束
#-------------------------------

import numpy as np



def cos_sim13(a,M, mdim=2):
    """计算向量组之间的相似度:1对多
    
    import numpy as np 
    a = np.array([1,2,3])
    print(a.shape)  # (3,)
    a= a.ravel()
    print(a.shape)  # (3,)
    b = a.reshape(-1,1)
    print(b.shape)   #(3, 1)
    b = b.ravel()
    print(b.shape)   #(3,)
    
    """
    a = np.array(a).ravel()
    a_norm  = np.linalg.norm(a)
    M = np.array(M)
    if M.ndim ==1 or mdim == 1:
        M = M.ravel()
        M_norm  = np.linalg.norm(M)   
    elif mdim == 2 :
        if M.ndim != 2:
            raise Exception("M.ndim !=2")
        M_norm  = np.linalg.norm(M, axis=1)     
    dot = M@a  
    sim = dot / (a_norm * M_norm + 1e-9)
    return sim.round(7)

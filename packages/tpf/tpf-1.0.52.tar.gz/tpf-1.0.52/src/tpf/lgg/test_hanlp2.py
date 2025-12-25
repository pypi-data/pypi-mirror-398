#-*- coding:utf-8 -*-
from jpype import *

# 注意路径的分隔,windown是;,linux是:
# startJVM(getDefaultJVMPath(), "-Djava.class.path=/opt/aisty/73_code/yijing/hanlp1.5/hanlp-1.5.0.jar:/opt/aisty/73_code/yijing/hanlp1.5","-Xms1g","-Xmx1g") # 启动JVM，Linux需替换分号;为冒号:

# 注意路径的分隔,windown是;,linux是:
#startJVM(getDefaultJVMPath(), "-Djava.class.path=/opt/aisty/73_code/yijing/hanlp1.8/hanlp-1.8.2.jar:/opt/aisty/73_code/yijing/hanlp1.8","-Xms1g","-Xmx1g") # 启动JVM，Linux需替换分号;为冒号:


startJVM(getDefaultJVMPath(), "-Djava.class.path=/wks/models/HanLP/hanlp-1.8.2-release/hanlp-1.8.2.jar:/wks/models/HanLP/hanlp-1.8.2-release","-Xms1g","-Xmx1g") # 启动JVM，Linux需替换分号;为冒号:


print("=" * 30 + "HanLP分词" + "=" * 30)
HanLP = JClass('com.hankcs.hanlp.HanLP')

# 中文分词
print(HanLP.segment('你好，欢迎在Python中调用HanLP的API'))
print("-" * 70)

shutdownJVM()
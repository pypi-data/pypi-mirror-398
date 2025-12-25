


def return_json1():
    
    output_format = """
    输出格式：json格式，包含在```json ```标记中，
    1. query字段，string类型，其value为用户的问题
    2. result字段，string类型，其value为最终回复结果
    3. thinking字段，list类型，
    3.1 列表元素为大模型的思考步骤，按思考顺序整理为list列表；
    3.2 若无思考步骤，则列表为空
    
    """
    return output_format


class SqlJiaoYi():
    def __init__(self):
        self.init_item()

    def prompt1(self,query,col_name,df_table_jiaoyi,df_table_kehu,tiaojian):
        """
        - col_name:表的列名，只能从这里面取
        - df_table_jiaoyi:交易表结构信息
        - df_table_kehu:客户表结构信息 
        
        """
        #业务列名对应字典
        bsn_col_name = yj.col_desc()

        # 输出格式增加了各种定义、约束
        output_format = yj.output_format()

        examples = yj.examples()
        
        sql_1 = self.sql_1 
        sql_2 = self.sql_2

        task1_prompt=f"""
你的任务是根据用户的问题，结合提供的材料信息，生成一个可以在oracle中执行的SQL;

你必须遵循以下约束来完成任务
1. 最终SQL按客户号PARTY_ID分组
2. 你生成的回复必须遵循上文中给定的事实信息。不可以编造信息。DO NOT MAKE UP INFORMATION.
3. 看到一个概念时尝试获取它的准确定义，并分析从哪些地方可以得到这个概念的准确描述
4. 生成一个SQL查询时，请在查询中包含全部的已知信息。
5. 列名仅限于{col_name},只能从该列名中选择相对合适的列名,可参考{bsn_col_name}
6. DT_TIME字段是'YYYY-MM-DD HH24:MI:SS'格式的字符串，请使用TO_DATE(t.DT_TIME, 'YYYY-MM-DD HH24:MI:SS')转日期后再进行日期计算


思考步骤，现在开始分步思考并输出思考的过程：
第1步思考:
理解用户的问题，然后从下面的表结构信息中找出相关的字段，并使用表信息中的列名重新描述问题 

#交易流水表结构信息如下
{df_table_jiaoyi}

#客户表结构信息如下
{df_table_kehu}

第1步思考举例：
1.用户意图:理解出用户真实的意图
2.请首先使用表结构中的“字段描述”的含义与匹配用户的问题，请逐个检索字段描述，然后与用户的问题进行匹配，然后选出可能用的列名；不要假设一个表结构中不存在的列，只能从表结构中选择一个列名
- 本外币标志 CURR_CD	
3. 重新描述问题
- 统计交易流水表中，按本外币标志（CURR_CD）区分的本币和外币交易次数

第2步思考举例：
1. 确定需要的SQL操作：用户希望进行统计，因此需要使用聚合函数（如COUNT）来计算交易次数。
2. 确定分组依据：根据本外币标志（CURR_CD）进行分组。
3. 确定输出字段：需要输出本外币标志（CURR_CD）和对应的交易次数。

第3步思考举例：
1. 确定SQL语句的基本结构

第4步思考举例，生成原始SQL：
1. 检查SQL语句的完整性和正确性，确保没有遗漏的部分。
2. 确保字段名和表名的拼写正确，并符合Oracle SQL的语法。

第5步思考举例,生成case when SQL:
1. 将第4步输出的sql按字段取值的不同转换为case when格式，有多个值的，只需要取一个值举例即可; 然后为每一个值的含义添加业务注释，注释的格式为/**/
比如将{sql_1}改写为{sql_2}
2. 所在where语句后面的条件，可参考{tiaojian},同时将所有的条件全部转移到case when 语句中，然后取消整个SQL的where条件


你必须遵循以下约束来完成任务
1. 最终SQL按客户号PARTY_ID分组
2. 你生成的回复必须遵循上文中给定的事实信息。不可以编造信息。DO NOT MAKE UP INFORMATION.
3. 看到一个概念时尝试获取它的准确定义，并分析从哪些地方可以得到这个概念的准确描述
4. 生成一个SQL查询时，请在查询中包含全部的已知信息。

输出格式
{output_format}

用户问题
{query}

"""
        return task1_prompt


    def tiaojian(self):
        _tiaojian = {
            "IP归属地国别不等于中国":"t.TRCD_COUNTRY != 'CHN'",
            "IP归属地国别不等于CHN":"t.TRCD_COUNTRY != 'CHN'",
            "交易发生地国别<>CHN/Z01/Z02/Z03":"t.TRCD_COUNTRY not in ('CHN','Z01','Z02','Z03')",
            "交易发生地在新疆":"t.TRCD_COUNTRY in ('CN-XJ','XJ')",
            "交易发生地在台湾、香港、越南、老挝、泰国、柬埔寨、缅甸":"t.TRCD_COUNTRY not in ('TWN','HKG','VNM','LAO','THA','KHM','MMR')",
            "跨境":"t.OVERAREA_IND='1'",
            "交易发生地非境内":"t.OVERAREA_IND='1' and t.TRCD_COUNTRY not in ('CHN','Z01','Z02','Z03') ",
            "境内":"t.OVERAREA_IND='0'",
            "现金":"t.CASH_IND='00'",
            "转账":"t.CASH_IND='01'",
            "代发工资":"",
            "代发工资":" t.TX_CD = '8001'",
            "非(代发工资,部分提前还贷,全部提前还,贷款放款,还贷)":" t.TX_CD NOT IN ('8001','3013','3014','6002','3010') ",
            "付交易":"t.TSDR='02'",
            "交易渠道=ATM":"t.CHANNEL='4'",
            "交易渠道为ATM或其他自助设备":"AND t.CHANNEL IN ('4', '02')",
            "交易渠道=POS":"t.CHANNEL='5'",
            "对方不是我行客户":"t.OPP_ISPARTY='0'",
            "对方是我行客户":"t.OPP_ISPARTY='1'",
            "交易对手非行内":"t.OPP_ISPARTY='0'",
            "交易主体是商户的实际控制人":"AND EXISTS (\n SELECT 1 \n FROM BB11_MCHT_INFO   B, /*商户信息*/\n     BH11_PARTY_REAL   C  /*商户关系*/\n WHERE t.MERCH_NO = B.MERCH_NO AND B.PARTY_ID  =  C.PARTY_ID AND C.REAL_TYPE = '5') ",
            "是否我行商户=是":"t.IS_MERCH='1' ",
            "交易对手客户类型对私":"AND t.OPP_PARTY_CLASS_CD = 'I'",
            "交易对手凭证类型是贷记卡":"AND t.TCAT ='120016' ",
            "交易对手是否我行商户=是":"AND EXISTS(select 1 \n   from BB11_TRANS r\n  where r.PARTY_ID = t.OPP_PARTY_ID and r.IS_MERCH='1' )",
            "非同名":"AND T.PARTY_NAME <> T.TCNM ",
            "非同客户":"AND T.PARTY_ID <>  T.OPP_PARTY_ID ",
            "同一交易对手":"AND T.PARTY_ID = T.OPP_PARTY_ID ",
            "交易对手客户类型为对公且非同名":"AND t.OPP_PARTY_CLASS_CD='C' AND T.PARTY_NAME <> T.TCNM ",
            "资金来源或用途含有'借款'":"AND t.CRSP like '%借款%' ",
            "异地":"AND SUBSTR(T.TRCD_AREA,1,4) <>  SUBSTR(T.CFRC_AREA,1,4) /*交易发生地<>对方地区*/",
            "交易发生地<>对方地区":"AND SUBSTR(T.TRCD_AREA,1,4) <>  SUBSTR(T.CFRC_AREA,1,4) /*交易发生地<>对方地区*/",
            "最近一次 【本/外】币 转账 收交易 （交易对手客户类型为对公且非同名、资金来源或用途含有‘借款'）与最近一次付交易的时间间隔（单位：小时）":f"{self.sql_time1}",
            "交易金额为万元整数倍":" MOD(t.CNY_AMT, 10000) = 0 ",
            "交易渠道：网银":"AND t.CHANNEL = '2' ",
            "天数":"count(t.TSTM)",
            "手机银行":"AND t.CHANNEL = '6' ",
            "交易渠道=网银/手机银行":"AND t.CHANNEL IN ('2', '6') ",
            "借记卡":"AND t.CARD_TYPE = '10' ",
            "高危":"AND EXISTS (\n     SELECT 1\n     FROM\n         MP01_CMP_PARAM_VAL C\n     WHERE\n         C.PARAM1     = T.CFRC_AREA\n     AND C.PARMVALKEY = 'sys0010'/*恐怖地区高风险地区2018-71号文*/\n     )",
            "通道国":"AND T.TRCD_COUNTRY IN  ('AFG','BRN','IDN','IRN','IRQ','KAZ','KGZ','MYS','PAK','SYR','THA','TJK','TKM','TUR','UZB','VNM')",
            "通道省":"AND SUBSTR(T.TRCD_AREA,1,3) IN ('650','610','510','530','500','450','410','150','230','440','310')",
            "贩毒":"AND EXISTS (\n          SELECT 1\n          FROM\n     BB15_BLACK_AREALIST C\n          WHERE\n              C.AREAID = T.TRCD_AREA\n          AND SUBSTR(C.AREA_TYPECD,1,1) = '1'\n      )",
            "涉毒高危":"AND EXISTS (\n          SELECT 1\n          FROM\n     BB15_BLACK_AREALIST C\n          WHERE\n              C.AREAID = T.TRCD_AREA\n          AND SUBSTR(C.AREA_TYPECD,1,1) = '1'\n      )",
            "走私":"AND EXISTS (\n          SELECT 1\n          FROM\n     BB15_BLACK_AREALIST C\n          WHERE\n              C.AREAID = T.TRCD_AREA\n          AND SUBSTR(C.AREA_TYPECD,2,1) = '2'\n      )",
            "恐怖活动":"AND EXISTS (\n          SELECT 1\n          FROM\n     BB15_BLACK_AREALIST C\n          WHERE\n              C.AREAID = T.TRCD_AREA\n          AND SUBSTR(C.AREA_TYPECD,3,1) = '3'\n      )",
            "涉恐地区":"AND EXISTS (\n          SELECT 1\n          FROM\n     BB15_BLACK_AREALIST C\n          WHERE\n              C.AREAID = T.TRCD_AREA\n          AND SUBSTR(C.AREA_TYPECD,3,1) = '3'\n      )",
            "涉恐":"AND EXISTS (\n          SELECT 1\n          FROM\n     BB15_BLACK_AREALIST C\n          WHERE\n              C.AREAID = T.TRCD_AREA\n          AND SUBSTR(C.AREA_TYPECD,3,1) = '3'\n      )",
            "赌博":"AND EXISTS (\n          SELECT 1\n          FROM\n     BB15_BLACK_AREALIST C\n          WHERE\n              C.AREAID = T.TRCD_AREA\n          AND SUBSTR(C.AREA_TYPECD,4,1) = '4'\n      )",
            "避税":"AND EXISTS (\n          SELECT 1\n          FROM\n     BB15_BLACK_AREALIST C\n          WHERE\n              C.AREAID = T.TRCD_AREA\n          AND SUBSTR(C.AREA_TYPECD,5,1) = '5'\n      )",
            "涉外收支交易代码非空":"AND t.TSCT IS NOT NULL ",
            "通常交易不频繁账户(交易次数少于10次)":"AND t.PARTY_ID IN (\n     SELECT distinct \n       PARTY_ID\n     FROM\n       BB11_TRANS_SMALL_01\n     WHERE\n       TSTM <= '@statisdt@'\n       and TSTM > to_char(\n         to_date('@statisdt@', 'YYYY-MM-DD') - to_number('@v_days@'),\n         'YYYY-MM-DD'\n       )\n       and PARTY_CLASS_CD = '@party_class_cd@'\n     GROUP BY\n       PARTY_ID\n     HAVING\n       COUNT(*) < 10\n       /*通常交易不频繁账户(交易次数少于10次)*/\n   )",
            "账户状态=正常":"p.PARTY_STATUS_CD = '0' ",
            "商户":{
              "同义词":["商户类型","商户标识"],
              "关联表":"join BB11_PARTY p on p.PARTY_ID = t.PARTY_ID",
              "判断条件":"AND p.CDD_TYPE='03'",
            },
            "异常时间":{
              "描述":"时间范围在晚上23点至第二天凌晨6点之间",
              "判断条件":"TO_NUMBER(TO_CHAR(TO_DATE(t.DT_TIME, 'YYYY-MM-DD HH24:MI:SS'), 'HH24') >= 23 OR TO_NUMBER(TO_CHAR(TO_DATE(t.DT_TIME, 'YYYY-MM-DD HH24:MI:SS'), 'HH24') < 6  ",
            },
            "直贴":"AND t.TX_CD='6001' ",
            "保险":"t.TCNM like '%保险%' ",
            "证券":"AND t.TX_TYPE_CD IN ('03','04','05')/*股票类交易,理财类交易,其他投资类交易*/ ",
            "售汇":"AND t.TX_CD='5002' /*aml交易代码：售汇5002*/ ",
            "购汇":"AND t.TX_CD='5002' /*aml交易代码：售汇5002*/ ",
            "节日短期内":"AND (\n         SELECT\n             COUNT(1)\n         FROM\n             MP01_HOLIDAY  A\n         WHERE\n             A.DAYKEY >= XDATE_MINUS_DAY(to_char(to_date('@statisdt@','YYYY-MM-DD')-to_number('@v_days@'),'YYYY-MM-DD')  ,-3)\n         AND A.DAYKEY <= XDATE_MINUS_DAY('@statisdt@' ,3)\n         AND A.ISHOLIDAY = '1'\n         ) >= 1",
            
        }
        return _tiaojian
        
         

    def init_item(self):
        self.sql_time1="""NVL((MAX(
    CASE
      WHEN CURR_CD='1' /*本币*/
      AND t.TSDR='01' /*收交易*/
      AND t.OPP_PARTY_CLASS_CD='C' /*交易对手客户类型为对公*/
      AND t.PARTY_NAME != t.TCNM /*非同名交易*/
      AND t.CRSP like '%借款%' /*资金来源或用途含有'借款'*/
      AND t.CASH_IND='01' /*转账交易*/
      THEN TO_DATE(t.DT_TIME, 'YYYY-MM-DD HH24:MI:SS')
    END
  ) - MAX(
    CASE
      WHEN CURR_CD='1' /*本币*/
      AND t.TSDR='02' /*付交易*/
      THEN TO_DATE(t.DT_TIME, 'YYYY-MM-DD HH24:MI:SS')
    END
  )) * 24,0) AS BB_ZZ_SH_C,
  NVL((MAX(
    CASE
      WHEN CURR_CD='2' /*外币*/
      AND t.TSDR='01' /*收交易*/
      AND CURR_CD='2' AND t.OPP_PARTY_CLASS_CD='C' /*交易对手客户类型为对公*/
      AND t.PARTY_NAME != t.TCNM /*非同名交易*/
      AND t.CRSP like '%借款%' /*资金来源或用途含有'借款'*/
      AND t.CASH_IND='01' /*转账交易*/
      THEN TO_DATE(t.DT_TIME, 'YYYY-MM-DD HH24:MI:SS')
    END
  ) - MAX(
    CASE
      WHEN CURR_CD='2' /*外币*/
      AND t.TSDR='02' /*付交易*/
      THEN TO_DATE(t.DT_TIME, 'YYYY-MM-DD HH24:MI:SS')
    END
  )) * 24,0) AS WB_ZZ_SH_C"""
        self.sql_1 = """SELECT PARTY_ID, CURR_CD, COUNT(*) AS TRANSACTION_COUNT
FROM BB11_TRANS_SMALL_01 bts 
GROUP BY PARTY_ID, CURR_CD"""
        self.sql_2 = """select 
  t.party_id,
  COUNT( 
    CASE
      WHEN CURR_CD='1'   /*币种，本币*/
      THEN 1  
    END
    ) AS BB_CT,
COUNT( 
    CASE
      WHEN CURR_CD='2'    /*币种，外币*/
      THEN 1  
    END
    ) AS WB_CT
from BB11_TRANS_SMALL_01 t 
GROUP BY t.party_id """
        
        
    def col_desc(self):
        """存放LLM不容易从表定义中识别的列"""
        bsn_col_name = {
            "币种":"CURR_CD",
            "IP地址":"TRAN_IP",
            "ip归属地国别":"TRCD_COUNTRY",
            "对手账户":"t.TCAC",
        }
        return bsn_col_name
        

    def jiaoyi_desc(self):
        # label_names = ["是否本币",	"是否跨境",	"交易媒介",	"交易币种",	"交易去向",	"是否跨行",	"统计对象及方法"]
        jiaoyi_dict = {}
        jiaoyi_dict["交易币种"] = {"col_name":"CRTP","desc":["交易币种","交易币种个数"]}
        jiaoyi_dict["是否本币"] = {"col_name":"CURR_CD","desc":["本币外币","是否本币"],"values":{"本币":"1","外币":"2"}}
        
        jiaoyi_dict["是否跨境"] = {"col_name":"OVERAREA_IND","desc":["是否跨境","境内境外标识"],"values":{"境内":"0","境外":"1"}}
        
        jiaoyi_dict["交易媒介"] = {"col_name":"CASH_IND","desc":["现金","转账","不分"],"values":{"现金":"00","转帐":"02","不分":['00','01']}}
        jiaoyi_dict["交易去向"] = {"col_name":"TSDR","desc":["收交易","付交易","交易(不分)","收/付/不分"],"values":{"收交易":"01","付交易":"02","不分":['01','02']}}
        
        jiaoyi_dict["交易渠道"] = {"col_name":"TX_CD","desc":["第三方支付"],"values":{"第三方支付-消费":"9001","第三方支付-充值":"9002","第三方支付-提现":"9003","第三方支付-转账":"9004"}}
        
        
        jiaoyi_dict["统计对象及方法"] = {"金额":"sum","笔数":"count",
                                  "对手账户":{"col_name":"TCAC", "func":"count", "desc":["对手账户","对方账户"]},
                                  "对手非同名账户":{"col_name":"TCNM", "func":"count", "desc":["对手非同名账户","对方非同名账户"]},
                                  "交易发生地国别":{"col_name":"TRCD_COUNTRY", "func":"count", "desc":["交易发生地国别","交易发生地国家"]},
                                  "交易IP地址":{"col_name":"TRAN_IP", "func":"count", "desc":["交易IP地址","交易的IP地址个数"]},
                                  "交易发生地":{"col_name":"TRCD_AREA", "func":"count", "desc":["交易发生地","交易发生地行政区"]},
                                  "对方所在地区":{"col_name":"CFRC_AREA", "func":"count", "desc":["对方所在地区","对方所在地"]},
                                 }
        return jiaoyi_dict


    def output_format(self):
        # 输出格式增加了各种定义、约束
        _output_format = f"""
        以JSON格式输出。包含的字段有：
        1. desc字段中说明生成sql的逻辑，简单说明
        2. sql1:原始SQL,第4步思考直接根据用户问题生成的SQL
        (1) sql中的列名带表名前缀，交易流水表的前缀为t
        (2) 每一个字段,每一个条件，都要加注释说明其业务含义，注释以/*开头，以*/结尾
        (3) 再一次检查SQL语法，比如括号一定要成对，确保SQL语句可执行
        
        3. sql2:case when sql,第5步思考转换为case when 格式的SQL
        (1) sql中的列名带表名前缀，交易流水表的前缀为t
        (2) 每一个字段,每一个条件，都要加注释说明其业务含义，注释以/*开头，以*/结尾
        (3) 默认只取折人民币金额
        (4) 再一次检查SQL语法，比如括号一定要成对，确保SQL语句可执行
        
        
        输出中只包含用户提及的字段，不要猜测任何用户未直接提及的字段，不输出值为null的字段。
        """
        return _output_format


    def examples(self):
        _examples = """
【本/外】币【收/付/双方】交易次数汇总（交易渠道：非柜面）:{{
  "desc": "根据用户需求，统计交易流水表中按客户号分组的本外币、收付双方的交易次数，且交易渠道为非柜面。从表结构中识别出相关字段：CURR_CD(本外币标志)、TSDR(收付标志)、CHANNEL(交易渠道)。非柜面交易渠道在字段描述中未明确给出具体值，但柜面渠道值为'1'，因此非柜面应为非'1'的值。",
  "sql1": "SELECT \n  t.PARTY_ID, /** 客户号 **/\n  t.CURR_CD, /** 本外币标志：1-本币，2-外币 **/\n  t.TSDR, /** 收付标志：01-收，02-付 **/\n  COUNT(*) AS TRANSACTION_COUNT /** 交易次数 **/\nFROM BB11_TRANS_SMALL_01 t \nWHERE t.CHANNEL != '1' /** 交易渠道非柜面 **/\nGROUP BY t.PARTY_ID, t.CURR_CD, t.TSDR",
  "sql2": "SELECT \n   t.PARTY_ID, /** 客户号 **/\n   COUNT(CASE WHEN t.CURR_CD='1' AND t.TSDR='01' AND t.CHANNEL != '1' THEN 1 END) AS BB_RECEIVE_CT, /** 本币收非柜面交易次数 **/\n   COUNT(CASE WHEN t.CURR_CD='1' AND t.TSDR='02' AND t.CHANNEL != '1' THEN 1 END) AS BB_PAY_CT, /** 本币付非柜面交易次数 **/\n   COUNT(CASE WHEN t.CURR_CD='2' AND t.TSDR='01' AND t.CHANNEL != '1' THEN 1 END) AS WB_RECEIVE_CT, /** 外币收非柜面交易次数 **/\n   COUNT(CASE WHEN t.CURR_CD='2' AND t.TSDR='02' AND t.CHANNEL != '1' THEN 1 END) AS WB_PAY_CT /** 外币付非柜面交易次数 **/\n FROM BB11_TRANS_SMALL_01 t \n GROUP BY t.PARTY_ID"
}},
【本/外】币交易的IP地址个数汇总:{{
  "desc": "根据用户问题，统计交易流水表中按本外币标志（CURR_CD）区分的本币和外币交易的IP地址（TRAN_IP）个数，并按客户号（PARTY_ID）分组。",
  "sql1": "SELECT \n  t.PARTY_ID, /*客户号*/\n  t.CURR_CD, /*币种标志*/\n  COUNT(DISTINCT t.TRAN_IP) AS IP_COUNT /*IP地址个数*/\nFROM BB11_TRANS t \nGROUP BY t.PARTY_ID, t.CURR_CD",
  "sql2": "SELECT \n  t.PARTY_ID, /*客户号*/\n  COUNT( \n    CASE \n      WHEN t.CURR_CD='1' /*币种，本币*/\n      THEN t.TRAN_IP \n    END\n  ) AS LOCAL_IP_COUNT, /*本币交易的IP地址个数*/\n  COUNT( \n    CASE \n      WHEN t.CURR_CD='2' /*币种，外币*/\n      THEN t.TRAN_IP \n    END\n  ) AS FOREIGN_IP_COUNT /*外币交易的IP地址个数*/\nFROM BB11_TRANS t \nGROUP BY t.PARTY_ID"
}},
【本/外】币交易次数汇总（ip归属地国别≠CHN）:{{
  "desc": "统计IP归属地不为中国的本币和外币交易次数，按客户号分组",
  "sql1": "SELECT \n    t.PARTY_ID, /** 我行客户号 */\n    t.CURR_CD, /** 本外币标志 1:本币 2:外币 */\n    COUNT(*) AS TRANSACTION_COUNT\nFROM \n    BB11_TRANS_SMALL_01 t\nWHERE \n    t.TRCD_COUNTRY != 'CHN' /** IP归属地国别不等于中国 */\nGROUP BY \n    t.PARTY_ID, \n    t.CURR_CD",
  "sql2": "SELECT \n    t.PARTY_ID, /** 我行客户号 */\n    COUNT(CASE WHEN t.CURR_CD = '1' THEN 1 END) AS CNY_TRANS_COUNT, /** 本币交易次数 */\n    COUNT(CASE WHEN t.CURR_CD = '2' THEN 1 END) AS FOR_TRANS_COUNT /** 外币交易次数 */\nFROM \n    BB11_TRANS_SMALL_01 t\nWHERE \n    t.TRCD_COUNTRY != 'CHN' /** IP归属地国别不等于中国 */\nGROUP BY \n    t.PARTY_ID"
}},
外币跨境交易次数汇总（交易币种为MYR/THB/TRY/VND/SYP/AZN/PKR/AFN/KZT/KGS/UZS/TJS/SR/MMK/JPY/EUR）:{{
  "desc": "统计外币跨境交易次数，限定特定外币币种，按客户号分组",
  "sql1": "SELECT \n    t.PARTY_ID, /** 我行客户号 */\n    COUNT(*) AS TRANSACTION_COUNT\nFROM \n    BB11_TRANS_SMALL_01 t\nWHERE \n    t.CURR_CD = '2' /** 外币交易 */\n    AND t.OVERAREA_IND = '1' /** 跨境交易 */\n    AND t.CRTP IN ('MYR','THB','TRY','VND','SYP','AZN','PKR','AFN','KZT','KGS','UZS','TJS','SR','MMK','JPY','EUR') /** 指定外币币种 */\nGROUP BY \n    t.PARTY_ID",
  "sql2": "SELECT \n    t.PARTY_ID, /** 我行客户号 */\n    COUNT(CASE WHEN t.CURR_CD = '2' AND t.OVERAREA_IND = '1' AND t.CRTP IN ('MYR','THB','TRY','VND','SYP','AZN','PKR','AFN','KZT','KGS','UZS','TJS','SR','MMK','JPY','EUR') THEN 1 END) AS FOREIGN_CROSSBORDER_COUNT /** 外币跨境交易次数 */\nFROM \n    BB11_TRANS_SMALL_01 t\nGROUP BY \n    t.PARTY_ID"
}},
现金付交易金额汇总（交易渠道=ATM，交易发生地国别<>CHN.Z01.Z02.Z03，取折美金额）:{{
  "desc": "统计现金付交易金额，限定ATM渠道和非CHN.Z01.Z02.Z03地区，按客户号分组",
  "sql1": "SELECT \n    t.PARTY_ID, /** 我行客户号 */\n    SUM(t.USD_AMT) AS TOTAL_USD_AMOUNT /** 折美元金额合计 */\nFROM \n    BB11_TRANS_SMALL_01 t\nWHERE \n    t.CASH_IND = '00' /** 现金交易 */\n    AND t.CHANNEL = '4' /** ATM渠道 */\n    AND t.TSDR = '02' /** 付交易 */\n    AND t.TRCD_COUNTRY NOT IN ('CHN', 'Z01','Z02', 'Z03') /** 非指定地区 */\nGROUP BY \n    t.PARTY_ID",
  "sql2": "SELECT \n    t.PARTY_ID, /** 我行客户号 */\n    SUM(CASE WHEN t.CASH_IND = '00' AND t.CHANNEL = '4' AND t.TSDR = '02' AND t.TRCD_COUNTRY NOT IN ('CHN', 'Z01','Z02', 'Z03') THEN t.USD_AMT ELSE 0 END) AS CASH_ATM_PAYMENT_USD_AMOUNT /** 现金ATM付交易折美元金额(非指定地区) */\nFROM \n    BB11_TRANS_SMALL_01 t\nGROUP BY \n    t.PARTY_ID"
}},
转账【本/外】币付交易【次数/金额】汇总（交易发生地行政区划代码前四位≠交易去向行政区划代码前四位）:{{
  "desc": "统计转账方式下的本币/外币付交易次数和金额，限定条件为交易发生地与交易去向地行政区划代码前四位不同。使用CURR_CD区分币种，TSDR判断付交易，CASH_IND判断转账交易，TRCD_AREA和TX_GO_AREA判断异地交易。",
  "sql1": "SELECT \n  t.PARTY_ID, /*客户号*/\n  t.CURR_CD, /*币种，1:本币 2:外币*/\n  COUNT(*) AS TRANSACTION_COUNT, /*交易次数*/\n  SUM(t.CNY_AMT) AS CNY_AMOUNT, /*折人民币金额*/\n  SUM(t.USD_AMT) AS USD_AMOUNT /*折美元金额*/\nFROM BB11_TRANS_SMALL_01 t\nWHERE t.TSDR = '02' /*付交易*/\n  AND t.CASH_IND = '01' /*转账交易*/\n  AND SUBSTR(t.TRCD_AREA,1,4) <> SUBSTR(t.TX_GO_AREA,1,4) /*交易发生地≠交易去向地*/\nGROUP BY t.PARTY_ID, t.CURR_CD",
  "sql2": "SELECT \n  t.PARTY_ID, /*客户号*/\n  COUNT(CASE WHEN t.CURR_CD='1' AND t.TSDR='02' AND t.CASH_IND='01' AND SUBSTR(t.TRCD_AREA,1,4) <> SUBSTR(t.TX_GO_AREA,1,4) THEN 1 END) AS BB_TRANSFER_PAY_COUNT, /*本币转账付交易次数*/\n  COUNT(CASE WHEN t.CURR_CD='2' AND t.TSDR='02' AND t.CASH_IND='01' AND SUBSTR(t.TRCD_AREA,1,4) <> SUBSTR(t.TX_GO_AREA,1,4) THEN 1 END) AS WB_TRANSFER_PAY_COUNT, /*外币转账付交易次数*/\n  SUM(CASE WHEN t.CURR_CD='1' AND t.TSDR='02' AND t.CASH_IND='01' AND SUBSTR(t.TRCD_AREA,1,4) <> SUBSTR(t.TX_GO_AREA,1,4) THEN t.CNY_AMT ELSE 0 END) AS BB_CNY_AMOUNT, /*本币折人民币金额*/\n  SUM(CASE WHEN t.CURR_CD='2' AND t.TSDR='02' AND t.CASH_IND='01' AND SUBSTR(t.TRCD_AREA,1,4) <> SUBSTR(t.TX_GO_AREA,1,4) THEN t.CNY_AMT ELSE 0 END) AS WB_CNY_AMOUNT, /*外币折人民币金额*/\n  SUM(CASE WHEN t.CURR_CD='1' AND t.TSDR='02' AND t.CASH_IND='01' AND SUBSTR(t.TRCD_AREA,1,4) <> SUBSTR(t.TX_GO_AREA,1,4) THEN t.USD_AMT ELSE 0 END) AS BB_USD_AMOUNT, /*本币折美元金额*/\n  SUM(CASE WHEN t.CURR_CD='2' AND t.TSDR='02' AND t.CASH_IND='01' AND SUBSTR(t.TRCD_AREA,1,4) <> SUBSTR(t.TX_GO_AREA,1,4) THEN t.USD_AMT ELSE 0 END) AS WB_USD_AMOUNT /*外币折美元金额*/\nFROM BB11_TRANS_SMALL_01 t\nGROUP BY t.PARTY_ID"
}},
【本/外】币付交易【次数/金额】汇总（交易发生地非境内）:{{
  "desc": "根据用户问题，需要统计本币和外币的付交易次数和折人民币金额，且交易发生地非境内。从表结构中，我们找到以下相关字段：CURR_CD(本外币标志), TSDR(收付标志), CNY_AMT(折人民币金额), TRCD_COUNTRY(交易发生地国别), OVERAREA_IND(是否跨境交易)。用户要求按PARTY_ID分组，且默认只取折人民币金额。",
  "sql1": "SELECT \n  t.PARTY_ID, /*客户号*/\n  t.CURR_CD, /*本外币标志,1:本币,2:外币*/\n  COUNT(*) AS TRANSACTION_COUNT, /*付交易次数*/\n  SUM(t.CNY_AMT) AS CNY_AMOUNT /*折人民币金额*/\nFROM BB11_TRANS_SMALL_01 t\nWHERE t.TSDR = '02' /*付交易*/\n  AND t.OVERAREA_IND = '1' /*跨境交易*/\n  AND t.TRCD_COUNTRY NOT IN ('CHN','Z01','Z02','Z03') /*交易发生地非境内*/\nGROUP BY t.PARTY_ID, t.CURR_CD",
  "sql2": "SELECT \n  t.PARTY_ID, /*客户号*/\n  COUNT(CASE WHEN t.CURR_CD = '1' AND t.TSDR = '02' AND t.OVERAREA_IND = '1' AND t.TRCD_COUNTRY NOT IN ('CHN','Z01','Z02','Z03') THEN 1 END) AS BB_TRANS_COUNT, /*本币付交易次数(交易发生地非境内)*/\n  COUNT(CASE WHEN t.CURR_CD = '2' AND t.TSDR = '02' AND t.OVERAREA_IND = '1' AND t.TRCD_COUNTRY NOT IN ('CHN','Z01','Z02','Z03') THEN 1 END) AS WB_TRANS_COUNT, /*外币付交易次数(交易发生地非境内)*/\n  SUM(CASE WHEN t.CURR_CD = '1' AND t.TSDR = '02' AND t.OVERAREA_IND = '1' AND t.TRCD_COUNTRY NOT IN ('CHN','Z01','Z02','Z03') THEN t.CNY_AMT END) AS BB_CNY_AMOUNT, /*本币付交易折人民币金额(交易发生地非境内)*/\n  SUM(CASE WHEN t.CURR_CD = '2' AND t.TSDR = '02' AND t.OVERAREA_IND = '1' AND t.TRCD_COUNTRY NOT IN ('CHN','Z01','Z02','Z03') THEN t.CNY_AMT END) AS WB_CNY_AMOUNT /*外币付交易折人民币金额(交易发生地非境内)*/\nFROM BB11_TRANS_SMALL_01 t\nGROUP BY t.PARTY_ID"
}},
【本/外】币转账【收/付】交易次数汇总（交易对手是否行内=否）:{{
  "desc": "根据用户问题，需要统计本外币转账收付交易次数，且交易对手不是行内客户。首先从表结构中识别相关字段：CURR_CD(本外币标志)、TSDR(收付标志)、OPP_ISPARTY(对方是否我行客户)。然后按PARTY_ID分组，统计不同条件下的交易次数。",
  "sql1": "SELECT \n  t.PARTY_ID, /*客户号*/\n  t.CURR_CD, /*本外币标志,1:本币,2:外币*/\n  t.TSDR, /*收付标志(01:收02:付)*/\n  COUNT(*) AS TRANSACTION_COUNT /*交易次数*/\nFROM BB11_TRANS_SMALL_01 t\nWHERE t.OPP_ISPARTY = '0' /*对方不是我行客户*/\nGROUP BY t.PARTY_ID, t.CURR_CD, t.TSDR",
  "sql2": "SELECT \n  t.PARTY_ID, /*客户号*/\n  COUNT(\n    CASE\n      WHEN t.CURR_CD = '1' AND t.TSDR = '01' AND CASH_IND='01'   AND t.OPP_ISPARTY = '0' /*本币收交易且对手非行内*/\n      THEN 1\n    END\n  ) AS BB_RECEIVE_CT,\n  COUNT(\n    CASE\n      WHEN t.CURR_CD = '1' AND t.TSDR = '02' AND CASH_IND='01'   AND t.OPP_ISPARTY = '0' /*本币付交易且对手非行内*/\n      THEN 1\n    END\n  ) AS BB_PAY_CT,\n  COUNT(\n    CASE\n      WHEN t.CURR_CD = '2' AND t.TSDR = '01' AND CASH_IND='01'   AND t.OPP_ISPARTY = '0' /*外币收交易且对手非行内*/\n      THEN 1\n    END\n  ) AS WB_RECEIVE_CT,\n  COUNT(\n    CASE\n      WHEN t.CURR_CD = '2' AND t.TSDR = '02' AND CASH_IND='01'   AND t.OPP_ISPARTY = '0' /*外币付交易且对手非行内*/\n      THEN 1\n    END\n  ) AS WB_PAY_CT\nFROM BB11_TRANS_SMALL_01 t\nGROUP BY t.PARTY_ID"
}},
【本/外】币转账【交易/收交易/付交易】【次数/金额/对手账户数】汇总（交易对手客户类型：对私）:{{
  "desc": "根据用户问题，需要统计本外币转账交易中收付交易的次数、金额和对手账户数，且交易对手客户类型为对私。从表结构中识别相关字段：CURR_CD(本外币标志)、TSDR(收付标志)、OPP_PARTY_CLASS_CD(对方客户类型)、CNY_AMT(折人民币金额)、TCAC(对方账号)。按PARTY_ID分组，统计不同条件下的交易情况。",
  "sql1": "SELECT \n  t.PARTY_ID, /*客户号*/\n  t.CURR_CD, /*本外币标志,1:本币,2:外币*/\n  t.TSDR, /*收付标志(01:收02:付)*/\n  COUNT(*) AS TRANSACTION_COUNT, /*交易次数*/\n  SUM(t.CNY_AMT) AS TRANSACTION_AMOUNT, /*交易金额(折人民币)*/\n  COUNT(DISTINCT t.TCAC) AS OPP_ACCOUNT_COUNT /*对手账户数*/\nFROM BB11_TRANS_SMALL_01 t\nWHERE t.OPP_PARTY_CLASS_CD = 'I' /*对方客户类型为对私*/\n  AND t.CASH_IND = '01' /*转账交易*/\nGROUP BY t.PARTY_ID, t.CURR_CD, t.TSDR",
  "sql2": "SELECT \n  t.PARTY_ID, /*客户号*/\n  /*本币交易统计*/\n  COUNT(CASE WHEN t.CURR_CD = '1' AND t.TSDR = '01' AND t.OPP_PARTY_CLASS_CD = 'I' AND t.CASH_IND = '01' THEN 1 END) AS BB_RECEIVE_COUNT, /*本币收交易次数*/\n  SUM(CASE WHEN t.CURR_CD = '1' AND t.TSDR = '01' AND t.OPP_PARTY_CLASS_CD = 'I' AND t.CASH_IND = '01' THEN t.CNY_AMT ELSE 0 END) AS BB_RECEIVE_AMOUNT, /*本币收交易金额*/\n  COUNT(DISTINCT CASE WHEN t.CURR_CD = '1' AND t.TSDR = '01' AND t.OPP_PARTY_CLASS_CD = 'I' AND t.CASH_IND = '01' THEN t.TCAC END) AS BB_RECEIVE_ACCOUNT_COUNT, /*本币收交易对手账户数*/\n  \n  COUNT(CASE WHEN t.CURR_CD = '1' AND t.TSDR = '02' AND t.OPP_PARTY_CLASS_CD = 'I' AND t.CASH_IND = '01' THEN 1 END) AS BB_PAY_COUNT, /*本币付交易次数*/\n  SUM(CASE WHEN t.CURR_CD = '1' AND t.TSDR = '02' AND t.OPP_PARTY_CLASS_CD = 'I' AND t.CASH_IND = '01' THEN t.CNY_AMT ELSE 0 END) AS BB_PAY_AMOUNT, /*本币付交易金额*/\n  COUNT(DISTINCT CASE WHEN t.CURR_CD = '1' AND t.TSDR = '02' AND t.OPP_PARTY_CLASS_CD = 'I' AND t.CASH_IND = '01' THEN t.TCAC END) AS BB_PAY_ACCOUNT_COUNT, /*本币付交易对手账户数*/\n  \n  /*外币交易统计*/\n  COUNT(CASE WHEN t.CURR_CD = '2' AND t.TSDR = '01' AND t.OPP_PARTY_CLASS_CD = 'I' AND t.CASH_IND = '01' THEN 1 END) AS WB_RECEIVE_COUNT, /*外币收交易次数*/\n  SUM(CASE WHEN t.CURR_CD = '2' AND t.TSDR = '01' AND t.OPP_PARTY_CLASS_CD = 'I' AND t.CASH_IND = '01' THEN t.CNY_AMT ELSE 0 END) AS WB_RECEIVE_AMOUNT, /*外币收交易金额*/\n  COUNT(DISTINCT CASE WHEN t.CURR_CD = '2' AND t.TSDR = '01' AND t.OPP_PARTY_CLASS_CD = 'I' AND t.CASH_IND = '01' THEN t.TCAC END) AS WB_RECEIVE_ACCOUNT_COUNT, /*外币收交易对手账户数*/\n  \n  COUNT(CASE WHEN t.CURR_CD = '2' AND t.TSDR = '02' AND t.OPP_PARTY_CLASS_CD = 'I' AND t.CASH_IND = '01' THEN 1 END) AS WB_PAY_COUNT, /*外币付交易次数*/\n  SUM(CASE WHEN t.CURR_CD = '2' AND t.TSDR = '02' AND t.OPP_PARTY_CLASS_CD = 'I' AND t.CASH_IND = '01' THEN t.CNY_AMT ELSE 0 END) AS WB_PAY_AMOUNT, /*外币付交易金额*/\n  COUNT(DISTINCT CASE WHEN t.CURR_CD = '2' AND t.TSDR = '02' AND t.OPP_PARTY_CLASS_CD = 'I' AND t.CASH_IND = '01' THEN t.TCAC END) AS WB_PAY_ACCOUNT_COUNT /*外币付交易对手账户数*/\nFROM BB11_TRANS_SMALL_01 t\nGROUP BY t.PARTY_ID"
}},
私转公【本/外】币转账收交易【次数/金额】汇总:{{
  "desc": "根据用户问题，需要统计私转公的本外币转账收交易的次数和金额。从表结构中识别相关字段：PARTY_CLASS_CD(客户类型)、OPP_PARTY_CLASS_CD(对方客户类型)、CURR_CD(本外币标志)、TSDR(收付标志)、CASH_IND(现钞标志)、CNY_AMT(折人民币金额)。按PARTY_ID分组，统计不同条件下的交易情况。",
  "sql1": "SELECT \n  t.PARTY_ID, /*客户号*/\n  t.CURR_CD, /*本外币标志,1:本币,2:外币*/\n  COUNT(*) AS TRANSACTION_COUNT, /*交易次数*/\n  SUM(t.CNY_AMT) AS TRANSACTION_AMOUNT /*交易金额(折人民币)*/\nFROM BB11_TRANS_SMALL_01 t\nWHERE t.PARTY_CLASS_CD = 'I' /*客户类型为对私*/\n  AND t.OPP_PARTY_CLASS_CD = 'C' /*对方客户类型为对公*/\n  AND t.TSDR = '01' /*收交易*/\n  AND t.CASH_IND = '01' /*转账交易*/\nGROUP BY t.PARTY_ID, t.CURR_CD",
  "sql2": "SELECT \n  t.PARTY_ID, /*客户号*/\n  COUNT(CASE WHEN t.CURR_CD = '1' AND t.PARTY_CLASS_CD = 'I' AND t.OPP_PARTY_CLASS_CD = 'C' AND t.TSDR = '01' AND t.CASH_IND = '01' THEN 1 END) AS BB_RECEIVE_COUNT, /*本币收交易次数*/\n  SUM(CASE WHEN t.CURR_CD = '1' AND t.PARTY_CLASS_CD = 'I' AND t.OPP_PARTY_CLASS_CD = 'C' AND t.TSDR = '01' AND t.CASH_IND = '01' THEN t.CNY_AMT ELSE 0 END) AS BB_RECEIVE_AMOUNT, /*本币收交易金额*/\n  COUNT(CASE WHEN t.CURR_CD = '2' AND t.PARTY_CLASS_CD = 'I' AND t.OPP_PARTY_CLASS_CD = 'C' AND t.TSDR = '01' AND t.CASH_IND = '01' THEN 1 END) AS WB_RECEIVE_COUNT, /*外币收交易次数*/\n  SUM(CASE WHEN t.CURR_CD = '2' AND t.PARTY_CLASS_CD = 'I' AND t.OPP_PARTY_CLASS_CD = 'C' AND t.TSDR = '01' AND t.CASH_IND = '01' THEN t.CNY_AMT ELSE 0 END) AS WB_RECEIVE_AMOUNT /*外币收交易金额*/\nFROM BB11_TRANS_SMALL_01 t\nGROUP BY t.PARTY_ID"
}},
对私客户【本/外】币转账 收网银交易【次数/金额】汇总（交易对手客户类型为对公）:{{
  "desc": "根据用户问题，需要统计对私客户的本外币转账收网银交易的次数和金额，且交易对手客户类型为对公。从表结构中识别相关字段：PARTY_CLASS_CD(客户类型)、OPP_PARTY_CLASS_CD(对方客户类型)、CURR_CD(本外币标志)、TSDR(收付标志)、CASH_IND(现钞标志)、CHANNEL(交易渠道)、CNY_AMT(折人民币金额)。按PARTY_ID分组，统计不同条件下的交易情况。",
  "sql1": "SELECT \n  t.PARTY_ID, /*客户号*/\n  t.CURR_CD, /*本外币标志,1:本币,2:外币*/\n  COUNT(*) AS TRANSACTION_COUNT, /*交易次数*/\n  SUM(t.CNY_AMT) AS TRANSACTION_AMOUNT /*交易金额(折人民币)*/\nFROM BB11_TRANS_SMALL_01 t\nWHERE t.PARTY_CLASS_CD = 'I' /*客户类型为对私*/\n  AND t.OPP_PARTY_CLASS_CD = 'C' /*对方客户类型为对公*/\n  AND t.TSDR = '01' /*收交易*/\n  AND t.CASH_IND = '01' /*转账交易*/\n  AND t.CHANNEL = '2' /*网银交易*/\nGROUP BY t.PARTY_ID, t.CURR_CD",
  "sql2": "SELECT \n  t.PARTY_ID, /*客户号*/\n  COUNT(CASE WHEN t.CURR_CD = '1' AND t.PARTY_CLASS_CD = 'I' AND t.OPP_PARTY_CLASS_CD = 'C' AND t.TSDR = '01' AND t.CASH_IND = '01' AND t.CHANNEL = '2' THEN 1 END) AS BB_RECEIVE_COUNT, /*本币收交易次数*/\n  SUM(CASE WHEN t.CURR_CD = '1' AND t.PARTY_CLASS_CD = 'I' AND t.OPP_PARTY_CLASS_CD = 'C' AND t.TSDR = '01' AND t.CASH_IND = '01' AND t.CHANNEL = '2' THEN t.CNY_AMT ELSE 0 END) AS BB_RECEIVE_AMOUNT, /*本币收交易金额*/\n  COUNT(CASE WHEN t.CURR_CD = '2' AND t.PARTY_CLASS_CD = 'I' AND t.OPP_PARTY_CLASS_CD = 'C' AND t.TSDR = '01' AND t.CASH_IND = '01' AND t.CHANNEL = '2' THEN 1 END) AS WB_RECEIVE_COUNT, /*外币收交易次数*/\n  SUM(CASE WHEN t.CURR_CD = '2' AND t.PARTY_CLASS_CD = 'I' AND t.OPP_PARTY_CLASS_CD = 'C' AND t.TSDR = '01' AND t.CASH_IND = '01' AND t.CHANNEL = '2' THEN t.CNY_AMT ELSE 0 END) AS WB_RECEIVE_AMOUNT /*外币收交易金额*/\nFROM BB11_TRANS_SMALL_01 t\nGROUP BY t.PARTY_ID"
}},
对公客户最近一次【本/外】币转账收交易（交易对手客户类型为对公且非同名、资金来源或用途含有‘借款'）与最近一次付交易的时间间隔（单位：小时）:{ {
  "desc": "生成SQL的逻辑是：首先筛选出对公客户的交易记录，然后分别找出最近一次符合条件的本/外币转账收交易和最近一次付交易，计算两者之间的时间间隔。收交易的条件包括：交易对手客户类型为对公（OPP_PARTY_CLASS_CD='C'）、非同名交易（t.PARTY_NAME != t.TCNM）、资金来源或用途含有'借款'（t.CRSP like '%借款%'）、转账交易（t.CASH_IND='01'）、收交易（t.TSDR='01'）。付交易的条件包括：付交易（t.TSDR='02'）。最后按客户号分组，计算时间间隔。",
  "sql1": "SELECT \n  t.PARTY_ID, /*客户号*/\n  MAX(CASE WHEN t.TSDR='01' AND t.OPP_PARTY_CLASS_CD='C' AND t.PARTY_NAME != t.TCNM AND t.CRSP like '%借款%' AND t.CASH_IND='01' THEN TO_DATE(t.DT_TIME, 'YYYY-MM-DD HH24:MI:SS') END) AS LAST_RECEIVE_TIME, /*最近一次符合条件的收交易时间*/\n  MAX(CASE WHEN t.TSDR='02' THEN TO_DATE(t.DT_TIME, 'YYYY-MM-DD HH24:MI:SS') END) AS LAST_PAY_TIME, /*最近一次付交易时间*/\n  (MAX(CASE WHEN t.TSDR='01' AND t.OPP_PARTY_CLASS_CD='C' AND t.PARTY_NAME != t.TCNM AND t.CRSP like '%借款%' AND t.CASH_IND='01' THEN TO_DATE(t.DT_TIME, 'YYYY-MM-DD HH24:MI:SS') END) - MAX(CASE WHEN t.TSDR='02' THEN TO_DATE(t.DT_TIME, 'YYYY-MM-DD HH24:MI:SS') END)) * 24 AS TIME_INTERVAL_HOURS /*时间间隔（小时）*/\nFROM \n  BB11_TRANS_SMALL_01 t\nWHERE \n  t.PARTY_CLASS_CD='C' /*对公客户*/\nGROUP BY \n  t.PARTY_ID",
  "sql2": "SELECT \n  t.PARTY_ID, /*客户号*/\n  MAX(\n    CASE\n      WHEN t.TSDR='01' /*收交易*/\n      AND t.OPP_PARTY_CLASS_CD='C' /*交易对手客户类型为对公*/\n      AND t.PARTY_NAME != t.TCNM /*非同名交易*/\n      AND t.CRSP like '%借款%' /*资金来源或用途含有'借款'*/\n      AND t.CASH_IND='01' /*转账交易*/\n      THEN TO_DATE(t.DT_TIME, 'YYYY-MM-DD HH24:MI:SS')\n    END\n  ) AS LAST_RECEIVE_TIME, /*最近一次符合条件的收交易时间*/\n  MAX(\n    CASE\n      WHEN t.TSDR='02' /*付交易*/\n      THEN TO_DATE(t.DT_TIME, 'YYYY-MM-DD HH24:MI:SS')\n    END\n  ) AS LAST_PAY_TIME, /*最近一次付交易时间*/\n  (MAX(\n    CASE\n      WHEN t.TSDR='01' /*收交易*/\n      AND t.OPP_PARTY_CLASS_CD='C' /*交易对手客户类型为对公*/\n      AND t.PARTY_NAME != t.TCNM /*非同名交易*/\n      AND t.CRSP like '%借款%' /*资金来源或用途含有'借款'*/\n      AND t.CASH_IND='01' /*转账交易*/\n      THEN TO_DATE(t.DT_TIME, 'YYYY-MM-DD HH24:MI:SS')\n    END\n  ) - MAX(\n    CASE\n      WHEN t.TSDR='02' /*付交易*/\n      THEN TO_DATE(t.DT_TIME, 'YYYY-MM-DD HH24:MI:SS')\n    END\n  )) * 24 AS TIME_INTERVAL_HOURS /*时间间隔（小时）*/\nFROM \n  BB11_TRANS_SMALL_01 t\nWHERE \n  t.PARTY_CLASS_CD='C' /*对公客户*/\nGROUP BY \n  t.PARTY_ID"
}},
【本/外】币交易【对手账户个数/交易次数汇总】（交易对手客户类型对私、跨境、单笔交易金额≤a1）:{{
  "desc": "根据用户问题，需要统计本币和外币交易中对手账户个数和交易次数汇总，条件包括交易对手客户类型为对私、跨境交易、单笔交易金额≤a1。从表结构中确定相关字段：币种(CURR_CD)、交易对手客户类型(OPP_PARTY_CLASS_CD)、跨境标志(OVERAREA_IND)、交易金额(CNY_AMT/USD_AMT)。",
  "sql1": "SELECT \n  t.PARTY_ID, /*客户号*/\n  t.CURR_CD, /*币种，1:本币,2:外币*/\n  COUNT(DISTINCT t.TCAC) AS OPP_ACCT_COUNT, /*对手账户个数*/\n  COUNT(*) AS TRANS_COUNT /*交易次数*/\nFROM BB11_TRANS_SMALL_01 t\nWHERE t.OPP_PARTY_CLASS_CD = 'I' /*交易对手客户类型为对私*/\n  AND t.OVERAREA_IND = '1' /*跨境交易*/\n  AND t.CNY_AMT <= :a1 /*单笔交易金额≤a1*/\nGROUP BY t.PARTY_ID, t.CURR_CD",
  "sql2": "SELECT \n  t.PARTY_ID, /*客户号*/\n  COUNT(DISTINCT \n    CASE\n      WHEN t.CURR_CD = '1' /*本币*/\n        AND t.OPP_PARTY_CLASS_CD = 'I' /*交易对手客户类型为对私*/\n        AND t.OVERAREA_IND = '1' /*跨境交易*/\n        AND t.CNY_AMT <= :a1 /*单笔交易金额≤a1*/\n      THEN t.TCAC /*对手账号*/\n    END\n  ) AS BB_DS_KJ_ACCT_COUNT, /*本币对私跨境小额对手账户个数*/\n  COUNT(\n    CASE\n      WHEN t.CURR_CD = '1' /*本币*/\n        AND t.OPP_PARTY_CLASS_CD = 'I' /*交易对手客户类型为对私*/\n        AND t.OVERAREA_IND = '1' /*跨境交易*/\n        AND t.CNY_AMT <= :a1 /*单笔交易金额≤a1*/\n      THEN 1\n    END\n  ) AS BB_DS_KJ_COUNT, /*本币对私跨境小额交易次数*/\n  COUNT(DISTINCT \n    CASE\n      WHEN t.CURR_CD = '2' /*外币*/\n        AND t.OPP_PARTY_CLASS_CD = 'I' /*交易对手客户类型为对私*/\n        AND t.OVERAREA_IND = '1' /*跨境交易*/\n        AND t.CNY_AMT <= :a1 /*单笔交易金额≤a1*/\n      THEN t.TCAC /*对手账号*/\n    END\n  ) AS WB_DS_KJ_ACCT_COUNT, /*外币对私跨境小额对手账户个数*/\n  COUNT(\n    CASE\n      WHEN t.CURR_CD = '2' /*外币*/\n        AND t.OPP_PARTY_CLASS_CD = 'I' /*交易对手客户类型为对私*/\n        AND t.OVERAREA_IND = '1' /*跨境交易*/\n        AND t.CNY_AMT <= :a1 /*单笔交易金额≤a1*/\n      THEN 1\n    END\n  ) AS WB_DS_KJ_COUNT /*外币对私跨境小额交易次数*/\nFROM BB11_TRANS_SMALL_01 t\nGROUP BY t.PARTY_ID"
}},
【本/外】币现金交易次数汇总（单笔交易金额≥本币50000/外币10000）:{{
  "desc": "根据用户问题，需要统计本币和外币的现金交易次数，其中本币交易金额≥50000，外币交易金额≥10000。从表结构中确定相关字段：币种(CURR_CD)、现金标志(CASH_IND)、交易金额(CNY_AMT/USD_AMT)。",
  "sql1": "SELECT \n  t.PARTY_ID, /*客户号*/\n  t.CURR_CD, /*币种，1:本币,2:外币*/\n  COUNT(*) AS CASH_TRANS_COUNT /*现金交易次数*/\nFROM BB11_TRANS_SMALL_01 t\nWHERE t.CASH_IND = '00' /*现金交易*/\n  AND (\n    (t.CURR_CD = '1' AND t.CNY_AMT >= 50000) /*本币且金额≥50000*/\n    OR \n    (t.CURR_CD = '2' AND t.USD_AMT >= 10000) /*外币且金额≥10000*/\n  )\nGROUP BY t.PARTY_ID, t.CURR_CD",
  "sql2": "SELECT \n  t.PARTY_ID, /*客户号*/\n  COUNT(\n    CASE\n      WHEN t.CASH_IND = '00' /*现金交易*/\n        AND t.CURR_CD = '1' /*本币*/\n        AND t.CNY_AMT >= 50000 /*金额≥50000*/\n      THEN 1\n    END\n  ) AS BB_XJ_LARGE_COUNT, /*本币大额现金交易次数*/\n  COUNT(\n    CASE\n      WHEN t.CASH_IND = '00' /*现金交易*/\n        AND t.CURR_CD = '2' /*外币*/\n        AND t.USD_AMT >= 10000 /*金额≥10000*/\n      THEN 1\n    END\n  ) AS WB_XJ_LARGE_COUNT /*外币大额现金交易次数*/\nFROM BB11_TRANS_SMALL_01 t\nGROUP BY t.PARTY_ID"
}},
本币现金付交易次数汇总（单笔交易金额（交易渠道为ATM或其他自助设备、付、现金、非跨境）≥2700）:{{
  "desc": "生成SQL逻辑：统计本币现金付交易次数，条件包括交易渠道为ATM或其他自助设备、付交易、现金交易、非跨境交易，且单笔交易金额≥2700。按客户号PARTY_ID分组。",
  "sql1": "SELECT \n  t.PARTY_ID, /*客户号*/\n  COUNT(*) AS TRANSACTION_COUNT /*交易次数*/\nFROM BB11_TRANS_SMALL_01 t\nWHERE \n  t.CURR_CD = '1' /*本币*/\n  AND t.CASH_IND = '00' /*现金交易*/\n  AND t.TSDR = '02' /*付交易*/\n  AND t.OVERAREA_IND = '0' /*非跨境交易*/\n  AND t.CHANNEL IN ('4', '02') /*交易渠道为ATM或其他自助设备*/\n  AND t.CNY_AMT >= 2700 /*单笔交易金额≥2700*/\nGROUP BY t.PARTY_ID",
  "sql2": "SELECT \n  t.PARTY_ID, /*客户号*/\n  COUNT(\n    CASE\n      WHEN t.CURR_CD = '1' /*本币*/\n      AND t.CASH_IND = '00' /*现金交易*/\n      AND t.TSDR = '02' /*付交易*/\n      AND t.OVERAREA_IND = '0' /*非跨境交易*/\n      AND t.CHANNEL IN ('4', '02') /*交易渠道为ATM或其他自助设备*/\n      AND t.CNY_AMT >= 2700 /*单笔交易金额≥2700*/\n      THEN 1\n    END\n  ) AS BB_XJ_F_CT /*本币现金付交易次数*/\nFROM BB11_TRANS_SMALL_01 t\nGROUP BY t.PARTY_ID"
}},
本币 付交易 对手账户个数(非同名，单笔交易金额≤A2):{{
  "desc": "生成SQL的逻辑是根据用户需求统计本币付交易中对手账户的个数，要求是非同名交易且单笔交易金额不超过a1。需要筛选本币交易(CURR_CD='1')、付交易(TSDR='02')、非同名交易(PARTY_NAME != TCNM)且金额不超过a1的记录，并按客户号分组统计对手账户个数。",
  "sql1": "SELECT \n  t.PARTY_ID, /** 客户号 */\n  COUNT(DISTINCT t.TCAC) AS OPP_ACCOUNT_COUNT /** 对手账户个数 */\nFROM BB11_TRANS_SMALL_01 t\nWHERE t.CURR_CD = '1' /** 本币交易 */\n  AND t.TSDR = '02' /** 付交易 */\n  AND t.PARTY_NAME != t.TCNM /** 非同名交易 */\n  AND t.CNY_AMT <= :a1 /** 单笔交易金额≤a1 */\nGROUP BY t.PARTY_ID",
  "sql2": "SELECT \n  t.PARTY_ID, /** 客户号 */\n  COUNT(DISTINCT \n    CASE\n      WHEN t.CURR_CD = '1' /** 本币交易 */\n        AND t.TSDR = '02' /** 付交易 */\n        AND t.PARTY_NAME != t.TCNM /** 非同名交易 */\n        AND t.CNY_AMT <= :a1 /** 单笔交易金额≤a1 */\n      THEN t.TCAC /** 对手账户 */\n    END\n  ) AS OPP_ACCOUNT_COUNT /** 本币付交易对手账户个数(非同名，单笔交易金额≤a1) */\nFROM BB11_TRANS_SMALL_01 t\nGROUP BY t.PARTY_ID"
}},
本币现金交易金额汇总（交易渠道：柜面，交易金额汇总为万元整数倍）:{{
  "desc": "生成SQL的逻辑是根据用户需求统计本币现金交易金额汇总，要求交易渠道为柜面，并且如果交易金额汇总不是万元整数倍则显示为0。根据表结构信息，我们需要使用CURR_CD='1'表示本币，CASH_IND='00'表示现金交易，CHANNEL='1'表示柜面交易渠道。使用SUM函数汇总CNY_AMT(折人民币金额)，并通过MOD函数判断是否为万元整数倍。",
  "sql1": "SELECT \n  t.PARTY_ID, /*客户号*/\n  CASE \n    WHEN MOD(SUM(t.CNY_AMT), 10000) = 0 THEN SUM(t.CNY_AMT) /*交易金额为万元整数倍时显示实际金额*/\n    ELSE 0 /*交易金额不为万元整数倍时显示0*/\n  END AS TOTAL_AMOUNT\nFROM \n  BB11_TRANS_SMALL_01 t\nWHERE \n  t.CURR_CD = '1' /*本币*/\n  AND t.CASH_IND = '00' /*现金交易*/\n  AND t.CHANNEL = '1' /*柜面交易渠道*/\nGROUP BY \n  t.PARTY_ID",
  "sql2": "SELECT \n  t.PARTY_ID, /*客户号*/\n  CASE \n    WHEN MOD(SUM(\n      CASE\n        WHEN t.CURR_CD = '1' /*本币*/\n        AND t.CASH_IND = '00' /*现金交易*/\n        AND t.CHANNEL = '1' /*柜面交易渠道*/\n        THEN t.CNY_AMT /*折人民币金额*/\n      END\n    ), 10000) = 0 THEN SUM(\n      CASE\n        WHEN t.CURR_CD = '1' /*本币*/\n        AND t.CASH_IND = '00' /*现金交易*/\n        AND t.CHANNEL = '1' /*柜面交易渠道*/\n        THEN t.CNY_AMT /*折人民币金额*/\n      END\n    )\n    ELSE 0 /*交易金额不为万元整数倍时显示0*/\n  END AS TOTAL_AMOUNT\nFROM \n  BB11_TRANS_SMALL_01 t\nGROUP BY \n  t.PARTY_ID"
}},
【本/外】币交易【对手账户个数/交易次数汇总】（交易对手客户类型对私、跨境、单笔交易金额≤a1）:{{
  "desc": "根据用户问题，需要统计本/外币交易中对手账户个数和交易次数汇总，条件包括交易对手客户类型对私、跨境、单笔交易金额≤a1。从表结构中识别相关字段：币种(CURR_CD)、对手账户(TCAC)、交易对手客户类型(OPP_PARTY_CLASS_CD)、跨境标志(OVERAREA_IND)、交易金额(CNY_AMT)。",
  "sql1": "SELECT \n  t.PARTY_ID, /*客户号*/\n  t.CURR_CD, /*币种，1:本币,2:外币*/\n  COUNT(DISTINCT t.TCAC) AS OPP_ACCT_COUNT, /*对手账户个数*/\n  COUNT(*) AS TRANS_COUNT /*交易次数*/\nFROM BB11_TRANS_SMALL_01 t\nWHERE t.OPP_PARTY_CLASS_CD = 'I' /*交易对手客户类型对私*/\n  AND t.OVERAREA_IND = '1' /*跨境交易*/\n  AND t.CNY_AMT <= a1 /*单笔交易金额≤a1*/\nGROUP BY t.PARTY_ID, t.CURR_CD",
  "sql2": "SELECT \n  t.PARTY_ID, /*客户号*/\n  COUNT(DISTINCT \n    CASE\n      WHEN t.CURR_CD = '1' /*本币*/\n        AND t.OPP_PARTY_CLASS_CD = 'I' /*交易对手客户类型对私*/\n        AND t.OVERAREA_IND = '1' /*跨境交易*/\n        AND t.CNY_AMT <= a1 /*单笔交易金额≤a1*/\n      THEN t.TCAC /*对手账户*/\n    END\n  ) AS BB_OPP_ACCT_COUNT, /*本币对手账户个数*/\n  COUNT(\n    CASE\n      WHEN t.CURR_CD = '1' /*本币*/\n        AND t.OPP_PARTY_CLASS_CD = 'I' /*交易对手客户类型对私*/\n        AND t.OVERAREA_IND = '1' /*跨境交易*/\n        AND t.CNY_AMT <= a1 /*单笔交易金额≤a1*/\n      THEN 1\n    END\n  ) AS BB_TRANS_COUNT, /*本币交易次数*/\n  COUNT(DISTINCT \n    CASE\n      WHEN t.CURR_CD = '2' /*外币*/\n        AND t.OPP_PARTY_CLASS_CD = 'I' /*交易对手客户类型对私*/\n        AND t.OVERAREA_IND = '1' /*跨境交易*/\n        AND t.CNY_AMT <= a1 /*单笔交易金额≤a1*/\n      THEN t.TCAC /*对手账户*/\n    END\n  ) AS WB_OPP_ACCT_COUNT, /*外币对手账户个数*/\n  COUNT(\n    CASE\n      WHEN t.CURR_CD = '2' /*外币*/\n        AND t.OPP_PARTY_CLASS_CD = 'I' /*交易对手客户类型对私*/\n        AND t.OVERAREA_IND = '1' /*跨境交易*/\n        AND t.CNY_AMT <= a1 /*单笔交易金额≤a1*/\n      THEN 1\n    END\n  ) AS WB_TRANS_COUNT /*外币交易次数*/\nFROM BB11_TRANS_SMALL_01 t\nGROUP BY t.PARTY_ID"
}},
同时发生本币和外币的转账【收/付】交易金额汇总，本币与外币的金额汇总皆不为0:{{
  "desc": "根据用户问题，需要统计同时发生本币和外币的转账收付交易，并按客户号分组，要求本币与外币的金额汇总皆不为0。首先识别出本外币标志(CURR_CD)、转账交易(CASH_IND='01')、收付标志(TSDR)等关键字段，然后按PARTY_ID分组计算汇总金额，并筛选出本币和外币金额都不为0的记录。",
  "sql1": "SELECT \n  t.PARTY_ID, /*客户号*/\n  SUM(CASE WHEN t.CURR_CD = '1' THEN t.CNY_AMT ELSE 0 END) AS BB_AMT, /*本币折人民币金额汇总*/\n  SUM(CASE WHEN t.CURR_CD = '2' THEN t.USD_AMT ELSE 0 END) AS WB_AMT /*外币折美元金额汇总*/\nFROM BB11_TRANS_SMALL_01 t\nWHERE t.CASH_IND = '01' /*转账交易*/\nGROUP BY t.PARTY_ID\nHAVING SUM(CASE WHEN t.CURR_CD = '1' THEN t.CNY_AMT ELSE 0 END) != 0\n   AND SUM(CASE WHEN t.CURR_CD = '2' THEN t.USD_AMT ELSE 0 END) != 0",
  "sql2": "SELECT \n  t.PARTY_ID, /*客户号*/\n  SUM(\n    CASE\n      WHEN t.CURR_CD = '1' AND t.TSDR = '01' /*本币收交易*/\n      THEN t.CNY_AMT\n      ELSE 0\n    END\n  ) AS BB_RECEIVE_CNY, /*本币收交易折人民币金额汇总*/\n  SUM(\n    CASE\n      WHEN t.CURR_CD = '1' AND t.TSDR = '02' /*本币付交易*/\n      THEN t.CNY_AMT\n      ELSE 0\n    END\n  ) AS BB_PAY_CNY, /*本币付交易折人民币金额汇总*/\n  SUM(\n    CASE\n      WHEN t.CURR_CD = '2' AND t.TSDR = '01' /*外币收交易*/\n      THEN t.USD_AMT\n      ELSE 0\n    END\n  ) AS WB_RECEIVE_USD, /*外币收交易折美元金额汇总*/\n  SUM(\n    CASE\n      WHEN t.CURR_CD = '2' AND t.TSDR = '02' /*外币付交易*/\n      THEN t.USD_AMT\n      ELSE 0\n    END\n  ) AS WB_PAY_USD /*外币付交易折美元金额汇总*/\nFROM BB11_TRANS_SMALL_01 t\nWHERE t.CASH_IND = '01' /*转账交易*/\nGROUP BY t.PARTY_ID\nHAVING SUM(CASE WHEN t.CURR_CD = '1' THEN t.CNY_AMT ELSE 0 END) != 0\n   AND SUM(CASE WHEN t.CURR_CD = '2' THEN t.USD_AMT ELSE 0 END) != 0"
}},
同时发生本币和外币的境内【收/付】交易金额汇总:{{
  "desc": "根据用户需求，需要统计同时发生本币和外币的境内收付交易金额汇总，且金额汇总都不为0的客户。首先筛选境内交易(OVERAREA_IND='0')，然后按客户分组统计本币和外币的收付交易金额，最后筛选出本外币金额都不为0的客户。",
  "sql1": "SELECT \n  t.PARTY_ID, /*客户号*/\n  SUM(CASE WHEN t.CURR_CD='1' AND t.TSDR='01' THEN t.CNY_AMT ELSE 0 END) AS BB_RECEIVE_AMT, /*本币收交易金额*/\n  SUM(CASE WHEN t.CURR_CD='1' AND t.TSDR='02' THEN t.CNY_AMT ELSE 0 END) AS BB_PAY_AMT, /*本币付交易金额*/\n  SUM(CASE WHEN t.CURR_CD='2' AND t.TSDR='01' THEN t.CNY_AMT ELSE 0 END) AS WB_RECEIVE_AMT, /*外币收交易金额*/\n  SUM(CASE WHEN t.CURR_CD='2' AND t.TSDR='02' THEN t.CNY_AMT ELSE 0 END) AS WB_PAY_AMT /*外币付交易金额*/\nFROM \n  BB11_TRANS_SMALL_01 t\nWHERE \n  t.OVERAREA_IND='0' /*境内交易*/\nGROUP BY \n  t.PARTY_ID\nHAVING \n  SUM(CASE WHEN t.CURR_CD='1' AND t.TSDR='01' THEN t.CNY_AMT ELSE 0 END) != 0\n  AND SUM(CASE WHEN t.CURR_CD='1' AND t.TSDR='02' THEN t.CNY_AMT ELSE 0 END) != 0\n  AND SUM(CASE WHEN t.CURR_CD='2' AND t.TSDR='01' THEN t.CNY_AMT ELSE 0 END) != 0\n  AND SUM(CASE WHEN t.CURR_CD='2' AND t.TSDR='02' THEN t.CNY_AMT ELSE 0 END) != 0",
  "sql2": "SELECT \n  t.PARTY_ID, /*客户号*/\n  SUM(\n    CASE\n      WHEN t.CURR_CD='1' /*本币*/\n      AND t.TSDR='01' /*收交易*/\n      AND t.OVERAREA_IND='0' /*境内交易*/\n      THEN t.CNY_AMT /*折人民币金额*/\n      ELSE 0\n    END\n  ) AS BB_RECEIVE_AMT, /*本币收交易金额*/\n  SUM(\n    CASE\n      WHEN t.CURR_CD='1' /*本币*/\n      AND t.TSDR='02' /*付交易*/\n      AND t.OVERAREA_IND='0' /*境内交易*/\n      THEN t.CNY_AMT /*折人民币金额*/\n      ELSE 0\n    END\n  ) AS BB_PAY_AMT, /*本币付交易金额*/\n  SUM(\n    CASE\n      WHEN t.CURR_CD='2' /*外币*/\n      AND t.TSDR='01' /*收交易*/\n      AND t.OVERAREA_IND='0' /*境内交易*/\n      THEN t.CNY_AMT /*折人民币金额*/\n      ELSE 0\n    END\n  ) AS WB_RECEIVE_AMT, /*外币收交易金额*/\n  SUM(\n    CASE\n      WHEN t.CURR_CD='2' /*外币*/\n      AND t.TSDR='02' /*付交易*/\n      AND t.OVERAREA_IND='0' /*境内交易*/\n      THEN t.CNY_AMT /*折人民币金额*/\n      ELSE 0\n    END\n  ) AS WB_PAY_AMT /*外币付交易金额*/\nFROM \n  BB11_TRANS_SMALL_01 t\nGROUP BY \n  t.PARTY_ID\nHAVING \n  SUM(\n    CASE\n      WHEN t.CURR_CD='1' /*本币*/\n      AND t.TSDR='01' /*收交易*/\n      AND t.OVERAREA_IND='0' /*境内交易*/\n      THEN t.CNY_AMT /*折人民币金额*/\n      ELSE 0\n    END\n  ) != 0\n  AND SUM(\n    CASE\n      WHEN t.CURR_CD='1' /*本币*/\n      AND t.TSDR='02' /*付交易*/\n      AND t.OVERAREA_IND='0' /*境内交易*/\n      THEN t.CNY_AMT /*折人民币金额*/\n      ELSE 0\n    END\n  ) != 0\n  AND SUM(\n    CASE\n      WHEN t.CURR_CD='2' /*外币*/\n      AND t.TSDR='01' /*收交易*/\n      AND t.OVERAREA_IND='0' /*境内交易*/\n      THEN t.CNY_AMT /*折人民币金额*/\n      ELSE 0\n    END\n  ) != 0\n  AND SUM(\n    CASE\n      WHEN t.CURR_CD='2' /*外币*/\n      AND t.TSDR='02' /*付交易*/\n      AND t.OVERAREA_IND='0' /*境内交易*/\n      THEN t.CNY_AMT /*折人民币金额*/\n      ELSE 0\n    END\n  ) != 0"
}},
（非居民）【本/外】币现金收交易次数汇总:{{
  "desc": "统计非居民客户的本外币现金收交易次数汇总，按客户号PARTY_ID分组。非居民客户通过客户表的AML2_TYPE_CD='02'标识，现金交易通过交易流水表的CASH_IND='00'标识，收交易通过TSDR='01'标识。",
  "sql1": "SELECT \n  t.PARTY_ID, /**/客户号\n  t.CURR_CD, /**/本外币标志，1:本币,2:外币\n  COUNT(*) AS TRANSACTION_COUNT /**/交易次数\nFROM BB11_TRANS_SMALL_01 t\nJOIN BB11_PARTY p ON t.PARTY_ID = p.PARTY_ID\nWHERE p.AML2_TYPE_CD = '02' /**/非居民客户*/\n  AND t.CASH_IND = '00' /**/现金交易*/\n  AND t.TSDR = '01' /**/收交易*/\nGROUP BY t.PARTY_ID, t.CURR_CD",
  "sql2": "SELECT \n   t.PARTY_ID, \n   COUNT(\n     CASE\n       WHEN t.CURR_CD='1' AND t.CASH_IND = '00' AND t.TSDR = '01' AND p.AML2_TYPE_CD = '02' \n       THEN 1\n     END\n   ) AS BB_XJS_CT, \n   COUNT(\n     CASE\n       WHEN t.CURR_CD='2' AND t.CASH_IND = '00' AND t.TSDR = '01' AND p.AML2_TYPE_CD = '02' \n       THEN 1\n     END\n   ) AS WB_XJS_CT \n FROM BB11_TRANS_SMALL_01 t\n JOIN BB11_PARTY p ON t.PARTY_ID = p.PARTY_ID\n GROUP BY t.PARTY_ID "
}},
外币转账收交易【次数/金额】汇总（居民、跨境、转账）:{{
  "desc": "统计居民客户的外币跨境转账收交易的次数和金额汇总，按客户号PARTY_ID分组。居民客户通过客户表的AML2_TYPE_CD='01'标识，外币交易通过交易流水表的CURR_CD='2'标识，跨境交易通过OVERAREA_IND='1'标识，转账交易通过CASH_IND='01'标识，收交易通过TSDR='01'标识。",
  "sql1": "SELECT \n  t.PARTY_ID, /**/客户号\n  COUNT(*) AS TRANSACTION_COUNT, /**/交易次数\n  SUM(t.CRAT) AS TRANSACTION_AMOUNT /**/原币交易金额\nFROM BB11_TRANS_SMALL_01 t\nJOIN BB11_PARTY p ON t.PARTY_ID = p.PARTY_ID\nWHERE p.AML2_TYPE_CD = '01' /**/居民客户*/\n  AND t.CURR_CD = '2' /**/外币交易*/\n  AND t.OVERAREA_IND = '1' /**/跨境交易*/\n  AND t.CASH_IND = '01' /**/转账交易*/\n  AND t.TSDR = '01' /**/收交易*/\nGROUP BY t.PARTY_ID",
  "sql2": "SELECT \n  t.PARTY_ID, \n  COUNT(\n CASE\n WHEN t.CURR_CD = '2' \n AND t.OVERAREA_IND = '1' \n       AND t.CASH_IND = '01' \n       AND t.TSDR = '01' AND p.AML2_TYPE_CD = '01' \n       THEN 1\n     END\n   ) AS WB_KJ_ZZS_CT,\n   SUM(\n     CASE\n       WHEN t.CURR_CD = '2' \n       AND t.OVERAREA_IND = '1' \n       AND t.CASH_IND = '01'\n       AND t.TSDR = '01' AND p.AML2_TYPE_CD = '01' \n       THEN t.CRAT \n       ELSE 0\n     END\n   ) AS WB_KJ_ZZS_AMT \n FROM BB11_TRANS_SMALL_01 t\n JOIN BB11_PARTY p ON t.PARTY_ID = p.PARTY_ID\n GROUP BY t.PARTY_ID"
}},
转账本币收交易次数汇总(交易渠道=网银/手机银行,单笔交易金额不为零,单笔金额≤10元):{{
  "desc": "生成SQL的逻辑：根据用户需求统计本币收交易次数，条件包括交易渠道为网银/手机银行、单笔交易金额不为零且≤10元。从交易流水表中筛选符合条件的数据，按客户号分组统计。",
  "sql1": "SELECT \n  t.PARTY_ID, /**/ 客户号\n  COUNT(*) AS TRANSACTION_COUNT /**/ 交易次数\nFROM \n  BB11_TRANS_SMALL_01 t\nWHERE \n  t.CURR_CD = '1' /**/ 本币标志\n  AND t.TSDR = '01' /**/ 收交易\n  AND t.CHANNEL IN ('2', '6') /**/ 交易渠道为网银(2)或手机银行(3)\n  AND t.CNY_AMT > 0 /**/ 交易金额不为零\n  AND t.CNY_AMT <= 10 /**/ 单笔金额≤10元\n  AND t.CASH_IND = '01' /**/ 转账交易\nGROUP BY \n  t.PARTY_ID",
  "sql2": "SELECT \n  t.PARTY_ID, /**/ 客户号\n  COUNT(\n    CASE\n      WHEN t.CURR_CD = '1' /**/ 本币标志\n      AND t.TSDR = '01' /**/ 收交易\n      AND t.CHANNEL IN ('2', '6') /**/ 交易渠道为网银(2)或手机银行(3)\n      AND t.CNY_AMT > 0 /**/ 交易金额不为零\n      AND t.CNY_AMT <= 10 /**/ 单笔金额≤10元\n      AND t.CASH_IND = '01' /**/ 转账交易\n      THEN 1\n    END\n  ) AS TRANSACTION_COUNT /**/ 转账本币收交易次数\nFROM \n  BB11_TRANS_SMALL_01 t\nGROUP BY \n  t.PARTY_ID"
}},
境内交易发生地个数汇总（交易方向国别为CHN、Z01、Z02、Z03）:{{
  "desc": "根据用户需求，统计境内交易发生地个数汇总，条件是交易方向国别为CHN、Z01、Z02、Z03。需要按客户号PARTY_ID分组，统计每个客户的境内交易发生地个数。",
  "sql1": "SELECT \n  t.PARTY_ID, /** 客户号 **/\n  COUNT(DISTINCT t.TRCD_COUNTRY) AS DOMESTIC_TRANSACTION_COUNT /** 境内交易发生地个数 **/\nFROM \n  BB11_TRANS_SMALL_01 t\nWHERE \n  t.TRCD_COUNTRY IN ('CHN','Z01','Z02','Z03') AND t.OVERAREA_IND='0' /** 交易方向国别为CHN、Z01、Z02、Z03 **/\nGROUP BY \n  t.PARTY_ID",
  "sql2": "SELECT \n  t.PARTY_ID, /** 客户号 **/\n  COUNT(DISTINCT \n    CASE \n      WHEN t.OVERAREA_IND='0' AND t.TRCD_COUNTRY IN ('CHN','Z01','Z02','Z03') /** 交易方向国别为CHN、Z01、Z02、Z03 **/\n      THEN t.TRCD_AREA  \n    END\n  ) AS DOMESTIC_TRANSACTION_COUNT /** 境内交易发生地个数 **/\nFROM \n  BB11_TRANS_SMALL_01 t\nGROUP BY \n  t.PARTY_ID"
}},
最近一次【本/外】币收付交易时间间隔（单位：小时）:{{
  "desc": "统计每个客户最近一次本币和外币收交易与付交易的时间间隔（单位：小时）。使用TO_DATE函数转换DT_TIME字段为日期格式进行计算。",
  "sql1": "SELECT \n  t.PARTY_ID, /*客户号*/\n  NVL((MAX(CASE WHEN t.CURR_CD = '1' AND t.TSDR = '01' THEN TO_DATE(t.DT_TIME, 'YYYY-MM-DD HH24:MI:SS') END) - \n      MAX(CASE WHEN t.CURR_CD = '1' AND t.TSDR = '02' THEN TO_DATE(t.DT_TIME, 'YYYY-MM-DD HH24:MI:SS') END)) * 24 AS BB_INTERVAL_HOURS, /*本币收付时间间隔(小时)*/\n  NVL((MAX(CASE WHEN t.CURR_CD = '2' AND t.TSDR = '01' THEN TO_DATE(t.DT_TIME, 'YYYY-MM-DD HH24:MI:SS') END) - \n      MAX(CASE WHEN t.CURR_CD = '2' AND t.TSDR = '02' THEN TO_DATE(t.DT_TIME, 'YYYY-MM-DD HH24:MI:SS') END)) * 24 AS WB_INTERVAL_HOURS /*外币收付时间间隔(小时)*/\nFROM \n  BB11_TRANS_SMALL_01 t\nGROUP BY \n  t.PARTY_ID",
  "sql2": "SELECT \n  t.PARTY_ID, /*客户号*/\n  NVL((MAX(\n    CASE\n      WHEN t.CURR_CD = '1' /*本币*/\n      AND t.TSDR = '01' /*收交易*/\n      THEN TO_DATE(t.DT_TIME, 'YYYY-MM-DD HH24:MI:SS')\n    END\n  ) - MAX(\n    CASE\n      WHEN t.CURR_CD = '1' /*本币*/\n      AND t.TSDR = '02' /*付交易*/\n      THEN TO_DATE(t.DT_TIME, 'YYYY-MM-DD HH24:MI:SS')\n    END\n  )) * 24, 0) AS BB_INTERVAL_HOURS, /*本币收付时间间隔(小时)*/\n  NVL((MAX(\n    CASE\n      WHEN t.CURR_CD = '2' /*外币*/\n      AND t.TSDR = '01' /*收交易*/\n      THEN TO_DATE(t.DT_TIME, 'YYYY-MM-DD HH24:MI:SS')\n    END\n  ) - MAX(\n    CASE\n      WHEN t.CURR_CD = '2' /*外币*/\n      AND t.TSDR = '02' /*付交易*/\n      THEN TO_DATE(t.DT_TIME, 'YYYY-MM-DD HH24:MI:SS')\n    END\n  )) * 24, 0) AS WB_INTERVAL_HOURS /*外币收付时间间隔(小时)*/\nFROM \n  BB11_TRANS_SMALL_01 t\nGROUP BY \n  t.PARTY_ID"
}},
商户转账收交易金额汇总（交易渠道：POS或类似业务）:{{
  "desc": "根据用户需求，统计交易流水表中按客户号分组的本币和外币商户转账收交易金额汇总，限定交易渠道为POS或类似业务。使用CURR_CD区分本外币(1:本币,2:外币)，TSDR='01'表示收交易，IS_MERCH='1'表示我行商户，CHANNEL='3'表示POS渠道。",
  "sql1": "SELECT \n  t.PARTY_ID, /*客户号*/\n  t.CURR_CD, /*币种,1:本币,2:外币*/\n  SUM(t.CNY_AMT) AS TOTAL_AMOUNT /*折人民币金额汇总*/\nFROM \n  BB11_TRANS_SMALL_01 t\nWHERE \n  t.TSDR = '01' /*收交易*/\n  AND t.IS_MERCH = '1' /*我行商户*/\n  AND t.CHANNEL = '5' /*交易渠道:POS*/\nGROUP BY \n  t.PARTY_ID, t.CURR_CD",
  "sql2": "SELECT \n  t.PARTY_ID, /*客户号*/\n  SUM(\n    CASE\n      WHEN t.CURR_CD = '1' /*本币*/\n      AND t.TSDR = '01' /*收交易*/\n      AND t.IS_MERCH = '1' /*我行商户*/\n      AND t.CHANNEL = '5' /*交易渠道:POS*/\n      THEN t.CNY_AMT\n      ELSE 0\n    END\n  ) AS BB_MERCH_RECEIVE_AMT, /*本币商户转账收交易金额汇总*/\n  SUM(\n    CASE\n      WHEN t.CURR_CD = '2' /*外币*/\n      AND t.TSDR = '01' /*收交易*/\n      AND t.IS_MERCH = '1' /*我行商户*/\n      AND t.CHANNEL = '3' /*交易渠道:POS*/\n      THEN t.CNY_AMT\n      ELSE 0\n    END\n  ) AS WB_MERCH_RECEIVE_AMT /*外币商户转账收交易金额汇总*/\nFROM \n  BB11_TRANS_SMALL_01 t\nGROUP BY \n  t.PARTY_ID"
}},


"""
        return _examples


    def alg_table_name(self, query):
        """SQL生成-生成字典：算法名称，表名等
        """
        # 输出格式增加了各种定义、约束
        output_format = f"""
        以JSON格式输出。包含的字段有四个：
        1. alg_name字段:算法名称,简略概括用户问题，并以算法为后缀
        2. feature_table_name字段，该算法的表名，以BA11_TRANS_为前缀，取算法名称三到六个关键汉字的首写字母的大写作为一组,一组直接一个关键字，以_拼接，作为后缀
        3. feature_table_name_comment字段，为表添加中文注释，以"特征表"为后缀
        4. alg_desc字段，为用户的问题
        输出中只包含用户提及的字段，不要猜测任何用户未直接提及的字段，不输出值为null的字段。
        """

        #举例说明
        examples = """
    【本/外】币【收方/付方/双方】交易【笔数/金额】汇总（交易渠道：第三方支付）:{{
    "alg_name":"交易第三方支付算法"
    }},
    外币交易次数汇总:{{
    "alg_name":"交易次数汇总算法"
    }}，
    【本/外】币交易次数汇总（ip归属地国别≠CHN）:{{
    "alg_name": "交易IP非CHN算法",
    "feature_table_name": "BA11_TRANS_JYIP_FCHN",
    "feature_table_name_comment": "交易IP非CHN特征表"
    }},
    【本/外】币交易的IP地址个数：{{
    "alg_name":"交易IP地址算法"
    }},
    交易发生地国家个数：{{
    "alg_name":"交易发生国家算法"
    }},
    【收/付/双方】交易对手账户个数(非同名)：{{
    "alg_name":"交易对手非同名账户算法",
    "feature_table_name": "BA11_TRANS_JYDS_FTM",
    "feature_table_name_comment": "交易对手非同名账户特征表"
    }},
    外币跨境交易次数汇总（交易币种为MYR/THB/TRY/VND/SYP/AZN/PKR/AFN/KZT/KGS/UZS/TJS/SR/MMK/JPY/EUR）:{{
    "alg_name": "外币多币种跨境交易次数汇总算法",
    "feature_table_name": "BA11_TRANS_DBKJ_WB",
    "feature_table_name_comment": "外币多币种跨境交易次数特征表"
    }},
    一个月，对私客户现金付交易金额汇总（交易渠道=ATM，交交易发生地<>CHN.Z01.Z02.Z03，取折美金额）:{{
    "alg_name": "对私客户跨境ATM现金付交易金额汇总算法",
    "feature_table_name": "BA11_TRANS_DKXJ_ATM",
    "feature_table_name_comment": "对私客户跨境ATM现金付交易金额特征表"
    }},
    现金付交易金额汇总（交易渠道=ATM，交交易发生地<>CHN.Z01.Z02.Z03，取折美金额）:{{
    "alg_name": "ATM现金付交易金额汇总算法",
    "feature_table_name": "BA11_TRANS_XJJE_ATM",
    "feature_table_name_comment": "ATM现金付交易金额特征表"
    }},
    【本/外】币交易次数汇总（单笔交易金额为整数）:{{
    "alg_name": "整数金额交易次数汇总算法",
    "feature_table_name": "BA11_TRANS_ZSJE",
    "feature_table_name_comment": "整数金额交易次数特征表",
    "alg_desc": "【本/外】币交易次数汇总（单笔交易金额为整数）"
    }}

    """
        
        prompt = f"""
        根据用户问题生成摘要，以“算法”结尾
        
        举例说明
        {examples}
        
        输出格式
        {output_format}
        
        用户问题
        {query}
        
        """
        return prompt
        
    def prompt_bsn_fenlei(self, query):
        
        #【本/外】币，缩写BB
        BB_condition_str = {"BB":"本币","WB":"外币"}
        BB_condition = {"BB":"CURR_CD='1'","WB":"CURR_CD='2'"}

        # BB_condition_str = {"BB":"本币","WB":"外币","BW":"本外币不分"}
        # BB_condition = {"BB":"CURR_CD='1'","WB":"CURR_CD='2'","BW":"CURR_CD in ('1','2')"}
        # BB_condition_str = {"BW":"本外币不分"}
        # BB_condition = {"BW":"CURR_CD in ('1','2')"}
        # BB_list = [BB_condition,BB_condition_str]


        #境内境外，
        NW_condition_str = {"NI":"境内","WA":"境外","ALL":"不分"}
        NW_condition = {"NI":"t.OVERAREA_IND='0'","WA":"t.OVERAREA_IND='1'"}
        # NW_list=[NW_condition,NW_condition_str]

        #交易媒介,转账/现金，缩写MJ
        MJ_condition_str = {"XJ":"现金","ZZ":"转账","ALL":"不分"}
        MJ_condition = {"XJ":"CASH_IND='00'","ZZ":"CASH_IND='01'","ALL":"CASH_IND in('00','01')"}

        #交易收付款,缩写FF
        FF_condition_str= {"SH":"收交易","FU":"付交易","FF":"收付交易"}
        FF_condition= {"SH":"TSDR='01'","FU":"TSDR='02'","FF":"TSDR in('01','02')"}

        FF_condition_str= {"SH":"收交易","FU":"付交易"}
        FF_condition= {"SH":"TSDR='01'","FU":"TSDR='02'"}
        
        bsn_label = ["币种","现金转账","收付",]
        bsn_leibie = {
            "币种":{
                "缩写表示":BB_condition_str,
                "判断条件":BB_condition
            },
            "收付":{
                "缩写表示":FF_condition_str,
                "判断条件":FF_condition
            },
            "现金转账":{
                "缩写表示":MJ_condition_str,
                "判断条件":MJ_condition
            },
            
        }
        jiaoyi_dict = {}
        # jiaoyi_dict["统计对象及方法"] = {
        #     "金额":"sum","笔数":"count",
        #     "对手账户":{"col_name":"TCAC", "func":"count", "desc":["对手账户","对方账户"]},
        #     "对手非同名账户":{"col_name":"TCNM", "func":"count", "desc":["对手非同名账户","对方非同名账户"]},
        #     "交易发生地国别":{"col_name":"TRCD_COUNTRY", "func":"count", "desc":["交易发生地国别","交易发生地国家"]},
        #     "交易IP地址":{"col_name":"TRAN_IP", "func":"count", "desc":["交易IP地址","交易的IP地址个数"]},
        #     "交易发生地":{"col_name":"TRCD_AREA", "func":"count", "desc":["交易发生地","交易发生地行政区"]},
        #     "对方所在地区":{"col_name":"CFRC_AREA", "func":"count", "desc":["对方所在地区","对方所在地"]},
        #     }
        
        jiaoyi_dict["统计对象列表"] = ["次数","金额","取折美金额","客户数"]
        jiaoyi_dict["统计对象及方法"] = {
            "次数":{
                "同义词":["交易次数","次数汇总"],
                "处理方法":"count_then1",
            },
            "金额":{
                "同义词":["金额汇总"],
                "处理方法":"sum_rmb",
            },
            "取折美金额":{
                "同义词":["折美金额"],
                "处理方法":"sum_usd",
            },
            "客户数":{
                "同义词":["客户个数"],
                "处理方法":"count_kehu",
            },
            
        }

        
        d1 = {
            "业务类别":['收付'],
            '收付': {
                "desc":"付交易次数汇总中出现了付交易这三个字，对应业务类别收付中的付交易",
                '涉及类别':["FU"],
                '缩写表示': {'FU': '付交易'},
                '判断条件': {'FU': "TSDR='02'"}
            },
            "统计对象及方法":{
                    "统计对象列表":["次数"],
                    "次数":{
                        "desc":"付交易次数汇总中出现了次数这两个字，对应统计对象及方法中的次数",
                        "同义词":["交易次数","次数汇总"],
                        "处理方法":"count_then1",
                    },
                }
                
            }
        
        d2 = {
            "业务类别":['现金转账','收付'],
            '现金转账': {
                "desc":"【现金/不分】收交易次数汇总（交易发生地=CHN.Z01.Z02.Z03）中出现了【现金/不分】，对应业务类别现金转账中的现金与不分",
                '涉及类别':["XJ","ALL"],
                '缩写表示': {"XJ":"现金","ALL":"不分"},
                '判断条件':  {"XJ":"CASH_IND='00'","ALL":"CASH_IND in('00','01')"}
            },
            '收付': {
                "desc":"【现金/不分】收交易次数汇总（交易发生地=CHN.Z01.Z02.Z03）中出现了收交易，对应业务类别收付中的收交易",
                '涉及类别':["SH"],
                '缩写表示': {'SH': '收交易'},
                '判断条件': {'SH': "TSDR='01'"}
            },
            "统计对象及方法":{
                    "统计对象列表":["次数"],
                    "次数":{
                        "desc":"【现金/不分】收交易次数汇总（交易发生地=CHN.Z01.Z02.Z03）中出现了次数这两个字，对应统计对象及方法中的次数",
                        "同义词":["交易次数","次数汇总"],
                        "处理方法":"count_then1",
                    },
                }
                
            }
            
        examples = f"""
        付交易次数汇总:f{d1},
        【现金/不分】收交易次数汇总（交易发生地=CHN.Z01.Z02.Z03）:f{d2},
        
        
        """

        
        _prompt = f"""
        你的任务是对用户问题进行归类，判断用户问题属于{bsn_label}中的哪些类别,以及属于{jiaoyi_dict["统计对象列表"]}中的哪些统计对象及方法
        1. 过滤用户问题中与{bsn_label}和{jiaoyi_dict["统计对象列表"]}无关的内容，只留下与{bsn_label}和{jiaoyi_dict["统计对象列表"]}相关的内容
        2. 参考{bsn_label}提取涉及的业务类别，类别是固定的，只能从{bsn_label}中取
        3. 提取完类别后，参考{bsn_leibie}返回所提取类别的缩写表示与判断条件
        4. 整理并提取统计对象及方法信息;若金额与取折美金额同时出现，则按取折美金额处理
        
        以JSON格式输出。包含的字段只能是业务类别{bsn_label}中出现过的类别
        每一个字段的类别皆是字典，单个类别字段是一个字典，它包含的字段有：
        1. 涉及类别,list类型，其值为所涉及到业务类别中缩写形式的类别，值为缩写列表
        2. 缩写表示,dict类型，涉及类别list中元素的缩写表示
        3. 判断条件,dict类型，涉及类别list中元素的判断条件
        4. 统计对象及方法,dict类型，参考{jiaoyi_dict["统计对象及方法"]}中的元素
        
        示例：
        {examples}
        
        用户问题:
        {query}

        """
        return _prompt
    
yj = SqlJiaoYi()
                
    


'''
Description: 常用词性组合
Author: 七三学徒
Date: 2022-01-29 15:52:32
FilePath: /73_code/aisty/lgg/pos.py
'''


keep_pos="q,qg,qt,qv,s,t,tg,g,gb,gbc,gc,gg,gm,gp,m,mg,Mg,mq,n,an,vn,ude1,nr,ns,nt,nz,nb,nba,nbc,nbp,nf,ng,nh,nhd,o,nz,nx,ntu,nts,nto,nth,ntch,ntcf,ntcb,ntc,nt,nsf,ns,nrj,nrf,nr2,nr1,nr,nnt,nnd,nn,nmc,nm,nl,nit,nis,nic,ni,nhm,nhd"
keep_pos_nouns=set(keep_pos.split(","))
keep_pos_v="v,vd,vg,vf,vl,vshi,vyou,vx,vi"
keep_pos_v=set(keep_pos_v.split(","))
keep_pos_p=set(['p','pbei','pba'])

# 命名实体识别语法1
stanford_ner1={
        'stanford_ner_drop': r"""
        DATE:{<DATE>+<MISC>?<DATE>*}
        {<DATE>+<MISC>?<DATE>*}
        {<DATE>+}
        {<TIME>+}
        ORGANIZATIONL:{<ORGANIZATION>+}
        LOCATION:{<LOCATION|STATE_OR_PROVINCE|CITY|COUNTRY>+}
        """
    }




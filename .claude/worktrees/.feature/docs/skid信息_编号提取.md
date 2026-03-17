# 我希望从每条记录中提取“滚床编号” ，并增加factor字段，weight字段
格式如下：
{"id": "", "type": <"xxx">, "plc": <"xxx">, "tag": <"xxx"> ,"factor": <{"norm":"4","e5":"3"}>, "RBindex": <"xxx">, "weight": <0>}
---
情况1：
{"id":"","type":"advise","plc":"L3FKT1","tag":".L3FKT1_1H_1H200OC_1H200OCFF1.ST[1].IL.SD.I1030_RBDataSkidNo"}
{"id":"","type":"advise","plc":"L3FKT1","tag":".L3FKT1_1H_1H200OC_1H200OCFF1.ST[2].IL.SD.I1030_RBDataSkidNo"}
提取为：
{"id": "", "type": "advise", "plc": "L3FKT1", "tag": ".L3FKT1_1H_1H200OC_1H200OCFF1.ST[1].IL.SD.I1030_RBDataSkidNo", "factor": <{"norm":"4","e5":"3"}>, "RBindex": "1H200OCFF1.ST[1]", "weight": <0>}
{"id": "", "type": "advise", "plc": "L3FKT1", "tag": ".L3FKT1_1H_1H200OC_1H200OCFF1.ST[2].IL.SD.I1030_RBDataSkidNo", "factor": <{"norm":"4","e5":"3"}>, "RBindex": "1H200OCFF1.ST[2]", "weight": <0>}

情况2:
{"id":"","type":"advise","plc":"L3FUB2","tag":".L3FUB2_1A_1A010RB_1A010RB.IL.SD.I1030_RBDataSkidNo"}
{"id":"","type":"advise","plc":"L3FUB2","tag":".L3FUB2_1B_1B020RB_1B020RB.ILO.SD.I1030_RBDataSkidNo"}
提取为：
{"id": "", "type": "advise", "plc": "L3FUB2", "tag": ".L3FUB2_1A_1A010RB_1A010RB.IL.SD.I1030_RBDataSkidNo", "factor": <{"norm":"4","e5":"3"}>, "RBindex": "1A010RB", "weight": <0>}
{"id": "", "type": "advise", "plc": "L3FUB2", "tag": ".L3FUB2_1B_1B020RB_1B020RB.ILO.SD.I1030_RBDataSkidNo", "factor": <{"norm":"4","e5":"3"}>, "RBindex": "1B020RB", "weight": <0>}

情况3：
{"id":"","type":"advise","plc":"L3FUB2","tag":".L3FUB2_1G_15AS_1G175EL_1G175RB.IL.SD.I1030_RBDataSkidNo"},
{"id":"","type":"advise","plc":"L3FUB2","tag":".L3FUB2_1G_15AS_1G400EH_1G400RB.IL.SD.I1030_RBDataSkidNo"}
提取为：
{"id": "", "type": "advise", "plc": "L3FUB2", "tag": ".L3FUB2_1G_15AS_1G175EL_1G175RB.IL.SD.I1030_RBDataSkidNo", "factor": <{"norm":"4","e5":"3"}>, "RBindex": "1G175RB", "weight": <0>}
{"id": "", "type": "advise", "plc": "L3FUB2", "tag": ".L3FUB2_1G_15AS_1G400EH_1G400RB.IL.SD.I1030_RBDataSkidNo", "factor": <{"norm":"4","e5":"3"}>, "RBindex": "1G400RB", "weight": <0>}
---
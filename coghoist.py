import streamlit as st
import random
from pymongo import MongoClient
from urllib.parse import quote_plus
import certifi,datetime

st.set_page_config(
    page_title="易经思维哑铃",
    page_icon="☯"
    
)
st.title('易经思维哑铃')
st.text('用象数思维重构现实困境的底层逻辑')
@st.cache_resource(show_spinner="正在连接数据库")
def get_mongo_collection():
    try:
        secrets = st.secrets.mongodb
        config = {
            "username": secrets.username,
            "password": secrets.password,
            "cluster": secrets.cluster,
            "db_name": secrets.db_name,
            "appname": secrets.appname,
            "collection": secrets.collection
        }
        username = quote_plus(config["username"])
        password = quote_plus(config["password"])
        uri = f"mongodb+srv://{username}:{password}@{config['cluster']}/{config['db_name']}?appName={config['appname']}"

        client = MongoClient(uri, tls=True, tlsCAFile=certifi.where())
        client.admin.command("ping")
        db = client[config["db_name"]]
        return db[config["collection"]]
    except Exception as e:
        st.error(f"无法连接到 MongoDB: {e}")
        return None

def query_gua(zhugua_bin, hugua_bin, biangua_bin):
    collection = get_mongo_collection()
    query = {"binary": {"$in": [zhugua_bin, hugua_bin, biangua_bin]}}
    docs = collection.find(query)
    ret = {}
    for result in docs:
        if result['binary'] == zhugua_bin :
            ret['zhugua'] = result
        if result['binary'] == hugua_bin :
            ret['hugua'] = result
        if result['binary'] == biangua_bin :
            ret['biangua'] = result
    return ret

def find_gua(query):
    collection = get_mongo_collection()
    return collection.find_one(query)

gua_dict = {
    1: {"name": "乾", "symbol": "☰", "wuxing": "金", "binary": "111"},
    2: {"name": "兑", "symbol": "☱", "wuxing": "金", "binary": "110"},
    3: {"name": "离", "symbol": "☲", "wuxing": "火", "binary": "101"},
    4: {"name": "震", "symbol": "☳", "wuxing": "木", "binary": "100"},
    5: {"name": "巽", "symbol": "☴", "wuxing": "木", "binary": "011"},
    6: {"name": "坎", "symbol": "☵", "wuxing": "水", "binary": "010"},
    7: {"name": "艮", "symbol": "☶", "wuxing": "土", "binary": "001"},
    8: {"name": "坤", "symbol": "☷", "wuxing": "土", "binary": "000"}
}

def calculate_gua(num1, num2, num3):

    shang = (num1 % 8) or 8

    xia = ((num2 + num3) % 8) or 8

    dong_yao = (num1 + num2 + num3) % 6 or 6
    return shang, xia, dong_yao


def generate_gua(shang, xia, dong_yao):

    shang = shang % 8 or 8
    xia = xia % 8 or 8

    
    zhu_shang = gua_dict[shang]
    zhu_xia = gua_dict[xia]
    six_yao = zhu_xia["binary"] + zhu_shang["binary"]  

    hu_shang_bin = six_yao[2:5]  
    hu_xia_bin = six_yao[1:4]    
    hu_shang = next(g for g in gua_dict.values() if g["binary"] == hu_shang_bin)
    hu_xia = next(g for g in gua_dict.values() if g["binary"] == hu_xia_bin)

    bian_bin = flip_bit_at_position(six_yao,dong_yao-1)
    bian_shang_bin = bian_bin[3:]
    bian_xia_bin = bian_bin[:3]

    bian_shang = next(g for g in gua_dict.values() if g["binary"] == bian_shang_bin)
    bian_xia = next(g for g in gua_dict.values() if g["binary"] == bian_xia_bin)
    
    return {
        "主卦": (zhu_shang["name"], zhu_xia["name"]),
        "互卦": (hu_shang["name"], hu_xia["name"]),
        "变卦": (bian_shang["name"], bian_xia["name"]),
        "变爻位置": dong_yao
    }


def wuxing_analysis(zhu, hu, bian, dong_yao):

    gua_wuxing = {
        "乾": "金", "兑": "金", "离": "火", "震": "木",
        "巽": "木", "坎": "水", "艮": "土", "坤": "土"
    }

    shengke_relation = {

        ("木","火"): "体生用（耗损小凶）", ("火","土"): "体生用（耗损小凶）",
        ("土","金"): "体生用（耗损小凶）", ("金","水"): "体生用（耗损小凶）",
        ("水","木"): "体生用（耗损小凶）",

        ("金","木"): "体克用（压制小吉）", ("木","土"): "体克用（压制小吉）",
        ("土","水"): "体克用（压制小吉）", ("水","火"): "体克用（压制小吉）",
        ("火","金"): "体克用（压制小吉）",

        ("木","金"): "用克体（反克大凶）", ("土","木"): "用克体（反克大凶）",
        ("水","土"): "用克体（反克大凶）", ("火","水"): "用克体（反克大凶）",
        ("金","火"): "用克体（反克大凶）",

        ("金","金"): "比和（平衡中吉）", ("木","木"): "比和（平衡中吉）",
        ("水","水"): "比和（平衡中吉）", ("火","火"): "比和（平衡中吉）",
        ("土","土"): "比和（平衡中吉）"
    }


    def get_ti_yong(shang, xia, dong_yao):
        if dong_yao <= 3:  
            return {"体": gua_wuxing[shang], "用": gua_wuxing[xia]}
        else:             
            return {"体": gua_wuxing[xia], "用": gua_wuxing[shang]}


    phases = {
        "本卦": get_ti_yong(zhu[0], zhu[1], dong_yao),
        "互卦": get_ti_yong(hu[0], hu[1], dong_yao),
        "变卦": get_ti_yong(bian[0], bian[1], dong_yao)
    }


    power = "（用卦得动爻加持）" if dong_yao <=3 else "（体卦得动爻加持）"


    report = {}
    for phase in phases:
        ti = phases[phase]["体"]
        yong = phases[phase]["用"]
        relation = shengke_relation.get((ti, yong), "五行无直接生克")

        if "反克" in relation:
            relation += "（需结合卦气旺衰判断）"
        
        report[phase] = f"{phase.ljust(4)}：{ti}→{yong} → {relation}{power if phase=='主卦' else ''}"
       
    return report


wuxing_map = {
    "乾": {"wx": "金", "方位": "西北"},
    "兑": {"wx": "金", "方位": "正西"},
    "离": {"wx": "火", "方位": "正南"},
    "震": {"wx": "木", "方位": "正东"},
    "巽": {"wx": "木", "方位": "东南"},
    "坎": {"wx": "水", "方位": "正北"},
    "艮": {"wx": "土", "方位": "东北"},
    "坤": {"wx": "土", "方位": "西南"}
}


def get_season():
    now = datetime.datetime.now()
    month = now.month
    if 3 <= month <= 5: return '春'
    elif 6 <= month <= 8: return '夏'
    elif 9 <= month <= 11: return '秋'
    else: return '冬'

season_wx = {'春':'木', '夏':'火', '秋':'金', '冬':'水'}


def wuxing_analysis(master, guest):
    relations = {
        ("金", "木"): "金克木（凶）",
        ("木", "土"): "木克土（凶）",
        ("土", "水"): "土克水（凶）",
        ("水", "火"): "水克火（凶）",
        ("火", "金"): "火克金（凶）",
        ("木", "金"): "木耗金（平）",
        ("土", "木"): "土耗木（平）",
        ("水", "土"): "水耗土（平）",
        ("火", "水"): "火耗水（平）",
        ("金", "火"): "金耗火（平）",
        ("金", "土"): "土生金（吉）",
        ("土", "火"): "火生土（吉）",
        ("火", "木"): "木生火（吉）",
        ("木", "水"): "水生木（吉）",
        ("水", "金"): "金生水（吉）",
        ("金", "金"): "比和（大吉）",
        ("木", "木"): "比和（大吉）",
        ("水", "水"): "比和（大吉）",
        ("火", "火"): "比和（大吉）",
        ("土", "土"): "比和（大吉）"
    }
    return relations.get((master, guest), "未知关系")


def get_guaqi_status(gua):
    current_season = get_season()
    gua_wx = wuxing_map[gua]["wx"]
    
    if gua_wx == season_wx[current_season]:
        return "旺"
    elif season_wx[current_season] == "木" and gua_wx == "土":
        return "衰"
    elif season_wx[current_season] == "火" and gua_wx == "金":
        return "衰"
    elif season_wx[current_season] == "金" and gua_wx == "木":
        return "衰" 
    elif season_wx[current_season] == "水" and gua_wx == "火":
        return "衰"
    else:
        return "平"

def meihua_analysis(zhu, hu, bian, dong_yao):

    shang_gua, xia_gua = zhu
    ti_yong = "上卦为用" if dong_yao > 3 else "下卦为用"
    ti_gua = xia_gua if dong_yao > 3 else shang_gua
    yong_gua = shang_gua if dong_yao > 3 else xia_gua


    ti_wx = wuxing_map[ti_gua]["wx"]
    yong_wx = wuxing_map[yong_gua]["wx"]
    ti_yong_rel = wuxing_analysis(ti_wx, yong_wx)
    

    ti_guaqi = get_guaqi_status(ti_gua)
    yong_guaqi = get_guaqi_status(yong_gua)

    hu_shang_wx = wuxing_map[hu[0]]["wx"]
    hu_xia_wx = wuxing_map[hu[1]]["wx"]
    hu_shang_rel = wuxing_analysis(ti_wx, hu_shang_wx)
    hu_xia_rel = wuxing_analysis(ti_wx, hu_xia_wx)

    bian_shang_wx = wuxing_map[bian[0]]["wx"]
    bian_xia_wx = wuxing_map[bian[1]]["wx"]
    bian_shang_rel = wuxing_analysis(ti_wx, bian_shang_wx)
    bian_xia_rel = wuxing_analysis(ti_wx, bian_xia_wx)

    try:
        ti_yong_ji_xiong = ti_yong_rel.split("（")[1].replace("）", "")
        initial_status = "吉" if "吉" in ti_yong_ji_xiong else "平" if "平" in ti_yong_ji_xiong else "凶"
    except (IndexError, TypeError):
        ti_yong_ji_xiong = "关系未明"
        initial_status = "需人工研判"
    
    zhugua_bin = calculate_gua_binary(result['主卦'][0][0],result['主卦'][1][0])
    hugua_bin = calculate_gua_binary(result['互卦'][0][0],result['互卦'][1][0])
    biangua_bin = calculate_gua_binary(result['变卦'][0][0],result['变卦'][1][0])

    sangua = query_gua(zhugua_bin, hugua_bin, biangua_bin)
    
    st.info('本卦（现状）：代表事物发展的初始状态与当前情形', icon="🌱")
    st.metric(f"{sangua['zhugua']['guaxiang']}", 
              f"{sangua['zhugua']['guaming']}{sangua['zhugua']['guahua']}")
    st.markdown(f"""
        - ​**体卦**：{ti_gua}卦（{wuxing_map[ti_gua]['wx']}）卦气：{ti_guaqi}
        - ​**用卦**：{yong_gua}卦（{wuxing_map[yong_gua]['wx']}）卦气：{yong_guaqi}
        - ​**体用关系**：{ti_yong_rel} → ​**{ti_yong_ji_xiong}**
                """)
    with st.expander(f"{sangua['zhugua']['guaming']}卦的卦爻辞"):
        show_gua(sangua['zhugua'])

    st.info('互卦（过程）：揭示事物发展的中间过程与潜在动因', icon="🪴")
    st.metric(f"{sangua['hugua']['guaxiang']}", f"{sangua['hugua']['guaming']}{sangua['hugua']['guahua']}")
    st.markdown(f"""
        | 卦位 | 卦名 | 五行 | 卦气 | 与体卦关系 |
        |------|------|------|------|------------|
        | 上互 | {hu[0]} | {hu_shang_wx} | {get_guaqi_status(hu[0])} | {hu_shang_rel} |
        | 下互 | {hu[1]} | {hu_xia_wx} | {get_guaqi_status(hu[1])} | {hu_xia_rel} |
                
                """)
    st.text(" ")
    with st.expander(f"{sangua['hugua']['guaming']}卦的卦爻辞"):
        show_gua(sangua['hugua'])

    st.info('变卦（结果）：预示事物发展的最终结果与趋势走向', icon="🌲")
    st.metric(f"{sangua['biangua']['guaxiang']}", f"{sangua['biangua']['guaming']}{sangua['biangua']['guahua']}")
    st.markdown(f"""
        | 卦位 | 卦名 | 五行 | 卦气 | 与体卦关系 |
        |------|------|------|------|------------|
        | 变上 | {bian[0]} | {bian_shang_wx} | {get_guaqi_status(bian[0])} | {bian_shang_rel} |
        | 变下 | {bian[1]} | {bian_xia_wx} | {get_guaqi_status(bian[1])} | {bian_xia_rel} |
                """)
    st.text(" ")
    with st.expander(f"{sangua['biangua']['guaming']}卦的卦爻辞"):
        show_gua(sangua['biangua'])
    
    st.warning("综合分析")
    st.markdown(f"""
        1. ​**当前态势**：{initial_status}（主卦体用{ti_yong_ji_xiong}）
        2. ​**发展过程**：互卦呈现{hu_shang_rel.split('（')[0]}与{hu_xia_rel.split('（')[0]}的交织
        3. ​**最终结果**：变卦显示{bian_shang_rel.split('（')[0]}与{bian_xia_rel.split('（')[0]}的叠加
        4. ​**卦气影响**：体卦{ti_gua}正值{ti_guaqi}，{['宜静守','宜进取'][ti_guaqi=='旺']}
        5. ​**应期推断**：{calculate_period(result['变爻位置'])} 
        6. ​**方位提示**：{wuxing_map[ti_gua]['方位']}方位动向
                """)
    
def calculate_period(dong_yao):
    base_days = [1, 3, 5, 7, 9, 11]
    return f"{base_days[dong_yao-1]}日内" if dong_yao <=6 else "超过七日"


def calculate_gua_binary(upper_gua, lower_gua):
    gua_dict = {
        "乾": "111",
        "坤": "000",
        "震": "100",
        "巽": "011",
        "坎": "010",
        "离": "101",
        "艮": "001",
        "兑": "110"
    }
    lower_binary = gua_dict.get(lower_gua)
    upper_binary = gua_dict.get(upper_gua)

    if lower_binary and upper_binary:
        combined_binary = lower_binary + upper_binary
        return combined_binary
    else:
        return None

def flip_bit_at_position(binary_string, n):
    return binary_string[:n] + str(1 - int(binary_string[n])) + binary_string[n + 1:] if 0 <= n < len(binary_string) else binary_string


def show_gua(doc):
    st.metric(f"{doc['guaxiang']}", f"{doc['guaming']}")
    guaxiang = st.container()
    guaxiang.markdown(f"<div style='font-size:256px;text-align: center;'>{doc['guahua']}</div>", unsafe_allow_html=True)

   
    st.markdown("***")
    
    st.markdown(f"#### {doc['guaci']}")
    st.markdown(f"> <span style='color:#FF0000;'>彖传：</span>{doc['tuanzhuan']}", unsafe_allow_html=True)
    st.markdown(f"> <span style='color:#FF0000;'>象传：</span>{doc['xiangzhuan']['daxiang']}", unsafe_allow_html=True)
    st.markdown("***")

    i = 0
    for yaoci in doc['yaoci']:
        st.markdown(f"#### {yaoci}")
        st.markdown(f"> <span style='color:#FF0000;'>象传：</span>{doc['xiangzhuan']['xiaoxiang'][i]}", unsafe_allow_html=True)
        i+=1
        st.markdown("***")


# Streamlit界面

tabA, tabB = st.tabs(["梅花易数", "易经速查"])
with tabA:
    st.success('数字→卦象→决策：直觉转数字，数字生卦象，卦象助决策')
    st.caption("在三个输入框里填写第一时间想到的数字,比如想到的车牌号、生日数字都可以。")
    num1 = st.number_input("第一个数代表现状（上卦）", min_value=1, value=random.randint(1, 99))
    num2 = st.number_input("第二个数代表本质（下卦）", min_value=1, value=random.randint(1, 99))
    num3 = st.number_input("第三个数代表变化（动爻）", min_value=1, value=random.randint(1, 99))

    if st.button("☯ 起卦：数字生卦象", type="primary", use_container_width=True):
        shang, xia, dong_yao = calculate_gua(num1, num2, num3)
        result = generate_gua(shang, xia, dong_yao)
        ti = shang
        yong = xia
        if dong_yao <= 3 :
            ti = xia
            yong = shang
        
        zhugua_bin = calculate_gua_binary(result['主卦'][0][0],result['主卦'][1][0])
        hugua_bin = calculate_gua_binary(result['互卦'][0][0],result['互卦'][1][0])
        biangua_bin = calculate_gua_binary(result['变卦'][0][0],result['变卦'][1][0])

        sangua = query_gua(zhugua_bin, hugua_bin, biangua_bin)

        meihua_analysis(result['主卦'], result['互卦'], result['变卦'], dong_yao)

with tabB:
    tab1, tab2, tab3 = st.tabs(["按卦序查", "按上下卦查", "按爻位查"])

with tab1:
    guaxu = st.slider(label="选择卦序",min_value=1,max_value=64,value=1)
    if st.button("查询", type="primary", use_container_width=True, key='q1'):
        
        query = {"index": guaxu}
        doc = find_gua(query)
        if doc:
            show_gua(doc)
  
with tab2:
    options = [
        {"display": "乾 ☰", "id": '111'},
        {"display": "坤 ☷", "id": '000'},
        {"display": "震 ☳", "id": '100'},
        {"display": "巽 ☴", "id": '011'},
        {"display": "坎 ☵", "id": '010'},
        {"display": "离 ☲", "id": '101'},
        {"display": "艮 ☶", "id": '001'},
        {"display": "兑 ☱", "id": '110'}
    ]


    shang = st.selectbox(
        label="选择上卦",
        options=range(len(options)), 
        format_func=lambda x: options[x]["display"],  
        key="shang"
    )
    xia = st.selectbox(
        label="选择下卦",
        options=range(len(options)),  
        format_func=lambda x: options[x]["display"], 
        key="xia"
    )
    if st.button("查询", type="primary", use_container_width=True, key='q3'):
        binary = options[xia]['id'] + options[shang]["id"]
        query = {"binary": binary}
        doc = find_gua(query)
        if doc:
            show_gua(doc)
        

with tab3:
    st.caption("选择每一爻")
    options = {
        0: "阴", 
        1: "阳"
    }
    s6 = st.select_slider(
        "上爻",
        options=list(options.keys()),
        format_func=lambda x: options[x]
    )
    s5 = st.select_slider(
        "五爻",
        options=list(options.keys()),
        format_func=lambda x: options[x]
    )
    s4 = st.select_slider(
        "四爻",
        options=list(options.keys()),
        format_func=lambda x: options[x]
    )
    s3 = st.select_slider(
        "三爻",
        options=list(options.keys()),
        format_func=lambda x: options[x]
    )
    s2 = st.select_slider(
        "二爻",
        options=list(options.keys()),
        format_func=lambda x: options[x]
    )
    s1 = st.select_slider(
        "初爻",
        options=list(options.keys()),
        format_func=lambda x: options[x]
    )
    if st.button("查询", type="primary", use_container_width=True, key='q2'):
        binary=f"{s1}{s2}{s3}{s4}{s5}{s6}"
        query = {"binary": binary}
        doc = find_gua(query)
        if doc:
            show_gua(doc)
        
    

st.text(' ')
st.markdown("""
            `
            > 1. 本工具仅限于传统文化研习用途；
            >
            > 2. 严禁将其与封建迷信活动相关联;
            >
            > 3. 自行承担因理解偏差产生的后果。
            `
            `""")
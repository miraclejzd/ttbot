filter_list = [
    "原神",
    "十连",
    "单抽",
    "-",
    "@",
    "#",
    "/",
    "\\",
    "查询",
    "语录",
    "入典",
    "随机",
    "抽卡",
    "help",
    "帮助",
    "点歌",
    "来点",
    "更新"
]


def filt(content: str) -> bool:
    for ft in filter_list:
        if content.find(ft) != -1:
            return False
    return True

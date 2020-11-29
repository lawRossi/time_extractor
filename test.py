from time_extractor.util import str2number
from time_extractor.extraction import TimeExtractor
import json
import arrow


if __name__ == "__main__":
    assert(str2number("七") == 7)
    assert(str2number("十") == 10)
    assert(str2number("拾") == 10)
    assert(str2number("十三") == 13)
    assert(str2number("三十") == 30)
    assert(str2number("三拾") == 30)
    assert(str2number("四佰") == 400)
    assert(str2number("伍仟") == 5000)
    assert(str2number("拾万") == 100000)
    assert(str2number("叁萬") == 30000)
    assert(str2number("二十三") == 23)
    assert(str2number("三百二十三") == 323)
    assert(str2number("一千零二十二") == 1022)
    assert(str2number("九万八千七百零9") == 98709)
    assert(str2number("三十八万零二十三") == 380023)
    assert(str2number("9000万7千三百") == 90007300)
    assert(str2number("壹仟零2十二") == 1022)
    assert(str2number("十亿八千万零叁拾") == 1080000030)
    assert(str2number("二百五") == 250)
    assert(str2number("三千九") == 3900)
    assert(str2number("三万二") == 32000)
    assert(str2number("三千九十") == 3090)
    assert(str2number("叁万二百") == 30200)
    assert(str2number("一万零二百") == 10200)

    assert(str2number("万三") == -1)
    assert(str2number("五万千") == -1)
    assert(str2number("五万3千百") == -1)

    extractor = TimeExtractor()

    with open("test_cases.txt", encoding="utf-8") as fi:
        line = fi.readline().strip()
        base = arrow.get(line, "YYYY-MM-DD HH:mm:ss")
        for line in fi:
            splits = line.strip().split("\t")
            items = list(extractor.extract(splits[0], base))
            if len(splits) != 4:
                assert len(items) == 0
            else:
                assert len(items) == 1
                assert items[0].time_str == splits[1]
                assert items[0].to_dict()["type"] == splits[2]
                result = json.loads(splits[-1])
                extracted = items[0].to_dict()
                if  extracted != result:
                    print(result, extracted)

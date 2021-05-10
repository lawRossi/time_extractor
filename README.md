# Time Extractor

![Licence](https://img.shields.io/github/license/lawRossi/time_extractor)
![Python](https://img.shields.io/badge/Python->=3.6-blue)

一个简单实用的中文时间抽取和标准化工具包。欢迎使用，如发现问题或有优化建议，欢迎反馈和赐教。


## 安装
clone https://github.com/lawRossi/time_extractor.git

python setup.py install


## 特性
- 时间抽取

  对应Time类，支持具体时间（如2020年12月4日8点）和模糊时间（如下午3点)的抽取，并对抽取的时间进行标准化，进行标准化时可以指定时间基准。

- 时间区间抽取

  对应TimeRange类，支持时间区间（如今天上午，2020年10月1日到2020年10月8日等）的抽取。

- 时间差抽取

  对应TimeDelta类，支持时间差（如3个工作日后，2个小时后等）的抽取。

- 时间周期

  对应TimeCycle类，支持“时间周期”（如每年3月，每天4点等）的抽取。

具体支持的时间元素类型可以参考test_cases.txt。


## 使用
```python
from time_extractor.extraction import TimeExtractor
import arrow
from time_extractor.extraction import Time


extractor = TimeExtractor()
text = "今天晚上7点提交了代码"
base = arrow.get()
for item in extractor.extract(text, base=base):
    print(item.to_dict())
    if isinstance(item, Time):
        print(item.to_arrow())
```

TimeExtractor类的extract函数有两个特殊缺省参数，其中range_mapping定义模糊时间区间（上午，晚上）的具体时间定义，不指定该参数则使用默认定义，具体参考Time类源码；另一个参数handle_special_year指定是否进行特殊年份的转换，例如将“98年”转换为“1998年”，“12年”转换为“2012年”，具体参考Time类源码。


## 注意事项

1. 由于时间抽取是基于正则表达式实现的，所以不能根据上下文判断抽取的内容是否是时间元素。例如，从文本“王明天说了他不来”会抽取出“明天”。这一点在使用工具包时需要注意。

2. 对于周日的处理比较绕，这里做以下约定：

   1)假如“今天”是2020-11-30(周一)，周日指的是“接下来一个周日”(2020-12-06)；上周日指的是“昨天”(2010-11-29); 下周日指的(2020-12-13)。
   
   2)假如“今天”是2020-11-29(周日)，则周六指的是接下来一个“周六”(2020-12-05)，上周六指的是“昨天”(2020-11-28)。

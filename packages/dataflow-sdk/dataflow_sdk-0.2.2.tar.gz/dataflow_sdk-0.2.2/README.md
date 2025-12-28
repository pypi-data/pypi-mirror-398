# dataflow-sdk

## Example

```python
from dataflow_sdk import save_items, Record
from dataflow_sdk.entity.model import CrawlType

result = {
    'name': 'xiaoming',
    "age": 25,
    "hello": "world",
    "world": 1121211
}

records = [Record(
    crawl_url=f"https://add.weee.tsinghua.edu.cn/{x}",
    crawl_type=CrawlType.ITEM,
    data=result,
    metadata={"name": "gage"},
) for x in range(10)]

save_items('Your Sink ID', records)
```
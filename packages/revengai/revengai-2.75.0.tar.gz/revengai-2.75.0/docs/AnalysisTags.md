# AnalysisTags


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**analysis_tags** | [**List[TagItem]**](TagItem.md) |  | 

## Example

```python
from revengai.models.analysis_tags import AnalysisTags

# TODO update the JSON string below
json = "{}"
# create an instance of AnalysisTags from a JSON string
analysis_tags_instance = AnalysisTags.from_json(json)
# print the JSON string representation of the object
print(AnalysisTags.to_json())

# convert the object into a dict
analysis_tags_dict = analysis_tags_instance.to_dict()
# create an instance of AnalysisTags from a dict
analysis_tags_from_dict = AnalysisTags.from_dict(analysis_tags_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



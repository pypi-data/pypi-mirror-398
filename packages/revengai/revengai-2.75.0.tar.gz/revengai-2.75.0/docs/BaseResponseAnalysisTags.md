# BaseResponseAnalysisTags


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**status** | **bool** | Response status on whether the request succeeded | [optional] [default to True]
**data** | [**AnalysisTags**](AnalysisTags.md) |  | [optional] 
**message** | **str** |  | [optional] 
**errors** | [**List[ErrorModel]**](ErrorModel.md) |  | [optional] 
**meta** | [**MetaModel**](MetaModel.md) | Metadata | [optional] 

## Example

```python
from revengai.models.base_response_analysis_tags import BaseResponseAnalysisTags

# TODO update the JSON string below
json = "{}"
# create an instance of BaseResponseAnalysisTags from a JSON string
base_response_analysis_tags_instance = BaseResponseAnalysisTags.from_json(json)
# print the JSON string representation of the object
print(BaseResponseAnalysisTags.to_json())

# convert the object into a dict
base_response_analysis_tags_dict = base_response_analysis_tags_instance.to_dict()
# create an instance of BaseResponseAnalysisTags from a dict
base_response_analysis_tags_from_dict = BaseResponseAnalysisTags.from_dict(base_response_analysis_tags_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



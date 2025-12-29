# AnalysisAccessInfo


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**owner** | **bool** |  | 
**username** | **str** |  | 

## Example

```python
from revengai.models.analysis_access_info import AnalysisAccessInfo

# TODO update the JSON string below
json = "{}"
# create an instance of AnalysisAccessInfo from a JSON string
analysis_access_info_instance = AnalysisAccessInfo.from_json(json)
# print the JSON string representation of the object
print(AnalysisAccessInfo.to_json())

# convert the object into a dict
analysis_access_info_dict = analysis_access_info_instance.to_dict()
# create an instance of AnalysisAccessInfo from a dict
analysis_access_info_from_dict = AnalysisAccessInfo.from_dict(analysis_access_info_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



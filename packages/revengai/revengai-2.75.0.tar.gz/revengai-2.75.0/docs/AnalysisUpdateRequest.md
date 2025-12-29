# AnalysisUpdateRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**binary_name** | **str** |  | [optional] 
**analysis_scope** | **str** |  | [optional] 

## Example

```python
from revengai.models.analysis_update_request import AnalysisUpdateRequest

# TODO update the JSON string below
json = "{}"
# create an instance of AnalysisUpdateRequest from a JSON string
analysis_update_request_instance = AnalysisUpdateRequest.from_json(json)
# print the JSON string representation of the object
print(AnalysisUpdateRequest.to_json())

# convert the object into a dict
analysis_update_request_dict = analysis_update_request_instance.to_dict()
# create an instance of AnalysisUpdateRequest from a dict
analysis_update_request_from_dict = AnalysisUpdateRequest.from_dict(analysis_update_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



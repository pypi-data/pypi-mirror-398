# AnalysisCreateResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**analysis_id** | **int** | ID of created analysis | 
**binary_id** | **int** | ID of created binary | 

## Example

```python
from revengai.models.analysis_create_response import AnalysisCreateResponse

# TODO update the JSON string below
json = "{}"
# create an instance of AnalysisCreateResponse from a JSON string
analysis_create_response_instance = AnalysisCreateResponse.from_json(json)
# print the JSON string representation of the object
print(AnalysisCreateResponse.to_json())

# convert the object into a dict
analysis_create_response_dict = analysis_create_response_instance.to_dict()
# create an instance of AnalysisCreateResponse from a dict
analysis_create_response_from_dict = AnalysisCreateResponse.from_dict(analysis_create_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



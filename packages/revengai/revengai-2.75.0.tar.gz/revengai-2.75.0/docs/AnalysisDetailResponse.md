# AnalysisDetailResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**access** | [**AnalysisAccessInfo**](AnalysisAccessInfo.md) |  | 
**analysis_id** | **int** |  | 
**analysis_scope** | **str** |  | 
**architecture** | **str** |  | 
**binary_dynamic** | **bool** |  | 
**binary_format** | **str** |  | 
**binary_name** | **str** |  | 
**binary_size** | **int** |  | 
**binary_type** | **str** |  | 
**creation** | **str** |  | 
**debug** | **bool** |  | 
**model_name** | **str** |  | 
**sbom** | **Dict[str, object]** |  | [optional] 
**sha_256_hash** | **str** |  | 

## Example

```python
from revengai.models.analysis_detail_response import AnalysisDetailResponse

# TODO update the JSON string below
json = "{}"
# create an instance of AnalysisDetailResponse from a JSON string
analysis_detail_response_instance = AnalysisDetailResponse.from_json(json)
# print the JSON string representation of the object
print(AnalysisDetailResponse.to_json())

# convert the object into a dict
analysis_detail_response_dict = analysis_detail_response_instance.to_dict()
# create an instance of AnalysisDetailResponse from a dict
analysis_detail_response_from_dict = AnalysisDetailResponse.from_dict(analysis_detail_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



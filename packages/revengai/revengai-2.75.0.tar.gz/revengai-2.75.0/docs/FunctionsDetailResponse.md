# FunctionsDetailResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**function_id** | **int** | Function id | 
**function_name** | **str** |  | 
**function_name_mangled** | **str** |  | 
**function_vaddr** | **int** |  | 
**function_size** | **int** |  | 
**analysis_id** | **int** |  | 
**binary_id** | **int** |  | 
**binary_name** | **str** |  | 
**sha_256_hash** | **str** |  | 
**debug_hash** | **str** |  | 
**debug** | **bool** |  | 
**embedding_3d** | **List[float]** |  | [optional] 
**embedding_1d** | **List[float]** |  | [optional] 

## Example

```python
from revengai.models.functions_detail_response import FunctionsDetailResponse

# TODO update the JSON string below
json = "{}"
# create an instance of FunctionsDetailResponse from a JSON string
functions_detail_response_instance = FunctionsDetailResponse.from_json(json)
# print the JSON string representation of the object
print(FunctionsDetailResponse.to_json())

# convert the object into a dict
functions_detail_response_dict = functions_detail_response_instance.to_dict()
# create an instance of FunctionsDetailResponse from a dict
functions_detail_response_from_dict = FunctionsDetailResponse.from_dict(functions_detail_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



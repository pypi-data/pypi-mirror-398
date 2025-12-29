# FunctionSearchResult


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**function_id** | **int** | The function ID | 
**function_name** | **str** | The name of the function | 
**binary_name** | **str** | The name of the binary the function belongs to | 
**created_at** | **datetime** | The creation date of the function | 
**model_id** | **int** | The model ID used to analyze the binary the function belongs to | 
**model_name** | **str** | The name of the model used to analyze the binary the function belongs to | 
**owned_by** | **str** | The owner of the binary the function belongs to | 

## Example

```python
from revengai.models.function_search_result import FunctionSearchResult

# TODO update the JSON string below
json = "{}"
# create an instance of FunctionSearchResult from a JSON string
function_search_result_instance = FunctionSearchResult.from_json(json)
# print the JSON string representation of the object
print(FunctionSearchResult.to_json())

# convert the object into a dict
function_search_result_dict = function_search_result_instance.to_dict()
# create an instance of FunctionSearchResult from a dict
function_search_result_from_dict = FunctionSearchResult.from_dict(function_search_result_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



# MatchedFunction


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**function_id** | **int** | Unique identifier of the matched function | 
**binary_id** | **int** |  | 
**function_name** | **str** |  | 
**function_vaddr** | **int** |  | 
**mangled_name** | **str** |  | 
**debug** | **bool** |  | 
**binary_name** | **str** |  | 
**sha_256_hash** | **str** |  | 
**analysis_id** | **int** |  | 
**similarity** | **float** |  | [optional] 
**confidence** | **float** |  | [optional] 

## Example

```python
from revengai.models.matched_function import MatchedFunction

# TODO update the JSON string below
json = "{}"
# create an instance of MatchedFunction from a JSON string
matched_function_instance = MatchedFunction.from_json(json)
# print the JSON string representation of the object
print(MatchedFunction.to_json())

# convert the object into a dict
matched_function_dict = matched_function_instance.to_dict()
# create an instance of MatchedFunction from a dict
matched_function_from_dict = MatchedFunction.from_dict(matched_function_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



# FunctionMatch


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**function_id** | **int** | Unique identifier of the function | 
**matched_functions** | [**List[MatchedFunction]**](MatchedFunction.md) |  | 
**confidences** | [**List[NameConfidence]**](NameConfidence.md) |  | [optional] 

## Example

```python
from revengai.models.function_match import FunctionMatch

# TODO update the JSON string below
json = "{}"
# create an instance of FunctionMatch from a JSON string
function_match_instance = FunctionMatch.from_json(json)
# print the JSON string representation of the object
print(FunctionMatch.to_json())

# convert the object into a dict
function_match_dict = function_match_instance.to_dict()
# create an instance of FunctionMatch from a dict
function_match_from_dict = FunctionMatch.from_dict(function_match_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



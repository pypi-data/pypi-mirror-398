# MatchedFunctionSuggestion


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**function_id** | **int** | Unique identifier of the matched function | 
**function_vaddr** | **int** | Virtual address of the matched function | 
**suggested_name** | **str** |  | [optional] 
**suggested_demangled_name** | **str** | De-mangled name of the function group that contains the matched functions | 

## Example

```python
from revengai.models.matched_function_suggestion import MatchedFunctionSuggestion

# TODO update the JSON string below
json = "{}"
# create an instance of MatchedFunctionSuggestion from a JSON string
matched_function_suggestion_instance = MatchedFunctionSuggestion.from_json(json)
# print the JSON string representation of the object
print(MatchedFunctionSuggestion.to_json())

# convert the object into a dict
matched_function_suggestion_dict = matched_function_suggestion_instance.to_dict()
# create an instance of MatchedFunctionSuggestion from a dict
matched_function_suggestion_from_dict = MatchedFunctionSuggestion.from_dict(matched_function_suggestion_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



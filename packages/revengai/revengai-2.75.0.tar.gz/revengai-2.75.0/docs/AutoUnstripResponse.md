# AutoUnstripResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**progress** | **int** | Progress of the auto-unstrip operation, represented as a percentage | [optional] [default to 0]
**status** | **str** |  | [optional] 
**total_time** | **int** |  | [optional] 
**matches** | [**List[MatchedFunctionSuggestion]**](MatchedFunctionSuggestion.md) |  | [optional] 
**applied** | **bool** |  | [optional] 
**error_message** | **str** |  | [optional] 

## Example

```python
from revengai.models.auto_unstrip_response import AutoUnstripResponse

# TODO update the JSON string below
json = "{}"
# create an instance of AutoUnstripResponse from a JSON string
auto_unstrip_response_instance = AutoUnstripResponse.from_json(json)
# print the JSON string representation of the object
print(AutoUnstripResponse.to_json())

# convert the object into a dict
auto_unstrip_response_dict = auto_unstrip_response_instance.to_dict()
# create an instance of AutoUnstripResponse from a dict
auto_unstrip_response_from_dict = AutoUnstripResponse.from_dict(auto_unstrip_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



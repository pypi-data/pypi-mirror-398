# FunctionMapping


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**function_map** | **Dict[str, int]** | Mapping of remote function ids to local function addresses | 
**inverse_function_map** | **Dict[str, int]** | Mapping of local function addresses to remote function ids | 
**name_map** | **Dict[str, str]** | Mapping of local function addresses to mangled names | 

## Example

```python
from revengai.models.function_mapping import FunctionMapping

# TODO update the JSON string below
json = "{}"
# create an instance of FunctionMapping from a JSON string
function_mapping_instance = FunctionMapping.from_json(json)
# print the JSON string representation of the object
print(FunctionMapping.to_json())

# convert the object into a dict
function_mapping_dict = function_mapping_instance.to_dict()
# create an instance of FunctionMapping from a dict
function_mapping_from_dict = FunctionMapping.from_dict(function_mapping_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



# GenerateFunctionDataTypes


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**queued** | **bool** | [DEPRECATED] This value has been replaced with the &#x60;data_types_list&#x60; field | 
**reference** | **str** | [DEPRECATED] This value has been replaced with the &#x60;data_types_list&#x60; field | 
**data_types_list** | [**GenerationStatusList**](GenerationStatusList.md) | List of function data types information that are either already generated, or now queued for generation | 

## Example

```python
from revengai.models.generate_function_data_types import GenerateFunctionDataTypes

# TODO update the JSON string below
json = "{}"
# create an instance of GenerateFunctionDataTypes from a JSON string
generate_function_data_types_instance = GenerateFunctionDataTypes.from_json(json)
# print the JSON string representation of the object
print(GenerateFunctionDataTypes.to_json())

# convert the object into a dict
generate_function_data_types_dict = generate_function_data_types_instance.to_dict()
# create an instance of GenerateFunctionDataTypes from a dict
generate_function_data_types_from_dict = GenerateFunctionDataTypes.from_dict(generate_function_data_types_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



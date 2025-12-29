# FunctionMappingFull


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**inverse_string_map** | [**Dict[str, InverseStringMapItem]**](InverseStringMapItem.md) |  | 
**inverse_function_map** | [**Dict[str, InverseFunctionMapItem]**](InverseFunctionMapItem.md) |  | 
**unmatched_functions** | [**Dict[str, InverseValue]**](InverseValue.md) |  | 
**unmatched_custom_types** | [**Dict[str, InverseValue]**](InverseValue.md) |  | 
**unmatched_strings** | [**Dict[str, InverseValue]**](InverseValue.md) |  | 
**unmatched_vars** | [**Dict[str, InverseValue]**](InverseValue.md) |  | 
**unmatched_go_to_labels** | [**Dict[str, InverseValue]**](InverseValue.md) |  | 
**unmatched_custom_function_pointers** | [**Dict[str, InverseValue]**](InverseValue.md) |  | 
**unmatched_variadic_lists** | [**Dict[str, InverseValue]**](InverseValue.md) |  | 
**unmatched_enums** | [**Dict[str, InverseValue]**](InverseValue.md) |  | 
**unmatched_global_vars** | [**Dict[str, InverseValue]**](InverseValue.md) |  | 
**fields** | **Dict[str, Dict[str, InverseValue]]** |  | 
**unmatched_external_vars** | [**Dict[str, InverseValue]**](InverseValue.md) | No longer provided. | [optional] 

## Example

```python
from revengai.models.function_mapping_full import FunctionMappingFull

# TODO update the JSON string below
json = "{}"
# create an instance of FunctionMappingFull from a JSON string
function_mapping_full_instance = FunctionMappingFull.from_json(json)
# print the JSON string representation of the object
print(FunctionMappingFull.to_json())

# convert the object into a dict
function_mapping_full_dict = function_mapping_full_instance.to_dict()
# create an instance of FunctionMappingFull from a dict
function_mapping_full_from_dict = FunctionMappingFull.from_dict(function_mapping_full_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



# GenerationStatusList


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**total_count** | **int** | Total number of functions in analysis | [optional] [default to 0]
**total_data_types_count** | **int** | Total number of functions with data types | [optional] [default to 0]
**items** | [**List[FunctionDataTypesStatus]**](FunctionDataTypesStatus.md) | List of function data types information | 

## Example

```python
from revengai.models.generation_status_list import GenerationStatusList

# TODO update the JSON string below
json = "{}"
# create an instance of GenerationStatusList from a JSON string
generation_status_list_instance = GenerationStatusList.from_json(json)
# print the JSON string representation of the object
print(GenerationStatusList.to_json())

# convert the object into a dict
generation_status_list_dict = generation_status_list_instance.to_dict()
# create an instance of GenerationStatusList from a dict
generation_status_list_from_dict = GenerationStatusList.from_dict(generation_status_list_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



# Basic


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**binary_name** | **str** | The name of the binary uploaded | 
**binary_size** | **int** | The size of the binary uploaded (bytes) | 
**creation** | **datetime** | When the binary was uploaded | 
**sha_256_hash** | **str** | The hash of the binary uploaded | 
**model_name** | **str** | The model name used for analysis | 
**model_id** | **int** | The model ID used for analysis | 
**owner_username** | **str** | The name of the owner of the binary | 
**analysis_scope** | **str** | The scope of the analysis | 
**is_owner** | **bool** | Whether the current user is the owner | 
**debug** | **bool** | Whether the current analysis was analysed with debug symbols | 
**function_count** | **int** | The number of functions in the binary | 
**is_advanced** | **bool** | Whether the analysis was advanced | 
**base_address** | **int** |  | 

## Example

```python
from revengai.models.basic import Basic

# TODO update the JSON string below
json = "{}"
# create an instance of Basic from a JSON string
basic_instance = Basic.from_json(json)
# print the JSON string representation of the object
print(Basic.to_json())

# convert the object into a dict
basic_dict = basic_instance.to_dict()
# create an instance of Basic from a dict
basic_from_dict = Basic.from_dict(basic_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



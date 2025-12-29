# InverseFunctionMapItem


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | 
**addr** | [**Addr**](Addr.md) |  | 
**is_external** | **bool** |  | [optional] [default to False]

## Example

```python
from revengai.models.inverse_function_map_item import InverseFunctionMapItem

# TODO update the JSON string below
json = "{}"
# create an instance of InverseFunctionMapItem from a JSON string
inverse_function_map_item_instance = InverseFunctionMapItem.from_json(json)
# print the JSON string representation of the object
print(InverseFunctionMapItem.to_json())

# convert the object into a dict
inverse_function_map_item_dict = inverse_function_map_item_instance.to_dict()
# create an instance of InverseFunctionMapItem from a dict
inverse_function_map_item_from_dict = InverseFunctionMapItem.from_dict(inverse_function_map_item_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



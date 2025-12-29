# InverseStringMapItem


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**string** | **str** |  | 
**addr** | **int** |  | 

## Example

```python
from revengai.models.inverse_string_map_item import InverseStringMapItem

# TODO update the JSON string below
json = "{}"
# create an instance of InverseStringMapItem from a JSON string
inverse_string_map_item_instance = InverseStringMapItem.from_json(json)
# print the JSON string representation of the object
print(InverseStringMapItem.to_json())

# convert the object into a dict
inverse_string_map_item_dict = inverse_string_map_item_instance.to_dict()
# create an instance of InverseStringMapItem from a dict
inverse_string_map_item_from_dict = InverseStringMapItem.from_dict(inverse_string_map_item_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



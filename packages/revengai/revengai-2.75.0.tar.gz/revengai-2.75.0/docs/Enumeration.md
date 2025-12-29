# Enumeration


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**last_change** | **str** |  | [optional] 
**name** | **str** | Name of the enumeration | 
**members** | **Dict[str, int]** | Dictionary of enumeration members and their values | 
**artifact_type** | **str** | Type of artifact that the enumeration is associated with | [optional] 

## Example

```python
from revengai.models.enumeration import Enumeration

# TODO update the JSON string below
json = "{}"
# create an instance of Enumeration from a JSON string
enumeration_instance = Enumeration.from_json(json)
# print the JSON string representation of the object
print(Enumeration.to_json())

# convert the object into a dict
enumeration_dict = enumeration_instance.to_dict()
# create an instance of Enumeration from a dict
enumeration_from_dict = Enumeration.from_dict(enumeration_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



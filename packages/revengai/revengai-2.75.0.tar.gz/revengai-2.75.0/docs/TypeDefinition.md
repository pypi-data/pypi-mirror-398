# TypeDefinition


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**last_change** | **str** |  | [optional] 
**name** | **str** | Name of the type definition | 
**type** | **str** | Underlying type of the type definition | 
**artifact_type** | **str** | Type of artifact the type definition is associated with | [optional] 

## Example

```python
from revengai.models.type_definition import TypeDefinition

# TODO update the JSON string below
json = "{}"
# create an instance of TypeDefinition from a JSON string
type_definition_instance = TypeDefinition.from_json(json)
# print the JSON string representation of the object
print(TypeDefinition.to_json())

# convert the object into a dict
type_definition_dict = type_definition_instance.to_dict()
# create an instance of TypeDefinition from a dict
type_definition_from_dict = TypeDefinition.from_dict(type_definition_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



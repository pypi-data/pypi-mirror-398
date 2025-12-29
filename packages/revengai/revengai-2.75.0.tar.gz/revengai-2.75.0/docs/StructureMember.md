# StructureMember


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**last_change** | **str** |  | [optional] 
**name** | **str** | Name of the structure member | 
**offset** | **int** | Offset of the member within the structure | 
**type** | **str** | Data type of the structure member | 
**size** | **int** | Size of the structure member in bytes | 

## Example

```python
from revengai.models.structure_member import StructureMember

# TODO update the JSON string below
json = "{}"
# create an instance of StructureMember from a JSON string
structure_member_instance = StructureMember.from_json(json)
# print the JSON string representation of the object
print(StructureMember.to_json())

# convert the object into a dict
structure_member_dict = structure_member_instance.to_dict()
# create an instance of StructureMember from a dict
structure_member_from_dict = StructureMember.from_dict(structure_member_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



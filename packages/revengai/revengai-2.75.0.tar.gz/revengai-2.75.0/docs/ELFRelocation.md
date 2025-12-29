# ELFRelocation


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**address** | **int** |  | 
**type** | **str** |  | 
**size** | **int** |  | 
**addend** | **int** |  | 
**symbol_name** | **str** |  | 
**is_dynamic** | **bool** |  | 
**is_pltgot** | **bool** |  | 

## Example

```python
from revengai.models.elf_relocation import ELFRelocation

# TODO update the JSON string below
json = "{}"
# create an instance of ELFRelocation from a JSON string
elf_relocation_instance = ELFRelocation.from_json(json)
# print the JSON string representation of the object
print(ELFRelocation.to_json())

# convert the object into a dict
elf_relocation_dict = elf_relocation_instance.to_dict()
# create an instance of ELFRelocation from a dict
elf_relocation_from_dict = ELFRelocation.from_dict(elf_relocation_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



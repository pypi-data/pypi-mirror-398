# ElfDynamicEntry


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**tag** | **str** |  | 
**value** | **int** |  | 

## Example

```python
from revengai.models.elf_dynamic_entry import ElfDynamicEntry

# TODO update the JSON string below
json = "{}"
# create an instance of ElfDynamicEntry from a JSON string
elf_dynamic_entry_instance = ElfDynamicEntry.from_json(json)
# print the JSON string representation of the object
print(ElfDynamicEntry.to_json())

# convert the object into a dict
elf_dynamic_entry_dict = elf_dynamic_entry_instance.to_dict()
# create an instance of ElfDynamicEntry from a dict
elf_dynamic_entry_from_dict = ElfDynamicEntry.from_dict(elf_dynamic_entry_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



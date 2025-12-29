# ELFSection


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**name** | **str** |  | 
**type** | **str** |  | 
**virtual_address** | **int** |  | 
**virtual_size** | **int** |  | 
**raw_size** | **int** |  | 
**file_offset** | **int** |  | 
**flags** | **str** |  | 
**flags_raw** | **int** |  | 
**entropy** | **float** |  | 
**alignment** | **int** |  | 

## Example

```python
from revengai.models.elf_section import ELFSection

# TODO update the JSON string below
json = "{}"
# create an instance of ELFSection from a JSON string
elf_section_instance = ELFSection.from_json(json)
# print the JSON string representation of the object
print(ELFSection.to_json())

# convert the object into a dict
elf_section_dict = elf_section_instance.to_dict()
# create an instance of ELFSection from a dict
elf_section_from_dict = ELFSection.from_dict(elf_section_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



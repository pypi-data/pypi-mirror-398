# ELFSegment


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**type** | **str** |  | 
**virtual_address** | **int** |  | 
**virtual_size** | **int** |  | 
**physical_address** | **int** |  | 
**physical_size** | **int** |  | 
**file_offset** | **int** |  | 
**flags** | **str** |  | 
**flags_raw** | **int** |  | 
**alignment** | **int** |  | 

## Example

```python
from revengai.models.elf_segment import ELFSegment

# TODO update the JSON string below
json = "{}"
# create an instance of ELFSegment from a JSON string
elf_segment_instance = ELFSegment.from_json(json)
# print the JSON string representation of the object
print(ELFSegment.to_json())

# convert the object into a dict
elf_segment_dict = elf_segment_instance.to_dict()
# create an instance of ELFSegment from a dict
elf_segment_from_dict = ELFSegment.from_dict(elf_segment_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



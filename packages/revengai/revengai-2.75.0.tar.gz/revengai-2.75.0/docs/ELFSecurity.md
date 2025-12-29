# ELFSecurity


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**pie** | **bool** |  | 
**stripped** | **bool** |  | 
**canary** | **bool** |  | 
**nx** | **bool** |  | 
**relo** | **bool** |  | 

## Example

```python
from revengai.models.elf_security import ELFSecurity

# TODO update the JSON string below
json = "{}"
# create an instance of ELFSecurity from a JSON string
elf_security_instance = ELFSecurity.from_json(json)
# print the JSON string representation of the object
print(ELFSecurity.to_json())

# convert the object into a dict
elf_security_dict = elf_security_instance.to_dict()
# create an instance of ELFSecurity from a dict
elf_security_from_dict = ELFSecurity.from_dict(elf_security_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



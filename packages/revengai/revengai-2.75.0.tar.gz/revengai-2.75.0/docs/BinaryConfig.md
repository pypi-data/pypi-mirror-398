# BinaryConfig


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**isa** | [**ISA**](ISA.md) |  | [optional] 
**platform** | [**Platform**](Platform.md) |  | [optional] 
**file_format** | [**FileFormat**](FileFormat.md) |  | [optional] 

## Example

```python
from revengai.models.binary_config import BinaryConfig

# TODO update the JSON string below
json = "{}"
# create an instance of BinaryConfig from a JSON string
binary_config_instance = BinaryConfig.from_json(json)
# print the JSON string representation of the object
print(BinaryConfig.to_json())

# convert the object into a dict
binary_config_dict = binary_config_instance.to_dict()
# create an instance of BinaryConfig from a dict
binary_config_from_dict = BinaryConfig.from_dict(binary_config_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



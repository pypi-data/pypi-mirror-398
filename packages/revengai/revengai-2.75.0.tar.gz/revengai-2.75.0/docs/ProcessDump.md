# ProcessDump


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**base_address** | **int** |  | 
**actual_filename** | **str** |  | 
**filename_friendly** | **str** |  | 
**extended_metadata** | [**ProcessDumpMetadata**](ProcessDumpMetadata.md) |  | 

## Example

```python
from revengai.models.process_dump import ProcessDump

# TODO update the JSON string below
json = "{}"
# create an instance of ProcessDump from a JSON string
process_dump_instance = ProcessDump.from_json(json)
# print the JSON string representation of the object
print(ProcessDump.to_json())

# convert the object into a dict
process_dump_dict = process_dump_instance.to_dict()
# create an instance of ProcessDump from a dict
process_dump_from_dict = ProcessDump.from_dict(process_dump_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



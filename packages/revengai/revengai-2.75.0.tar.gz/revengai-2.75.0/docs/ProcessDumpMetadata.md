# ProcessDumpMetadata


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**sha256** | **str** |  | 
**type** | **str** |  | 
**size** | **int** |  | 

## Example

```python
from revengai.models.process_dump_metadata import ProcessDumpMetadata

# TODO update the JSON string below
json = "{}"
# create an instance of ProcessDumpMetadata from a JSON string
process_dump_metadata_instance = ProcessDumpMetadata.from_json(json)
# print the JSON string representation of the object
print(ProcessDumpMetadata.to_json())

# convert the object into a dict
process_dump_metadata_dict = process_dump_metadata_instance.to_dict()
# create an instance of ProcessDumpMetadata from a dict
process_dump_metadata_from_dict = ProcessDumpMetadata.from_dict(process_dump_metadata_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



# ProcessDumpsData


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**count** | **int** |  | 
**dumps** | [**List[ProcessDump]**](ProcessDump.md) |  | 

## Example

```python
from revengai.models.process_dumps_data import ProcessDumpsData

# TODO update the JSON string below
json = "{}"
# create an instance of ProcessDumpsData from a JSON string
process_dumps_data_instance = ProcessDumpsData.from_json(json)
# print the JSON string representation of the object
print(ProcessDumpsData.to_json())

# convert the object into a dict
process_dumps_data_dict = process_dumps_data_instance.to_dict()
# create an instance of ProcessDumpsData from a dict
process_dumps_data_from_dict = ProcessDumpsData.from_dict(process_dumps_data_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



# ProcessDumps


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**success** | **bool** |  | 
**data** | [**ProcessDumpsData**](ProcessDumpsData.md) |  | 

## Example

```python
from revengai.models.process_dumps import ProcessDumps

# TODO update the JSON string below
json = "{}"
# create an instance of ProcessDumps from a JSON string
process_dumps_instance = ProcessDumps.from_json(json)
# print the JSON string representation of the object
print(ProcessDumps.to_json())

# convert the object into a dict
process_dumps_dict = process_dumps_instance.to_dict()
# create an instance of ProcessDumps from a dict
process_dumps_from_dict = ProcessDumps.from_dict(process_dumps_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



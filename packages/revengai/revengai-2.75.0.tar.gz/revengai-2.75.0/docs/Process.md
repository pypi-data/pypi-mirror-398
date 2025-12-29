# Process


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**pid** | **int** |  | 
**procname** | **str** |  | 
**executable_name** | **str** |  | 
**args** | **List[str]** |  | 
**ts_from** | **float** |  | 
**ts_to** | **float** |  | 
**children** | **List[object]** |  | 

## Example

```python
from revengai.models.process import Process

# TODO update the JSON string below
json = "{}"
# create an instance of Process from a JSON string
process_instance = Process.from_json(json)
# print the JSON string representation of the object
print(Process.to_json())

# convert the object into a dict
process_dict = process_instance.to_dict()
# create an instance of Process from a dict
process_from_dict = Process.from_dict(process_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



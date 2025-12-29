# BinarySearchResult


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**binary_id** | **int** | The binary ID | 
**binary_name** | **str** | The name of the binary | 
**analysis_id** | **int** | The analysis ID | 
**sha_256_hash** | **str** | The SHA-256 hash of the binary | 
**tags** | **List[str]** |  | 
**created_at** | **datetime** | The creation date of the binary | 
**model_id** | **int** | The model ID of the binary | 
**model_name** | **str** | The name of the model | 
**owned_by** | **str** | The owner of the binary | 

## Example

```python
from revengai.models.binary_search_result import BinarySearchResult

# TODO update the JSON string below
json = "{}"
# create an instance of BinarySearchResult from a JSON string
binary_search_result_instance = BinarySearchResult.from_json(json)
# print the JSON string representation of the object
print(BinarySearchResult.to_json())

# convert the object into a dict
binary_search_result_dict = binary_search_result_instance.to_dict()
# create an instance of BinarySearchResult from a dict
binary_search_result_from_dict = BinarySearchResult.from_dict(binary_search_result_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



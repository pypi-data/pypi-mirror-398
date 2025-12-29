# BinarySearchResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**results** | [**List[BinarySearchResult]**](BinarySearchResult.md) | The results of the search | 

## Example

```python
from revengai.models.binary_search_response import BinarySearchResponse

# TODO update the JSON string below
json = "{}"
# create an instance of BinarySearchResponse from a JSON string
binary_search_response_instance = BinarySearchResponse.from_json(json)
# print the JSON string representation of the object
print(BinarySearchResponse.to_json())

# convert the object into a dict
binary_search_response_dict = binary_search_response_instance.to_dict()
# create an instance of BinarySearchResponse from a dict
binary_search_response_from_dict = BinarySearchResponse.from_dict(binary_search_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



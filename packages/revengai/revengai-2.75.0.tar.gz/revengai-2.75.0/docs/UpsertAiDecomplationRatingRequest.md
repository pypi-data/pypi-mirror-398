# UpsertAiDecomplationRatingRequest


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**rating** | [**AiDecompilationRating**](AiDecompilationRating.md) | The rating for the AI decompilation response | 
**reason** | **str** |  | 

## Example

```python
from revengai.models.upsert_ai_decomplation_rating_request import UpsertAiDecomplationRatingRequest

# TODO update the JSON string below
json = "{}"
# create an instance of UpsertAiDecomplationRatingRequest from a JSON string
upsert_ai_decomplation_rating_request_instance = UpsertAiDecomplationRatingRequest.from_json(json)
# print the JSON string representation of the object
print(UpsertAiDecomplationRatingRequest.to_json())

# convert the object into a dict
upsert_ai_decomplation_rating_request_dict = upsert_ai_decomplation_rating_request_instance.to_dict()
# create an instance of UpsertAiDecomplationRatingRequest from a dict
upsert_ai_decomplation_rating_request_from_dict = UpsertAiDecomplationRatingRequest.from_dict(upsert_ai_decomplation_rating_request_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



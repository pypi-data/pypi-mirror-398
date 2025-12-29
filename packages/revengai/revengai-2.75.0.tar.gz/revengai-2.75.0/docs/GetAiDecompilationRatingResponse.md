# GetAiDecompilationRatingResponse


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**rating** | [**AiDecompilationRating**](AiDecompilationRating.md) | The rating the user has given to the AI decompilation response | 
**reason** | **str** |  | 

## Example

```python
from revengai.models.get_ai_decompilation_rating_response import GetAiDecompilationRatingResponse

# TODO update the JSON string below
json = "{}"
# create an instance of GetAiDecompilationRatingResponse from a JSON string
get_ai_decompilation_rating_response_instance = GetAiDecompilationRatingResponse.from_json(json)
# print the JSON string representation of the object
print(GetAiDecompilationRatingResponse.to_json())

# convert the object into a dict
get_ai_decompilation_rating_response_dict = get_ai_decompilation_rating_response_instance.to_dict()
# create an instance of GetAiDecompilationRatingResponse from a dict
get_ai_decompilation_rating_response_from_dict = GetAiDecompilationRatingResponse.from_dict(get_ai_decompilation_rating_response_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



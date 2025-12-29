# StringFunctions

This is a string with the functions where the string is used.  A function string is a string literal referenced within a function. When analyzing stripped or obfuscated binaries, function strings can help identify the function’s purpose.

## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**value** | **str** | The value of the string literal | 
**functions** | [**List[AppApiRestV2FunctionsResponsesFunction]**](AppApiRestV2FunctionsResponsesFunction.md) | The function ids the string literal was found within | 

## Example

```python
from revengai.models.string_functions import StringFunctions

# TODO update the JSON string below
json = "{}"
# create an instance of StringFunctions from a JSON string
string_functions_instance = StringFunctions.from_json(json)
# print the JSON string representation of the object
print(StringFunctions.to_json())

# convert the object into a dict
string_functions_dict = string_functions_instance.to_dict()
# create an instance of StringFunctions from a dict
string_functions_from_dict = StringFunctions.from_dict(string_functions_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)



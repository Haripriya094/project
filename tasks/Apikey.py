import tiktoken

def count_tokens(text, model="gpt-4o-mini"):
    enc = tiktoken.encoding_for_model(model) # call the model name and store the tokenizer ID in the variable
    tokens = enc.encode(text)  # convert the string text to token integer IDs


    return len(tokens)

text = "Hello! This is a token counting example."
print("Token count:", count_tokens(text))

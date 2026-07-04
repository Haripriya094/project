from scripts.prompts import  Prompts

from slm_model import run_model

import os


def read_code_file(filename: str) -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, filename)

    print(f"Looking for file at: {file_path}")
    print(f"File exists: {os.path.exists(file_path)}")

    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]

    for encoding in encodings:
        try:
            with open(file_path, "r", encoding=encoding) as f:
                content = f.read()
                print(f"Successfully read with encoding: {encoding}")
                return content
        except UnicodeDecodeError:
            continue

    raise UnicodeDecodeError(
        "utf-8", b"", 0, 1, "Failed to decode file"
    )


def save_output(output: str, filename: str = "technical_specification_output.txt"):
    """Save the generated output to a text file"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(base_dir, filename)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"\nOutput saved to: {output_path}")


# Read Python source code
print("Starting script...")
code = read_code_file("test_python_file.py")

# Get the prompt rules from FunctionalSpecification
final_prompt = Prompts.get_functional_specification_prompt(code)

# Send to model
output = run_model(final_prompt)

print("\n" + "=" * 50)
print("Sending to model for analysis...")
print("=" * 50)



# Save output to file
save_output(output)

print("\n" + "=" * 50)
print("Process completed successfully!")
print("=" * 50)
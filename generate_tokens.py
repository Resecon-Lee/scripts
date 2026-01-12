# Script to generate a 300,000 token text file

# Define the sentence to repeat (10 tokens for simplicity)
sentence = "This is a sample sentence for token counting purposes.\n"
tokens_per_sentence = 10

# Calculate how many repetitions to reach 300,000 tokens
# Reserve 2 lines at the end: one for the message, one for final line
num_sentences = (300_000 // tokens_per_sentence) - 2

# File output path
output_file = "300k_tokens.txt"

with open(output_file, "w") as f:
    for _ in range(num_sentences):
        f.write(sentence)
    # Second to last line: custom message
    f.write("Successfully generated 300k tokens\n")
    # Last line: regular sentence to maintain token count
    f.write(sentence)

print(f"Generated '{output_file}' with approximately 300,000 tokens.")

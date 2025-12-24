from webnexa import WebNexa

# Option 4: Summarize the website
chat4 = WebNexa(hf_token="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")
chat4.load_website("https://ketabrah.com/")
print("Summary (5 lines):")
print(chat4.summarize(max_lines=5))

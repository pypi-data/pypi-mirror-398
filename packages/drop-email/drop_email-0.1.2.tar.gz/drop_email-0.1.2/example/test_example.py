"""
Test example for drop_email package
Usage: import drop_email as de
"""

import drop_email as de
import pandas as pd


# Example 0: Send a Experiment Result DataFrame
print("Example 0: Sending a Experiment Result DataFrame")
df = pd.DataFrame({
    'Task': [
        'Image Classification',
        'Text Classification',
        'Object Detection',
        'Machine Translation',
        'Question Answering',
        'Sentiment Analysis',
        'Named Entity Recognition',
        'Image Generation',
    ],
    'Model': [
        'ResNet-50',
        'BERT-Large',
        'YOLOv8',
        'mT5',
        'GPT-3.5',
        'RoBERTa',
        'BERT-Base',
        'Stable Diffusion',
    ],
    'Score': [0.945, 0.923, 0.891, 0.876, 0.862, 0.938, 0.915, 0.847]
})

de.send(df, subject="Experiment Result")


# Example 1: Send a pandas DataFrame
print("Example 1: Sending a pandas DataFrame")
df = pd.DataFrame({
    'Name': ['Alice', 'Bob', 'Charlie', 'Diana'],
    'Age': [25, 30, 35, 28],
    'City': ['New York', 'London', 'Tokyo', 'Paris'],
    'Salary': [75000, 80000, 90000, 72000]
})

# Uncomment to send email
# de.send(df, subject="Employee Data Report")

# Example 2: Send a dictionary
print("\nExample 2: Sending a dictionary")
data_dict = {
    'Total Users': 1500,
    'Active Users': 1200,
    'Revenue': '$125,000',
    'Growth Rate': '15%'
}

# Uncomment to send email
# de.send(data_dict, subject="Monthly Statistics")

# Example 3: Send a list of DataFrames
print("\nExample 3: Sending a list of DataFrames")
df1 = pd.DataFrame({
    'Product': ['A', 'B', 'C'],
    'Sales': [100, 200, 150]
})

df2 = pd.DataFrame({
    'Region': ['North', 'South', 'East', 'West'],
    'Revenue': [50000, 60000, 55000, 58000]
})

data_list = [df1, df2]

# Uncomment to send email
# de.send(data_list, subject="Sales Report")

# Example 4: Send with custom receivers
print("\nExample 4: Sending with custom receivers")
# Uncomment to send email
# de.send(df, subject="Custom Report", receivers=["custom@example.com"])

print("\nAll examples completed! Uncomment the de.send() calls to actually send emails.")
print("Make sure to configure your email settings in the config file first.")


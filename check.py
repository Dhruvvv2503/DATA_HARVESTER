import pandas as pd
from io import StringIO

# Sample CSV data
csv_data = """company,website,email
Alpha Tech,alpha-tech.com,contact@alpha-tech.com
Beta Solutions,betasolutions.com,
Gamma Co.,gamma.com,support@gamma.com
Delta Innovations,delta-tech.com,info@delta-tech.com
Epsilon Group,,contact@epsilon.com
"""

# Read the CSV data from the string (simulating file read)
data = pd.read_csv(StringIO(csv_data))
print(data)

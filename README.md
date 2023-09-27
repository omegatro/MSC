# MSC
MSC project

# Architecture notes

## Modules
1. Input parsing
   - Managing different file types
   - Dealing with specific file structure issues
   - Managing different ways to access the files
   - Providing command-line interface 
2. Preprocessing
   - Lowercasing
   - Stemming
   - Tokenization
   - Converting to vector representation
   - Feature engineering
3. Modeling
   - Assigning multiple cluster labels per document
   - Providing justification for the assignment
4. Testing & validation
   - Testing if clustering is reasonable
   - Testing for complience with human-generated results
5. Validation
   - Checking using datasets beyond testing
6. Visualization
   - Responsive Cluster visualization intreface (django)

# Implementation notes
  - APIs used
    - pyzotero
    - Entrez
    - sciencedirect

# Note to self
 - Hierarchical Topic modeling -> Hierarchical topics as nodes -> Disambiguation -> Document assignment to nodes based on Model-assigned topic sequence
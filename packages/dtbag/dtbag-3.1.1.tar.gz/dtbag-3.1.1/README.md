# dtbag: Data Tools for Business, Analytics & General Tasks

**Streamline your data preparation for Machine Learning and Business Analytics.**

`dtbag` is a Python library that focuses on creating solutions to common problems, and what distinguishes it from others is that it adopts a "solution in one line" approach, meaning it combines all the necessary steps to work internally and returns the result in a single output.
For instance "CatUnifier" function solves a common categorical data problem, inconsistent categorical data due to incorrect entries, spelling mistakes, different write/map data, etc... 
data might have only four real categories but the output can show two times or even many times that number, and this will affect any charts/ machine learning models etc.. and return wrong results.

**Clean inconsistent data entries**

*   **data =**  ["Pencil", "Book", "Pencle", "Boook", "Bouk", "pencl", "pencyl", "Sook","Pencil"]
*   **CatLists_output =**  CatUnifier(data, threshold=0.6)
*   **Result:**  ['Pencil', 'Book']

*   **CatUnifier_output =**  CatUnifier(data, threshold=0.6)
*   **Result:**  ['Pencil','Book','Pencil','Book','Book','Pencil','Pencil','Book','Pencil']


## Key Features

*   **Smart Text Unification :**  Intelligently groups and standardizes similar text entries (like names, addresses, product titles) even with typos, different cases, or accents.
*   **Built for Real Data :**  Handles common data issues like inconsistent capitalization (`"New York"`, `"NEW YORK"`), diacritics (`"Café"`, `"Cafe"`), and minor spelling variations.
*   **Multilingual Support :**  Works seamlessly across languages commonly found in business data, including **Arabic, English, French, Spanish, German**, and more.
*   **Zero Dependencies :**  Uses only Python's robust standard library, ensuring lightweight and conflict-free installation.
*   **Preserves Original Data :**  Returns the most frequent *original* version in each group, maintaining data integrity.


## What's Inside:

*   **CatLists :** 
   Returns a list containing the corrected unique categories from the erroneous categories.
*   **CatUnifier :** 
   Returns the entire input list as a new list with fully corrected categories and in the same order as entered, so that it can be replaced directly.


## Quick Start

#### Installation
```bash
pip install dtbag
```


#### Basic Usage: Cleaning Text Data
```python
from dtbag import CatUnifier
from dtbag import CatLists

raw_customers = ["Café Marrakech", "CAFÉ MARRAKECH", 'Café Mrakech', 'Cafe Marakesh', 'Cafffé Marrakech', 'Cfé Markech', 'Sturbuks', 'Starbucks', "Starbucks", "starbucks", "Café Marrakech"]
dtbag.CatUnifier(raw_customers, threshold=0.7)
Output: ['Café Marrakech', 'Café Marrakech', 'Café Marrakech', 'Café Marrakech', 'Café Marrakech', 'Café Marrakech', 'Starbucks', 'Starbucks', 'Starbucks', 'Starbucks', 'Café Marrakech']

dtbag.CatLists(raw_customers, threshold=0.75)
Output: ['Café Marrakech', 'Starbucks']
```
```python
products = ["laptop-13inch", "Mouse Wireless", "Laptop 13 Inch", "Laptop 13\"", "mouse wirlss", "Mouse Wireless"]
dtbag.CatUnifier(products, threshold=0.6)
Output: ['Laptop 13"', 'Mouse Wireless', 'Laptop 13"', 'Laptop 13"', 'Mouse Wireless', 'Mouse Wireless']

dtbag.CatLists(products, threshold=0.6)
Output: ['Laptop 13"', 'Mouse Wireless']
```
```python
international = ["São Paulo", "Sao Paulo", "Saw Paullow", "München", "Muenchen", "Naïve", "Naive", "Nayve", "Naive"]
dtbag.CatUnifier(international, threshold=0.7)
Output: ['São Paulo', 'São Paulo', 'São Paulo', 'München', 'München', 'Naive', 'Naive', 'Naive', 'Naive']

dtbag.CatLists(international, threshold=0.7)
Output: ['São Paulo', 'München', 'Naive']
```


#### Tuning Precision
```python
strict_cleaning = unify_similar_items(data, threshold=0.9)  # High precision
lenient_cleaning = unify_similar_items(data, threshold=0.6) # More grouping
```
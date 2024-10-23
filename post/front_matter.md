---
lang: en 

title: Front Matter
author: Gilad Kutiel
date: 2024-09-30

description: This section explains how to write a new post in blgit. It provides step-by-step instructions on creating and formatting content for your blog.

favicon: ⚙️
image: front_matter.jpg
---

Each `.md` file should have a front matter section like so:

```
---
lang: en 

title: Front Matter
author: Gilad Kutiel
date: 2024-9-28

description: How to write Front Matter

favicon: ⚙️
image: front_matter.jpg
---
```

The content of the front matter is passed to the template engine as key-val attributes.

**Note:** The `index.md` file must have two additional attributes, namely **url** and **date format**. 
These attributes are important for the generation process.

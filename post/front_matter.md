---
lang: en 

title: Front Matter
author: Gilad Kutiel
date: 2024-9-30

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

The content of the front matter are passed to the template engine as key-val attributes.

Note that the attributes defined in the index.md files are passed to the template engine for each post. However, you can (and should) override them in individual posts as needed.
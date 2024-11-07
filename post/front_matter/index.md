---
author: Gilad Kutiel
date: 2024-09-30
description: This section explains how to write a new post in blgit. It provides step-by-step
  instructions on creating and formatting content for your blog.
draft: true
favicon: 🕮
image: img/front_matter.jpg
lang: en
title: Front Matter
---

Your `index_md` file should have a front matter section like so:

```
---
lang: en
url: https://blgit.org
date_format: '%d/%m/%Y'

title: blgit.org
description: Some description
image: /img/image.jpg
favicon: 🔨
---
```

Which will be passed to the template engine as key-val attributes.

Each of your post `.md` files should have a front matter section like this:

```
---
date: 2024-09-28

title: blgit.org
description: Some description
image: /img/image.jpg
favicon: 🔨
---
```

These are mandatory for the proper generation of the blog.
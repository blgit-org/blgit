---
lang: en 

title: Usage
author: Gilad Kutiel
date: 2024-9-29

description: How to use GoGoBlog

favicon: 🪛
image: usage.jpg
---

GoGoBlog uses the following file structure:
```
index.md

post
└─ my_first_post.md

html
├─ menu.html
└─ comments.html

docs
├─ index.html
├─ index.css
└─ my_first_post.html
```

Where `index.md` is the home page of your blog and the `post` folder is used to host your posts. 
The `html` folder is where GoGoBlog is looking for html partials such as the top menu and the commenting service you chose to use in your blog.
Finally, the `docs` folder is where the generated blog is saved to. 
You can safely add images to this foler and edit the `index.css` file under this folder as GoGoBlog will not overide or delete your files. The `docs` folder should be uploded to your static hosting service (e.g. GitHub pages) 

To create this directory structure and generate your blog simply run this:
```
blg
```
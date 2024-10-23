---
lang: en 

title: Usage
author: Gilad Kutiel
date: 2024-9-29

description: This section describes the directory structure of blgit and its basic usage. It covers how the files and folders are organized and provides guidance on how to use the tool effectively for managing your blog.

favicon: 🪛
image: usage.jpg
---

blgit uses the following file structure:
```

template
├─ html.j2
├─ index.j2
└─ post.j2

index.md

post
└─ my_first_post.md

docs
├─ index.html
├─ index.css
└─ my_first_post.html
```

The `.j2` files under the `template` folder controls how your home page and each post will look like.

`index.md` is where you write the content of the home page and the `post` folder is where you write the content of your posts. 

The `docs` folder is where the generated blog is saved to. 

You can safely edit the `.j2` files to fit your needs. 
You can also add images and other files to the `docs` folder and also edit the `index.css` file as blgit will not override or delete your files. 

The `docs` folder should be uploaded to your static hosting service (e.g. GitHub pages) 

To create this directory structure and generate your blog simply run this:
```
blgit build
```

**Tip:** If you don't want to run `blgit` after every change, you can use your favorite file-watching tool like this:
```
ls **.css **.j2 **.md | entr -c blgit build     
```
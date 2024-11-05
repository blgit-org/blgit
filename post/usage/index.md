---
lang: en 

title: Usage
author: Gilad Kutiel
date: 2024-09-29

description: This section describes the directory structure of blgit and its basic usage. It covers how the files and folders are organized and provides guidance on how to use the tool effectively for managing your blog.

favicon: 📜
image: /img/usage.jpg
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

The `.j2` files in the `template` folder control the appearance of your homepage and each post.

In the `post` folder, you write all your content in `.md` files. blgit is flexible with file structure, allowing you to use either a flat or hierarchical organization.

The `index.md` file serves two purposes: primarily, it contains the content of your homepage; additionally, it configures certain aspects of the blog generation process.

The `docs` folder is where the generated blog is saved.

Feel free to customize the `.j2` files to suit your needs. You can also add images and other files to the `docs` folder, as well as edit the `index.css` file—blgit will not overwrite or delete your files.

The `docs` folder should be uploaded to your static hosting service (e.g., GitHub Pages).

To create this directory structure and generate your blog, simply run:

```bash
blgit build
```

**Tip:** If you don't want to run `blgit` after every change, you can use your favorite file-watching tool like this:
```
ls **.css **.j2 **.md | entr -c blgit build     
```
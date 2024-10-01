#! /usr/bin/env node

import fs from 'fs'
import { read } from 'gray-matter'
import { marked } from 'marked'
import path from 'path'
import { h } from 'preact'
import { render } from 'preact-render-to-string'

interface Metadata {
    lang: string
    author: string
    date: string
    favicon: string
    title: string
    description: string
    image: string
}

interface Post {
    data: Metadata
    content: string
    path: string
}

function loadResource(file: string) {
    return fs.readFileSync(path.resolve(__dirname, file)).toString()
}

fs.mkdirSync('pos')

const posts = fs.readdirSync('post').map(
    file => read(`post/${file}`)).sort(
        (a, b) => a.data.date > b.data.date ? -1 : 1) as unknown as Post[]


function localDate(post: Post) {
    return new Date(post.data.date).toLocaleDateString(post.data.lang)
}

function htmlPath(post: Post) {
    return `${path.basename(post.path, '.md')}.html`
}

function favicon(icon: string) {
    return <link rel="icon" href={`data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>${icon}</text></svg>`} />
}

const metaViewport = <meta name="viewport" content="width=device-width, initial-scale=1.0" />

function ogTitle(title: string) {
    return <meta property="og:title" content={title} />
}

function ogDescription(description: string) {
    return <meta property="og:description" content={description} />
}

function ogImage(image: string) {
    return <meta property="og:image" content={`https://gilad.kutiel.com/${image}`} />
}

function include(el: h.JSX.Element, file: string) {
    if (!fs.existsSync(file)) {
        console.warn(`W: file not found: ${file}`)
        return
    }

    el.props.dangerouslySetInnerHTML = { __html: fs.readFileSync(file, 'utf8') }

    return el
}

const postPreview = (post: Post) =>
    <a class="block" href={htmlPath(post)}>
        <div className="preview">
            <img src={post.data.image} alt="" />
            <h3>{post.data.title}</h3>
            <p>{post.data.description}</p>
        </div>
    </a>

function renderHtml(args: {
    lang: string,
    title: string,
    description: string,
    image: string,
    favicon: string,
    body: h.JSX.Element
}) {
    return render(
        <html lang={args.lang} dir="auto">
            <head>
                {metaViewport}
                {ogTitle(args.title)}
                {ogDescription(args.description)}
                {ogImage(args.image)}

                <link rel="stylesheet" href="index.css" />
                {favicon(args.favicon)}
                <title>{args.title}</title>
            </head>
            <body>
                {include(<menu />, 'html/menu.html')}
                {args.body}
            </body>
        </html>
    )
}


function renderPost(i: number) {
    const n = posts.length

    const prev = posts[(n + i - 1) % n]
    const post = posts[i]
    const next = posts[(i + 1) % n]

    console.log(`rendering ${post.path}`)

    fs.writeFileSync(
        `docs/${path.basename(post.path, '.md')}.html`,
        renderHtml({
            ...post.data,
            body: <main>
                <div class='title'>
                    <h1>{post.data.title}</h1>
                    <div class='author'>
                        {post.data.author} ︱ {localDate(post)}
                    </div>
                </div>


                <img src={post.data.image} alt={post.data.title} />

                <div dangerouslySetInnerHTML={{ __html: marked(post.content) as string }}></div>

                <div class="related">
                    {[prev, next].map(postPreview)}
                </div>

                {include(<footer />, 'html/comments.html')}
            </main>
        })
    )
}

function ensureExists(resource: string) {
    if (fs.existsSync(resource)) return

    console.info(`${resource} not found, creating...`)

    fs.mkdirSync(path.dirname(resource), { recursive: true })
    fs.writeFileSync(resource, loadResource(resource))
}

ensureExists('docs/index.css')
ensureExists('html/menu.html')
ensureExists('html/comments.html')
ensureExists('index.md')


const index = read('index.md') as unknown as Post

fs.writeFileSync(
    'docs/index.html',
    renderHtml({
        ...index.data,
        body: <main>
            <div dangerouslySetInnerHTML={{ __html: marked(index.content) as string }}></div>
            <div className="posts">
                {posts.map(post =>
                    <a class="block" href={htmlPath(post)}>
                        <div className="post">
                            <div className="row center">
                                <h2>{post.data.favicon} {post.data.title}</h2>
                                <div class='author'>{post.data.author} ︱ {post.data.date}</div>
                            </div>
                            <p>{post.data.description}</p>
                        </div>
                    </a>
                )}
            </div>
        </main>

    }))

for (const [i, _] of posts.entries()) {
    renderPost(i)
}


console.log('Blog is ready!')
console.log('Run `npx serve docs` to view it locally')
#! /usr/bin/env node

import { Feed } from 'feed'
import fs from 'fs'
import { read } from 'gray-matter'
import { marked } from 'marked'
import path from 'path'
import { h } from 'preact'
import { render } from 'preact-render-to-string'

class Fs {
    static post = 'post'
    static index_md = 'index.md'
    static menu_html = 'html/menu.html'
    static comments_html = 'html/comments.html'
    static index_css = 'docs/index.css'
    static cover_jpg = 'docs/cover.jpg'
}

interface Metadata {
    url: string
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
    return fs.readFileSync(path.resolve(__dirname, file))
}

function localDate(post: Post) {
    return new Date(post.data.date).toLocaleDateString(post.data.lang)
}

function htmlPath(post: Post) {
    return `${path.basename(post.path, '.md')}.html`
}

function favicon(icon: string) {
    return <link rel="icon" href={`data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>${icon}</text></svg>`} />
}


function ogTitle(title: string) {
    return <meta property="og:title" content={title} />
}

function ogDescription(description: string) {
    return <meta property="og:description" content={description} />
}

function ogImage(image: string) {
    return <meta property="og:image" content={`${index.data.url}/${image}`} />
}

function include(el: h.JSX.Element, file: string) {
    if (!fs.existsSync(file)) {
        console.warn(`W: file not found: ${file}`)
        return
    }

    el.props.dangerouslySetInnerHTML = { __html: fs.readFileSync(file, 'utf8') }

    return el
}

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
                {favicon(args.favicon)}

                {metaViewport}

                {ogTitle(args.title)}
                {ogDescription(args.description)}
                {ogImage(args.image)}

                <link rel="alternate" type="application/rss+xml" href={rssLink} title={index.data.title} />
                <link rel="stylesheet" href="index.css" />

                <title>{args.title}</title>
            </head>
            <body>
                {include(<menu />, 'html/menu.html')}
                {args.body}
            </body>
        </html>
    )
}

function ensureExists(resource: string) {
    if (fs.existsSync(resource)) return

    console.info(`${resource} not found, creating...`)

    fs.mkdirSync(path.dirname(resource), { recursive: true })
    fs.writeFileSync(resource, loadResource(resource))
}

function author(post: Post) {
    return <div class='author'>{post.data.author} ︱ {localDate(post)}</div>
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
                    {author(post)}
                </div>

                <p>{post.data.description}</p>

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

const postPreview = (post: Post) =>
    <a class="block" href={htmlPath(post)}>
        <div class="preview">
            <img src={post.data.image} alt="" />
            <h3>{post.data.title}</h3>
            <p>{post.data.description}</p>
        </div>
    </a>


const metaViewport = <meta name="viewport" content="width=device-width, initial-scale=1.0" />


fs.mkdirSync(Fs.post, { recursive: true })

ensureExists(Fs.index_css)
ensureExists(Fs.menu_html)
ensureExists(Fs.comments_html)
ensureExists(Fs.index_md)
ensureExists(Fs.cover_jpg)

const posts = fs.readdirSync(Fs.post).map(
    // older to newer
    file => read(`${Fs.post}/${file}`)).sort(
        (a, b) => a.data.date > b.data.date ? 1 : -1) as unknown as Post[]

const index = read('index.md') as unknown as Post
const rssLink = `${index.data.url}/rss.xml`


function renderFeed() {
    const today = new Date()
    const feed = new Feed({
        title: index.data.title,
        description: index.data.description,
        id: index.data.url,
        link: index.data.url,
        language: index.data.lang,
        image: `${index.data.url}/${index.data.image}`,
        copyright: `All rights reserved ${today.getFullYear()}, ${index.data.author}`,
        generator: 'blgit',
        feedLinks: {
            rss: rssLink,
        },
        author: {
            name: index.data.author,
        }
    })

    for (const post of posts) {
        const data = post.data
        feed.addItem({
            title: data.title,
            id: `${index.data.url}/${htmlPath(post)}`,
            link: `${index.data.url}/${htmlPath(post)}`,
            description: post.data.description,
            date: new Date(post.data.date),
            image: `${index.data.url}/${post.data.image}`,
            author: [{
                name: index.data.author,
            }]
        })
    }
    console.log('writing rss.xml')
    fs.writeFileSync('docs/rss.xml', feed.rss2())
}

function renderIndexHtml() {
    fs.writeFileSync(
        'docs/index.html',
        renderHtml({
            ...index.data,
            body: <main>
                <div dangerouslySetInnerHTML={{ __html: marked(index.content) as string }}></div>
                <div class="posts">
                    {posts.map(post =>
                        <a class="block" href={htmlPath(post)}>
                            <div class="post">
                                <div class="row center">
                                    <h2>{post.data.favicon} {post.data.title}</h2>
                                    {author(post)}
                                </div>
                                <p>{post.data.description}</p>
                            </div>
                        </a>
                    )}
                </div>
            </main>

        }))
}

// OUTPUTS
renderFeed()
renderIndexHtml()
for (const [i, _] of posts.entries()) {
    renderPost(i)
}


// DONE
console.log('')
console.log('🎉🎉🎉🎉🎉🎉🎉')
console.log('Blog is ready!')
console.log('Run `npx serve docs` to view it locally')
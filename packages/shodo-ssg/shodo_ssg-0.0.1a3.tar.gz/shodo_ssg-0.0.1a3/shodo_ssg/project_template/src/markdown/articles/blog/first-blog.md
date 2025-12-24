@frontmatter
{
    "title": "First Blog",
    "category": "general",
    "body_class": "blog-page first-blog",
    "description": "This is the first blog description",
    "tags": ["four", "five","six"],
    "published_datetime": "2025-01-25T05:00:00Z"
}
@endfrontmatter

## First Blog Post
This page was automatically generated as html by creating a markdown file in the `markdown/articles` directory! It's a perfect way to quickly publish blog posts, articles, or updates. 

Articles from the `markdown/articles` directory are rendered with a reusable template defined in `views/articles/` Just add a `layout.jinja` file under a subdirectory that matches the subdirectory tree used in `markdown/articles`, or simply define a `layout.jinja` at the root of `views/articles` if you want to use a single layout template for all articles. 

The site builder will always match up the layout template that is closest in the tree, so `markdown/articles/blog/updates/new-post.md` would be matched with `views/articles/blog/layout.jinja` if no layout is defined for the `updates` directory.

#### layout.jinja

The `layout.jinja` is just a normal jinja template, but the `{{ article }}` variable has been reserved as a variable for passing in the content data from each page. Simply define whatever repeated layout you would like to wrap the `{{ article.content }}` content, such as a header and footer.

Here is an example layout template:

```html
<div class="container">
    <header class="page-header">
        <h1 class="page-header__title">This is the root article layout</h1>
    </header>
    <main>
        {{ article.content }}
    </main>
    <footer>Thanks for reading</footer>
</div>
```

[Back to home](/)
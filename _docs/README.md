# AnyLog Docs

Technical documentation for [AnyLog Edge Data Fabric](https://www.anylog.network/), built with Jekyll and hosted on GitHub Pages.

## Local development

```bash
bundle install
bundle exec jekyll serve
# → http://localhost:4000
```

## Adding a new doc page

1. Create a Markdown file in `_docs/`, e.g. `_docs/my-topic.md`
2. Add front matter:
   ```yaml
   ---
   title: My Topic
   description: One-line description shown under the title.
   layout: page
   ---
   ```
3. Register it in `_config.yml` under the appropriate `nav` section:
   ```yaml
   nav:
     - title: My Section
       items:
         - slug: my-topic
           title: My Topic
   ```

## Deployment

Push to the `main` branch. GitHub Pages builds and publishes automatically.
Configure under **Settings → Pages → Source: Deploy from branch → main / root**.

### Local-Blog

A complete blog web server running on bottle.py.
It serves blog posts written in Markdown.

#### Prerequisites

You need Python3 and some packages. Get them using:

    pip install --upgrade -r requirements.txt

#### Usage

```bash
./app.py \
  --b http://johndoe.wordpress.com \
  -a "John Doe" \
  -t "Local Blog" \
  --about "John Doe is an IT entrepreneur and young professional with a special interest in blogging" \
  --catchphrase "Your blog, served from your local computer" \
  --external-links Github=https://github.com/johndoe \
  --debug \
  ~/markdown_blog_posts/
```


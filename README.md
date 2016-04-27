### Local-Blog

Made to serve a backup copy of your wordpress blog created with
[backup-wordpress-blog.py](https://gist.github.com/pklaus/4546743).

#### Prerequisites

You need Python3 and some packages. Get them using:

    pip install -r requirements.txt

#### Usage

    ./app.py \
      --b http://johndoe.wordpress.com \
      -a "John Doe" \
      -t "Local Blog" \
      --catchphrase "Your blog, served from your local computer" \
      --external-links Github=https://github.com/johndoe \
      --debug \
      ~/blog-backup/2015-12-24/ \


# hytale-api

Unofficial Python library for interacting with the Hytale API.

⚠️ **This library is unofficial and based on publicly discovered endpoints.**

Hytale is set to release on the 13th of January and I hope more _documented_ and more useful endpoints can be added.

## Get Started

### Installation

```bash
pip install hytale-api
```

OR

```bash
pip install git+https://github.com/DRagssss/hytale-api.git
```

### Example Use

This package consists of some endpoints that do not need any authorization (since they are basic information which are accessible on the Hytale website) so it's extremely easy to use.

Get excerpts of the latest 3 blogs.

```Python
from hytale import get_blogs

blogs = get_blogs()  # limit defaults to 3

for blog in blogs:
    print(blog.bodyExcerpt)  # first couple sentences of body
```

You can also get the entire HTML body of a singular blog.

```Python
from hytale import get_blog

slug = "hytale-s-1st-faq"  # this will get the blog from https://hytale.com/news/2025/12/hytale-s-1st-faq
blog = get_blog(slug)

print(blog.body)  # very long HTML content
```

All endpoints to do with accounts such as username reservations and game profiles require a logged-in user to access them. This is checked by the accounts API using the "ory_kratos_session" cookie value. To get this follow the steps below.

1. Login at https://hytale.com and then open dev tools in your browser (shortcut Ctrl-Shift-C.)
2. Navigate to the **Application** or **Storage** and then go to **Cookies**.
3. Go to cookies under the URL https://accounts.hytale.com.
4. Copy the value of the ory_kratos_session cookie.

This is how the AccountClient object is used.

```py
from hytale import AccountClient

client = AccountClient("YOUR_SESSION_COOKIE_VALUE")

available = client.get_available("MrBeast")  # check if the MrBeast username is available (example)
```

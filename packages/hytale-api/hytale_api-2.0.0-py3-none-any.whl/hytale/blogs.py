from .http import get
from .models.blogs.blog_post import BlogPost
from .models.blogs.blog_post_excerpt import BlogPostExcerpt


def get_blogs(limit=3) -> list[BlogPostExcerpt]:
    """Get the most recent blogs with a snippet of the blog post's body.

    Args:
        limit (int, optional): The number of blog posts to retrieve. Defaults to 3.

    Returns:
        list[BlogPostExcerpt]: A list of blog post excerpts.
    """
    data = get("/blog/post/published", limit=limit)
    return [BlogPostExcerpt.from_dict(item) for item in data]


def get_blog(slug: str) -> BlogPost:
    """Get a blog post with the entire body HTML content

    Args:
        slug (str): The slug provided by Hytale. For example https://hytale.com/news/2025/12/hytale-s-1st-faq has a slug of "hytale-s-1st-faq"

    Returns:
        BlogPost: The blog post.
    """
    data = get(f"/blog/post/slug/{slug}")
    return BlogPost.from_dict(data)


def get_blogs_for_year_month(year: int, month: int) -> list[BlogPostExcerpt]:
    """Get the most recent blogs within a year and month

    Args:
        year (int): The year to filter blogs by.
        month (int): The month to filter blogs by.

    Returns:
        list[BlogPostExcerpt]: A list of blog post excerpts.
    """
    data = get(f"/blog/post/archive/{year}/{month}")
    return [BlogPostExcerpt.from_dict(item) for item in data]


def get_blogs_for_year(year: int) -> list[BlogPostExcerpt]:
    """Get the most recent blogs within a year. Please prefer the use of get_blogs_for_year_month() as this function simply calls it 12 times.

    Args:
        year (int): The year to filter blogs by.

    Returns:
        list[BlogPostExcerpt]: A list of blog post excerpts.
    """

    blogs = []
    for i in range(1, 13):
        i = 13 - i  # reverse the order of months
        monthly_blogs = get_blogs_for_year_month(year, i)
        blogs.extend(monthly_blogs)
    return blogs

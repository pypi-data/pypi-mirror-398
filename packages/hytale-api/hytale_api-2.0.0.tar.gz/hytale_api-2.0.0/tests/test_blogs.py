import unittest
from datetime import datetime
from unittest.mock import patch

from hytale import BlogPostExcerpt, get_blogs


class TestGetBlogs(unittest.TestCase):
    @patch("hytale.blogs.get")
    def test_get_blogs_with_mock(self, mock_get):
        mock_get.return_value = [
            {
                "_id": "123",
                "title": "Test Blog",
                "author": "Author",
                "featured": True,
                "tags": ["test", "hytale"],
                "publishedAt": "2025-12-19T12:00:00+00:00",
                "coverImage": {
                    "_id": "cover123",
                    "variants": ["blog_thumb", "blog_cover"],
                    "s3Key": "abc.png",
                    "mimeType": "image/png",
                    "attached": True,
                    "createdAt": "2025-12-19T12:00:00+00:00",
                    "__v": 1,
                    "contentId": "123",
                    "contentType": "BlogPost",
                },
                "createdAt": "2025-12-19T12:00:00+00:00",
                "slug": "test-blog",
                "bodyExcerpt": "This is a test blog excerpt",
            }
        ]

        blogs = get_blogs(1)

        assert isinstance(blogs, list)
        assert all(isinstance(blog, BlogPostExcerpt) for blog in blogs)

        first_blog = blogs[0]
        assert first_blog.title == "Test Blog"
        assert first_blog.coverImage.s3Key == "abc.png"
        assert first_blog.bodyExcerpt == "This is a test blog excerpt"
        assert first_blog.publishedAt == datetime.fromisoformat(
            "2025-12-19T12:00:00+00:00"
        )
        assert first_blog.coverImage.createdAt == datetime.fromisoformat(
            "2025-12-19T12:00:00+00:00"
        )

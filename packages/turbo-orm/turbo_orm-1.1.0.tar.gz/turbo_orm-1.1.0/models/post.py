from lite_model import Model, IntegerField, TextField


class Post(Model):
    name = TextField()
    created_at = TextField()  # Use DateTimeField in production

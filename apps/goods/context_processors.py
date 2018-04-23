from django_redis import get_redis_connection


def get_cart_count(request):
    cart_count = 0
    if request.user.is_authenticated():
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % request.user.id
        cart_count = conn.hlen(cart_key)
    return {"cart_count": cart_count}

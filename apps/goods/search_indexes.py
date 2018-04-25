from haystack import indexes
from apps.goods.models import GoodsSKU


# 指定对于某个类的某些数据建立索引
# 类名无要求，但一般都是模型类名+Index
class GoodsSKUIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)

    def get_model(self):
        # 返回模型类
        return GoodsSKU

    def index_queryset(self, using=None):
        # 返回表中的所有数据
        return self.get_model().objects.all()

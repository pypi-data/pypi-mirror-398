
class BaseDeal:
    def has_prev(self):
        return 1
    def has_deal(self):
        return 1
    def sp(self):
        return super(self.__class__, self)
    def regist(self, mgs):
        if self._id is None:
            self._id = mgs.regist()
    def id(self):
        return self._id
    def same(self, s, target):
        return self.like(s, target) == target
    @staticmethod
    def like(s, target):
        if type(target) ==type(s):
            return s
        if type(s)==str:
            return s.encode()
        return s.decode()
    def __str__(self):
        return "BaseDeal"
    def __repr__(self):
        return str(self)
    def __init__(self, *argv, **maps):
        self._id = None
        self.init(*argv, **maps)
    def init(self, *argv, **maps):
        pass
    def prev(self, buffer, queue, pos):
        """
            input:
                buffer: 1,读取字符串/字节，没有pop的时候，会保留读取的数据据, buffer.read(size=1, pop = False), buffer.pop_read(size=1)
                        2,缓存, buffer.add(chars), buffer.lget(size=1): chars, buffer.rget(size=1): chars
                        buffer.lpop(size=1):None, buffer.rpop(size=1)
                queue: 存放生成节点的队列, queue=list<obj>
                pos: 位置计算: pos.update(chars), pos.get(index=0|index<=0): return [row, column]
            output:
                bool: 是否进行了处理
        """
        return False
    def deal(self, queue, stack):
        """
            input:
                queue: 节点输入队列
                stack: 存放生成结果的栈
            output:
                bool: 是否进行了处理
        """
        return False

pass


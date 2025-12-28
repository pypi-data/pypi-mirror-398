class Slice:

    def __class_getitem__(cls, item):
        return item


if __name__ == '__main__':
    print(Slice[1:])

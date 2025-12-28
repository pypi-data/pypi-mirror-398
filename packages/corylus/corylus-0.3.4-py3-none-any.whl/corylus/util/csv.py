__all__ = ['csv']

from csv import reader
import sys

def csv(input=sys.stdin, delimiter=','):
    for row in reader(input, delimiter=delimiter):
        yield row

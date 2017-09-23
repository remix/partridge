import numpy as np
import pandas as pd

from partridge.utilities import empty_df, setwrap


def test_empty_df():
    actual = empty_df(['foo', 'bar'])

    expected = pd.DataFrame({
        'foo': [],
        'bar': [],
    }, columns=['foo', 'bar'], dtype=np.unicode)

    assert actual.equals(expected)


def test_setwrap():
    assert setwrap('a') == {'a'}
    assert setwrap(['a']) == {'a'}
    assert setwrap({'a'}) == {'a'}

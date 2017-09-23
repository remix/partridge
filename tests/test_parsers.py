import datetime
import numpy as np


from partridge.parsers import \
    parse_time, parse_date, \
    vparse_time, vparse_date


def test_parse_date():
    assert parse_date('20990101') == datetime.date(2099, 1, 1)
    assert parse_date(datetime.date(2099, 1, 1)) == datetime.date(2099, 1, 1)


def test_parse_date_with_invalid_month():
    try:
        parse_date('20991401')
        assert False
    except ValueError as e:
        assert 'unconverted data remains: 01' in repr(e)


def test_parse_date_with_invalid_day():
    try:
        parse_date('20990133')
        assert False
    except ValueError as e:
        assert 'unconverted data remains: 3' in repr(e)


def test_vparse_date():
    datestrs = ['20990101', '20990102']
    dateobjs = [datetime.date(2099, 1, 1), datetime.date(2099, 1, 2)]

    assert np.array_equal(vparse_date(np.array(datestrs)), dateobjs)
    assert np.array_equal(vparse_date(np.array(dateobjs)), dateobjs)


def test_parse_time():
    assert parse_time('') is np.nan
    assert parse_time('  ') is np.nan
    assert parse_time('00:00:00') == 0
    assert parse_time('0:00:00') == 0
    assert parse_time('01:02:03') == 3723
    assert parse_time('1:02:03') == 3723
    assert parse_time('25:24:23') == 91463
    assert parse_time('250:24:23') == 901463


def test_parse_time_with_invalid_input():
    try:
        parse_time('10:15:00am')
        assert False
    except ValueError as e:
        assert 'invalid literal for int()' in repr(e)


def test_vparse_time():
    timestrs = ['00:00:00', '250:24:23']
    timeints = [0, 901463]

    assert np.array_equal(vparse_time(np.array(timestrs)), timeints)

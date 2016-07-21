from math import ceil
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy.orm import aliased
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declared_attr
import sqlalchemy.types as types

from impression.utils import (json_dumps, camelcase_to_underscore,
                                             underscore_to_camelcase, uuid)
from datetime import datetime

db = SQLAlchemy()
Session = db.session


class ChoiceType(types.TypeDecorator):
    impl = types.String

    def __init__(self, choices, **kw):
        self.choices = dict(choices)
        super(ChoiceType, self).__init__(**kw)

    def process_bind_param(self, value, dialect):
        return [k for k, v in self.choices.iteritems() if v == value][0]

    def process_result_value(self, value, dialect):
        return self.choices[value]


def safe_commit(session=None, close_after=False):
    """This commit function will rollback the transaction if
    committing goes awry. Also will close the connection if
    boolean is passed.

    @param session: A SQLAlchemy Session instance to commit.
    @param close_after: Boolean saying whether or not to close the SQLAlchemy's
                        Session connection after committing."""
    from sqlalchemy.exc import InvalidRequestError
    if session is None:
        session = Session

    try:
        session.commit()
    except InvalidRequestError as exc:
        # This exception is raised when another error with our
        # database has occurred. For Example, OperationalError for a
        # missing column or invalid column value.
        print(exc)
    except (Exception, SQLAlchemyError):
        session.rollback()
        raise

    if close_after:
        session.close()


def results_to_dict(result_list, **kwargs):
    return [result.to_dict(**kwargs) for result in result_list]


def results_to_json(result_list):
    return json_dumps([result.to_dict(camel_case=True) for result in result_list])


def unique_results(result_list):
    ids = []
    return_list = []
    for result in result_list:
        if result.id not in ids:
            return_list.append(result)
            ids.append(result.id)
    return return_list


def paginate(query_object, current_page, pagesize):
    """
    Return a tuple containing the result set limited & offset by the current
    page and page size along with the number of the maximum pages for the query.
    @param query_object: SQLAlchemy query to paginate.
    @param current_page: An Integer value representing the current page in the
                         result. Pages 'start' at 1.
    @param pagesize: An integer value representing the page size of our result
                     and the number of rows to return.
    @return: A tuple containing the result then the maximum page number.
    """

    pagesize = int(pagesize) if pagesize else 0
    current_page = int(current_page) if current_page else 0

    if current_page <= 0:
        # The paginate function assumes that current_page's lower
        # limit is 1 - to coincide with the frontend of BriteCore.
        current_page = 1

    if pagesize <= 0:
        # The page size can't be less than or equal to zero,
        # otherwise no results would be returned.
        pagesize = 1

    max_pages = int(ceil(float(query_object.count()) / pagesize))
    result = query_object.limit(pagesize)\
                         .offset((current_page - 1) * pagesize).all()

    return result, max_pages


def property_to_dict(model_property, **kwargs):
    '''
    Takes a SQLAlchemy model's property and converts it to a dict.

    @param kwargs: Magical kwargs can pass anything but we would
                   expect a potential camel_case=True here.
    '''
    if type(model_property) in ('list', 'tuple'):
        try:
            # **kwargs will typically pass camel_case=T/F
            return_val = [x.to_dict(**kwargs) for x in model_property]
        except AttributeError:
            return_val = model_property
    else:
        if isinstance(model_property, OurMixin):
            # **kwargs will typically pass camel_case=T/F
            return_val = model_property.to_dict(**kwargs)
        else:
            return_val = model_property
    return return_val


def filter_by_date(query_object, filter_dict, filter_column):
    """
    Adds to / from date filters to an existing SQLAlchemy query object.

    @param query_object: The SQLAlchemy Query Object to filter.
    @param filter_dict: A dictionary containing date parts to filter by;
                        keys in the form of '(from|to)(Day|Month|Year)'.
                        Example: 'fromDay'.
    @param filter_column: A SQLAlchemy column to use in the filters.
                          Example: AccountHistory.transaction_date_time.
    @return: The newly filtered Query Object.
    """
    from sqlalchemy import extract
    if filter_dict:
        if not all([filter_dict['fromYear'], filter_dict['toYear'],
                    filter_dict['fromMonth'], filter_dict['toMonth'],
                    filter_dict['fromDay'], filter_dict['toDay']]):

            # Add SQL filters for each individual date part defined by the
            # filter
            for attr, key in (('year', 'fromYear'), ('year', 'toYear'),
                              ('month', 'fromMonth'), ('month', 'toMonth'),
                              ('day', 'fromDay'), ('day', 'toDay')):

                if filter_dict[key]:
                    filter_date_part = extract(attr, filter_column)
                    if key.startswith('from'):
                        query_object = query_object.filter(
                            filter_date_part >= filter_dict[key])
                    else:
                        query_object = query_object.filter(
                            filter_date_part <= filter_dict[key])

        else:
            # if filter_dict is complete, search by the days
            try:
                from_date = datetime(int(filter_dict['fromYear']), int(
                    filter_dict['fromMonth']), int(filter_dict['fromDay']))
                # Add in 23:59:59 for between() to grab all rows with time
                # greater than midnight of the toDate #8482 -- Ben Hayden
                # 06/13/12
                to_date = datetime(int(filter_dict['toYear']), int(
                    filter_dict['toMonth']), int(filter_dict['toDay']), 23, 59, 59)
                query_object = query_object.filter(
                    filter_column.between(from_date, to_date))
            except ValueError:
                # Except out of any invalid dates, and return error message
                raise UserWarning(
                    "Invalid Date Filters entered. Please check the date values and search again.")

    return query_object


class OurMixin(object):
    """Our Mixin class for defining declarative table models
    in SQLAlchemy. We use this class to define consistent table
    args, methods, etc."""

    # We want all tables to have created_on and updated_on fields
    @declared_attr
    def created_on(cls):
        return db.Column(db.DateTime(), nullable=False, default=datetime.now)

    @declared_attr
    def updated_on(cls):
        return db.Column(db.DateTime(), nullable=False, default=datetime.now)

    # Auto set ID with uuid on init
    def __init__(self, **kwargs):
        """Override default __init__, if the mapper has an id
        column and it isn't set, set it to a new uuid."""
        for k, v in kwargs.items():
            setattr(self, k, v)

        if hasattr(self, 'id') and not self.id and isinstance(self.__table__.c.id.type, db.VARCHAR):
            self.id = uuid()

    def __repr__(self):
        if hasattr(self, 'id'):
            return '%s(%s) Address: %s\n%s' % (self.__class__, self.id, id(self), self.to_json())
        else:
            return '%s Address: %s\n%s' % (self.__class__, id(self), self.to_json())

    def __str__(self):
        return self.to_json()

    @classmethod
    def aliased(self, name=None):
        """Convenience method to alias a table under another name."""
        return aliased(self) if name is None else aliased(self, name=name)

    @classmethod
    def all(self):
        """Convenience method to return all the records in a table.

        @return: The model with the passed primary key."""
        return Session.query(self).all()

    def clone(self, source):
        for column in source.__table__.c:
            if column.name != 'id':
                setattr(self, camelcase_to_underscore(column.name), getattr(
                    source, camelcase_to_underscore(column.name)))
            else:
                setattr(self, 'id', uuid())

    @classmethod
    def count(self):
        return Session.query(func.count(self.id)).scalar()

    def delete(self):
        """Convenience method to remove a model from the session
        and ultimately from the database upon commit."""
        Session.delete(self)

    @classmethod
    def filter(self, *args, **kwargs):
        """Convenience method to return a Query object with the
        passed SQLAlchemy Clause statement a filter.

        @return: A SQLALchemy Query object."""
        return Session.query(self).filter(*args, **kwargs)

    @classmethod
    def filter_by(self, *args, **kwargs):
        """Convenience method to return a Query object with the
        passed args & kwargs to Query.filter_by.

        @return: A SQLALchemy Query object."""
        return Session.query(self).filter_by(*args, **kwargs)

    @classmethod
    def first(self):
        """Convenience method to return a single record in a table.

        @return: The first model from the table."""
        return Session.query(self).first()

    def from_dict(self, the_dict, strict=False):
        '''
        Convenience method to populate a model from a dict. It will automatically convert camel case keys
        to underscore equivalents.

        @param: the_dict: A dictionary of values to be set in the model.
        @param: strict: A boolean switch to throw an exception if the corresponding key is not found

        @return: An instance of the model with the keys set.
        '''
        for key in the_dict:
            us_key = camelcase_to_underscore(key)
            if hasattr(self, us_key):
                setattr(self, us_key, the_dict[key])
            else:
                if strict:
                    raise UserWarning('from_dict() error: The %s model does not have a %s key.' % (
                        self.__class__, us_key))
        return self

    @classmethod
    def get(self, primary_key):
        """Convenience method to take a primary key of the model
        and return a single model instance or None if the model
        couldn't be found using the key.

        @param primary_key: The primary key for the model.
        @return: The model with the passed primary key."""
        result = None
        if primary_key is not None:
            result = Session.query(self).get(primary_key)
        return result

    def insert(self, merge=True, return_key='id'):
        """Convenience method to add a model to the session
        and ultimately insert in the database permanently upon commit."""
        Session.add(self)
        if hasattr(self, 'id'):
            return json_dumps({return_key: self.id})
        else:
            return True

    @property
    def is_valid(self):
        return self.validate().get('success', False)

    @classmethod
    def join(self, *args, **kwargs):
        """Convenience method to return a Query object
        by using the Query.join object.

        @return: A SQLALchemy Query object."""
        return Session.query(self).join(*args, **kwargs)

    @classmethod
    def max(self, column_name):
        from sqlalchemy import func
        return Session.query(func.max(getattr(self, column_name))).scalar()

    @classmethod
    def min(self, column_name):
        from sqlalchemy import func
        return Session.query(func.min(getattr(self, column_name))).scalar()

    @classmethod
    def order_by(self, *args, **kwargs):
        """Convenience method to return a Query object with the
        passed args & kwargs to Query.order_by.

        @return: A SQLALchemy Query object."""
        return Session.query(self).order_by(*args, **kwargs)

    @classmethod
    def outerjoin(self, *args, **kwargs):
        """Convenience method to return a Query object
        by using the Query.outerjoin object.

        @return: A SQLALchemy Query object."""
        return Session.query(self).outerjoin(*args, **kwargs)

    @classmethod
    def random(self):
        engine = str(db.engine)
        if 'postgresql' in engine:
            # Postgres
            return Session.query(self).order_by(func.random()).first()
        elif 'mysql' in engine:
            # MySQL
            return Session.query(self).order_by(func.rand()).first()
        elif 'sqlite' in engine:
            # sqlite
            return Session.query(self).order_by(func.random()).first()

    @classmethod
    def select_from(self, *args, **kwargs):
        """Convenience method to return a Query object
        via a call to Query.select_from().

        @return: A SQLAlchemy Query Object."""
        return Session.query(self).select_from(*args, **kwargs)

    @classmethod
    def sum(self, column_name):
        from sqlalchemy import func
        return Session.query(func.sum(getattr(self, column_name))).scalar()

    @classmethod
    def columns(self, *columns):
        """Convenience method to return a Query object
        to select specific columns.
        NOTE: columns must be fully specified from model:
            > MyModel.columns(MyModel.id, OtherModel.name)

        @return: A SQLAlchemy Query Object."""
        return Session.query(*columns)

    def set(self, **kwargs):
        """
        Use each key in kwargs to set the appropriate value in self
        """
        for key in kwargs:
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
            else:
                raise UserWarning('%s has no attribute %s' %
                                  (self.__class__, key))

    def doc_dict(self, camel_case=False, columns=None):
        '''
        Convenience method to generate a dict from a model instance. It can automatically convert camel case keys
        to underscore equivalents.

        @param: camel_case: A boolean switch to convert the resulting dict keys to camel case.
        @param: columns: A list of (camelCased) columns that should be included in the result as keys.
        @param: renames: A dictionary of {'column_name': 'myCoolNewColumnName'} to use used like AS

        @return: An dict with all the columns of the model as keys and values.
        '''
        the_dict = self.to_dict(camel_case=camel_case, columns=columns)
        for key in the_dict:
            cc_key = underscore_to_camelcase(key) if not camel_case else key
            sqltype = self.find_type(cc_key)
            the_dict[key] = sqltype

        return the_dict

    def to_dict(self, camel_case=False, columns=None, datetime_to_str=False):
        '''
        Convenience method to generate a dict from a model instance. It can automatically convert camel case keys
        to underscore equivalents.

        @param: camel_case: A boolean switch to convert the resulting dict keys to camel case.
        @param: columns: A list of (camelCased) columns that should be included in the result as keys.

        @return: An dict with all the columns of the model as keys and values.
        '''
        return_dict = {}
        for column in self.__table__.c:
            us_column_name = camelcase_to_underscore(column.name)
            if not columns or column.name in columns:
                if camel_case:
                    key = column.name
                else:
                    key = us_column_name
                value = str(getattr(self, us_column_name))
                if datetime_to_str:
                    if isinstance(value, datetime):
                        value = str(value)
                return_dict[key] = value
        return return_dict

    def to_json(self, columns=None):
        '''
        Convenience method to generate a JSON object from a model instance. It will automatically convert camel case keys
        to underscore equivalents.

        @param: columns: A list of (camelCased) columns that should be included in the result as keys.

        @return: A JSON object with all the columns of the model as keys and values.
        '''
        from json import loads  # We need this import because our json_loads doesn't throw exceptions!
        my_dict = self.to_dict(camel_case=True, columns=columns)
        for key in my_dict:
            try:
                loaded = loads(my_dict[key])
                my_dict[key] = loaded
            except (TypeError, ValueError):
                # Not JSON... keep going.
                pass
        return json_dumps(my_dict)

    def validate(self):
        return {'success': True, 'messages': []}
